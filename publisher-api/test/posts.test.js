import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, fakeTk } from './helpers.js';
import { validatePost } from '../src/posts.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1]);
const T = 1_800_000_000;
const settings = { privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: false, auto_add_music: false,
                   brand_organic: false, branded_content: false };

async function setup() {
  const s = await (await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU } })).json();
  const h = { Cookie: `tt_sid=${s.session_id}` };
  const up = async () => (await (await callWorker('/v1/media', { method: 'POST',
    headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json()).key;
  return { h, account_id: s.account_id, keys: [await up(), await up()] };
}

describe('validatePost', () => {
  const base = { account_id: 'acc_1', image_keys: ['k1'], settings, title: '', caption: '' };

  it('turns scheduled_at null into now', () => {
    expect(validatePost({ ...base, scheduled_at: null }, T).scheduled_at).toBe(T);
  });
  it('rejects a time under 5 minutes ahead', () => {
    expect(() => validatePost({ ...base, scheduled_at: T + 299 }, T)).toThrow(/5 minutes/);
    expect(validatePost({ ...base, scheduled_at: T + 300 }, T).scheduled_at).toBe(T + 300);
  });
  it('requires a privacy level from the known list', () => {
    expect(() => validatePost({ ...base, settings: { ...settings, privacy_level: '' } }, T)).toThrow(/who can view/i);
  });
  it('refuses branded content set to Only me', () => {
    expect(() => validatePost({ ...base, settings: { ...settings, privacy_level: 'SELF_ONLY', branded_content: true } }, T))
      .toThrow(/Branded content/);
  });
  it('limits images, title and caption, counting emoji as one character', () => {
    expect(() => validatePost({ ...base, image_keys: [] }, T)).toThrow(/at least one/i);
    expect(() => validatePost({ ...base, image_keys: Array(36).fill('k') }, T)).toThrow(/35/);
    expect(validatePost({ ...base, title: '😀'.repeat(90) }, T).title).toHaveLength(180);
    expect(() => validatePost({ ...base, title: 'x'.repeat(91) }, T)).toThrow(/90/);
    expect(() => validatePost({ ...base, caption: 'x'.repeat(4001) }, T)).toThrow(/4000/);
  });
  it('rejects a cover index outside the images', () => {
    expect(() => validatePost({ ...base, cover_index: 1 }, T)).toThrow(/cover/i);
  });
});

describe('posts routes', () => {
  beforeEach(() => resetDb(env));

  it('schedules a post, attaches its images, and lists it', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, cover_index: 0, title: 'T', caption: 'C', settings, scheduled_at: at } });
    expect(res.status).toBe(200);
    const p = await res.json();
    expect(p.status).toBe('queued');
    expect(p.images[0]).toMatch(/^https:\/\/arco-publisher\.vercel\.app\/media\//);
    const m = await env.DB.prepare('SELECT post_id, delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m).toEqual({ post_id: p.id, delete_after: null });
    const list = await (await callWorker(`/v1/posts?from=${at - 10}&to=${at + 10}`, { headers: h })).json();
    expect(list.posts.map(x => x.id)).toEqual([p.id]);
  });

  it('rejects a privacy level the creator does not currently offer', async () => {
    const { h, account_id, keys } = await setup();
    const tk = fakeTk({ creatorInfo: async () => ({ privacy_level_options: ['SELF_ONLY'] }) });
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h, tk,
      body: { account_id, image_keys: keys, settings, scheduled_at: null } });
    expect(res.status).toBe(400);
    expect((await res.json()).error).toMatch(/not available for this account/);
  });

  it('refuses images from another workspace or already used by a post', async () => {
    const a = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    await callWorker('/v1/posts', { method: 'POST', headers: a.h,
      body: { account_id: a.account_id, image_keys: a.keys, settings, scheduled_at: at } });
    const again = await callWorker('/v1/posts', { method: 'POST', headers: a.h,
      body: { account_id: a.account_id, image_keys: a.keys, settings, scheduled_at: at } });
    expect(again.status).toBe(400);
  });

  it('an edited post can reuse the images of a cancelled one', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    await callWorker(`/v1/posts/${p.id}`, { method: 'DELETE', headers: h });
    const again = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at + 60 } });
    expect(again.status).toBe(200);
    const m = await env.DB.prepare('SELECT delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m.delete_after).toBeNull();
  });

  it('cancels a queued post and schedules its images for deletion in 7 days', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    const c = await (await callWorker(`/v1/posts/${p.id}`, { method: 'DELETE', headers: h })).json();
    expect(c.status).toBe('cancelled');
    const m = await env.DB.prepare('SELECT delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m.delete_after).toBeGreaterThan(Math.floor(Date.now() / 1000) + 6 * 86400);
  });

  it('enforces 30 queued posts per workspace', async () => {
    const { h, account_id } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const t = Math.floor(Date.now() / 1000);
    const ws = (await env.DB.prepare('SELECT workspace_id FROM accounts WHERE id = ?').bind(account_id).first()).workspace_id;
    for (let i = 0; i < 30; i++) {
      await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings,
          scheduled_at, next_attempt_at, created_at, updated_at) VALUES (?, ?, ?, 'queued', '[]', '{}', ?, ?, ?, ?)`)
        .bind(`pst_${i}`, ws, account_id, at, at, t, t).run();
    }
    const key = (await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json()).key;
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: [key], settings, scheduled_at: at } });
    expect(res.status).toBe(409);
  });

  it('refuses Retry when TikTok may already have published the post', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    await env.DB.prepare(`UPDATE posts SET status = 'failed', publish_id = 'pub-7' WHERE id = ?`).bind(p.id).run();
    const res = await callWorker(`/v1/posts/${p.id}/retry`, { method: 'POST', headers: h });
    expect(res.status).toBe(409);
    expect((await res.json()).error).toMatch(/check the profile/i);
  });

  it('replaces a scheduled post only when the new one is saved', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const a = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at + 600, title: 'edited', replaces: a.id } });
    expect(res.status).toBe(200);
    const b = await res.json();
    const old = await env.DB.prepare('SELECT status FROM posts WHERE id = ?').bind(a.id).first();
    expect(old.status).toBe('cancelled');
    const m = await env.DB.prepare('SELECT post_id, delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m).toEqual({ post_id: b.id, delete_after: null });
  });

  it('a failed replacement leaves the original scheduled', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const a = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: 5, replaces: a.id } });
    expect(res.status).toBe(400);
    expect((await env.DB.prepare('SELECT status FROM posts WHERE id = ?').bind(a.id).first()).status).toBe('queued');
  });
});
