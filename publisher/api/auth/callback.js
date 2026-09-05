// Step two: TikTok sends the operator back here with ?code=. Exchange it for
// an access token, drop the token in an httpOnly cookie, and return to the
// page. The token never reaches page scripts and is never written to disk.

import {
  OAUTH_TOKEN_URL,
  clearCookie,
  env,
  envelope,
  readCookie,
  redirectUri,
  setCookie,
} from '../_lib.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');

  // The operator tapped Cancel on TikTok's consent screen.
  const denied = url.searchParams.get('error');
  if (denied) return back(res, `TikTok returned ${denied}`);

  const expected = readCookie(req, 'tt_state');
  const verifier = readCookie(req, 'tt_verifier');
  clearCookie(res, 'tt_state');
  clearCookie(res, 'tt_verifier');

  if (!code) return back(res, 'no authorization code came back');
  // A missing or mismatched state means this callback was not started by us.
  if (!expected || state !== expected) return back(res, 'state mismatch, start over');
  if (!verifier) return back(res, 'the login attempt expired, start over');

  let body;
  try {
    const r = await fetch(OAUTH_TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_key: env('TIKTOK_CLIENT_KEY'),
        client_secret: env('TIKTOK_CLIENT_SECRET'),
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri(req),
        code_verifier: verifier,
      }),
    });
    body = await envelope(r, 'code exchange');
  } catch (err) {
    return back(res, err.message);
  }

  if (!body.access_token) return back(res, 'no access token in the response');

  // Expire the cookie with the token so a dead session logs out by itself
  // rather than failing every call until someone notices.
  setCookie(res, 'tt_at', body.access_token, {
    maxAge: Math.max(60, Number(body.expires_in) || 86400),
  });
  res.redirect(302, '/');
}

function back(res, why) {
  res.redirect(302, '/?auth_error=' + encodeURIComponent(why));
}
