import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, signUp } from './helpers.js';
import { notifyFailures } from '../src/notify.js';

const T = 1_800_000_000;
function mailbox(fail = false) {
  const sent = [];
  return { sent, send: async m => { if (fail) throw new Error('down'); sent.push(m); } };
}
async function failedPost(ws, id, { by = null, account = 'acc_1' } = {}) {
  await baseEnv.DB.prepare(`INSERT OR IGNORE INTO accounts (id, workspace_id, open_id, platform, username, refresh_token_enc,
      connected_at, token_updated_at) VALUES (?, ?, ?, 'instagram', 'bakery', 'x', 1, 1)`).bind(account, ws, `ig:${account}`).run();
  await baseEnv.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at,
      next_attempt_at, created_at, updated_at, fail_reason, created_by) VALUES (?, ?, ?, 'failed', '[]', '{}', ?, ?, 1, 1, 'Instagram said no', ?)`)
    .bind(id, ws, account, T, T, by).run();
}

describe('failure emails', () => {
  beforeEach(() => resetDb(baseEnv));

  it('one email per person listing every failure, sent once', async () => {
    const me = await signUp(baseEnv, 'maker@x.co');
    await failedPost(me.ws, 'p1', { by: me.userId });
    await failedPost(me.ws, 'p2', { by: me.userId });
    const mail = mailbox();
    const env = { ...baseEnv, __mail: mail };
    expect(await notifyFailures(env)).toBe(1);
    expect(mail.sent).toHaveLength(1);
    expect(mail.sent[0]).toMatchObject({ to: 'maker@x.co', subject: '2 posts failed to publish' });
    expect(mail.sent[0].text).toContain('Instagram said no');
    expect(await notifyFailures(env)).toBe(0);
  });

  it('goes to the owner when the maker has left, and to nobody outside the workspace', async () => {
    const owner = await signUp(baseEnv, 'owner@x.co');
    const other = await signUp(baseEnv, 'stranger@x.co');
    await failedPost(owner.ws, 'p1', { by: other.userId });    // not a member of owner.ws
    const mail = mailbox();
    await notifyFailures({ ...baseEnv, __mail: mail });
    expect(mail.sent.map(m => m.to)).toEqual(['owner@x.co']);
  });

  it('a failed send is retried on the next run', async () => {
    const me = await signUp(baseEnv);
    await failedPost(me.ws, 'p1', { by: me.userId });
    await notifyFailures({ ...baseEnv, __mail: mailbox(true) });
    const mail = mailbox();
    expect(await notifyFailures({ ...baseEnv, __mail: mail })).toBe(1);
  });
});
