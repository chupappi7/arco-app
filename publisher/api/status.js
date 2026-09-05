// Poll a publish. The guidelines require the page to show a processing state
// rather than claiming success the moment the request returns.

import { STATUS_FETCH_URL, accessTokenFrom, envelope, fail } from './_lib.js';

export default async function handler(req, res) {
  const token = await accessTokenFrom(req);
  if (!token) return fail(res, 401, 'not connected', 'no_session');

  const url = new URL(req.url, 'https://placeholder.invalid');
  const publishId = url.searchParams.get('publish_id');
  if (!publishId) return fail(res, 400, 'publish_id is required');

  try {
    const r = await fetch(STATUS_FETCH_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify({ publish_id: publishId }),
    });
    const body = await envelope(r, 'status fetch');
    res.setHeader('Cache-Control', 'no-store');
    res.status(200).json(body.data || {});
  } catch (err) {
    fail(res, 502, err.message, err.code);
  }
}
