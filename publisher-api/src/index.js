import { json, HttpError, match, readJson, now } from './http.js';
import { tkFor, TikTokError } from './tiktok.js';
import { oauthIntake, metaIntake, igIntake, rotateApiKey, logout } from './auth.js';
import { startEmail, verifyEmail, callerFor, need, myWorkspaces, switchWorkspace, addWorkspace, updateWorkspace,
  logoutEverywhere, transferOwnership, listMembers, invite, cancelInvite, acceptInvite, updateMember, removeMember } from './users.js';
import { metaFor, MetaError } from './meta.js';
import { listAccounts, creatorInfoFor, disconnect, refreshInstagramTokens } from './accounts.js';
import * as L from './limits.js';
import { uploadMedia, serveMedia, copyMedia } from './media.js';
import { createPost, listPosts, cancelPost, retryPost, listDrafts, updatePost } from './posts.js';
import { tick, publishNow } from './publisher.js';
import { notifyFailures } from './notify.js';
import { writeCaptions, aiUsage } from './ai.js';
import { runCleanup, deleteWorkspace } from './cleanup.js';
import { refreshStats, getStats, STATS_PER_TICK } from './stats.js';
import { listBrands, createBrand, renameBrand, deleteBrand, assign } from './brands.js';

async function me(req, env, { who }) {
  const ws = who.ws;
  const row = await env.DB.prepare('SELECT name, timezone, slots, api_key_hash FROM workspaces WHERE id = ?').bind(ws).first();
  const user = who.userId ? await env.DB.prepare('SELECT email FROM users WHERE id = ?').bind(who.userId).first() : null;
  return json({
    user: user ? { id: who.userId, email: user.email } : null,
    // A workspace from before email sign-in: the page asks for an email.
    needs_email: who.via === 'legacy',
    workspace: { id: ws, name: row?.name || 'My workspace', timezone: row?.timezone || null, slots: row?.slots ? JSON.parse(row.slots) : null, role: who.role, brand_scope: who.scope },
    workspaces: await myWorkspaces(env, who.userId),
    workspace_id: ws,
    accounts: await listAccounts(env, who),
    brands: await listBrands(env, who),
    api_key_set: !!row?.api_key_hash,
    limits: { accounts: L.MAX_ACCOUNTS, queued: L.MAX_QUEUED, images: L.MAX_IMAGES,
              image_bytes: L.MAX_IMAGE_BYTES, workspace_bytes: L.MAX_WORKSPACE_BYTES,
              min_lead_seconds: L.MIN_LEAD_SECONDS, ig_images: L.IG_MAX_IMAGES, ig_caption: L.IG_MAX_CAPTION },
    facebook_enabled: !!(env.META_APP_ID && env.META_APP_SECRET),
    instagram_enabled: !!(env.IG_APP_ID && env.IG_APP_SECRET),
    ai_enabled: !!(env.ANTHROPIC_API_KEY || env.__ai),
  });
}

const body = req => readJson(req);

// [method, pattern, handler, access]. access is 'public', 'internal', or the
// lowest role allowed: 'member', 'admin', 'owner'. Handlers get `who`
// ({ ws, userId, role, scope }) and pass it, not a bare workspace id, to
// anything that reads accounts or posts, so brand limits apply everywhere.
export const ROUTES = [
  ['POST', '/internal/oauth', async (req, env, { tk }) => json(await oauthIntake(env, tk, await body(req))), 'internal'],
  ['POST', '/internal/meta-oauth', async (req, env) => json(await metaIntake(env, metaFor(env), await body(req))), 'internal'],
  ['POST', '/internal/ig-oauth', async (req, env) => json(await igIntake(env, metaFor(env), await body(req))), 'internal'],
  ['POST', '/internal/email-verify', async (req, env) => json(await verifyEmail(env, await body(req))), 'internal'],
  ['POST', '/v1/auth/email/start', async (req, env) => json(await startEmail(env, await body(req))), 'public'],

  ['GET', '/v1/me', me, 'member'],
  ['DELETE', '/v1/me', async (req, env, { who }) => { await deleteWorkspace(env, who.ws); return json({ ok: true }); }, 'owner'],
  ['POST', '/v1/logout', async (req, env) => { await logout(env, req); return json({ ok: true }); }, 'member'],
  ['POST', '/v1/logout-all', async (req, env, { who }) => json(await logoutEverywhere(env, who)), 'member'],
  ['POST', '/v1/api-key', async (req, env, { who }) => json({ api_key: await rotateApiKey(env, who.ws) }), 'owner'],

  ['POST', '/v1/workspaces', async (req, env, { who }) => json(await addWorkspace(env, who, await body(req))), 'member'],
  ['POST', '/v1/session/workspace', async (req, env, { who }) => json(await switchWorkspace(env, who, await body(req))), 'member'],
  ['PATCH', '/v1/workspace', async (req, env, { who }) => json(await updateWorkspace(env, who, await body(req))), 'admin'],
  ['POST', '/v1/workspace/transfer', async (req, env, { who }) => json(await transferOwnership(env, who, await body(req))), 'owner'],
  ['GET', '/v1/members', async (req, env, { who }) => json(await listMembers(env, who)), 'admin'],
  ['POST', '/v1/invites', async (req, env, { who }) => json(await invite(env, who, await body(req))), 'admin'],
  ['DELETE', '/v1/invites/:id', async (req, env, { who, params }) => json(await cancelInvite(env, who, params.id)), 'admin'],
  ['POST', '/v1/invites/accept', async (req, env, { who }) => json(await acceptInvite(env, who, await body(req))), 'member'],
  ['PATCH', '/v1/members/:id', async (req, env, { who, params }) => json(await updateMember(env, who, params.id, await body(req))), 'admin'],
  ['DELETE', '/v1/members/:id', async (req, env, { who, params }) => json(await removeMember(env, who, params.id)), 'member'],

  ['GET', '/v1/accounts', async (req, env, { who }) => json({ accounts: await listAccounts(env, who) }), 'member'],
  ['DELETE', '/v1/accounts/:id', async (req, env, { who, params }) => { await disconnect(env, who, params.id); return json({ ok: true }); }, 'admin'],
  ['PATCH', '/v1/accounts/:id', async (req, env, { who, params }) =>
    json(await assign(env, who.ws, [params.id], (await body(req)).brand_id ?? null)), 'admin'],
  ['GET', '/v1/accounts/:id/creator-info', async (req, env, { who, params, tk }) => json(await creatorInfoFor(env, tk, who, params.id)), 'member'],
  ['GET', '/v1/brands', async (req, env, { who }) => json({ brands: await listBrands(env, who) }), 'member'],
  ['POST', '/v1/brands', async (req, env, { who }) => json(await createBrand(env, who.ws, await body(req))), 'admin'],
  ['PATCH', '/v1/brands/:id', async (req, env, { who, params }) => json(await renameBrand(env, who.ws, params.id, await body(req))), 'admin'],
  ['DELETE', '/v1/brands/:id', async (req, env, { who, params }) => json(await deleteBrand(env, who.ws, params.id)), 'admin'],
  ['POST', '/v1/brands/:id/accounts', async (req, env, { who, params }) =>
    json(await assign(env, who.ws, (await body(req)).account_ids, params.id)), 'admin'],

  ['POST', '/v1/media', async (req, env, { who }) => json(await uploadMedia(env, who.ws, req)), 'member'],
  ['POST', '/v1/media/copy', async (req, env, { who }) => json(await copyMedia(env, who, (await body(req)).keys)), 'member'],
  ['GET', '/media/:ws/:file', async (req, env, { params }) => serveMedia(env, `${params.ws}/${params.file}`), 'public'],
  // TikTok's fetcher, or a CDN in front of it, may check an image with HEAD first.
  ['HEAD', '/media/:ws/:file', async (req, env, { params }) => serveMedia(env, `${params.ws}/${params.file}`, 'HEAD'), 'public'],
  ['POST', '/v1/posts', async (req, env, { who, tk, ctx }) => {
    const post = await createPost(env, tk, who, await body(req));
    if (post.status === 'queued' && post.scheduled_at <= now()) {
      ctx.waitUntil(publishNow(env, tk, post.id).then(() => notifyFailures(env)).catch(e => console.error('publishNow', e)));
    }
    return json(post);
  }, 'member'],
  ['GET', '/v1/posts', async (req, env, { who, url }) => {
    const from = Number(url.searchParams.get('from')), to = Number(url.searchParams.get('to'));
    if (!Number.isInteger(from) || !Number.isInteger(to) || to <= from || to - from > 62 * 86400) {
      throw new HttpError(400, 'from and to must be epoch seconds, at most 62 days apart');
    }
    return json({ posts: await listPosts(env, who, from, to) });
  }, 'member'],
  ['GET', '/v1/stats', async (req, env, { who, url }) => json(await getStats(env, who, Number(url.searchParams.get('days') || 7),
    undefined, url.searchParams.get('platform') || 'all')), 'member'],
  ['POST', '/v1/ai/captions', async (req, env, { who }) => json(await writeCaptions(env, who, await body(req))), 'member'],
  ['GET', '/v1/ai/usage', async (req, env, { who }) => json(await aiUsage(env, who)), 'member'],
  ['GET', '/v1/drafts', async (req, env, { who }) => json({ drafts: await listDrafts(env, who) }), 'member'],
  ['PATCH', '/v1/posts/:id', async (req, env, { who, params }) => json(await updatePost(env, who, params.id, await body(req))), 'member'],
  ['DELETE', '/v1/posts/:id', async (req, env, { who, params }) => json(await cancelPost(env, who, params.id)), 'member'],
  ['POST', '/v1/posts/:id/retry', async (req, env, { who, params }) => json(await retryPost(env, who, params.id)), 'member'],
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
        const context = { params, url, tk: tkFor(env), who: null, ctx };
        if (access === 'internal' && !sameSecret(req.headers.get('X-Internal-Secret') || '', env.INTERNAL_SECRET)) {
          return json({ error: 'forbidden' }, 403);
        }
        if (access !== 'public' && access !== 'internal') {
          const who = await callerFor(env, req);
          if (!who) return json({ error: 'Sign in first' }, 401);
          need(who, access);
          context.who = who;
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
      const tk = tkFor(env);
      const counts = await tick(env, tk);
      if (counts.started || counts.published || counts.failed) console.log('tick', JSON.stringify(counts));
      await notifyFailures(env).catch(e => console.error('notify', e));
      await refreshInstagramTokens(env, metaFor(env)).catch(e => console.error('ig refresh', e));
      // Stats use only what publishing left of the per-run call allowance.
      const spare = L.TICK_FETCH_BUDGET - counts.calls - 3;
      await refreshStats(env, metaFor(env), tk, now(), Math.min(STATS_PER_TICK, spare)).catch(e => console.error('stats', e));
      await runCleanup(env);
    })());
  },
};
