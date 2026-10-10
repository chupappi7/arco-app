import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk } from './helpers.js';
import { oauthIntake, resolveCaller, rotateApiKey } from '../src/auth.js';
import { accessTokenFor } from '../src/accounts.js';
import { decrypt } from '../src/crypto.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const intake = (tk, extra = {}) => oauthIntake(env, tk,
  { code: 'c', code_verifier: 'v', redirect_uri: RU, ...extra });

describe('oauth intake', () => {
  beforeEach(() => resetDb(env));

  it('first sign-in creates a workspace, an account and a session', async () => {
    const r = await intake(fakeTk());
    expect(r.workspace_id).toMatch(/^ws_/);
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(r.account_id).first();
    expect(acc.username).toBe('creator');
    expect(acc.refresh_token_enc).not.toContain('rt-1');
    expect(await decrypt(acc.refresh_token_enc, env.TOKEN_KEY)).toBe('rt-1');
    const caller = await resolveCaller(env, new Request('https://x', { headers: { Cookie: `tt_sid=${r.session_id}` } }));
    expect(caller).toEqual({ workspaceId: r.workspace_id, via: 'session' });
  });

  it('signing in again with the same TikTok account returns the same workspace', async () => {
    const a = await intake(fakeTk());
    const b = await intake(fakeTk());
    expect(b.workspace_id).toBe(a.workspace_id);
    expect(b.account_id).toBe(a.account_id);
  });

  it('Add account attaches a second TikTok account to the current workspace', async () => {
    const a = await intake(fakeTk());
    const b = await intake(fakeTk({ exchangeCode: async () => ({ access_token: 'at2', refresh_token: 'rt-2', open_id: 'open-2' }) }),
      { session_id: a.session_id });
    expect(b.workspace_id).toBe(a.workspace_id);
    const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id=?').bind(a.workspace_id).first();
    expect(n).toBe(2);
  });

  it('refuses to add an account that belongs to another workspace', async () => {
    await intake(fakeTk());                                   // open-1 -> workspace A
    const other = await intake(fakeTk({ exchangeCode: async () => ({ access_token: 'x', refresh_token: 'y', open_id: 'open-9' }) }));
    await expect(intake(fakeTk(), { session_id: other.session_id })).rejects.toMatchObject({ status: 409 });
  });

  it('an added account cannot be used to sign into the workspace it was added to', async () => {
    const a = await intake(fakeTk());
    await intake(fakeTk({ exchangeCode: async () => ({ access_token: 'at', refresh_token: 'rt-2', open_id: 'open-2' }) }),
      { session_id: a.session_id });
    await expect(intake(fakeTk({ exchangeCode: async () => ({ access_token: 'at', refresh_token: 'rt-2', open_id: 'open-2' }) })))
      .rejects.toThrow(/someone else/);
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
    expect(await resolveCaller(env, req(k2))).toEqual({ workspaceId: workspace_id, via: 'key' });
    expect(await resolveCaller(env, req(k1))).toBeNull();
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

