// Past posts. Publisher only knows the numbers of what it published itself, so
// each connected account's own posts (made in the apps, or before it was
// connected) are read in, 90 days back, with their numbers. A new account is
// read first; after that every account is read again once a day for new posts
// and fresh numbers. The cron gives this a few calls a tick, after publishing
// and stats have had theirs, and a long account is read a page per call
// across ticks (the paging cursor is kept on the account).
//
// Imported rows are status 'published' with imported = 1: no R2 media, no
// library folder, never queued, edited, cancelled or retried. A post Publisher
// made is never imported twice: by its id, and on TikTok (where the id can come
// late) by its time.

import { now } from './http.js';
import { randomToken } from './crypto.js';
import { accessTokenFor } from './accounts.js';
import { count, denied, rest, markReconnect, INSIGHTS_RETRY, ID_MATCH } from './stats.js';

const DAY = 86400;
export const IMPORT_BACK = 90 * DAY;
export const IMPORT_PER_TICK = 3;
const SWEEP_EVERY = DAY;
const RETRY_AFTER = 3600;

const resting = (a, t) => a.insights_denied_at && a.insights_denied_at > t - INSIGHTS_RETRY;
const epoch = s => {
  // Graph writes offsets as +0000.
  const ms = Date.parse(String(s || '').replace(/([+-]\d\d)(\d\d)$/, '$1:$2'));
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : null;
};

// An imported post and a Publisher post with the same id (a race between the
// two, settled later): the Publisher post stays. Two imported copies: the first.
export async function dropDuplicateImports(env) {
  await env.DB.prepare(`DELETE FROM posts WHERE imported = 1 AND public_post_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM posts q WHERE q.account_id = posts.account_id AND q.public_post_id = posts.public_post_id
        AND (q.imported = 0 OR q.rowid < posts.rowid))`).run();
}

// ---- one page per platform -----------------------------------------------------
// Each returns { items, next, calls }: items normalised, next the cursor of the
// following page or null when the read is done.

async function tiktokPage(env, tk, a, token, cursor, cutoff, t) {
  let page;
  try { page = await tk.videoPage(token, cursor); }
  catch (err) { if (!denied(err)) throw err; await rest(env, a, t); return { items: [], next: null, calls: 1 }; }
  const items = page.videos.filter(v => v.id && v.create_time).map(v => ({
    id: String(v.id), at: Number(v.create_time), caption: v.video_description || v.title || '',
    post_url: v.share_url || null, thumb_url: v.cover_image_url || null, media_url: null,
    stats: { views: count(v.view_count), likes: count(v.like_count), comments: count(v.comment_count), shares: count(v.share_count) },
  }));
  const oldest = Math.min(...items.map(i => i.at));
  const next = page.has_more && page.cursor != null && items.length && oldest >= cutoff ? String(page.cursor) : null;
  return { items, next, calls: 1 };
}

// Instagram and Facebook: the numbers that need insights come in the same call
// when the token allows it; when it does not, the page is read again without
// them. An Instagram account then rests a week, as in stats.js; a Facebook Page
// rests only when even the basic read is refused (facebookPage).
async function withInsights(env, a, t, budget, read, restOnDeny) {
  const tryInsights = !resting(a, t);
  if (!tryInsights) return { body: await read(false), calls: 1 };
  try {
    const body = await read(true);
    if (a.insights_denied_at) {
      await env.DB.prepare('UPDATE accounts SET insights_denied_at = NULL WHERE id = ?').bind(a.id).run();
      a.insights_denied_at = null;
    }
    return { body, calls: 1 };
  } catch (err) {
    if (err.code === 'needs_reconnect' || err.transient) throw err;
    if (restOnDeny && denied(err)) await rest(env, a, t);
    // Without spare calls, the page is read next tick (insights now resting).
    if (budget < 2) return { body: null, calls: 1 };
    return { body: await read(false), calls: 2 };
  }
}

async function instagramPage(env, mt, a, token, cursor, cutoff, t, budget) {
  const igId = a.open_id.slice(3);
  const { body, calls } = await withInsights(env, a, t, budget, insights => mt.igMediaPage(token, igId, { after: cursor, insights }), true);
  if (!body) return { items: [], next: cursor, calls, again: true };
  const items = (body.data || []).filter(m => m.id && epoch(m.timestamp)).map(m => {
    const s = { likes: count(m.like_count), comments: count(m.comments_count) };
    for (const x of m.insights?.data || []) {
      const v = x.values?.[0]?.value ?? x.total_value?.value;
      const key = { views: 'views', reach: 'reach', saved: 'saves', shares: 'shares' }[x.name];
      if (key && v !== undefined) s[key] = count(v);
    }
    return { id: String(m.id), at: epoch(m.timestamp), caption: m.caption || '', post_url: m.permalink || null,
      thumb_url: (m.media_type === 'VIDEO' ? m.thumbnail_url : m.media_url) || m.thumbnail_url || null,
      media_url: m.media_url || null, stats: s };
  });
  const oldest = Math.min(...items.map(i => i.at));
  const after = body.paging?.cursors?.after;
  const next = body.paging?.next && after && items.length && oldest >= cutoff ? after : null;
  return { items, next, calls };
}

async function facebookPage(env, mt, a, token, cursor, cutoff, t, budget) {
  const pageId = a.open_id.slice(3), wasResting = resting(a, t);
  let r;
  try {
    r = await withInsights(env, a, t, budget, insights => mt.fbPostsPage(token, pageId, { after: cursor, since: cutoff, insights }), false);
  } catch (err) {
    // Without pages_read_user_content the Page's posts cannot be read at all.
    if (!denied(err)) throw err;
    await rest(env, a, t);
    return { items: [], next: null, calls: wasResting ? 1 : 2 };
  }
  const { body, calls } = r;
  if (!body) return { items: [], next: cursor, calls, again: true };
  const items = (body.data || []).filter(p => p.id && epoch(p.created_time)).map(p => {
    const s = { likes: count(p.reactions?.summary?.total_count), comments: count(p.comments?.summary?.total_count), shares: count(p.shares?.count) };
    for (const x of p.insights?.data || []) {
      const key = { post_media_view: 'views', post_total_media_view_unique: 'reach' }[x.name];
      if (key) s[key] = count(x.values?.[0]?.value);
    }
    return { id: String(p.id), at: epoch(p.created_time), caption: p.message || '', post_url: p.permalink_url || null,
      thumb_url: p.full_picture || null, media_url: p.full_picture || null, stats: s };
  });
  const oldest = Math.min(...items.map(i => i.at));
  const after = body.paging?.cursors?.after;
  const next = body.paging?.next && after && items.length && oldest >= cutoff ? after : null;
  return { items, next, calls };
}

// ---- writing one page ----------------------------------------------------------

async function save(env, a, items, cutoff, t) {
  items = items.filter(i => i.at >= cutoff);
  if (!items.length) return { imported: 0, updated: 0 };
  const marks = items.map(() => '?').join(',');
  const { results: known } = await env.DB.prepare(`SELECT id, public_post_id, imported FROM posts
      WHERE account_id = ? AND public_post_id IN (${marks})`).bind(a.id, ...items.map(i => i.id)).all();
  const byRemote = new Map(known.map(r => [String(r.public_post_id), r]));
  // TikTok: Publisher posts still waiting for their id, matched by time like
  // findTikTokIds does. One still publishing holds off nearby posts for now.
  let waiting = [];
  if (a.platform === 'tiktok') {
    ({ results: waiting } = await env.DB.prepare(`SELECT id, status, scheduled_at FROM posts WHERE account_id = ? AND imported = 0
        AND public_post_id IS NULL AND status IN ('published', 'publishing') AND scheduled_at > ?`)
      .bind(a.id, cutoff - ID_MATCH).all());
  }
  const writes = [];
  let imported = 0, updated = 0;
  for (const i of items) {
    const row = byRemote.get(i.id);
    if (row && !row.imported) continue;
    if (row) {
      writes.push(env.DB.prepare(`UPDATE posts SET caption = ?, post_url = COALESCE(?, post_url), thumb_url = COALESCE(?, thumb_url),
          media_url = COALESCE(?, media_url), stats = ?, stats_at = ?, updated_at = ? WHERE id = ? AND imported = 1`)
        .bind(i.caption, i.post_url, i.thumb_url, i.media_url, JSON.stringify(i.stats), t, t, row.id));
      updated++;
      continue;
    }
    const near = waiting.filter(p => Math.abs(p.scheduled_at - i.at) <= ID_MATCH)
      .sort((x, y) => Math.abs(x.scheduled_at - i.at) - Math.abs(y.scheduled_at - i.at));
    if (near.length) {
      const p = near[0];
      waiting = waiting.filter(x => x !== p);
      if (p.status === 'published') {
        writes.push(env.DB.prepare('UPDATE posts SET public_post_id = ?, stats = ?, stats_at = ? WHERE id = ? AND public_post_id IS NULL')
          .bind(i.id, JSON.stringify(i.stats), t, p.id));
      }
      continue;
    }
    writes.push(env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, title, caption, image_keys, cover_index,
        settings, scheduled_at, next_attempt_at, public_post_id, post_url, stats, stats_at, imported, media_url, thumb_url, created_at, updated_at)
        VALUES (?, ?, ?, 'published', '', ?, '[]', 0, '{}', ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)`)
      .bind('pst_' + randomToken('', 8), a.workspace_id, a.id, i.caption, i.at, i.at, i.id, i.post_url,
        JSON.stringify(i.stats), t, i.media_url, i.thumb_url, t, t));
    imported++;
  }
  if (writes.length) await env.DB.batch(writes);
  return { imported, updated };
}

// ---- the cron job --------------------------------------------------------------

export async function importPast(env, mt, tk, t = now(), budget = IMPORT_PER_TICK) {
  const done = { calls: 0, imported: 0, updated: 0, accounts: 0 };
  if (budget <= 0) return done;
  await dropDuplicateImports(env);
  // Never read first, then reads under way, then the longest ago.
  const { results: accs } = await env.DB.prepare(`SELECT * FROM accounts WHERE needs_reconnect = 0
      AND (import_cursor IS NOT NULL OR imported_at IS NULL OR imported_at < ?)
      AND (platform != 'tiktok' OR insights_denied_at IS NULL OR insights_denied_at < ?)
      ORDER BY imported_at IS NOT NULL, import_cursor IS NULL, COALESCE(imported_at, 0) LIMIT ?`)
    .bind(t - SWEEP_EVERY, t - INSIGHTS_RETRY, budget).all();
  const cutoff = t - IMPORT_BACK;
  for (const a of accs) {
    if (budget <= 0) break;
    let cursor = a.import_cursor || null;
    try {
      const token = await accessTokenFor(env, tk, a);
      // Page after page of this account while calls last.
      while (budget > 0) {
        const page = a.platform === 'tiktok' ? await tiktokPage(env, tk, a, token, cursor, cutoff, t)
          : a.platform === 'instagram' ? await instagramPage(env, mt, a, token, cursor, cutoff, t, budget)
            : await facebookPage(env, mt, a, token, cursor, cutoff, t, budget);
        budget -= page.calls; done.calls += page.calls;
        if (page.again) {
          // Not read this time; keep the place and come back next tick.
          await env.DB.prepare('UPDATE accounts SET import_cursor = ? WHERE id = ?').bind(cursor ?? '', a.id).run();
          break;
        }
        const n = await save(env, a, page.items, cutoff, t);
        done.imported += n.imported; done.updated += n.updated;
        cursor = page.next;
        if (!cursor) {
          await env.DB.prepare('UPDATE accounts SET imported_at = ?, import_cursor = NULL WHERE id = ?').bind(t, a.id).run();
          done.accounts++;
          break;
        }
        await env.DB.prepare('UPDATE accounts SET import_cursor = ? WHERE id = ?').bind(cursor, a.id).run();
      }
    } catch (err) {
      if (err.code === 'needs_reconnect') await markReconnect(env, a.id);
      else {
        // Start over in an hour rather than every minute.
        console.error('import', a.id, err.message);
        await env.DB.prepare('UPDATE accounts SET imported_at = ?, import_cursor = NULL WHERE id = ?')
          .bind(t - SWEEP_EVERY + RETRY_AFTER, a.id).run();
      }
    }
  }
  return done;
}
