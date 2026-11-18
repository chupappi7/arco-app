import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { MIN_LEAD_SECONDS, MAX_QUEUED, IG_MAX_IMAGES } from './limits.js';
import { wsOf, inScope } from './scope.js';
import { listAccounts, getAccount, accessTokenFor, isMeta } from './accounts.js';
import { listBrands } from './brands.js';
import { parseSlots } from './slots.js';
import { listFolders } from './folders.js';
import { copyMedia, mediaUrl } from './media.js';
import { createPost, cancelPost, updatePost, validatePost, checkLength, loadPost, postJson, refuseImported } from './posts.js';

// Scheduling by plan: what an AI agent (or any API client) uses to turn
// library folders into posts. A plan is checked in full and shown first
// (confirm: false); confirming it makes every post in one batch, which can
// be undone as one. While the workspace has ai_review on, the posts wait as
// drafts at their planned time until a person approves them.

const bad = msg => { throw new HttpError(400, msg); };
const PLATFORMS = ['tiktok', 'instagram', 'facebook'];
export const MAX_PLAN = 30;

// ---- time, in the workspace's zone ------------------------------------------

function parts(ms, tz) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit',
    day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).formatToParts(new Date(ms)).map(x => [x.type, x.value]));
  return { y: +p.year, m: +p.month, d: +p.day, h: +p.hour, mi: +p.minute, s: +p.second };
}
const offsetMin = (ms, tz) => { const p = parts(ms, tz); return (Date.UTC(p.y, p.m - 1, p.d, p.h, p.mi, p.s) - Math.floor(ms / 1000) * 1000) / 60000; };

// Wall-clock time in a zone -> epoch seconds (two passes settle DST edges).
export function zonedToEpoch(y, m, d, h, mi, tz) {
  const guess = Date.UTC(y, m - 1, d, h, mi);
  let t = guess - offsetMin(guess, tz) * 60000;
  t = guess - offsetMin(t, tz) * 60000;
  return Math.floor(t / 1000);
}

const pad = n => String(n).padStart(2, '0');
export function localIso(sec, tz) {
  const p = parts(sec * 1000, tz), off = offsetMin(sec * 1000, tz), a = Math.abs(off);
  return `${p.y}-${pad(p.m)}-${pad(p.d)}T${pad(p.h)}:${pad(p.mi)}${off < 0 ? '-' : '+'}${pad(Math.floor(a / 60))}:${pad(a % 60)}`;
}
const weekday = (sec, tz) => new Intl.DateTimeFormat('en-US', { timeZone: tz, weekday: 'long' }).format(new Date(sec * 1000));
export const when = (sec, tz) => (sec == null ? null : { at: sec, local: localIso(sec, tz), weekday: weekday(sec, tz) });

// "2026-11-20T18:00" is read in the workspace's zone; with Z or an offset it
// means exactly that instant; a number is epoch seconds.
export function parseWhen(v, tz) {
  if (typeof v === 'number' && Number.isInteger(v)) return v;
  const s = String(v ?? '').trim();
  if (/^\d{9,10}$/.test(s)) return Number(s);
  if (/(Z|[+-]\d\d:?\d\d)$/i.test(s)) {
    const t = Date.parse(s);
    if (Number.isNaN(t)) bad(`Can't read the time "${s}". Use 2026-11-20T18:00`);
    return Math.floor(t / 1000);
  }
  const m = s.match(/^(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d)(?::\d\d)?$/);
  if (!m) bad(`Can't read the time "${s}". Use 2026-11-20T18:00 (workspace time)`);
  return zonedToEpoch(+m[1], +m[2], +m[3], +m[4], +m[5], tz);
}

export async function workspaceInfo(env, ws) {
  const row = await env.DB.prepare('SELECT name, timezone, slots, ai_review FROM workspaces WHERE id = ?').bind(ws).first();
  return { name: row?.name || 'My workspace', timezone: row?.timezone || 'UTC', timezone_set: !!row?.timezone,
    slots: parseSlots(row?.slots), review: row ? !!row.ai_review : true };
}

// A brand by id or by name (any case); 'none' or null means accounts in no brand.
export async function resolveBrand(env, w, ref) {
  if (ref === undefined) return undefined;
  if (ref === null || ref === 'none' || ref === '') return null;
  const brands = await listBrands(env, w), r = String(ref).trim().toLowerCase();
  const b = brands.find(x => x.id === ref) || brands.find(x => x.name.toLowerCase() === r);
  if (!b) throw new HttpError(404, `No brand called "${ref}". Brands: ${brands.map(x => x.name).join(', ') || 'none yet'}`);
  return b;
}

// ---- free posting slots -------------------------------------------------------

// The brand's posting times (or the workspace's), from `from` on, minus the
// times its accounts already have a post (or an approval-waiting draft) at.
export async function freeSlots(env, w, brand, { count = 10, from = now(), days = 28, taken = new Set(), info } = {}) {
  info ||= await workspaceInfo(env, wsOf(w));
  const tz = info.timezone, slots = brand?.slots || info.slots;
  if (!slots) return { timezone: tz, slots: [], reason: 'No posting times are set for this brand or the workspace. Set them in Publisher, or give each post a time.' };
  const ids = (await listAccounts(env, w)).filter(a => (brand ? a.brand_id === brand.id : !a.brand_id)).map(a => a.id);
  let busy = [];
  if (ids.length) {
    const { results } = await env.DB.prepare(`SELECT scheduled_at FROM posts WHERE workspace_id = ? AND status IN ('queued', 'publishing', 'draft')
        AND scheduled_at >= ? AND account_id IN (${ids.map(() => '?').join(',')})`).bind(wsOf(w), from - 60, ...ids).all();
    busy = results.map(r => r.scheduled_at);
  }
  const earliest = Math.max(from, now() + MIN_LEAD_SECONDS + 60), out = [];
  for (let i = 0; i <= days && out.length < count; i++) {
    const p = parts((from + i * 86400) * 1000, tz);
    if (!slots.days.includes(new Date(Date.UTC(p.y, p.m - 1, p.d)).getUTCDay())) continue;
    for (const hm of slots.times) {
      const [h, mi] = hm.split(':').map(Number), at = zonedToEpoch(p.y, p.m, p.d, h, mi, tz);
      if (at < earliest || out.some(x => x.at === at) || taken.has(`${brand?.id || 'none'}:${at}`)) continue;
      if (busy.some(b => Math.abs(b - at) < 60)) continue;
      out.push(when(at, tz));
      if (out.length >= count) break;
    }
  }
  return { timezone: tz, posting_times: slots, slots: out };
}

// ---- plans --------------------------------------------------------------------

const handle = a => `${a.platform === 'facebook' ? '' : '@'}${a.username || a.display_name}`;

async function libraryItems(env, w, keys) {
  if (!Array.isArray(keys) || !keys.length || keys.length > 35 || !keys.every(k => typeof k === 'string')) bad('library_keys must be a list of 1 to 35 library keys');
  const sc = inScope(w, 'brand_id'), marks = keys.map(() => '?').join(',');
  const { results } = await env.DB.prepare(`SELECT key, content_type, duration_ms, brand_id FROM media WHERE workspace_id = ? AND in_library = 1
      AND key IN (${marks})${sc.sql}`).bind(wsOf(w), ...keys, ...sc.binds).all();
  if (results.length !== new Set(keys).size) throw new HttpError(404, 'One or more library_keys are not in the library');
  return keys.map(k => results.find(r => r.key === k)).map(r => ({ key: r.key, kind: r.content_type.startsWith('video/') ? 'video' : 'photo',
    content_type: r.content_type, duration_ms: r.duration_ms, brand_id: r.brand_id }));
}

// Turns one plan entry into its posts (one per account), checked, nothing saved.
async function draftEntry(env, w, item, n, ctx) {
  const { info, accounts, taken } = ctx, tz = info.timezone, errors = [];
  const fail = msg => ({ index: n, ok: false, errors: [msg] });
  if (!item || typeof item !== 'object') return fail('Each post must be an object');

  let folder = null, media;
  try {
    if (item.folder_id) {
      folder = (await listFolders(env, w, { id: item.folder_id }))[0];
      if (!folder) throw new HttpError(404, `Folder ${item.folder_id} not found`);
      const { results } = await env.DB.prepare(`SELECT key, content_type, duration_ms FROM media WHERE folder_id = ? AND in_library = 1
          ORDER BY position, created_at, key`).bind(folder.id).all();
      media = results.map(r => ({ key: r.key, kind: r.content_type.startsWith('video/') ? 'video' : 'photo', content_type: r.content_type, duration_ms: r.duration_ms }));
      if (!media.length) return fail(`Folder "${folder.name}" is empty`);
    } else if (item.library_keys) media = await libraryItems(env, w, item.library_keys);
    else return fail('Give folder_id or library_keys');
  } catch (e) { return fail(e.message); }
  const video = media[0].kind === 'video' ? media[0] : null;
  if (video && media.length > 1) return fail('A post holds photos or one video, not both');

  let brand;
  try { brand = await resolveBrand(env, w, item.brand); } catch (e) { return fail(e.message); }
  if (brand === undefined) brand = folder?.brand_id ? await resolveBrand(env, w, folder.brand_id) : null;

  let targets = accounts;
  if (Array.isArray(item.account_ids) && item.account_ids.length) {
    const unknown = item.account_ids.filter(id => !accounts.some(a => a.id === id));
    if (unknown.length) return fail(`Unknown account ids: ${unknown.join(', ')}`);
    targets = accounts.filter(a => item.account_ids.includes(a.id));
  } else targets = accounts.filter(a => (brand ? a.brand_id === brand.id : !a.brand_id));
  if (Array.isArray(item.platforms) && item.platforms.length) {
    if (!item.platforms.every(p => PLATFORMS.includes(p))) return fail(`platforms can be ${PLATFORMS.join(', ')}`);
    targets = targets.filter(a => item.platforms.includes(a.platform));
  }
  const skipped = targets.filter(a => a.needs_reconnect).map(a => ({ account_id: a.id, handle: handle(a), platform: a.platform, reason: 'needs reconnecting in Publisher' }));
  targets = targets.filter(a => !a.needs_reconnect);
  if (!targets.length) return { index: n, ok: false, folder: folder && { id: folder.id, name: folder.name }, skipped,
    errors: [brand ? `Brand "${brand.name}" has no connected accounts${item.platforms ? ' on those platforms' : ''}` : 'No accounts to post to. Give brand or account_ids.'] };

  // Time: what was asked, or the brand's next free posting slot.
  let at;
  try {
    if (item.at !== undefined && item.at !== null && item.at !== 'next_slot') at = parseWhen(item.at, tz);
    else {
      const free = await freeSlots(env, w, brand, { count: 1, taken, info, from: item.after ? parseWhen(item.after, tz) : now() });
      if (!free.slots.length) return fail(free.reason || 'No free posting slot in the next 4 weeks. Give a time with "at".');
      at = free.slots[0].at;
    }
  } catch (e) { return fail(e.message); }
  if (at < now() + MIN_LEAD_SECONDS) errors.push('The time must be at least 5 minutes from now');
  taken.add(`${brand?.id || 'none'}:${at}`);

  if (typeof item.caption !== 'string') return fail('caption is required (it can be "" for no caption)');
  const captions = item.captions && typeof item.captions === 'object' ? item.captions : {};
  const tt = item.tiktok && typeof item.tiktok === 'object' ? item.tiktok : {};
  const posts = targets.map(a => {
    const input = { account_id: a.id, caption: typeof captions[a.platform] === 'string' ? captions[a.platform] : item.caption,
      title: String(item.title ?? ''), image_keys: video ? [] : media.map(m => m.key), video_key: video ? video.key : null, cover_index: 0,
      settings: a.platform === 'tiktok' ? { privacy_level: tt.privacy_level || '', disable_comment: !!tt.disable_comment,
        auto_add_music: !!tt.auto_add_music, disable_duet: !!tt.disable_duet, disable_stitch: !!tt.disable_stitch,
        brand_organic: !!tt.brand_organic, branded_content: !!tt.branded_content } : {},
      scheduled_at: Math.max(at, now() + MIN_LEAD_SECONDS) };
    const out = { account_id: a.id, handle: handle(a), platform: a.platform, caption: input.caption, input, error: null };
    try {
      validatePost(input, now(), a.platform, { draft: info.review });
      if (a.platform === 'instagram' && !video && media.some(m => m.content_type !== 'image/jpeg')) bad('Instagram only accepts JPG photos');
      if (a.platform === 'instagram' && !video && media.length > IG_MAX_IMAGES) bad(`Instagram takes at most ${IG_MAX_IMAGES} photos`);
      if (video?.duration_ms) checkLength(a.platform, video.duration_ms);
    } catch (e) { out.error = e.message; }
    return out;
  });
  posts.forEach(p => p.error && errors.push(`${p.handle} (${p.platform}): ${p.error}`));
  return { index: n, ok: !errors.length, errors, skipped,
    folder: folder && { id: folder.id, name: folder.name, status: folder.status },
    brand: brand ? { id: brand.id, name: brand.name } : null, when: when(at, tz),
    media: video ? { kind: 'video', key: video.key } : { kind: 'photos', count: media.length, cover: mediaUrl(env, media[0].key) },
    keys: media.map(m => m.key), video: !!video, posts };
}

const shape = e => ({ index: e.index, ok: e.ok, errors: e.errors, skipped: e.skipped?.length ? e.skipped : undefined,
  folder: e.folder || undefined, brand: e.brand, when: e.when, media: e.media,
  posts: e.posts?.map(p => ({ account_id: p.account_id, handle: p.handle, platform: p.platform, caption: p.caption, error: p.error || undefined })) });

export async function schedulePlan(env, tk, w, body) {
  const list = body?.posts;
  if (!Array.isArray(list) || !list.length) bad('posts must be a list of 1 or more posts');
  if (list.length > MAX_PLAN) bad(`A plan can hold up to ${MAX_PLAN} posts. Split it.`);
  const info = await workspaceInfo(env, wsOf(w));
  const ctx = { info, accounts: await listAccounts(env, w), taken: new Set() };
  const entries = [];
  for (let n = 0; n < list.length; n++) entries.push(await draftEntry(env, w, list[n], n, ctx));
  const ok = entries.every(e => e.ok), mode = info.review ? 'drafts_for_approval' : 'scheduled';
  const summary = { timezone: info.timezone, mode, posts: entries.length, publishes: entries.reduce((s, e) => s + (e.posts?.length || 0), 0) };
  if (body.confirm !== true || !ok) {
    return { preview: true, ok, ...summary, plan: entries.map(shape),
      next: ok ? 'Show this plan to the person. Call again with the same posts and confirm: true to make it.'
        : 'Fix the errors, then preview again.' };
  }

  if (!info.review) {
    const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND status = 'queued'`).bind(wsOf(w)).first();
    if (n + summary.publishes > MAX_QUEUED) throw new HttpError(409, `That would make more than ${MAX_QUEUED} posts waiting`);
  }
  const batch = 'bat_' + randomToken('', 8), made = [], failed = [];
  for (const e of entries) {
    const group = 'grp_' + randomToken('', 8), at = e.when.at;
    for (const p of e.posts) {
      try {
        const keys = e.video ? [] : (await copyMedia(env, w, e.keys)).media.map(m => m.key);
        const post = await createPost(env, tk, w, { ...p.input, image_keys: keys, draft: info.review, group_id: group });
        await env.DB.prepare(`UPDATE posts SET folder_id = ?, batch_id = ?, source = 'ai', scheduled_at = ?, next_attempt_at = ? WHERE id = ?`)
          .bind(e.folder?.id || null, batch, at, at, post.id).run();
        made.push({ post_id: post.id, index: e.index, handle: p.handle, platform: p.platform, status: post.status, when: e.when });
      } catch (err) {
        failed.push({ index: e.index, handle: p.handle, platform: p.platform, error: err.message });
      }
    }
  }
  return { batch_id: batch, ...summary, made, failed,
    note: info.review ? 'Made as drafts at their planned times. They publish only after someone approves them in Publisher (Drafts).'
      : 'Scheduled. Undo the whole run with undo_batch.' };
}

// ---- after a plan -------------------------------------------------------------

export async function undoBatch(env, w, batch) {
  if (!/^bat_[0-9a-f]{16}$/.test(String(batch))) bad('batch_id is invalid');
  const sc = inScope(w, 'a.brand_id');
  const { results } = await env.DB.prepare(`SELECT p.id, p.status FROM posts p JOIN accounts a ON a.id = p.account_id
      WHERE p.workspace_id = ? AND p.batch_id = ?${sc.sql}`).bind(wsOf(w), batch, ...sc.binds).all();
  if (!results.length) throw new HttpError(404, 'No posts in that batch');
  const undone = [], kept = [];
  for (const r of results) {
    if (!['queued', 'draft'].includes(r.status)) { kept.push({ post_id: r.id, status: r.status }); continue; }
    try { await cancelPost(env, w, r.id); undone.push(r.id); } catch (e) { kept.push({ post_id: r.id, status: r.status, error: e.message }); }
  }
  return { undone: undone.length, kept };
}

// Caption, title or time of a post that has not started. A draft keeps the
// new time as its planned time.
export async function editPost(env, w, id, body) {
  const info = await workspaceInfo(env, wsOf(w));
  const row = await loadPost(env, w, id);
  refuseImported(row);
  const at = body?.at === undefined ? undefined : parseWhen(body.at, info.timezone);
  if (row.status === 'draft') {
    if (at !== undefined && at < now() + MIN_LEAD_SECONDS) bad('Pick a time at least 5 minutes from now');
    const out = await updatePost(env, w, id, { caption: body?.caption, title: body?.title });
    if (at === undefined) return out;
    await env.DB.prepare(`UPDATE posts SET scheduled_at = ?, next_attempt_at = ? WHERE id = ? AND status = 'draft'`).bind(at, at, id).run();
    return postJson(env, await loadPost(env, w, id));
  }
  return updatePost(env, w, id, { caption: body?.caption, title: body?.title, ...(at === undefined ? {} : { scheduled_at: at }) });
}

// A person approves an AI draft: it is scheduled at its planned time (or a
// new one), with a TikTok privacy choice where needed.
export async function approvePost(env, tk, w, id, body = {}) {
  const row = await loadPost(env, w, id);
  refuseImported(row);
  if (row.status !== 'draft') throw new HttpError(409, 'Only drafts can be approved');
  const info = await workspaceInfo(env, wsOf(w));
  const at = body.at === undefined ? row.scheduled_at : parseWhen(body.at, info.timezone);
  if (at < now() + MIN_LEAD_SECONDS) throw new HttpError(409, 'Its planned time has passed. Approve it with a new time.');
  const account = await getAccount(env, w, row.account_id);
  if (account.needs_reconnect) throw new HttpError(409, 'Reconnect this account before posting', 'needs_reconnect');
  const settings = JSON.parse(row.settings);
  if (account.platform === 'tiktok' && body.privacy_level) settings.privacy_level = body.privacy_level;
  const p = validatePost({ account_id: row.account_id, image_keys: JSON.parse(row.image_keys), video_key: row.video_key,
    cover_index: row.cover_index, title: row.title, caption: row.caption, settings, scheduled_at: at }, now(), account.platform);
  if (!isMeta(account)) {
    const info2 = await tk.creatorInfo(await accessTokenFor(env, tk, account));
    if (!(info2.privacy_level_options || []).includes(p.settings.privacy_level)) bad('That privacy level is not available for this account right now');
  }
  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND status = 'queued'`).bind(wsOf(w)).first();
  if (n >= MAX_QUEUED) throw new HttpError(409, `You can have at most ${MAX_QUEUED} posts waiting at a time`);
  const r = await env.DB.prepare(`UPDATE posts SET status = 'queued', settings = ?, scheduled_at = ?, next_attempt_at = ?, updated_at = ?
      WHERE id = ? AND workspace_id = ? AND status = 'draft'`).bind(JSON.stringify(p.settings), at, at, now(), id, wsOf(w)).run();
  if (!r.meta.changes) throw new HttpError(409, 'That draft just changed. Reload and try again.');
  return postJson(env, await loadPost(env, w, id));
}

// Posts in a window, drafts included, with where they came from.
export async function findPosts(env, w, { from, to, brand, status = 'all' } = {}) {
  const info = await workspaceInfo(env, wsOf(w)), tz = info.timezone;
  const f = from === undefined ? now() - 7 * 86400 : parseWhen(from, tz), t = to === undefined ? now() + 21 * 86400 : parseWhen(to, tz);
  const b = await resolveBrand(env, w, brand);
  const sc = inScope(w, 'a.brand_id');
  const bf = b === undefined ? { sql: '', binds: [] } : b === null ? { sql: ' AND a.brand_id IS NULL', binds: [] } : { sql: ' AND a.brand_id = ?', binds: [b.id] };
  const stf = status === 'all' ? { sql: " AND p.status != 'cancelled'", binds: [] } : { sql: ' AND p.status = ?', binds: [String(status)] };
  const { results } = await env.DB.prepare(`SELECT p.*, a.username, a.display_name, a.platform, a.brand_id, f.name AS folder_name
      FROM posts p JOIN accounts a ON a.id = p.account_id LEFT JOIN library_folders f ON f.id = p.folder_id
      WHERE p.workspace_id = ? AND p.scheduled_at >= ? AND p.scheduled_at < ?${sc.sql}${bf.sql}${stf.sql} ORDER BY p.scheduled_at LIMIT 300`)
    .bind(wsOf(w), f, t, ...sc.binds, ...bf.binds, ...stf.binds).all();
  return { timezone: tz, posts: results.map(r => ({ post_id: r.id, status: r.status === 'draft' && r.source === 'ai' ? 'awaiting_approval' : r.status,
    when: when(r.scheduled_at, tz), platform: r.platform, account_id: r.account_id, handle: handle(r), brand_id: r.brand_id,
    folder: r.folder_id ? { id: r.folder_id, name: r.folder_name } : null, batch_id: r.batch_id || null, by_ai: r.source === 'ai',
    caption: r.caption, media: r.video_key ? 'video' : `${JSON.parse(r.image_keys).length} photos`,
    fail_reason: r.fail_reason || undefined, post_url: r.post_url || undefined, stats: r.stats ? JSON.parse(r.stats) : undefined,
    imported: !!r.imported })) };
}
