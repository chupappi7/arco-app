import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { MAX_FOLDERS } from './limits.js';
import { mediaUrl } from './media.js';
import { wsOf, inScope } from './scope.js';
import { brandFor } from './library.js';

// Library folders. One folder is one post: its photos in order (cover first)
// or one video, plus a note for whoever writes the caption. A folder's status
// comes from the posts made from it, so "the new ones" is a query, not a
// flag someone has to keep up to date.

const cleanName = n => {
  const name = String(n ?? '').trim().replace(/\s+/g, ' ');
  if (!name) throw new HttpError(400, 'Give the folder a name');
  if ([...name].length > 80) throw new HttpError(400, 'Folder names can be at most 80 characters');
  return name;
};
const cleanNote = n => {
  if (n === null || n === undefined) return null;
  const note = String(n).trim();
  if ([...note].length > 2000) throw new HttpError(400, 'A folder note can be at most 2000 characters');
  return note || null;
};

export const STATUSES = ['unused', 'awaiting_approval', 'scheduled', 'posted'];

export async function getFolder(env, w, id) {
  const sc = inScope(w, 'brand_id');
  const row = await env.DB.prepare(`SELECT * FROM library_folders WHERE id = ? AND workspace_id = ?${sc.sql}`)
    .bind(String(id), wsOf(w), ...sc.binds).first();
  if (!row) throw new HttpError(404, 'Folder not found');
  return row;
}

// brand: 'all', a brand id or 'none'; status: 'all' or one of STATUSES.
export async function listFolders(env, w, { brand = 'all', status = 'all', id = null } = {}) {
  if (status !== 'all' && !STATUSES.includes(status)) throw new HttpError(400, `status must be all or one of ${STATUSES.join(', ')}`);
  const ws = wsOf(w), sc = inScope(w, 'f.brand_id');
  const bf = id ? { sql: ' AND f.id = ?', binds: [String(id)] }
    : !brand || brand === 'all' ? { sql: '', binds: [] }
    : brand === 'none' ? { sql: ' AND f.brand_id IS NULL', binds: [] } : { sql: ' AND f.brand_id = ?', binds: [String(brand)] };
  const { results: folders } = await env.DB.prepare(`SELECT f.*, b.name AS brand_name FROM library_folders f
      LEFT JOIN brands b ON b.id = f.brand_id WHERE f.workspace_id = ?${sc.sql}${bf.sql} ORDER BY f.created_at DESC LIMIT ${MAX_FOLDERS}`)
    .bind(ws, ...sc.binds, ...bf.binds).all();
  if (!folders.length) return [];
  const { results: items } = await env.DB.prepare(`SELECT m.key, m.folder_id, m.position, m.content_type, m.name, m.duration_ms
      FROM media m JOIN library_folders f ON f.id = m.folder_id WHERE m.workspace_id = ? AND m.in_library = 1${sc.sql}${bf.sql}
      ORDER BY m.folder_id, m.position, m.created_at, m.key`).bind(ws, ...sc.binds, ...bf.binds).all();
  const { results: posts } = await env.DB.prepare(`SELECT p.folder_id, p.status,
      MIN(CASE WHEN p.status IN ('queued', 'publishing', 'draft') THEN p.scheduled_at END) AS next_at,
      MAX(CASE WHEN p.status = 'published' THEN p.scheduled_at END) AS last_at
      FROM posts p JOIN library_folders f ON f.id = p.folder_id WHERE p.workspace_id = ?${sc.sql}${bf.sql} GROUP BY p.folder_id, p.status`)
    .bind(ws, ...sc.binds, ...bf.binds).all();
  const out = folders.map(f => {
    const mine = items.filter(i => i.folder_id === f.id).map(i => ({ key: i.key, url: mediaUrl(env, i.key),
      kind: i.content_type.startsWith('video/') ? 'video' : 'photo', name: i.name, duration_ms: i.duration_ms }));
    const ps = posts.filter(p => p.folder_id === f.id), has = s => ps.some(p => p.status === s);
    const status = has('published') ? 'posted' : has('queued') || has('publishing') ? 'scheduled' : has('draft') ? 'awaiting_approval' : 'unused';
    const next = ps.map(p => p.next_at).filter(Boolean), last = ps.map(p => p.last_at).filter(Boolean);
    return { id: f.id, name: f.name, brand_id: f.brand_id, brand: f.brand_name || null, note: f.note,
      kind: mine.some(i => i.kind === 'video') ? 'video' : mine.length ? 'photos' : 'empty',
      items: mine, status, next_at: next.length ? Math.min(...next) : null, posted_at: last.length ? Math.max(...last) : null,
      created_at: f.created_at };
  });
  return status === 'all' ? out : out.filter(f => f.status === status);
}

export async function createFolder(env, w, body) {
  const ws = wsOf(w), name = cleanName(body?.name), brandId = await brandFor(env, w, body?.brand_id);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM library_folders WHERE workspace_id = ?').bind(ws).first();
  if (n >= MAX_FOLDERS) throw new HttpError(409, `The library holds up to ${MAX_FOLDERS} folders`);
  const id = 'fld_' + randomToken('', 8), t = now();
  await env.DB.prepare(`INSERT INTO library_folders (id, workspace_id, brand_id, name, note, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)`).bind(id, ws, brandId, name, cleanNote(body?.note), t, t).run();
  return (await listFolders(env, w, { id }))[0];
}

// Rename, re-note, move to another brand (its items follow), or reorder.
export async function updateFolder(env, w, id, body) {
  const f = await getFolder(env, w, id), ws = wsOf(w), t = now();
  const name = body?.name === undefined ? f.name : cleanName(body.name);
  const note = body?.note === undefined ? f.note : cleanNote(body.note);
  const brandId = body?.brand_id === undefined ? f.brand_id : await brandFor(env, w, body.brand_id);
  const stmts = [env.DB.prepare('UPDATE library_folders SET name = ?, note = ?, brand_id = ?, updated_at = ? WHERE id = ? AND workspace_id = ?')
    .bind(name, note, brandId, t, f.id, ws)];
  if (brandId !== f.brand_id) stmts.push(env.DB.prepare('UPDATE media SET brand_id = ? WHERE folder_id = ? AND workspace_id = ?').bind(brandId, f.id, ws));
  if (body?.order !== undefined) {
    const order = body.order;
    const { results } = await env.DB.prepare('SELECT key FROM media WHERE folder_id = ? AND workspace_id = ? AND in_library = 1').bind(f.id, ws).all();
    const have = new Set(results.map(r => r.key));
    if (!Array.isArray(order) || order.length !== have.size || !order.every(k => have.has(k)) || new Set(order).size !== order.length) {
      throw new HttpError(400, 'order must list every item in the folder exactly once');
    }
    order.forEach((k, i) => stmts.push(env.DB.prepare('UPDATE media SET position = ? WHERE key = ? AND workspace_id = ?').bind(i, k, ws)));
  }
  await env.DB.batch(stmts);
  return (await listFolders(env, w, { id: f.id }))[0];
}

// Deleting a folder keeps its items in the library, unfiled, unless asked to
// remove them too (then the cleanup deletes them, as with any removal).
export async function deleteFolder(env, w, id, { removeItems = false } = {}) {
  const f = await getFolder(env, w, id), ws = wsOf(w), t = now();
  if (removeItems) {
    const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND status IN ('queued', 'publishing', 'draft')
        AND video_key IN (SELECT key FROM media WHERE folder_id = ?)`).bind(ws, f.id).first();
    if (n) throw new HttpError(409, `This folder's video is used by ${n} scheduled post${n === 1 ? '' : 's'}`);
  }
  await env.DB.batch([
    removeItems
      ? env.DB.prepare('UPDATE media SET in_library = 0, folder_id = NULL, delete_after = ? WHERE folder_id = ? AND workspace_id = ?').bind(t, f.id, ws)
      : env.DB.prepare('UPDATE media SET folder_id = NULL, position = NULL WHERE folder_id = ? AND workspace_id = ?').bind(f.id, ws),
    env.DB.prepare('DELETE FROM library_folders WHERE id = ? AND workspace_id = ?').bind(f.id, ws),
  ]);
  return { ok: true };
}

// Files library items into a folder, after what is already there. The items
// take the folder's brand. A folder holds photos or one video, not both.
export async function fileInto(env, w, keys, folderId) {
  const f = await getFolder(env, w, folderId), ws = wsOf(w);
  if (!Array.isArray(keys) || !keys.length || keys.length > 100 || !keys.every(k => typeof k === 'string')) {
    throw new HttpError(400, 'keys must be a list of up to 100 library keys');
  }
  keys = [...new Set(keys)];
  const marks = keys.map(() => '?').join(',');
  const { results: adding } = await env.DB.prepare(`SELECT key, content_type FROM media WHERE workspace_id = ? AND in_library = 1 AND key IN (${marks})`)
    .bind(ws, ...keys).all();
  if (adding.length !== keys.length) throw new HttpError(404, 'One or more items are not in the library');
  const { results: there } = await env.DB.prepare('SELECT key, content_type, position FROM media WHERE workspace_id = ? AND folder_id = ? AND in_library = 1')
    .bind(ws, f.id).all();
  const all = [...there.filter(x => !keys.includes(x.key)), ...adding];
  const videos = all.filter(x => x.content_type.startsWith('video/')).length;
  if (videos > 1 || (videos && all.length > 1)) throw new HttpError(400, 'A folder holds photos or one video, not both');
  let pos = there.filter(x => !keys.includes(x.key)).reduce((m, x) => Math.max(m, x.position ?? -1), -1);
  await env.DB.batch([
    ...keys.map(k => env.DB.prepare('UPDATE media SET folder_id = ?, position = ?, brand_id = ? WHERE key = ? AND workspace_id = ?')
      .bind(f.id, ++pos, f.brand_id, k, ws)),
    env.DB.prepare('UPDATE library_folders SET updated_at = ? WHERE id = ?').bind(now(), f.id),
  ]);
  return f;
}
