import { decrypt, encrypt } from './crypto.js';
import { HttpError, now } from './http.js';
import { KEEP_AFTER_DONE } from './limits.js';

export async function listAccounts(env, ws) {
  const { results } = await env.DB.prepare(`SELECT id, platform, username, display_name, avatar_url, needs_reconnect, brand_id
      FROM accounts WHERE workspace_id = ? ORDER BY connected_at`).bind(ws).all();
  return results.map(r => ({ ...r, needs_reconnect: !!r.needs_reconnect }));
}

export async function getAccount(env, ws, id) {
  const row = await env.DB.prepare('SELECT * FROM accounts WHERE id = ? AND workspace_id = ?').bind(id, ws).first();
  if (!row) throw new HttpError(404, 'Account not found');
  return row;
}

// Access tokens live 24 hours; reuse one until 5 minutes before it expires.
// Refreshing on every call made concurrent callers race TikTok's token
// rotation, and the loser looked exactly like a revoked account.
const EARLY = 300;

export const isMeta = account => account.platform === 'instagram' || account.platform === 'facebook';

export async function accessTokenFor(env, tk, account, retried = false) {
  // A Page token does not expire; an Instagram token is renewed by the cron
  // (refreshInstagramTokens) long before its 60 days run out.
  if (isMeta(account)) {
    if (account.platform === 'instagram' && account.access_expires_at && account.access_expires_at <= now()) {
      await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(account.id).run();
      const e = new Error('Reconnect this account'); e.code = 'needs_reconnect'; throw e;
    }
    return decrypt(account.access_token_enc, env.TOKEN_KEY);
  }
  const t = now();
  if (account.access_token_enc && account.access_expires_at > t + EARLY) {
    return decrypt(account.access_token_enc, env.TOKEN_KEY);
  }
  const refreshToken = await decrypt(account.refresh_token_enc, env.TOKEN_KEY);
  let tokens;
  try {
    tokens = await tk.refresh(refreshToken);
  } catch (err) {
    if (err.code === 'needs_reconnect') {
      const fresh = await env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(account.id).first();
      // Someone else rotated the token after we read it: use theirs.
      if (!retried && fresh && fresh.refresh_token_enc !== account.refresh_token_enc) {
        return accessTokenFor(env, tk, fresh, true);
      }
      await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(account.id).run();
    }
    throw err;
  }
  const rotated = tokens.refresh_token && tokens.refresh_token !== refreshToken;
  await env.DB.prepare(`UPDATE accounts SET refresh_token_enc = ?, access_token_enc = ?, access_expires_at = ?,
      token_updated_at = ? WHERE id = ?`)
    .bind(rotated ? await encrypt(tokens.refresh_token, env.TOKEN_KEY) : account.refresh_token_enc,
          await encrypt(tokens.access_token, env.TOKEN_KEY), t + Number(tokens.expires_in || 86400), t, account.id)
    .run();
  return tokens.access_token;
}

export async function forgetAccessToken(env, accountId) {
  await env.DB.prepare('UPDATE accounts SET access_token_enc = NULL, access_expires_at = NULL WHERE id = ?')
    .bind(accountId).run();
}

export async function creatorInfoFor(env, tk, ws, id) {
  const account = await getAccount(env, ws, id);
  if (isMeta(account)) throw new HttpError(400, 'Creator info is a TikTok setting');
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

// Instagram tokens last 60 days and can only be refreshed once a day old and
// before they expire. Renew any within 20 days of expiry, a few per tick, so
// an account nobody posts to for two months still works.
const IG_RENEW_WITHIN = 20 * 86400;
export async function refreshInstagramTokens(env, mt, t = now(), limit = 3) {
  const { results } = await env.DB.prepare(`SELECT * FROM accounts WHERE platform = 'instagram' AND needs_reconnect = 0
      AND access_expires_at IS NOT NULL AND access_expires_at < ? AND token_updated_at < ?
      ORDER BY access_expires_at LIMIT ?`).bind(t + IG_RENEW_WITHIN, t - 86400, limit).all();
  let renewed = 0;
  for (const a of results) {
    try {
      const r = await mt.igRefresh(await decrypt(a.access_token_enc, env.TOKEN_KEY));
      const enc = await encrypt(r.access_token, env.TOKEN_KEY);
      await env.DB.prepare(`UPDATE accounts SET access_token_enc = ?, refresh_token_enc = ?, access_expires_at = ?,
          token_updated_at = ? WHERE id = ?`).bind(enc, enc, t + Number(r.expires_in || 60 * 86400), t, a.id).run();
      renewed++;
    } catch (err) {
      if (err.code === 'needs_reconnect') {
        await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(a.id).run();
      }
    }
  }
  return renewed;
}
