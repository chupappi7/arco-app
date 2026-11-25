import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb } from './helpers.js';
import { warmup } from '../src/warmup.js';
import { rules } from '../src/notifications.js';
import { getStats } from '../src/stats.js';

const T = 1_800_000_000, H = 3600, D = 86400;
// A post published `ago` seconds before T, read 7 hours after it went out.
const post = (ago, views) => ({ scheduled_at: T - ago, views, stats_at: T - ago + 7 * H });
const daily = list => list.map((v, i) => post((list.length - i) * D, v));

describe('warm-up stage', () => {
  it('new: under 3 days connected or under 3 posts', () => {
    expect(warmup({ connected_at: T - D, published: 5, posts: daily([900, 900, 900]) }, T).stage).toBe('new');
    expect(warmup({ connected_at: T - 20 * D, published: 2, posts: daily([900, 900]) }, T).stage).toBe('new');
  });

  it('ready: the last 5 posts\' median is at least 200 views', () => {
    const w = warmup({ connected_at: T - 20 * D, published: 8, posts: daily([0, 0, 0, 150, 220, 300, 250, 400]) }, T);
    expect(w).toMatchObject({ stage: 'ready', median: 250 });
    expect(w.views).toEqual([0, 0, 0, 150, 220, 300, 250, 400]);
  });

  it('stuck: 10+ days in, the last 5 posts all under 50 views', () => {
    expect(warmup({ connected_at: T - 12 * D, published: 6, posts: daily([0, 10, 0, 3, 40, 12]) }, T).stage).toBe('stuck');
    expect(warmup({ connected_at: T - 8 * D, published: 6, posts: daily([0, 10, 0, 3, 40, 12]) }, T).stage).toBe('warming');
    expect(warmup({ connected_at: T - 12 * D, published: 6, posts: daily([0, 10, 0, 3, 60, 12]) }, T).stage).toBe('warming');
  });

  it('warming, with the trend of the last 3 against the 3 before', () => {
    expect(warmup({ connected_at: T - 12 * D, published: 6, posts: daily([20, 30, 25, 60, 90, 80]) }, T)).toMatchObject({ stage: 'warming', trend: 'up' });
    expect(warmup({ connected_at: T - 12 * D, published: 6, posts: daily([90, 80, 70, 40, 30, 20]) }, T).trend).toBe('down');
    expect(warmup({ connected_at: T - 12 * D, published: 4, posts: daily([40, 50, 60, 70]) }, T).trend).toBe(null);
  });

  it('ignores views read in a post\'s first 6 hours, and keeps the last 10', () => {
    const fresh = { scheduled_at: T - H, views: 0, stats_at: T };
    const w = warmup({ connected_at: T - 30 * D, published: 13, posts: [...daily([300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300]), fresh] }, T);
    expect(w.views).toHaveLength(10);
    expect(w.stage).toBe('ready');
  });

  it('says so when the platform shares no views', () => {
    const w = warmup({ connected_at: T - 30 * D, published: 6, posts: [] }, T);
    expect(w.stage).toBe('warming');
    expect(w.next).toMatch(/views/i);
  });
});

describe('warm-up alerts', () => {
  const acct = (o = {}) => ({ id: 'a1', workspace_id: 'ws1', brand_id: null, platform: 'tiktok', username: 'a1', followers: null, needs_reconnect: 0, connected_at: T - 20 * D, ...o });
  const pst = (i, views) => ({ id: `p${i}`, workspace_id: 'ws1', account_id: 'a1', status: 'published', scheduled_at: T - (10 - i) * D,
    s: { views }, stats_at: T - (10 - i) * D + 7 * H, brand_id: null, platform: 'tiktok', username: 'a1', connected_at: T - 20 * D });
  const run = (views, o) => rules({ posts: views.map((v, i) => pst(i, v)), accounts: [acct(o)], low: new Map(), comps: [],
    first: new Map(), published: new Map([['a1', views.length]]) }, T).filter(n => n.kind.startsWith('warm'));

  it('tells once an account is warmed up, only for accounts connected in the last 60 days', () => {
    expect(run([10, 20, 250, 300, 260, 280])).toMatchObject([{ key: 'warmup:a1:ready', tone: 'win', account: 'a1' }]);
    expect(run([10, 20, 250, 300, 260, 280], { connected_at: T - 90 * D })).toEqual([]);
  });

  it('flags an account that is stuck', () => {
    expect(run([0, 5, 0, 10, 3, 0])).toMatchObject([{ key: 'warmstuck:a1', kind: 'warmstuck', tone: 'bad' }]);
    expect(run([40, 60, 80, 90, 100, 120])).toEqual([]);
  });
});

describe('warm-up in stats', () => {
  beforeEach(() => resetDb(env));

  it('each account carries its stage, last views and next step', async () => {
    await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, username, refresh_token_enc, connected_at, token_updated_at)
        VALUES ('a1', 'ws1', 'o1', 'tiktok', 'one', 'x', ?, ?)`).bind(T - 20 * D, T - 20 * D).run();
    const views = [0, 0, 220, 300, 250, 260];
    for (const [i, v] of views.entries()) {
      const at = T - (views.length - i) * D;
      await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at, next_attempt_at, stats, stats_at, created_at, updated_at)
          VALUES (?, 'ws1', 'a1', 'published', '[]', '{}', ?, ?, ?, ?, ?, ?)`).bind(`p${i}`, at, at, JSON.stringify({ views: v }), at + 7 * H, at, at).run();
    }
    const s = await getStats(env, 'ws1', 7, T);
    expect(s.accounts[0].warmup).toMatchObject({ stage: 'ready', views, posts: 6, days: 20 });
  });
});
