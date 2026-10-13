import { randomToken, sha256Hex, encrypt } from './crypto.js';
import { HttpError, now, cookie } from './http.js';
import { MAX_ACCOUNTS, SESSION_TTL } from './limits.js';
import { sessionCaller, need } from './users.js';

const SIGN_IN_FIRST = 'Sign in to ARCO Publisher with your email first, then connect accounts from the Accounts tab.';

// Connecting an account is something a signed-in owner or admin does.
async function connector(env, sessionId) {
  const who = sessionId ? await sessionCaller(env, sessionId) : null;
  if (!who) throw new HttpError(401, SIGN_IN_FIRST);
  need(who, 'admin');
  return who;
}

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

  // Signed in: connect to the current workspace. Not signed in: only the
  // TikTok account a workspace was created with before email sign-in existed
  // may still open it, until its owner adds an email.
  const who = session_id ? await sessionCaller(env, session_id) : null;
  if (who) need(who, 'admin');
  let ws = who?.ws || null;
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
  } else {
    if (!existing) throw new HttpError(401, SIGN_IN_FIRST);
    // An account added to someone else's workspace (an agency connecting a
    // client) must never hand that client the workspace.
    if (!existing.can_sign_in) throw new HttpError(409, NOT_YOURS);
    const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM memberships WHERE workspace_id = ?').bind(existing.workspace_id).first();
    if (n > 0) throw new HttpError(401, 'This workspace now signs in with email. Use "Continue with email".');
    ws = existing.workspace_id;
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
      .bind(accountId, ws, tokens.open_id, ...profile, enc, t, t, 0).run();
  }
  const sessionId = adding ? session_id : await createSession(env, ws);
  return { session_id: sessionId, workspace_id: ws, account_id: accountId };
}

// Connected accounts belong to the signed-in admin's workspace. One already
// in another workspace is refused, so nobody can pull a Page or an Instagram
// account (and its posting rights) out of someone else's workspace.
async function metaWorkspace(env, { sessionId, openIds }) {
  const who = await connector(env, sessionId);
  const marks = openIds.map(() => '?').join(',');
  const { results: existing } = await env.DB.prepare(
    `SELECT id, workspace_id, open_id FROM accounts WHERE open_id IN (${marks})`).bind(...openIds).all();
  if (existing.some(r => r.workspace_id !== who.ws)) {
    throw new HttpError(409, 'One of these accounts is already connected to another ARCO Publisher workspace. ' +
      'Its admin has to disconnect it first.');
  }
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id = ?').bind(who.ws).first();
  const fresh = openIds.filter(o => !existing.some(r => r.open_id === o)).length;
  if (n + fresh > MAX_ACCOUNTS) {
    throw new HttpError(409, `A workspace can connect up to ${MAX_ACCOUNTS} accounts. Disconnect some first.`);
  }
  return { ws: who.ws, byOpenId: new Map(existing.map(r => [r.open_id, r])) };
}

// Facebook Login: one consent connects every Page the person picked. Page
// tokens do not expire, so the token is both the "refresh" and the access
// token, with no expiry to wait for.
export async function metaIntake(env, mt, { code, redirect_uri, session_id }) {
  if (!code) throw new HttpError(400, 'code is required');
  if (redirect_uri !== env.META_REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');
  await connector(env, session_id);

  const short = await mt.exchangeCode({ code, redirectUri: redirect_uri });
  const long = await mt.longLived(short.access_token);
  const user = await mt.me(long.access_token);
  const pages = ((await mt.pages(long.access_token)).data || []).filter(p => p.access_token);
  if (!pages.length) throw new HttpError(400, 'No Facebook Page came back. Pick at least one Page on the Facebook screen.');

  const found = pages.map(p => ({ open_id: `fb:${p.id}`, name: p.name || '', avatar: p.picture?.data?.url || '', token: p.access_token }));
  const { ws, byOpenId } = await metaWorkspace(env, { sessionId: session_id, openIds: found.map(f => f.open_id) });

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
        .bind(id, ws, f.open_id, String(user.id), f.name, f.name, f.avatar, enc, enc, t, t, 0));
  }
  await env.DB.batch(statements);
  return { session_id, workspace_id: ws, account_ids: ids };
}

// Instagram Login: the person signs in as the Instagram account itself, so
// (like TikTok) signing in again with it returns to its workspace. The token
// lives 60 days; refreshInstagramTokens renews it well before that.
export async function igIntake(env, mt, { code, redirect_uri, session_id }) {
  if (!code) throw new HttpError(400, 'code is required');
  if (redirect_uri !== env.IG_REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');
  await connector(env, session_id);

  // Instagram appends '#_' to the code; it is not part of it.
  const short = await mt.igExchangeCode({ code: String(code).replace(/#_$/, ''), redirectUri: redirect_uri });
  const long = await mt.igLongLived(short.access_token);
  const me = await mt.igMe(long.access_token);
  const igId = String(me.user_id || short.user_id || me.id);
  const openId = `ig:${igId}`;
  const { ws, byOpenId } = await metaWorkspace(env, { sessionId: session_id, openIds: [openId] });

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
      .bind(id, ws, openId, ...profile, enc, enc, expires, t, t, 0).run();
  }
  return { session_id, workspace_id: ws, account_ids: [id] };
}
