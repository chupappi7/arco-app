import { HttpError, json, now } from './http.js';
import { listAccounts } from './accounts.js';
import { listBrands } from './brands.js';
import { listFolders, createFolder, updateFolder, deleteFolder, STATUSES } from './folders.js';
import { addToLibrary } from './library.js';
import { uploadMedia, videoTicket, uploadVideo, photoTicket } from './media.js';
import { getFolder } from './folders.js';
import { getStats, PERIODS } from './stats.js';
import { cancelPost, retryPost } from './posts.js';
import { workspaceInfo, resolveBrand, freeSlots, schedulePlan, undoBatch, editPost, findPosts, when, parseWhen, MAX_PLAN } from './planner.js';
import { MAX_IMAGE_BYTES, MAX_VIDEO_BYTES, IG_MAX_IMAGES, IG_MAX_CAPTION, IG_MAX_HASHTAGS, MIN_LEAD_SECONDS } from './limits.js';
import { wsOf } from './scope.js';

// ARCO Publisher as an MCP server (Streamable HTTP, stateless, JSON replies).
// Signed in with the workspace's API key: Authorization: Bearer apk_…
// Every tool goes through the same functions as the app, so the same checks,
// limits and brand rules apply.

const VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05'];

const INSTRUCTIONS = `ARCO Publisher schedules photo and video posts to TikTok, Instagram and Facebook for one workspace.
How to work:
1. Start with get_overview: brands, their accounts, posting times, brand voice, library folders and free slots.
2. Content lives in library folders. One folder = one post (its photos in order, or one video) plus a note from the person. Use list_folders with status "unused" for "the new ones".
3. Write captions in the brand's voice, using the folder note. Instagram: at most ${IG_MAX_CAPTION} characters and ${IG_MAX_HASHTAGS} hashtags. Use "captions" to vary a caption per platform.
4. Always call schedule_posts with confirm: false first, show the person the plan (time, accounts, caption per post), and only confirm after they agree, unless they told you to go ahead without checking.
5. Times are in the workspace's time zone unless they carry an offset. Leave "at" out to use the brand's next free posting slot.
6. If the workspace has approval on, confirmed posts wait as drafts until a person approves them in Publisher. Say so.
7. Each confirmed run returns a batch_id; undo_batch cancels everything in it that has not been published.
8. Posts made outside Publisher (in the apps, or before an account was connected) are read in with their numbers, so list_posts and get_stats cover whole accounts. They carry imported: true and are read-only: they cannot be edited, cancelled or retried.
9. Files: if they are online, give their links to upload_to_folder. If they are on the person's own computer and you can run commands there, call get_upload_links, then upload each file to its link (one command each, in order). Upload only the files the person named, never others from their computer.`;

const str = (description, extra = {}) => ({ type: 'string', description, ...extra });
const UPLOAD_LINK_TTL = 15 * 60;
const brandArg = str('Brand name or id. "none" means accounts in no brand.');

const TOOLS = [
  {
    name: 'get_overview',
    description: 'Start here. The workspace: time zone, approval mode, each brand with its accounts, posting times, brand voice, library folder counts and next free posting slots.',
    inputSchema: { type: 'object', properties: {} },
    annotations: { readOnlyHint: true },
    run: overview,
  },
  {
    name: 'list_folders',
    description: 'Library folders (one folder = one post) with their photos or video, note, brand and status: unused, awaiting_approval, scheduled or posted.',
    inputSchema: { type: 'object', properties: { brand: brandArg, status: str('Filter by status', { enum: ['all', ...STATUSES] }) } },
    annotations: { readOnlyHint: true },
    run: async (c, a) => {
      const b = await resolveBrand(c.env, c.who, a.brand);
      const folders = await listFolders(c.env, c.who, { brand: b === undefined ? 'all' : b === null ? 'none' : b.id, status: a.status || 'all' });
      const tz = (await workspaceInfo(c.env, wsOf(c.who))).timezone;
      return { folders: folders.map(f => ({ ...f, next: when(f.next_at, tz), posted: when(f.posted_at, tz), next_at: undefined, posted_at: undefined })) };
    },
  },
  {
    name: 'create_folder',
    description: 'Make a library folder for one post, filed under a brand, with an optional note (the brief, an offer, a code, "not before Friday").',
    inputSchema: { type: 'object', required: ['name'], properties: { name: str('Folder name, e.g. "Black Friday promo"'), brand: brandArg, note: str('Brief for the caption') } },
    run: async (c, a) => createFolder(c.env, c.who, { name: a.name, note: a.note, brand_id: await brandId(c, a.brand) }),
  },
  {
    name: 'update_folder',
    description: 'Rename a folder, change its note or brand, or reorder its photos (order: every key, cover first).',
    inputSchema: { type: 'object', required: ['folder_id'], properties: { folder_id: str('Folder id'), name: str('New name'), note: str('New note'),
      brand: brandArg, order: { type: 'array', items: { type: 'string' }, description: 'All item keys in the new order' } } },
    run: async (c, a) => updateFolder(c.env, c.who, a.folder_id, { name: a.name, note: a.note, order: a.order,
      ...(a.brand === undefined ? {} : { brand_id: await brandId(c, a.brand) }) }),
  },
  {
    name: 'delete_folder',
    description: 'Delete a folder. Its photos stay in the library unless remove_items is true.',
    inputSchema: { type: 'object', required: ['folder_id'], properties: { folder_id: str('Folder id'), remove_items: { type: 'boolean' } } },
    annotations: { destructiveHint: true },
    run: (c, a) => deleteFolder(c.env, c.who, a.folder_id, { removeItems: a.remove_items === true }),
  },
  {
    name: 'upload_to_folder',
    description: `Add files to a folder, in order, from public https URLs (or a photo as base64). For files on the person's own computer use get_upload_links instead. Photos: JPG or PNG up to ${MAX_IMAGE_BYTES / 1048576} MB (Instagram needs JPG). Video: one MP4 or MOV per folder, up to ${MAX_VIDEO_BYTES / 1048576} MB, by URL only.`,
    inputSchema: { type: 'object', required: ['folder_id', 'files'], properties: { folder_id: str('Folder id'),
      files: { type: 'array', maxItems: 10, items: { type: 'object', properties: { url: str('https URL of the file'),
        data_base64: str('The photo, base64'), filename: str('File name, e.g. 01.jpg'), content_type: str('image/jpeg, image/png, video/mp4 or video/quicktime') } } } } },
    run: uploadFiles,
  },
  {
    name: 'get_upload_links',
    description: `For files on the person's own computer, when you can run commands there: one-time links that put each file into a folder. Give each file's name, type and exact size in bytes (e.g. from \`stat\`). Each link takes one PUT of exactly that file, works once, and expires in ${UPLOAD_LINK_TTL / 60} minutes; a ready curl command comes with it. Photos: JPG or PNG up to ${MAX_IMAGE_BYTES / 1048576} MB, up to 35 in order. Video: one MP4 or MOV up to ${MAX_VIDEO_BYTES / 1048576} MB, into an empty folder. Only for files the person named.`,
    inputSchema: { type: 'object', required: ['folder_id', 'files'], properties: { folder_id: str('Folder id'),
      files: { type: 'array', minItems: 1, maxItems: 35, items: { type: 'object', required: ['filename', 'content_type', 'bytes'], properties: {
        filename: str('File name, e.g. slide-1.jpg'), content_type: str('image/jpeg, image/png, video/mp4 or video/quicktime'),
        bytes: { type: 'integer', description: 'Exact file size in bytes' } } } } } },
    run: uploadLinks,
  },
  {
    name: 'find_slots',
    description: "The brand's next free posting slots, from its posting times (or the workspace's), skipping times already taken.",
    inputSchema: { type: 'object', properties: { brand: brandArg, count: { type: 'integer', minimum: 1, maximum: 50 }, from: str('Start looking from this time') } },
    annotations: { readOnlyHint: true },
    run: async (c, a) => {
      const b = await resolveBrand(c.env, c.who, a.brand ?? null), info = await workspaceInfo(c.env, wsOf(c.who));
      return freeSlots(c.env, c.who, b, { count: Math.min(50, Math.max(1, a.count || 10)), info,
        from: a.from ? parseWhen(a.from, info.timezone) : now() });
    },
  },
  {
    name: 'schedule_posts',
    description: `Plan and schedule posts. Each post is a folder (or library_keys) going to a brand's accounts at a time. confirm: false (default) checks everything and returns the plan without saving; show it to the person, then call again with confirm: true. Up to ${MAX_PLAN} posts per call.`,
    inputSchema: {
      type: 'object', required: ['posts'],
      properties: {
        confirm: { type: 'boolean', description: 'false = preview only (default). true = make the posts.' },
        posts: { type: 'array', maxItems: MAX_PLAN, items: { type: 'object', required: ['caption'], properties: {
          folder_id: str('Library folder to post'),
          library_keys: { type: 'array', items: { type: 'string' }, description: 'Instead of a folder: library item keys, in order' },
          brand: str("Brand name or id. Default: the folder's brand. Posts go to all of the brand's connected accounts."),
          platforms: { type: 'array', items: { type: 'string', enum: ['tiktok', 'instagram', 'facebook'] }, description: 'Only these platforms' },
          account_ids: { type: 'array', items: { type: 'string' }, description: 'Exactly these accounts instead of the brand' },
          at: str('When, e.g. 2026-11-20T18:00 (workspace time). Leave out for the next free slot.'),
          after: str('With no "at": take the first free slot after this time'),
          caption: str('Caption for every platform'),
          captions: { type: 'object', description: 'Per-platform caption overrides', properties: { tiktok: { type: 'string' }, instagram: { type: 'string' }, facebook: { type: 'string' } } },
          title: str('TikTok title (photo posts), up to 90 characters'),
          tiktok: { type: 'object', description: 'TikTok settings. privacy_level is required when approval is off.', properties: {
            privacy_level: str('Who can view', { enum: ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR', 'SELF_ONLY'] }),
            disable_comment: { type: 'boolean' }, auto_add_music: { type: 'boolean' }, disable_duet: { type: 'boolean' }, disable_stitch: { type: 'boolean' },
            brand_organic: { type: 'boolean', description: 'Promotes your own brand' }, branded_content: { type: 'boolean', description: 'Paid partnership' } } },
        } } },
      },
    },
    run: (c, a) => schedulePlan(c.env, c.tk, c.who, a),
  },
  {
    name: 'list_posts',
    description: 'Posts in a time window (default: the last 7 days and the next 21), with status (awaiting_approval, queued, publishing, published, failed), caption, folder, batch and numbers. Posts made outside Publisher have imported: true and are read-only.',
    inputSchema: { type: 'object', properties: { brand: brandArg, from: str('From'), to: str('To'),
      status: str('Only this status', { enum: ['all', 'draft', 'queued', 'publishing', 'published', 'failed'] }) } },
    annotations: { readOnlyHint: true },
    run: (c, a) => findPosts(c.env, c.who, a),
  },
  {
    name: 'update_post',
    description: 'Change the caption, title or time of a post that has not started publishing.',
    inputSchema: { type: 'object', required: ['post_id'], properties: { post_id: str('Post id'), caption: str('New caption'), title: str('New title'), at: str('New time') } },
    run: (c, a) => editPost(c.env, c.who, a.post_id, a),
  },
  {
    name: 'cancel_post',
    description: 'Cancel a post that has not started publishing (a draft is deleted).',
    inputSchema: { type: 'object', required: ['post_id'], properties: { post_id: str('Post id') } },
    annotations: { destructiveHint: true },
    run: (c, a) => cancelPost(c.env, c.who, a.post_id),
  },
  {
    name: 'undo_batch',
    description: 'Cancel every post of one schedule_posts run that has not been published yet.',
    inputSchema: { type: 'object', required: ['batch_id'], properties: { batch_id: str('The batch_id schedule_posts returned') } },
    annotations: { destructiveHint: true },
    run: (c, a) => undoBatch(c.env, c.who, a.batch_id),
  },
  {
    name: 'retry_post',
    description: 'Try a failed post again.',
    inputSchema: { type: 'object', required: ['post_id'], properties: { post_id: str('Post id') } },
    run: (c, a) => retryPost(c.env, c.who, a.post_id),
  },
  {
    name: 'get_stats',
    description: 'Results for a period: totals against the previous period, per platform, followers per account, and the top posts. Use it to see what works.',
    inputSchema: { type: 'object', properties: { brand: brandArg, days: { type: 'integer', enum: PERIODS },
      platform: str('Platform', { enum: ['all', 'tiktok', 'instagram', 'facebook'] }) } },
    annotations: { readOnlyHint: true },
    run: async (c, a) => {
      const b = await resolveBrand(c.env, c.who, a.brand);
      const st = await getStats(c.env, c.who, a.days || 30, undefined, a.platform || 'all', b === undefined ? 'all' : b === null ? 'none' : b.id);
      return { days: st.days, published: st.published, tracked: st.tracked, totals: st.totals, previous: st.previous, followers: st.followers,
        by_platform: st.by_platform, accounts: st.accounts,
        imported: st.imported,
        top: (st.top || []).map(p => ({ post_id: p.id, platform: p.platform, username: p.username, at: p.scheduled_at, caption: p.caption, stats: p.stats, post_url: p.post_url, imported: p.imported })) };
    },
  },
];

async function brandId(c, ref) {
  const b = await resolveBrand(c.env, c.who, ref);
  return b ? b.id : null;
}

async function overview(c) {
  const { env, who } = c, info = await workspaceInfo(env, wsOf(who));
  const [brands, accounts, folders] = await Promise.all([listBrands(env, who), listAccounts(env, who), listFolders(env, who)]);
  const acct = a => ({ id: a.id, platform: a.platform, handle: `${a.platform === 'facebook' ? '' : '@'}${a.username || a.display_name}`, needs_reconnect: a.needs_reconnect });
  const lib = id => { const mine = folders.filter(f => (f.brand_id || null) === id), n = s => mine.filter(f => f.status === s).length;
    return { folders: mine.length, unused: n('unused'), awaiting_approval: n('awaiting_approval'), scheduled: n('scheduled'), posted: n('posted') }; };
  const out = [];
  for (const b of brands) {
    out.push({ id: b.id, name: b.name, voice: b.voice || null, posting_times: b.slots || info.slots || null,
      accounts: accounts.filter(a => a.brand_id === b.id).map(acct), library: lib(b.id),
      next_free_slots: (await freeSlots(env, who, b, { count: 3, info })).slots });
  }
  const loose = accounts.filter(a => !brands.some(b => b.id === a.brand_id));
  return {
    workspace: info.name, timezone: info.timezone, timezone_set: info.timezone_set, now: when(now(), info.timezone),
    approval: info.review ? 'on: confirmed posts wait as drafts until a person approves them in Publisher' : 'off: confirmed posts are scheduled directly',
    brands: out,
    ...(loose.length || !brands.length ? { not_in_a_brand: { accounts: loose.map(acct), library: lib(null), posting_times: info.slots,
      next_free_slots: (await freeSlots(env, who, null, { count: 3, info })).slots } } : {}),
    rules: {
      min_lead_minutes: MIN_LEAD_SECONDS / 60,
      instagram: `JPG photos only, at most ${IG_MAX_IMAGES} per post, captions up to ${IG_MAX_CAPTION} characters and ${IG_MAX_HASHTAGS} hashtags; videos post as Reels (3 s to 15 min)`,
      tiktok: 'Photo posts up to 35 photos with an optional title (90 characters); videos up to the account limit. Privacy is chosen per post.',
      facebook: 'Page posts, photos or one video.',
      folders: 'One folder = one post: photos in order (cover first) or one video.',
    },
  };
}

const EXT = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', mp4: 'video/mp4', mov: 'video/quicktime' };
const typeOf = (f, header) => {
  const h = String(header || '').split(';')[0].trim().toLowerCase().replace('image/jpg', 'image/jpeg');
  if (EXT[Object.keys(EXT).find(k => EXT[k] === h)]) return h;
  const ext = String(f.filename || f.url || '').split('?')[0].split('.').pop().toLowerCase();
  return String(f.content_type || '').toLowerCase().replace('image/jpg', 'image/jpeg') || EXT[ext] || h;
};

// Only public https hosts by name: no IP literals, no local or internal
// names, and every redirect is checked the same way (at most 3).
const blockedHost = h => {
  h = h.toLowerCase().replace(/\.$/, '');
  return !h.includes('.') || /^[\d.]+$/.test(h) || h.startsWith('[') || h.includes(':')
    || /(^|\.)(localhost|local|internal|intranet|lan|home|corp|arpa)$/.test(h);
};
export async function fetchPublic(url, hops = 3) {
  let u;
  try { u = new URL(url); } catch { throw new HttpError(400, 'That is not a valid URL'); }
  if (u.protocol !== 'https:') throw new HttpError(400, 'Only https URLs');
  if (u.username || u.password || blockedHost(u.hostname)) throw new HttpError(400, 'That URL host is not allowed');
  const res = await fetch(u.toString(), { redirect: 'manual' });
  if (res.status >= 300 && res.status < 400 && res.headers.get('Location')) {
    if (!hops) throw new HttpError(400, 'Too many redirects');
    return fetchPublic(new URL(res.headers.get('Location'), u).toString(), hops - 1);
  }
  return res;
}

// Links, not bytes: the file goes from the person's computer straight to
// storage, and each link allows only that one file, once, briefly.
const shq = s => `'${String(s).replace(/'/g, `'\\''`)}'`;
async function uploadLinks(c, a) {
  const { env, who } = c, files = a.files;
  if (!Array.isArray(files) || !files.length || files.length > 35) throw new HttpError(400, 'files must be a list of 1 to 35 files');
  const folder = await getFolder(env, who, a.folder_id);
  const videos = files.filter(f => String(f.content_type || '').toLowerCase().startsWith('video/'));
  if (videos.length && files.length > 1) throw new HttpError(400, 'A folder holds photos or one video, not both: ask for one video on its own');
  const { p } = await env.DB.prepare('SELECT MAX(position) AS p FROM media WHERE folder_id = ? AND in_library = 1').bind(folder.id).first();
  const req = new Request(env.API_ORIGIN || 'https://api.internal/');
  const out = [];
  for (const [i, f] of files.entries()) {
    const name = String(f.filename || `file-${i + 1}`).split('/').pop().slice(0, 120);
    const type = String(f.content_type || '').toLowerCase();
    try {
      const t = type.startsWith('video/')
        ? await videoTicket(env, who, { content_type: type, bytes: f.bytes, name, folder_id: folder.id }, req, { ttl: UPLOAD_LINK_TTL })
        : await photoTicket(env, who, { content_type: type, bytes: f.bytes, name, folder_id: folder.id }, req, { ttl: UPLOAD_LINK_TTL, position: (p ?? -1) + 1 + i });
      out.push({ filename: name, ok: true, method: 'PUT', content_type: type, bytes: f.bytes, upload_url: t.upload_url, expires_at: t.expires_at,
        curl: `curl -sS --fail-with-body -T <path to ${name}> -H ${shq(`Content-Type: ${type}`)} ${shq(t.upload_url)}` });
    } catch (e) { out.push({ filename: name, ok: false, error: e.message }); }
  }
  return { folder: { id: folder.id, name: folder.name }, links: out,
    next: 'PUT each file to its link with its exact Content-Type (curl -T sends the right length). Then list_folders shows them in the folder, and schedule_posts can post it.' };
}

async function uploadFiles(c, a) {
  const { env, who } = c, files = a.files;
  if (!Array.isArray(files) || !files.length || files.length > 10) throw new HttpError(400, 'files must be a list of 1 to 10 files');
  const out = [];
  for (const [i, f] of files.entries()) {
    const name = String(f.filename || (f.url ? f.url.split('?')[0].split('/').pop() : `file-${i + 1}`)).slice(0, 120);
    try {
      let bytes, type;
      if (f.data_base64) {
        type = typeOf(f, f.content_type);
        if (!type.startsWith('image/')) throw new HttpError(400, 'Send videos by URL, not base64');
        const bin = atob(String(f.data_base64).replace(/^data:[^,]*,/, '').replace(/\s/g, ''));
        bytes = Uint8Array.from(bin, ch => ch.charCodeAt(0));
      } else if (f.url) {
        const res = await fetchPublic(String(f.url));
        if (!res.ok) throw new HttpError(400, `Fetching it failed (${res.status})`);
        type = typeOf(f, res.headers.get('Content-Type'));
        if (type.startsWith('video/')) {
          const size = Number(res.headers.get('Content-Length') || 0);
          if (!size) throw new HttpError(400, 'The video URL must send a Content-Length');
          const t = await videoTicket(env, who, { content_type: type, bytes: size, name, folder_id: a.folder_id }, new Request('https://api.internal/'));
          const token = t.upload_url.split('/upload/')[1];
          const v = await uploadVideo(env, token, new Request('https://api.internal/upload', { method: 'PUT', body: res.body,
            headers: { 'Content-Type': type, 'Content-Length': String(size) }, duplex: 'half' }));
          out.push({ name, key: v.key, kind: 'video', ok: true });
          continue;
        }
        bytes = new Uint8Array(await res.arrayBuffer());
      } else throw new HttpError(400, 'Give url or data_base64');
      // The bytes decide, not the name: a PNG called .jpg is still a PNG.
      if (bytes[0] === 0xff && bytes[1] === 0xd8) type = 'image/jpeg';
      else if (bytes[0] === 0x89 && bytes[1] === 0x50) type = 'image/png';
      if (!['image/jpeg', 'image/png'].includes(type)) throw new HttpError(400, 'Photos must be JPG or PNG; videos MP4 or MOV');
      const m = await uploadMedia(env, wsOf(who), new Request('https://api.internal/', { method: 'POST', body: bytes, headers: { 'Content-Type': type } }));
      await addToLibrary(env, who, { keys: [m.key], folder_id: a.folder_id, names: { [m.key]: name } });
      out.push({ name, key: m.key, kind: 'photo', ok: true });
    } catch (e) {
      out.push({ name, ok: false, error: e.message });
    }
  }
  const [folder] = await listFolders(env, who, { id: a.folder_id });
  return { uploaded: out.filter(x => x.ok).length, failed: out.filter(x => !x.ok).length, files: out,
    folder: folder && { id: folder.id, name: folder.name, kind: folder.kind, items: folder.items.length } };
}

// ---- JSON-RPC ---------------------------------------------------------------------

const rpcError = (id, code, message) => ({ jsonrpc: '2.0', id: id ?? null, error: { code, message } });
const listed = TOOLS.map(({ name, description, inputSchema, annotations }) => ({ name, description, inputSchema, ...(annotations ? { annotations } : {}) }));

async function handle(msg, c) {
  if (!msg || msg.jsonrpc !== '2.0' || typeof msg.method !== 'string') return rpcError(msg?.id, -32600, 'Invalid request');
  const { id, method, params = {} } = msg;
  if (id === undefined) return null; // a notification: nothing to answer
  switch (method) {
    case 'initialize':
      return { jsonrpc: '2.0', id, result: {
        protocolVersion: VERSIONS.includes(params.protocolVersion) ? params.protocolVersion : VERSIONS[0],
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: 'arco-publisher', title: 'ARCO Publisher', version: '1.0.0' },
        instructions: INSTRUCTIONS } };
    case 'ping': return { jsonrpc: '2.0', id, result: {} };
    case 'tools/list': return { jsonrpc: '2.0', id, result: { tools: listed } };
    case 'tools/call': {
      const tool = TOOLS.find(t => t.name === params.name);
      if (!tool) return rpcError(id, -32602, `Unknown tool: ${params.name}`);
      try {
        const out = await tool.run(c, params.arguments || {});
        return { jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: JSON.stringify(out) }] } };
      } catch (e) {
        if (!(e instanceof HttpError) && !e?.code) console.error('mcp', params.name, e);
        const message = e instanceof HttpError || e?.code ? e.message : 'Something went wrong on our side';
        return { jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: message }], isError: true } };
      }
    }
    default: return rpcError(id, -32601, `Method not found: ${method}`);
  }
}

export async function mcp(req, env, { who, tk }) {
  let body;
  try { body = await req.json(); } catch { return json(rpcError(null, -32700, 'Parse error'), 400); }
  const c = { env, who, tk };
  if (Array.isArray(body)) {
    const out = (await Promise.all(body.map(m => handle(m, c)))).filter(Boolean);
    return out.length ? json(out) : new Response(null, { status: 202 });
  }
  const out = await handle(body, c);
  return out ? json(out) : new Response(null, { status: 202 });
}
