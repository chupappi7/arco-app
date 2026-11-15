import { HttpError, now } from './http.js';
import { MAX_LIBRARY } from './limits.js';
import { mediaUrl } from './media.js';
import { wsOf, scopeOf, inScope } from './scope.js';

// The library holds photos and videos uploaded ahead of time. They are ordinary media
// rows marked in_library, with no post and no delete date, so the cleanup
// never takes them. Scheduling photos copies them (POST /v1/media/copy): a
// photo post owns its own images, and the library keeps the original. A
// video post points at the library video instead (posts.video_key).

const keyList = keys => {
  if (!Array.isArray(keys) || !keys.length || keys.length > 100 || !keys.every(k => typeof k === 'string')) {
    throw new HttpError(400, 'keys must be a list of up to 100 image keys');
  }
  return [...new Set(keys)];
};

// A brand to file under: null (shared), or one of the workspace's brands that
// the caller can see.
export async function brandFor(env, w, brandId) {
  if (brandId === null || brandId === undefined || brandId === '') {
    if (scopeOf(w)) throw new HttpError(400, 'Choose one of your brands');
    return null;
  }
  const sc = inScope(w, 'id');
  const row = await env.DB.prepare(`SELECT id FROM brands WHERE id = ? AND workspace_id = ?${sc.sql}`)
    .bind(String(brandId), wsOf(w), ...sc.binds).first();
  if (!row) throw new HttpError(404, 'Brand not found');
  return row.id;
}

// brand: 'all', a brand id, or 'none' (shared, in no brand).
export async function listLibrary(env, w, brand = 'all') {
  const sc = inScope(w, 'brand_id');
  const bf = !brand || brand === 'all' ? { sql: '', binds: [] }
    : brand === 'none' ? { sql: ' AND brand_id IS NULL', binds: [] } : { sql: ' AND brand_id = ?', binds: [String(brand)] };
  const { results } = await env.DB.prepare(`SELECT key, brand_id, name, bytes, content_type, duration_ms, width, height, created_at FROM media
      WHERE workspace_id = ? AND in_library = 1${sc.sql}${bf.sql} ORDER BY created_at DESC, key LIMIT ${MAX_LIBRARY}`)
    .bind(wsOf(w), ...sc.binds, ...bf.binds).all();
  return { items: results.map(r => ({ ...r, url: mediaUrl(env, r.key) })) };
}

// Fresh uploads (POST /v1/media) are moved into the library.
export async function addToLibrary(env, w, body) {
  const ws = wsOf(w), keys = keyList(body?.keys), brandId = await brandFor(env, w, body?.brand_id);
  const names = body?.names && typeof body.names === 'object' ? body.names : {};
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND in_library = 1').bind(ws).first();
  if (n + keys.length > MAX_LIBRARY) throw new HttpError(409, `The library holds up to ${MAX_LIBRARY} items`);
  const marks = keys.map(() => '?').join(',');
  const { n: fresh } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND key IN (${marks})
      AND post_id IS NULL AND in_library = 0`).bind(ws, ...keys).first();
  if (fresh !== keys.length) throw new HttpError(400, 'One or more images are missing or already used. Upload them again.');
  await env.DB.batch(keys.map(k => env.DB.prepare(`UPDATE media SET in_library = 1, delete_after = NULL, brand_id = ?, name = ?
      WHERE workspace_id = ? AND key = ?`).bind(brandId, String(names[k] ?? '').slice(0, 120) || null, ws, k)));
  return listLibrary(env, w);
}

async function ownedKeys(env, w, keys) {
  const sc = inScope(w, 'brand_id'), marks = keys.map(() => '?').join(',');
  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND in_library = 1
      AND key IN (${marks})${sc.sql}`).bind(wsOf(w), ...keys, ...sc.binds).first();
  if (n !== keys.length) throw new HttpError(404, 'One or more photos are not in the library');
}

export async function moveInLibrary(env, w, body) {
  const keys = keyList(body?.keys);
  await ownedKeys(env, w, keys);
  const brandId = await brandFor(env, w, body?.brand_id);
  const marks = keys.map(() => '?').join(',');
  await env.DB.prepare(`UPDATE media SET brand_id = ? WHERE workspace_id = ? AND in_library = 1 AND key IN (${marks})`)
    .bind(brandId, wsOf(w), ...keys).run();
  return { ok: true };
}

// Removing hands the files to the cleanup, which deletes them on its next run.
// Photo posts own copies, but a video post points at the library video
// itself, so a video stays while a post that has not finished still uses it.
export async function removeFromLibrary(env, w, body) {
  const keys = keyList(body?.keys);
  await ownedKeys(env, w, keys);
  const marks = keys.map(() => '?').join(',');
  const { n: used } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND video_key IN (${marks})
      AND status IN ('queued', 'publishing')`).bind(wsOf(w), ...keys).first();
  if (used) throw new HttpError(409, `${used === 1 ? 'A scheduled post uses' : `${used} scheduled posts use`} this video. Cancel ${used === 1 ? 'it' : 'them'} or wait until ${used === 1 ? 'it is' : 'they are'} published.`);
  await env.DB.prepare(`UPDATE media SET in_library = 0, delete_after = ? WHERE workspace_id = ? AND in_library = 1 AND key IN (${marks})`)
    .bind(now(), wsOf(w), ...keys).run();
  return { ok: true };
}
