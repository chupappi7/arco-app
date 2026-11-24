// Competitor channels: other people's YouTube channels, followed by their
// public numbers (subscribers, views, newest uploads). Reading them needs only
// GOOGLE_API_KEY, about 3 quota units per channel per refresh.

import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { wsOf, inScope, scopeOf } from './scope.js';
import { ytFor } from './youtube.js';

export const MAX_COMPETITORS = 30;
export const COMPETITOR_EVERY = 12 * 3600;
const PER_TICK = 2;
const bad = msg => { throw new HttpError(400, msg); };
const dayOf = t => new Date(t * 1000).toISOString().slice(0, 10);

// "@name", "name", a channel id, or a youtube.com link to either.
export function parseChannelRef(raw) {
  let s = String(raw || '').trim();
  if (!s) return null;
  try {
    if (/youtube\.com|youtu\.be/i.test(s)) {
      const u = new URL(/^https?:/i.test(s) ? s : 'https://' + s);
      const parts = u.pathname.split('/').filter(Boolean);
      if (parts[0]?.startsWith('@')) s = parts[0];
      else if (parts[0] === 'channel' && parts[1]) s = parts[1];
      else if ((parts[0] === 'c' || parts[0] === 'user') && parts[1]) s = '@' + parts[1];
      else return null;
    }
  } catch { return null; }
  if (/^UC[\w-]{22}$/.test(s)) return { id: s };
  const h = s.replace(/^@/, '');
  return /^[\w.\-·]{3,100}$/.test(h) ? { handle: h } : null;
}

const toJson = (r, change) => ({
  id: r.id, platform: r.platform, brand_id: r.brand_id, channel_id: r.channel_id, handle: r.handle, title: r.title,
  avatar_url: r.avatar_url, subscribers: r.subscribers, views: r.views, videos: r.videos,
  recent: r.recent ? JSON.parse(r.recent) : [], stats_at: r.stats_at, url: `https://www.youtube.com/${r.handle ? '@' + r.handle : 'channel/' + r.channel_id}`,
  subscribers_change_7d: change ?? null,
});

const keyOf = env => { if (!env.GOOGLE_API_KEY) throw new HttpError(409, 'Competitor tracking needs a YouTube API key on the server', 'no_api_key'); return env.GOOGLE_API_KEY; };

async function fetchChannel(env, ref) {
  const yt = ytFor(env), key = keyOf(env);
  const c = await yt.publicChannel(key, ref);
  if (!c) return null;
  const recent = c.uploads ? await yt.publicRecent(key, c.uploads) : [];
  return { ...c, recent };
}

async function save(env, id, c, t) {
  await env.DB.batch([
    env.DB.prepare(`UPDATE competitors SET handle = ?, title = ?, avatar_url = ?, subscribers = ?, views = ?, videos = ?, recent = ?, stats_at = ? WHERE id = ?`)
      .bind(c.handle || null, c.title, c.avatar_url, Number.isFinite(c.subscribers) ? c.subscribers : null,
        Number.isFinite(c.views) ? c.views : null, Number.isFinite(c.videos) ? c.videos : null, JSON.stringify(c.recent || []), t, id),
    env.DB.prepare(`INSERT INTO competitor_days (competitor_id, day, subscribers, views) VALUES (?, ?, ?, ?)
        ON CONFLICT (competitor_id, day) DO UPDATE SET subscribers = excluded.subscribers, views = excluded.views`)
      .bind(id, dayOf(t), Number.isFinite(c.subscribers) ? c.subscribers : null, Number.isFinite(c.views) ? c.views : null),
  ]);
}

export async function listCompetitors(env, w, brand = 'all') {
  const sc = inScope(w, 'brand_id');
  const bf = brand === 'all' ? { sql: '', binds: [] } : brand === 'none' ? { sql: ' AND brand_id IS NULL', binds: [] } : { sql: ' AND brand_id = ?', binds: [brand] };
  const { results } = await env.DB.prepare(`SELECT * FROM competitors WHERE workspace_id = ?${sc.sql}${bf.sql} ORDER BY subscribers DESC, created_at`)
    .bind(wsOf(w), ...sc.binds, ...bf.binds).all();
  if (!results.length) return [];
  const t = now(), since = dayOf(t - 7 * 86400);
  const { results: old } = await env.DB.prepare(`SELECT competitor_id, subscribers FROM competitor_days WHERE day = (
      SELECT MIN(day) FROM competitor_days d2 WHERE d2.competitor_id = competitor_days.competitor_id AND d2.day >= ?)
      AND competitor_id IN (${results.map(() => '?').join(',')})`).bind(since, ...results.map(r => r.id)).all();
  const was = new Map(old.map(o => [o.competitor_id, o.subscribers]));
  return results.map(r => toJson(r, r.subscribers != null && was.get(r.id) != null ? r.subscribers - was.get(r.id) : null));
}

export async function addCompetitor(env, w, body) {
  const ref = parseChannelRef(body?.channel);
  if (!ref) bad('Give a YouTube channel: @handle, a channel link, or a channel id');
  let brand = body?.brand_id ? String(body.brand_id) : null;
  const scope = scopeOf(w);
  if (scope && (!brand || !scope.includes(brand))) bad('Pick one of your brands for this competitor');
  if (brand) {
    const b = await env.DB.prepare('SELECT id FROM brands WHERE id = ? AND workspace_id = ?').bind(brand, wsOf(w)).first();
    if (!b) bad('That brand no longer exists');
  }
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM competitors WHERE workspace_id = ?').bind(wsOf(w)).first();
  if (n >= MAX_COMPETITORS) throw new HttpError(409, `You can follow at most ${MAX_COMPETITORS} competitors`);
  const c = await fetchChannel(env, ref);
  if (!c) throw new HttpError(404, 'No YouTube channel by that name');
  const dup = await env.DB.prepare(`SELECT id FROM competitors WHERE workspace_id = ? AND platform = 'youtube' AND channel_id = ?`).bind(wsOf(w), c.id).first();
  if (dup) throw new HttpError(409, `You already follow ${c.title}`);
  const id = 'cmp_' + randomToken('', 8), t = now();
  await env.DB.prepare(`INSERT INTO competitors (id, workspace_id, brand_id, platform, channel_id, created_at) VALUES (?, ?, ?, 'youtube', ?, ?)`)
    .bind(id, wsOf(w), brand, c.id, t).run();
  await save(env, id, c, t);
  return (await listCompetitors(env, w)).find(x => x.id === id);
}

export async function removeCompetitor(env, w, id) {
  const sc = inScope(w, 'brand_id');
  const r = await env.DB.prepare(`DELETE FROM competitors WHERE id = ? AND workspace_id = ?${sc.sql}`).bind(id, wsOf(w), ...sc.binds).run();
  if (!r.meta.changes) throw new HttpError(404, 'Competitor not found');
  await env.DB.prepare('DELETE FROM competitor_days WHERE competitor_id = ?').bind(id).run();
  return { ok: true };
}

// Cron: a couple of channels per run, each about every 12 hours.
export async function refreshCompetitors(env, t = now(), budget = PER_TICK) {
  if (!env.GOOGLE_API_KEY || budget <= 0) return 0;
  const { results } = await env.DB.prepare(`SELECT id, channel_id FROM competitors WHERE stats_at IS NULL OR stats_at < ?
      ORDER BY COALESCE(stats_at, 0) LIMIT ?`).bind(t - COMPETITOR_EVERY, budget).all();
  let done = 0;
  for (const r of results) {
    try {
      const c = await fetchChannel(env, { id: r.channel_id });
      if (c) await save(env, r.id, c, t);
      else await env.DB.prepare('UPDATE competitors SET stats_at = ? WHERE id = ?').bind(t, r.id).run();
      done++;
    } catch (e) {
      console.error('competitor', r.id, e.message);
      await env.DB.prepare('UPDATE competitors SET stats_at = ? WHERE id = ?').bind(t, r.id).run();
    }
  }
  return done;
}
