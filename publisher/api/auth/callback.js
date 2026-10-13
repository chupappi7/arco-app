// Step two: TikTok sends the browser back with ?code=. The Worker does the
// exchange and keeps the tokens; this function only proves the round trip
// was ours (state + PKCE verifier cookies) and hands over the session cookie.

import {
  clearCookie, readCookie, rawCookie, redirectUri, env, setSessionCookie, workerFetch, SESSION_COOKIE,
} from '../_lib.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const denied = url.searchParams.get('error');
  if (denied) return back(res, `TikTok returned ${denied}`);

  const expected = readCookie(req, 'tt_state');
  const verifier = readCookie(req, 'tt_verifier');
  const adding = readCookie(req, 'tt_add') === '1';
  clearCookie(res, 'tt_state');
  clearCookie(res, 'tt_verifier');
  clearCookie(res, 'tt_add');

  if (!code) return back(res, 'no authorization code came back');
  // No state cookie at all: the sign-in was started by the command-line token
  // tool, which keeps its own state and verifier. Leave the code unspent.
  if (!expected) return handoff(res);
  if (state !== expected) return back(res, 'state mismatch, start over');
  if (!verifier) return back(res, 'the sign-in attempt expired, start over');

  let body;
  try {
    const r = await workerFetch('/internal/oauth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Internal-Secret': env('INTERNAL_SECRET') },
      body: JSON.stringify({
        code, code_verifier: verifier, redirect_uri: redirectUri(req),
        session_id: rawCookie(req, SESSION_COOKIE) || undefined,
      }),
    });
    body = await r.json();
    if (!r.ok) return back(res, body.error || `sign-in failed (${r.status})`);
  } catch (err) {
    return back(res, 'could not reach the ARCO Publisher service, try again');
  }

  setSessionCookie(res, body.session_id);
  res.redirect(302, adding ? '/app.html?connected=1#accounts' : '/app.html');
}

function back(res, why) {
  res.redirect(302, '/app.html?auth_error=' + encodeURIComponent(why));
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
