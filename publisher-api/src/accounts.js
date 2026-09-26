import { decrypt, encrypt } from './crypto.js';
import { HttpError, now } from './http.js';
import { KEEP_AFTER_DONE } from './limits.js';

export async function listAccounts(env, ws) {
  const { results } = await env.DB.prepare(`SELECT id, username, display_name, avatar_url, needs_reconnect
      FROM accounts WHERE workspace_id = ? ORDER BY connected_at`).bind(ws).all();
  return results.map(r => ({ ...r, needs_reconnect: !!r.needs_reconnect }));
}

export async function getAccount(env, ws, id) {
  const row = await env.DB.prepare('SELECT * FROM accounts WHERE id = ? AND workspace_id = ?').bind(id, ws).first();
  if (!row) throw new HttpError(404, 'Account not found');
  return row;
}

export async function accessTokenFor(env, tk, account) {
  const refreshToken = await decrypt(account.refresh_token_enc, env.TOKEN_KEY);
  try {
    const t = await tk.refresh(refreshToken);
    if (t.refresh_token && t.refresh_token !== refreshToken) {
      await env.DB.prepare('UPDATE accounts SET refresh_token_enc = ?, token_updated_at = ? WHERE id = ?')
        .bind(await encrypt(t.refresh_token, env.TOKEN_KEY), now(), account.id).run();
    }
    return t.access_token;
  } catch (err) {
    if (err.code === 'needs_reconnect') {
      await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(account.id).run();
    }
    throw err;
  }
}

export async function creatorInfoFor(env, tk, ws, id) {
  const account = await getAccount(env, ws, id);
  return tk.creatorInfo(await accessTokenFor(env, tk, account));
}

export async function disconnect(env, ws, id) {
  await getAccount(env, ws, id);
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE media SET delete_after = ? WHERE post_id IN
        (SELECT id FROM posts WHERE account_id = ? AND status IN ('queued', 'publishing'))`).bind(t, id),
    env.DB.prepare(`UPDATE posts SET status = 'cancelled', fail_reason = 'Account disconnected', updated_at = ?
        WHERE account_id = ? AND status IN ('queued', 'publishing')`).bind(t, id),
    env.DB.prepare(`UPDATE media SET delete_after = ? WHERE post_id IN
        (SELECT id FROM posts WHERE account_id = ?) AND delete_after IS NULL`).bind(t + KEEP_AFTER_DONE, id),
    env.DB.prepare('DELETE FROM accounts WHERE id = ?').bind(id),
  ]);
}
