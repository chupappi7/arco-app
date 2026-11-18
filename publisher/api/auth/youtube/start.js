// Google sign-in for YouTube. prompt=consent every time, so Google always
// hands over a refresh token (it only does so on a fresh consent); "add"
// also shows the account chooser, so a second channel can be connected.

import crypto from 'node:crypto';
import { b64url, clearCookie, env, originOf, setCookie } from '../../_lib.js';

const AUTHORIZE = 'https://accounts.google.com/o/oauth2/v2/auth';
const SCOPE = 'https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly';
export const ytRedirectUri = req => `${originOf(req)}/api/auth/youtube/callback`;

export default function handler(req, res) {
  const state = b64url(crypto.randomBytes(16));
  setCookie(res, 'yt_state', state, { maxAge: 600 });
  const add = new URL(req.url, 'https://x').searchParams.get('add') === '1';
  if (add) setCookie(res, 'yt_add', '1', { maxAge: 600 });
  else clearCookie(res, 'yt_add');

  const u = new URL(AUTHORIZE);
  u.searchParams.set('client_id', env('GOOGLE_CLIENT_ID'));
  u.searchParams.set('redirect_uri', ytRedirectUri(req));
  u.searchParams.set('response_type', 'code');
  u.searchParams.set('scope', SCOPE);
  u.searchParams.set('access_type', 'offline');
  u.searchParams.set('include_granted_scopes', 'true');
  u.searchParams.set('prompt', add ? 'select_account consent' : 'consent');
  u.searchParams.set('state', state);
  res.redirect(302, u.toString());
}
