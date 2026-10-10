import { json, HttpError, match, readJson, now } from './http.js';
import { tkFor, TikTokError } from './tiktok.js';
import { oauthIntake, metaIntake, resolveCaller, rotateApiKey, logout } from './auth.js';
import { metaFor, MetaError } from './meta.js';
import { listAccounts, creatorInfoFor, disconnect } from './accounts.js';
import * as L from './limits.js';
import { uploadMedia, serveMedia, copyMedia } from './media.js';
import { createPost, listPosts, cancelPost, retryPost } from './posts.js';
import { tick, publishNow } from './publisher.js';
import { runCleanup, deleteWorkspace } from './cleanup.js';

async function me(req, env, { ws }) {
  const row = await env.DB.prepare('SELECT api_key_hash FROM workspaces WHERE id = ?').bind(ws).first();
  return json({
    workspace_id: ws,
    accounts: await listAccounts(env, ws),
    api_key_set: !!row?.api_key_hash,
    limits: { accounts: L.MAX_ACCOUNTS, queued: L.MAX_QUEUED, images: L.MAX_IMAGES,
              image_bytes: L.MAX_IMAGE_BYTES, workspace_bytes: L.MAX_WORKSPACE_BYTES,
              min_lead_seconds: L.MIN_LEAD_SECONDS, ig_images: L.IG_MAX_IMAGES, ig_caption: L.IG_MAX_CAPTION },
    meta_enabled: !!(env.META_APP_ID && env.META_APP_SECRET),
  });
}

// [method, pattern, handler, access]. Later tasks append to this list.
export const ROUTES = [
  ['POST', '/internal/oauth', async (req, env, { tk }) => json(await oauthIntake(env, tk, await readJson(req))), 'internal'],
  ['POST', '/internal/meta-oauth', async (req, env) => json(await metaIntake(env, metaFor(env), await readJson(req))), 'internal'],
  ['GET', '/v1/me', me, 'user'],
  ['DELETE', '/v1/me', async (req, env, { ws }) => { await deleteWorkspace(env, ws); return json({ ok: true }); }, 'user'],
  ['POST', '/v1/logout', async (req, env) => { await logout(env, req); return json({ ok: true }); }, 'user'],
  ['POST', '/v1/api-key', async (req, env, { ws }) => json({ api_key: await rotateApiKey(env, ws) }), 'user'],
  ['GET', '/v1/accounts', async (req, env, { ws }) => json({ accounts: await listAccounts(env, ws) }), 'user'],
  ['DELETE', '/v1/accounts/:id', async (req, env, { ws, params }) => { await disconnect(env, ws, params.id); return json({ ok: true }); }, 'user'],
  ['GET', '/v1/accounts/:id/creator-info', async (req, env, { ws, params, tk }) => json(await creatorInfoFor(env, tk, ws, params.id)), 'user'],
  ['POST', '/v1/media', async (req, env, { ws }) => json(await uploadMedia(env, ws, req)), 'user'],
  ['POST', '/v1/media/copy', async (req, env, { ws }) => json(await copyMedia(env, ws, (await readJson(req)).keys)), 'user'],
  ['GET', '/media/:ws/:file', async (req, env, { params }) => serveMedia(env, `${params.ws}/${params.file}`), 'public'],
  // TikTok's fetcher, or a CDN in front of it, may check an image with HEAD first.
  ['HEAD', '/media/:ws/:file', async (req, env, { params }) => serveMedia(env, `${params.ws}/${params.file}`, 'HEAD'), 'public'],
  ['POST', '/v1/posts', async (req, env, { ws, tk, ctx }) => {
    const post = await createPost(env, tk, ws, await readJson(req));
    if (post.scheduled_at <= now()) ctx.waitUntil(publishNow(env, tk, post.id).catch(e => console.error('publishNow', e)));
    return json(post);
  }, 'user'],
  ['GET', '/v1/posts', async (req, env, { ws, url }) => {
    const from = Number(url.searchParams.get('from')), to = Number(url.searchParams.get('to'));
    if (!Number.isInteger(from) || !Number.isInteger(to) || to <= from || to - from > 62 * 86400) {
      throw new HttpError(400, 'from and to must be epoch seconds, at most 62 days apart');
    }
    return json({ posts: await listPosts(env, ws, from, to) });
  }, 'user'],
  ['DELETE', '/v1/posts/:id', async (req, env, { ws, params }) => json(await cancelPost(env, ws, params.id)), 'user'],
  ['POST', '/v1/posts/:id/retry', async (req, env, { ws, params }) => json(await retryPost(env, ws, params.id)), 'user'],
];

function sameSecret(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

function toResponse(err) {
  if (err instanceof HttpError) return json({ error: err.message, code: err.code }, err.status);
  if (err instanceof TikTokError || err instanceof MetaError || err?.code === 'needs_reconnect') {
    const reconnect = err.code === 'needs_reconnect';
    return json({ error: err.message, code: err.code }, reconnect ? 409 : 502);
  }
  console.error(err);
  return json({ error: 'Something went wrong on our side' }, 500);
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    try {
      for (const [method, pattern, handler, access] of ROUTES) {
        if (method !== req.method) continue;
        const params = match(pattern, url.pathname);
        if (!params) continue;
        const context = { params, url, tk: tkFor(env), ws: null, ctx };
        if (access === 'internal' && !sameSecret(req.headers.get('X-Internal-Secret') || '', env.INTERNAL_SECRET)) {
          return json({ error: 'forbidden' }, 403);
        }
        if (access === 'user') {
          const caller = await resolveCaller(env, req);
          if (!caller) return json({ error: 'Sign in first' }, 401);
          context.ws = caller.workspaceId;
        }
        return await handler(req, env, context);
      }
      return json({ error: 'Not found' }, 404);
    } catch (err) {
      return toResponse(err);
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      const counts = await tick(env, tkFor(env));
      if (counts.started || counts.published || counts.failed) console.log('tick', JSON.stringify(counts));
      await runCleanup(env);
    })());
  },
};
