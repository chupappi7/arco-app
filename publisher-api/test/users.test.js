import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, fakeTk, signUp } from './helpers.js';
import { startEmail, verifyEmail, callerFor } from '../src/users.js';
import { encrypt } from '../src/crypto.js';

// Mail double: remembers what was sent.
function mailbox() {
  const sent = [];
  return { sent, send: async m => { sent.push(m); }, codeFor: to => sent.filter(m => m.to === to).at(-1)?.subject.slice(0, 6),
    linkFor: to => sent.filter(m => m.to === to).at(-1)?.text.match(/https:\S+/)?.[0] };
}
const T = 1_800_000_000;
const cookie = sid => ({ Cookie: `tt_sid=${sid}` });
const req = (sid, path, method = 'GET', body, env = baseEnv) => callWorker(path, { method, headers: cookie(sid), body, env });

describe('email sign-in', () => {
  let env, mail;
  beforeEach(async () => { await resetDb(baseEnv); mail = mailbox(); env = { ...baseEnv, __mail: mail }; });

  it('a code signs a new person up with their own workspace, and signs them back into it later', async () => {
    await startEmail(env, { email: ' Pat@Example.com ' });
    const code = mail.codeFor('pat@example.com');
    expect(code).toMatch(/^\d{6}$/);
    const a = await verifyEmail(env, { email: 'pat@example.com', code });
    const who = await callerFor(env, new Request('https://x', { headers: cookie(a.session_id) }));
    expect(who).toMatchObject({ ws: a.workspace_id, role: 'owner' });
    await startEmail(env, { email: 'pat@example.com' });
    const b = await verifyEmail(env, { email: 'PAT@example.com', code: mail.codeFor('pat@example.com') });
    expect(b.workspace_id).toBe(a.workspace_id);
  });

  it('a code works once, wrong guesses run out, and the code is stored only as a hash', async () => {
    await startEmail(env, { email: 'a@b.co' });
    const code = mail.codeFor('a@b.co');
    const row = await baseEnv.DB.prepare('SELECT code_hash FROM login_codes').first();
    expect(row.code_hash).not.toContain(code);
    const wrong = code === '000000' ? '111111' : '000000';
    for (let i = 0; i < 4; i++) await expect(verifyEmail(env, { email: 'a@b.co', code: wrong })).rejects.toMatchObject({ status: 400 });
    await expect(verifyEmail(env, { email: 'a@b.co', code: wrong })).rejects.toMatchObject({ status: 400 });
    // Fifth wrong guess used the last attempt: even the right code is refused now.
    await expect(verifyEmail(env, { email: 'a@b.co', code })).rejects.toMatchObject({ status: 400 });
  });

  it('guesses sent in parallel cannot exceed five attempts', async () => {
    await startEmail(env, { email: 'p@b.co' });
    const code = mail.codeFor('p@b.co');
    const wrong = code === '000000' ? '111111' : '000000';
    await Promise.allSettled(Array.from({ length: 12 }, () => verifyEmail(env, { email: 'p@b.co', code: wrong })));
    const row = await baseEnv.DB.prepare('SELECT attempts FROM login_codes WHERE email = ?').bind('p@b.co').first();
    expect(row.attempts).toBe(5);
    await expect(verifyEmail(env, { email: 'p@b.co', code })).rejects.toMatchObject({ status: 400 });
  });

  it('parallel code requests cannot exceed the hourly cap', async () => {
    await Promise.allSettled(Array.from({ length: 12 }, () => startEmail(env, { email: 'flood@b.co' })));
    const { n } = await baseEnv.DB.prepare('SELECT COUNT(*) AS n FROM login_codes WHERE email = ?').bind('flood@b.co').first();
    expect(n).toBe(5);
  });

  it('a used code cannot be replayed', async () => {
    await startEmail(env, { email: 'a@b.co' });
    const code = mail.codeFor('a@b.co');
    await verifyEmail(env, { email: 'a@b.co', code });
    await expect(verifyEmail(env, { email: 'a@b.co', code })).rejects.toMatchObject({ status: 400 });
  });

  it('limits codes per hour and answers the same whether or not the person exists', async () => {
    for (let i = 0; i < 5; i++) expect(await startEmail(env, { email: 'x@y.co' })).toEqual({ ok: true });
    await expect(startEmail(env, { email: 'x@y.co' })).rejects.toMatchObject({ status: 429 });
    await expect(startEmail(env, { email: 'not-an-email' })).rejects.toMatchObject({ status: 400 });
  });

  it('the start endpoint is public; verification is internal only', async () => {
    const res = await callWorker('/v1/auth/email/start', { method: 'POST', body: { email: 'q@w.co' }, env });
    expect(res.status).toBe(200);
    expect((await callWorker('/internal/email-verify', { method: 'POST', body: { email: 'q@w.co', code: '123456' } })).status).toBe(403);
  });

  it('an old TikTok-only workspace becomes the verifying person\'s, once', async () => {
    await baseEnv.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, 1)').bind('ws_old').run();
    const { createSession } = await import('../src/auth.js');
    const legacy = await createSession(baseEnv, 'ws_old');
    await startEmail(env, { email: 'old@owner.co' });
    const r = await verifyEmail(env, { email: 'old@owner.co', code: mail.codeFor('old@owner.co'), legacy_session: legacy });
    expect(r.workspace_id).toBe('ws_old');
    // Someone else can't claim it afterwards with a stale legacy session.
    await startEmail(env, { email: 'thief@x.co' });
    const t = await verifyEmail(env, { email: 'thief@x.co', code: mail.codeFor('thief@x.co'), legacy_session: legacy });
    expect(t.workspace_id).not.toBe('ws_old');
  });
});

describe('members, roles and invites', () => {
  let env, mail;
  beforeEach(async () => { await resetDb(baseEnv); mail = mailbox(); env = { ...baseEnv, __mail: mail }; });

  async function join(owner, email, body) {
    expect((await req(owner.sid, '/v1/invites', 'POST', { email, ...body }, env)).status).toBe(200);
    const token = new URL(mail.linkFor(email)).searchParams.get('invite');
    const them = await signUp(baseEnv, email);
    const res = await req(them.sid, '/v1/invites/accept', 'POST', { token }, env);
    return { ...them, res, token };
  }

  it('an invite only works for the address it was sent to', async () => {
    const owner = await signUp(baseEnv);
    await req(owner.sid, '/v1/invites', 'POST', { email: 'right@x.co' }, env);
    const token = new URL(mail.linkFor('right@x.co')).searchParams.get('invite');
    const wrong = await signUp(baseEnv, 'wrong@x.co');
    expect((await req(wrong.sid, '/v1/invites/accept', 'POST', { token }, env)).status).toBe(403);
    const right = await signUp(baseEnv, 'right@x.co');
    expect((await req(right.sid, '/v1/invites/accept', 'POST', { token }, env)).status).toBe(200);
    // and only once
    expect((await req(right.sid, '/v1/invites/accept', 'POST', { token }, env)).status).toBe(404);
  });

  it('members cannot manage people, accounts, brands, keys or the workspace', async () => {
    const owner = await signUp(baseEnv);
    const m = await join(owner, 'm@x.co', { role: 'member' });
    for (const [path, method, body] of [
      ['/v1/members', 'GET'], ['/v1/invites', 'POST', { email: 'z@x.co' }], ['/v1/brands', 'POST', { name: 'B' }],
      ['/v1/api-key', 'POST'], ['/v1/me', 'DELETE'], ['/v1/workspace', 'PATCH', { name: 'x' }],
    ]) expect((await req(m.sid, path, method, body, env)).status, path).toBe(403);
  });

  it('an admin cannot remove the owner or another admin; the owner cannot be demoted', async () => {
    const owner = await signUp(baseEnv);
    const a1 = await join(owner, 'a1@x.co', { role: 'admin' });
    const a2 = await join(owner, 'a2@x.co', { role: 'admin' });
    expect((await req(a1.sid, `/v1/members/${owner.userId}`, 'DELETE', undefined, env)).status).toBe(403);
    expect((await req(a1.sid, `/v1/members/${a2.userId}`, 'DELETE', undefined, env)).status).toBe(403);
    expect((await req(a1.sid, `/v1/members/${owner.userId}`, 'PATCH', { role: 'member' }, env)).status).toBe(403);
    expect((await req(owner.sid, `/v1/members/${a2.userId}`, 'DELETE', undefined, env)).status).toBe(200);
  });

  it('only the owner makes, changes, cancels or removes admins; admins manage members', async () => {
    const owner = await signUp(baseEnv);
    const a1 = await join(owner, 'adm1@x.co', { role: 'admin' });
    const a2 = await join(owner, 'adm2@x.co', { role: 'admin' });
    const m = await join(owner, 'mem@x.co', { role: 'member' });
    expect((await req(a1.sid, `/v1/members/${a2.userId}`, 'PATCH', { role: 'member' }, env)).status).toBe(403);
    expect((await req(a1.sid, `/v1/members/${m.userId}`, 'PATCH', { role: 'admin' }, env)).status).toBe(403);
    expect((await req(a1.sid, '/v1/invites', 'POST', { email: 'new-admin@x.co', role: 'admin' }, env)).status).toBe(403);
    expect((await req(a1.sid, '/v1/invites', 'POST', { email: 'new-member@x.co', role: 'member' }, env)).status).toBe(200);
    await req(owner.sid, '/v1/invites', 'POST', { email: 'owner-made-admin@x.co', role: 'admin' }, env);
    const { invites } = await (await req(owner.sid, '/v1/members', 'GET', undefined, env)).json();
    const adminInvite = invites.find(i => i.role === 'admin');
    expect((await req(a1.sid, `/v1/invites/${adminInvite.id}`, 'DELETE', undefined, env)).status).toBe(403);
    // nor by re-inviting the same address as a member
    expect((await req(a1.sid, '/v1/invites', 'POST', { email: 'owner-made-admin@x.co', role: 'member' }, env)).status).toBe(403);
    const after = (await (await req(owner.sid, '/v1/members', 'GET', undefined, env)).json()).invites;
    expect(after.find(i => i.email === 'owner-made-admin@x.co').role).toBe('admin');
    expect((await req(owner.sid, `/v1/members/${a2.userId}`, 'PATCH', { role: 'member' }, env)).status).toBe(200);
  });

  it('an API key cannot see or manage people', async () => {
    const owner = await signUp(baseEnv);
    const m = await join(owner, 'k@x.co', { role: 'member' });
    const { rotateApiKey } = await import('../src/auth.js');
    const key = { Authorization: `Key ${await rotateApiKey(baseEnv, owner.ws)}` };
    const k = (path, method = 'GET', body) => callWorker(path, { method, headers: key, body, env });
    expect((await k('/v1/members')).status).toBe(403);
    expect((await k('/v1/invites', 'POST', { email: 'z@x.co' })).status).toBe(403);
    expect((await k(`/v1/members/${m.userId}`, 'PATCH', { role: 'member', brand_ids: null })).status).toBe(403);
    expect((await k(`/v1/members/${m.userId}`, 'DELETE')).status).toBe(403);
  });

  it('the owner can hand the workspace to a member, and nobody else can', async () => {
    const owner = await signUp(baseEnv);
    const adm = await join(owner, 'next@x.co', { role: 'admin' });
    const mem = await join(owner, 'm2@x.co', { role: 'member' });
    expect((await req(adm.sid, '/v1/workspace/transfer', 'POST', { user_id: adm.userId }, env)).status).toBe(403);
    expect((await req(owner.sid, '/v1/workspace/transfer', 'POST', { user_id: 'usr_nobody' }, env)).status).toBe(404);
    expect((await req(owner.sid, '/v1/workspace/transfer', 'POST', { user_id: adm.userId }, env)).status).toBe(200);
    const roles = Object.fromEntries((await (await req(adm.sid, '/v1/members', 'GET', undefined, env)).json()).members.map(x => [x.email, x.role]));
    expect(roles['next@x.co']).toBe('owner');
    expect(Object.values(roles).filter(r => r === 'owner')).toHaveLength(1);
    expect(roles[mem.email]).toBe('member');
    // the old owner is an admin now and cannot take it back
    expect((await req(owner.sid, '/v1/workspace/transfer', 'POST', { user_id: owner.userId }, env)).status).toBe(403);
  });

  it('ownership cannot be handed to someone who already owns the maximum', async () => {
    const owner = await signUp(baseEnv);
    const full = await join(owner, 'full@x.co', { role: 'member' });
    for (let i = 0; i < 9; i++) await req(full.sid, '/v1/workspaces', 'POST', { name: `w${i}` }, env);   // 1 own + 9 = 10
    await req(full.sid, '/v1/session/workspace', 'POST', { workspace_id: owner.ws }, env);
    expect((await req(owner.sid, '/v1/workspace/transfer', 'POST', { user_id: full.userId }, env)).status).toBe(409);
  });

  it('someone removed from a workspace loses it on their very next request', async () => {
    const owner = await signUp(baseEnv);
    const m = await join(owner, 'gone@x.co', { role: 'member' });
    expect((await (await req(m.sid, '/v1/me', 'GET', undefined, env)).json()).workspace.id).toBe(owner.ws);
    await req(owner.sid, `/v1/members/${m.userId}`, 'DELETE', undefined, env);
    expect((await (await req(m.sid, '/v1/me', 'GET', undefined, env)).json()).workspace.id).not.toBe(owner.ws);
  });

  it('admins set the workspace time zone; unknown zones are refused', async () => {
    const owner = await signUp(baseEnv);
    expect((await req(owner.sid, '/v1/workspace', 'PATCH', { timezone: 'America/New_York' }, env)).status).toBe(200);
    expect((await (await req(owner.sid, '/v1/me', 'GET', undefined, env)).json()).workspace.timezone).toBe('America/New_York');
    expect((await req(owner.sid, '/v1/workspace', 'PATCH', { timezone: 'Mars/Olympus' }, env)).status).toBe(400);
    const m = await join(owner, 'tz@x.co', { role: 'member' });
    expect((await req(m.sid, '/v1/workspace', 'PATCH', { timezone: 'UTC' }, env)).status).toBe(403);
  });

  it('nobody can switch into a workspace they are not a member of', async () => {
    const a = await signUp(baseEnv), b = await signUp(baseEnv);
    expect((await req(a.sid, '/v1/session/workspace', 'POST', { workspace_id: b.ws }, env)).status).toBe(404);
  });

  it('sign out everywhere ends every session of that person', async () => {
    const a = await signUp(baseEnv);
    const { newSession } = await import('../src/users.js');
    const second = await newSession(baseEnv, a.userId, a.ws);
    await req(a.sid, '/v1/logout-all', 'POST', undefined, env);
    expect((await req(second, '/v1/me', 'GET', undefined, env)).status).toBe(401);
  });
});

describe('isolation', () => {
  let env, mail;
  beforeEach(async () => { await resetDb(baseEnv); mail = mailbox(); env = { ...baseEnv, __mail: mail }; });

  // Two workspaces, each with a brand, an account in it, and a post with an image.
  async function world() {
    const make = async (tag) => {
      const o = await signUp(baseEnv, `${tag}@x.co`);
      const acc = `acc_${tag}`, brand = `brd_${tag}`, post = `pst_${tag}`, key = `${o.ws}/${tag}.jpg`;
      await baseEnv.DB.prepare('INSERT INTO brands (id, workspace_id, name, created_at) VALUES (?, ?, ?, 1)').bind(brand, o.ws, tag).run();
      await baseEnv.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, username, refresh_token_enc, connected_at, token_updated_at, brand_id)
          VALUES (?, ?, ?, ?, ?, 1, 1, ?)`).bind(acc, o.ws, `open-${tag}`, tag, await encrypt('rt', baseEnv.TOKEN_KEY), brand).run();
      await baseEnv.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at,
          next_attempt_at, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, '{}', ?, ?, 1, 1)`)
        .bind(post, o.ws, acc, JSON.stringify([key]), T, T).run();
      await baseEnv.MEDIA.put(key, new Uint8Array([0xff, 0xd8, 0xff, 1]));
      await baseEnv.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, post_id) VALUES (?, ?, 4, 'image/jpeg', 1, ?)`)
        .bind(key, o.ws, post).run();
      return { ...o, acc, brand, post, key };
    };
    return { a: await make('alpha'), b: await make('beta') };
  }

  it('one workspace can see or touch nothing of another\'s', async () => {
    const { a, b } = await world();
    const me = await (await req(a.sid, '/v1/me', 'GET', undefined, env)).json();
    expect(me.accounts.map(x => x.id)).toEqual([a.acc]);
    expect(me.brands.map(x => x.id)).toEqual([a.brand]);
    const posts = (await (await req(a.sid, `/v1/posts?from=${T - 10}&to=${T + 10}`, 'GET', undefined, env)).json()).posts;
    expect(posts.map(p => p.id)).toEqual([a.post]);
    for (const [path, method, body] of [
      [`/v1/accounts/${b.acc}/creator-info`, 'GET'], [`/v1/accounts/${b.acc}`, 'DELETE'],
      [`/v1/accounts/${b.acc}`, 'PATCH', { brand_id: a.brand }], [`/v1/brands/${b.brand}`, 'PATCH', { name: 'x' }],
      [`/v1/brands/${b.brand}`, 'DELETE'], [`/v1/posts/${b.post}`, 'DELETE'], [`/v1/posts/${b.post}/retry`, 'POST'],
      ['/v1/posts', 'POST', { account_id: b.acc, image_keys: [a.key], caption: 'x' }],
      ['/v1/media/copy', 'POST', { keys: [b.key] }], [`/v1/members/${b.userId}`, 'PATCH', { role: 'member' }],
    ]) {
      const res = await req(a.sid, path, method, body, { ...env, __tk: fakeTk() });
      expect([400, 403, 404], `${method} ${path} -> ${res.status}`).toContain(res.status);
    }
    // and nothing of b's changed
    expect((await baseEnv.DB.prepare('SELECT status FROM posts WHERE id = ?').bind(b.post).first()).status).toBe('queued');
    expect((await baseEnv.DB.prepare('SELECT brand_id FROM accounts WHERE id = ?').bind(b.acc).first()).brand_id).toBe(b.brand);
    expect((await baseEnv.DB.prepare('SELECT name FROM brands WHERE id = ?').bind(b.brand).first()).name).toBe('beta');
  });

  it('a member limited to one brand sees and acts only within it', async () => {
    const owner = await signUp(baseEnv, 'agency@x.co');
    const mk = async (tag) => {
      const brand = `brd_${tag}`, acc = `acc_${tag}`, post = `pst_${tag}`, key = `${owner.ws}/${tag}.jpg`;
      await baseEnv.DB.prepare('INSERT INTO brands (id, workspace_id, name, created_at) VALUES (?, ?, ?, 1)').bind(brand, owner.ws, tag).run();
      await baseEnv.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, username, refresh_token_enc, connected_at, token_updated_at, brand_id)
          VALUES (?, ?, ?, ?, ?, 1, 1, ?)`).bind(acc, owner.ws, `open-${tag}`, tag, await encrypt('rt', baseEnv.TOKEN_KEY), brand).run();
      await baseEnv.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at,
          next_attempt_at, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, '{}', ?, ?, 1, 1)`)
        .bind(post, owner.ws, acc, JSON.stringify([key]), T, T).run();
      await baseEnv.MEDIA.put(key, new Uint8Array([0xff, 0xd8, 0xff, 1]));
      await baseEnv.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, post_id) VALUES (?, ?, 4, 'image/jpeg', 1, ?)`)
        .bind(key, owner.ws, post).run();
      return { brand, acc, post, key };
    };
    const bakery = await mk('bakery'), gym = await mk('gym');
    // an account in no brand at all
    await baseEnv.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, username, refresh_token_enc, connected_at, token_updated_at)
        VALUES ('acc_loose', ?, 'open-loose', 'loose', 'x', 1, 1)`).bind(owner.ws).run();

    await req(owner.sid, '/v1/invites', 'POST', { email: 'free@x.co', role: 'member', brand_ids: [bakery.brand] }, env);
    const token = new URL(mail.linkFor('free@x.co')).searchParams.get('invite');
    const free = await signUp(baseEnv, 'free@x.co');
    await req(free.sid, '/v1/invites/accept', 'POST', { token }, env);

    const me = await (await req(free.sid, '/v1/me', 'GET', undefined, env)).json();
    expect(me.workspace).toMatchObject({ id: owner.ws, role: 'member', brand_scope: [bakery.brand] });
    expect(me.accounts.map(x => x.id)).toEqual([bakery.acc]);
    expect(me.brands.map(x => x.id)).toEqual([bakery.brand]);
    const posts = (await (await req(free.sid, `/v1/posts?from=${T - 10}&to=${T + 10}`, 'GET', undefined, env)).json()).posts;
    expect(posts.map(p => p.id)).toEqual([bakery.post]);

    const tkEnv = { ...env, __tk: fakeTk() };
    expect((await req(free.sid, `/v1/accounts/${gym.acc}/creator-info`, 'GET', undefined, tkEnv)).status).toBe(404);
    expect((await req(free.sid, `/v1/posts/${gym.post}`, 'DELETE', undefined, env)).status).toBe(404);
    expect((await req(free.sid, '/v1/media/copy', 'POST', { keys: [gym.key] }, env)).status).toBe(404);
    expect((await req(free.sid, '/v1/media/copy', 'POST', { keys: [bakery.key] }, env)).status).toBe(200);
    expect((await req(free.sid, '/v1/posts', 'POST', { account_id: 'acc_loose', image_keys: [bakery.key], caption: 'x' }, tkEnv)).status).toBe(404);
    expect((await baseEnv.DB.prepare('SELECT status FROM posts WHERE id = ?').bind(gym.post).first()).status).toBe('queued');
  });

  it('invites can only scope a member to brands of this workspace', async () => {
    const { a, b } = await world();
    const res = await req(a.sid, '/v1/invites', 'POST', { email: 'n@x.co', role: 'member', brand_ids: [b.brand] }, env);
    expect(res.status).toBe(404);
  });
});
