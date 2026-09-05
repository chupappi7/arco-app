// The creator's own posting settings, straight from TikTok.
//
// The content-sharing guidelines require the posting page to be built from
// this response and to re-read it every time the page renders: only the
// privacy levels this creator actually has may be offered, and a control the
// creator has turned off must be shown turned off. So this is deliberately
// not cached.

import { CREATOR_INFO_URL, accessTokenFrom, envelope, fail } from './_lib.js';

export default async function handler(req, res) {
  const token = await accessTokenFrom(req);
  if (!token) return fail(res, 401, 'not connected', 'no_session');

  try {
    const r = await fetch(CREATOR_INFO_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
    });
    const body = await envelope(r, 'creator info');
    res.setHeader('Cache-Control', 'no-store');
    res.status(200).json(body.data || {});
  } catch (err) {
    // An expired token is the ordinary case, not a failure worth alarming over.
    const dead = /access_token_invalid|scope_not_authorized/.test(err.message);
    fail(res, dead ? 401 : 502, err.message, err.code);
  }
}
