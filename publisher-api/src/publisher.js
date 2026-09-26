import { now } from './http.js';
import { accessTokenFor } from './accounts.js';
import { buildPhotoBody } from './tiktok.js';
import { mediaUrl } from './media.js';
import { RETRY_DELAYS, PER_ACCOUNT_PER_TICK, KEEP_AFTER_DONE, PUBLISH_TIMEOUT } from './limits.js';

const STUCK_AFTER = 600;

export async function claimDue(env, t, limit = 25) {
  const { results } = await env.DB.prepare(`UPDATE posts SET status = 'publishing', updated_at = ?
      WHERE status = 'queued' AND id IN (SELECT id FROM posts WHERE status = 'queued' AND next_attempt_at <= ?
        ORDER BY next_attempt_at LIMIT ?)
      RETURNING *`).bind(t, t, limit).all();
  return results;
}

async function finish(env, id, t, fields) {
  const sets = Object.keys(fields).map(k => `${k} = ?`).join(', ');
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET ${sets}, updated_at = ? WHERE id = ?`).bind(...Object.values(fields), t, id),
    env.DB.prepare('UPDATE media SET delete_after = ? WHERE post_id = ?').bind(t + KEEP_AFTER_DONE, id),
  ]);
}
const fail = (env, id, t, reason) => finish(env, id, t, { status: 'failed', fail_reason: reason });

// One access token per account per tick; a failure is remembered so the
// account's other posts fail the same way without another refresh.
function tokenCache(env, tk) {
  const cache = new Map();
  return async accountId => {
    if (!cache.has(accountId)) {
      cache.set(accountId, (async () => {
        const account = await env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
        if (!account) { const e = new Error('Account disconnected'); e.code = 'gone'; throw e; }
        return accessTokenFor(env, tk, account);
      })());
    }
    return cache.get(accountId);
  };
}

async function start(env, tk, post, token, t) {
  const settings = JSON.parse(post.settings);
  try {
    const access = await token(post.account_id);
    const info = await tk.creatorInfo(access);
    if (!(info.privacy_level_options || []).includes(settings.privacy_level)) {
      await fail(env, post.id, t, `"${settings.privacy_level}" is no longer available for this account. Edit the post and choose again.`);
      return 'failed';
    }
    if (settings.branded_content && settings.privacy_level === 'SELF_ONLY') {
      await fail(env, post.id, t, 'Branded content cannot be posted as Only me');
      return 'failed';
    }
    const keys = JSON.parse(post.image_keys);
    const { publish_id } = await tk.initPhoto(access, buildPhotoBody({
      title: post.title, caption: post.caption, coverIndex: post.cover_index, settings,
      imageUrls: keys.map(k => mediaUrl(env, k)),
    }));
    await env.DB.prepare(`UPDATE posts SET publish_id = ?, attempts = attempts + 1, fail_reason = NULL, updated_at = ?
        WHERE id = ?`).bind(publish_id, t, post.id).run();
    return 'started';
  } catch (err) {
    if (err.code === 'needs_reconnect') {
      await fail(env, post.id, t, 'Reconnect this account');
      const { results } = await env.DB.prepare(`SELECT id FROM posts WHERE account_id = ? AND status = 'queued'`)
        .bind(post.account_id).all();
      for (const r of results) await fail(env, r.id, t, 'Reconnect this account');
      return 'failed';
    }
    if (err.transient && post.attempts < RETRY_DELAYS.length) {
      await env.DB.prepare(`UPDATE posts SET status = 'queued', attempts = attempts + 1, next_attempt_at = ?,
          fail_reason = ?, updated_at = ? WHERE id = ?`)
        .bind(t + RETRY_DELAYS[post.attempts], `Retrying: ${err.message}`, t, post.id).run();
      return 'requeued';
    }
    await fail(env, post.id, t, err.message || 'Publishing failed');
    return 'failed';
  }
}

async function poll(env, tk, post, token, t) {
  try {
    const s = await tk.status(await token(post.account_id), post.publish_id);
    if (s.status === 'PUBLISH_COMPLETE') {
      const ids = s.publicaly_available_post_id || [];
      await finish(env, post.id, t, { status: 'published', public_post_id: ids[0] ? String(ids[0]) : null });
      return 'published';
    }
    if (s.status === 'FAILED') {
      await fail(env, post.id, t, `TikTok rejected the post: ${s.fail_reason || 'no reason given'}`);
      return 'failed';
    }
  } catch (err) {
    if (!err.transient) { await fail(env, post.id, t, err.message); return 'failed'; }
  }
  if (t - post.updated_at > PUBLISH_TIMEOUT) {
    await fail(env, post.id, t, 'TikTok did not confirm the post within an hour. Check the profile before retrying.');
    return 'failed';
  }
  return 'pending';
}

export async function tick(env, tk, t = now()) {
  const counts = { started: 0, published: 0, failed: 0, requeued: 0 };
  const token = tokenCache(env, tk);

  // Recover posts claimed by a tick that died before sending content/init.
  await env.DB.prepare(`UPDATE posts SET status = 'queued', updated_at = ?
      WHERE status = 'publishing' AND publish_id IS NULL AND updated_at < ?`).bind(t, t - STUCK_AFTER).run();

  const claimed = await claimDue(env, t);
  const perAccount = new Map();
  for (const p of claimed) {
    const n = perAccount.get(p.account_id) || 0;
    if (n >= PER_ACCOUNT_PER_TICK) {
      await env.DB.prepare(`UPDATE posts SET status = 'queued', updated_at = ? WHERE id = ?`).bind(t, p.id).run();
      continue;
    }
    perAccount.set(p.account_id, n + 1);
    const r = await start(env, tk, p, token, t);
    if (r === 'started') counts.started++; else counts[r]++;
  }

  const { results: publishing } = await env.DB.prepare(`SELECT * FROM posts
      WHERE status = 'publishing' AND publish_id IS NOT NULL ORDER BY updated_at LIMIT 25`).all();
  for (const p of publishing) {
    const r = await poll(env, tk, p, token, t);
    if (r === 'published') counts.published++;
    else if (r === 'failed') counts.failed++;
  }
  return counts;
}
