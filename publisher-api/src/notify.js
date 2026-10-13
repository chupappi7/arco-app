import { now } from './http.js';
import { mailerFor, failureMail } from './email.js';

// Tell people about posts that failed. Runs after each publishing pass and
// sweeps every failure not yet reported, so no failure path can forget to
// call it. Rows are claimed (notified = 1) before mail goes out, so two
// overlapping runs never email the same failure; if sending fails they are
// released for the next run. One email per person per run, however many
// posts it lists.
export async function notifyFailures(env, limit = 50) {
  const { results } = await env.DB.prepare(`UPDATE posts SET notified = 1
      WHERE id IN (SELECT id FROM posts WHERE status = 'failed' AND notified = 0 ORDER BY updated_at LIMIT ?)
      RETURNING id, workspace_id, account_id, created_by, scheduled_at, fail_reason`).bind(limit).all();
  if (!results.length) return 0;

  const byPerson = new Map();
  for (const p of results) {
    // The person who made the post, while they are still in that workspace;
    // otherwise the workspace's owner.
    let to = p.created_by ? await env.DB.prepare(`SELECT u.email FROM users u JOIN memberships m ON m.user_id = u.id
        WHERE u.id = ? AND m.workspace_id = ?`).bind(p.created_by, p.workspace_id).first() : null;
    if (!to) to = await env.DB.prepare(`SELECT u.email FROM users u JOIN memberships m ON m.user_id = u.id
        WHERE m.workspace_id = ? AND m.role = 'owner' LIMIT 1`).bind(p.workspace_id).first();
    if (!to) continue;
    const a = await env.DB.prepare('SELECT platform, username FROM accounts WHERE id = ?').bind(p.account_id).first();
    const w = await env.DB.prepare('SELECT name, timezone FROM workspaces WHERE id = ?').bind(p.workspace_id).first();
    if (!byPerson.has(to.email)) byPerson.set(to.email, []);
    byPerson.get(to.email).push({ ...p, platform: a?.platform || 'tiktok', username: a?.username || 'an account',
      workspace: w?.name || 'your workspace', timezone: w?.timezone || 'UTC' });
  }
  let sent = 0;
  for (const [email, posts] of byPerson) {
    try {
      await mailerFor(env).send({ to: email, ...failureMail(posts, `${env.PUBLIC_ORIGIN}/app.html#calendar`) });
      sent++;
    } catch (err) {
      console.error('failure mail', err?.message);
      const marks = posts.map(() => '?').join(',');
      await env.DB.prepare(`UPDATE posts SET notified = 0 WHERE id IN (${marks})`).bind(...posts.map(p => p.id)).run();
    }
  }
  return sent;
}
