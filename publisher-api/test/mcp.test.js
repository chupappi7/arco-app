import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, signUp } from './helpers.js';
import { encrypt } from '../src/crypto.js';
import { rotateApiKey } from '../src/auth.js';
import { zonedToEpoch, parseWhen, localIso, staggerOffsets, STAGGER } from '../src/planner.js';

const JPEG_B64 = btoa(String.fromCharCode(0xff, 0xd8, 0xff, 0xe0, 1, 2, 3, 4));
const PNG_B64 = btoa(String.fromCharCode(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 9));

async function workspace({ review = true } = {}) {
  const { ws } = await signUp(env);
  await env.DB.prepare(`UPDATE workspaces SET timezone = 'Europe/Prague', slots = ?, ai_review = ? WHERE id = ?`)
    .bind(JSON.stringify({ days: [0, 1, 2, 3, 4, 5, 6], times: ['09:00', '18:00'] }), review ? 1 : 0, ws).run();
  await env.DB.prepare('INSERT INTO brands (id, workspace_id, name, created_at) VALUES (?, ?, ?, 1)').bind('brd_bakery', ws, 'Bakery').run();
  const enc = await encrypt('tok', env.TOKEN_KEY);
  for (const [id, platform, brand] of [['acc_tt', 'tiktok', 'brd_bakery'], ['acc_ig', 'instagram', 'brd_bakery'], ['acc_x', 'facebook', null]]) {
    await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, platform, username, refresh_token_enc, access_token_enc,
        access_expires_at, connected_at, token_updated_at, brand_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?)`)
      .bind(id, ws, `${platform === 'tiktok' ? '' : platform === 'instagram' ? 'ig:' : 'fb:'}${id}`, platform, id, enc, enc, 9e9, brand).run();
  }
  const key = await rotateApiKey(env, ws);
  return { ws, h: { Authorization: `Bearer ${key}` } };
}

let seq = 0;
async function rpc(h, method, params) {
  const res = await callWorker('/mcp', { method: 'POST', headers: h, body: { jsonrpc: '2.0', id: ++seq, method, params } });
  return { status: res.status, body: res.status === 202 ? null : await res.json() };
}
async function tool(h, name, args = {}) {
  const { body } = await rpc(h, 'tools/call', { name, arguments: args });
  const r = body.result;
  return { error: r.isError ? r.content[0].text : null, data: r.isError ? null : JSON.parse(r.content[0].text) };
}
async function folderWithPhotos(h, name, n = 2, b64 = JPEG_B64) {
  const f = (await tool(h, 'create_folder', { name, brand: 'bakery', note: '20% off, code BF20' })).data;
  const up = await tool(h, 'upload_to_folder', { folder_id: f.id, files: [...Array(n)].map((_, i) => ({ data_base64: b64, filename: `${i + 1}.jpg` })) });
  expect(up.data.uploaded).toBe(n);
  return f;
}

describe('mcp protocol', () => {
  beforeEach(() => resetDb(env));

  it('needs the API key, then initializes and lists the tools', async () => {
    const res = await callWorker('/mcp', { method: 'POST', body: { jsonrpc: '2.0', id: 1, method: 'initialize', params: {} } });
    expect(res.status).toBe(401);
    expect(res.headers.get('WWW-Authenticate')).toContain('Bearer');

    const { h } = await workspace();
    const init = (await rpc(h, 'initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '1' } })).body;
    expect(init.result.protocolVersion).toBe('2025-06-18');
    expect(init.result.serverInfo.name).toBe('arco-publisher');
    expect(init.result.instructions).toMatch(/confirm: false/);
    expect((await callWorker('/mcp', { method: 'POST', headers: h, body: { jsonrpc: '2.0', method: 'notifications/initialized' } })).status).toBe(202);

    // The connector link carries the key in the path instead of a header.
    const link = `/mcp/${h.Authorization.slice(7)}`;
    const viaLink = await callWorker(link, { method: 'POST', body: { jsonrpc: '2.0', id: 99, method: 'initialize', params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '1' } } } });
    expect(viaLink.status).toBe(200);
    expect((await viaLink.json()).result.serverInfo.name).toBe('arco-publisher');
    expect((await callWorker(`/mcp/apk_${'0'.repeat(64)}`, { method: 'POST', body: { jsonrpc: '2.0', id: 1, method: 'initialize', params: {} } })).status).toBe(401);

    const tools = (await rpc(h, 'tools/list')).body.result.tools.map(t => t.name);
    expect(tools).toEqual(expect.arrayContaining(['get_overview', 'list_folders', 'upload_to_folder', 'schedule_posts', 'undo_batch', 'get_stats']));
    expect((await rpc(h, 'nope/nope')).body.error.code).toBe(-32601);
    expect((await rpc(h, 'tools/call', { name: 'no_such_tool', arguments: {} })).body.error.code).toBe(-32602);
  });
});

describe('time', () => {
  it('reads wall-clock times in the workspace zone, across DST', () => {
    expect(zonedToEpoch(2026, 7, 1, 9, 0, 'Europe/Prague')).toBe(Date.UTC(2026, 6, 1, 7, 0) / 1000);
    expect(zonedToEpoch(2026, 12, 1, 9, 0, 'Europe/Prague')).toBe(Date.UTC(2026, 11, 1, 8, 0) / 1000);
    expect(parseWhen('2026-12-01T09:00', 'Europe/Prague')).toBe(Date.UTC(2026, 11, 1, 8, 0) / 1000);
    expect(parseWhen('2026-12-01T09:00Z', 'Europe/Prague')).toBe(Date.UTC(2026, 11, 1, 9, 0) / 1000);
    expect(localIso(Date.UTC(2026, 11, 1, 8, 0) / 1000, 'Europe/Prague')).toBe('2026-12-01T09:00+01:00');
    expect(() => parseWhen('next tuesday', 'UTC')).toThrow(/2026-11-20T18:00/);
  });
});

describe('stagger', () => {
  it('spaces accounts on one platform an hour apart, other platforms start at the same time', () => {
    const accts = [{ id: 'a', platform: 'tiktok' }, { id: 'b', platform: 'instagram' }, { id: 'c', platform: 'tiktok' }, { id: 'd', platform: 'tiktok' }];
    const o = staggerOffsets(accts);
    expect([o.get('a'), o.get('b'), o.get('c'), o.get('d')]).toEqual([0, 0, STAGGER, 2 * STAGGER]);
    expect([...staggerOffsets(accts, false).values()]).toEqual([0, 0, 0, 0]);
  });
});

describe('mcp tools', () => {
  beforeEach(() => resetDb(env));

  it('gives an overview with brands, accounts, slots and approval mode', async () => {
    const { h } = await workspace();
    const o = (await tool(h, 'get_overview')).data;
    expect(o.timezone).toBe('Europe/Prague');
    expect(o.approval).toMatch(/^on/);
    expect(o.brands[0]).toMatchObject({ name: 'Bakery', library: { folders: 0 } });
    expect(o.brands[0].accounts.map(a => a.platform).sort()).toEqual(['instagram', 'tiktok']);
    expect(o.brands[0].next_free_slots).toHaveLength(3);
    expect(o.not_in_a_brand.accounts.map(a => a.id)).toEqual(['acc_x']);
  });

  it('builds a folder from uploads, in order, and lists it as unused', async () => {
    const { h } = await workspace();
    const f = await folderWithPhotos(h, 'Black Friday', 3);
    const list = (await tool(h, 'list_folders', { brand: 'Bakery', status: 'unused' })).data.folders;
    expect(list).toHaveLength(1);
    expect(list[0]).toMatchObject({ id: f.id, kind: 'photos', status: 'unused', note: '20% off, code BF20', brand: 'Bakery' });
    expect(list[0].items.map(i => i.name)).toEqual(['1.jpg', '2.jpg', '3.jpg']);
    const reordered = (await tool(h, 'update_folder', { folder_id: f.id, order: [...list[0].items.map(i => i.key)].reverse() })).data;
    expect(reordered.items.map(i => i.name)).toEqual(['3.jpg', '2.jpg', '1.jpg']);
    const bad = await tool(h, 'upload_to_folder', { folder_id: f.id, files: [{ url: 'http://example.com/a.jpg' }] });
    expect(bad.data.files[0]).toMatchObject({ ok: false, error: 'Only https URLs' });
    for (const url of ['https://127.0.0.1/a.jpg', 'https://localhost/a.jpg', 'https://[::1]/a.jpg', 'https://169.254.169.254/x', 'https://db.internal/a.jpg']) {
      const r = await tool(h, 'upload_to_folder', { folder_id: f.id, files: [{ url }] });
      expect(r.data.files[0]).toMatchObject({ ok: false, error: 'That URL host is not allowed' });
    }
    expect((await tool(h, 'create_folder', { name: 'X', brand: 'Nope' })).error).toMatch(/No brand called "Nope"/);
  });

  it('previews a plan, then makes approval drafts at the planned times; approve and undo work', async () => {
    const { h } = await workspace();
    const f1 = await folderWithPhotos(h, 'Croissants'), f2 = await folderWithPhotos(h, 'Black Friday');
    const posts = [{ folder_id: f1.id, caption: 'Fresh at 4am 🥐' },
                   { folder_id: f2.id, caption: 'BF20 for 20% off', captions: { instagram: 'BF20 for 20% off #bakery' }, at: '2027-01-15T18:00' }];
    const pre = (await tool(h, 'schedule_posts', { posts })).data;
    expect(pre).toMatchObject({ preview: true, ok: true, mode: 'drafts_for_approval', posts: 2, publishes: 4 });
    expect(pre.plan[0].posts.map(p => p.platform).sort()).toEqual(['instagram', 'tiktok']);
    expect(pre.plan[1].when.local).toBe('2027-01-15T18:00+01:00');
    expect(pre.plan[1].posts.find(p => p.platform === 'instagram').caption).toBe('BF20 for 20% off #bakery');
    expect(await env.DB.prepare('SELECT COUNT(*) AS n FROM posts').first('n')).toBe(0);

    const made = (await tool(h, 'schedule_posts', { posts, confirm: true })).data;
    expect(made.failed).toEqual([]);
    expect(made.made).toHaveLength(4);
    expect(made.made.every(m => m.status === 'draft')).toBe(true);
    const rows = (await env.DB.prepare('SELECT * FROM posts ORDER BY scheduled_at').all()).results;
    expect(rows.every(r => r.batch_id === made.batch_id && r.source === 'ai' && r.status === 'draft')).toBe(true);
    expect(rows.at(-1).scheduled_at).toBe(parseWhen('2027-01-15T18:00', 'Europe/Prague'));
    expect(rows[0].scheduled_at).toBe(pre.plan[0].when.at);
    expect((await tool(h, 'list_folders', { brand: 'Bakery' })).data.folders.every(x => x.status === 'awaiting_approval')).toBe(true);

    // The next plan does not take a slot the drafts hold.
    const again = (await tool(h, 'schedule_posts', { posts: [{ folder_id: f1.id, caption: 'x' }] })).data;
    expect(again.plan[0].when.at).not.toBe(pre.plan[0].when.at);

    const listed = (await tool(h, 'list_posts', { brand: 'Bakery', to: '2027-02-01T00:00' })).data.posts;
    expect(listed).toHaveLength(4);
    expect(listed.every(p => p.status === 'awaiting_approval' && p.by_ai)).toBe(true);

    // A person approves the TikTok one with a privacy choice.
    const tt = rows.find(r => r.account_id === 'acc_tt');
    const ap = await callWorker(`/v1/posts/${tt.id}/approve`, { method: 'POST', headers: { Authorization: h.Authorization }, body: { privacy_level: 'PUBLIC_TO_EVERYONE' } });
    expect(ap.status).toBe(200);
    expect(await ap.json()).toMatchObject({ status: 'queued', scheduled_at: tt.scheduled_at });

    const undo = (await tool(h, 'undo_batch', { batch_id: made.batch_id })).data;
    expect(undo.undone).toBe(4);
    const left = (await env.DB.prepare(`SELECT status, COUNT(*) AS n FROM posts GROUP BY status`).all()).results;
    expect(left).toEqual([{ status: 'cancelled', n: 1 }]);
  });

  it('with approval off, schedules directly and needs a TikTok privacy choice', async () => {
    const { h } = await workspace({ review: false });
    const f = await folderWithPhotos(h, 'Cookies');
    const noPrivacy = (await tool(h, 'schedule_posts', { posts: [{ folder_id: f.id, caption: 'hi' }], confirm: true })).data;
    expect(noPrivacy.preview).toBe(true);
    expect(noPrivacy.ok).toBe(false);
    expect(noPrivacy.plan[0].errors[0]).toMatch(/tiktok.*Choose who can view/i);

    const ok = (await tool(h, 'schedule_posts', { posts: [{ folder_id: f.id, caption: 'hi', tiktok: { privacy_level: 'PUBLIC_TO_EVERYONE' } }], confirm: true })).data;
    expect(ok.mode).toBe('scheduled');
    expect(ok.made.map(m => m.status)).toEqual(['queued', 'queued']);
    expect((await tool(h, 'list_folders', {})).data.folders[0].status).toBe('scheduled');
  });

  it('records the folder a post made in the app came from, and shows where drafts came from', async () => {
    const { h } = await workspace({ review: false });
    const key = { Authorization: h.Authorization.replace('Bearer', 'Key') };
    const f = await folderWithPhotos(h, 'Manual', 1);
    const copy = await (await callWorker('/v1/media/copy', { method: 'POST', headers: key, body: { keys: [f.items?.[0]?.key || (await tool(h, 'list_folders', {})).data.folders[0].items[0].key] } })).json();
    const res = await callWorker('/v1/posts', { method: 'POST', headers: key, body: { account_id: 'acc_ig', image_keys: [copy.media[0].key], caption: 'x',
      scheduled_at: Math.floor(Date.now() / 1000) + 3600, folder_id: f.id } });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ folder_id: f.id, source: null });
    expect((await tool(h, 'list_folders', {})).data.folders[0].status).toBe('scheduled');
    const bad = await callWorker('/v1/posts', { method: 'POST', headers: key, body: { account_id: 'acc_ig', image_keys: [copy.media[0].key], caption: 'x', folder_id: 'fld_nope' } });
    expect((await bad.json()).error).toMatch(/folder no longer exists/);
  });

  it('refuses Instagram for PNG photos and reports an empty folder', async () => {
    const { h } = await workspace();
    const png = await folderWithPhotos(h, 'PNGs', 1, PNG_B64);
    const empty = (await tool(h, 'create_folder', { name: 'Empty', brand: 'Bakery' })).data;
    const r = (await tool(h, 'schedule_posts', { posts: [{ folder_id: png.id, caption: 'a' }, { folder_id: empty.id, caption: 'b' }] })).data;
    expect(r.ok).toBe(false);
    expect(r.plan[0].errors.join(' ')).toMatch(/Instagram only accepts JPG/);
    expect(r.plan[1].errors).toEqual(['Folder "Empty" is empty']);
    const tiktokOnly = (await tool(h, 'schedule_posts', { posts: [{ folder_id: png.id, caption: 'a', platforms: ['tiktok'] }] })).data;
    expect(tiktokOnly.ok).toBe(true);
  });

  it('finds free slots from posting times in the workspace zone', async () => {
    const { h } = await workspace();
    const s = (await tool(h, 'find_slots', { brand: 'Bakery', count: 4 })).data;
    expect(s.timezone).toBe('Europe/Prague');
    expect(s.slots).toHaveLength(4);
    expect(s.slots.every(x => /T(09|18):00\+0[12]:00$/.test(x.local))).toBe(true);
  });

  it('turns the approval setting on and off', async () => {
    const { h } = await workspace();
    const key = { Authorization: h.Authorization.replace('Bearer', 'Key') };
    expect((await callWorker('/v1/workspace', { method: 'PATCH', headers: key, body: { ai_review: false } })).status).toBe(200);
    expect((await (await callWorker('/v1/me', { headers: key })).json()).ai_review).toBe(false);
    expect((await tool(h, 'get_overview')).data.approval).toMatch(/^off/);
  });
});

describe('upload links (files on the person\'s computer)', () => {
  beforeEach(() => resetDb(env));
  const JPEG = Uint8Array.from(atob(JPEG_B64), ch => ch.charCodeAt(0));
  const MP4 = new Uint8Array([0, 0, 0, 0x18, 0x66, 0x74, 0x79, 0x70, 0x69, 0x73, 0x6f, 0x6d, 1, 2, 3, 4]);
  const put = (url, bytes, type) => callWorker(new URL(url).pathname, { method: 'PUT',
    headers: { 'Content-Type': type, 'Content-Length': String(bytes.length) }, body: bytes });

  it('puts photos into the folder in the asked order, each link once, with a curl command', async () => {
    const { h } = await workspace();
    const f = (await tool(h, 'create_folder', { name: 'Slides', brand: 'bakery' })).data;
    const r = await tool(h, 'get_upload_links', { folder_id: f.id, files: [1, 2, 3].map(i => ({ filename: `slide-${i}.jpg`, content_type: 'image/jpeg', bytes: JPEG.length })) });
    expect(r.data.links).toHaveLength(3);
    expect(r.data.links[0].curl).toContain("-H 'Content-Type: image/jpeg'");
    // Uploaded out of order, they still land in the order asked for.
    for (const i of [2, 0, 1]) expect((await put(r.data.links[i].upload_url, JPEG, 'image/jpeg')).status).toBe(200);
    expect((await put(r.data.links[0].upload_url, JPEG, 'image/jpeg')).status).toBe(409);
    const [folder] = (await tool(h, 'list_folders', {})).data.folders;
    expect(folder.items.map(x => x.name)).toEqual(['slide-1.jpg', 'slide-2.jpg', 'slide-3.jpg']);
  });

  it('refuses a different size, type or content than the link was made for', async () => {
    const { h } = await workspace();
    const f = (await tool(h, 'create_folder', { name: 'Slides', brand: 'bakery' })).data;
    const [a, b, c] = (await tool(h, 'get_upload_links', { folder_id: f.id, files: [1, 2, 3].map(i => ({ filename: `${i}.jpg`, content_type: 'image/jpeg', bytes: JPEG.length })) })).data.links;
    expect((await put(a.upload_url, new Uint8Array([...JPEG, 9]), 'image/jpeg')).status).toBe(400);
    expect((await put(b.upload_url, JPEG, 'image/png')).status).toBe(400);
    expect((await put(c.upload_url, new Uint8Array(JPEG.length).fill(7), 'image/jpeg')).status).toBe(400);
    expect((await put(a.upload_url.replace(/.$/, ch => (ch === 'x' ? 'y' : 'x')), JPEG, 'image/jpeg')).status).toBe(403);
    expect((await tool(h, 'list_folders', {})).data.folders[0].items).toEqual([]);
  });

  it('keeps photos and a video apart, and checks the limits up front', async () => {
    const { h } = await workspace();
    const f = (await tool(h, 'create_folder', { name: 'Clip', brand: 'bakery' })).data;
    expect((await tool(h, 'get_upload_links', { folder_id: f.id, files: [{ filename: 'a.mp4', content_type: 'video/mp4', bytes: 10 }, { filename: 'b.jpg', content_type: 'image/jpeg', bytes: 10 }] })).error).toMatch(/one video/);
    const big = (await tool(h, 'get_upload_links', { folder_id: f.id, files: [{ filename: 'huge.jpg', content_type: 'image/jpeg', bytes: 50 * 1048576 }] })).data.links[0];
    expect(big.ok).toBe(false);
    const v = (await tool(h, 'get_upload_links', { folder_id: f.id, files: [{ filename: 'clip.mp4', content_type: 'video/mp4', bytes: MP4.length }] })).data.links[0];
    expect((await put(v.upload_url, MP4, 'video/mp4')).status).toBe(200);
    const late = (await tool(h, 'get_upload_links', { folder_id: f.id, files: [{ filename: 'x.jpg', content_type: 'image/jpeg', bytes: JPEG.length }] })).data.links[0];
    expect(late.ok).toBe(false);
    expect((await tool(h, 'get_upload_links', { folder_id: 'fld_nope', files: [{ filename: 'x.jpg', content_type: 'image/jpeg', bytes: 4 }] })).error).toMatch(/not found/i);
  });
});
