// Email accounts, sessions, workspaces, members and invites.
//
// Isolation rules this file guarantees:
//  - a session belongs to one user and points at one workspace that user is a
//    member of; resolveCaller re-checks the membership on every request
//  - a member may be limited to some brands (scope); owners and admins see all
//  - invites only work for the email they were sent to

import { randomToken, sha256Hex } from './crypto.js';
import { HttpError, now, cookie } from './http.js';
import { mailerFor, codeMail, inviteMail } from './email.js';
import { SESSION_TTL } from './limits.js';

const ROLES = ['owner', 'admin', 'member'];
const CODE_TTL = 600, CODE_MAX_ATTEMPTS = 5, CODES_PER_HOUR = 5, INVITE_TTL = 7 * 86400;
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;

export const normEmail = e => {
  const email = String(e ?? '').trim().toLowerCase();
  if (email.length > 254 || !EMAIL.test(email)) throw new HttpError(400, 'Enter a valid email address');
  return email;
};
const codeHash = (env, email, code) => sha256Hex(`${env.TOKEN_KEY}|login|${email}|${code}`);

function sixDigits() {
  // Rejection sampling, so every code is equally likely.
  const buf = new Uint32Array(1);
  for (;;) { crypto.getRandomValues(buf); if (buf[0] < 4_294_000_000) return String(buf[0] % 1_000_000).padStart(6, '0'); }
}

function sameText(a, b) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

// ---- sign in with an emailed code -------------------------------------

// Always answers the same way, so it cannot be used to learn who has an account.
export async function startEmail(env, body) {
  const email = normEmail(body?.email);
  const t = now();
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM login_codes WHERE email = ? AND created_at > ?')
    .bind(email, t - 3600).first();
  if (n >= CODES_PER_HOUR) throw new HttpError(429, 'Too many codes requested. Wait a while and try again.');
  const code = sixDigits();
  await env.DB.prepare(`INSERT INTO login_codes (id, email, code_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)`)
    .bind(randomToken('lc_', 8), email, await codeHash(env, email, code), t + CODE_TTL, t).run();
  await mailerFor(env).send({ to: email, ...codeMail(code) });
  return { ok: true };
}

// The newest unexpired code for the address is the only one that counts, and
// it allows CODE_MAX_ATTEMPTS guesses in total.
async function checkCode(env, email, code) {
  const t = now();
  const row = await env.DB.prepare(`SELECT * FROM login_codes WHERE email = ? AND expires_at > ?
      ORDER BY created_at DESC LIMIT 1`).bind(email, t).first();
  const bad = new HttpError(400, 'That code is wrong or has expired. Request a new one.');
  if (!row || row.attempts >= CODE_MAX_ATTEMPTS) throw bad;
  await env.DB.prepare('UPDATE login_codes SET attempts = attempts + 1 WHERE id = ?').bind(row.id).run();
  if (!/^\d{6}$/.test(String(code ?? '')) || !sameText(row.code_hash, await codeHash(env, email, String(code)))) throw bad;
  await env.DB.prepare('DELETE FROM login_codes WHERE email = ?').bind(email).run();
}

export async function createWorkspace(env, userId, name = 'My workspace') {
  const ws = 'ws_' + randomToken('', 8), t = now();
  await env.DB.batch([
    env.DB.prepare('INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)').bind(ws, cleanWsName(name), t),
    env.DB.prepare(`INSERT INTO memberships (workspace_id, user_id, role, created_at) VALUES (?, ?, 'owner', ?)`).bind(ws, userId, t),
  ]);
  return ws;
}

const cleanWsName = n => {
  const name = String(n ?? '').trim().replace(/\s+/g, ' ');
  if (!name || [...name].length > 60) throw new HttpError(400, 'Workspace names are 1 to 60 characters');
  return name;
};

export async function newSession(env, userId, ws) {
  const id = randomToken('ses_');
  await env.DB.prepare('INSERT INTO sessions (id_hash, workspace_id, user_id, expires_at) VALUES (?, ?, ?, ?)')
    .bind(await sha256Hex(id), ws, userId, now() + SESSION_TTL).run();
  return id;
}

// Called by the Vercel function, which then sets the session cookie.
// legacy_session: a session from before email sign-in, whose workspace has no
// members yet. Verifying an email from it makes that person its owner.
export async function verifyEmail(env, { email: raw, code, legacy_session }) {
  const email = normEmail(raw);
  await checkCode(env, email, code);
  const t = now();
  let user = await env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first();
  if (!user) {
    user = { id: 'usr_' + randomToken('', 8) };
    await env.DB.prepare('INSERT INTO users (id, email, created_at, last_seen_at) VALUES (?, ?, ?, ?)').bind(user.id, email, t, t).run();
  } else {
    await env.DB.prepare('UPDATE users SET last_seen_at = ? WHERE id = ?').bind(t, user.id).run();
  }

  let ws = null;
  if (legacy_session) {
    const s = await env.DB.prepare('SELECT workspace_id, user_id FROM sessions WHERE id_hash = ? AND expires_at > ?')
      .bind(await sha256Hex(legacy_session), t).first();
    if (s && !s.user_id && s.workspace_id) {
      const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM memberships WHERE workspace_id = ?').bind(s.workspace_id).first();
      if (n === 0) {
        await env.DB.prepare(`INSERT INTO memberships (workspace_id, user_id, role, created_at) VALUES (?, ?, 'owner', ?)`)
          .bind(s.workspace_id, user.id, t).run();
        ws = s.workspace_id;
      }
      await env.DB.prepare('DELETE FROM sessions WHERE id_hash = ?').bind(await sha256Hex(legacy_session)).run();
    }
  }
  if (!ws) ws = (await env.DB.prepare(`SELECT workspace_id FROM memberships WHERE user_id = ? ORDER BY created_at LIMIT 1`)
    .bind(user.id).first())?.workspace_id;
  if (!ws) ws = await createWorkspace(env, user.id);
  return { session_id: await newSession(env, user.id, ws), workspace_id: ws };
}

// ---- who is calling ----------------------------------------------------

export async function sessionCaller(env, sessionId) {
  if (!sessionId) return null;
  const idHash = await sha256Hex(sessionId);
  const s = await env.DB.prepare('SELECT workspace_id, user_id FROM sessions WHERE id_hash = ? AND expires_at > ?')
    .bind(idHash, now()).first();
  if (!s) return null;
  // Before email sign-in: the old one-account workspace, until an email is added.
  if (!s.user_id) {
    const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM memberships WHERE workspace_id = ?').bind(s.workspace_id).first();
    if (n > 0) return null;   // claimed since; sign in with email
    return { ws: s.workspace_id, userId: null, role: 'owner', scope: null, via: 'legacy', sessionHash: idHash };
  }
  let m = await env.DB.prepare('SELECT workspace_id, role, brand_ids FROM memberships WHERE user_id = ? AND workspace_id = ?')
    .bind(s.user_id, s.workspace_id).first();
  if (!m) {
    // Removed from that workspace: fall back to another, or a fresh one.
    m = await env.DB.prepare('SELECT workspace_id, role, brand_ids FROM memberships WHERE user_id = ? ORDER BY created_at LIMIT 1')
      .bind(s.user_id).first();
    if (!m) m = { workspace_id: await createWorkspace(env, s.user_id), role: 'owner', brand_ids: null };
    await env.DB.prepare('UPDATE sessions SET workspace_id = ? WHERE id_hash = ?').bind(m.workspace_id, idHash).run();
  }
  return { ws: m.workspace_id, userId: s.user_id, role: m.role,
    scope: m.role === 'member' && m.brand_ids ? JSON.parse(m.brand_ids) : null, via: 'session', sessionHash: idHash };
}

export async function callerFor(env, req) {
  const auth = req.headers.get('Authorization') || '';
  if (auth.startsWith('Key ')) {
    // An API key acts as an admin of its workspace (it cannot manage people).
    const row = await env.DB.prepare('SELECT id FROM workspaces WHERE api_key_hash = ?')
      .bind(await sha256Hex(auth.slice(4).trim())).first();
    return row ? { ws: row.id, userId: null, role: 'admin', scope: null, via: 'key' } : null;
  }
  return sessionCaller(env, cookie(req, 'tt_sid'));
}

export const RANK = { member: 1, admin: 2, owner: 3 };
export function need(who, role) {
  if (RANK[who.role] < RANK[role]) {
    throw new HttpError(403, role === 'owner' ? 'Only the workspace owner can do that' : 'Only workspace admins can do that');
  }
}

// ---- workspaces ----------------------------------------------------------

export async function myWorkspaces(env, userId) {
  if (!userId) return [];
  const { results } = await env.DB.prepare(`SELECT w.id, w.name, m.role FROM memberships m JOIN workspaces w ON w.id = m.workspace_id
      WHERE m.user_id = ? ORDER BY w.name COLLATE NOCASE`).bind(userId).all();
  return results;
}

export async function switchWorkspace(env, who, body) {
  if (!who.userId) throw new HttpError(400, 'Add your email first');
  const m = await env.DB.prepare('SELECT 1 FROM memberships WHERE user_id = ? AND workspace_id = ?')
    .bind(who.userId, String(body?.workspace_id ?? '')).first();
  if (!m) throw new HttpError(404, 'Workspace not found');
  await env.DB.prepare('UPDATE sessions SET workspace_id = ? WHERE id_hash = ?').bind(body.workspace_id, who.sessionHash).run();
  return { ok: true };
}

export async function addWorkspace(env, who, body) {
  if (!who.userId) throw new HttpError(400, 'Add your email first');
  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM memberships WHERE user_id = ? AND role = 'owner'`).bind(who.userId).first();
  if (n >= 10) throw new HttpError(409, 'You can own up to 10 workspaces');
  const ws = await createWorkspace(env, who.userId, body?.name || 'New workspace');
  if (who.sessionHash) await env.DB.prepare('UPDATE sessions SET workspace_id = ? WHERE id_hash = ?').bind(ws, who.sessionHash).run();
  return { id: ws };
}

export async function renameWorkspace(env, who, body) {
  await env.DB.prepare('UPDATE workspaces SET name = ? WHERE id = ?').bind(cleanWsName(body?.name), who.ws).run();
  return { ok: true };
}

export async function logoutEverywhere(env, who) {
  if (who.userId) await env.DB.prepare('DELETE FROM sessions WHERE user_id = ?').bind(who.userId).run();
  else if (who.sessionHash) await env.DB.prepare('DELETE FROM sessions WHERE id_hash = ?').bind(who.sessionHash).run();
  return { ok: true };
}

// ---- members and invites -------------------------------------------------

async function cleanScope(env, ws, role, brandIds) {
  if (role !== 'member' || brandIds == null) return null;
  if (!Array.isArray(brandIds) || !brandIds.every(x => typeof x === 'string') || brandIds.length > 50) {
    throw new HttpError(400, 'brand_ids must be a list of brand ids');
  }
  const ids = [...new Set(brandIds)];
  if (!ids.length) throw new HttpError(400, 'Give the member at least one brand, or access to all');
  const marks = ids.map(() => '?').join(',');
  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM brands WHERE workspace_id = ? AND id IN (${marks})`).bind(ws, ...ids).first();
  if (n !== ids.length) throw new HttpError(404, 'Brand not found');
  return JSON.stringify(ids);
}

const assignable = (who, role) => {
  if (!['admin', 'member'].includes(role)) throw new HttpError(400, 'Role must be admin or member');
  need(who, 'admin');
};

export async function listMembers(env, who) {
  const { results: members } = await env.DB.prepare(`SELECT u.id AS user_id, u.email, m.role, m.brand_ids, m.created_at
      FROM memberships m JOIN users u ON u.id = m.user_id WHERE m.workspace_id = ? ORDER BY m.created_at`).bind(who.ws).all();
  const { results: invites } = await env.DB.prepare(`SELECT id, email, role, brand_ids, expires_at FROM invites
      WHERE workspace_id = ? AND expires_at > ? ORDER BY created_at`).bind(who.ws, now()).all();
  const parse = r => ({ ...r, brand_ids: r.brand_ids ? JSON.parse(r.brand_ids) : null });
  return { members: members.map(parse), invites: invites.map(parse) };
}

export async function invite(env, who, body) {
  if (!who.userId) throw new HttpError(400, 'Add your email first');
  const role = body?.role || 'member';
  assignable(who, role);
  const email = normEmail(body?.email);
  const already = await env.DB.prepare(`SELECT 1 FROM memberships m JOIN users u ON u.id = m.user_id
      WHERE m.workspace_id = ? AND u.email = ?`).bind(who.ws, email).first();
  if (already) throw new HttpError(409, 'That person is already in this workspace');
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM invites WHERE workspace_id = ? AND expires_at > ?').bind(who.ws, now()).first();
  if (n >= 50) throw new HttpError(409, 'Too many open invites. Cancel some first.');
  const scope = await cleanScope(env, who.ws, role, body?.brand_ids);
  const token = randomToken('inv_'), id = 'ivt_' + randomToken('', 8), t = now();
  await env.DB.prepare(`DELETE FROM invites WHERE workspace_id = ? AND email = ?`).bind(who.ws, email).run();
  await env.DB.prepare(`INSERT INTO invites (id, workspace_id, email, role, brand_ids, token_hash, invited_by, expires_at, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .bind(id, who.ws, email, role, scope, await sha256Hex(token), who.userId, t + INVITE_TTL, t).run();
  const ws = await env.DB.prepare('SELECT name FROM workspaces WHERE id = ?').bind(who.ws).first();
  const inviter = await env.DB.prepare('SELECT email FROM users WHERE id = ?').bind(who.userId).first();
  await mailerFor(env).send({ to: email, ...inviteMail({ workspace: ws.name, inviter: inviter.email,
    link: `${env.PUBLIC_ORIGIN}/app.html?invite=${encodeURIComponent(token)}` }) });
  return { id, email, role, brand_ids: scope ? JSON.parse(scope) : null };
}

export async function cancelInvite(env, who, id) {
  need(who, 'admin');
  await env.DB.prepare('DELETE FROM invites WHERE id = ? AND workspace_id = ?').bind(id, who.ws).run();
  return { ok: true };
}

export async function acceptInvite(env, who, body) {
  if (!who.userId) throw new HttpError(400, 'Add your email first');
  const inv = await env.DB.prepare('SELECT * FROM invites WHERE token_hash = ? AND expires_at > ?')
    .bind(await sha256Hex(String(body?.token ?? '')), now()).first();
  if (!inv) throw new HttpError(404, 'This invite has expired or was cancelled');
  const me = await env.DB.prepare('SELECT email FROM users WHERE id = ?').bind(who.userId).first();
  if (me.email !== inv.email) throw new HttpError(403, `This invite is for ${inv.email}. Sign in with that email to accept it.`);
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO memberships (workspace_id, user_id, role, brand_ids, created_at) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (workspace_id, user_id) DO NOTHING`).bind(inv.workspace_id, who.userId, inv.role, inv.brand_ids, now()),
    env.DB.prepare('DELETE FROM invites WHERE id = ?').bind(inv.id),
    env.DB.prepare('UPDATE sessions SET workspace_id = ? WHERE id_hash = ?').bind(inv.workspace_id, who.sessionHash),
  ]);
  return { workspace_id: inv.workspace_id };
}

async function memberRow(env, ws, userId) {
  const m = await env.DB.prepare('SELECT role FROM memberships WHERE workspace_id = ? AND user_id = ?').bind(ws, userId).first();
  if (!m) throw new HttpError(404, 'Member not found');
  return m;
}

export async function updateMember(env, who, userId, body) {
  need(who, 'admin');
  const m = await memberRow(env, who.ws, userId);
  if (m.role === 'owner') throw new HttpError(403, 'The owner\'s role cannot be changed');
  const role = body?.role || m.role;
  assignable(who, role);
  const scope = await cleanScope(env, who.ws, role, body?.brand_ids === undefined ? null : body.brand_ids);
  await env.DB.prepare('UPDATE memberships SET role = ?, brand_ids = ? WHERE workspace_id = ? AND user_id = ?')
    .bind(role, scope, who.ws, userId).run();
  return { ok: true };
}

export async function removeMember(env, who, userId) {
  const self = userId === who.userId;
  if (!self) need(who, 'admin');
  const m = await memberRow(env, who.ws, userId);
  if (m.role === 'owner') throw new HttpError(403, 'The owner cannot be removed. Delete the workspace instead.');
  if (m.role === 'admin' && !self) need(who, 'owner');
  await env.DB.batch([
    env.DB.prepare('DELETE FROM memberships WHERE workspace_id = ? AND user_id = ?').bind(who.ws, userId),
    // Their sessions pointing here move elsewhere on the next request.
  ]);
  return { ok: true };
}
