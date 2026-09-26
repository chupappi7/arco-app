import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { getAccount, accessTokenFor } from './accounts.js';
import { mediaUrl } from './media.js';
import { MAX_IMAGES, MAX_QUEUED, MIN_LEAD_SECONDS, KEEP_AFTER_DONE, PRIVACY } from './limits.js';

const len = s => [...String(s ?? '')].length;
const bad = msg => { throw new HttpError(400, msg); };

export function validatePost(input, t = now()) {
  const i = input || {};
  if (typeof i.account_id !== 'string' || !i.account_id) bad('Pick an account');
  const keys = Array.isArray(i.image_keys) ? i.image_keys : [];
  if (keys.length < 1) bad('Add at least one image');
  if (keys.length > MAX_IMAGES) bad(`A photo post can have at most ${MAX_IMAGES} images`);
  if (!keys.every(k => typeof k === 'string' && k)) bad('Image list is invalid');
  const cover = i.cover_index == null ? 0 : Number(i.cover_index);
  if (!Number.isInteger(cover) || cover < 0 || cover >= keys.length) bad('The cover must be one of the images');
  const title = String(i.title ?? ''), caption = String(i.caption ?? '');
  if (len(title) > 90) bad('The title can be at most 90 characters');
  if (len(caption) > 4000) bad('The caption can be at most 4000 characters');
  const s = i.settings || {};
  if (!PRIVACY.includes(s.privacy_level)) bad('Choose who can view this post');
  const settings = {
    privacy_level: s.privacy_level,
    disable_comment: !!s.disable_comment,
    auto_add_music: !!s.auto_add_music,
    brand_organic: !!s.brand_organic,
    branded_content: !!s.branded_content,
  };
  if (settings.branded_content && settings.privacy_level === 'SELF_ONLY') {
    bad('Branded content cannot be posted as Only me');
  }
  let at;
  if (i.scheduled_at === null || i.scheduled_at === undefined) at = t;
  else {
    at = Number(i.scheduled_at);
    if (!Number.isInteger(at)) bad('scheduled_at must be epoch seconds or null');
    if (at < t + MIN_LEAD_SECONDS) bad('Pick a time at least 5 minutes from now');
  }
  return { account_id: i.account_id, title, caption, image_keys: keys, cover_index: cover, settings, scheduled_at: at };
}

export function postJson(env, row) {
  const keys = JSON.parse(row.image_keys);
  return {
    id: row.id, account_id: row.account_id, username: row.username ?? '', status: row.status,
    title: row.title, caption: row.caption, images: keys.map(k => mediaUrl(env, k)), image_keys: keys,
    cover_index: row.cover_index, settings: JSON.parse(row.settings), scheduled_at: row.scheduled_at,
    attempts: row.attempts, public_post_id: row.public_post_id, fail_reason: row.fail_reason,
    post_url: row.status === 'published' && row.public_post_id && row.username
      ? `https://www.tiktok.com/@${row.username}/photo/${row.public_post_id}` : null,
  };
}

async function loadPost(env, ws, id) {
  const row = await env.DB.prepare(`SELECT p.*, a.username FROM posts p LEFT JOIN accounts a ON a.id = p.account_id
      WHERE p.id = ? AND p.workspace_id = ?`).bind(id, ws).first();
  if (!row) throw new HttpError(404, 'Post not found');
  return row;
}

export async function createPost(env, tk, ws, input) {
  const p = validatePost(input);
  const account = await getAccount(env, ws, p.account_id);
  if (account.needs_reconnect) throw new HttpError(409, 'Reconnect this account before posting', 'needs_reconnect');

  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND status = 'queued'`).bind(ws).first();
  if (n >= MAX_QUEUED) throw new HttpError(409, `You can have at most ${MAX_QUEUED} posts waiting at a time`);

  const marks = p.image_keys.map(() => '?').join(',');
  // Images may come fresh from upload, or from a cancelled/failed post being
  // edited into a new one. Images of a queued or published post are taken.
  const { results } = await env.DB.prepare(`SELECT key FROM media WHERE workspace_id = ? AND key IN (${marks})
      AND (post_id IS NULL OR post_id IN (SELECT id FROM posts WHERE status IN ('cancelled', 'failed')))`)
    .bind(ws, ...p.image_keys).all();
  if (results.length !== new Set(p.image_keys).size || results.length !== p.image_keys.length) {
    bad('One or more images are missing, already used by another post, or listed twice. Upload them again.');
  }

  // The panel already limits privacy to what TikTok offers; check again here
  // because the API can be called without the panel.
  const info = await tk.creatorInfo(await accessTokenFor(env, tk, account));
  if (!(info.privacy_level_options || []).includes(p.settings.privacy_level)) {
    bad('That privacy level is not available for this account right now');
  }

  const id = 'pst_' + randomToken('', 8), t = now();
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, title, caption, image_keys, cover_index,
        settings, scheduled_at, next_attempt_at, created_at, updated_at)
        VALUES (?, ?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, ws, p.account_id, p.title, p.caption, JSON.stringify(p.image_keys), p.cover_index,
            JSON.stringify(p.settings), p.scheduled_at, p.scheduled_at, t, t),
    env.DB.prepare(`UPDATE media SET post_id = ?, delete_after = NULL WHERE workspace_id = ? AND key IN (${marks})`)
      .bind(id, ws, ...p.image_keys),
  ]);
  return postJson(env, await loadPost(env, ws, id));
}

export async function listPosts(env, ws, from, to) {
  const { results } = await env.DB.prepare(`SELECT p.*, a.username FROM posts p LEFT JOIN accounts a ON a.id = p.account_id
      WHERE p.workspace_id = ? AND p.scheduled_at >= ? AND p.scheduled_at < ? ORDER BY p.scheduled_at`)
    .bind(ws, from, to).all();
  return results.map(r => postJson(env, r));
}

export async function cancelPost(env, ws, id) {
  const row = await loadPost(env, ws, id);
  if (row.status !== 'queued') throw new HttpError(409, 'Only posts that have not started can be cancelled');
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET status = 'cancelled', updated_at = ? WHERE id = ? AND status = 'queued'`).bind(t, id),
    env.DB.prepare('UPDATE media SET delete_after = ? WHERE post_id = ?').bind(t + KEEP_AFTER_DONE, id),
  ]);
  return postJson(env, await loadPost(env, ws, id));
}

export async function retryPost(env, ws, id) {
  const row = await loadPost(env, ws, id);
  if (row.status !== 'failed') throw new HttpError(409, 'Only failed posts can be retried');
  const keys = JSON.parse(row.image_keys);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM media WHERE post_id = ?').bind(id).first();
  if (n !== keys.length) throw new HttpError(409, 'The images for this post were already deleted. Create it again.');
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET status = 'queued', attempts = 0, next_attempt_at = ?, fail_reason = NULL,
        publish_id = NULL, updated_at = ? WHERE id = ?`).bind(t, t, id),
    env.DB.prepare('UPDATE media SET delete_after = NULL WHERE post_id = ?').bind(id),
  ]);
  return postJson(env, await loadPost(env, ws, id));
}
