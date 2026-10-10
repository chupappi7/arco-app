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

// Facebook Login: one consent connects every Page the person picked and the
// Instagram professional account linked to each. Signing in this way with no
// session lands in the workspace these accounts already belong to, or a new one.
export async function metaIntake(env, mt, { code, redirect_uri, session_id }) {
  if (!code) throw new HttpError(400, 'code is required');
  if (redirect_uri !== env.META_REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');

  const short = await mt.exchangeCode({ code, redirectUri: redirect_uri });
  const long = await mt.longLived(short.access_token);
  const user = await mt.me(long.access_token);
  const pages = (await mt.pages(long.access_token)).data || [];

  const found = [];
  for (const p of pages) {
    if (!p.access_token) continue;
    found.push({ platform: 'facebook', open_id: `fb:${p.id}`, username: p.name || '',
      display_name: p.name || '', avatar_url: p.picture?.data?.url || '', token: p.access_token });
    const ig = p.instagram_business_account;
    if (ig?.id) {
      found.push({ platform: 'instagram', open_id: `ig:${ig.id}`, username: ig.username || '',
        display_name: ig.name || ig.username || '', avatar_url: ig.profile_picture_url || '', token: p.access_token });
    }
  }
  if (!found.length) {
    throw new HttpError(400, 'No Facebook Page came back. Pick at least one Page on the Facebook screen, ' +
      'and link your Instagram professional account to that Page to post to Instagram.');
  }

  const marks = found.map(() => '?').join(',');
  const { results: existing } = await env.DB.prepare(
    `SELECT id, workspace_id, open_id FROM accounts WHERE open_id IN (${marks})`).bind(...found.map(f => f.open_id)).all();
  const byOpenId = new Map(existing.map(r => [r.open_id, r]));

  let ws = session_id ? await sessionWorkspace(env, session_id) : null;
  const adding = !!ws;
  if (!ws) {
    const mine = existing[0] || await env.DB.prepare('SELECT workspace_id FROM accounts WHERE meta_user_id = ? LIMIT 1')
      .bind(String(user.id)).first();
    ws = mine?.workspace_id;
  }
  const t = now();
  if (!ws) {
    ws = 'ws_' + randomToken('', 8);
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?)').bind(ws, t).run();
  }

  const elsewhere = existing.find(r => r.workspace_id !== ws);
  if (elsewhere) {
    throw new HttpError(409, 'One of these Pages or Instagram accounts is already connected to another workspace. ' +
      'Sign in there and disconnect it first.');
  }
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id = ?').bind(ws).first();
  const fresh = found.filter(f => !byOpenId.has(f.open_id)).length;
  if (n + fresh > MAX_ACCOUNTS) {
    throw new HttpError(409, `A workspace can connect up to ${MAX_ACCOUNTS} accounts. ` +
      'Pick fewer Pages on the Facebook screen, or disconnect some first.');
  }

  const statements = [];
  const ids = [];
  for (const f of found) {
    const enc = await encrypt(f.token, env.TOKEN_KEY);
    const old = byOpenId.get(f.open_id);
    // Page tokens do not expire, so the token is both the "refresh" and the
    // access token, with no expiry to wait for.
    if (old) {
      ids.push(old.id);
      statements.push(env.DB.prepare(`UPDATE accounts SET refresh_token_enc = ?, access_token_enc = ?,
          access_expires_at = NULL, needs_reconnect = 0, username = ?, display_name = ?, avatar_url = ?,
          meta_user_id = ?, token_updated_at = ? WHERE id = ?`)
        .bind(enc, enc, f.username, f.display_name, f.avatar_url, String(user.id), t, old.id));
    } else {
      const id = 'acc_' + randomToken('', 8);
      ids.push(id);
      statements.push(env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, meta_user_id,
          username, display_name, avatar_url, refresh_token_enc, access_token_enc, connected_at, token_updated_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
        .bind(id, ws, f.open_id, f.platform, String(user.id), f.username, f.display_name, f.avatar_url, enc, enc, t, t));
    }
  }
  await env.DB.batch(statements);
  const sessionId = adding ? session_id : await createSession(env, ws);
  return { session_id: sessionId, workspace_id: ws, account_ids: ids };
}
