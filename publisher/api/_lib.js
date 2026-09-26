// Shared bits for the serverless functions.
//
// There is no database here on purpose. The only thing worth persisting is the
// user's access token, and that lives in an httpOnly cookie for the length of
// its own 24h life. A dropped session just means logging in again, which is
// the correct trade for never storing someone's TikTok token on a host we
// don't control.

import crypto from 'node:crypto';

export const AUTHORIZE_URL = 'https://www.tiktok.com/v2/auth/authorize/';
export const OAUTH_TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/';

// video.publish is what the audit is for; user.info.basic comes with Login Kit.
export const SCOPE = 'user.info.basic,video.publish,video.upload';

export const b64url = buf =>
  buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

export function env(name) {
  const v = process.env[name];
  if (!v) throw new Error(`missing environment variable ${name}`);
  return v;
}

/** The deployment's own origin, which must equal the registered redirect URI. */
export function originOf(req) {
  const proto = req.headers['x-forwarded-proto'] || 'https';
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  return `${proto}://${host}`;
}

export const redirectUri = req => `${originOf(req)}/api/auth/callback`;

// --- cookies -------------------------------------------------------------
// Signed so a session cookie cannot be forged, httpOnly so page scripts can
// never read the token, SameSite=Lax so it survives the redirect back from
// TikTok but is not sent from third-party pages.

function sign(value, secret) {
  return b64url(crypto.createHmac('sha256', secret).update(value).digest());
}

export function setCookie(res, name, value, { maxAge = 86400 } = {}) {
  const signed = `${b64url(Buffer.from(value))}.${sign(value, env('SESSION_SECRET'))}`;
  const parts = [
    `${name}=${signed}`,
    'Path=/',
    'HttpOnly',
    'Secure',
    'SameSite=Lax',
    `Max-Age=${maxAge}`,
  ];
  append(res, parts.join('; '));
}

export function clearCookie(res, name) {
  append(res, `${name}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`);
}

function append(res, cookie) {
  const prev = res.getHeader('Set-Cookie');
  res.setHeader('Set-Cookie', prev ? [].concat(prev, cookie) : [cookie]);
}

export function readCookie(req, name) {
  const raw = (req.headers.cookie || '')
    .split(';')
    .map(s => s.trim())
    .find(s => s.startsWith(`${name}=`));
  if (!raw) return null;
  const [payload, mac] = raw.slice(name.length + 1).split('.');
  if (!payload || !mac) return null;
  let value;
  try {
    value = Buffer.from(payload.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString();
  } catch {
    return null;
  }
  const expected = sign(value, env('SESSION_SECRET'));
  // Constant-time compare: a length mismatch would throw, so guard it first.
  if (mac.length !== expected.length) return null;
  if (!crypto.timingSafeEqual(Buffer.from(mac), Buffer.from(expected))) return null;
  return value;
}

// --- the Worker ------------------------------------------------------------

export const SESSION_COOKIE = 'tt_sid';
const SESSION_MAX_AGE = 30 * 86400;

/** The Worker's session id, as the browser holds it (plain, not signed:
 *  the Worker stores only its hash and is the one that checks it). */
export function rawCookie(req, name) {
  const raw = (req.headers.cookie || '').split(';').map(s => s.trim()).find(s => s.startsWith(`${name}=`));
  return raw ? decodeURIComponent(raw.slice(name.length + 1)) : null;
}

export function setSessionCookie(res, id) {
  append(res, `${SESSION_COOKIE}=${encodeURIComponent(id)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${SESSION_MAX_AGE}`);
}

export async function workerFetch(path, init = {}) {
  return fetch(`${env('WORKER_ORIGIN')}${path}`, init);
}
