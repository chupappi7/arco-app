import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { MAX_BRANDS } from './limits.js';
import { wsOf, inScope } from './scope.js';
import { cleanSlots, parseSlots } from './slots.js';

const cleanName = n => {
  const name = String(n ?? '').trim().replace(/\s+/g, ' ');
  if (!name) throw new HttpError(400, 'Give the brand a name');
  if ([...name].length > 60) throw new HttpError(400, 'Brand names can be at most 60 characters');
  return name;
};

export async function listBrands(env, w) {
  const sc = inScope(w, 'id');
  const { results } = await env.DB.prepare(`SELECT id, name, slots FROM brands WHERE workspace_id = ?${sc.sql} ORDER BY name COLLATE NOCASE`)
    .bind(wsOf(w), ...sc.binds).all();
  return results.map(b => ({ ...b, slots: parseSlots(b.slots) }));
}

async function getBrand(env, ws, id) {
  const row = await env.DB.prepare('SELECT id, name FROM brands WHERE id = ? AND workspace_id = ?').bind(id, ws).first();
  if (!row) throw new HttpError(404, 'Brand not found');
  return row;
}

export async function createBrand(env, ws, body) {
  const name = cleanName(body?.name);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM brands WHERE workspace_id = ?').bind(ws).first();
  if (n >= MAX_BRANDS) throw new HttpError(409, `A workspace can have up to ${MAX_BRANDS} brands`);
  const id = 'brd_' + randomToken('', 8);
  await env.DB.prepare('INSERT INTO brands (id, workspace_id, name, created_at) VALUES (?, ?, ?, ?)')
    .bind(id, ws, name, now()).run();
  // Accounts can be put straight into a new brand.
  if (Array.isArray(body?.account_ids) && body.account_ids.length) await assign(env, ws, body.account_ids, id);
  return { id, name };
}

// Rename, and/or set posting times (null clears them back to the default).
export async function renameBrand(env, ws, id, body) {
  const b = await getBrand(env, ws, id);
  const name = body?.name === undefined ? b.name : cleanName(body.name);
  await env.DB.prepare('UPDATE brands SET name = ? WHERE id = ? AND workspace_id = ?').bind(name, id, ws).run();
  if (body?.slots !== undefined) {
    await env.DB.prepare('UPDATE brands SET slots = ? WHERE id = ? AND workspace_id = ?').bind(cleanSlots(body.slots), id, ws).run();
  }
  return { id, name };
}

// Deleting a brand only ungroups its accounts; nothing is disconnected.
export async function deleteBrand(env, ws, id) {
  await getBrand(env, ws, id);
  await env.DB.batch([
    env.DB.prepare('UPDATE accounts SET brand_id = NULL WHERE brand_id = ? AND workspace_id = ?').bind(id, ws),
    env.DB.prepare('DELETE FROM brands WHERE id = ? AND workspace_id = ?').bind(id, ws),
  ]);
  return { ok: true };
}

// Move accounts into a brand (or out of any, with brandId null). Every id is
// checked against the workspace, so nobody can file someone else's account.
export async function assign(env, ws, accountIds, brandId) {
  if (!Array.isArray(accountIds) || !accountIds.length || accountIds.length > 50
      || !accountIds.every(x => typeof x === 'string')) {
    throw new HttpError(400, 'account_ids must be a list of account ids');
  }
  if (brandId !== null) await getBrand(env, ws, brandId);
  const marks = accountIds.map(() => '?').join(',');
  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM accounts WHERE workspace_id = ? AND id IN (${marks})`)
    .bind(ws, ...accountIds).first();
  if (n !== new Set(accountIds).size) throw new HttpError(404, 'Account not found');
  await env.DB.prepare(`UPDATE accounts SET brand_id = ? WHERE workspace_id = ? AND id IN (${marks})`)
    .bind(brandId, ws, ...accountIds).run();
  return { ok: true };
}
