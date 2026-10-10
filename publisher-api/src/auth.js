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

const NOT_YOURS = 'This account was added to someone else\'s ARCO Publisher workspace, so it cannot be used to sign in. ' +
  'Ask them to disconnect it if you want your own workspace.';

export async function oauthIntake(env, tk, { code, code_verifier, redirect_uri, session_id }) {
  if (!code || !code_verifier) throw new HttpError(400, 'code and code_verifier are required');
  if (redirect_uri !== env.REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');

  const tokens = await tk.exchangeCode({ code, codeVerifier: code_verifier, redirectUri: redirect_uri });
  const info = await tk.creatorInfo(tokens.access_token);
  const t = now();
  const existing = await env.DB.prepare('SELECT id, workspace_id, can_sign_in FROM accounts WHERE open_id = ?')
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
    // Only an account that signs into its workspace may open it. One that was
    // added to someone else's workspace (an agency connecting a client) must
    // not hand that client every other account in it.
    if (!existing.can_sign_in) throw new HttpError(409, NOT_YOURS);
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
        refresh_token_enc, connected_at, token_updated_at, can_sign_in) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(accountId, ws, tokens.open_id, ...profile, enc, t, t, adding ? 0 : 1).run();
  }
  const sessionId = adding ? session_id : await createSession(env, ws);
  return { session_id: sessionId, workspace_id: ws, account_id: accountId };
}

// Find or create the workspace a Meta sign-in lands in, and refuse any
// account that already belongs to another workspace.
//
// Without a session, the workspace is found only by WHO signed in (the same
// Facebook person, or the Instagram account itself), never by the Pages
// someone can manage: several people manage one Page, and managing it must
// not open the workspace of whoever connected it first.
async function metaWorkspace(env, { sessionId, owner, openIds }) {
  const marks = openIds.map(() => '?').join(',');
  const { results: existing } = await env.DB.prepare(
    `SELECT id, workspace_id, open_id, can_sign_in FROM accounts WHERE open_id IN (${marks})`).bind(...openIds).all();
  let ws = sessionId ? await sessionWorkspace(env, sessionId) : null;
  const adding = !!ws;
  if (!ws && owner) ws = (await env.DB.prepare(owner.sql).bind(owner.value).first())?.workspace_id || null;
  const t = now();
  if (!ws) {
    if (existing.length) throw new HttpError(409, existing.some(r => !r.can_sign_in) ? NOT_YOURS
      : 'This account is already connected to another ARCO Publisher workspace. Sign in there and disconnect it first.');
    ws = 'ws_' + randomToken('', 8);
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?)').bind(ws, t).run();
  }
  if (existing.some(r => r.workspace_id !== ws)) {
    throw new HttpError(409, 'One of these accounts is already connected to another ARCO Publisher workspace. ' +
      'Sign in there and disconnect it first.');
  }
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id = ?').bind(ws).first();
  const fresh = openIds.filter(o => !existing.some(r => r.open_id === o)).length;
  if (n + fresh > MAX_ACCOUNTS) {
    throw new HttpError(409, `A workspace can connect up to ${MAX_ACCOUNTS} accounts. Disconnect some first.`);
  }
  return { ws, adding, byOpenId: new Map(existing.map(r => [r.open_id, r])), canSignIn: adding ? 0 : 1 };
}

// Facebook Login: one consent connects every Page the person picked. Page
// tokens do not expire, so the token is both the "refresh" and the access
// token, with no expiry to wait for.
export async function metaIntake(env, mt, { code, redirect_uri, session_id }) {
  if (!code) throw new HttpError(400, 'code is required');
  if (redirect_uri !== env.META_REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');

  const short = await mt.exchangeCode({ code, redirectUri: redirect_uri });
  const long = await mt.longLived(short.access_token);
  const user = await mt.me(long.access_token);
  const pages = ((await mt.pages(long.access_token)).data || []).filter(p => p.access_token);
  if (!pages.length) throw new HttpError(400, 'No Facebook Page came back. Pick at least one Page on the Facebook screen.');

  const found = pages.map(p => ({ open_id: `fb:${p.id}`, name: p.name || '', avatar: p.picture?.data?.url || '', token: p.access_token }));
  const { ws, adding, byOpenId, canSignIn } = await metaWorkspace(env, { sessionId: session_id, openIds: found.map(f => f.open_id),
    owner: { sql: 'SELECT workspace_id FROM accounts WHERE meta_user_id = ? AND can_sign_in = 1 LIMIT 1', value: String(user.id) } });

  const t = now();
  const statements = [], ids = [];
  for (const f of found) {
    const enc = await encrypt(f.token, env.TOKEN_KEY);
    const old = byOpenId.get(f.open_id);
    const id = old?.id || 'acc_' + randomToken('', 8);
    ids.push(id);
    statements.push(old
      ? env.DB.prepare(`UPDATE accounts SET refresh_token_enc = ?, access_token_enc = ?, access_expires_at = NULL,
          needs_reconnect = 0, username = ?, display_name = ?, avatar_url = ?, meta_user_id = ?, token_updated_at = ?
          WHERE id = ?`).bind(enc, enc, f.name, f.name, f.avatar, String(user.id), t, id)
      : env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, meta_user_id, username, display_name,
          avatar_url, refresh_token_enc, access_token_enc, connected_at, token_updated_at, can_sign_in)
          VALUES (?, ?, ?, 'facebook', ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
        .bind(id, ws, f.open_id, String(user.id), f.name, f.name, f.avatar, enc, enc, t, t, canSignIn));
  }
  await env.DB.batch(statements);
  return { session_id: adding ? session_id : await createSession(env, ws), workspace_id: ws, account_ids: ids };
}

// Instagram Login: the person signs in as the Instagram account itself, so
// (like TikTok) signing in again with it returns to its workspace. The token
// lives 60 days; refreshInstagramTokens renews it well before that.
export async function igIntake(env, mt, { code, redirect_uri, session_id }) {
  if (!code) throw new HttpError(400, 'code is required');
  if (redirect_uri !== env.IG_REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');

  // Instagram appends '#_' to the code; it is not part of it.
  const short = await mt.igExchangeCode({ code: String(code).replace(/#_$/, ''), redirectUri: redirect_uri });
  const long = await mt.igLongLived(short.access_token);
  const me = await mt.igMe(long.access_token);
  const igId = String(me.user_id || short.user_id || me.id);
  const openId = `ig:${igId}`;
  const { ws, adding, byOpenId, canSignIn } = await metaWorkspace(env, { sessionId: session_id, openIds: [openId],
    owner: { sql: 'SELECT workspace_id FROM accounts WHERE open_id = ? AND can_sign_in = 1', value: openId } });

  const t = now();
  const enc = await encrypt(long.access_token, env.TOKEN_KEY);
  const expires = t + Number(long.expires_in || 60 * 86400);
  const profile = [me.username || '', me.name || me.username || '', me.profile_picture_url || ''];
  const old = byOpenId.get(openId);
  const id = old?.id || 'acc_' + randomToken('', 8);
  if (old) {
    await env.DB.prepare(`UPDATE accounts SET refresh_token_enc = ?, access_token_enc = ?, access_expires_at = ?,
        needs_reconnect = 0, username = ?, display_name = ?, avatar_url = ?, token_updated_at = ? WHERE id = ?`)
      .bind(enc, enc, expires, ...profile, t, id).run();
  } else {
    await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, username, display_name, avatar_url,
        refresh_token_enc, access_token_enc, access_expires_at, connected_at, token_updated_at, can_sign_in)
        VALUES (?, ?, ?, 'instagram', ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, ws, openId, ...profile, enc, enc, expires, t, t, canSignIn).run();
  }
  return { session_id: adding ? session_id : await createSession(env, ws), workspace_id: ws, account_ids: [id] };
}
