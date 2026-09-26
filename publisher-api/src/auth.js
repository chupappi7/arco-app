import { randomToken, sha256Hex, encrypt } from './crypto.js';
import { HttpError, now, cookie } from './http.js';
import { MAX_ACCOUNTS, SESSION_TTL } from './limits.js';

export async function createSession(env, workspaceId) {
  const id = randomToken('ses_');
  await env.DB.prepare('INSERT INTO sessions (id_hash, workspace_id, expires_at) VALUES (?, ?, ?)')
    .bind(await sha256Hex(id), workspaceId, now() + SESSION_TTL).run();
  return id;
}

export async function sessionWorkspace(env, sessionId) {
  if (!sessionId) return null;
  const row = await env.DB.prepare('SELECT workspace_id FROM sessions WHERE id_hash = ? AND expires_at > ?')
    .bind(await sha256Hex(sessionId), now()).first();
  return row ? row.workspace_id : null;
}

export async function resolveCaller(env, req) {
  const auth = req.headers.get('Authorization') || '';
  if (auth.startsWith('Key ')) {
    const row = await env.DB.prepare('SELECT id FROM workspaces WHERE api_key_hash = ?')
      .bind(await sha256Hex(auth.slice(4).trim())).first();
    return row ? { workspaceId: row.id, via: 'key' } : null;
  }
  const ws = await sessionWorkspace(env, cookie(req, 'tt_sid'));
  return ws ? { workspaceId: ws, via: 'session' } : null;
}

export async function rotateApiKey(env, workspaceId) {
  const key = randomToken('apk_');
  await env.DB.prepare('UPDATE workspaces SET api_key_hash = ? WHERE id = ?')
    .bind(await sha256Hex(key), workspaceId).run();
  return key;
}

export async function logout(env, req) {
  const id = cookie(req, 'tt_sid');
  if (id) await env.DB.prepare('DELETE FROM sessions WHERE id_hash = ?').bind(await sha256Hex(id)).run();
}

export async function oauthIntake(env, tk, { code, code_verifier, redirect_uri, session_id }) {
  if (!code || !code_verifier) throw new HttpError(400, 'code and code_verifier are required');
  if (redirect_uri !== env.REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');

  const tokens = await tk.exchangeCode({ code, codeVerifier: code_verifier, redirectUri: redirect_uri });
  const info = await tk.creatorInfo(tokens.access_token);
  const t = now();
  const existing = await env.DB.prepare('SELECT id, workspace_id FROM accounts WHERE open_id = ?')
    .bind(tokens.open_id).first();

  let ws = session_id ? await sessionWorkspace(env, session_id) : null;
  const adding = !!ws;
  if (adding) {
    if (existing && existing.workspace_id !== ws) {
      throw new HttpError(409, 'This TikTok account is already connected to another workspace. ' +
        'Sign in with it and disconnect it there first.');
    }
    if (!existing) {
      const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id = ?').bind(ws).first();
      if (n >= MAX_ACCOUNTS) throw new HttpError(409, `A workspace can connect up to ${MAX_ACCOUNTS} accounts.`);
    }
  } else if (existing) {
    ws = existing.workspace_id;
  } else {
    ws = 'ws_' + randomToken('', 8);
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?)').bind(ws, t).run();
  }

  const enc = await encrypt(tokens.refresh_token, env.TOKEN_KEY);
  const profile = [info.creator_username || '', info.creator_nickname || '', info.creator_avatar_url || ''];
  let accountId = existing?.id;
  if (existing) {
    await env.DB.prepare(`UPDATE accounts SET refresh_token_enc = ?, access_token_enc = NULL, access_expires_at = NULL,
        needs_reconnect = 0, username = ?,
        display_name = ?, avatar_url = ?, token_updated_at = ? WHERE id = ?`)
      .bind(enc, ...profile, t, accountId).run();
  } else {
    accountId = 'acc_' + randomToken('', 8);
    await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, username, display_name, avatar_url,
        refresh_token_enc, connected_at, token_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(accountId, ws, tokens.open_id, ...profile, enc, t, t).run();
  }
  const sessionId = adding ? session_id : await createSession(env, ws);
  return { session_id: sessionId, workspace_id: ws, account_id: accountId };
}
