// Applies schema.sql to the test D1. Statements are split on ";" at line end.
import schema from '../schema.sql?raw';

export async function applySchema(env) {
  const statements = schema.split(/;\s*$/m).map(s => s.trim()).filter(Boolean);
  for (const sql of statements) await env.DB.prepare(sql).run();
}

import { env as baseEnv, createExecutionContext, waitOnExecutionContext } from 'cloudflare:test';
import worker from '../src/index.js';

// A TikTok client double. Override any method per test.
export function fakeTk(overrides = {}) {
  let n = 0;
  return {
    exchangeCode: async () => ({ access_token: 'at', refresh_token: 'rt-1', open_id: 'open-1',
      scope: 'user.info.basic,video.publish,video.upload', expires_in: 86400, refresh_expires_in: 31536000 }),
    refresh: async () => ({ access_token: `at-${++n}`, refresh_token: 'rt-1' }),
    creatorInfo: async () => ({ creator_username: 'creator', creator_nickname: 'Creator',
      creator_avatar_url: 'https://p16/a.jpg',
      privacy_level_options: ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'SELF_ONLY'],
      comment_disabled: false }),
    initPhoto: async () => ({ publish_id: 'pub-1' }),
    status: async () => ({ status: 'PUBLISH_COMPLETE', publicaly_available_post_id: ['7500000000000000001'] }),
    ...overrides,
  };
}

// Call the Worker's fetch handler with a fake TikTok client injected.
export async function callWorker(path, { method = 'GET', headers = {}, body, tk = fakeTk(), env: extra } = {}) {
  const init = { method, headers: { ...headers } };
  if (body !== undefined) {
    if (body instanceof Uint8Array || body instanceof ArrayBuffer) init.body = body;
    else { init.body = JSON.stringify(body); init.headers['Content-Type'] = 'application/json'; }
  }
  const ctx = createExecutionContext();
  const res = await worker.fetch(new Request(`https://api.test${path}`, init), { ...baseEnv, __tk: tk, ...(extra || {}) }, ctx);
  await waitOnExecutionContext(ctx);
  return res;
}

export async function resetDb(env) {
  await applySchema(env);
  for (const t of ['posts', 'media', 'sessions', 'accounts', 'brands', 'memberships', 'invites', 'login_codes', 'users', 'ai_usage', 'workspaces']) {
    await env.DB.prepare(`DELETE FROM ${t}`).run();
  }
}

// A signed-up person with their own workspace, as email sign-in leaves them.
let signups = 0;
export async function signUp(env, email = `owner${++signups}-${Date.now()}@test.dev`) {
  const { createWorkspace, newSession } = await import('../src/users.js');
  const userId = 'usr_' + Math.random().toString(16).slice(2, 10);
  await env.DB.prepare('INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)').bind(userId, email, 1).run();
  const ws = await createWorkspace(env, userId);
  return { sid: await newSession(env, userId, ws), ws, userId, email };
}
