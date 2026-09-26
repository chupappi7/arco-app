import { now } from './http.js';
import { accessTokenFor, forgetAccessToken } from './accounts.js';
import { buildPhotoBody } from './tiktok.js';
import { mediaUrl } from './media.js';
import { RETRY_DELAYS, PER_ACCOUNT_PER_TICK, KEEP_AFTER_DONE, PUBLISH_TIMEOUT } from './limits.js';

const STUCK_AFTER = 600;
// publish_id = '' marks a content/init call in flight: TikTok may have
// accepted it even if we never heard back, so such a post is never resent.
const IN_FLIGHT = '';
const UNKNOWN = 'The publish request may have reached TikTok, but no answer came back. Check the profile before posting it again.';

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
  await env.DB.prepare('UPDATE posts SET attempts = attempts + 1, updated_at = ? WHERE id = ?').bind(t, post.id).run();
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
    await env.DB.prepare('UPDATE posts SET publish_id = ?, updated_at = ? WHERE id = ?').bind(IN_FLIGHT, t, post.id).run();
    const { publish_id } = await tk.initPhoto(access, buildPhotoBody({
      title: post.title, caption: post.caption, coverIndex: post.cover_index, settings,
      imageUrls: keys.map(k => mediaUrl(env, k)),
    }));
    await env.DB.prepare(`UPDATE posts SET publish_id = ?, fail_reason = NULL, updated_at = ? WHERE id = ?`)
      .bind(publish_id, t, post.id).run();
    return 'started';
  } catch (err) {
    if (err.code === 'needs_reconnect') {
      await forgetAccessToken(env, post.account_id);
      const acc = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id = ?').bind(post.account_id).first();
      // Only a failed refresh proves the grant is gone. A cached access token
      // TikTok rejected is retried once with a freshly refreshed one.
      if (acc && !acc.needs_reconnect && post.attempts < RETRY_DELAYS.length) {
        await env.DB.prepare(`UPDATE posts SET status = 'queued', publish_id = NULL, next_attempt_at = ?,
            fail_reason = ?, updated_at = ? WHERE id = ?`)
          .bind(t + RETRY_DELAYS[post.attempts], 'Retrying with a fresh TikTok token', t, post.id).run();
        return 'requeued';
      }
      await fail(env, post.id, t, 'Reconnect this account');
      const { results } = await env.DB.prepare(`SELECT id FROM posts WHERE account_id = ? AND status = 'queued'`)
        .bind(post.account_id).all();
      for (const r of results) await fail(env, r.id, t, 'Reconnect this account');
      return 'failed';
    }
    if (err.transient && post.attempts < RETRY_DELAYS.length) {
      // A transient error means TikTok refused or never got the request, so
      // clearing the in-flight mark and trying again cannot double-post.
      await env.DB.prepare(`UPDATE posts SET status = 'queued', publish_id = NULL, next_attempt_at = ?,
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
      // A definite rejection: nothing went live, so Retry is safe.
      await finish(env, post.id, t, { status: 'failed', publish_id: null,
        fail_reason: `TikTok rejected the post: ${s.fail_reason || 'no reason given'}` });
      return 'failed';
    }
  } catch (err) {
    // Only a lost account ends polling early; anything else is retried on the
    // next tick until the timeout below.
    if (err.code === 'needs_reconnect') {
      await forgetAccessToken(env, post.account_id);
      await fail(env, post.id, t, 'Lost access to this account while TikTok was processing the post. ' +
        'Check the profile before posting it again.');
      return 'failed';
    }
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

  // Recover posts left by a tick that died. Not yet sent: safe to queue again.
  // Sent but unanswered: fail, because resending could post it twice.
  await env.DB.prepare(`UPDATE posts SET status = 'queued', updated_at = ?
      WHERE status = 'publishing' AND publish_id IS NULL AND updated_at < ?`).bind(t, t - STUCK_AFTER).run();
  const { results: lost } = await env.DB.prepare(`SELECT id FROM posts
      WHERE status = 'publishing' AND publish_id = ? AND updated_at < ?`).bind(IN_FLIGHT, t - STUCK_AFTER).all();
  for (const r of lost) { await fail(env, r.id, t, UNKNOWN); counts.failed++; }

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
      WHERE status = 'publishing' AND publish_id IS NOT NULL AND publish_id != '' ORDER BY updated_at LIMIT 25`).all();
  for (const p of publishing) {
    const r = await poll(env, tk, p, token, t);
    if (r === 'published') counts.published++;
    else if (r === 'failed') counts.failed++;
  }
  return counts;
}
