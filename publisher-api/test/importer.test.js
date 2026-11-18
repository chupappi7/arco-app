import { env as baseEnv, createExecutionContext, waitOnExecutionContext } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk, callWorker, signUp } from './helpers.js';
import { encrypt } from '../src/crypto.js';
import { importPast, IMPORT_BACK } from '../src/importer.js';
import { getStats, refreshStats } from '../src/stats.js';
import { MetaError } from '../src/meta.js';
import worker from '../src/index.js';

const T = 1_800_000_000;
const DAY = 86400;
const env = baseEnv;

async function account(id, platform, ws = 'ws1', extra = {}) {
  const enc = await encrypt(`tok-${id}`, env.TOKEN_KEY);
  await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, username, refresh_token_enc, access_token_enc,
      access_expires_at, connected_at, token_updated_at, brand_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?)`)
    .bind(id, ws, `${platform === 'tiktok' ? '' : platform === 'instagram' ? 'ig:' : 'fb:'}${id}-remote`, platform, id, enc, enc,
      platform === 'tiktok' ? 4_000_000_000 : null, extra.brand ?? null).run();
}
async function post(id, accountId, at, { ws = 'ws1', status = 'published', remote = `m-${id}`, stats = null } = {}) {
  await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at,
      next_attempt_at, public_post_id, stats, created_at, updated_at) VALUES (?, ?, ?, ?, '["k"]', '{}', ?, ?, ?, ?, 1, 1)`)
    .bind(id, ws, accountId, status, at, at, remote, stats && JSON.stringify(stats)).run();
}
const rows = async (where = '1 = 1') => (await env.DB.prepare(`SELECT * FROM posts WHERE ${where} ORDER BY scheduled_at DESC`).all()).results;

// TikTok's list: `pages` of videos, newest first, cursor = the index of the next page.
function tiktokPages(pages, calls = []) {
  return fakeTk({
    videoPage: async (tok, cursor) => {
      const i = cursor ? Number(cursor) : 0;
      calls.push(i);
      return { videos: pages[i] || [], cursor: i + 1, has_more: i + 1 < pages.length };
    },
  });
}
const video = (id, at, extra = {}) => ({ id, create_time: at, view_count: 100, like_count: 10, comment_count: 2, share_count: 1,
  video_description: `caption ${id}`, cover_image_url: `https://cdn/${id}.jpg`, share_url: `https://www.tiktok.com/@x/video/${id}`, ...extra });

describe('importing past TikTok posts', () => {
  beforeEach(() => resetDb(env));

  it('pages back 90 days, across ticks, and stops at the cutoff', async () => {
    await account('tt1', 'tiktok');
    const pages = [
      [video('7001', T - 1 * DAY), video('7002', T - 2 * DAY)],
      [video('7003', T - 30 * DAY), video('7004', T - 60 * DAY)],
      [video('7005', T - 89 * DAY), video('7006', T - 91 * DAY)],
      [video('7007', T - 120 * DAY)],
    ];
    const calls = [];
    const tk = tiktokPages(pages, calls);
    let done = await importPast(env, {}, tk, T, 2);
    expect(done.calls).toBe(2);
    expect((await rows()).length).toBe(4);
    let a = await env.DB.prepare("SELECT imported_at, import_cursor FROM accounts WHERE id = 'tt1'").first();
    expect(a.imported_at).toBe(null);
    expect(a.import_cursor).toBe('2');
    done = await importPast(env, {}, tk, T + 60, 3);
    // Page 3 reaches past 90 days: the read is done, page 4 is never asked for.
    expect(done.calls).toBe(1);
    expect(calls).toEqual([0, 1, 2]);
    const all = await rows();
    expect(all.map(r => r.public_post_id)).toEqual(['7001', '7002', '7003', '7004', '7005']);
    const r = all[0];
    expect(r).toMatchObject({ status: 'published', imported: 1, image_keys: '[]', settings: '{}', scheduled_at: T - DAY,
      caption: 'caption 7001', thumb_url: 'https://cdn/7001.jpg', post_url: 'https://www.tiktok.com/@x/video/7001' });
    expect(JSON.parse(r.stats)).toEqual({ views: 100, likes: 10, comments: 2, shares: 1 });
    a = await env.DB.prepare("SELECT imported_at, import_cursor FROM accounts WHERE id = 'tt1'").first();
    expect(a).toEqual({ imported_at: T + 60, import_cursor: null });
    // Read again only a day later.
    expect((await importPast(env, {}, tk, T + 3600, 3)).calls).toBe(0);
  });

  it('never doubles a Publisher post, by id or by time', async () => {
    await account('tt1', 'tiktok');
    await post('mine', 'tt1', T - 2 * DAY, { remote: '7002' });
    // Published, id not known yet: matched by time (within the hour), and given the id.
    await post('late', 'tt1', T - 3 * DAY, { remote: null });
    const tk = tiktokPages([[video('7001', T - DAY), video('7002', T - 2 * DAY), video('7003', T - 3 * DAY + 600)]]);
    await importPast(env, {}, tk, T, 3);
    const all = await rows();
    expect(all.length).toBe(3);
    expect(all.filter(r => r.imported).map(r => r.public_post_id)).toEqual(['7001']);
    const late = all.find(r => r.id === 'late');
    expect(late.public_post_id).toBe('7003');
    expect(JSON.parse(late.stats).views).toBe(100);
    expect(all.find(r => r.id === 'mine').stats).toBe(null);
  });

  it('holds off a video next to a post still publishing, and drops a copy once the post gets its id', async () => {
    await account('tt1', 'tiktok');
    await post('busy', 'tt1', T - 3600, { status: 'publishing', remote: null });
    const tk = tiktokPages([[video('7009', T - 3000)]]);
    await importPast(env, {}, tk, T, 3);
    expect((await rows('imported = 1')).length).toBe(0);
    // A race the other way: imported first, then publishing hands over the same id.
    await env.DB.prepare(`UPDATE posts SET status = 'published', public_post_id = NULL WHERE id = 'busy'`).run();
    await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at, next_attempt_at,
        public_post_id, imported, created_at, updated_at) VALUES ('imp', 'ws1', 'tt1', 'published', '[]', '{}', ?, ?, '7009', 1, 1, 1)`)
      .bind(T - 3000, T - 3000).run();
    await env.DB.prepare(`UPDATE posts SET public_post_id = '7009' WHERE id = 'busy'`).run();
    await importPast(env, {}, tk, T + 2 * DAY, 3);
    const all = await rows();
    expect(all.map(r => r.id)).toEqual(['busy']);
  });

  it('lets the TikTok id finder claim a video that was imported first', async () => {
    await account('tt1', 'tiktok');
    await post('a', 'tt1', T - 3600, { remote: null });
    await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at, next_attempt_at,
        public_post_id, imported, created_at, updated_at) VALUES ('imp', 'ws1', 'tt1', 'published', '[]', '{}', ?, ?, '7700', 1, 1, 1)`)
      .bind(T - 3600 + 40, T - 3600 + 40).run();
    const tk = fakeTk({ userStats: async () => ({ follower_count: 1 }), status: async () => ({}),
      listVideos: async () => [{ id: '7700', create_time: T - 3600 + 40 }], videoStats: async () => [] });
    await refreshStats(env, {}, tk, T, 6);
    const all = await rows();
    expect(all.map(r => [r.id, r.public_post_id])).toEqual([['a', '7700']]);
  });

  it('is idempotent: a second sweep updates numbers and adds only new posts', async () => {
    await account('tt1', 'tiktok');
    let views = 100;
    const list = () => [video('7001', T - DAY, { view_count: views }), video('7002', T - 2 * DAY, { view_count: views })];
    let extra = [];
    const tk = fakeTk({ videoPage: async () => ({ videos: [...extra, ...list()], cursor: 1, has_more: false }) });
    await importPast(env, {}, tk, T, 3);
    views = 900; extra = [video('7010', T + DAY, { view_count: 900 })];
    await importPast(env, {}, tk, T + DAY + 10, 3);
    const all = await rows();
    expect(all.map(r => r.public_post_id)).toEqual(['7010', '7001', '7002']);
    expect(all.map(r => JSON.parse(r.stats).views)).toEqual([900, 900, 900]);
  });

  it('marks an account for reconnecting when its token is dead', async () => {
    await account('tt1', 'tiktok');
    const e = new Error('Reconnect this account'); e.code = 'needs_reconnect';
    await importPast(env, {}, fakeTk({ videoPage: async () => { throw e; } }), T, 3);
    expect((await env.DB.prepare("SELECT needs_reconnect FROM accounts WHERE id = 'tt1'").first()).needs_reconnect).toBe(1);
  });
});

const igMedia = (id, at, extra = {}) => ({ id, caption: `ig ${id}`, media_type: 'IMAGE', media_url: `https://ig/${id}.jpg`,
  permalink: `https://www.instagram.com/p/${id}/`, timestamp: new Date(at * 1000).toISOString().replace('.000Z', '+0000'),
  like_count: 20, comments_count: 4, ...extra });

describe('importing past Instagram posts', () => {
  beforeEach(() => resetDb(env));

  it('reads media with insights where allowed', async () => {
    await account('ig1', 'instagram');
    const calls = [];
    const mt = { igMediaPage: async (tok, igId, o) => { calls.push([igId, o.after || null, o.insights]);
      const m = o.after ? [igMedia('i3', T - 95 * DAY)] : [igMedia('i1', T - DAY, { insights: { data: [{ name: 'views', values: [{ value: 500 }] }, { name: 'saved', values: [{ value: 3 }] }] } }),
        igMedia('i2', T - 5 * DAY, { media_type: 'VIDEO', thumbnail_url: 'https://ig/i2-thumb.jpg', media_url: 'https://ig/i2.mp4' })];
      return { data: m, paging: { cursors: { after: 'AFT' }, next: o.after ? undefined : 'https://next' } }; } };
    const done = await importPast(env, mt, fakeTk(), T, 3);
    expect(calls).toEqual([['ig1-remote', null, true], ['ig1-remote', 'AFT', true]]);
    expect(done.imported).toBe(2);
    const all = await rows();
    expect(all.map(r => r.public_post_id)).toEqual(['i1', 'i2']);
    expect(JSON.parse(all[0].stats)).toEqual({ likes: 20, comments: 4, views: 500, saves: 3 });
    expect(all[0]).toMatchObject({ caption: 'ig i1', post_url: 'https://www.instagram.com/p/i1/', thumb_url: 'https://ig/i1.jpg', scheduled_at: T - DAY });
    expect(all[1].thumb_url).toBe('https://ig/i2-thumb.jpg');
  });

  it('falls back to likes and comments without insights, and rests insights for a week', async () => {
    await account('ig1', 'instagram');
    const calls = [];
    const mt = { igMediaPage: async (tok, igId, o) => { calls.push(o.insights);
      if (o.insights) throw new MetaError('instagram media list: (#10) Application does not have permission', { code: '10' });
      return { data: [igMedia('i1', T - DAY)], paging: {} }; } };
    await importPast(env, mt, fakeTk(), T, 3);
    expect(calls).toEqual([true, false]);
    const [r] = await rows();
    expect(JSON.parse(r.stats)).toEqual({ likes: 20, comments: 4 });
    expect((await env.DB.prepare("SELECT insights_denied_at FROM accounts WHERE id = 'ig1'").first()).insights_denied_at).toBe(T);
    // Next day: straight to the basic read.
    await importPast(env, mt, fakeTk(), T + DAY + 1, 3);
    expect(calls).toEqual([true, false, false]);
    expect((await rows()).length).toBe(1);
  });
});

describe('importing past Facebook posts', () => {
  beforeEach(() => resetDb(env));

  it('reads Page posts with views, and the basic counts without read_insights', async () => {
    await account('fb1', 'facebook');
    const calls = [];
    let insightsOk = true;
    const fbPost = (id, at) => ({ id, message: `fb ${id}`, created_time: new Date(at * 1000).toISOString().replace('.000Z', '+0000'),
      permalink_url: `https://facebook.com/${id}`, full_picture: `https://fb/${id}.jpg`, shares: { count: 2 },
      reactions: { summary: { total_count: 9 } }, comments: { summary: { total_count: 1 } } });
    const mt = { fbPostsPage: async (tok, pageId, o) => { calls.push([pageId, o.since, o.insights]);
      if (o.insights && !insightsOk) throw new MetaError('facebook post list: (#200) requires read_insights', { code: '200' });
      const p = fbPost('fb_1', T - DAY);
      if (o.insights) p.insights = { data: [{ name: 'post_media_view', values: [{ value: 77 }] }] };
      return { data: [p], paging: {} }; } };
    await importPast(env, mt, fakeTk(), T, 3);
    expect(calls).toEqual([['fb1-remote', T - IMPORT_BACK, true]]);
    let [r] = await rows();
    expect(r).toMatchObject({ imported: 1, caption: 'fb fb_1', post_url: 'https://facebook.com/fb_1', thumb_url: 'https://fb/fb_1.jpg' });
    expect(JSON.parse(r.stats)).toEqual({ likes: 9, comments: 1, shares: 2, views: 77 });
    insightsOk = false;
    await importPast(env, mt, fakeTk(), T + DAY + 1, 3);
    [r] = await rows();
    expect(JSON.parse(r.stats)).toEqual({ likes: 9, comments: 1, shares: 2 });
    // Insights alone refused: the Page is not put to rest.
    expect((await env.DB.prepare("SELECT insights_denied_at FROM accounts WHERE id = 'fb1'").first()).insights_denied_at).toBe(null);
  });
});

describe('imported posts in stats and as read-only posts', () => {
  beforeEach(() => resetDb(env));

  it('count in totals, per platform and top posts, carrying imported and thumb_url', async () => {
    await account('tt1', 'tiktok');
    await post('mine', 'tt1', T - DAY, { remote: '7100', stats: { views: 50, likes: 1 } });
    await importPast(env, {}, tiktokPages([[video('7200', T - 2 * DAY, { view_count: 5000 })]]), T, 3);
    const st = await getStats(env, 'ws1', 7, T);
    expect(st.published).toBe(2);
    expect(st.imported).toBe(1);
    expect(st.totals.views).toBe(5050);
    expect(st.by_platform[0].views).toBe(5050);
    expect(st.top[0]).toMatchObject({ public_post_id: '7200', imported: true, thumb_url: 'https://cdn/7200.jpg', images: [] });
    expect(st.top[1].imported).toBe(false);
  });

  it('refuse cancel, retry, edit and approve with a 400', async () => {
    const s = await (await callWorker('/internal/oauth', { method: 'POST', headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
      body: { code: 'c', code_verifier: 'v', redirect_uri: 'https://arco-publisher.vercel.app/api/auth/callback', session_id: (await signUp(env)).sid } })).json();
    const h = { Cookie: `tt_sid=${s.session_id}` };
    const acc = await env.DB.prepare('SELECT workspace_id FROM accounts WHERE id = ?').bind(s.account_id).first();
    const at = Math.floor(Date.now() / 1000) - DAY;
    await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings, scheduled_at, next_attempt_at,
        public_post_id, imported, created_at, updated_at) VALUES ('imp1', ?, ?, 'published', '[]', '{}', ?, ?, '7300', 1, 1, 1)`)
      .bind(acc.workspace_id, s.account_id, at, at).run();
    for (const [path, method, body] of [['/v1/posts/imp1', 'DELETE'], ['/v1/posts/imp1/retry', 'POST'],
      ['/v1/posts/imp1', 'PATCH', { caption: 'x' }], ['/v1/posts/imp1/approve', 'POST', {}]]) {
      const res = await callWorker(path, { method, headers: h, body });
      expect(res.status, `${method} ${path}`).toBe(400);
      expect((await res.json()).error).toMatch(/outside Publisher/);
    }
    // Listed, marked as imported.
    const list = await (await callWorker(`/v1/posts?from=${at - 10}&to=${at + 10}`, { headers: h })).json();
    expect(list.posts.map(p => [p.id, p.imported])).toEqual([['imp1', true]]);
    // Disconnecting the account removes what was only read in.
    await callWorker(`/v1/accounts/${s.account_id}`, { method: 'DELETE', headers: h });
    expect((await rows("id = 'imp1'")).length).toBe(0);
  });
});

describe('cron', () => {
  beforeEach(() => resetDb(env));

  it('gives past posts only a few calls a tick, after stats', async () => {
    for (const id of ['tt1', 'tt2', 'tt3']) await account(id, 'tiktok');
    const calls = [];
    const tk = tiktokPages([[video('8001', Math.floor(Date.now() / 1000) - DAY)], [], [], [], []], calls);
    tk.userStats = async () => ({ follower_count: 1 });
    const ctx = createExecutionContext();
    await worker.scheduled({}, { ...env, __tk: tk, __meta: {} }, ctx);
    await waitOnExecutionContext(ctx);
    expect(calls.length).toBe(3);
    expect((await rows('imported = 1')).length).toBeGreaterThan(0);
  });

  it('gets no calls when there are none to spare', async () => {
    await account('tt1', 'tiktok');
    const calls = [];
    expect(await importPast(env, {}, tiktokPages([[video('1', T)]], calls), T, 0)).toMatchObject({ calls: 0 });
    expect(await importPast(env, {}, tiktokPages([[video('1', T)]], calls), T, -4)).toMatchObject({ calls: 0 });
    expect(calls).toEqual([]);
  });
});
