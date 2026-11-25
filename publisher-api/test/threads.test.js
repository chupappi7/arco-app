import { env as baseEnv } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk, signUp } from './helpers.js';
import { thIntake } from '../src/auth.js';
import { refreshInstagramTokens } from '../src/accounts.js';
import { createPost } from '../src/posts.js';
import { tick } from '../src/publisher.js';
import { refreshStats } from '../src/stats.js';
import { decrypt } from '../src/crypto.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/threads/callback';
const T = 1_800_000_000;

function fakeMeta(overrides = {}) {
  const calls = [];
  let n = 0;
  return {
    calls,
    thExchangeCode: async a => { calls.push(['thExchangeCode', a]); return { access_token: 'th-short', user_id: 'th-1' }; },
    thLongLived: async () => ({ access_token: 'th-long', expires_in: 5184000 }),
    thMe: async () => ({ id: 'th-1', username: 'arco.app', name: 'ARCO', threads_profile_picture_url: 'https://th/a.jpg' }),
    thRefresh: async () => ({ access_token: 'th-renewed', expires_in: 5184000 }),
    thItem: async (...a) => { calls.push(['thItem', ...a]); return { id: `item-${++n}` }; },
    thCarousel: async (...a) => { calls.push(['thCarousel', ...a]); return { id: 'carousel-1' }; },
    thContainerStatus: async () => ({ status: 'FINISHED' }),
    thPublish: async (...a) => { calls.push(['thPublish', ...a]); return { id: 'thmedia-1' }; },
    thPermalink: async () => ({ permalink: 'https://www.threads.net/@arco.app/post/abc' }),
    thMediaStats: async () => ({ data: [{ name: 'views', values: [{ value: 420 }] }, { name: 'likes', values: [{ value: 12 }] },
      { name: 'replies', values: [{ value: 3 }] }, { name: 'reposts', values: [{ value: 2 }] }, { name: 'quotes', values: [{ value: 1 }] }] }),
    thAccountStats: async () => ({ data: [{ name: 'followers_count', total_value: { value: 87 } }] }),
    ...overrides,
  };
}

const withMeta = mt => ({ ...baseEnv, __meta: mt });
const thIn = async (mt, session_id) => thIntake(withMeta(mt), mt, { code: 'c#_', redirect_uri: RU, session_id: session_id ?? (await signUp(baseEnv)).sid });
const account = () => baseEnv.DB.prepare(`SELECT * FROM accounts WHERE platform = 'threads'`).first();

async function upload(ws, n, type = 'image/jpeg') {
  const keys = [];
  for (let i = 0; i < n; i++) {
    const key = `${ws}/img-${i}-${Math.random().toString(16).slice(2)}.${type === 'image/png' ? 'png' : 'jpg'}`;
    await baseEnv.MEDIA.put(key, new Uint8Array([0xff, 0xd8, 0xff, i]), { httpMetadata: { contentType: type } });
    await baseEnv.DB.prepare('INSERT INTO media (key, workspace_id, bytes, content_type, created_at) VALUES (?, ?, 4, ?, ?)')
      .bind(key, ws, type, T).run();
    keys.push(key);
  }
  return keys;
}

describe('threads login', () => {
  beforeEach(() => resetDb(baseEnv));

  it('connects the Threads profile with a 60-day token, and renews it', async () => {
    const mt = fakeMeta();
    const r = await thIn(mt);
    expect(mt.calls[0][1].code).toBe('c');            // the '#_' suffix is stripped
    const th = await account();
    expect(th).toMatchObject({ open_id: 'th:th-1', username: 'arco.app', avatar_url: 'https://th/a.jpg' });
    expect(await decrypt(th.access_token_enc, baseEnv.TOKEN_KEY)).toBe('th-long');
    const again = await thIn(fakeMeta(), r.session_id);
    expect(again.account_ids).toEqual(r.account_ids);
    const t = Math.floor(Date.now() / 1000) + 45 * 86400;
    expect(await refreshInstagramTokens(baseEnv, fakeMeta(), t)).toBe(1);
    expect(await decrypt((await account()).access_token_enc, baseEnv.TOKEN_KEY)).toBe('th-renewed');
  });
});

describe('threads posts', () => {
  let ws;
  beforeEach(async () => {
    await resetDb(baseEnv);
    ws = (await thIn(fakeMeta())).workspace_id;
  });
  const make = async (n = 3, extra = {}) => createPost(baseEnv, fakeTk(), ws, { account_id: (await account()).id,
    image_keys: await upload(ws, n, extra.type), caption: 'hello', scheduled_at: null, ...extra });

  it('holds posts to 500 characters and 20 photos, JPG or PNG', async () => {
    await expect(make(1, { caption: 'x'.repeat(501) })).rejects.toThrow(/500/);
    await expect(make(21)).rejects.toThrow(/at most 20/);
    expect((await make(2, { type: 'image/png' })).platform).toBe('threads');
  });

  it('publishes a carousel: items, carousel, then publish once processed', async () => {
    const p = await make(3);
    const mt = fakeMeta();
    await tick(withMeta(mt), fakeTk(), T + 10);
    const row = await baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('published');
    expect(row.post_url).toBe('https://www.threads.net/@arco.app/post/abc');
    expect(mt.calls.filter(c => c[0] === 'thItem')).toHaveLength(3);
    expect(mt.calls.find(c => c[0] === 'thItem')[3]).toMatchObject({ carouselItem: true });
    expect(mt.calls.find(c => c[0] === 'thCarousel')[4]).toBe('hello');
    expect(mt.calls.filter(c => c[0] === 'thPublish')).toHaveLength(1);
  });

  it('a single photo is one post with its text', async () => {
    await make(1);
    const mt = fakeMeta();
    await tick(withMeta(mt), fakeTk(), T + 10);
    expect(mt.calls.find(c => c[0] === 'thItem')[3]).toMatchObject({ text: 'hello' });
    expect(mt.calls.some(c => c[0] === 'thCarousel')).toBe(false);
  });

  it('fails with Threads\' reason when it cannot process the media', async () => {
    const p = await make(1);
    await tick(withMeta(fakeMeta({ thContainerStatus: async () => ({ status: 'ERROR', error_message: 'FAILED_DOWNLOADING_IMAGE' }) })), fakeTk(), T + 10);
    const row = await baseEnv.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(p.id).first();
    expect(row.status).toBe('failed');
    expect(row.fail_reason).toMatch(/Threads could not process the images: FAILED_DOWNLOADING_IMAGE/);
  });

  it('reads views, likes, replies and reposts, and followers', async () => {
    const p = await make(1);
    const mt = fakeMeta();
    await tick(withMeta(mt), fakeTk(), T + 10);
    await refreshStats(withMeta(mt), mt, fakeTk(), Math.floor(Date.now() / 1000) + 3600);
    const row = await baseEnv.DB.prepare('SELECT stats FROM posts WHERE id = ?').bind(p.id).first();
    expect(JSON.parse(row.stats)).toMatchObject({ views: 420, likes: 12, comments: 3, shares: 3 });
    expect((await account()).followers).toBe(87);
  });
});
