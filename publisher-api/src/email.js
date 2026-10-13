import { HttpError } from './http.js';

// Transactional mail through Resend. Tests put a fake on env.__mail.
export function mailerFor(env) {
  if (env.__mail) return env.__mail;
  return {
    async send({ to, subject, text, html }) {
      if (!env.RESEND_API_KEY || !env.MAIL_FROM) throw new HttpError(503, 'Email is not set up yet');
      const res = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: env.MAIL_FROM, to: [to], subject, text, html }),
        signal: AbortSignal.timeout(15_000),
      });
      if (!res.ok) {
        console.error('resend', res.status, (await res.text()).slice(0, 300));
        throw new HttpError(502, 'Could not send the email, try again in a minute');
      }
    },
  };
}

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const shell = body => `<div style="font:15px/1.6 -apple-system,Segoe UI,sans-serif;max-width:480px;margin:0 auto;color:#18181B">${body}
  <p style="color:#71717A;font-size:12px;margin-top:28px">ARCO Publisher · If you did not expect this email, you can ignore it.</p></div>`;

export const codeMail = code => ({
  subject: `${code} is your ARCO Publisher code`,
  text: `Your sign-in code is ${code}. It expires in 10 minutes. Never share it with anyone.`,
  html: shell(`<p>Your sign-in code:</p><p style="font-size:30px;letter-spacing:6px;font-weight:700">${esc(code)}</p>
    <p>It expires in 10 minutes. Never share it with anyone, ARCO Publisher will never ask for it.</p>`),
});

export const inviteMail = ({ workspace, inviter, link }) => ({
  subject: `${inviter} invited you to ${workspace} on ARCO Publisher`,
  text: `${inviter} invited you to the workspace "${workspace}" on ARCO Publisher. Accept: ${link} (expires in 7 days)`,
  html: shell(`<p><b>${esc(inviter)}</b> invited you to the workspace <b>${esc(workspace)}</b> on ARCO Publisher.</p>
    <p><a href="${esc(link)}" style="display:inline-block;background:#0284C7;color:#fff;padding:10px 16px;border-radius:9px;text-decoration:none;font-weight:600">Accept invite</a></p>
    <p style="color:#71717A">The invite expires in 7 days and only works for this email address.</p>`),
});
