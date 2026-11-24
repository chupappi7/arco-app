import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, signUp } from './helpers.js';
import { parseChannelRef, addCompetitor, listCompetitors, removeCompetitor, refreshCompetitors, COMPETITOR_EVERY } from '../src/competitors.js';

function fakeYt(subs = 5000) {
  const calls = [];
  return {
    calls,
    publicChannel: async (key, ref) => { calls.push(['channel', key, ref]);
      if (ref.handle === 'nobody') return null;
      return { id: 'UCaaaaaaaaaaaaaaaaaaaaaa', title: 'Rival', handle: 'rival', avatar_url: 'https://yt/r.jpg', subscribers: subs.n ?? subs, views: 90000, videos: 40, uploads: 'UUaaa' }; },
    publicRecent: async (key, uploads) => { calls.push(['recent', uploads]);
      return [{ id: 'v2', title: 'Second', published_at: 2, views: 300 }, { id: 'v1', title: 'First', published_at: 1, views: 1200 }]; },
  };
}
const envWith = (yt, key = 'k-1') => ({ ...baseEnv, __yt: yt, GOOGLE_API_KEY: key });

describe('competitor channels', () => {
  beforeEach(() => resetDb(baseEnv));

  it('reads handles, links and channel ids', () => {
    expect(parseChannelRef('@MrBeast')).toEqual({ handle: 'MrBeast' });
    expect(parseChannelRef('https://www.youtube.com/@some.one/videos')).toEqual({ handle: 'some.one' });
    expect(parseChannelRef('youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA')).toEqual({ id: 'UCX6OQ3DkcsbYNE6H8uQQuVA' });
    expect(parseChannelRef('https://youtube.com/watch?v=abc')).toBeNull();
    expect(parseChannelRef('')).toBeNull();
  });

  it('adds a channel with its numbers and uploads, refuses duplicates and unknown names, and removes it', async () => {
    const { ws } = await signUp(baseEnv), yt = fakeYt(), env = envWith(yt);
    const c = await addCompetitor(env, ws, { channel: '@rival' });
    expect(c).toMatchObject({ title: 'Rival', handle: 'rival', subscribers: 5000, url: 'https://www.youtube.com/@rival' });
    expect(c.recent.map(v => v.id)).toEqual(['v2', 'v1']);
    expect(yt.calls[0]).toEqual(['channel', 'k-1', { handle: 'rival' }]);
    await expect(addCompetitor(env, ws, { channel: 'UCaaaaaaaaaaaaaaaaaaaaaa' })).rejects.toThrow(/already follow/);
    await expect(addCompetitor(env, ws, { channel: '@nobody' })).rejects.toThrow(/No YouTube channel/);
    expect(await listCompetitors(env, ws)).toHaveLength(1);
    await removeCompetitor(env, ws, c.id);
    expect(await listCompetitors(env, ws)).toEqual([]);
  });

  it('needs the API key', async () => {
    const { ws } = await signUp(baseEnv);
    await expect(addCompetitor({ ...baseEnv, __yt: fakeYt(), GOOGLE_API_KEY: '' }, ws, { channel: '@rival' })).rejects.toThrow(/API key/);
  });

  it('refreshes stale channels on the cron and shows subscriber growth over 7 days', async () => {
    const { ws } = await signUp(baseEnv), subs = { n: 5000 }, yt = fakeYt(subs), env = envWith(yt);
    const c = await addCompetitor(env, ws, { channel: '@rival' });
    const t0 = Math.floor(Date.now() / 1000);
    // pretend the first numbers were from 6 days ago
    await baseEnv.DB.prepare('UPDATE competitor_days SET day = ? WHERE competitor_id = ?').bind(new Date((t0 - 6 * 86400) * 1000).toISOString().slice(0, 10), c.id).run();
    expect(await refreshCompetitors(env, t0)).toBe(0);            // fresh, nothing to do
    subs.n = 5600;
    expect(await refreshCompetitors(env, t0 + COMPETITOR_EVERY + 1)).toBe(1);
    const [now] = await listCompetitors(env, ws);
    expect(now.subscribers).toBe(5600);
    expect(now.subscribers_change_7d).toBe(600);
  });
});
