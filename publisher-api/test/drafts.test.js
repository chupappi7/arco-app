import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, fakeTk, signUp } from './helpers.js';
import { tick } from '../src/publisher.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1]);
const settings = { privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: false, auto_add_music: false,
                   brand_organic: false, branded_content: false };

async function setup() {
  const me = await signUp(env);
  const s = await (await callWorker('/internal/oauth', { method: 'POST', headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU, session_id: me.sid } })).json();
  const h = { Cookie: `tt_sid=${me.sid}` };
  const up = async () => (await (await callWorker('/v1/media', { method: 'POST',
    headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json()).key;
  return { h, me, account_id: s.account_id, up };
}
const call = (path, h, method = 'GET', body) => callWorker(path, { method, headers: h, body });

describe('drafts', () => {
  beforeEach(() => resetDb(env));

  it('saves a draft without privacy or time, never publishes it, and keeps it out of the calendar', async () => {
    const { h, account_id, up } = await setup();
    const group = 'grp_' + '0123456789abcdef';
    const res = await call('/v1/posts', h, 'POST', { account_id, image_keys: [await up()], caption: 'later', draft: true, group_id: group });
    expect(res.status).toBe(200);
    const d = await res.json();
    expect(d.status).toBe('draft');
    expect(d.group_id).toBe(group);
    await tick(env, fakeTk(), Math.floor(Date.now() / 1000) + 3600);
    const drafts = (await (await call('/v1/drafts', h)).json()).drafts;
    expect(drafts.map(x => [x.id, x.status])).toEqual([[d.id, 'draft']]);
    const t = Math.floor(Date.now() / 1000);
    const cal = (await (await call(`/v1/posts?from=${t - 86400}&to=${t + 86400}`, h)).json()).posts;
    expect(cal).toEqual([]);
  });

  it('deleting a draft removes it and frees its images', async () => {
    const { h, account_id, up } = await setup();
    const key = await up();
    const d = await (await call('/v1/posts', h, 'POST', { account_id, image_keys: [key], draft: true })).json();
    expect((await (await call(`/v1/posts/${d.id}`, h, 'DELETE')).json()).deleted).toBe(true);
    expect((await (await call('/v1/drafts', h)).json()).drafts).toEqual([]);
    const m = await env.DB.prepare('SELECT post_id, delete_after FROM media WHERE key = ?').bind(key).first();
    expect(m.post_id).toBeNull();
    expect(m.delete_after).not.toBeNull();
  });

  it('rejects a malformed group id', async () => {
    const { h, account_id, up } = await setup();
    const res = await call('/v1/posts', h, 'POST', { account_id, image_keys: [await up()], draft: true, group_id: 'x; drop' });
    expect(res.status).toBe(400);
  });
});

describe('quick edit', () => {
  beforeEach(() => resetDb(env));

  it('changes the caption and moves the time of a queued post', async () => {
    const { h, account_id, up } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await call('/v1/posts', h, 'POST', { account_id, image_keys: [await up()], settings, caption: 'old', scheduled_at: at })).json();
    const r = await (await call(`/v1/posts/${p.id}`, h, 'PATCH', { caption: 'new', scheduled_at: at + 600 })).json();
    expect(r.caption).toBe('new');
    expect(r.scheduled_at).toBe(at + 600);
    const row = await env.DB.prepare('SELECT next_attempt_at FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.next_attempt_at).toBe(at + 600);
  });

  it('refuses a time in the past, a caption over the limit, and a post that has started', async () => {
    const { h, account_id, up } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await call('/v1/posts', h, 'POST', { account_id, image_keys: [await up()], settings, scheduled_at: at })).json();
    expect((await call(`/v1/posts/${p.id}`, h, 'PATCH', { scheduled_at: at - 7200 })).status).toBe(400);
    expect((await call(`/v1/posts/${p.id}`, h, 'PATCH', { caption: 'x'.repeat(4001) })).status).toBe(400);
    await env.DB.prepare(`UPDATE posts SET status = 'publishing' WHERE id = ?`).bind(p.id).run();
    expect((await call(`/v1/posts/${p.id}`, h, 'PATCH', { caption: 'late' })).status).toBe(409);
  });

  it('cannot edit another workspace\'s post', async () => {
    const a = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await call('/v1/posts', a.h, 'POST', { account_id: a.account_id, image_keys: [await a.up()], settings, scheduled_at: at })).json();
    const b = await signUp(env);
    expect((await call(`/v1/posts/${p.id}`, { Cookie: `tt_sid=${b.sid}` }, 'PATCH', { caption: 'mine now' })).status).toBe(404);
  });
});
