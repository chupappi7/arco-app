// Threads Login: the person signs in as the Threads profile itself, like
// Instagram Login. Threads has no option to force a fresh sign-in, so adding a
// second profile means switching accounts on threads.net first.

import crypto from 'node:crypto';
import { b64url, clearCookie, env, originOf, setCookie } from '../../_lib.js';

const AUTHORIZE = 'https://threads.net/oauth/authorize';
const SCOPE = 'threads_basic,threads_content_publish,threads_manage_insights';
export const thRedirectUri = req => `${originOf(req)}/api/auth/threads/callback`;

export default function handler(req, res) {
  const state = b64url(crypto.randomBytes(16));
  setCookie(res, 'th_state', state, { maxAge: 600 });
  const add = new URL(req.url, 'https://x').searchParams.get('add') === '1';
  if (add) setCookie(res, 'th_add', '1', { maxAge: 600 });
  else clearCookie(res, 'th_add');

  const u = new URL(AUTHORIZE);
  u.searchParams.set('client_id', env('TH_APP_ID'));
  u.searchParams.set('redirect_uri', thRedirectUri(req));
  u.searchParams.set('response_type', 'code');
  u.searchParams.set('scope', SCOPE);
  u.searchParams.set('state', state);
  res.redirect(302, u.toString());
}
