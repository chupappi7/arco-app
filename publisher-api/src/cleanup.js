import { now } from './http.js';

// D1 allows at most 100 bound parameters per statement, so rows are removed
// by condition (no key lists) and R2 deletes go in chunks. Rows go first: if
// the R2 delete then fails, an orphaned object costs storage, whereas a row
// pointing at a deleted object would be retried forever.
const CHUNK = 500;

async function deleteObjects(env, keys) {
  for (let i = 0; i < keys.length; i += CHUNK) await env.MEDIA.delete(keys.slice(i, i + CHUNK));
}

export async function runCleanup(env, t = now()) {
  const { results } = await env.DB.prepare(
    'SELECT key FROM media WHERE delete_after IS NOT NULL AND delete_after <= ? ORDER BY key LIMIT 1000').bind(t).all();
  const keys = results.map(r => r.key);
  if (keys.length) {
    // Same 1000 rows as the SELECT above, so no row loses its object unseen.
    await env.DB.prepare(`DELETE FROM media WHERE key IN (SELECT key FROM media
        WHERE delete_after IS NOT NULL AND delete_after <= ? ORDER BY key LIMIT 1000)`).bind(t).run();
    await deleteObjects(env, keys);
  }
  const s = await env.DB.prepare('DELETE FROM sessions WHERE expires_at <= ?').bind(t).run();
  await env.DB.batch([
    env.DB.prepare('DELETE FROM login_codes WHERE expires_at <= ?').bind(t - 3600),
    env.DB.prepare('DELETE FROM invites WHERE expires_at <= ?').bind(t),
    env.DB.prepare('DELETE FROM ai_usage WHERE day < ?').bind(new Date((t - 7 * 86400) * 1000).toISOString().slice(0, 10)),
  ]);
  return { images: keys.length, sessions: s.meta.changes };
}

export async function deleteWorkspace(env, ws) {
  const { results } = await env.DB.prepare('SELECT key FROM media WHERE workspace_id = ?').bind(ws).all();
  await env.DB.batch(['media', 'posts', 'accounts', 'sessions', 'brands', 'memberships', 'invites', 'ai_usage'].map(t =>
    env.DB.prepare(`DELETE FROM ${t} WHERE workspace_id = ?`).bind(ws))
    .concat(env.DB.prepare('DELETE FROM workspaces WHERE id = ?').bind(ws)));
  await deleteObjects(env, results.map(r => r.key));
}
