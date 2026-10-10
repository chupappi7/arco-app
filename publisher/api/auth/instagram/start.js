// Instagram Login: the person signs in as the Instagram professional account
// itself; no Facebook Page is needed. "add" asks for credentials even when an
// Instagram session exists, so a second account can be added without logging
// the first one out.

import crypto from 'node:crypto';
import { b64url, clearCookie, env, originOf, setCookie } from '../../_lib.js';

const AUTHORIZE = 'https://www.instagram.com/oauth/authorize';
const SCOPE = 'instagram_business_basic,instagram_business_content_publish';
export const igRedirectUri = req => `${originOf(req)}/api/auth/instagram/callback`;

export default function handler(req, res) {
  const state = b64url(crypto.randomBytes(16));
  setCookie(res, 'ig_state', state, { maxAge: 600 });
  const add = new URL(req.url, 'https://x').searchParams.get('add') === '1';
  if (add) setCookie(res, 'ig_add', '1', { maxAge: 600 });
  else clearCookie(res, 'ig_add');

  const u = new URL(AUTHORIZE);
  u.searchParams.set('client_id', env('IG_APP_ID'));
  u.searchParams.set('redirect_uri', igRedirectUri(req));
  u.searchParams.set('response_type', 'code');
  u.searchParams.set('scope', SCOPE);
  u.searchParams.set('state', state);
  if (add) u.searchParams.set('force_reauth', 'true');
  res.redirect(302, u.toString());
}
