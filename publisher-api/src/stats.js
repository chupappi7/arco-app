// Numbers from the platforms. The cron reads a few posts and accounts each
// minute with whatever outbound calls publishing left over: a post is read
// every 3 hours for its first 3 days, then daily until it is 30 days old;
// an account's followers every 6 hours, kept one row per day for trends.
//
// TikTok needs user.info.stats and video.list. Accounts connected before
// those scopes were requested lack them until they reconnect; such an account
// is left alone for a week at a time, the way Instagram insights are.

import { now, HttpError } from './http.js';
import { accessTokenFor } from './accounts.js';
import { wsOf, inScope } from './scope.js';
import { postJson } from './posts.js';

const DAY = 86400;
export const FOLLOW_FOR = 30 * DAY;
const YOUNG = 3 * DAY;
const YOUNG_EVERY = 3 * 3600;
const ACCOUNT_EVERY = 6 * 3600;
const INSIGHTS_RETRY = 7 * DAY;
export const STATS_PER_TICK = 6;

const utcDay = t => new Date(t * 1000).toISOString().slice(0, 10);
const count = v => (Number.isFinite(Number(v)) ? Number(v) : 0);
// Graph says "no permission" as code 10, 200-299, or a 100 about permissions.
const denied = err => /^(10|2\d\d)$/.test(String(err.code)) || err.code === 'scope_not_authorized'
  || /permission|scope/i.test(err.message || '');
const resting = (a, t) => a.insights_denied_at && a.insights_denied_at > t - INSIGHTS_RETRY;
async function rest(env, account, t) {
  await env.DB.prepare('UPDATE accounts SET insights_denied_at = ? WHERE id = ?').bind(t, account.id).run();
  account.insights_denied_at = t;
}

async function markReconnect(env, accountId) {
  await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(accountId).run();
}

// Instagram: likes and comments always; views, reach, saves and shares when the
// token has the insights permission. Without it, the account is not asked
// again for a week, so each read stays one call.
async function readInstagram(env, mt, token, post, account, t) {
  const tryInsights = !account.insights_denied_at || account.insights_denied_at < t - INSIGHTS_RETRY;
  let r;
  try {
    r = await mt.igMediaStats(token, post.public_post_id, { insights: tryInsights });
    if (tryInsights && account.insights_denied_at) {
      await env.DB.prepare('UPDATE accounts SET insights_denied_at = NULL WHERE id = ?').bind(account.id).run();
      account.insights_denied_at = null;
    }
  } catch (err) {
    // Without insights the basic counts may still work (an unsupported
    // metric fails the whole call too).
    if (!tryInsights || err.code === 'needs_reconnect' || err.transient) throw err;
    if (denied(err)) {
      await env.DB.prepare('UPDATE accounts SET insights_denied_at = ? WHERE id = ?').bind(t, account.id).run();
      account.insights_denied_at = t;
    }
    r = await mt.igMediaStats(token, post.public_post_id);
  }
  const s = { likes: count(r.like_count), comments: count(r.comments_count) };
  for (const m of r.insights?.data || []) {
    const v = m.values?.[0]?.value ?? m.total_value?.value;
    const key = { views: 'views', reach: 'reach', saved: 'saves', shares: 'shares' }[m.name];
    if (key && v !== undefined) s[key] = count(v);
  }
  return s;
}

// Without pages_read_user_content Facebook refuses to read the post at all;
// the account is then left alone for a week, like Instagram insights.
async function readFacebook(env, mt, token, post, account, t) {
  if (account.insights_denied_at && account.insights_denied_at > t - INSIGHTS_RETRY) return null;
  let r;
  try { r = await mt.fbPostStats(token, post.public_post_id); }
  catch (err) {
    if (!denied(err)) throw err;
    await env.DB.prepare('UPDATE accounts SET insights_denied_at = ? WHERE id = ?').bind(t, account.id).run();
    account.insights_denied_at = t;
    return null;
  }
  return { likes: count(r.reactions?.summary?.total_count), comments: count(r.comments?.summary?.total_count),
    shares: count(r.shares?.count) };
}

export async function refreshStats(env, mt, tk, t = now(), budget = STATS_PER_TICK) {
  const done = { posts: 0, accounts: 0 };
  if (budget <= 0) return done;
  const accounts = new Map();
  const load = async id => {
    if (!accounts.has(id)) {
      accounts.set(id, (async () => {
        const account = await env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(id).first();
        return { account, token: await accessTokenFor(env, tk, account) };
      })());
    }
    return accounts.get(id);
  };

  // Accounts first, but at most a third of the budget, so posts keep moving.
  const accountBudget = Math.max(1, Math.floor(budget / 3));
  const { results: accs } = await env.DB.prepare(`SELECT id, platform, open_id, insights_denied_at FROM accounts
      WHERE needs_reconnect = 0 AND (stats_at IS NULL OR stats_at < ?)
        AND (platform != 'tiktok' OR insights_denied_at IS NULL OR insights_denied_at < ?)
      ORDER BY COALESCE(stats_at, 0) LIMIT ?`).bind(t - ACCOUNT_EVERY, t - INSIGHTS_RETRY, accountBudget).all();
  for (const a of accs) {
    budget--;
    try {
      const { token } = await load(a.id);
      let r;
      if (a.platform === 'tiktok') {
        try { r = await tk.userStats(token); }
        catch (err) { if (!denied(err)) throw err; await rest(env, a, t); continue; }
      } else r = a.platform === 'instagram' ? await mt.igAccountStats(token) : await mt.fbPageStats(token, a.open_id.slice(3));
      const followers = count(r.follower_count ?? r.followers_count ?? r.fan_count);
      await env.DB.batch([
        env.DB.prepare('UPDATE accounts SET followers = ?, stats_at = ? WHERE id = ?').bind(followers, t, a.id),
        env.DB.prepare(`INSERT INTO follower_history (account_id, day, followers) VALUES (?, ?, ?)
            ON CONFLICT (account_id, day) DO UPDATE SET followers = excluded.followers`).bind(a.id, utcDay(t), followers),
      ]);
      done.accounts++;
    } catch (err) {
      if (err.code === 'needs_reconnect') await markReconnect(env, a.id);
      // Anything else: try again next time, not every minute.
      else console.error('stats account', a.id, err.message), await env.DB.prepare('UPDATE accounts SET stats_at = ? WHERE id = ?').bind(t, a.id).run();
    }
  }

  if (budget <= 0) return done;
  const { results: posts } = await env.DB.prepare(`SELECT p.id, p.account_id, p.public_post_id, p.scheduled_at, a.platform
      FROM posts p JOIN accounts a ON a.id = p.account_id
      WHERE p.status = 'published' AND a.needs_reconnect = 0
        AND (a.platform != 'tiktok' OR a.insights_denied_at IS NULL OR a.insights_denied_at < ?)
        AND p.public_post_id IS NOT NULL AND p.scheduled_at > ?
        AND (p.stats_at IS NULL OR (p.scheduled_at > ? AND p.stats_at < ?) OR p.stats_at < ?)
      ORDER BY COALESCE(p.stats_at, 0), p.scheduled_at DESC LIMIT ?`)
    .bind(t - INSIGHTS_RETRY, t - FOLLOW_FOR, t - YOUNG, t - YOUNG_EVERY, t - DAY, budget).all();
  const save = (id, s) => env.DB.prepare('UPDATE posts SET stats = COALESCE(?, stats), stats_at = ? WHERE id = ?').bind(s ? JSON.stringify(s) : null, t, id).run();
  const ttByAccount = new Map();
  for (const p of posts.filter(x => x.platform === 'tiktok')) ttByAccount.set(p.account_id, [...(ttByAccount.get(p.account_id) || []), p]);
  for (const [accountId, list] of ttByAccount) {
    try {
      const { account, token } = await load(accountId);
      let videos;
      try { videos = await tk.videoStats(token, list.map(p => p.public_post_id)); }
      catch (err) { if (!denied(err)) throw err; await rest(env, account, t); continue; }
      const byId = new Map(videos.map(v => [String(v.id), v]));
      for (const p of list) {
        const v = byId.get(String(p.public_post_id));
        await save(p.id, v ? { views: count(v.view_count), likes: count(v.like_count), comments: count(v.comment_count), shares: count(v.share_count) } : null);
        if (v) done.posts++;
      }
    } catch (err) {
      if (err.code === 'needs_reconnect') await markReconnect(env, accountId);
      else { console.error('stats tiktok', accountId, err.message); for (const p of list) await save(p.id, null); }
    }
  }
  for (const p of posts.filter(x => x.platform !== 'tiktok')) {
    try {
      const { account, token } = await load(p.account_id);
      const s = account.platform === 'instagram' ? await readInstagram(env, mt, token, p, account, t) : await readFacebook(env, mt, token, p, account, t);
      await save(p.id, s);
      if (s) done.posts++;
    } catch (err) {
      if (err.code === 'needs_reconnect') await markReconnect(env, p.account_id);
      else {
        console.error('stats post', p.id, err.message);
        await env.DB.prepare('UPDATE posts SET stats_at = ? WHERE id = ?').bind(t, p.id).run();
      }
    }
  }
  return done;
}

const METRICS = ['views', 'reach', 'likes', 'comments', 'shares', 'saves'];

// GET /v1/stats?days=7|30|90&platform=all|tiktok|instagram|facebook: totals for
// posts published in the period, a day-by-day series for the charts, a
// breakdown per platform, the top posts, and followers per account with the
// change over the period. Limited to the caller's brands like everything else.
export const PERIODS = [7, 30, 90];
const PLATFORMS = ['tiktok', 'instagram', 'facebook'];
export async function getStats(env, w, days, t = now(), platform = 'all') {
  if (!PERIODS.includes(days)) throw new HttpError(400, 'days must be 7, 30 or 90');
  if (platform !== 'all' && !PLATFORMS.includes(platform)) throw new HttpError(400, 'unknown platform');
  const from = t - days * DAY;
  const pf = platform === 'all' ? { sql: '', binds: [] } : { sql: ' AND a.platform = ?', binds: [platform] };
  const sc = inScope(w, 'a.brand_id');
  const { results: rows } = await env.DB.prepare(`SELECT p.*, a.username, a.platform FROM posts p JOIN accounts a ON a.id = p.account_id
      WHERE p.workspace_id = ? AND p.status = 'published' AND p.scheduled_at >= ? AND p.scheduled_at <= ?${sc.sql}${pf.sql}
      ORDER BY p.scheduled_at DESC`).bind(wsOf(w), from, t, ...sc.binds, ...pf.binds).all();

  // One entry per UTC day of the period, oldest first.
  const dayKeys = [...Array(days)].map((_, i) => utcDay(t - (days - 1 - i) * DAY));
  const perDay = new Map(dayKeys.map(d => [d, { day: d, posts: 0, views: 0, engagement: 0, followers: null }]));

  const totals = Object.fromEntries(METRICS.map(m => [m, 0]));
  const has = new Set();
  const byPlatform = Object.fromEntries(PLATFORMS.map(pl => [pl, { platform: pl, posts: 0, views: null, likes: null, comments: null, shares: null, followers: null }]));
  let tracked = 0, updated = 0;
  const withStats = [];
  for (const r of rows) {
    const pl = r.platform || 'tiktok', d = perDay.get(utcDay(r.scheduled_at));
    byPlatform[pl].posts++;
    if (d) d.posts++;
    if (!r.stats) continue;
    const s = JSON.parse(r.stats);
    tracked++;
    updated = Math.max(updated, r.stats_at || 0);
    for (const m of METRICS) if (s[m] !== undefined) { totals[m] += s[m]; has.add(m); }
    for (const m of ['views', 'likes', 'comments', 'shares']) if (s[m] !== undefined) byPlatform[pl][m] = (byPlatform[pl][m] || 0) + s[m];
    if (d) { d.views += s.views || 0; d.engagement += (s.likes || 0) + (s.comments || 0) + (s.shares || 0) + (s.saves || 0); }
    withStats.push({ r, s, score: (s.views || 0) + 10 * ((s.likes || 0) + (s.comments || 0) + (s.shares || 0) + (s.saves || 0)) });
  }
  const top = withStats.sort((a, b) => b.score - a.score).slice(0, 6).map(x => postJson(env, x.r));

  const asc = inScope(w);
  const { results: all } = await env.DB.prepare(`SELECT id, username, platform, avatar_url, followers, stats_at, insights_denied_at FROM accounts
      WHERE workspace_id = ?${asc.sql} ORDER BY platform, username`).bind(wsOf(w), ...asc.binds).all();
  const startDay = dayKeys[0], today = dayKeys[days - 1];
  const accounts = [];
  for (const a of all) {
    if (platform !== 'all' && (a.platform || 'tiktok') !== platform) continue;
    let change = null;
    if (a.followers !== null) {
      const first = await env.DB.prepare(`SELECT day, followers FROM follower_history WHERE account_id = ? AND day >= ?
          ORDER BY day LIMIT 1`).bind(a.id, startDay).first();
      if (first && first.day < today) change = a.followers - first.followers;
    }
    accounts.push({ id: a.id, username: a.username, platform: a.platform || 'tiktok', avatar_url: a.avatar_url,
      followers: a.followers, change, updated_at: a.stats_at,
      limited: !!a.insights_denied_at && a.insights_denied_at > t - INSIGHTS_RETRY });
  }
  const known = accounts.filter(a => a.followers !== null);
  const changes = known.filter(a => a.change !== null);
  for (const a of known) byPlatform[a.platform].followers = (byPlatform[a.platform].followers || 0) + a.followers;

  // Followers per day: each account's last known count carried forward.
  if (known.length) {
    const marks = known.map(() => '?').join(',');
    const { results: hist } = await env.DB.prepare(`SELECT account_id, day, followers FROM follower_history
        WHERE account_id IN (${marks}) AND day <= ? ORDER BY day`).bind(...known.map(a => a.id), today).all();
    const last = new Map();
    let i = 0;
    for (const d of dayKeys) {
      while (i < hist.length && hist[i].day <= d) { last.set(hist[i].account_id, hist[i].followers); i++; }
      if (last.size) perDay.get(d).followers = [...last.values()].reduce((n, v) => n + v, 0);
    }
  }

  const flagsFrom = all.map(a => ({ platform: a.platform || 'tiktok', followers: a.followers, limited: !!a.insights_denied_at && a.insights_denied_at > t - INSIGHTS_RETRY }));
  return {
    days, platform, published: rows.length, tracked, updated_at: updated || null,
    totals: Object.fromEntries(METRICS.filter(m => has.has(m)).map(m => [m, totals[m]])),
    followers: { total: known.length ? known.reduce((n, a) => n + a.followers, 0) : null,
      change: changes.length ? changes.reduce((n, a) => n + a.change, 0) : null },
    series: [...perDay.values()],
    by_platform: PLATFORMS.map(pl => byPlatform[pl]).filter(x => all.some(a => (a.platform || 'tiktok') === x.platform)),
    platforms: PLATFORMS.filter(pl => all.some(a => (a.platform || 'tiktok') === pl)),
    accounts, top,
    tiktok_pending: flagsFrom.some(a => a.platform === 'tiktok' && a.followers === null && !a.limited),
    tiktok_reconnect: flagsFrom.some(a => a.platform === 'tiktok' && a.limited),
    facebook_limited: flagsFrom.some(a => a.platform === 'facebook' && a.limited),
  };
}
