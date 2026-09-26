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
