// Step two of email sign-in: the code the person typed goes to the Worker,
// which checks it and opens a session; this sets the session cookie. A
// session from before email sign-in is passed along so its workspace can be
// claimed by whoever verifies first.

import { rawCookie, setSessionCookie, workerFetch, env, SESSION_COOKIE } from '../../_lib.js';

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  const { email, code } = typeof req.body === 'object' && req.body ? req.body : {};
  try {
    const r = await workerFetch('/internal/email-verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Internal-Secret': env('INTERNAL_SECRET') },
      body: JSON.stringify({ email, code, legacy_session: rawCookie(req, SESSION_COOKIE) || undefined }),
    });
    const body = await r.json();
    if (!r.ok) return res.status(r.status).json({ error: body.error || 'Sign-in failed' });
    setSessionCookie(res, body.session_id);
    return res.status(200).json({ ok: true });
  } catch {
    return res.status(502).json({ error: 'Could not reach the ARCO Publisher service, try again' });
  }
}
