import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, fakeTk, signUp } from './helpers.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';

async function signIn(openId = 'open-1') {
  const tk = fakeTk({ exchangeCode: async () => ({ access_token: 'at', refresh_token: 'rt', open_id: openId }) });
  const s = await (await callWorker('/internal/oauth', { method: 'POST', tk,
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU, session_id: (await signUp(env)).sid } })).json();
  return { h: { Cookie: `tt_sid=${s.session_id}` }, account: s.account_id };
}
const call = (path, h, method = 'GET', body) => callWorker(path, { method, headers: h, body });

describe('brands', () => {
  beforeEach(() => resetDb(env));

  it('creates a brand with accounts, lists it on /me, renames and deletes it', async () => {
    const { h, account } = await signIn();
    const b = await (await call('/v1/brands', h, 'POST', { name: '  Client   Bakery ', account_ids: [account] })).json();
    expect(b.name).toBe('Client Bakery');
    let me = await (await call('/v1/me', h)).json();
    expect(me.brands).toEqual([{ id: b.id, name: 'Client Bakery', slots: null }]);
    expect(me.accounts[0].brand_id).toBe(b.id);

    await call(`/v1/brands/${b.id}`, h, 'PATCH', { name: 'Bakery' });
    expect((await (await call('/v1/brands', h)).json()).brands[0].name).toBe('Bakery');

    await call(`/v1/brands/${b.id}`, h, 'DELETE');
    me = await (await call('/v1/me', h)).json();
    expect(me.brands).toEqual([]);
    expect(me.accounts[0].brand_id).toBeNull();     // ungrouped, not disconnected
  });

  it('moves an account between brands and out of them', async () => {
    const { h, account } = await signIn();
    const a = await (await call('/v1/brands', h, 'POST', { name: 'A' })).json();
    const b = await (await call('/v1/brands', h, 'POST', { name: 'B' })).json();
    await call(`/v1/brands/${a.id}/accounts`, h, 'POST', { account_ids: [account] });
    await call(`/v1/accounts/${account}`, h, 'PATCH', { brand_id: b.id });
    expect((await (await call('/v1/me', h)).json()).accounts[0].brand_id).toBe(b.id);
    await call(`/v1/accounts/${account}`, h, 'PATCH', { brand_id: null });
    expect((await (await call('/v1/me', h)).json()).accounts[0].brand_id).toBeNull();
  });

  it('never touches another workspace\'s brands or accounts', async () => {
    const one = await signIn('open-1');
    const two = await signIn('open-2');
    const theirs = await (await call('/v1/brands', two.h, 'POST', { name: 'Theirs' })).json();
    expect((await call(`/v1/brands/${theirs.id}`, one.h, 'PATCH', { name: 'x' })).status).toBe(404);
    expect((await call(`/v1/brands/${theirs.id}`, one.h, 'DELETE')).status).toBe(404);
    expect((await call(`/v1/brands/${theirs.id}/accounts`, one.h, 'POST', { account_ids: [one.account] })).status).toBe(404);
    const mine = await (await call('/v1/brands', one.h, 'POST', { name: 'Mine' })).json();
    expect((await call(`/v1/brands/${mine.id}/accounts`, one.h, 'POST', { account_ids: [two.account] })).status).toBe(404);
    expect((await call(`/v1/accounts/${two.account}`, one.h, 'PATCH', { brand_id: mine.id })).status).toBe(404);
  });

  it('stores posting times per brand and as the workspace default, and validates them', async () => {
    const { h } = await signIn();
    const b = await (await call('/v1/brands', h, 'POST', { name: 'Bakery' })).json();
    expect((await call(`/v1/brands/${b.id}`, h, 'PATCH', { slots: { days: [5, 1, 1], times: ['18:00', '09:00'] } })).status).toBe(200);
    expect((await call('/v1/workspace', h, 'PATCH', { slots: { days: [0, 6], times: ['10:30'] } })).status).toBe(200);
    const me = await (await call('/v1/me', h)).json();
    expect(me.brands[0]).toMatchObject({ name: 'Bakery', slots: { days: [1, 5], times: ['09:00', '18:00'] } });
    expect(me.workspace.slots).toEqual({ days: [0, 6], times: ['10:30'] });
    for (const slots of [{ days: [], times: ['09:00'] }, { days: [7], times: ['09:00'] }, { days: [1], times: ['9am'] }, { days: [1], times: ['24:00'] }]) {
      expect((await call(`/v1/brands/${b.id}`, h, 'PATCH', { slots })).status).toBe(400);
    }
    expect((await call(`/v1/brands/${b.id}`, h, 'PATCH', { slots: null })).status).toBe(200);
    expect((await (await call('/v1/me', h)).json()).brands[0].slots).toBeNull();
  });

  it('requires a name of sensible length', async () => {
    const { h } = await signIn();
    expect((await call('/v1/brands', h, 'POST', { name: '   ' })).status).toBe(400);
    expect((await call('/v1/brands', h, 'POST', { name: 'x'.repeat(61) })).status).toBe(400);
  });
});
