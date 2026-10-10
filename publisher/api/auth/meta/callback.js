// Facebook sends the browser back with ?code=. The Worker exchanges it and
// keeps the Page tokens; this only checks the state cookie and sets the session.

import { clearCookie, readCookie, rawCookie, env, setSessionCookie, workerFetch, SESSION_COOKIE } from '../../_lib.js';
import { metaRedirectUri } from './start.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const denied = url.searchParams.get('error_description') || url.searchParams.get('error');
  const expected = readCookie(req, 'mt_state');
  const adding = readCookie(req, 'mt_add') === '1';
  clearCookie(res, 'mt_state');
  clearCookie(res, 'mt_add');

  if (denied) return back(res, `Facebook returned: ${denied}`);
  if (!code) return back(res, 'no authorization code came back');
  if (!expected || state !== expected) return back(res, 'the sign-in attempt expired or did not match, start over');

  let body;
  try {
    const r = await workerFetch('/internal/meta-oauth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Internal-Secret': env('INTERNAL_SECRET') },
      body: JSON.stringify({ code, redirect_uri: metaRedirectUri(req),
        session_id: adding ? rawCookie(req, SESSION_COOKIE) || undefined : undefined }),
    });
    body = await r.json();
    if (!r.ok) return back(res, body.error || `sign-in failed (${r.status})`);
  } catch {
    return back(res, 'could not reach the ARCO Publisher service, try again');
  }
  setSessionCookie(res, body.session_id);
  const n = (body.account_ids || []).length;
  res.redirect(302, `/app.html?connected=${n}${adding ? '#settings' : ''}`);
}

function back(res, why) {
  res.redirect(302, '/app.html?auth_error=' + encodeURIComponent(why));
}
