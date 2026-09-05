import { clearCookie } from '../_lib.js';

export default function handler(req, res) {
  clearCookie(res, 'tt_at');
  res.redirect(302, '/');
}
