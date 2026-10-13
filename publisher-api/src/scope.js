// The caller ("who") is { ws, userId, role, scope }. Older call sites and the
// tests pass a bare workspace id, which means the whole workspace.
export const wsOf = w => (typeof w === 'string' ? w : w.ws);
export const scopeOf = w => (typeof w === 'string' ? null : w.scope || null);

// SQL limiting rows to the caller's brands: appended to a WHERE clause, with
// its binds spread after the others. A member limited to brands sees nothing
// outside them, including accounts that are in no brand.
export function inScope(w, col = 'brand_id') {
  const s = scopeOf(w);
  if (!s) return { sql: '', binds: [] };
  if (!s.length) return { sql: ' AND 0', binds: [] };
  return { sql: ` AND ${col} IN (${s.map(() => '?').join(',')})`, binds: s };
}
