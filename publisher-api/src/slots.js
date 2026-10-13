import { HttpError } from './http.js';

// Posting slots: the days (0 = Sunday … 6) and wall-clock times ("HH:MM", in
// the workspace's zone) that "Add to queue" fills. Stored as JSON text.
export function cleanSlots(v) {
  if (v === null) return null;
  const days = Array.isArray(v?.days) ? [...new Set(v.days)] : null;
  const times = Array.isArray(v?.times) ? [...new Set(v.times)] : null;
  if (!days || !days.length || !days.every(d => Number.isInteger(d) && d >= 0 && d <= 6)) {
    throw new HttpError(400, 'Pick at least one day for posting times');
  }
  if (!times || !times.length || times.length > 24 || !times.every(t => /^([01]\d|2[0-3]):[0-5]\d$/.test(t))) {
    throw new HttpError(400, 'Posting times are 1 to 24 times like 09:00');
  }
  return JSON.stringify({ days: days.sort(), times: times.sort() });
}
export const parseSlots = s => (s ? JSON.parse(s) : null);
