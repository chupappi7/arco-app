// Step one of Login Kit: send the operator to TikTok to authorize.
//
// The state and the PKCE verifier are handed to the browser as short-lived
// signed cookies rather than kept server-side, because there is no server-side
// to keep them in. Signing is what stops either being tampered with; the
// callback refuses anything that does not match.

import crypto from 'node:crypto';
import { AUTHORIZE_URL, SCOPE, b64url, env, redirectUri, setCookie } from '../_lib.js';

export default function handler(req, res) {
  const state = b64url(crypto.randomBytes(16));
  const verifier = b64url(crypto.randomBytes(32));
  const challenge = b64url(crypto.createHash('sha256').update(verifier).digest());

  // Ten minutes is longer than anyone takes to tap Authorize, and short enough
  // that an abandoned attempt cannot be resumed later.
  setCookie(res, 'tt_state', state, { maxAge: 600 });
  setCookie(res, 'tt_verifier', verifier, { maxAge: 600 });

  const u = new URL(AUTHORIZE_URL);
  u.searchParams.set('client_key', env('TIKTOK_CLIENT_KEY'));
  u.searchParams.set('scope', SCOPE);
  u.searchParams.set('response_type', 'code');
  u.searchParams.set('redirect_uri', redirectUri(req));
  u.searchParams.set('state', state);
  u.searchParams.set('code_challenge', challenge);
  u.searchParams.set('code_challenge_method', 'S256');

  res.redirect(302, u.toString());
}
