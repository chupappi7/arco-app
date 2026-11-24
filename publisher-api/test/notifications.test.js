import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb } from './helpers.js';
import { rules, runNotifications, listNotifications, markSeen, NOTIFY_EVERY } from '../src/notifications.js';

const T = 1_800_000_000, H = 3600, D = 86400;
const acct = (id, o = {}) => ({ id, workspace_id: 'ws1', brand_id: 'b1', platform: 'tiktok', username: id, followers: null, needs_reconnect: 0, connected_at: T - 90 * D, ...o });
const pst = (id, account, at, o = {}) => ({ id, workspace_id: 'ws1', account_id: account, status: 'published', scheduled_at: at, s: null, stats_at: null,
  brand_id: 'b1', platform: 'tiktok', username: account, connected_at: T - 90 * D, ...o });
const facts = (o = {}) => ({ posts: [], accounts: [acct('a1')], low: new Map(), comps: [], first: new Map(), ...o });
const keys = f => rules(f, T).map(n => n.key).sort();

describe('notification rules', () => {
  it('views: only the highest milestone passed', () => {
    expect(keys(facts({ posts: [pst('p1', 'a1', T - D, { s: { views: 12000 } })] }))).toContain('views:p1:10000');
    expect(keys(facts({ posts: [pst('p1', 'a1', T - D, { s: { views: 12000 } })] }))).not.toContain('views:p1:1000');
    expect(keys(facts({ posts: [pst('p1', 'a1', T - D, { s: { views: 999 } })] }))).toEqual(['empty:b1']);
    expect(keys(facts({ posts: [pst('p1', 'a1', T - D, { s: { views: 999 } }), pst('q', 'a1', T + H, { status: 'queued' })] }))).toEqual([]);
  });

  it('breakout: 3x the account median, this week, at least 500 views', () => {
    const base = [1, 2, 3, 4].map(i => pst(`o${i}`, 'a1', T - 10 * D, { s: { views: 200 } }));
    expect(keys(facts({ posts: [...base, pst('w', 'a1', T - D, { s: { views: 900 } })] }))).toContain('breakout:w');
    expect(keys(facts({ posts: [...base, pst('w', 'a1', T - 9 * D, { s: { views: 900 } })] }))).not.toContain('breakout:w');
  });

  it('followers: fires when crossed this week, not for what the account already had', () => {
    expect(keys(facts({ accounts: [acct('a1', { followers: 1200 })], low: new Map([['a1', 900]]) }))).toEqual(['followers:a1:1000']);
    expect(keys(facts({ accounts: [acct('a1', { followers: 1200 })], low: new Map([['a1', 1100]]) }))).toEqual([]);
  });

  it('problems: zero views after 6 hours grouped per account, failed, reconnect, empty queue', () => {
    const z = (id, at, after) => pst(id, 'a1', at, { s: { views: 0 }, stats_at: at + after });
    const f = facts({ accounts: [acct('a1', { needs_reconnect: 1 })],
      posts: [z('z1', T - 2 * D, 7 * H), z('z2', T - D, 7 * H), z('z3', T - H, 2 * H), pst('f1', 'a1', T - H, { status: 'failed' })] });
    const out = rules(f, T);
    const zero = out.filter(n => n.kind === 'zero');
    expect(zero).toHaveLength(1);
    expect(zero[0]).toMatchObject({ key: 'zero:z2', post: 'z2', title: '0 views on @a1 · 2 posts' });
    expect(out.map(n => n.key)).toEqual(expect.arrayContaining(['failed:f1', 'reconnect:a1', 'empty:b1']));
  });

  it('competitor breakouts', () => {
    const recent = [100, 120, 90, 110].map((v, i) => ({ id: 'v' + i, views: v, published_at: T - 20 * D })).concat({ id: 'hot', title: 'Hot', views: 5000, published_at: T - D });
    expect(keys(facts({ comps: [{ id: 'c1', workspace_id: 'ws1', brand_id: null, title: 'Rival', recent: JSON.stringify(recent) }] }))).toEqual(['cbreak:hot']);
  });
});

describe('notification runs', () => {
  beforeEach(() => resetDb(env));
  const addAccount = (id, extra = '') => env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, username, refresh_token_enc, connected_at, token_updated_at, needs_reconnect)
      VALUES (?, 'ws1', ?, 'tiktok', ?, 'x', 1, 1, ?)`).bind(id, 'o-' + id, id, extra === 'broken' ? 1 : 0).run();

  it('writes each event once, takes back fixed problems, and tracks what each person has seen', async () => {
    await addAccount('a1', 'broken');
    expect((await runNotifications(env, T)).made).toBe(1);
    expect((await runNotifications(env, T + 60)).made).toBe(0);                      // throttled
    expect((await runNotifications(env, T + NOTIFY_EVERY + 1)).made).toBe(0);       // already there
    const who = { ws: 'ws1', userId: 'u1', role: 'owner', scope: null };
    let l = await listNotifications(env, who);
    expect(l).toMatchObject({ unread: 1, items: [{ kind: 'reconnect', title: 'Reconnect @a1', unread: true }] });
    await markSeen(env, who, T + 10);
    l = await listNotifications(env, who);
    expect(l.unread).toBe(0);
    expect((await listNotifications(env, { ...who, userId: 'u2' })).unread).toBe(1);
    await env.DB.prepare('UPDATE accounts SET needs_reconnect = 0').run();
    expect((await runNotifications(env, T + 2 * NOTIFY_EVERY + 2)).removed).toBe(1);
    expect((await listNotifications(env, who)).items).toEqual([]);
  });
});
