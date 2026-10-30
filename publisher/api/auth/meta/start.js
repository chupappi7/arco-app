// Facebook Login, for Facebook Pages. (Instagram has its own login, see
// ../instagram.) Same shape as the TikTok start: a signed state cookie, and
// "add" keeps the current workspace.

import crypto from 'node:crypto';
import { b64url, clearCookie, env, originOf, setCookie } from '../../_lib.js';

export const META_DIALOG = 'https://www.facebook.com/v23.0/dialog/oauth';
// business_management makes Pages owned through a Business portfolio show up.
export const META_SCOPE = ['pages_show_list', 'pages_read_engagement', 'pages_read_user_content', 'pages_manage_posts',
  'business_management'].join(',');
export const metaRedirectUri = req => `${originOf(req)}/api/auth/meta/callback`;

export default function handler(req, res) {
  const state = b64url(crypto.randomBytes(16));
  setCookie(res, 'mt_state', state, { maxAge: 600 });
  const add = new URL(req.url, 'https://x').searchParams.get('add') === '1';
  if (add) setCookie(res, 'mt_add', '1', { maxAge: 600 });
  else clearCookie(res, 'mt_add');

  const u = new URL(META_DIALOG);
  u.searchParams.set('client_id', env('META_APP_ID'));
  u.searchParams.set('redirect_uri', metaRedirectUri(req));
  u.searchParams.set('state', state);
  u.searchParams.set('scope', META_SCOPE);
  u.searchParams.set('response_type', 'code');
  // Re-show the Page picker on reconnect, so someone can add a Page they skipped.
  u.searchParams.set('auth_type', 'rerequest');
  res.redirect(302, u.toString());
}
