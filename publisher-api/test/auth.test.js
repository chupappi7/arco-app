import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk, signUp } from './helpers.js';
import { oauthIntake, rotateApiKey } from '../src/auth.js';
import { callerFor } from '../src/users.js';
import { accessTokenFor } from '../src/accounts.js';
import { decrypt } from '../src/crypto.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
// Signed in as a new workspace's owner unless a session_id (or null) is given.
const intake = async (tk, extra = {}) => oauthIntake(env, tk, { code: 'c', code_verifier: 'v', redirect_uri: RU,
  session_id: 'session_id' in extra ? extra.session_id : (await signUp(env)).sid, ...extra });
const tk2 = () => fakeTk({ exchangeCode: async () => ({ access_token: 'at', refresh_token: 'rt-2', open_id: 'open-2' }) });

describe('oauth intake', () => {
  beforeEach(() => resetDb(env));

  it('connects TikTok into the signed-in owner\'s workspace, token encrypted', async () => {
    const me = await signUp(env);
    const r = await intake(fakeTk(), { session_id: me.sid });
    expect(r.workspace_id).toBe(me.ws);
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(r.account_id).first();
    expect(acc.username).toBe('creator');
    expect(acc.refresh_token_enc).not.toContain('rt-1');
    expect(await decrypt(acc.refresh_token_enc, env.TOKEN_KEY)).toBe('rt-1');
    const caller = await callerFor(env, new Request('https://x', { headers: { Cookie: `tt_sid=${r.session_id}` } }));
    expect(caller).toMatchObject({ ws: me.ws, userId: me.userId, role: 'owner', scope: null });
  });

  it('without a session, TikTok cannot create a workspace', async () => {
    await expect(intake(fakeTk(), { session_id: null })).rejects.toMatchObject({ status: 401 });
  });

  it('a workspace from before email sign-in opens with its TikTok until an email claims it', async () => {
    const { encrypt } = await import('../src/crypto.js');
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, 1)').bind('ws_old').run();
    await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, refresh_token_enc, connected_at, token_updated_at, can_sign_in)
        VALUES ('acc_old', 'ws_old', 'open-1', ?, 1, 1, 1)`).bind(await encrypt('rt', env.TOKEN_KEY)).run();
    const r = await intake(fakeTk(), { session_id: null });
    expect(r.workspace_id).toBe('ws_old');
    const legacy = await callerFor(env, new Request('https://x', { headers: { Cookie: `tt_sid=${r.session_id}` } }));
    expect(legacy).toMatchObject({ ws: 'ws_old', via: 'legacy' });
    await env.DB.prepare(`INSERT INTO memberships (workspace_id, user_id, role, created_at) VALUES ('ws_old', 'usr_x', 'owner', 1)`).run();
    await expect(intake(fakeTk(), { session_id: null })).rejects.toMatchObject({ status: 401 });
    expect(await callerFor(env, new Request('https://x', { headers: { Cookie: `tt_sid=${r.session_id}` } }))).toBeNull();
  });

  it('a member (not admin) cannot connect accounts', async () => {
    const me = await signUp(env);
    await env.DB.prepare(`UPDATE memberships SET role = 'member' WHERE user_id = ?`).bind(me.userId).run();
    await expect(intake(fakeTk(), { session_id: me.sid })).rejects.toMatchObject({ status: 403 });
  });

  it('Add account attaches a second TikTok account to the current workspace', async () => {
    const a = await intake(fakeTk());
    const b = await intake(tk2(), { session_id: a.session_id });
    expect(b.workspace_id).toBe(a.workspace_id);
    const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id=?').bind(a.workspace_id).first();
    expect(n).toBe(2);
  });

  it('refuses to add an account that belongs to another workspace', async () => {
    await intake(fakeTk());                                   // open-1 -> workspace A
    await expect(intake(fakeTk())).rejects.toMatchObject({ status: 409 });   // workspace B wants it too
  });

  it('an added account cannot be used to sign into the workspace it was added to', async () => {
    const a = await intake(fakeTk());
    await intake(tk2(), { session_id: a.session_id });
    await expect(intake(tk2(), { session_id: null })).rejects.toThrow(/someone else/);
  });

  it('rejects an unexpected redirect_uri', async () => {
    await expect(oauthIntake(env, fakeTk(), { code: 'c', code_verifier: 'v', redirect_uri: 'https://evil/cb' }))
      .rejects.toMatchObject({ status: 400 });
  });
});

describe('api keys', () => {
  beforeEach(() => resetDb(env));

  it('a rotated key authenticates and the previous key stops working', async () => {
    const { workspace_id } = await intake(fakeTk());
    const k1 = await rotateApiKey(env, workspace_id);
    const k2 = await rotateApiKey(env, workspace_id);
    const req = k => new Request('https://x', { headers: { Authorization: `Key ${k}` } });
    expect(await callerFor(env, req(k2))).toMatchObject({ ws: workspace_id, via: 'key', role: 'admin' });
    expect(await callerFor(env, req(k1))).toBeNull();
  });
});

describe('accessTokenFor', () => {
  beforeEach(() => resetDb(env));

  it('stores a rotated refresh token', async () => {
    const { account_id } = await intake(fakeTk());
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(account_id).first();
    await accessTokenFor(env, fakeTk({ refresh: async () => ({ access_token: 'new', refresh_token: 'rt-rotated' }) }), acc);
    const after = await env.DB.prepare('SELECT refresh_token_enc FROM accounts WHERE id=?').bind(account_id).first();
    expect(await decrypt(after.refresh_token_enc, env.TOKEN_KEY)).toBe('rt-rotated');
  });

  it('a revoked token flags the account and rethrows', async () => {
    const { account_id } = await intake(fakeTk());
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(account_id).first();
    const revoked = fakeTk({ refresh: async () => { const e = new Error('Reconnect this account'); e.code = 'needs_reconnect'; throw e; } });
    await expect(accessTokenFor(env, revoked, acc)).rejects.toMatchObject({ code: 'needs_reconnect' });
    const after = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id=?').bind(account_id).first();
    expect(after.needs_reconnect).toBe(1);
  });
});

describe('access token reuse and rotation races', () => {
  beforeEach(() => resetDb(env));

  it('reuses a fresh access token instead of refreshing every call', async () => {
    const { account_id } = await intake(fakeTk());
    let refreshes = 0;
    const tk = fakeTk({ refresh: async () => { refreshes++; return { access_token: 'at-x', refresh_token: 'rt-1', expires_in: 86400 }; } });
    const load = () => env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(account_id).first();
    expect(await accessTokenFor(env, tk, await load())).toBe('at-x');
    expect(await accessTokenFor(env, tk, await load())).toBe('at-x');
    expect(refreshes).toBe(1);
    const row = await load();
    expect(row.access_token_enc).not.toContain('at-x');
  });

  it('does not flag an account when a parallel refresh already rotated its token', async () => {
    const { account_id } = await intake(fakeTk());
    const stale = await env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(account_id).first();
    // Another caller refreshed first and stored rt-2; our rt-1 is now dead.
    const { encrypt } = await import('../src/crypto.js');
    await env.DB.prepare('UPDATE accounts SET refresh_token_enc = ? WHERE id = ?')
      .bind(await encrypt('rt-2', env.TOKEN_KEY), account_id).run();
    const tk = fakeTk({ refresh: async rt => {
      if (rt === 'rt-1') { const e = new Error('Reconnect this account'); e.code = 'needs_reconnect'; throw e; }
      return { access_token: 'at-2', refresh_token: 'rt-2', expires_in: 86400 };
    } });
    expect(await accessTokenFor(env, tk, stale)).toBe('at-2');
    const row = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id = ?').bind(account_id).first();
    expect(row.needs_reconnect).toBe(0);
  });
});

