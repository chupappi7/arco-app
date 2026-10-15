import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk } from './helpers.js';
import { encrypt } from '../src/crypto.js';
import { refreshStats, getStats } from '../src/stats.js';
import { MetaError } from '../src/meta.js';

const T = 1_800_000_000;
const env = baseEnv;

async function account(id, platform, ws = 'ws1', extra = {}) {
  const enc = await encrypt(`tok-${id}`, env.TOKEN_KEY);
  await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, username, refresh_token_enc, access_token_enc,
      connected_at, token_updated_at, brand_id) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?)`)
    .bind(id, ws, `${platform === 'tiktok' ? '' : platform === 'instagram' ? 'ig:' : 'fb:'}${id}-remote`, platform, id, enc, enc, extra.brand ?? null).run();
}
async function post(id, accountId, at, { ws = 'ws1', status = 'published', remote = `m-${id}`, stats = null, statsAt = null } = {}) {
  await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at,
      next_attempt_at, public_post_id, stats, stats_at, created_at, updated_at) VALUES (?, ?, ?, ?, '[]', '{}', ?, ?, ?, ?, ?, 1, 1)`)
    .bind(id, ws, accountId, status, at, at, remote, stats && JSON.stringify(stats), statsAt).run();
}

function fakeMeta(over = {}) {
  const calls = [];
  return {
    calls,
    igMediaStats: async (tok, id, o = {}) => { calls.push(['ig', id, !!o.insights]);
      return { like_count: 12, comments_count: 3,
        ...(o.insights ? { insights: { data: [{ name: 'views', values: [{ value: 900 }] }, { name: 'saved', values: [{ value: 4 }] }] } } : {}) }; },
    igAccountStats: async () => { calls.push(['igacc']); return { followers_count: 1500 }; },
    fbPostStats: async (tok, id) => { calls.push(['fb', id]);
      return { reactions: { summary: { total_count: 7 } }, comments: { summary: { total_count: 2 } }, shares: { count: 1 } }; },
    fbPageStats: async (tok, id) => { calls.push(['fbpage', id]); return { followers_count: 300 }; },
    ...over,
  };
}

describe('refreshStats', () => {
  beforeEach(() => resetDb(env));

  it('reads Instagram and Facebook posts and accounts, never TikTok', async () => {
    await account('ig1', 'instagram'); await account('fb1', 'facebook'); await account('tt1', 'tiktok');
    await post('p1', 'ig1', T - 3600); await post('p2', 'fb1', T - 7200); await post('p3', 'tt1', T - 3600);
    const mt = fakeMeta();
    const done = await refreshStats(env, mt, fakeTk(), T, 6);
    expect(done).toEqual({ posts: 2, accounts: 2 });
    const p1 = await env.DB.prepare('SELECT stats FROM posts WHERE id = ?').bind('p1').first();
    expect(JSON.parse(p1.stats)).toEqual({ likes: 12, comments: 3, views: 900, saves: 4 });
    const p2 = await env.DB.prepare('SELECT stats FROM posts WHERE id = ?').bind('p2').first();
    expect(JSON.parse(p2.stats)).toEqual({ likes: 7, comments: 2, shares: 1 });
    expect(mt.calls.some(c => c[1] === 'm-p3')).toBe(false);
    const fb = await env.DB.prepare('SELECT followers FROM accounts WHERE id = ?').bind('fb1').first();
    expect(fb.followers).toBe(300);
    expect(mt.calls).toContainEqual(['fbpage', 'fb1-remote']);
  });

  it('falls back to likes and comments when insights are not allowed, and stops asking for a week', async () => {
    await account('ig1', 'instagram');
    await post('p1', 'ig1', T - 3600); await post('p2', 'ig1', T - 3600);
    const mt = fakeMeta({ igMediaStats: async (tok, id, o = {}) => {
      mt.calls.push(['ig', id, !!o.insights]);
      if (o.insights) throw new MetaError('instagram stats: (#10) Application does not have permission', { code: '10' });
      return { like_count: 5, comments_count: 1 };
    } });
    await refreshStats(env, mt, fakeTk(), T, 6);
    const rows = (await env.DB.prepare('SELECT stats FROM posts ORDER BY id').all()).results;
    expect(rows.map(r => JSON.parse(r.stats))).toEqual([{ likes: 5, comments: 1 }, { likes: 5, comments: 1 }]);
    // One insights attempt, then the second post goes straight to the basic call.
    expect(mt.calls.filter(c => c[0] === 'ig' && c[2]).length).toBe(1);
    const a = await env.DB.prepare('SELECT insights_denied_at FROM accounts WHERE id = ?').bind('ig1').first();
    expect(a.insights_denied_at).toBe(T);
  });

  it('respects the call budget and the refresh schedule', async () => {
    await account('ig1', 'instagram');
    for (let i = 0; i < 8; i++) await post(`p${i}`, 'ig1', T - 3600);
    // Old post read 2 hours ago: not due (daily). Young post read 2 hours ago: not due (3-hourly).
    await post('old', 'ig1', T - 10 * 86400, { stats: { likes: 1 }, statsAt: T - 7200 });
    await post('young', 'ig1', T - 86400, { stats: { likes: 1 }, statsAt: T - 7200 });
    await post('gone', 'ig1', T - 40 * 86400);
    const mt = fakeMeta();
    const done = await refreshStats(env, mt, fakeTk(), T, 4);
    expect(done.accounts + done.posts).toBe(4);
    const read = mt.calls.filter(c => c[0] === 'ig').map(c => c[1]);
    expect(read).not.toContain('m-old'); expect(read).not.toContain('m-young'); expect(read).not.toContain('m-gone');
    expect(await refreshStats(env, mt, fakeTk(), T, 0)).toEqual({ posts: 0, accounts: 0 });
  });

  it('marks an account for reconnecting when its token is dead', async () => {
    await account('ig1', 'instagram'); await post('p1', 'ig1', T - 3600);
    const dead = async () => { throw new MetaError('Reconnect this account', { code: 'needs_reconnect' }); };
    await refreshStats(env, fakeMeta({ igAccountStats: dead, igMediaStats: dead }), fakeTk(), T, 6);
    const a = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id = ?').bind('ig1').first();
    expect(a.needs_reconnect).toBe(1);
  });
});

describe('getStats', () => {
  beforeEach(() => resetDb(env));

  it('totals the period, ranks top posts, and reports follower change', async () => {
    await account('ig1', 'instagram'); await account('fb1', 'facebook'); await account('tt1', 'tiktok');
    await post('a', 'ig1', T - 86400, { stats: { likes: 10, comments: 2, views: 500 }, statsAt: T - 60 });
    await post('b', 'fb1', T - 2 * 86400, { stats: { likes: 3, comments: 1, shares: 2 }, statsAt: T - 60 });
    await post('c', 'tt1', T - 3600);
    await post('old', 'ig1', T - 20 * 86400, { stats: { likes: 99 }, statsAt: T - 60 });
    await env.DB.prepare('UPDATE accounts SET followers = 1500, stats_at = ? WHERE id = ?').bind(T - 60, 'ig1').run();
    await env.DB.prepare(`INSERT INTO follower_history VALUES ('ig1', ?, 1450), ('ig1', ?, 1500)`)
      .bind(new Date((T - 5 * 86400) * 1000).toISOString().slice(0, 10), new Date(T * 1000).toISOString().slice(0, 10)).run();

    const s = await getStats(env, 'ws1', 7, T);
    expect(s.published).toBe(3);
    expect(s.tracked).toBe(2);
    expect(s.totals).toEqual({ views: 500, likes: 13, comments: 3, shares: 2 });
    expect(s.top.map(p => p.id)).toEqual(['a', 'b']);
    expect(s.top[0].stats.views).toBe(500);
    expect(s.followers).toEqual({ total: 1500, change: 50 });
    expect(s.tiktok_pending).toBe(true);
    expect((await getStats(env, 'ws1', 30, T)).totals.likes).toBe(112);
  });

  it('shows nothing from another workspace or outside a member\'s brands', async () => {
    await account('ig1', 'instagram', 'ws1', { brand: 'b1' }); await account('ig2', 'instagram', 'ws1', { brand: 'b2' });
    await account('igx', 'instagram', 'ws2');
    await post('a', 'ig1', T - 3600, { stats: { likes: 1 }, statsAt: T });
    await post('b', 'ig2', T - 3600, { stats: { likes: 10 }, statsAt: T });
    await post('x', 'igx', T - 3600, { ws: 'ws2', stats: { likes: 100 }, statsAt: T });
    expect((await getStats(env, 'ws1', 7, T)).totals.likes).toBe(11);
    const member = await getStats(env, { ws: 'ws1', scope: ['b1'] }, 7, T);
    expect(member.totals.likes).toBe(1);
    expect(member.accounts.map(a => a.id)).toEqual(['ig1']);
    await expect(getStats(env, 'ws1', 9, T)).rejects.toThrow('days');
  });
});
