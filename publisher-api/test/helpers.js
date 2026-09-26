// Applies schema.sql to the test D1. Statements are split on ";" at line end.
import schema from '../schema.sql?raw';

export async function applySchema(env) {
  const statements = schema.split(/;\s*$/m).map(s => s.trim()).filter(Boolean);
  for (const sql of statements) await env.DB.prepare(sql).run();
}
