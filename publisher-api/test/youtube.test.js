import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk, signUp } from './helpers.js';
import { ytIntake } from '../src/auth.js';
import { accessTokenFor } from '../src/accounts.js';
import { createPost } from '../src/posts.js';
import { tick, FORCED_PRIVATE } from '../src/publisher.js';
import { refreshStats, getStats } from '../src/stats.js';
import { schedulePlan } from '../src/planner.js';
import { decrypt } from '../src/crypto.js';
import { YouTubeError } from '../src/youtube.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/youtube/callback';
const T = 1_800_000_000;
const MP4 = new Uint8Array([0, 0, 0, 0x18, 0x66, 0x74, 0x79, 0x70, 0x69, 0x73, 0x6f, 0x6d, 1, 2, 3, 4]);

function fakeYt(over = {}) {
  const calls = [];
  const y = {
    calls,
    exchangeCode: async () => ({ access_token: 'yt-access', refresh_token: 'yt-refresh', expires_in: 3599 }),
    refresh: async rt => { calls.push(['refresh', rt]); return { access_token: 'yt-fresh', expires_in: 3599 }; },
    myChannel: async () => ({ id: 'UC123', title: 'ARCO', custom_url: 'arcoapp', avatar_url: 'https://yt/a.jpg', subscribers: 1200 }),
    startUpload: async (tok, meta) => { calls.push(['start', tok, meta]); return 'https://upload.yt/session-1'; },
    putUpload: async (loc, body, bytes, type) => {
      const got = new Uint8Array(await new Response(body).arrayBuffer());
      calls.push(['put', loc, bytes, type, got.length]);
      return { id: 'vid-1', status: { privacyStatus: 'public' } };
    },
    videoStats: async (tok, ids) => { calls.push(['stats', ids]); return ids.map(id => ({ id, statistics: { viewCount: '900', likeCount: '40', commentCount: '3' } })); },
    ...over,
  };
  return y;
}
const withYt = yt => ({ ...baseEnv, __yt: yt });

async function connect(yt, extra = {}) {
  const s = extra.s || await signUp(baseEnv);
  const r = await ytIntake(withYt(yt), yt, { code: 'c', redirect_uri: RU, session_id: s.sid });
  return { ...s, accountId: r.account_ids[0] };
}

async function libraryVideo(ws, durationMs = 20_000) {
  const key = `${ws}/v-${Math.random().toString(16).slice(2)}.mp4`;
  await baseEnv.MEDIA.put(key, MP4, { httpMetadata: { contentType: 'video/mp4' } });
  await baseEnv.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, in_library, duration_ms)
      VALUES (?, ?, ?, 'video/mp4', 1, 1, ?)`).bind(key, ws, MP4.length, durationMs).run();
  return key;
}
const row = id => baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(id).first();

describe('connecting YouTube', () => {
  beforeEach(() => resetDb(baseEnv));

  it('keeps the channel with its refresh token, and a reconnect keeps it when Google sends none', async () => {
    const yt = fakeYt();
    const { ws, accountId, sid } = await connect(yt);
    const a = await baseEnv.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
    expect(a).toMatchObject({ workspace_id: ws, platform: 'youtube', open_id: 'yt:UC123', username: 'arcoapp', display_name: 'ARCO', followers: 1200 });
    expect(await decrypt(a.refresh_token_enc, baseEnv.TOKEN_KEY)).toBe('yt-refresh');

    const again = fakeYt({ exchangeCode: async () => ({ access_token: 'yt-access-2', expires_in: 3599 }) });
    await ytIntake(withYt(again), again, { code: 'c', redirect_uri: RU, session_id: sid });
    const b = await baseEnv.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
    expect(await decrypt(b.refresh_token_enc, baseEnv.TOKEN_KEY)).toBe('yt-refresh');
    expect(await decrypt(b.access_token_enc, baseEnv.TOKEN_KEY)).toBe('yt-access-2');
  });

  it('says what to do when Google gives no lasting access for a new channel', async () => {
    const yt = fakeYt({ exchangeCode: async () => ({ access_token: 'a', expires_in: 3599 }) });
    const s = await signUp(baseEnv);
    await expect(ytIntake(withYt(yt), yt, { code: 'c', redirect_uri: RU, session_id: s.sid })).rejects.toThrow(/myaccount\.google\.com\/permissions/);
    await expect(ytIntake(withYt(yt), yt, { code: 'c', redirect_uri: 'https://evil.example/cb', session_id: s.sid })).rejects.toThrow(/redirect_uri/);
  });

  it('refreshes an expired access token, and a revoked one asks to reconnect', async () => {
    const yt = fakeYt();
    const { accountId } = await connect(yt);
    await baseEnv.DB.prepare('UPDATE accounts SET access_expires_at = 1 WHERE id = ?').bind(accountId).run();
    let a = await baseEnv.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
    expect(await accessTokenFor(withYt(yt), fakeTk(), a)).toBe('yt-fresh');
    expect(yt.calls.filter(c => c[0] === 'refresh')).toEqual([['refresh', 'yt-refresh']]);

    const dead = fakeYt({ refresh: async () => { throw new YouTubeError('Reconnect this account', { code: 'needs_reconnect' }); } });
    await baseEnv.DB.prepare('UPDATE accounts SET access_expires_at = 1 WHERE id = ?').bind(accountId).run();
    a = await baseEnv.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
    await expect(accessTokenFor(withYt(dead), fakeTk(), a)).rejects.toThrow(/Reconnect/);
    expect((await baseEnv.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id = ?').bind(accountId).first()).needs_reconnect).toBe(1);
  });
});

describe('posting to YouTube', () => {
  beforeEach(() => resetDb(baseEnv));

  it('uploads the library video with title, description and visibility, as a Short when it is short', async () => {
    const yt = fakeYt();
    const { ws, accountId } = await connect(yt);
    const key = await libraryVideo(ws, 20_000);
    const p = await createPost(withYt(yt), fakeTk(), ws, { account_id: accountId, video_key: key, caption: 'Plan the day\nmore text #focus',
      settings: { yt_privacy: 'unlisted' } });
    expect(p.settings).toEqual({ yt_privacy: 'unlisted', yt_title: 'Plan the day', made_for_kids: false });
    await tick(withYt(yt), fakeTk(), T);
    const start = yt.calls.find(c => c[0] === 'start');
    expect(start[2]).toMatchObject({ title: 'Plan the day', description: 'Plan the day\nmore text #focus', privacy: 'unlisted', bytes: MP4.length, contentType: 'video/mp4' });
    expect(yt.calls.find(c => c[0] === 'put')).toEqual(['put', 'https://upload.yt/session-1', MP4.length, 'video/mp4', MP4.length]);
    expect(await row(p.id)).toMatchObject({ status: 'published', public_post_id: 'vid-1', post_url: 'https://www.youtube.com/shorts/vid-1', fail_reason: null });
  });

  it('links a long video as a normal video, and says so when YouTube kept it private', async () => {
    const yt = fakeYt({ putUpload: async (loc, body) => { await new Response(body).arrayBuffer(); return { id: 'vid-2', status: { privacyStatus: 'private' } }; } });
    const { ws, accountId } = await connect(yt);
    const key = await libraryVideo(ws, 300_000);
    const p = await createPost(withYt(yt), fakeTk(), ws, { account_id: accountId, video_key: key, title: 'Deep work', caption: 'x' });
    await tick(withYt(yt), fakeTk(), T);
    expect(await row(p.id)).toMatchObject({ status: 'published', post_url: 'https://youtu.be/vid-2', fail_reason: FORCED_PRIVATE });
  });

  it('a lost answer after the bytes were sent is not resent; a refused start is retried', async () => {
    const lost = fakeYt({ putUpload: async (loc, body) => { await new Response(body).arrayBuffer(); throw new YouTubeError('upload: network error', { code: 'network', transient: true }); } });
    const { ws, accountId } = await connect(lost);
    const p = await createPost(withYt(lost), fakeTk(), ws, { account_id: accountId, video_key: await libraryVideo(ws), caption: 'x' });
    await tick(withYt(lost), fakeTk(), T);
    expect((await row(p.id)).status).toBe('failed');
    expect((await row(p.id)).fail_reason).toMatch(/no answer came back/);

    const busy = fakeYt({ startUpload: async () => { throw new YouTubeError('upload start: HTTP 503', { code: 'http_503', transient: true }); } });
    const q = await createPost(withYt(busy), fakeTk(), ws, { account_id: accountId, video_key: await libraryVideo(ws), caption: 'y' });
    await tick(withYt(busy), fakeTk(), T);
    expect((await row(q.id)).status).toBe('queued');
  });

  it('takes videos only, and a plan for photos leaves the brand channel out', async () => {
    const yt = fakeYt();
    const { ws, accountId } = await connect(yt);
    const img = `${ws}/p.jpg`;
    await baseEnv.MEDIA.put(img, new Uint8Array([0xff, 0xd8, 0xff]));
    await baseEnv.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at) VALUES (?, ?, 3, 'image/jpeg', 1)`).bind(img, ws).run();
    await expect(createPost(withYt(yt), fakeTk(), ws, { account_id: accountId, image_keys: [img], caption: 'x' })).rejects.toThrow(/YouTube takes videos only/);
    await expect(createPost(withYt(yt), fakeTk(), ws, { account_id: accountId, video_key: await libraryVideo(ws), caption: 'x',
      settings: { yt_title: 'a'.repeat(101) } })).rejects.toThrow(/100 characters/);

    await baseEnv.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, in_library) VALUES (?, ?, 3, 'image/jpeg', 1, 1)`).bind(`${ws}/lib.jpg`, ws).run();
    await baseEnv.MEDIA.put(`${ws}/lib.jpg`, new Uint8Array([0xff, 0xd8, 0xff]));
    const plan = await schedulePlan(withYt(yt), fakeTk(), ws, { posts: [{ library_keys: [`${ws}/lib.jpg`], account_ids: [accountId], caption: 'hi', at: '2030-01-01T10:00' }] });
    expect(plan.plan[0].skipped).toEqual([{ account_id: accountId, handle: '@arcoapp', platform: 'youtube', reason: 'YouTube takes videos only' }]);
  });
});

describe('YouTube numbers', () => {
  beforeEach(() => resetDb(baseEnv));
  it('reads subscribers, and views, likes and comments for every due video in one call', async () => {
    const yt = fakeYt({ myChannel: async () => ({ id: 'UC123', title: 'ARCO', custom_url: 'arcoapp', avatar_url: 'https://yt/b.jpg', subscribers: 1300 }) });
    const { ws, accountId } = await connect(fakeYt());
    for (const id of ['a', 'b']) {
      await baseEnv.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at, next_attempt_at,
          public_post_id, created_at, updated_at) VALUES (?, ?, ?, 'published', '[]', '{}', ?, ?, ?, 1, 1)`)
        .bind(id, ws, accountId, T - 3600, T - 3600, `vid-${id}`).run();
    }
    await refreshStats(withYt(yt), {}, fakeTk(), T, 6);
    expect(yt.calls.filter(c => c[0] === 'stats')).toEqual([['stats', ['vid-a', 'vid-b']]]);
    expect(JSON.parse((await row('a')).stats)).toEqual({ views: 900, likes: 40, comments: 3 });
    const acc = await baseEnv.DB.prepare('SELECT followers, avatar_url FROM accounts WHERE id = ?').bind(accountId).first();
    expect(acc).toEqual({ followers: 1300, avatar_url: 'https://yt/b.jpg' });
    const st = await getStats(baseEnv, ws, 7, T, 'youtube');
    expect(st.totals.views).toBe(1800);
    expect(st.by_platform.map(x => x.platform)).toEqual(['youtube']);
  });
});
