import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { getAccount, accessTokenFor, isMeta } from './accounts.js';
import { wsOf, inScope } from './scope.js';
import { mediaUrl } from './media.js';
import { MAX_IMAGES, MAX_QUEUED, MAX_DRAFTS, MIN_LEAD_SECONDS, KEEP_AFTER_DONE, PRIVACY,
  IG_MAX_IMAGES, IG_MAX_CAPTION, IG_MAX_HASHTAGS, FB_MAX_CAPTION } from './limits.js';

const len = s => [...String(s ?? '')].length;
const bad = msg => { throw new HttpError(400, msg); };

// A draft keeps whatever is filled in: no privacy choice or time is needed
// until it is scheduled, and it is validated in full then.
export function validatePost(input, t = now(), platform = 'tiktok', { draft = false } = {}) {
  const i = input || {};
  if (typeof i.account_id !== 'string' || !i.account_id) bad('Pick an account');
  const keys = Array.isArray(i.image_keys) ? i.image_keys : [];
  if (keys.length < 1) bad('Add at least one image');
  if (keys.length > MAX_IMAGES) bad(`A photo post can have at most ${MAX_IMAGES} images`);
  if (platform === 'instagram' && keys.length > IG_MAX_IMAGES) bad(`An Instagram post can have at most ${IG_MAX_IMAGES} images`);
  if (!keys.every(k => typeof k === 'string' && k)) bad('Image list is invalid');
  const cover = i.cover_index == null ? 0 : Number(i.cover_index);
  if (!Number.isInteger(cover) || cover < 0 || cover >= keys.length) bad('The cover must be one of the images');
  const title = String(i.title ?? ''), caption = String(i.caption ?? '');
  if (len(title) > 90) bad('The title can be at most 90 characters');
  const capMax = platform === 'facebook' ? FB_MAX_CAPTION : 4000;
  if (len(caption) > capMax) bad(`The caption can be at most ${capMax} characters`);
  if (platform === 'instagram') {
    if (len(caption) > IG_MAX_CAPTION) bad(`An Instagram caption can be at most ${IG_MAX_CAPTION} characters`);
    if ((caption.match(/#[^\s#]+/g) || []).length > IG_MAX_HASHTAGS) bad(`Instagram allows at most ${IG_MAX_HASHTAGS} hashtags`);
  }
  const at = draft ? t : scheduledAt(i, t);
  // Privacy, music and the disclosure toggles are TikTok's; Instagram and
  // Facebook posts are public on a public profile.
  if (platform !== 'tiktok') {
    return { account_id: i.account_id, title, caption, image_keys: keys, cover_index: cover, settings: {}, scheduled_at: at };
  }
  const s = i.settings || {};
  if (draft && !s.privacy_level) {
    return { account_id: i.account_id, title, caption, image_keys: keys, cover_index: cover, scheduled_at: at,
      settings: { privacy_level: '', disable_comment: !!s.disable_comment, auto_add_music: !!s.auto_add_music,
        brand_organic: !!s.brand_organic, branded_content: !!s.branded_content } };
  }
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
  return { account_id: i.account_id, title, caption, image_keys: keys, cover_index: cover, settings, scheduled_at: at };
}

function scheduledAt(i, t) {
  if (i.scheduled_at === null || i.scheduled_at === undefined) return t;
  const at = Number(i.scheduled_at);
  if (!Number.isInteger(at)) bad('scheduled_at must be epoch seconds or null');
  if (at < t + MIN_LEAD_SECONDS) bad('Pick a time at least 5 minutes from now');
  return at;
}

function tiktokUrl(row) {
  return row.public_post_id && row.username ? `https://www.tiktok.com/@${row.username}/photo/${row.public_post_id}` : null;
}

export function postJson(env, row) {
  const keys = JSON.parse(row.image_keys);
  return {
    id: row.id, account_id: row.account_id, platform: row.platform ?? 'tiktok', username: row.username ?? '', status: row.status,
    title: row.title, caption: row.caption, images: keys.map(k => mediaUrl(env, k)), image_keys: keys,
    cover_index: row.cover_index, settings: JSON.parse(row.settings), scheduled_at: row.scheduled_at,
    attempts: row.attempts, public_post_id: row.public_post_id, fail_reason: row.fail_reason,
    group_id: row.group_id ?? null, updated_at: row.updated_at,
    post_url: row.status === 'published' ? (row.post_url || tiktokUrl(row)) : null,
    stats: row.stats ? JSON.parse(row.stats) : null, stats_at: row.stats_at ?? null,
  };
}

async function loadPost(env, w, id) {
  const sc = inScope(w, 'a.brand_id');
  const row = await env.DB.prepare(`SELECT p.*, a.username, a.platform FROM posts p LEFT JOIN accounts a ON a.id = p.account_id
      WHERE p.id = ? AND p.workspace_id = ?${sc.sql}`).bind(id, wsOf(w), ...sc.binds).first();
  if (!row) throw new HttpError(404, 'Post not found');
  return row;
}

export async function createPost(env, tk, w, input) {
  const ws = wsOf(w);
  if (typeof input?.account_id !== 'string' || !input.account_id) bad('Pick an account');
  const account = await getAccount(env, w, input.account_id);
  const draft = input.draft === true;
  const p = validatePost(input, now(), account.platform, { draft });
  // Posts made together share a group, so a draft reopens with all its accounts.
  const group = input.group_id == null ? null : String(input.group_id);
  if (group !== null && !/^grp_[0-9a-f]{16}$/.test(group)) bad('group_id is invalid');
  if (account.needs_reconnect) throw new HttpError(409, 'Reconnect this account before posting', 'needs_reconnect');

  // Edit = a new post that replaces a queued one, which stays scheduled
  // until this one is saved.
  const replaces = typeof input?.replaces === 'string' && input.replaces ? input.replaces : null;
  if (replaces) {
    const old = await loadPost(env, w, replaces);
    if (old.status !== 'queued') throw new HttpError(409, 'That post has already started or finished, so it cannot be edited');
  }

  const kind = draft ? 'draft' : 'queued', cap = draft ? MAX_DRAFTS : MAX_QUEUED;
  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND status = ?`).bind(ws, kind).first();
  if (n - (replaces && !draft ? 1 : 0) >= cap) {
    throw new HttpError(409, draft ? `You can keep at most ${MAX_DRAFTS} drafts` : `You can have at most ${MAX_QUEUED} posts waiting at a time`);
  }

  const marks = p.image_keys.map(() => '?').join(',');
  // Images may come fresh from upload, or from a cancelled/failed post being
  // edited into a new one. Images of a queued or published post are taken.
  const { results } = await env.DB.prepare(`SELECT key, content_type FROM media WHERE workspace_id = ? AND key IN (${marks})
      AND (post_id IS NULL OR post_id = ? OR post_id IN (SELECT id FROM posts WHERE status IN ('cancelled', 'failed')))`)
    .bind(ws, ...p.image_keys, replaces).all();
  if (results.length !== new Set(p.image_keys).size || results.length !== p.image_keys.length) {
    bad('One or more images are missing, already used by another post, or listed twice. Upload them again.');
  }
  if (account.platform === 'instagram' && !draft && results.some(r => r.content_type !== 'image/jpeg')) {
    bad('Instagram only accepts JPG images');
  }

  // The panel already limits privacy to what TikTok offers; check again here
  // because the API can be called without the panel.
  if (!isMeta(account) && !draft) {
    const info = await tk.creatorInfo(await accessTokenFor(env, tk, account));
    if (!(info.privacy_level_options || []).includes(p.settings.privacy_level)) {
      bad('That privacy level is not available for this account right now');
    }
  }

  const id = 'pst_' + randomToken('', 8), t = now();
  if (replaces) {
    // Conditional, so a post the cron claimed a moment ago is not replaced
    // (and so not published twice).
    const r = await env.DB.prepare(`UPDATE posts SET status = 'cancelled', fail_reason = 'Replaced by an edit',
        updated_at = ? WHERE id = ? AND workspace_id = ? AND status = 'queued'`).bind(t, replaces, ws).run();
    if (!r.meta.changes) throw new HttpError(409, 'That post has just started publishing, so it cannot be edited');
  }
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, title, caption, image_keys, cover_index,
        settings, scheduled_at, next_attempt_at, created_at, updated_at, group_id, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, ws, p.account_id, kind, p.title, p.caption, JSON.stringify(p.image_keys), p.cover_index,
            JSON.stringify(p.settings), p.scheduled_at, p.scheduled_at, t, t, group,
            typeof w === 'string' ? null : w.userId || null),
    env.DB.prepare(`UPDATE media SET post_id = ?, delete_after = NULL WHERE workspace_id = ? AND key IN (${marks})`)
      .bind(id, ws, ...p.image_keys),
  ]);
  return postJson(env, await loadPost(env, w, id));
}

export async function listPosts(env, w, from, to) {
  const sc = inScope(w, 'a.brand_id');
  const { results } = await env.DB.prepare(`SELECT p.*, a.username, a.platform FROM posts p LEFT JOIN accounts a ON a.id = p.account_id
      WHERE p.workspace_id = ? AND p.status != 'draft' AND p.scheduled_at >= ? AND p.scheduled_at < ?${sc.sql} ORDER BY p.scheduled_at`)
    .bind(wsOf(w), from, to, ...sc.binds).all();
  return results.map(r => postJson(env, r));
}

export async function cancelPost(env, w, id) {
  const row = await loadPost(env, w, id);
  if (row.status === 'draft') {
    const t = now();
    await env.DB.batch([
      env.DB.prepare(`DELETE FROM posts WHERE id = ? AND status = 'draft'`).bind(id),
      env.DB.prepare('UPDATE media SET delete_after = ?, post_id = NULL WHERE post_id = ?').bind(t, id),
    ]);
    return { id, deleted: true };
  }
  if (row.status !== 'queued') throw new HttpError(409, 'Only posts that have not started can be cancelled');
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET status = 'cancelled', updated_at = ? WHERE id = ? AND status = 'queued'`).bind(t, id),
    env.DB.prepare('UPDATE media SET delete_after = ? WHERE post_id = ?').bind(t + KEEP_AFTER_DONE, id),
  ]);
  return postJson(env, await loadPost(env, w, id));
}

export async function retryPost(env, w, id) {
  const row = await loadPost(env, w, id);
  if (row.status !== 'failed') throw new HttpError(409, 'Only failed posts can be retried');
  if (row.publish_id !== null) {
    throw new HttpError(409, 'This post may already have been published. Check the profile, then use Edit to post it again.');
  }
  const keys = JSON.parse(row.image_keys);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM media WHERE post_id = ?').bind(id).first();
  if (n !== keys.length) throw new HttpError(409, 'The images for this post were already deleted. Create it again.');
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET status = 'queued', attempts = 0, next_attempt_at = ?, fail_reason = NULL,
        publish_id = NULL, notified = 0, updated_at = ? WHERE id = ?`).bind(t, t, id),
    env.DB.prepare('UPDATE media SET delete_after = NULL WHERE post_id = ?').bind(id),
  ]);
  return postJson(env, await loadPost(env, w, id));
}

export async function listDrafts(env, w) {
  const sc = inScope(w, 'a.brand_id');
  const { results } = await env.DB.prepare(`SELECT p.*, a.username, a.platform FROM posts p JOIN accounts a ON a.id = p.account_id
      WHERE p.workspace_id = ? AND p.status = 'draft'${sc.sql} ORDER BY p.updated_at DESC LIMIT 200`)
    .bind(wsOf(w), ...sc.binds).all();
  return results.map(r => postJson(env, r));
}

// Quick edit of a post that has not started: caption, title or time. The
// update is conditional on the status, so a post the cron has just claimed is
// never changed under it.
export async function updatePost(env, w, id, body) {
  const row = await loadPost(env, w, id);
  if (!['queued', 'draft'].includes(row.status)) throw new HttpError(409, 'That post has already started or finished');
  const merged = { account_id: row.account_id, image_keys: JSON.parse(row.image_keys), cover_index: row.cover_index,
    settings: JSON.parse(row.settings), title: body?.title ?? row.title, caption: body?.caption ?? row.caption,
    scheduled_at: body?.scheduled_at === undefined ? (row.status === 'draft' ? null : row.scheduled_at) : body.scheduled_at };
  const t = now();
  // Keeping a scheduled time that is already close is fine; a new one must be ahead.
  const keepsTime = body?.scheduled_at === undefined;
  const p = validatePost(keepsTime ? { ...merged, scheduled_at: null } : merged, t, row.platform, { draft: row.status === 'draft' });
  const at = keepsTime ? row.scheduled_at : p.scheduled_at;
  const r = await env.DB.prepare(`UPDATE posts SET title = ?, caption = ?, scheduled_at = ?, next_attempt_at = ?, updated_at = ?
      WHERE id = ? AND workspace_id = ? AND status = ?`)
    .bind(p.title, p.caption, at, at, t, id, wsOf(w), row.status).run();
  if (!r.meta.changes) throw new HttpError(409, 'That post has just started publishing, so it cannot be edited');
  return postJson(env, await loadPost(env, w, id));
}
