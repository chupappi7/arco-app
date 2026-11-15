import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { MAX_IMAGE_BYTES, MAX_WORKSPACE_BYTES, KEEP_UNATTACHED, MAX_VIDEO_BYTES, UPLOAD_TICKET_TTL, MAX_LIBRARY } from './limits.js';
import { wsOf, scopeOf, inScope } from './scope.js';
import { brandFor } from './library.js';
import { getFolder } from './folders.js';

const TYPES = {
  'image/jpeg': { ext: 'jpg', magic: [0xff, 0xd8, 0xff] },
  'image/png': { ext: 'png', magic: [0x89, 0x50, 0x4e, 0x47] },
};

const FULL = `Storage is full (${MAX_WORKSPACE_BYTES / 1024 / 1024 / 1024} GB). Images are freed 7 days after their post is done; remove videos you no longer need from the library.`;

export const mediaUrl = (env, key) => `${env.PUBLIC_ORIGIN}/media/${key}`;

export async function workspaceBytes(env, ws) {
  const row = await env.DB.prepare('SELECT COALESCE(SUM(bytes), 0) AS b FROM media WHERE workspace_id = ?').bind(ws).first();
  return row.b;
}

export async function uploadMedia(env, ws, req) {
  const contentType = (req.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
  const type = TYPES[contentType];
  if (!type) throw new HttpError(400, 'Upload JPG or PNG images only');
  const declared = Number(req.headers.get('Content-Length') || 0);
  if (declared > MAX_IMAGE_BYTES) throw new HttpError(400, 'Each image must be 5 MB or smaller');
  const bytes = new Uint8Array(await req.arrayBuffer());
  if (bytes.length === 0) throw new HttpError(400, 'The image is empty');
  if (bytes.length > MAX_IMAGE_BYTES) throw new HttpError(400, 'Each image must be 5 MB or smaller');
  if (!type.magic.every((b, i) => bytes[i] === b)) throw new HttpError(400, 'That file is not a valid JPG or PNG image');
  if ((await workspaceBytes(env, ws)) + bytes.length > MAX_WORKSPACE_BYTES) {
    throw new HttpError(409, FULL);
  }

  const key = `${ws}/${randomToken('', 16)}.${type.ext}`;
  await env.MEDIA.put(key, bytes, { httpMetadata: { contentType } });
  const t = now();
  await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, delete_after)
      VALUES (?, ?, ?, ?, ?, ?)`).bind(key, ws, bytes.length, contentType, t, t + KEEP_UNATTACHED).run();
  return { key, url: mediaUrl(env, key), bytes: bytes.length, content_type: contentType };
}

// Video fetchers (and browsers playing a preview) ask for byte ranges.
export async function serveMedia(env, key, method = 'GET', req = null) {
  const range = req?.headers.get('Range');
  let obj;
  try {
    obj = method === 'HEAD' ? await env.MEDIA.head(key) : await env.MEDIA.get(key, range ? { range: req.headers } : {});
  } catch {
    return new Response(null, { status: 416 });
  }
  if (!obj) return new Response(null, { status: 404 });
  const part = method !== 'HEAD' && range && obj.range ? obj.range : null;
  let offset = 0, length = obj.size;
  if (part) {
    if ('suffix' in part) { length = Math.min(part.suffix, obj.size); offset = obj.size - length; }
    else { offset = part.offset ?? 0; length = part.length ?? obj.size - offset; }
  }
  return new Response(method === 'HEAD' ? null : obj.body, {
    status: part ? 206 : 200,
    headers: {
      'Content-Type': obj.httpMetadata?.contentType || 'application/octet-stream',
      'Content-Length': String(length),
      'Accept-Ranges': 'bytes',
      ...(part ? { 'Content-Range': `bytes ${offset}-${offset + length - 1}/${obj.size}` } : {}),
      'Cache-Control': 'public, max-age=3600',
      'X-Content-Type-Options': 'nosniff',
      // Public only because TikTok and Meta fetch posts by URL; keys are 128
      // random bits, and nothing should index them.
      'X-Robots-Tag': 'noindex, nofollow',
    },
  });
}

// One upload, several posts: each post owns its images (that is what lets a
// finished post free its storage on its own clock), so posting the same
// photos to TikTok, Instagram and Facebook copies them once per extra post.
export async function copyMedia(env, w, keys) {
  const ws = wsOf(w);
  if (!Array.isArray(keys) || !keys.length || keys.length > 35 || !keys.every(k => typeof k === 'string')) {
    throw new HttpError(400, 'keys must be a list of up to 35 image keys');
  }
  if (keys.some(k => !/\.(jpg|png)$/.test(k))) throw new HttpError(400, 'Videos are not copied: schedule them straight from the library');
  const marks = keys.map(() => '?').join(',');
  const { results } = await env.DB.prepare(`SELECT key, bytes, content_type FROM media
      WHERE workspace_id = ? AND key IN (${marks})`).bind(ws, ...keys).all();
  const rows = new Map(results.map(r => [r.key, r]));
  if (rows.size !== new Set(keys).size) throw new HttpError(400, 'One or more images are missing. Upload them again.');
  // A member limited to brands may only copy images of posts they can see.
  if (scopeOf(w)) {
    const sc = inScope(w, 'a.brand_id');
    const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM media m JOIN posts p ON p.id = m.post_id
        JOIN accounts a ON a.id = p.account_id WHERE m.workspace_id = ? AND m.key IN (${marks})${sc.sql}`)
      .bind(ws, ...keys, ...sc.binds).first();
    const { n: attached } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND key IN (${marks})
        AND post_id IS NOT NULL`).bind(ws, ...keys).first();
    if (n !== attached) throw new HttpError(404, 'One or more images are missing. Upload them again.');
    const lsc = inScope(w, 'brand_id');
    const { n: lib } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND key IN (${marks}) AND in_library = 1`)
      .bind(ws, ...keys).first();
    const { n: libOk } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND key IN (${marks}) AND in_library = 1${lsc.sql}`)
      .bind(ws, ...keys, ...lsc.binds).first();
    if (lib !== libOk) throw new HttpError(404, 'One or more images are missing. Upload them again.');
  }
  const total = keys.reduce((n, k) => n + rows.get(k).bytes, 0);
  if ((await workspaceBytes(env, ws)) + total > MAX_WORKSPACE_BYTES) {
    throw new HttpError(409, FULL);
  }
  const t = now();
  const out = [];
  for (const k of keys) {
    const obj = await env.MEDIA.get(k);
    if (!obj) throw new HttpError(400, 'One or more images are missing. Upload them again.');
    const r = rows.get(k);
    const key = `${ws}/${randomToken('', 16)}.${k.split('.').pop()}`;
    await env.MEDIA.put(key, await obj.arrayBuffer(), { httpMetadata: { contentType: r.content_type } });
    await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, delete_after)
        VALUES (?, ?, ?, ?, ?, ?)`).bind(key, ws, r.bytes, r.content_type, t, t + KEEP_UNATTACHED).run();
    out.push({ key, url: mediaUrl(env, key) });
  }
  return { media: out };
}

// ---- video -----------------------------------------------------------
//
// Videos go to the library in one request straight to the Worker, not
// through the site's proxy. The page first asks for a ticket (a signed,
// one-hour permission for one key, size and type), then PUTs the file to
// upload_url. The file is streamed into R2, never held in memory.

const VIDEO_TYPES = { 'video/mp4': 'mp4', 'video/quicktime': 'mov' };
const enc = new TextEncoder();
const b64u = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const unb64u = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
const hmacKey = env => crypto.subtle.importKey('raw', enc.encode('upload:' + env.INTERNAL_SECRET),
  { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);

const int = (v, max) => { const n = Number(v); return Number.isInteger(n) && n > 0 && n <= max ? n : null; };

export async function videoTicket(env, w, body, req) {
  const ws = wsOf(w), b = body || {};
  const ext = VIDEO_TYPES[String(b.content_type || '').toLowerCase()];
  if (!ext) throw new HttpError(400, 'Upload MP4 or MOV videos only');
  const bytes = Number(b.bytes);
  if (!Number.isInteger(bytes) || bytes < 1) throw new HttpError(400, 'The video is empty');
  if (bytes > MAX_VIDEO_BYTES) throw new HttpError(400, `Each video must be ${MAX_VIDEO_BYTES / 1024 / 1024} MB or smaller`);
  const folder = b.folder_id ? await getFolder(env, w, b.folder_id) : null;
  if (folder) {
    const { n: inside } = await env.DB.prepare('SELECT COUNT(*) AS n FROM media WHERE folder_id = ? AND in_library = 1').bind(folder.id).first();
    if (inside) throw new HttpError(400, 'A folder holds photos or one video, not both. Make a new folder for this video.');
  }
  const brandId = folder ? folder.brand_id : await brandFor(env, w, b.brand_id);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM media WHERE workspace_id = ? AND in_library = 1').bind(ws).first();
  if (n >= MAX_LIBRARY) throw new HttpError(409, `The library holds up to ${MAX_LIBRARY} items`);
  if ((await workspaceBytes(env, ws)) + bytes > MAX_WORKSPACE_BYTES) throw new HttpError(409, FULL);
  const claims = {
    key: `${ws}/${randomToken('', 16)}.${ext}`, ws, bytes, type: String(b.content_type).toLowerCase(),
    brand: brandId, folder: folder ? folder.id : null, name: String(b.name ?? '').slice(0, 120) || null,
    dur: int(b.duration_ms, 24 * 3600 * 1000), w: int(b.width, 20000), h: int(b.height, 20000),
    exp: now() + UPLOAD_TICKET_TTL,
  };
  const payload = b64u(enc.encode(JSON.stringify(claims)));
  const sig = b64u(new Uint8Array(await crypto.subtle.sign('HMAC', await hmacKey(env), enc.encode(payload))));
  const origin = env.API_ORIGIN || new URL(req.url).origin;
  return { key: claims.key, upload_url: `${origin}/upload/${payload}.${sig}`, expires_at: claims.exp };
}

export const uploadCors = env => ({
  'Access-Control-Allow-Origin': env.PUBLIC_ORIGIN,
  'Access-Control-Allow-Methods': 'PUT, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
  Vary: 'Origin',
});

async function readTicket(env, token) {
  const [payload, sig] = String(token).split('.');
  if (!payload || !sig) return null;
  try {
    if (!await crypto.subtle.verify('HMAC', await hmacKey(env), unb64u(sig), enc.encode(payload))) return null;
    return JSON.parse(new TextDecoder().decode(unb64u(payload)));
  } catch { return null; }
}

const isVideo = head => head.length >= 8 && String.fromCharCode(...head.slice(4, 8)) === 'ftyp';

export async function uploadVideo(env, token, req) {
  const c = await readTicket(env, token);
  if (!c) throw new HttpError(403, 'This upload link is not valid');
  if (c.exp < now()) throw new HttpError(403, 'This upload link has expired. Upload the video again.');
  const declared = Number(req.headers.get('Content-Length') || -1);
  if (declared !== c.bytes) throw new HttpError(400, 'The file size does not match what was announced');
  const contentType = (req.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
  if (contentType !== c.type) throw new HttpError(400, 'The file type does not match what was announced');
  if (await env.DB.prepare('SELECT 1 FROM media WHERE key = ?').bind(c.key).first()) throw new HttpError(409, 'This upload link was already used');
  const ws = await env.DB.prepare('SELECT 1 FROM workspaces WHERE id = ?').bind(c.ws).first();
  if (!ws) throw new HttpError(403, 'This upload link is not valid');
  if ((await workspaceBytes(env, c.ws)) + c.bytes > MAX_WORKSPACE_BYTES) throw new HttpError(409, FULL);

  if (!req.body) throw new HttpError(400, 'The video is empty');
  // A fixed length lets R2 take the stream as it arrives, and fails it if
  // the body runs short or long.
  try {
    await env.MEDIA.put(c.key, req.body.pipeThrough(new FixedLengthStream(c.bytes)), { httpMetadata: { contentType: c.type } });
  } catch {
    await env.MEDIA.delete(c.key).catch(() => {});
    throw new HttpError(400, 'The upload was cut off. Try again.');
  }
  const head = await env.MEDIA.get(c.key, { range: { offset: 0, length: 12 } });
  const first = head ? new Uint8Array(await head.arrayBuffer()) : new Uint8Array();
  const stored = await env.MEDIA.head(c.key);
  if (!isVideo(first) || stored?.size !== c.bytes) {
    await env.MEDIA.delete(c.key);
    throw new HttpError(400, 'That file is not a valid MP4 or MOV video');
  }
  const t = now();
  await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, delete_after,
      in_library, brand_id, name, duration_ms, width, height, folder_id, position) VALUES (?, ?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)`)
    .bind(c.key, c.ws, c.bytes, c.type, t, c.brand, c.name, c.dur, c.w, c.h, c.folder ?? null, c.folder ? 0 : null).run();
  return { key: c.key, url: mediaUrl(env, c.key), bytes: c.bytes, content_type: c.type };
}
