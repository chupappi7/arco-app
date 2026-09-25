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
  // No state cookie at all: the sign-in was started by the command-line token
  // tool, which holds its own state and PKCE verifier. The production app has
  // only this one redirect URI, so the tool lands here too. Leave the code
  // unspent and the address bar untouched so it can be copied back.
  if (!expected) return handoff(res);
  // A mismatched state means this callback was not started by us.
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

function handoff(res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.status(200).send(`<!doctype html><meta charset="utf-8">
<meta name="robots" content="noindex"><title>ARCO Publisher</title>
<body style="font:15px/1.6 -apple-system,sans-serif;max-width:560px;margin:15vh auto;padding:0 20px;color:#18181B;background:#F4F4F5">
<h1 style="font-size:20px">Authorized</h1>
<p>Copy the full address from the address bar and paste it back into the terminal
that started this sign-in. This page has not used the code.</p></body>`);
}
