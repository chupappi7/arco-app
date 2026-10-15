import { now } from './http.js';
import { accessTokenFor, forgetAccessToken, isMeta } from './accounts.js';
import { metaFor } from './meta.js';
import { buildPhotoBody } from './tiktok.js';
import { mediaUrl } from './media.js';
import { RETRY_DELAYS, PER_ACCOUNT_PER_TICK, KEEP_AFTER_DONE, PUBLISH_TIMEOUT,
  TICK_FETCH_BUDGET, POLL_RESERVE } from './limits.js';

const STUCK_AFTER = 600;
// publish_id = '' marks a content/init call in flight: TikTok may have
// accepted it even if we never heard back, so such a post is never resent.
const IN_FLIGHT = '';
const UNKNOWN = 'The publish request may have reached TikTok, but no answer came back. Check the profile before posting it again.';

// Fair across workspaces: at most PER_WORKSPACE_PER_TICK posts from any one
// workspace per tick, so one account manager queueing 200 posts for nine
// o'clock does not hold everyone else's nine o'clock post behind them.
const PER_WORKSPACE_PER_TICK = 5;
export async function claimDue(env, t, limit = 25) {
  const { results } = await env.DB.prepare(`UPDATE posts SET status = 'publishing', updated_at = ?
      WHERE status = 'queued' AND id IN (
        SELECT id FROM (SELECT id, next_attempt_at,
            ROW_NUMBER() OVER (PARTITION BY workspace_id ORDER BY next_attempt_at, id) AS rn
          FROM posts WHERE status = 'queued' AND next_attempt_at <= ?)
        WHERE rn <= ? ORDER BY next_attempt_at LIMIT ?)
      RETURNING *`).bind(t, t, PER_WORKSPACE_PER_TICK, limit).all();
  return results.sort((a, b) => a.next_attempt_at - b.next_attempt_at);
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
  const load = accountId => {
    if (!cache.has(accountId)) {
      cache.set(accountId, (async () => {
        const account = await env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
        if (!account) { const e = new Error('Account disconnected'); e.code = 'gone'; throw e; }
        return { account, access: await accessTokenFor(env, tk, account) };
      })());
    }
    return cache.get(accountId);
  };
  const token = async accountId => (await load(accountId)).access;
  token.load = load;
  return token;
}

// ---- Instagram and Facebook -------------------------------------------
//
// publish_id carries where a Meta post is: 'ig:<container>' is built and
// waiting for Instagram to process it, 'ig-pub:<container>' is being
// published right now (claimed, so it is published once), and '' is a
// Facebook post in flight. Containers that never get published are harmless,
// so everything before the publish call is safe to retry.

const IG_WAIT = 'ig:', IG_PUBLISHING = 'ig-pub:';
const igMark = (env, id, from, to, t) => env.DB.prepare(
  'UPDATE posts SET publish_id = ?, updated_at = ? WHERE id = ? AND publish_id = ?').bind(to, t, id, from).run();

async function metaLost(env, post, t) {
  await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(post.account_id).run();
  const msg = 'Reconnect this account';
  await fail(env, post.id, t, msg);
  const { results } = await env.DB.prepare(`SELECT id FROM posts WHERE account_id = ? AND status = 'queued'`)
    .bind(post.account_id).all();
  for (const r of results) await fail(env, r.id, t, msg);
  return 'failed';
}

async function requeueOrFail(env, post, t, err) {
  if (err.transient && post.attempts < RETRY_DELAYS.length) {
    await env.DB.prepare(`UPDATE posts SET status = 'queued', publish_id = NULL, next_attempt_at = ?,
        fail_reason = ?, updated_at = ? WHERE id = ?`)
      .bind(t + RETRY_DELAYS[post.attempts], `Retrying: ${err.message}`, t, post.id).run();
    return 'requeued';
  }
  await finish(env, post.id, t, { status: 'failed', publish_id: null, fail_reason: err.message || 'Publishing failed' });
  return 'failed';
}

async function startMeta(env, post, account, access, t) {
  const mt = metaFor(env);
  const urls = JSON.parse(post.image_keys).map(k => mediaUrl(env, k));
  const target = account.open_id.slice(3);   // strip 'ig:' / 'fb:'
  let sent = false;
  try {
    if (account.platform === 'instagram') {
      let container;
      if (urls.length === 1) container = (await mt.igImage(access, target, urls[0], { caption: post.caption })).id;
      else {
        const children = [];
        for (const u of urls) children.push((await mt.igImage(access, target, u, { carouselItem: true })).id);
        container = (await mt.igCarousel(access, target, children, post.caption)).id;
      }
      await env.DB.prepare('UPDATE posts SET publish_id = ?, fail_reason = NULL, updated_at = ? WHERE id = ?')
        .bind(IG_WAIT + container, t, post.id).run();
      return 'started';
    }
    // Facebook: upload unpublished photos (safe to repeat), then one post.
    const message = post.caption;
    let ids = [];
    if (urls.length > 1) for (const u of urls) ids.push((await mt.fbPhoto(access, target, u, { published: false })).id);
    await env.DB.prepare('UPDATE posts SET publish_id = ?, updated_at = ? WHERE id = ?').bind(IN_FLIGHT, t, post.id).run();
    sent = true;
    const out = urls.length === 1
      ? await mt.fbPhoto(access, target, urls[0], { published: true, caption: message })
      : await mt.fbFeed(access, target, message, ids);
    const postId = out.post_id || out.id;
    await finish(env, post.id, t, { status: 'published', publish_id: String(postId), public_post_id: String(postId),
      post_url: `https://www.facebook.com/${postId}`, fail_reason: null });
    return 'published';
  } catch (err) {
    if (err.code === 'needs_reconnect') return metaLost(env, post, t);
    // A dropped connection after the post call may still have posted.
    if (sent && err.code === 'network') { await fail(env, post.id, t, UNKNOWN); return 'failed'; }
    return requeueOrFail(env, post, t, err);
  }
}

async function pollInstagram(env, post, access, t) {
  const mt = metaFor(env);
  const account = await env.DB.prepare('SELECT open_id FROM accounts WHERE id = ?').bind(post.account_id).first();
  if (post.publish_id.startsWith(IG_PUBLISHING)) {
    // Another run is publishing it; if that run died, nobody knows whether it went out.
    if (t - post.updated_at > STUCK_AFTER) { await fail(env, post.id, t, UNKNOWN); return 'failed'; }
    return 'pending';
  }
  const container = post.publish_id.slice(IG_WAIT.length);
  try {
    const s = await mt.igContainerStatus(access, container);
    if (s.status_code === 'ERROR' || s.status_code === 'EXPIRED') {
      await finish(env, post.id, t, { status: 'failed', publish_id: null,
        fail_reason: `Instagram could not process the images: ${s.status || s.status_code}` });
      return 'failed';
    }
    if (s.status_code !== 'FINISHED') {
      if (t - post.updated_at > PUBLISH_TIMEOUT) {
        await finish(env, post.id, t, { status: 'failed', publish_id: null, fail_reason: 'Instagram did not finish processing the images within an hour.' });
        return 'failed';
      }
      return 'pending';
    }
  } catch (err) {
    if (err.code === 'needs_reconnect') return metaLost(env, post, t);
    return 'pending';
  }
  const claim = await igMark(env, post.id, post.publish_id, IG_PUBLISHING + container, t);
  if (!claim.meta.changes) return 'pending';
  let out;
  try {
    out = await mt.igPublish(access, account.open_id.slice(3), container);
  } catch (err) {
    if (err.code === 'needs_reconnect') return metaLost(env, post, t);
    if (err.code === 'network') { await fail(env, post.id, t, UNKNOWN); return 'failed'; }
    // Instagram answered with an error, so nothing went live.
    if (err.transient) { await igMark(env, post.id, IG_PUBLISHING + container, post.publish_id, t); return 'pending'; }
    await finish(env, post.id, t, { status: 'failed', publish_id: null, fail_reason: err.message });
    return 'failed';
  }
  const link = await mt.igPermalink(access, out.id).catch(() => ({}));
  await finish(env, post.id, t, { status: 'published', publish_id: String(out.id), public_post_id: String(out.id),
    post_url: link.permalink || null, fail_reason: null });
  return 'published';
}

async function start(env, tk, post, token, t) {
  const settings = JSON.parse(post.settings);
  await env.DB.prepare('UPDATE posts SET attempts = attempts + 1, updated_at = ? WHERE id = ?').bind(t, post.id).run();
  // A TikTok load failure is not handled here: token() below rejects with
  // the same cached error, and the TikTok path knows what each one means.
  const loaded = await token.load(post.account_id).catch(() => null);
  if (loaded && isMeta(loaded.account)) return startMeta(env, post, loaded.account, loaded.access, t);
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
  if (post.publish_id.startsWith(IG_WAIT) || post.publish_id.startsWith(IG_PUBLISHING)) {
    let access;
    try { access = await token(post.account_id); }
    catch (err) { await fail(env, post.id, t, err.message || 'Account disconnected'); return 'failed'; }
    return pollInstagram(env, post, access, t);
  }
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

// Outbound calls a start makes: TikTok refresh + creator info + init; for
// Instagram and Facebook one per image plus the carousel or the post.
async function startCost(env, post, token) {
  const loaded = await token.load(post.account_id).catch(() => null);
  if (!loaded || !isMeta(loaded.account)) return 3;
  const n = JSON.parse(post.image_keys).length;
  return n === 1 ? 1 : n + 1;
}

export async function tick(env, tk, t = now()) {
  const counts = { started: 0, published: 0, failed: 0, requeued: 0, calls: 0 };
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
  let budget = TICK_FETCH_BUDGET - POLL_RESERVE;
  for (const p of claimed) {
    const n = perAccount.get(p.account_id) || 0;
    const cost = await startCost(env, p, token);
    // A post bigger than the whole budget (a 35-photo Facebook post) still
    // goes out, alone, on a tick where nothing else has started.
    const fits = cost <= budget || budget === TICK_FETCH_BUDGET - POLL_RESERVE;
    if (n >= PER_ACCOUNT_PER_TICK || !fits) {
      await env.DB.prepare(`UPDATE posts SET status = 'queued', updated_at = ? WHERE id = ?`).bind(t, p.id).run();
      continue;
    }
    perAccount.set(p.account_id, n + 1);
    budget = Math.max(0, budget - cost);
    counts.calls += cost;
    const r = await start(env, tk, p, token, t);
    if (r === 'started') counts.started++; else counts[r]++;
  }

  const { results: publishing } = await env.DB.prepare(`SELECT * FROM posts
      WHERE status = 'publishing' AND publish_id IS NOT NULL AND publish_id != '' ORDER BY updated_at LIMIT 25`).all();
  budget += POLL_RESERVE;
  for (const p of publishing) {
    // An Instagram poll may also publish and fetch the link; TikTok's is one call.
    const cost = p.publish_id.startsWith(IG_WAIT) ? 3 : 1;
    if (cost > budget) break;
    budget -= cost;
    counts.calls += cost;
    const r = await poll(env, tk, p, token, t);
    if (r === 'published') counts.published++;
    else if (r === 'failed') counts.failed++;
  }
  return counts;
}

// "Post now": start one post as soon as it is created and watch TikTok for a
// short while, instead of waiting up to two cron ticks. Claiming uses the
// same guarded UPDATE as the cron, so the two can never both send a post.
export async function publishNow(env, tk, id, { sleep = ms => new Promise(r => setTimeout(r, ms)),
    now: clock = now, rounds = 8, every = 3000 } = {}) {
  const t = clock();
  const claimed = await env.DB.prepare(`UPDATE posts SET status = 'publishing', updated_at = ?
      WHERE id = ? AND status = 'queued' AND next_attempt_at <= ? RETURNING *`).bind(t, id, t).first();
  if (!claimed) return 'skipped';
  const token = tokenCache(env, tk);
  const r = await start(env, tk, claimed, token, t);
  if (r !== 'started') return r;
  for (let n = 0; n < rounds; n++) {
    const p = await env.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(id).first();
    const s = await poll(env, tk, p, token, clock());
    if (s !== 'pending') return s;
    if (n < rounds - 1) await sleep(every);
  }
  return 'pending';
}
