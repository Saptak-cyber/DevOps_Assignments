// Appointment times are clinic wall-clock values without an offset, e.g. "2026-10-08T10:30:00".
// We never pass them through Date parsing, so the browser's time zone can't shift them.

export const DAY_START = 8 * 60; // 08:00
export const DAY_END = 20 * 60; // 20:00

const pad = (n) => String(n).padStart(2, '0');

export function todayIso() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function shiftDay(iso, days) {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d + days);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function minutesOf(stamp) {
  const [, t] = stamp.split('T');
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m;
}

export const hhmm = (minutes) => `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`;

export const clock = (stamp) => stamp.slice(11, 16);

export function longDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' });
}

export function nowMinutes() {
  const d = new Date();
  return d.getHours() * 60 + d.getMinutes();
}

export function formatDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (!h) return `${m} min`;
  return m ? `${h} h ${m} min` : `${h} h`;
}
