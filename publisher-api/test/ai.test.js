import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, signUp } from './helpers.js';
import { AI_DAILY_LIMIT } from '../src/limits.js';

const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1]);

// A writer double that records what it was asked and answers from `reply`.
function fakeAi(reply) {
  const calls = [];
  return { calls, json: async req => { calls.push(req); return typeof reply === 'function' ? reply(req) : reply; } };
}
const call = (sid, path, method, body, ai) => callWorker(path, { method, headers: { Cookie: `tt_sid=${sid}` }, body,
  env: ai ? { __ai: ai } : {} });
async function upload(sid) {
  return (await (await callWorker('/v1/media', { method: 'POST',
    headers: { Cookie: `tt_sid=${sid}`, 'Content-Type': 'image/jpeg' }, body: JPEG })).json()).key;
}

describe('AI captions', () => {
  beforeEach(() => resetDb(baseEnv));

  it('writes a title and a caption per platform from the photos and the brief', async () => {
    const me = await signUp(baseEnv);
    const key = await upload(me.sid);
    const ai = fakeAi({ title: 'Morning bake', captions: { tiktok: 'tt', instagram: 'ig #bread', facebook: 'fb' } });
    const r = await (await call(me.sid, '/v1/ai/captions', 'POST',
      { platforms: ['tiktok', 'instagram', 'facebook'], image_keys: [key], brief: 'Sourdough out of the oven', tone: 'playful' }, ai)).json();
    expect(r).toMatchObject({ title: 'Morning bake', captions: { tiktok: 'tt', instagram: 'ig #bread', facebook: 'fb' }, remaining: AI_DAILY_LIMIT - 1 });
    const sent = ai.calls[0];
    expect(sent.content[0]).toEqual({ type: 'image', source: { type: 'url', url: `https://arco-publisher.vercel.app/media/${key}` } });
    expect(sent.content.at(-1).text).toContain('Sourdough out of the oven');
    expect(sent.schema.properties.captions.required).toEqual(['tiktok', 'instagram', 'facebook']);
  });

  it('keeps results inside platform limits whatever comes back', async () => {
    const me = await signUp(baseEnv);
    const tags = Array.from({ length: 40 }, (_, i) => `#t${i}`).join(' ');
    const ai = fakeAi({ title: 'x'.repeat(200), captions: { tiktok: 'ok', instagram: `${'y'.repeat(3000)} ${tags}` } });
    const r = await (await call(me.sid, '/v1/ai/captions', 'POST', { platforms: ['tiktok', 'instagram'], brief: 'b' }, ai)).json();
    expect([...r.title].length).toBe(90);
    expect([...r.captions.instagram].length).toBeLessThanOrEqual(2200);
    expect((r.captions.instagram.match(/#[^\s#]+/g) || []).length).toBeLessThanOrEqual(30);
  });

  it('rewrites a caption, using the brand voice', async () => {
    const me = await signUp(baseEnv);
    const b = await (await call(me.sid, '/v1/brands', 'POST', { name: 'Bakery' })).json();
    await call(me.sid, `/v1/brands/${b.id}`, 'PATCH', { voice: 'Warm, a little cheeky, never salesy.' });
    const ai = fakeAi({ text: 'Shorter one' });
    const r = await (await call(me.sid, '/v1/ai/captions', 'POST',
      { mode: 'rewrite', text: 'A long caption about bread', instruction: 'shorter', brand_id: b.id }, ai)).json();
    expect(r.text).toBe('Shorter one');
    expect(ai.calls[0].content[0].text).toContain('Warm, a little cheeky');
  });

  it('stops at the daily limit, even with requests in parallel, and failed writes do not count', async () => {
    const me = await signUp(baseEnv);
    await baseEnv.DB.prepare('INSERT INTO ai_usage (workspace_id, day, count) VALUES (?, ?, ?)')
      .bind(me.ws, new Date().toISOString().slice(0, 10), AI_DAILY_LIMIT - 3).run();
    const failing = fakeAi(() => { throw Object.assign(new Error('x'), { status: 502 }); });
    await call(me.sid, '/v1/ai/captions', 'POST', { platforms: ['facebook'], brief: 'b' }, failing);
    const ai = fakeAi({ title: '', captions: { facebook: 'ok' } });
    const res = await Promise.all(Array.from({ length: 8 }, () => call(me.sid, '/v1/ai/captions', 'POST', { platforms: ['facebook'], brief: 'b' }, ai)));
    expect(res.filter(r => r.status === 200)).toHaveLength(3);
    expect(res.filter(r => r.status === 429)).toHaveLength(5);
  });

  it('cannot read another workspace\'s images or brand voice', async () => {
    const a = await signUp(baseEnv), b = await signUp(baseEnv);
    const theirKey = await upload(b.sid);
    const theirBrand = await (await call(b.sid, '/v1/brands', 'POST', { name: 'Secret' })).json();
    const ai = fakeAi({ title: '', captions: { facebook: 'x' }, text: 'x' });
    expect((await call(a.sid, '/v1/ai/captions', 'POST', { platforms: ['facebook'], image_keys: [theirKey] }, ai)).status).toBe(404);
    expect((await call(a.sid, '/v1/ai/captions', 'POST', { mode: 'rewrite', text: 't', instruction: 'shorter', brand_id: theirBrand.id }, ai)).status).toBe(404);
    expect(ai.calls).toHaveLength(0);
  });

  it('says so when AI writing is not set up', async () => {
    const me = await signUp(baseEnv);
    expect((await call(me.sid, '/v1/ai/captions', 'POST', { platforms: ['facebook'], brief: 'b' })).status).toBe(503);
  });
});
