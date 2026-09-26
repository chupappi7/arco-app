// D1 in production rejects statements with more than 100 bound parameters;
// Miniflare does not. This wraps env.DB to enforce the real limit in tests.
export function strictDb(db) {
  const wrapStmt = stmt => new Proxy(stmt, {
    get(t, k) {
      if (k === 'bind') return (...args) => {
        if (args.length > 100) throw new Error(`D1_ERROR: too many SQL variables (${args.length})`);
        return wrapStmt(t.bind(...args));
      };
      const v = t[k]; return typeof v === 'function' ? v.bind(t) : v;
    },
  });
  return new Proxy(db, {
    get(t, k) {
      if (k === 'prepare') return sql => wrapStmt(t.prepare(sql));
      const v = t[k]; return typeof v === 'function' ? v.bind(t) : v;
    },
  });
}
