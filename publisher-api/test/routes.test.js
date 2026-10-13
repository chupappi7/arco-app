import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, signUp } from './helpers.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';

async function signIn() {
  const res = await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU, session_id: (await signUp(env)).sid } });
  return res.json();
}

describe('routes', () => {
  beforeEach(() => resetDb(env));

  it('/internal/oauth requires the internal secret', async () => {
    const res = await callWorker('/internal/oauth', { method: 'POST', body: { code: 'c' } });
    expect(res.status).toBe(403);
  });

  it('/v1/me needs a session or key', async () => {
    expect((await callWorker('/v1/me')).status).toBe(401);
    const s = await signIn();
    const res = await callWorker('/v1/me', { headers: { Cookie: `tt_sid=${s.session_id}` } });
    expect(res.status).toBe(200);
    const me = await res.json();
    expect(me.accounts).toHaveLength(1);
    expect(me.accounts[0].username).toBe('creator');
    expect(me.accounts[0]).not.toHaveProperty('refresh_token_enc');
  });

  it('POST /v1/api-key returns a key that works as Authorization: Key', async () => {
    const s = await signIn();
    const { api_key } = await (await callWorker('/v1/api-key', { method: 'POST',
      headers: { Cookie: `tt_sid=${s.session_id}` } })).json();
    expect(api_key).toMatch(/^apk_/);
    const res = await callWorker('/v1/accounts', { headers: { Authorization: `Key ${api_key}` } });
    expect(res.status).toBe(200);
  });

  it('creator-info for an account in another workspace is 404', async () => {
    const s = await signIn();
    const res = await callWorker('/v1/accounts/acc_nope/creator-info', { headers: { Cookie: `tt_sid=${s.session_id}` } });
    expect(res.status).toBe(404);
  });

  it('unknown paths are 404 JSON', async () => {
    const res = await callWorker('/nope');
    expect(res.status).toBe(404);
    expect((await res.json()).error).toBeTruthy();
  });
});
