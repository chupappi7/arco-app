// The bell. The cron looks at numbers the stats refresh already saved and
// writes one row per event; nothing here calls a platform. Each event has a
// key, so it fires once. Problems that fix themselves (0 views that start
// moving, an account reconnected, a queue refilled) are taken back.

import { now } from './http.js';
import { randomToken } from './crypto.js';
import { wsOf, inScope } from './scope.js';
import { warmup } from './warmup.js';

const DAY = 86400;
export const VIEW_MILESTONES = [1000, 10000, 100000, 1000000];
export const FOLLOWER_MILESTONES = [100, 1000, 10000, 100000];
export const ZERO_AFTER = 6 * 3600;
export const BREAKOUT = 3;
export const MAX_PER_RUN = 20;
export const NOTIFY_EVERY = 15 * 60;
const KEEP = 30 * DAY;

const PL = { tiktok: 'TikTok', instagram: 'Instagram', facebook: 'Facebook', youtube: 'YouTube', threads: 'Threads' };
const at = a => (a.platform === 'facebook' ? '' : '@') + (a.username || a.display_name || 'account');
const big = n => n >= 1e6 ? `${+(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${+(n / 1e3).toFixed(1)}K` : String(n);
const top = (list, v) => list.filter(m => v >= m).pop();
const median = v => { const s = [...v].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : null; };
const dayOf = t => new Date(t * 1000).toISOString().slice(0, 10);

// Everything the rules can see, per workspace, in a few queries.
async function facts(env, t) {
  const { results: posts } = await env.DB.prepare(`SELECT p.id, p.workspace_id, p.account_id, p.status, p.scheduled_at, p.stats, p.stats_at, p.post_url,
      a.brand_id, a.platform, a.username, a.display_name, a.connected_at
      FROM posts p JOIN accounts a ON a.id = p.account_id
      WHERE p.scheduled_at > ? AND p.status IN ('published', 'failed', 'queued')`).bind(t - 30 * DAY).all();
  const { results: accounts } = await env.DB.prepare(`SELECT id, workspace_id, brand_id, platform, username, display_name, followers, needs_reconnect, connected_at FROM accounts`).all();
  const { results: hist } = await env.DB.prepare(`SELECT account_id, MIN(followers) AS low FROM follower_history WHERE day >= ? GROUP BY account_id`).bind(dayOf(t - 8 * DAY)).all();
  const { results: comps } = await env.DB.prepare(`SELECT id, workspace_id, brand_id, title, handle, recent FROM competitors WHERE recent IS NOT NULL`).all().catch(() => ({ results: [] }));
  const { results: firsts } = await env.DB.prepare(`SELECT account_id, MIN(scheduled_at) AS first, COUNT(*) AS n FROM posts WHERE status = 'published' GROUP BY account_id`).all();
  for (const p of posts) p.s = p.stats ? JSON.parse(p.stats) : null;
  return { posts, accounts, low: new Map(hist.map(h => [h.account_id, h.low])), comps, first: new Map(firsts.map(f => [f.account_id, f.first])),
    published: new Map(firsts.map(f => [f.account_id, f.n])) };
}

// What should exist now: [{ ws, brand, key, kind, tone, title, body, post, account, url }].
export function rules(f, t) {
  const out = [], acc = new Map(f.accounts.map(a => [a.id, a]));
  const add = (a, n) => out.push({ ws: a.workspace_id, brand: a.brand_id ?? null, account: a.id ?? null, ...n });
  const pub = f.posts.filter(p => p.status === 'published');

  // Views milestones, only the highest one passed.
  for (const p of pub) {
    const v = p.s?.views, m = v == null ? null : top(VIEW_MILESTONES, v);
    if (m) add({ ...p, id: p.account_id }, { key: `views:${p.id}:${m}`, kind: 'views', tone: 'win', post: p.id,
      title: `A post passed ${big(m)} views`, body: null });
  }
  // Breakouts: far above the account's usual, in the last week.
  const byAcct = {};
  for (const p of pub) if (p.s?.views != null) (byAcct[p.account_id] ||= []).push(p.s.views);
  for (const p of pub) {
    const all = byAcct[p.account_id] || [], u = all.length >= 5 ? median(all) : null, v = p.s?.views;
    if (u && v >= 500 && v >= BREAKOUT * u && p.scheduled_at > t - 7 * DAY) add({ ...p, id: p.account_id }, { key: `breakout:${p.id}`, kind: 'breakout', tone: 'win', post: p.id,
      title: `Breakout: ${big(v)} views`, body: `${(v / u).toFixed(1)}× what this account usually gets. Post it again on another account.` });
  }
  // Follower milestones crossed in the last week (not ones the account already had).
  for (const a of f.accounts) {
    const m = a.followers == null ? null : top(FOLLOWER_MILESTONES, a.followers), low = f.low.get(a.id);
    if (m && low != null && low < m) add(a, { key: `followers:${a.id}:${m}`, kind: 'followers', tone: 'win',
      title: `${big(m)} followers`, body: `${big(a.followers)} now.` });
  }
  // A new account's first post going out.
  for (const a of f.accounts) {
    const first = f.first.get(a.id);
    if (first && first > t - 2 * DAY && a.connected_at > t - 30 * DAY) add(a, { key: `first:${a.id}`, kind: 'first', tone: 'win',
      title: 'First post is live', body: 'Views show in a few hours.' });
  }
  // Warm-up: a new account getting shown to people, or one that isn't.
  for (const a of f.accounts) {
    const mine = pub.filter(p => p.account_id === a.id).map(p => ({ scheduled_at: p.scheduled_at, views: p.s?.views, stats_at: p.stats_at }));
    const w = warmup({ connected_at: a.connected_at, published: f.published?.get(a.id) || 0, posts: mine }, t);
    if (w.stage === 'ready' && a.connected_at > t - 60 * DAY) add(a, { key: `warmup:${a.id}:ready`, kind: 'warmup', tone: 'win',
      title: `${at(a)} is warmed up`, body: `Last 5 posts: ${big(w.median)} views each, on the median.` });
    if (w.stage === 'stuck') add(a, { key: `warmstuck:${a.id}`, kind: 'warmstuck', tone: 'bad',
      title: `${at(a)} isn't getting shown yet`, body: w.next });
  }
  // Problems.
  const zero = {};
  for (const p of pub) if (p.s?.views === 0 && p.scheduled_at > t - 7 * DAY && (p.stats_at || 0) - p.scheduled_at >= ZERO_AFTER) (zero[p.account_id] ||= []).push(p);
  for (const [id, list] of Object.entries(zero)) {
    const a = acc.get(id); if (!a) continue;
    const latest = list.sort((x, y) => y.scheduled_at - x.scheduled_at)[0];
    add(a, { key: `zero:${latest.id}`, kind: 'zero', tone: 'bad', post: latest.id,
      title: list.length > 1 ? `${list.length} posts with 0 views` : 'A post with 0 views',
      body: `${PL[a.platform]} hasn't shown ${list.length > 1 ? 'them' : 'it'} to anyone yet. Common on new accounts or reused clips.` });
  }
  for (const p of f.posts) if (p.status === 'failed' && p.scheduled_at > t - 2 * DAY) add({ ...p, id: p.account_id }, { key: `failed:${p.id}`, kind: 'failed', tone: 'bad', post: p.id,
    title: 'A post failed', body: 'Tap to see why and post it again.' });
  for (const a of f.accounts) if (a.needs_reconnect) add(a, { key: `reconnect:${a.id}`, kind: 'reconnect', tone: 'bad',
    title: 'Reconnect this account', body: `${PL[a.platform]} access expired. Nothing posts here until you reconnect.` });
  // A brand that has been posting but has nothing in the next 24 hours.
  const brands = {};
  for (const a of f.accounts) if (a.brand_id) (brands[`${a.workspace_id}|${a.brand_id}`] ||= { ws: a.workspace_id, brand: a.brand_id, ids: new Set() }).ids.add(a.id);
  for (const b of Object.values(brands)) {
    const mine = f.posts.filter(p => b.ids.has(p.account_id));
    const recent = mine.some(p => p.status === 'published' && p.scheduled_at > t - 7 * DAY);
    const next = mine.some(p => p.status === 'queued' && p.scheduled_at > t && p.scheduled_at < t + DAY);
    if (recent && !next) out.push({ ws: b.ws, brand: b.brand, account: null, key: `empty:${b.brand}`, kind: 'empty', tone: 'bad',
      title: 'Nothing scheduled in the next 24 hours', body: 'You posted this week, but the queue is empty.' });
  }
  // Competitor breakouts: an idea to borrow.
  for (const c of f.comps) {
    const vids = JSON.parse(c.recent || '[]'), u = median(vids.map(v => v.views));
    for (const v of vids) if (u && v.views >= 1000 && v.views >= BREAKOUT * u && v.published_at > t - 7 * DAY)
      out.push({ ws: c.workspace_id, brand: c.brand_id, account: null, key: `cbreak:${v.id}`, kind: 'competitor', tone: 'info',
        url: `https://www.youtube.com/watch?v=${v.id}`, title: `${c.title} has a breakout`, body: `"${v.title}": ${big(v.views)} views, ${(v.views / u).toFixed(1)}× their usual.` });
  }
  return out;
}

const PROBLEM = ['zero', 'reconnect', 'empty', 'warmstuck'];

export async function runNotifications(env, t = now()) {
  const last = await env.DB.prepare(`SELECT seen_at FROM notification_seen WHERE workspace_id = '_cron' AND who = '_cron'`).first().catch(() => null);
  if (last && last.seen_at > t - NOTIFY_EVERY) return { made: 0, removed: 0 };
  await env.DB.prepare(`INSERT INTO notification_seen (workspace_id, who, seen_at) VALUES ('_cron', '_cron', ?)
      ON CONFLICT (workspace_id, who) DO UPDATE SET seen_at = excluded.seen_at`).bind(t).run();
  const want = rules(await facts(env, t), t);
  const { results: have } = await env.DB.prepare('SELECT id, workspace_id, key, kind, title, body FROM notifications').all();
  const haveKeys = new Set(have.map(h => `${h.workspace_id}|${h.key}`)), wantKeys = new Set(want.map(w => `${w.ws}|${w.key}`));
  // Take back problems that are no longer true.
  const gone = have.filter(h => PROBLEM.includes(h.kind) && !wantKeys.has(`${h.workspace_id}|${h.key}`));
  const perWs = {}, fresh = [];
  for (const w of want) {
    if (haveKeys.has(`${w.ws}|${w.key}`)) continue;
    if ((perWs[w.ws] = (perWs[w.ws] || 0) + 1) > MAX_PER_RUN) continue;
    fresh.push(w); haveKeys.add(`${w.ws}|${w.key}`);
  }
  // Keep the wording of rows that still hold up to date (a 0-view count grows).
  const byKey = new Map(have.map(h => [`${h.workspace_id}|${h.key}`, h]));
  const changed = want.map(w => [byKey.get(`${w.ws}|${w.key}`), w]).filter(([h, w]) => h && (h.title !== w.title || (h.body || null) !== (w.body || null)));
  const stmts = [
    ...changed.map(([h, w]) => env.DB.prepare('UPDATE notifications SET title = ?, body = ? WHERE id = ?').bind(w.title, w.body || null, h.id)),
    ...gone.map(h => env.DB.prepare('DELETE FROM notifications WHERE id = ?').bind(h.id)),
    ...fresh.map(w => env.DB.prepare(`INSERT OR IGNORE INTO notifications (id, workspace_id, brand_id, key, kind, tone, title, body, post_id, account_id, url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).bind('ntf_' + randomToken('', 8), w.ws, w.brand, w.key, w.kind, w.tone, w.title, w.body || null,
        w.post || null, w.account || null, w.url || null, t)),
    env.DB.prepare('DELETE FROM notifications WHERE created_at < ?').bind(t - KEEP),
  ];
  for (let i = 0; i < stmts.length; i += 50) await env.DB.batch(stmts.slice(i, i + 50));
  return { made: fresh.length, removed: gone.length };
}

const whoKey = w => (typeof w === 'string' ? 'ws' : w.userId || 'ws');

export async function listNotifications(env, w, brand = 'all') {
  const sc = inScope(w, 'brand_id');
  const bf = brand === 'all' ? { sql: '', binds: [] } : brand === 'none' ? { sql: ' AND brand_id IS NULL', binds: [] } : { sql: ' AND (brand_id = ? OR brand_id IS NULL)', binds: [brand] };
  const { results } = await env.DB.prepare(`SELECT * FROM notifications WHERE workspace_id = ?${sc.sql}${bf.sql} ORDER BY created_at DESC LIMIT 50`)
    .bind(wsOf(w), ...sc.binds, ...bf.binds).all();
  const seen = (await env.DB.prepare('SELECT seen_at FROM notification_seen WHERE workspace_id = ? AND who = ?').bind(wsOf(w), whoKey(w)).first())?.seen_at || 0;
  return { seen_at: seen, unread: results.filter(r => r.created_at > seen).length,
    items: results.map(r => ({ id: r.id, kind: r.kind, tone: r.tone, title: r.title, body: r.body, post_id: r.post_id, account_id: r.account_id,
      brand_id: r.brand_id, url: r.url, created_at: r.created_at, unread: r.created_at > seen })) };
}

export async function markSeen(env, w, t = now()) {
  await env.DB.prepare(`INSERT INTO notification_seen (workspace_id, who, seen_at) VALUES (?, ?, ?)
      ON CONFLICT (workspace_id, who) DO UPDATE SET seen_at = excluded.seen_at`).bind(wsOf(w), whoKey(w), t).run();
  return { ok: true, seen_at: t };
}
