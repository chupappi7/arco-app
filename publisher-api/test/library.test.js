import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, signUp } from './helpers.js';
import { runCleanup } from '../src/cleanup.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1, 2, 3, 4]);

async function session() {
  const s = await (await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU, session_id: (await signUp(env)).sid } })).json();
  return { Cookie: `tt_sid=${s.session_id}` };
}
const upload = async h => (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json();
const call = async (h, path, method = 'GET', body) => callWorker(path, { method, headers: h, body });

describe('library', () => {
  beforeEach(() => resetDb(env));

  it('keeps uploads past the cleanup, files them by brand, and copies them for posts', async () => {
    const h = await session();
    const b = await (await call(h, '/v1/brands', 'POST', { name: 'Bakery' })).json();
    const m1 = await upload(h), m2 = await upload(h);
    expect((await call(h, '/v1/library', 'POST', { keys: [m1.key], brand_id: b.id, names: { [m1.key]: 'cake.jpg' } })).status).toBe(200);
    expect((await call(h, '/v1/library', 'POST', { keys: [m2.key] })).status).toBe(200);

    await runCleanup(env, Math.floor(Date.now() / 1000) + 8 * 86400);
    const lr = await (await call(h, '/v1/library')).json();
    const all = lr.items;
    expect(lr.storage).toEqual({ used: JPEG.length * 2, library: JPEG.length * 2, limit: 5 * 1024 * 1024 * 1024 });
    expect(all.map(i => i.key).sort()).toEqual([m1.key, m2.key].sort());
    const mine = (await (await call(h, `/v1/library?brand=${b.id}`)).json()).items;
    expect(mine).toMatchObject([{ key: m1.key, brand_id: b.id, name: 'cake.jpg' }]);
    expect((await (await call(h, '/v1/library?brand=none')).json()).items.map(i => i.key)).toEqual([m2.key]);

    const copy = await (await call(h, '/v1/media/copy', 'POST', { keys: [m1.key] })).json();
    expect(copy.media[0].key).not.toBe(m1.key);
  });

  it('moves and removes, and will not take a key twice', async () => {
    const h = await session();
    const b = await (await call(h, '/v1/brands', 'POST', { name: 'Bakery' })).json();
    const m = await upload(h);
    await call(h, '/v1/library', 'POST', { keys: [m.key] });
    expect((await call(h, '/v1/library', 'POST', { keys: [m.key] })).status).toBe(400);
    expect((await call(h, '/v1/library', 'PATCH', { keys: [m.key], brand_id: b.id })).status).toBe(200);
    expect((await (await call(h, `/v1/library?brand=${b.id}`)).json()).items).toHaveLength(1);
    expect((await call(h, '/v1/library/remove', 'POST', { keys: [m.key] })).status).toBe(200);
    expect((await (await call(h, '/v1/library')).json()).items).toEqual([]);
    expect((await call(h, '/v1/library', 'PATCH', { keys: [m.key], brand_id: null })).status).toBe(404);
    expect((await call(h, '/v1/library', 'POST', { keys: [m.key], brand_id: 'brd_nope' })).status).toBe(404);
  });
});
