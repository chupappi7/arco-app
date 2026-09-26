import { now } from './http.js';

export async function runCleanup(env, t = now()) {
  const { results } = await env.DB.prepare(
    'SELECT key FROM media WHERE delete_after IS NOT NULL AND delete_after <= ? LIMIT 500').bind(t).all();
  const keys = results.map(r => r.key);
  if (keys.length) {
    await env.MEDIA.delete(keys);
    const marks = keys.map(() => '?').join(',');
    await env.DB.prepare(`DELETE FROM media WHERE key IN (${marks})`).bind(...keys).run();
  }
  const s = await env.DB.prepare('DELETE FROM sessions WHERE expires_at <= ?').bind(t).run();
  return { images: keys.length, sessions: s.meta.changes };
}

export async function deleteWorkspace(env, ws) {
  for (;;) {
    const { results } = await env.DB.prepare('SELECT key FROM media WHERE workspace_id = ? LIMIT 500').bind(ws).all();
    if (!results.length) break;
    const keys = results.map(r => r.key);
    await env.MEDIA.delete(keys);
    const marks = keys.map(() => '?').join(',');
    await env.DB.prepare(`DELETE FROM media WHERE key IN (${marks})`).bind(...keys).run();
  }
  await env.DB.batch(['posts', 'accounts', 'sessions'].map(t =>
    env.DB.prepare(`DELETE FROM ${t} WHERE workspace_id = ?`).bind(ws))
    .concat(env.DB.prepare('DELETE FROM workspaces WHERE id = ?').bind(ws)));
}
