import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk } from './helpers.js';
import { metaIntake, igIntake, createSession } from '../src/auth.js';
import { refreshInstagramTokens } from '../src/accounts.js';
import { claimDue } from '../src/publisher.js';
import { createPost } from '../src/posts.js';
import { tick, publishNow } from '../src/publisher.js';
import { copyMedia } from '../src/media.js';
import { decrypt } from '../src/crypto.js';
import { MetaError } from '../src/meta.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/meta/callback';
const IGRU = 'https://arco-publisher.vercel.app/api/auth/instagram/callback';
const T = 1_800_000_000;

function fakeMeta(overrides = {}) {
  const calls = [];
  const rec = name => async (...a) => { calls.push([name, ...a]); return {}; };
  let n = 0;
  const m = {
    calls,
    exchangeCode: async () => ({ access_token: 'short' }),
    longLived: async () => ({ access_token: 'long' }),
    me: async () => ({ id: 'fbuser-1', name: 'Pat' }),
    pages: async () => ({ data: [{ id: 'page-1', name: 'ARCO', access_token: 'page-token',
      picture: { data: { url: 'https://fb/p.jpg' } } }] }),
    igExchangeCode: async () => ({ access_token: 'ig-short', user_id: 'ig-1' }),
    igLongLived: async () => ({ access_token: 'ig-long', expires_in: 5184000 }),
    igMe: async () => ({ id: 'app-scoped-9', user_id: 'ig-1', username: 'arco.app', name: 'ARCO', profile_picture_url: 'https://ig/a.jpg' }),
    igRefresh: async () => ({ access_token: 'ig-renewed', expires_in: 5184000 }),
    igImage: async (...a) => { calls.push(['igImage', ...a]); return { id: `child-${++n}` }; },
    igCarousel: async (...a) => { calls.push(['igCarousel', ...a]); return { id: 'carousel-1' }; },
    igContainerStatus: async () => ({ status_code: 'FINISHED' }),
    igPublish: async (...a) => { calls.push(['igPublish', ...a]); return { id: 'igmedia-1' }; },
    igPermalink: async () => ({ permalink: 'https://www.instagram.com/p/abc/' }),
    fbPhoto: async (...a) => { calls.push(['fbPhoto', ...a]); return { id: `photo-${++n}`, post_id: 'page-1_single' }; },
    fbFeed: async (...a) => { calls.push(['fbFeed', ...a]); return { id: 'page-1_multi' }; },
    ...overrides,
  };
  return m;
}

const withMeta = mt => ({ ...baseEnv, __meta: mt });
const intake = (mt, extra = {}) => metaIntake(withMeta(mt), mt, { code: 'c', redirect_uri: RU, ...extra });
const igIn = (mt, extra = {}) => igIntake(withMeta(mt), mt, { code: 'c#_', redirect_uri: IGRU, ...extra });

async function account(platform) {
  return baseEnv.DB.prepare('SELECT * FROM accounts WHERE platform = ?').bind(platform).first();
}

async function upload(env, ws, n, type = 'image/jpeg') {
  const keys = [];
  for (let i = 0; i < n; i++) {
    const key = `${ws}/img-${i}-${Math.random().toString(16).slice(2)}.${type === 'image/png' ? 'png' : 'jpg'}`;
    await env.MEDIA.put(key, new Uint8Array([0xff, 0xd8, 0xff, i]), { httpMetadata: { contentType: type } });
    await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at) VALUES (?, ?, 4, ?, ?)`)
      .bind(key, ws, type, T).run();
    keys.push(key);
  }
  return keys;
}

describe('facebook login', () => {
  beforeEach(() => resetDb(baseEnv));

  it('connects the picked Pages into a new workspace', async () => {
    const r = await intake(fakeMeta());
    expect(r.workspace_id).toMatch(/^ws_/);
    expect(r.account_ids).toHaveLength(1);
    const fb = await account('facebook');
    expect(fb.open_id).toBe('fb:page-1');
    expect(await decrypt(fb.access_token_enc, baseEnv.TOKEN_KEY)).toBe('page-token');
    expect(fb.access_token_enc).not.toContain('page-token');
  });

  it('a second manager of the same Page cannot sign into the first one\'s workspace', async () => {
    await intake(fakeMeta());
    await expect(intake(fakeMeta({ me: async () => ({ id: 'fbuser-2', name: 'Someone else' }) })))
      .rejects.toThrow(/already connected to another/);
  });

  it('signing in again lands in the same workspace and updates the token', async () => {
    const a = await intake(fakeMeta());
    const b = await intake(fakeMeta({ pages: async () => ({ data: [{ id: 'page-1', name: 'ARCO', access_token: 'new-token' }] }),
      me: async () => ({ id: 'fbuser-1' }) }));
    expect(b.workspace_id).toBe(a.workspace_id);
    expect(await decrypt((await account('facebook')).access_token_enc, baseEnv.TOKEN_KEY)).toBe('new-token');
  });

  it('adds to the signed-in workspace', async () => {
    await baseEnv.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?)').bind('ws_tt', T).run();
    const sid = await createSession(baseEnv, 'ws_tt');
    const r = await intake(fakeMeta(), { session_id: sid });
    expect(r.workspace_id).toBe('ws_tt');
    expect(r.session_id).toBe(sid);
  });

  it('refuses when no Page was picked', async () => {
    await expect(intake(fakeMeta({ pages: async () => ({ data: [] }) }))).rejects.toThrow(/No Facebook Page/);
  });

  it('refuses a redirect_uri it does not know', async () => {
    await expect(intake(fakeMeta(), { redirect_uri: 'https://evil.test/cb' })).rejects.toThrow(/redirect_uri/);
  });
});

describe('instagram login', () => {
  beforeEach(() => resetDb(baseEnv));

  it('connects the Instagram account itself, with a 60-day token, keyed by its professional id', async () => {
    let code;
    const r = await igIn(fakeMeta({ igExchangeCode: async a => { code = a.code; return { access_token: 's', user_id: 'ig-1' }; } }));
    expect(code).toBe('c');                       // the '#_' suffix is stripped
    const ig = await account('instagram');
    expect(ig.open_id).toBe('ig:ig-1');
    expect(ig.username).toBe('arco.app');
    expect(await decrypt(ig.access_token_enc, baseEnv.TOKEN_KEY)).toBe('ig-long');
    expect(ig.access_expires_at).toBeGreaterThan(Date.now() / 1000 + 59 * 86400);
    const again = await igIn(fakeMeta());
    expect(again.workspace_id).toBe(r.workspace_id);
  });

  it('adds a second Instagram account to the signed-in workspace', async () => {
    const a = await igIn(fakeMeta());
    const b = await igIn(fakeMeta({ igMe: async () => ({ user_id: 'ig-2', username: 'arco.focus' }) }), { session_id: a.session_id });
    expect(b.workspace_id).toBe(a.workspace_id);
    const { n } = await baseEnv.DB.prepare(`SELECT COUNT(*) AS n FROM accounts WHERE platform = 'instagram'`).first();
    expect(n).toBe(2);
  });

  it('an account added to someone else\'s workspace cannot be used to sign into it', async () => {
    const agency = await intake(fakeMeta());                       // the agency signs in with Facebook
    await igIn(fakeMeta(), { session_id: agency.session_id });      // and adds the client's Instagram
    await expect(igIn(fakeMeta())).rejects.toThrow(/someone else/); // the client signs in with it
  });

  it('renews tokens nearing expiry and marks revoked ones for reconnect', async () => {
    await igIn(fakeMeta());
    const t = Math.floor(Date.now() / 1000) + 45 * 86400;   // 15 days left
    expect(await refreshInstagramTokens(baseEnv, fakeMeta(), t)).toBe(1);
    const ig = await account('instagram');
    expect(await decrypt(ig.access_token_enc, baseEnv.TOKEN_KEY)).toBe('ig-renewed');
    await baseEnv.DB.prepare('UPDATE accounts SET access_expires_at = ?, token_updated_at = 0').bind(t + 86400).run();
    await refreshInstagramTokens(baseEnv, fakeMeta({ igRefresh: async () => { throw new MetaError('x', { code: 'needs_reconnect' }); } }), t);
    expect((await account('instagram')).needs_reconnect).toBe(1);
  });
});

describe('instagram and facebook posts', () => {
  let ws;
  beforeEach(async () => {
    await resetDb(baseEnv);
    ws = (await intake(fakeMeta())).workspace_id;
    const sid = await createSession(baseEnv, ws);
    await igIn(fakeMeta(), { session_id: sid });
  });

  const make = async (platform, extra = {}) => {
    const acc = await account(platform);
    return createPost(baseEnv, fakeTk(), ws, { account_id: acc.id, image_keys: await upload(baseEnv, ws, 3),
      caption: 'hello #focus', scheduled_at: null, ...extra });
  };

  it('needs no TikTok privacy settings', async () => {
    const p = await make('instagram');
    expect(p.platform).toBe('instagram');
    expect(p.settings).toEqual({});
  });

  it('holds Instagram to 10 images, JPEG, and its caption limits', async () => {
    const acc = await account('instagram');
    await expect(createPost(baseEnv, fakeTk(), ws, { account_id: acc.id, image_keys: await upload(baseEnv, ws, 11) }))
      .rejects.toThrow(/at most 10/);
    await expect(createPost(baseEnv, fakeTk(), ws, { account_id: acc.id, image_keys: await upload(baseEnv, ws, 1, 'image/png') }))
      .rejects.toThrow(/JPG/);
    await expect(make('instagram', { caption: 'x'.repeat(2201) })).rejects.toThrow(/2200/);
    await expect(make('instagram', { caption: Array.from({ length: 31 }, (_, i) => `#t${i}`).join(' ') }))
      .rejects.toThrow(/30 hashtags/);
  });

  it('publishes an Instagram carousel: containers, then publish once processed', async () => {
    const p = await make('instagram');
    const mt = fakeMeta();
    await tick(withMeta(mt), fakeTk(), T + 10);
    let row = await baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('published');   // start + poll run in the same tick
    expect(row.post_url).toBe('https://www.instagram.com/p/abc/');
    expect(mt.calls.filter(c => c[0] === 'igImage')).toHaveLength(3);
    expect(mt.calls.find(c => c[0] === 'igImage')[2]).toBe('ig-1');
    expect(mt.calls.find(c => c[0] === 'igCarousel')[4]).toBe('hello #focus');
    expect(mt.calls.filter(c => c[0] === 'igPublish')).toHaveLength(1);
  });

  it('waits while Instagram is still processing, and never publishes twice', async () => {
    const p = await make('instagram');
    let status = 'IN_PROGRESS';
    const mt = fakeMeta({ igContainerStatus: async () => ({ status_code: status }) });
    await tick(withMeta(mt), fakeTk(), T + 10);
    expect((await baseEnv.DB.prepare('SELECT publish_id FROM posts WHERE id = ?').bind(p.id).first()).publish_id)
      .toBe('ig:carousel-1');
    status = 'FINISHED';
    await Promise.all([tick(withMeta(mt), fakeTk(), T + 70), tick(withMeta(mt), fakeTk(), T + 70)]);
    expect(mt.calls.filter(c => c[0] === 'igPublish')).toHaveLength(1);
  });

  it('fails without retry when Instagram rejects the images', async () => {
    const p = await make('instagram');
    await tick(withMeta(fakeMeta({ igContainerStatus: async () => ({ status_code: 'ERROR', status: 'bad ratio' }) })), fakeTk(), T + 10);
    const row = await baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('failed');
    expect(row.fail_reason).toMatch(/bad ratio/);
    expect(row.publish_id).toBeNull();     // nothing went live, so Retry is allowed
  });

  it('posts several photos to a Facebook Page as one post', async () => {
    const p = await make('facebook');
    const mt = fakeMeta();
    expect(await publishNow(withMeta(mt), fakeTk(), p.id)).toBe('published');
    const row = await baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.post_url).toBe('https://www.facebook.com/page-1_multi');
    expect(mt.calls.filter(c => c[0] === 'fbPhoto').every(c => c[4].published === false)).toBe(true);
    expect(mt.calls.find(c => c[0] === 'fbFeed')[4]).toHaveLength(3);
  });

  it('a revoked token marks the account for reconnect and fails its queue', async () => {
    const p = await make('facebook');
    const mt = fakeMeta({ fbPhoto: async () => { throw new MetaError('Reconnect this account', { code: 'needs_reconnect' }); } });
    await tick(withMeta(mt), fakeTk(), T + 10);
    expect((await account('facebook')).needs_reconnect).toBe(1);
    expect((await baseEnv.DB.prepare('SELECT status FROM posts WHERE id = ?').bind(p.id).first()).status).toBe('failed');
  });

  it('retries a transient Facebook error before posting', async () => {
    const p = await make('facebook');
    const mt = fakeMeta({ fbPhoto: async () => { throw new MetaError('rate limited', { code: '4', transient: true }); } });
    await tick(withMeta(mt), fakeTk(), T + 10);
    const row = await baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('queued');
    expect(row.next_attempt_at).toBeGreaterThan(T + 10);
  });

  it('copies images so the same photos can go to another post', async () => {
    const p = await make('facebook');
    const { media } = await copyMedia(baseEnv, ws, p.image_keys);
    expect(media).toHaveLength(3);
    expect(media[0].key).not.toBe(p.image_keys[0]);
    const q = await createPost(baseEnv, fakeTk(), ws, { account_id: (await account('instagram')).id,
      image_keys: media.map(m => m.key), caption: 'same photos' });
    expect(q.image_keys).toHaveLength(3);
  });
});

describe('tick budget', () => {
  beforeEach(() => resetDb(baseEnv));

  it('starts only what fits in one tick and leaves the rest queued', async () => {
    const ws = (await igIn(fakeMeta())).workspace_id;
    const acc = await account('instagram');
    // 10 posts x 10 images = 11 calls each; the start budget fits 3.
    for (let i = 0; i < 10; i++) {
      await createPost(baseEnv, fakeTk(), ws, { account_id: acc.id, image_keys: await upload(baseEnv, ws, 10), caption: `p${i}` });
    }
    const mt = fakeMeta();
    await tick(withMeta(mt), fakeTk(), T + 10);
    const { n } = await baseEnv.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE status = 'queued'`).first();
    expect(n).toBe(7);
    expect(mt.calls.filter(c => c[0] === 'igCarousel')).toHaveLength(3);
  });
});

describe('fairness', () => {
  beforeEach(() => resetDb(baseEnv));

  it('one workspace with a big queue cannot hold back another', async () => {
    for (const ws of ['ws_big', 'ws_small']) {
      await baseEnv.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?)').bind(ws, T).run();
      const n = ws === 'ws_big' ? 40 : 1;
      for (let i = 0; i < n; i++) {
        await baseEnv.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings,
            scheduled_at, next_attempt_at, created_at, updated_at) VALUES (?, ?, 'acc', 'queued', '[]', '{}', ?, ?, ?, ?)`)
          .bind(`${ws}_${i}`, ws, T - 100 + (ws === 'ws_big' ? 0 : 50), T - 100 + (ws === 'ws_big' ? 0 : 50), T, T).run();
      }
    }
    const got = await claimDue(baseEnv, T);
    expect(got.some(p => p.workspace_id === 'ws_small')).toBe(true);
    expect(got.filter(p => p.workspace_id === 'ws_big').length).toBeLessThanOrEqual(5);
  });

  it('a post bigger than the whole tick budget still goes out on its own', async () => {
    const ws = (await intake(fakeMeta())).workspace_id;
    const acc = await account('facebook');
    const p = await createPost(baseEnv, fakeTk(), ws, { account_id: acc.id, image_keys: await upload(baseEnv, ws, 35), caption: 'big' });
    await tick(withMeta(fakeMeta()), fakeTk(), T + 10);
    expect((await baseEnv.DB.prepare('SELECT status FROM posts WHERE id = ?').bind(p.id).first()).status).toBe('published');
  });
});
