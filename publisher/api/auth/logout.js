import { clearCookie, rawCookie, workerFetch, SESSION_COOKIE } from '../_lib.js';

export default async function handler(req, res) {
  const sid = rawCookie(req, SESSION_COOKIE);
  if (sid) {
    try {
      await workerFetch('/v1/logout', { method: 'POST', headers: { Cookie: `${SESSION_COOKIE}=${encodeURIComponent(sid)}` } });
    } catch { /* the cookie is cleared either way */ }
  }
  clearCookie(res, SESSION_COOKIE);
  clearCookie(res, 'tt_at');
  res.redirect(302, '/');
}
