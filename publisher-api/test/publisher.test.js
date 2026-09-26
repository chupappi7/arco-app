import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk } from './helpers.js';
import { claimDue, tick } from '../src/publisher.js';
import { encrypt } from '../src/crypto.js';
import { TikTokError } from '../src/tiktok.js';

const T = 1_800_000_000;
const settings = JSON.stringify({ privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: false,
  auto_add_music: false, brand_organic: false, branded_content: false });

async function seed({ posts = 1, account = 'acc_1', status = 'queued', at = T } = {}) {
  await env.DB.prepare('INSERT OR IGNORE INTO workspaces (id, created_at) VALUES (?, ?)').bind('ws_1', T).run();
  await env.DB.prepare(`INSERT OR IGNORE INTO accounts (id, workspace_id, open_id, username, refresh_token_enc,
      connected_at, token_updated_at) VALUES (?, 'ws_1', ?, 'creator', ?, ?, ?)`)
    .bind(account, `open-${account}`, await encrypt('rt-1', env.TOKEN_KEY), T, T).run();
  for (let i = 0; i < posts; i++) {
    const id = `pst_${account}_${i}`;
    await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings,
        scheduled_at, next_attempt_at, created_at, updated_at) VALUES (?, 'ws_1', ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, account, status, JSON.stringify([`ws_1/${account}-${i}.jpg`]), settings, at, at, T, T).run();
    await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, post_id)
        VALUES (?, 'ws_1', 1, 'image/jpeg', ?, ?)`).bind(`ws_1/${account}-${i}.jpg`, T, id).run();
  }
}
const post = id => env.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(id).first();

describe('publisher', () => {
  beforeEach(() => resetDb(env));

  it('claims a due post exactly once across overlapping ticks', async () => {
    await seed();
    const a = await claimDue(env, T);
    const b = await claimDue(env, T);
    expect(a).toHaveLength(1);
    expect(b).toHaveLength(0);
  });

  it('does not claim posts that are not due yet', async () => {
    await seed({ at: T + 60 });
    expect(await claimDue(env, T)).toHaveLength(0);
  });

  it('starts a due post with a PULL_FROM_URL body on the verified domain', async () => {
    await seed();
    let body;
    const tk = fakeTk({ initPhoto: async (at, b) => { body = b; return { publish_id: 'pub-9' }; },
                       status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) });
    await tick(env, tk, T);
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('publishing');
    expect(p.publish_id).toBe('pub-9');
    expect(body.source_info.photo_images).toEqual(['https://arco-publisher.vercel.app/media/ws_1/acc_1-0.jpg']);
  });

  it('marks published when TikTok confirms and schedules image deletion in 7 days', async () => {
    await seed();
    await tick(env, fakeTk(), T);          // init + first poll in the same tick
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('published');
    expect(p.public_post_id).toBe('7500000000000000001');
    const m = await env.DB.prepare('SELECT delete_after FROM media WHERE post_id = ?').bind(p.id).first();
    expect(m.delete_after).toBe(T + 7 * 86400);
  });

  it('fails instead of posting when the chosen privacy is no longer offered', async () => {
    await seed();
    let inited = false;
    const tk = fakeTk({ creatorInfo: async () => ({ privacy_level_options: ['SELF_ONLY'] }),
                        initPhoto: async () => { inited = true; return { publish_id: 'x' }; } });
    await tick(env, tk, T);
    const p = await post('pst_acc_1_0');
    expect(inited).toBe(false);
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/no longer available/);
  });

  it('retries transient errors after 1, 5 and 10 minutes, then fails', async () => {
    await seed();
    const tk = fakeTk({ initPhoto: async () => { throw new TikTokError('content init: boom', { code: 'internal_error', transient: true }); } });
    await tick(env, tk, T);
    let p = await post('pst_acc_1_0');
    expect([p.status, p.attempts, p.next_attempt_at]).toEqual(['queued', 1, T + 60]);
    await tick(env, tk, T + 60);
    p = await post('pst_acc_1_0');
    expect([p.status, p.attempts, p.next_attempt_at]).toEqual(['queued', 2, T + 60 + 300]);
    await tick(env, tk, T + 360);
    p = await post('pst_acc_1_0');
    expect([p.status, p.attempts, p.next_attempt_at]).toEqual(['queued', 3, T + 360 + 600]);
    await tick(env, tk, T + 960);
    p = await post('pst_acc_1_0');
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/boom/);
  });

  it('a revoked account fails all its queued posts and leaves other accounts alone', async () => {
    await seed({ posts: 2, account: 'acc_1' });
    await seed({ posts: 1, account: 'acc_2' });
    const tk = fakeTk({ refresh: async () => { throw new TikTokError('Reconnect this account', { code: 'needs_reconnect' }); } });
    const ok = fakeTk();
    // acc_1 revoked, acc_2 fine: route by which refresh token is asked for is not possible, so
    // give acc_2 a different token and branch on it.
    await env.DB.prepare('UPDATE accounts SET refresh_token_enc = ? WHERE id = ?')
      .bind(await encrypt('rt-2', env.TOKEN_KEY), 'acc_2').run();
    const mixed = fakeTk({ refresh: async rt => rt === 'rt-2' ? ok.refresh(rt) : tk.refresh(rt) });
    await tick(env, mixed, T);
    expect((await post('pst_acc_1_0')).fail_reason).toBe('Reconnect this account');
    expect((await post('pst_acc_1_1')).status).toBe('failed');
    expect((await post('pst_acc_2_0')).status).toBe('published');
    const a1 = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id = ?').bind('acc_1').first();
    expect(a1.needs_reconnect).toBe(1);
  });

  it('starts at most 5 posts per account per tick and leaves the rest queued', async () => {
    await seed({ posts: 7 });
    await tick(env, fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) }), T);
    const { results } = await env.DB.prepare('SELECT status, COUNT(*) AS n FROM posts GROUP BY status').all();
    expect(Object.fromEntries(results.map(r => [r.status, r.n]))).toEqual({ publishing: 5, queued: 2 });
  });

  it('fails a post TikTok never confirms within an hour', async () => {
    await seed();
    const pending = fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) });
    await tick(env, pending, T);
    await tick(env, pending, T + 3601);
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/within an hour/);
  });

  it('puts a post stuck in publishing without a publish_id back in the queue after 10 minutes', async () => {
    await seed({ status: 'publishing' });
    await tick(env, fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) }), T + 601);
    expect((await post('pst_acc_1_0')).publish_id).toBe('pub-1');   // re-queued, then started again
  });

  it('marks the post as in flight before asking TikTok to publish', async () => {
    await seed();
    let seen;
    const tk = fakeTk({ initPhoto: async () => { seen = (await post('pst_acc_1_0')).publish_id; return { publish_id: 'pub-1' }; } });
    await tick(env, tk, T);
    expect(seen).toBe('');
  });

  it('fails, rather than resends, a post whose publish request may have gone out', async () => {
    await seed({ status: 'publishing' });
    await env.DB.prepare(`UPDATE posts SET publish_id = '', attempts = 1 WHERE id = 'pst_acc_1_0'`).run();
    let inited = false;
    await tick(env, fakeTk({ initPhoto: async () => { inited = true; return { publish_id: 'x' }; } }), T + 601);
    const p = await post('pst_acc_1_0');
    expect(inited).toBe(false);
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/check the profile/i);
  });

  it('a network error while polling keeps the post publishing', async () => {
    await seed();
    await tick(env, fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) }), T);
    const flaky = fakeTk({ status: async () => { throw new TikTokError('status fetch: fetch failed', { code: 'network', transient: true }); } });
    await tick(env, flaky, T + 60);
    expect((await post('pst_acc_1_0')).status).toBe('publishing');
  });

  it('losing access while polling fails with a check-the-profile message', async () => {
    await seed();
    await tick(env, fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) }), T);
    const revoked = fakeTk({ refresh: async () => { throw new TikTokError('Reconnect this account', { code: 'needs_reconnect' }); } });
    await tick(env, revoked, T + 60);
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/check the profile/i);
  });

  it('a post TikTok explicitly rejected can be retried', async () => {
    await seed();
    await tick(env, fakeTk({ status: async () => ({ status: 'FAILED', fail_reason: 'picture_size_check_failed' }) }), T);
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('failed');
    expect(p.publish_id).toBeNull();
  });
});
