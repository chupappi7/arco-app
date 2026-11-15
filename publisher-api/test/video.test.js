import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, signUp, fakeTk } from './helpers.js';
import { metaIntake, igIntake } from '../src/auth.js';
import { createPost, retryPost } from '../src/posts.js';
import { tick } from '../src/publisher.js';
import { copyMedia } from '../src/media.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
// The start of an MP4: a box size, then "ftyp".
const MP4 = new Uint8Array([0, 0, 0, 0x18, 0x66, 0x74, 0x79, 0x70, 0x69, 0x73, 0x6f, 0x6d, 1, 2, 3, 4, 5, 6, 7, 8]);
const T = () => Math.floor(Date.now() / 1000);

async function session() {
  const s = await (await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU, session_id: (await signUp(env)).sid } })).json();
  return { Cookie: `tt_sid=${s.session_id}` };
}
const call = (h, path, method = 'GET', body, tk) => callWorker(path, { method, headers: h, body, tk });
const ticket = async (h, extra = {}) => call(h, '/v1/media/video', 'POST',
  { content_type: 'video/mp4', bytes: MP4.length, name: 'clip.mp4', duration_ms: 12000, width: 1080, height: 1920, ...extra });
const put = (t, bytes = MP4, type = 'video/mp4') => callWorker(new URL(t.upload_url).pathname, { method: 'PUT',
  headers: { 'Content-Type': type, 'Content-Length': String(bytes.length), Origin: 'https://arco-publisher.vercel.app' }, body: bytes });
async function uploadVideo(h, extra) {
  const t = await (await ticket(h, extra)).json();
  const r = await put(t);
  expect(r.status).toBe(200);
  return (await r.json()).key;
}

describe('video upload', () => {
  beforeEach(() => resetDb(env));

  it('uploads with a ticket straight to the Worker, into the library, and serves byte ranges', async () => {
    const h = await session();
    const tr = await ticket(h);
    expect(tr.status).toBe(200);
    const t = await tr.json();
    expect(t.upload_url).toMatch(/^https:\/\/arco-publisher-api\.[^/]+\/upload\/[\w-]+\.[\w-]+$/);
    expect(t.key).toMatch(/\.mp4$/);

    const pre = await callWorker(new URL(t.upload_url).pathname, { method: 'OPTIONS' });
    expect(pre.status).toBe(204);
    expect(pre.headers.get('Access-Control-Allow-Origin')).toBe('https://arco-publisher.vercel.app');
    expect(pre.headers.get('Access-Control-Allow-Methods')).toContain('PUT');

    const up = await put(t);
    expect(up.status).toBe(200);
    expect(up.headers.get('Access-Control-Allow-Origin')).toBe('https://arco-publisher.vercel.app');
    expect((await up.json()).url).toBe(`https://arco-publisher.vercel.app/media/${t.key}`);

    const items = (await (await call(h, '/v1/library')).json()).items;
    expect(items).toMatchObject([{ key: t.key, content_type: 'video/mp4', name: 'clip.mp4', duration_ms: 12000, width: 1080, height: 1920 }]);

    const whole = await callWorker(`/media/${t.key}`);
    expect(whole.status).toBe(200);
    expect(whole.headers.get('Accept-Ranges')).toBe('bytes');
    expect((await whole.arrayBuffer()).byteLength).toBe(MP4.length);
    const part = await callWorker(`/media/${t.key}`, { headers: { Range: 'bytes=4-7' } });
    expect(part.status).toBe(206);
    expect(part.headers.get('Content-Range')).toBe(`bytes 4-7/${MP4.length}`);
    expect(new TextDecoder().decode(await part.arrayBuffer())).toBe('ftyp');
  });

  it('turns away the wrong type, too large, tampered, reused, mismatched or non-video uploads', async () => {
    const h = await session();
    expect((await ticket(h, { content_type: 'video/webm' })).status).toBe(400);
    expect((await ticket(h, { bytes: 100 * 1024 * 1024 + 1 })).status).toBe(400);
    expect((await call({}, '/v1/media/video', 'POST', { content_type: 'video/mp4', bytes: 10 })).status).toBe(401);

    const t = await (await ticket(h)).json();
    const forged = { upload_url: t.upload_url.replace(/\.[\w-]+$/, '.AAAA') };
    expect((await put(forged)).status).toBe(403);
    expect((await put(t, MP4, 'video/quicktime')).status).toBe(400);
    expect((await put(t, MP4.slice(0, 10))).status).toBe(400);
    expect((await put(t)).status).toBe(200);
    expect((await put(t)).status).toBe(409);

    const junk = await (await ticket(h)).json();
    const r = await put(junk, new Uint8Array(MP4.length).fill(7));
    expect(r.status).toBe(400);
    expect(await env.MEDIA.head(junk.key)).toBeNull();
    expect((await (await call(h, '/v1/library')).json()).items).toHaveLength(1);
  });

  it('is never copied like a photo', async () => {
    const h = await session();
    const key = await uploadVideo(h);
    expect((await call(h, '/v1/media/copy', 'POST', { keys: [key] })).status).toBe(400);
  });
});

describe('tiktok video posts', () => {
  beforeEach(() => resetDb(env));
  const settings = { privacy_level: 'PUBLIC_TO_EVERYONE', disable_duet: true, disable_stitch: false };
  const accountId = async h => (await (await call(h, '/v1/accounts')).json()).accounts[0].id;

  it('schedules a library video, publishes it with video/init, and keeps the video', async () => {
    const h = await session();
    const key = await uploadVideo(h);
    const acc = await accountId(h);
    const res = await call(h, '/v1/posts', 'POST', { account_id: acc, video_key: key, image_keys: [], caption: 'watch this',
      settings, scheduled_at: T() + 600 });
    expect(res.status).toBe(200);
    const p = await res.json();
    expect(p).toMatchObject({ video_key: key, image_keys: [], video: `https://arco-publisher.vercel.app/media/${key}` });
    expect(p.settings).toMatchObject({ disable_duet: true, disable_stitch: false });
    expect(p.settings).not.toHaveProperty('auto_add_music');

    // The library video cannot be removed while the post waits.
    expect((await call(h, '/v1/library/remove', 'POST', { keys: [key] })).status).toBe(409);

    let body;
    const tk = fakeTk({ initVideo: async (at, b) => { body = b; return { publish_id: 'v-1' }; },
      initPhoto: async () => { throw new Error('photo path used'); } });
    await tick(env, tk, T() + 700);
    expect(body.source_info).toEqual({ source: 'PULL_FROM_URL', video_url: `https://arco-publisher.vercel.app/media/${key}` });
    expect(body.post_info).toMatchObject({ title: 'watch this', privacy_level: 'PUBLIC_TO_EVERYONE', disable_duet: true, disable_stitch: false });
    expect(body.media_type).toBeUndefined();
    const row = await env.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('published');
    const listed = (await (await call(h, `/v1/posts?from=${T()}&to=${T() + 86400}`)).json()).posts[0];
    expect(listed.post_url).toBe('https://www.tiktok.com/@creator/video/7500000000000000001');

    // Publishing hands photos to the cleanup; the library video stays.
    const m = await env.DB.prepare('SELECT in_library, delete_after FROM media WHERE key = ?').bind(key).first();
    expect(m).toEqual({ in_library: 1, delete_after: null });
    expect((await call(h, '/v1/library/remove', 'POST', { keys: [key] })).status).toBe(200);
  });

  it('refuses photos and video together, a video not in the library, and one too long for the account', async () => {
    const h = await session();
    const key = await uploadVideo(h, { duration_ms: 700_000 });
    const acc = await accountId(h);
    const jpg = await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' },
      body: new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1]) })).json();
    const mk = (extra, tk) => call(h, '/v1/posts', 'POST', { account_id: acc, settings, scheduled_at: null, ...extra }, tk);
    expect((await (await mk({ video_key: key, image_keys: [jpg.key] })).json()).error).toMatch(/not both/);
    expect((await (await mk({ video_key: 'ws_x/nope.mp4' })).json()).error).toMatch(/no longer in the library/);
    const short = fakeTk({ creatorInfo: async () => ({ privacy_level_options: ['PUBLIC_TO_EVERYONE'], max_video_post_duration_sec: 600 }) });
    expect((await (await mk({ video_key: key }, short)).json()).error).toMatch(/up to 10:00 min/);
    expect((await mk({ video_key: key, caption: 'x'.repeat(2201) })).status).toBe(400);
    expect((await mk({ video_key: key })).status).toBe(200);
  });

  it('retries a failed video post only while the video is still in the library', async () => {
    const h = await session();
    const key = await uploadVideo(h);
    const acc = await accountId(h);
    const p = await (await call(h, '/v1/posts', 'POST', { account_id: acc, video_key: key, settings, scheduled_at: T() + 600 })).json();
    await env.DB.prepare(`UPDATE posts SET status = 'failed', publish_id = NULL WHERE id = ?`).bind(p.id).run();
    expect((await call(h, `/v1/posts/${p.id}/retry`, 'POST')).status).toBe(200);
    await env.DB.prepare(`UPDATE posts SET status = 'failed', publish_id = NULL WHERE id = ?`).bind(p.id).run();
    await env.DB.prepare('UPDATE media SET in_library = 0 WHERE key = ?').bind(key).run();
    expect((await call(h, `/v1/posts/${p.id}/retry`, 'POST')).status).toBe(409);
  });
});

describe('instagram reels and facebook videos', () => {
  const calls = [];
  const mt = {
    exchangeCode: async () => ({ access_token: 'short' }),
    longLived: async () => ({ access_token: 'long' }),
    me: async () => ({ id: 'fbuser-1', name: 'Pat' }),
    pages: async () => ({ data: [{ id: 'page-1', name: 'ARCO', access_token: 'page-token' }] }),
    igExchangeCode: async () => ({ access_token: 'ig-short', user_id: 'ig-1' }),
    igLongLived: async () => ({ access_token: 'ig-long', expires_in: 5184000 }),
    igMe: async () => ({ id: 'app-9', user_id: 'ig-1', username: 'arco.app', name: 'ARCO' }),
    igReel: async (...a) => { calls.push(['igReel', ...a]); return { id: 'reel-1' }; },
    igImage: async () => { throw new Error('image path used'); },
    igContainerStatus: async () => ({ status_code: 'FINISHED' }),
    igPublish: async (...a) => { calls.push(['igPublish', ...a]); return { id: 'igmedia-1' }; },
    igPermalink: async () => ({ permalink: 'https://www.instagram.com/reel/abc/' }),
    fbVideo: async (...a) => { calls.push(['fbVideo', ...a]); return { id: 'vid-1' }; },
    fbPhoto: async () => { throw new Error('photo path used'); },
  };
  const menv = { ...env, __meta: mt };
  let ws, key;
  beforeEach(async () => {
    calls.length = 0;
    await resetDb(env);
    const me = await signUp(env);
    const r = await metaIntake(menv, mt, { code: 'c', redirect_uri: 'https://arco-publisher.vercel.app/api/auth/meta/callback', session_id: me.sid });
    await igIntake(menv, mt, { code: 'c#_', redirect_uri: 'https://arco-publisher.vercel.app/api/auth/instagram/callback', session_id: r.session_id });
    ws = r.workspace_id;
    key = `${ws}/clip.mp4`;
    await env.MEDIA.put(key, MP4, { httpMetadata: { contentType: 'video/mp4' } });
    await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, in_library, duration_ms)
        VALUES (?, ?, ?, 'video/mp4', 1, 1, 30000)`).bind(key, ws, MP4.length).run();
  });
  const acc = platform => env.DB.prepare('SELECT id FROM accounts WHERE platform = ?').bind(platform).first();
  const make = async (platform, extra = {}) => createPost(menv, fakeTk(), ws, { account_id: (await acc(platform)).id,
    video_key: key, caption: 'a reel', scheduled_at: null, ...extra });

  it('publishes an Instagram Reel from the library video', async () => {
    const p = await make('instagram');
    await tick(menv, fakeTk(), T() + 10);
    const row = await env.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('published');
    expect(row.post_url).toBe('https://www.instagram.com/reel/abc/');
    expect(calls[0]).toEqual(['igReel', 'ig-long', 'ig-1', `https://arco-publisher.vercel.app/media/${key}`, 'a reel']);
    expect(calls.filter(c => c[0] === 'igPublish')).toHaveLength(1);
  });

  it('publishes a Facebook Page video in one call', async () => {
    const p = await make('facebook');
    await tick(menv, fakeTk(), T() + 10);
    const row = await env.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row).toMatchObject({ status: 'published', public_post_id: 'vid-1', post_url: 'https://www.facebook.com/page-1/videos/vid-1' });
    expect(calls).toEqual([['fbVideo', 'page-token', 'page-1', `https://arco-publisher.vercel.app/media/${key}`, 'a reel']]);
  });

  it('checks Reel and Facebook video length', async () => {
    await env.DB.prepare('UPDATE media SET duration_ms = 2000 WHERE key = ?').bind(key).run();
    await expect(make('instagram')).rejects.toThrow(/Reels must be 3 s/);
    await env.DB.prepare('UPDATE media SET duration_ms = ? WHERE key = ?').bind(21 * 60 * 1000, key).run();
    await expect(make('facebook')).rejects.toThrow(/up to 20:00 min/);
  });

  it('does not copy video keys', async () => {
    await expect(copyMedia(menv, ws, [key])).rejects.toThrow(/not copied/);
  });
});
