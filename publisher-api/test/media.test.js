import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker } from './helpers.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1, 2, 3, 4]);
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 9]);

async function session() {
  const s = await (await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU } })).json();
  return { Cookie: `tt_sid=${s.session_id}` };
}

describe('media', () => {
  beforeEach(() => resetDb(env));

  it('uploads a JPEG, returns a URL on the verified domain, and serves it', async () => {
    const h = await session();
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG });
    expect(res.status).toBe(200);
    const m = await res.json();
    expect(m.url).toBe(`https://arco-publisher.vercel.app/media/${m.key}`);
    expect(m.key).toMatch(/^ws_[0-9a-f]{16}\/[0-9a-f]{32}\.jpg$/);
    const got = await callWorker(`/media/${m.key}`);
    expect(got.status).toBe(200);
    expect(got.headers.get('Content-Type')).toBe('image/jpeg');
    expect(new Uint8Array(await got.arrayBuffer())).toEqual(JPEG);
  });

  it('accepts PNG and stores .png', async () => {
    const h = await session();
    const m = await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/png' }, body: PNG })).json();
    expect(m.key.endsWith('.png')).toBe(true);
  });

  it('rejects a body whose bytes are not JPEG/PNG even if the header says so', async () => {
    const h = await session();
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' },
      body: new TextEncoder().encode('<html>') });
    expect(res.status).toBe(400);
  });

  it('rejects other content types', async () => {
    const h = await session();
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/gif' }, body: JPEG });
    expect(res.status).toBe(400);
  });

  it('rejects images over 5 MB', async () => {
    const h = await session();
    const big = new Uint8Array(5 * 1024 * 1024 + 1); big.set([0xff, 0xd8, 0xff]);
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: big });
    expect(res.status).toBe(400);
  });

  it('new uploads expire in 24 hours until attached to a post', async () => {
    const h = await session();
    const m = await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json();
    const row = await env.DB.prepare('SELECT delete_after, created_at FROM media WHERE key = ?').bind(m.key).first();
    expect(row.delete_after - row.created_at).toBe(86400);
  });

  it('unknown media is 404', async () => {
    expect((await callWorker('/media/ws_x/nope.jpg')).status).toBe(404);
  });

  it('answers HEAD with the type and size and no body, and GET includes the size', async () => {
    const h = await session();
    const m = await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json();
    const head = await callWorker(`/media/${m.key}`, { method: 'HEAD' });
    expect(head.status).toBe(200);
    expect(head.headers.get('Content-Type')).toBe('image/jpeg');
    expect(head.headers.get('Content-Length')).toBe(String(JPEG.length));
    const get = await callWorker(`/media/${m.key}`);
    expect(get.headers.get('Content-Length')).toBe(String(JPEG.length));
    await get.arrayBuffer();
  });
});
