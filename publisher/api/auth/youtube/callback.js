// Google sends the browser back with ?code=. The Worker exchanges it and keeps
// the refresh token; this only checks the state cookie and sets the session.

import { clearCookie, readCookie, rawCookie, env, setSessionCookie, workerFetch, SESSION_COOKIE } from '../../_lib.js';
import { ytRedirectUri } from './start.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const denied = url.searchParams.get('error');
  const expected = readCookie(req, 'yt_state');
  const adding = readCookie(req, 'yt_add') === '1';
  clearCookie(res, 'yt_state');
  clearCookie(res, 'yt_add');

  if (denied) return back(res, denied === 'access_denied' ? 'YouTube access was not allowed' : `Google returned: ${denied}`);
  if (!code) return back(res, 'no authorization code came back');
  if (!expected || state !== expected) return back(res, 'the sign-in attempt expired or did not match, start over');

  let body;
  try {
    const r = await workerFetch('/internal/yt-oauth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Internal-Secret': env('INTERNAL_SECRET') },
      body: JSON.stringify({ code, redirect_uri: ytRedirectUri(req), session_id: rawCookie(req, SESSION_COOKIE) || undefined }),
    });
    body = await r.json();
    if (!r.ok) return back(res, body.error || `connecting YouTube failed (${r.status})`);
  } catch {
    return back(res, 'could not reach the ARCO Publisher service, try again');
  }
  setSessionCookie(res, body.session_id);
  res.redirect(302, `/app.html?connected=1${adding ? '#accounts' : ''}`);
}

function back(res, why) {
  res.redirect(302, '/app.html?auth_error=' + encodeURIComponent(why));
}
