import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { MAX_IMAGE_BYTES, MAX_WORKSPACE_BYTES, KEEP_UNATTACHED } from './limits.js';

const TYPES = {
  'image/jpeg': { ext: 'jpg', magic: [0xff, 0xd8, 0xff] },
  'image/png': { ext: 'png', magic: [0x89, 0x50, 0x4e, 0x47] },
};

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
    throw new HttpError(409, 'Storage is full (200 MB). Images are freed 7 days after their post is done.');
  }

  const key = `${ws}/${randomToken('', 16)}.${type.ext}`;
  await env.MEDIA.put(key, bytes, { httpMetadata: { contentType } });
  const t = now();
  await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, delete_after)
      VALUES (?, ?, ?, ?, ?, ?)`).bind(key, ws, bytes.length, contentType, t, t + KEEP_UNATTACHED).run();
  return { key, url: mediaUrl(env, key), bytes: bytes.length, content_type: contentType };
}

export async function serveMedia(env, key, method = 'GET') {
  const obj = method === 'HEAD' ? await env.MEDIA.head(key) : await env.MEDIA.get(key);
  if (!obj) return new Response(null, { status: 404 });
  return new Response(method === 'HEAD' ? null : obj.body, {
    headers: {
      'Content-Type': obj.httpMetadata?.contentType || 'application/octet-stream',
      'Content-Length': String(obj.size),
      'Cache-Control': 'public, max-age=3600',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}

// One upload, several posts: each post owns its images (that is what lets a
// finished post free its storage on its own clock), so posting the same
// photos to TikTok, Instagram and Facebook copies them once per extra post.
export async function copyMedia(env, ws, keys) {
  if (!Array.isArray(keys) || !keys.length || keys.length > 35 || !keys.every(k => typeof k === 'string')) {
    throw new HttpError(400, 'keys must be a list of up to 35 image keys');
  }
  const marks = keys.map(() => '?').join(',');
  const { results } = await env.DB.prepare(`SELECT key, bytes, content_type FROM media
      WHERE workspace_id = ? AND key IN (${marks})`).bind(ws, ...keys).all();
  const rows = new Map(results.map(r => [r.key, r]));
  if (rows.size !== new Set(keys).size) throw new HttpError(400, 'One or more images are missing. Upload them again.');
  const total = keys.reduce((n, k) => n + rows.get(k).bytes, 0);
  if ((await workspaceBytes(env, ws)) + total > MAX_WORKSPACE_BYTES) {
    throw new HttpError(409, 'Storage is full (200 MB). Images are freed 7 days after their post is done.');
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
