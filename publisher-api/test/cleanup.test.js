import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb } from './helpers.js';
import { runCleanup, deleteWorkspace } from '../src/cleanup.js';

const T = 1_800_000_000;
async function img(key, { deleteAfter = null, postId = null, ws = 'ws_1' } = {}) {
  await env.MEDIA.put(key, new Uint8Array([0xff, 0xd8, 0xff]));
  await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, post_id, delete_after)
      VALUES (?, ?, 3, 'image/jpeg', ?, ?, ?)`).bind(key, ws, T, postId, deleteAfter).run();
}

describe('cleanup', () => {
  beforeEach(() => resetDb(env));

  it('deletes only images whose delete_after has passed', async () => {
    await img('ws_1/old.jpg', { deleteAfter: T - 1 });
    await img('ws_1/later.jpg', { deleteAfter: T + 100 });
    await img('ws_1/queued.jpg', { postId: 'pst_q' });          // attached to a live post: never deleted
    const r = await runCleanup(env, T);
    expect(r.images).toBe(1);
    expect(await env.MEDIA.head('ws_1/old.jpg')).toBeNull();
    expect(await env.MEDIA.head('ws_1/later.jpg')).not.toBeNull();
    expect(await env.MEDIA.head('ws_1/queued.jpg')).not.toBeNull();
  });

  it('removes expired sessions', async () => {
    await env.DB.prepare('INSERT INTO sessions VALUES (?, ?, ?)').bind('h1', 'ws_1', T - 1).run();
    await env.DB.prepare('INSERT INTO sessions VALUES (?, ?, ?)').bind('h2', 'ws_1', T + 1).run();
    expect((await runCleanup(env, T)).sessions).toBe(1);
  });

  it('deleteWorkspace removes every row and image for that workspace only', async () => {
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?), (?, ?)').bind('ws_1', T, 'ws_2', T).run();
    await img('ws_1/a.jpg');
    await img('ws_2/b.jpg', { ws: 'ws_2' });
    await env.DB.prepare('INSERT INTO sessions VALUES (?, ?, ?)').bind('h1', 'ws_1', T + 99).run();
    await deleteWorkspace(env, 'ws_1');
    expect(await env.MEDIA.head('ws_1/a.jpg')).toBeNull();
    expect(await env.MEDIA.head('ws_2/b.jpg')).not.toBeNull();
    for (const t of ['workspaces', 'sessions', 'media']) {
      const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM ${t} WHERE ${t === 'workspaces' ? 'id' : 'workspace_id'} = 'ws_1'`).first();
      expect(n).toBe(0);
    }
  });
});
