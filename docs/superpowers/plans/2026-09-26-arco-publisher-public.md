# ARCO Publisher (public) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn ARCO Publisher into a free, public TikTok photo-post scheduler (sign in with TikTok, upload your own photos, post now or schedule), with ARCO's local dashboard as one API client, so the Direct Post audit application is true.

**Architecture:** A new Cloudflare Worker `arco-publisher-api` owns all state (D1 for workspaces/accounts/sessions/posts/media, R2 for images) and runs a per-minute cron that publishes due posts. The Vercel site `arco-publisher.vercel.app` stays the front door: static pages, the OAuth start/callback (the live app's only redirect URI), and `vercel.json` rewrites that send `/api/v1/*` and `/media/*` straight to the Worker, so the session cookie and the TikTok-verified image domain both stay on `arco-publisher.vercel.app`. The dashboard calls the same API with an API key.

**Tech Stack:** Cloudflare Workers (ES modules, plain JavaScript), D1, R2, Wrangler 4, Vitest with `@cloudflare/vitest-pool-workers`; Vercel Node functions (existing `publisher/`); vanilla HTML/JS pages; Python 3 stdlib in `tools/dashboard.py`.

**Spec:** `docs/superpowers/specs/2026-09-26-arco-publisher-public-design.md`

## Global Constraints

- Photo posts only: `media_type: PHOTO`, `post_mode: DIRECT_POST`, `source: PULL_FROM_URL`, 1–35 images, JPG or PNG.
- Title ≤ 90 characters, caption ≤ 4000 characters (count code points: `[...s].length`).
- Image URLs TikTok pulls: `https://arco-publisher.vercel.app/media/<key>` only (the verified URL prefix is `https://arco-publisher.vercel.app/`).
- Redirect URI stays `https://arco-publisher.vercel.app/api/auth/callback`. No change to the live TikTok app.
- Scopes requested: `user.info.basic,video.publish,video.upload`.
- Privacy dropdown has no default; options come only from `creator_info.privacy_level_options`. Branded content may not be `SELF_ONLY`.
- Scheduled time at least 5 minutes ahead; store and compare as UTC epoch seconds.
- Limits: 10 accounts and 30 queued posts per workspace; 35 images per post; 5 MB per image; 200 MB stored per workspace.
- Retention: images deleted 7 days after their post reaches `published`, `failed` or `cancelled`; images never attached to a post deleted after 24 hours. Delete workspace removes everything at once.
- Refresh tokens encrypted with AES-GCM (key from Worker secret `TOKEN_KEY`); API keys and session ids stored only as SHA-256 hex.
- At most 5 TikTok requests per account per cron tick (TikTok allows 6/min per token).
- Never add a watermark or alter uploaded images server-side.
- Secrets never committed: `.dev.vars`, `.env*`, `.wrangler/` are gitignored.
- Commit messages end with the two attribution lines:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH`.

## Deviations from the spec (decided while planning)

- No server-side drafts. A post row is created only on **Post now** or **Schedule**; uploaded images that never join a post are deleted after 24 hours. The spec's "drafts untouched for 30 days" rule is therefore unnecessary.
- "Edit" a queued post = cancel it and open the composer prefilled with the same images and settings. No PATCH endpoint.
- Publishing is split across ticks: a tick sends `content/init` and stores `publish_id` (status `publishing`); later ticks poll `status/fetch` until terminal. Nothing waits inside one tick.

## Review Focus

1. **Two overlapping cron ticks** must never publish the same post twice — claim is a single conditional `UPDATE`; test calls claim twice and expects one row. (Task 6)
2. **A revoked TikTok authorization** between scheduling and firing must fail that account's posts with "Reconnect this account" and mark the account `needs_reconnect`, without touching other accounts. (Task 6)
3. **Creator privacy options change** after scheduling (e.g. account went private): the post fails with the reason instead of posting with a now-invalid privacy. (Task 6)
4. **Time zones**: a creator in UTC+7 picks 19:00 local; the API receives UTC epoch seconds and the calendar shows 19:00 local again; times under 5 minutes ahead are rejected with a message. (Tasks 5, 10)
5. **Images TikTok can't fetch**: served with the right `Content-Type`, not deleted while their post is `queued`/`publishing`, and uploads that are not JPG/PNG or over 5 MB rejected with 400 before storage. (Tasks 4, 7)

---

## File Structure

```
publisher-api/                      NEW — the Cloudflare Worker
  package.json                      scripts: test, deploy, db:migrate
  wrangler.toml                     D1 binding DB, R2 binding MEDIA, cron * * * * *
  vitest.config.js                  pool-workers config
  schema.sql                        all tables
  .gitignore                        .dev.vars, .wrangler/, node_modules/
  src/index.js                      fetch router + scheduled()
  src/http.js                       json(), error(), readJson(), route matching
  src/crypto.js                     randomToken, sha256Hex, encrypt, decrypt
  src/tiktok.js                     TikTok HTTP client (injectable fetch)
  src/auth.js                       oauth intake, sessions, api keys, resolveCaller
  src/accounts.js                   list, disconnect, creator-info
  src/media.js                      upload, serve, usage
  src/posts.js                      validate, create, list, cancel, retry
  src/publisher.js                  cron: claim, init, poll, retry policy
  src/cleanup.js                    retention + deleteWorkspace
  src/limits.js                     every limit constant
  test/helpers.js                   applySchema, seedWorkspace, fakeTikTok
  test/*.test.js                    one per src module

publisher/                          EXISTING — Vercel site
  vercel.json                       MODIFY: rewrites to the Worker
  api/_lib.js                       MODIFY: SCOPE unchanged; add workerFetch()
  api/auth/start.js                 MODIFY: ?add=1 support
  api/auth/callback.js              MODIFY: hand code to Worker, set tt_sid
  api/auth/logout.js                MODIFY: clear tt_sid, tell Worker
  api/creator-info.js, publish.js, status.js, drafts.js   DELETE (replaced by Worker)
  public/index.html                 REWRITE: product page (no tool on it)
  public/app.html                   NEW: the web app (compose, calendar, settings)
  public/app.js                     NEW: web app logic
  public/privacy.html, terms.html   MODIFY: match stored data and retention

tools/dashboard.py                  MODIFY: publish/schedule via the API, calendar
tools/pubapi.py                     NEW: tiny stdlib client for the Worker API
tools/test_pubapi.py                NEW: unittest for pubapi with a fake server
```

### Task 1: Worker scaffold, schema, crypto

**Files:**
- Create: `publisher-api/package.json`, `publisher-api/wrangler.toml`, `publisher-api/vitest.config.js`, `publisher-api/.gitignore`, `publisher-api/schema.sql`, `publisher-api/src/crypto.js`, `publisher-api/src/limits.js`, `publisher-api/test/helpers.js`
- Test: `publisher-api/test/crypto.test.js`

**Interfaces:**
- Produces: `randomToken(prefix = '', bytes = 32): string` (hex), `sha256Hex(text): Promise<string>`, `encrypt(plain, keyB64): Promise<string>` (format `v1.<iv>.<ct>` base64url), `decrypt(token, keyB64): Promise<string>`; `applySchema(env): Promise<void>` in test helpers; all tables in `schema.sql`; limit constants in `src/limits.js`.

- [ ] **Step 1: Create the package and config files**

`publisher-api/package.json`:
```json
{
  "name": "arco-publisher-api",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "deploy": "wrangler deploy",
    "db:migrate": "wrangler d1 execute arco-publisher --remote --file=schema.sql"
  },
  "devDependencies": {
    "@cloudflare/vitest-pool-workers": "^0.8.0",
    "vitest": "~3.2.0",
    "wrangler": "^4.0.0"
  }
}
```

`publisher-api/wrangler.toml` (the `database_id` is replaced with the real one in Task 8; tests run on a local D1 and accept any id):
```toml
name = "arco-publisher-api"
main = "src/index.js"
compatibility_date = "2026-09-01"
compatibility_flags = ["nodejs_compat"]

[vars]
PUBLIC_ORIGIN = "https://arco-publisher.vercel.app"
REDIRECT_URI = "https://arco-publisher.vercel.app/api/auth/callback"

[[d1_databases]]
binding = "DB"
database_name = "arco-publisher"
database_id = "local-dev"

[[r2_buckets]]
binding = "MEDIA"
bucket_name = "arco-publisher-media"

# Every minute: publish what is due, poll what is publishing, clean up.
[triggers]
crons = ["* * * * *"]
```

`publisher-api/vitest.config.js`:
```js
import { defineWorkersConfig } from '@cloudflare/vitest-pool-workers/config';

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: './wrangler.toml' },
        miniflare: {
          bindings: {
            // 32 bytes, base64: "0123456789abcdef0123456789abcdef"
            TOKEN_KEY: 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=',
            INTERNAL_SECRET: 'test-internal-secret',
            TIKTOK_CLIENT_KEY: 'test-client-key',
            TIKTOK_CLIENT_SECRET: 'test-client-secret',
          },
        },
      },
    },
  },
});
```

`publisher-api/.gitignore`:
```
node_modules/
.wrangler/
.dev.vars
```

- [ ] **Step 2: Install dependencies**

Run: `cd publisher-api && npm install`
Expected: installs without peer-dependency errors. If npm reports a vitest peer conflict, run `npm view @cloudflare/vitest-pool-workers peerDependencies` and pin `vitest` to the range it lists, then install again. If the installed pool-workers major no longer exports `defineWorkersConfig`, follow its README's config example; the bindings object stays the same.

- [ ] **Step 3: Write the schema**

`publisher-api/schema.sql`:
```sql
CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL,
  api_key_hash TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS workspaces_api_key ON workspaces(api_key_hash);

CREATE TABLE IF NOT EXISTS accounts (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  open_id TEXT NOT NULL UNIQUE,
  username TEXT NOT NULL DEFAULT '',
  display_name TEXT NOT NULL DEFAULT '',
  avatar_url TEXT NOT NULL DEFAULT '',
  refresh_token_enc TEXT NOT NULL,
  needs_reconnect INTEGER NOT NULL DEFAULT 0,
  connected_at INTEGER NOT NULL,
  token_updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS accounts_ws ON accounts(workspace_id);

CREATE TABLE IF NOT EXISTS sessions (
  id_hash TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS media (
  key TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  content_type TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  post_id TEXT,
  delete_after INTEGER
);
CREATE INDEX IF NOT EXISTS media_ws ON media(workspace_id);
CREATE INDEX IF NOT EXISTS media_delete ON media(delete_after);

CREATE TABLE IF NOT EXISTS posts (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  caption TEXT NOT NULL DEFAULT '',
  image_keys TEXT NOT NULL,
  cover_index INTEGER NOT NULL DEFAULT 0,
  settings TEXT NOT NULL,
  scheduled_at INTEGER NOT NULL,
  next_attempt_at INTEGER NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  publish_id TEXT,
  public_post_id TEXT,
  fail_reason TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS posts_due ON posts(status, next_attempt_at);
CREATE INDEX IF NOT EXISTS posts_ws ON posts(workspace_id, scheduled_at);
```

- [ ] **Step 4: Write limits**

`publisher-api/src/limits.js`:
```js
export const MAX_ACCOUNTS = 10;
export const MAX_QUEUED = 30;
export const MAX_IMAGES = 35;
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const MAX_WORKSPACE_BYTES = 200 * 1024 * 1024;
export const MIN_LEAD_SECONDS = 5 * 60;
export const KEEP_AFTER_DONE = 7 * 86400;
export const KEEP_UNATTACHED = 86400;
export const SESSION_TTL = 30 * 86400;
export const RETRY_DELAYS = [60, 300, 600]; // seconds before retries 1, 2, 3
export const PER_ACCOUNT_PER_TICK = 5;
export const PUBLISH_TIMEOUT = 3600;
export const PRIVACY = ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR', 'SELF_ONLY'];
```

- [ ] **Step 5: Write the failing crypto tests and the test helpers**

`publisher-api/test/helpers.js`:
```js
// Applies schema.sql to the test D1. Statements are split on ";" at line end.
import schema from '../schema.sql?raw';

export async function applySchema(env) {
  const statements = schema.split(/;\s*$/m).map(s => s.trim()).filter(Boolean);
  for (const sql of statements) await env.DB.prepare(sql).run();
}
```

`publisher-api/test/crypto.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect } from 'vitest';
import { randomToken, sha256Hex, encrypt, decrypt } from '../src/crypto.js';

describe('crypto', () => {
  it('sha256Hex matches the standard vector', async () => {
    expect(await sha256Hex('abc')).toBe(
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  });

  it('randomToken has the prefix and 2 hex chars per byte', () => {
    const t = randomToken('apk_', 16);
    expect(t).toMatch(/^apk_[0-9a-f]{32}$/);
    expect(randomToken('apk_', 16)).not.toBe(t);
  });

  it('encrypt/decrypt round-trips and never repeats ciphertext', async () => {
    const a = await encrypt('rft.secret', env.TOKEN_KEY);
    const b = await encrypt('rft.secret', env.TOKEN_KEY);
    expect(a).not.toBe(b);
    expect(a.startsWith('v1.')).toBe(true);
    expect(await decrypt(a, env.TOKEN_KEY)).toBe('rft.secret');
  });

  it('decrypt rejects tampered ciphertext', async () => {
    const a = await encrypt('rft.secret', env.TOKEN_KEY);
    const [v, iv, ct] = a.split('.');
    const flipped = ct.slice(0, -2) + (ct.slice(-2) === 'AA' ? 'AB' : 'AA');
    await expect(decrypt([v, iv, flipped].join('.'), env.TOKEN_KEY)).rejects.toThrow();
  });
});
```

- [ ] **Step 6: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/crypto.test.js`
Expected: FAIL — cannot resolve `../src/crypto.js`.

- [ ] **Step 7: Implement crypto**

`publisher-api/src/crypto.js`:
```js
const enc = new TextEncoder();
const dec = new TextDecoder();

const hex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
const b64url = buf => btoa(String.fromCharCode(...new Uint8Array(buf)))
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const fromB64url = s => Uint8Array.from(
  atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)),
  c => c.charCodeAt(0));

export function randomToken(prefix = '', bytes = 32) {
  return prefix + hex(crypto.getRandomValues(new Uint8Array(bytes)));
}

export async function sha256Hex(text) {
  return hex(await crypto.subtle.digest('SHA-256', enc.encode(text)));
}

async function aesKey(keyB64) {
  const raw = Uint8Array.from(atob(keyB64), c => c.charCodeAt(0));
  if (raw.length !== 32) throw new Error('TOKEN_KEY must be 32 bytes, base64');
  return crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt', 'decrypt']);
}

export async function encrypt(plain, keyB64) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, await aesKey(keyB64), enc.encode(plain));
  return `v1.${b64url(iv)}.${b64url(ct)}`;
}

export async function decrypt(token, keyB64) {
  const [v, iv, ct] = String(token).split('.');
  if (v !== 'v1' || !iv || !ct) throw new Error('unrecognised token format');
  const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: fromB64url(iv) }, await aesKey(keyB64), fromB64url(ct));
  return dec.decode(pt);
}
```

- [ ] **Step 8: Run to verify pass**

Run: `cd publisher-api && npx vitest run test/crypto.test.js`
Expected: 4 passed.

- [ ] **Step 9: Commit**

```bash
git add publisher-api/package.json publisher-api/package-lock.json publisher-api/wrangler.toml \
  publisher-api/vitest.config.js publisher-api/.gitignore publisher-api/schema.sql \
  publisher-api/src/crypto.js publisher-api/src/limits.js publisher-api/test/helpers.js \
  publisher-api/test/crypto.test.js
git commit -m "publisher-api: scaffold, schema, token crypto

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---

### Task 2: TikTok client

**Files:**
- Create: `publisher-api/src/tiktok.js`
- Test: `publisher-api/test/tiktok.test.js`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class TikTokError extends Error { code: string; httpStatus: number; transient: boolean }`
  - `tiktok({ clientKey, clientSecret, fetch }) → { exchangeCode({ code, codeVerifier, redirectUri }), refresh(refreshToken), creatorInfo(accessToken), initPhoto(accessToken, body), status(accessToken, publishId) }`
    - `exchangeCode` / `refresh` resolve `{ access_token, refresh_token, open_id, scope, expires_in, refresh_expires_in }`
    - `creatorInfo` resolves TikTok's `data` object (`creator_username`, `creator_nickname`, `creator_avatar_url`, `privacy_level_options`, `comment_disabled`, …)
    - `initPhoto` resolves `{ publish_id }`
    - `status` resolves `{ status, fail_reason, publicaly_available_post_id }`
  - `makeTikTok(env) → tiktok(...)` using `env.TIKTOK_CLIENT_KEY`, `env.TIKTOK_CLIENT_SECRET`, global `fetch`
  - `buildPhotoBody({ title, caption, imageUrls, coverIndex, settings }) → object` (the `content/init` JSON body)

- [ ] **Step 1: Write the failing tests**

`publisher-api/test/tiktok.test.js`:
```js
import { describe, it, expect } from 'vitest';
import { tiktok, buildPhotoBody, TikTokError } from '../src/tiktok.js';

function fakeFetch(responses) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url: String(url), init });
    const r = responses.shift();
    return new Response(JSON.stringify(r.body), { status: r.status ?? 200 });
  };
  fn.calls = calls;
  return fn;
}

describe('tiktok client', () => {
  it('exchangeCode posts form fields and returns tokens', async () => {
    const f = fakeFetch([{ body: { access_token: 'at', refresh_token: 'rt', open_id: 'o1',
      scope: 'user.info.basic,video.publish', expires_in: 86400, refresh_expires_in: 31536000 } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const t = await tk.exchangeCode({ code: 'c', codeVerifier: 'v', redirectUri: 'https://x/cb' });
    expect(t.open_id).toBe('o1');
    const body = new URLSearchParams(f.calls[0].init.body);
    expect(body.get('grant_type')).toBe('authorization_code');
    expect(body.get('code_verifier')).toBe('v');
    expect(body.get('client_key')).toBe('ck');
  });

  it('refresh maps invalid_grant to a non-transient needs_reconnect error', async () => {
    const f = fakeFetch([{ status: 400, body: { error: 'invalid_grant', error_description: 'Refresh token is invalid or expired.' } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const err = await tk.refresh('rt').catch(e => e);
    expect(err).toBeInstanceOf(TikTokError);
    expect(err.code).toBe('needs_reconnect');
    expect(err.transient).toBe(false);
  });

  it('v2 envelope errors carry the code and mark internal_error transient', async () => {
    const f = fakeFetch([{ body: { data: {}, error: { code: 'internal_error', message: 'boom', log_id: 'L' } } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const err = await tk.creatorInfo('at').catch(e => e);
    expect(err.code).toBe('internal_error');
    expect(err.transient).toBe(true);
  });

  it('HTTP 5xx and 429 are transient', async () => {
    const f = fakeFetch([{ status: 503, body: {} }, { status: 429, body: {} }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    expect((await tk.creatorInfo('at').catch(e => e)).transient).toBe(true);
    expect((await tk.status('at', 'p1').catch(e => e)).transient).toBe(true);
  });

  it('initPhoto sends the bearer token and returns publish_id', async () => {
    const f = fakeFetch([{ body: { data: { publish_id: 'p_123' }, error: { code: 'ok' } } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const r = await tk.initPhoto('at', { any: 1 });
    expect(r.publish_id).toBe('p_123');
    expect(f.calls[0].init.headers.Authorization).toBe('Bearer at');
  });

  it('buildPhotoBody produces a DIRECT_POST PHOTO PULL_FROM_URL body', () => {
    const b = buildPhotoBody({
      title: 't', caption: 'c', imageUrls: ['https://a/1.jpg', 'https://a/2.jpg'], coverIndex: 1,
      settings: { privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: true, auto_add_music: false,
                  brand_organic: true, branded_content: false },
    });
    expect(b).toEqual({
      media_type: 'PHOTO', post_mode: 'DIRECT_POST',
      post_info: { title: 't', description: 'c', privacy_level: 'PUBLIC_TO_EVERYONE',
        disable_comment: true, auto_add_music: false,
        brand_organic_toggle: true, brand_content_toggle: false },
      source_info: { source: 'PULL_FROM_URL', photo_images: ['https://a/1.jpg', 'https://a/2.jpg'],
        photo_cover_index: 1 },
    });
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/tiktok.test.js`
Expected: FAIL — cannot resolve `../src/tiktok.js`.

- [ ] **Step 3: Implement**

`publisher-api/src/tiktok.js`:
```js
const OAUTH_TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/';
const CREATOR_INFO_URL = 'https://open.tiktokapis.com/v2/post/publish/creator_info/query/';
const CONTENT_INIT_URL = 'https://open.tiktokapis.com/v2/post/publish/content/init/';
const STATUS_URL = 'https://open.tiktokapis.com/v2/post/publish/status/fetch/';

const TRANSIENT_CODES = new Set(['internal_error', 'rate_limit_exceeded']);

export class TikTokError extends Error {
  constructor(message, { code = 'unknown', httpStatus = 0, transient = false } = {}) {
    super(message);
    this.code = code;
    this.httpStatus = httpStatus;
    this.transient = transient;
  }
}

async function readBody(res) {
  const text = await res.text();
  try { return JSON.parse(text); } catch { return {}; }
}

function httpFailure(res, body, label) {
  const transient = res.status >= 500 || res.status === 429;
  const code = body?.error?.code || body?.error || `http_${res.status}`;
  const msg = body?.error?.message || body?.error_description || `HTTP ${res.status}`;
  return new TikTokError(`${label}: ${msg}`, { code: String(code), httpStatus: res.status, transient });
}

export function tiktok({ clientKey, clientSecret, fetch }) {
  async function oauth(params, label) {
    const res = await fetch(OAUTH_TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ client_key: clientKey, client_secret: clientSecret, ...params }).toString(),
    });
    const body = await readBody(res);
    if (body.error === 'invalid_grant') {
      throw new TikTokError('Reconnect this account', { code: 'needs_reconnect', httpStatus: res.status });
    }
    if (!res.ok || body.error || !body.access_token) throw httpFailure(res, body, label);
    return body;
  }

  async function v2(url, accessToken, payload, label) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json; charset=UTF-8' },
      body: payload === undefined ? undefined : JSON.stringify(payload),
    });
    const body = await readBody(res);
    if (!res.ok) throw httpFailure(res, body, label);
    const code = body?.error?.code;
    if (code && code !== 'ok') {
      if (code === 'access_token_invalid') {
        throw new TikTokError('Reconnect this account', { code: 'needs_reconnect', httpStatus: res.status });
      }
      throw new TikTokError(`${label}: ${body.error.message || code}`,
        { code, httpStatus: res.status, transient: TRANSIENT_CODES.has(code) });
    }
    return body.data || {};
  }

  return {
    exchangeCode: ({ code, codeVerifier, redirectUri }) => oauth(
      { code, grant_type: 'authorization_code', redirect_uri: redirectUri, code_verifier: codeVerifier },
      'code exchange'),
    refresh: refreshToken => oauth({ grant_type: 'refresh_token', refresh_token: refreshToken }, 'token refresh'),
    creatorInfo: accessToken => v2(CREATOR_INFO_URL, accessToken, undefined, 'creator info'),
    initPhoto: (accessToken, body) => v2(CONTENT_INIT_URL, accessToken, body, 'content init'),
    status: (accessToken, publishId) => v2(STATUS_URL, accessToken, { publish_id: publishId }, 'status fetch'),
  };
}

export const makeTikTok = env => tiktok({
  clientKey: env.TIKTOK_CLIENT_KEY, clientSecret: env.TIKTOK_CLIENT_SECRET, fetch: (...a) => fetch(...a),
});

export function buildPhotoBody({ title, caption, imageUrls, coverIndex, settings }) {
  return {
    media_type: 'PHOTO',
    post_mode: 'DIRECT_POST',
    post_info: {
      title,
      description: caption,
      privacy_level: settings.privacy_level,
      disable_comment: !!settings.disable_comment,
      auto_add_music: !!settings.auto_add_music,
      brand_organic_toggle: !!settings.brand_organic,
      brand_content_toggle: !!settings.branded_content,
    },
    source_info: { source: 'PULL_FROM_URL', photo_images: imageUrls, photo_cover_index: coverIndex },
  };
}
```

- [ ] **Step 4: Run to verify pass**

Run: `cd publisher-api && npx vitest run test/tiktok.test.js`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add publisher-api/src/tiktok.js publisher-api/test/tiktok.test.js
git commit -m "publisher-api: TikTok client with transient/needs-reconnect errors

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 3: HTTP router, sign-in intake, sessions, API keys, accounts

**Files:**
- Create: `publisher-api/src/http.js`, `publisher-api/src/auth.js`, `publisher-api/src/accounts.js`, `publisher-api/src/index.js`
- Modify: `publisher-api/src/tiktok.js` (add `tkFor`)
- Test: `publisher-api/test/auth.test.js`, `publisher-api/test/routes.test.js`
- Modify: `publisher-api/test/helpers.js` (add `fakeTk`, `callWorker`)

**Interfaces:**
- Consumes: `randomToken`, `sha256Hex`, `encrypt`, `decrypt` (Task 1); `makeTikTok`, `TikTokError` (Task 2); limits (Task 1).
- Produces:
  - `http.js`: `json(data, status = 200, headers = {}) → Response`, `class HttpError(status, message, code?)`, `readJson(req) → Promise<object>`, `match(pattern, path) → params | null`, `cookie(req, name) → string | null`, `now() → number` (epoch seconds)
  - `tiktok.js`: `tkFor(env)` → `env.__tk` if present (tests), else `makeTikTok(env)`
  - `auth.js`: `oauthIntake(env, tk, { code, code_verifier, redirect_uri, session_id? }) → { session_id, workspace_id, account_id }`, `createSession(env, ws) → string`, `sessionWorkspace(env, sessionId) → ws | null`, `resolveCaller(env, req) → { workspaceId, via: 'session' | 'key' } | null`, `rotateApiKey(env, ws) → 'apk_…'`, `logout(env, req)`
  - `accounts.js`: `listAccounts(env, ws) → [{ id, username, display_name, avatar_url, needs_reconnect }]`, `getAccount(env, ws, id) → row` (404 if not in ws), `accessTokenFor(env, tk, accountRow) → accessToken` (stores rotated refresh token; on revoked token sets `needs_reconnect=1` and rethrows), `creatorInfoFor(env, tk, ws, id) → creator_info data`, `disconnect(env, ws, id)`
  - `index.js`: default export `{ fetch, scheduled }`; `ROUTES` array of `[method, pattern, handler, access]` where access is `'public' | 'internal' | 'user'` and handler is `(req, env, { ws, params, url, tk }) → Response`
  - Worker routes after this task: `POST /internal/oauth`, `GET /v1/me`, `POST /v1/logout`, `POST /v1/api-key`, `GET /v1/accounts`, `DELETE /v1/accounts/:id`, `GET /v1/accounts/:id/creator-info`

- [ ] **Step 1: Write `http.js`**

`publisher-api/src/http.js`:
```js
export const now = () => Math.floor(Date.now() / 1000);

export class HttpError extends Error {
  constructor(status, message, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers },
  });
}

export async function readJson(req) {
  try { return await req.json(); } catch { throw new HttpError(400, 'Request body must be JSON'); }
}

export function match(pattern, path) {
  const p = pattern.split('/'), a = path.split('/');
  if (p.length !== a.length) return null;
  const params = {};
  for (let i = 0; i < p.length; i++) {
    if (p[i].startsWith(':')) params[p[i].slice(1)] = decodeURIComponent(a[i]);
    else if (p[i] !== a[i]) return null;
  }
  return params;
}

export function cookie(req, name) {
  const header = req.headers.get('Cookie') || '';
  for (const part of header.split(';')) {
    const i = part.indexOf('=');
    if (i > 0 && part.slice(0, i).trim() === name) return decodeURIComponent(part.slice(i + 1).trim());
  }
  return null;
}
```

- [ ] **Step 2: Add `tkFor` to `tiktok.js`**

Append to `publisher-api/src/tiktok.js`:
```js
// Tests put a fake client on env.__tk; production builds a real one.
export const tkFor = env => env.__tk || makeTikTok(env);
```

- [ ] **Step 3: Extend the test helpers**

Append to `publisher-api/test/helpers.js`:
```js
import { env as baseEnv, createExecutionContext, waitOnExecutionContext } from 'cloudflare:test';
import worker from '../src/index.js';

// A TikTok client double. Override any method per test.
export function fakeTk(overrides = {}) {
  let n = 0;
  return {
    exchangeCode: async () => ({ access_token: 'at', refresh_token: 'rt-1', open_id: 'open-1',
      scope: 'user.info.basic,video.publish,video.upload', expires_in: 86400, refresh_expires_in: 31536000 }),
    refresh: async () => ({ access_token: `at-${++n}`, refresh_token: 'rt-1' }),
    creatorInfo: async () => ({ creator_username: 'creator', creator_nickname: 'Creator',
      creator_avatar_url: 'https://p16/a.jpg',
      privacy_level_options: ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'SELF_ONLY'],
      comment_disabled: false }),
    initPhoto: async () => ({ publish_id: 'pub-1' }),
    status: async () => ({ status: 'PUBLISH_COMPLETE', publicaly_available_post_id: ['7500000000000000001'] }),
    ...overrides,
  };
}

// Call the Worker's fetch handler with a fake TikTok client injected.
export async function callWorker(path, { method = 'GET', headers = {}, body, tk = fakeTk() } = {}) {
  const init = { method, headers: { ...headers } };
  if (body !== undefined) {
    if (body instanceof Uint8Array || body instanceof ArrayBuffer) init.body = body;
    else { init.body = JSON.stringify(body); init.headers['Content-Type'] = 'application/json'; }
  }
  const ctx = createExecutionContext();
  const res = await worker.fetch(new Request(`https://api.test${path}`, init), { ...baseEnv, __tk: tk }, ctx);
  await waitOnExecutionContext(ctx);
  return res;
}

export async function resetDb(env) {
  await applySchema(env);
  for (const t of ['posts', 'media', 'sessions', 'accounts', 'workspaces']) {
    await env.DB.prepare(`DELETE FROM ${t}`).run();
  }
}
```

- [ ] **Step 4: Write the failing auth tests**

`publisher-api/test/auth.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk } from './helpers.js';
import { oauthIntake, resolveCaller, rotateApiKey } from '../src/auth.js';
import { accessTokenFor } from '../src/accounts.js';
import { decrypt } from '../src/crypto.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const intake = (tk, extra = {}) => oauthIntake(env, tk,
  { code: 'c', code_verifier: 'v', redirect_uri: RU, ...extra });

describe('oauth intake', () => {
  beforeEach(() => resetDb(env));

  it('first sign-in creates a workspace, an account and a session', async () => {
    const r = await intake(fakeTk());
    expect(r.workspace_id).toMatch(/^ws_/);
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(r.account_id).first();
    expect(acc.username).toBe('creator');
    expect(acc.refresh_token_enc).not.toContain('rt-1');
    expect(await decrypt(acc.refresh_token_enc, env.TOKEN_KEY)).toBe('rt-1');
    const caller = await resolveCaller(env, new Request('https://x', { headers: { Cookie: `tt_sid=${r.session_id}` } }));
    expect(caller).toEqual({ workspaceId: r.workspace_id, via: 'session' });
  });

  it('signing in again with the same TikTok account returns the same workspace', async () => {
    const a = await intake(fakeTk());
    const b = await intake(fakeTk());
    expect(b.workspace_id).toBe(a.workspace_id);
    expect(b.account_id).toBe(a.account_id);
  });

  it('Add account attaches a second TikTok account to the current workspace', async () => {
    const a = await intake(fakeTk());
    const b = await intake(fakeTk({ exchangeCode: async () => ({ access_token: 'at2', refresh_token: 'rt-2', open_id: 'open-2' }) }),
      { session_id: a.session_id });
    expect(b.workspace_id).toBe(a.workspace_id);
    const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id=?').bind(a.workspace_id).first();
    expect(n).toBe(2);
  });

  it('refuses to add an account that belongs to another workspace', async () => {
    await intake(fakeTk());                                   // open-1 -> workspace A
    const other = await intake(fakeTk({ exchangeCode: async () => ({ access_token: 'x', refresh_token: 'y', open_id: 'open-9' }) }));
    await expect(intake(fakeTk(), { session_id: other.session_id })).rejects.toMatchObject({ status: 409 });
  });

  it('rejects an unexpected redirect_uri', async () => {
    await expect(oauthIntake(env, fakeTk(), { code: 'c', code_verifier: 'v', redirect_uri: 'https://evil/cb' }))
      .rejects.toMatchObject({ status: 400 });
  });
});

describe('api keys', () => {
  beforeEach(() => resetDb(env));

  it('a rotated key authenticates and the previous key stops working', async () => {
    const { workspace_id } = await intake(fakeTk());
    const k1 = await rotateApiKey(env, workspace_id);
    const k2 = await rotateApiKey(env, workspace_id);
    const req = k => new Request('https://x', { headers: { Authorization: `Key ${k}` } });
    expect(await resolveCaller(env, req(k2))).toEqual({ workspaceId: workspace_id, via: 'key' });
    expect(await resolveCaller(env, req(k1))).toBeNull();
  });
});

describe('accessTokenFor', () => {
  beforeEach(() => resetDb(env));

  it('stores a rotated refresh token', async () => {
    const { account_id } = await intake(fakeTk());
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(account_id).first();
    await accessTokenFor(env, fakeTk({ refresh: async () => ({ access_token: 'new', refresh_token: 'rt-rotated' }) }), acc);
    const after = await env.DB.prepare('SELECT refresh_token_enc FROM accounts WHERE id=?').bind(account_id).first();
    expect(await decrypt(after.refresh_token_enc, env.TOKEN_KEY)).toBe('rt-rotated');
  });

  it('a revoked token flags the account and rethrows', async () => {
    const { account_id } = await intake(fakeTk());
    const acc = await env.DB.prepare('SELECT * FROM accounts WHERE id=?').bind(account_id).first();
    const revoked = fakeTk({ refresh: async () => { const e = new Error('Reconnect this account'); e.code = 'needs_reconnect'; throw e; } });
    await expect(accessTokenFor(env, revoked, acc)).rejects.toMatchObject({ code: 'needs_reconnect' });
    const after = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id=?').bind(account_id).first();
    expect(after.needs_reconnect).toBe(1);
  });
});
```

- [ ] **Step 5: Write the failing route tests**

`publisher-api/test/routes.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker } from './helpers.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';

async function signIn() {
  const res = await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU } });
  return res.json();
}

describe('routes', () => {
  beforeEach(() => resetDb(env));

  it('/internal/oauth requires the internal secret', async () => {
    const res = await callWorker('/internal/oauth', { method: 'POST', body: { code: 'c' } });
    expect(res.status).toBe(403);
  });

  it('/v1/me needs a session or key', async () => {
    expect((await callWorker('/v1/me')).status).toBe(401);
    const s = await signIn();
    const res = await callWorker('/v1/me', { headers: { Cookie: `tt_sid=${s.session_id}` } });
    expect(res.status).toBe(200);
    const me = await res.json();
    expect(me.accounts).toHaveLength(1);
    expect(me.accounts[0].username).toBe('creator');
    expect(me.accounts[0]).not.toHaveProperty('refresh_token_enc');
  });

  it('POST /v1/api-key returns a key that works as Authorization: Key', async () => {
    const s = await signIn();
    const { api_key } = await (await callWorker('/v1/api-key', { method: 'POST',
      headers: { Cookie: `tt_sid=${s.session_id}` } })).json();
    expect(api_key).toMatch(/^apk_/);
    const res = await callWorker('/v1/accounts', { headers: { Authorization: `Key ${api_key}` } });
    expect(res.status).toBe(200);
  });

  it('creator-info for an account in another workspace is 404', async () => {
    const s = await signIn();
    const res = await callWorker('/v1/accounts/acc_nope/creator-info', { headers: { Cookie: `tt_sid=${s.session_id}` } });
    expect(res.status).toBe(404);
  });

  it('unknown paths are 404 JSON', async () => {
    const res = await callWorker('/nope');
    expect(res.status).toBe(404);
    expect((await res.json()).error).toBeTruthy();
  });
});
```

- [ ] **Step 6: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/auth.test.js test/routes.test.js`
Expected: FAIL — cannot resolve `../src/auth.js` / `../src/index.js`.

- [ ] **Step 7: Implement `auth.js`**

`publisher-api/src/auth.js`:
```js
import { randomToken, sha256Hex, encrypt } from './crypto.js';
import { HttpError, now, cookie } from './http.js';
import { MAX_ACCOUNTS, SESSION_TTL } from './limits.js';

export async function createSession(env, workspaceId) {
  const id = randomToken('ses_');
  await env.DB.prepare('INSERT INTO sessions (id_hash, workspace_id, expires_at) VALUES (?, ?, ?)')
    .bind(await sha256Hex(id), workspaceId, now() + SESSION_TTL).run();
  return id;
}

export async function sessionWorkspace(env, sessionId) {
  if (!sessionId) return null;
  const row = await env.DB.prepare('SELECT workspace_id FROM sessions WHERE id_hash = ? AND expires_at > ?')
    .bind(await sha256Hex(sessionId), now()).first();
  return row ? row.workspace_id : null;
}

export async function resolveCaller(env, req) {
  const auth = req.headers.get('Authorization') || '';
  if (auth.startsWith('Key ')) {
    const row = await env.DB.prepare('SELECT id FROM workspaces WHERE api_key_hash = ?')
      .bind(await sha256Hex(auth.slice(4).trim())).first();
    return row ? { workspaceId: row.id, via: 'key' } : null;
  }
  const ws = await sessionWorkspace(env, cookie(req, 'tt_sid'));
  return ws ? { workspaceId: ws, via: 'session' } : null;
}

export async function rotateApiKey(env, workspaceId) {
  const key = randomToken('apk_');
  await env.DB.prepare('UPDATE workspaces SET api_key_hash = ? WHERE id = ?')
    .bind(await sha256Hex(key), workspaceId).run();
  return key;
}

export async function logout(env, req) {
  const id = cookie(req, 'tt_sid');
  if (id) await env.DB.prepare('DELETE FROM sessions WHERE id_hash = ?').bind(await sha256Hex(id)).run();
}

export async function oauthIntake(env, tk, { code, code_verifier, redirect_uri, session_id }) {
  if (!code || !code_verifier) throw new HttpError(400, 'code and code_verifier are required');
  if (redirect_uri !== env.REDIRECT_URI) throw new HttpError(400, 'unexpected redirect_uri');

  const tokens = await tk.exchangeCode({ code, codeVerifier: code_verifier, redirectUri: redirect_uri });
  const info = await tk.creatorInfo(tokens.access_token);
  const t = now();
  const existing = await env.DB.prepare('SELECT id, workspace_id FROM accounts WHERE open_id = ?')
    .bind(tokens.open_id).first();

  let ws = session_id ? await sessionWorkspace(env, session_id) : null;
  const adding = !!ws;
  if (adding) {
    if (existing && existing.workspace_id !== ws) {
      throw new HttpError(409, 'This TikTok account is already connected to another workspace. ' +
        'Sign in with it and disconnect it there first.');
    }
    if (!existing) {
      const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM accounts WHERE workspace_id = ?').bind(ws).first();
      if (n >= MAX_ACCOUNTS) throw new HttpError(409, `A workspace can connect up to ${MAX_ACCOUNTS} accounts.`);
    }
  } else if (existing) {
    ws = existing.workspace_id;
  } else {
    ws = 'ws_' + randomToken('', 8);
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?)').bind(ws, t).run();
  }

  const enc = await encrypt(tokens.refresh_token, env.TOKEN_KEY);
  const profile = [info.creator_username || '', info.creator_nickname || '', info.creator_avatar_url || ''];
  let accountId = existing?.id;
  if (existing) {
    await env.DB.prepare(`UPDATE accounts SET refresh_token_enc = ?, needs_reconnect = 0, username = ?,
        display_name = ?, avatar_url = ?, token_updated_at = ? WHERE id = ?`)
      .bind(enc, ...profile, t, accountId).run();
  } else {
    accountId = 'acc_' + randomToken('', 8);
    await env.DB.prepare(`INSERT INTO accounts (id, workspace_id, open_id, username, display_name, avatar_url,
        refresh_token_enc, connected_at, token_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(accountId, ws, tokens.open_id, ...profile, enc, t, t).run();
  }
  const sessionId = adding ? session_id : await createSession(env, ws);
  return { session_id: sessionId, workspace_id: ws, account_id: accountId };
}
```

- [ ] **Step 8: Implement `accounts.js`**

`publisher-api/src/accounts.js`:
```js
import { decrypt, encrypt } from './crypto.js';
import { HttpError, now } from './http.js';
import { KEEP_AFTER_DONE } from './limits.js';

export async function listAccounts(env, ws) {
  const { results } = await env.DB.prepare(`SELECT id, username, display_name, avatar_url, needs_reconnect
      FROM accounts WHERE workspace_id = ? ORDER BY connected_at`).bind(ws).all();
  return results.map(r => ({ ...r, needs_reconnect: !!r.needs_reconnect }));
}

export async function getAccount(env, ws, id) {
  const row = await env.DB.prepare('SELECT * FROM accounts WHERE id = ? AND workspace_id = ?').bind(id, ws).first();
  if (!row) throw new HttpError(404, 'Account not found');
  return row;
}

export async function accessTokenFor(env, tk, account) {
  const refreshToken = await decrypt(account.refresh_token_enc, env.TOKEN_KEY);
  try {
    const t = await tk.refresh(refreshToken);
    if (t.refresh_token && t.refresh_token !== refreshToken) {
      await env.DB.prepare('UPDATE accounts SET refresh_token_enc = ?, token_updated_at = ? WHERE id = ?')
        .bind(await encrypt(t.refresh_token, env.TOKEN_KEY), now(), account.id).run();
    }
    return t.access_token;
  } catch (err) {
    if (err.code === 'needs_reconnect') {
      await env.DB.prepare('UPDATE accounts SET needs_reconnect = 1 WHERE id = ?').bind(account.id).run();
    }
    throw err;
  }
}

export async function creatorInfoFor(env, tk, ws, id) {
  const account = await getAccount(env, ws, id);
  return tk.creatorInfo(await accessTokenFor(env, tk, account));
}

export async function disconnect(env, ws, id) {
  await getAccount(env, ws, id);
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE media SET delete_after = ? WHERE post_id IN
        (SELECT id FROM posts WHERE account_id = ? AND status IN ('queued', 'publishing'))`).bind(t, id),
    env.DB.prepare(`UPDATE posts SET status = 'cancelled', fail_reason = 'Account disconnected', updated_at = ?
        WHERE account_id = ? AND status IN ('queued', 'publishing')`).bind(t, id),
    env.DB.prepare(`UPDATE media SET delete_after = ? WHERE post_id IN
        (SELECT id FROM posts WHERE account_id = ?) AND delete_after IS NULL`).bind(t + KEEP_AFTER_DONE, id),
    env.DB.prepare('DELETE FROM accounts WHERE id = ?').bind(id),
  ]);
}
```

- [ ] **Step 9: Implement `index.js`**

`publisher-api/src/index.js`:
```js
import { json, HttpError, match, readJson } from './http.js';
import { tkFor, TikTokError } from './tiktok.js';
import { oauthIntake, resolveCaller, rotateApiKey, logout } from './auth.js';
import { listAccounts, creatorInfoFor, disconnect } from './accounts.js';
import * as L from './limits.js';

async function me(req, env, { ws }) {
  const row = await env.DB.prepare('SELECT api_key_hash FROM workspaces WHERE id = ?').bind(ws).first();
  return json({
    workspace_id: ws,
    accounts: await listAccounts(env, ws),
    api_key_set: !!row?.api_key_hash,
    limits: { accounts: L.MAX_ACCOUNTS, queued: L.MAX_QUEUED, images: L.MAX_IMAGES,
              image_bytes: L.MAX_IMAGE_BYTES, workspace_bytes: L.MAX_WORKSPACE_BYTES,
              min_lead_seconds: L.MIN_LEAD_SECONDS },
  });
}

// [method, pattern, handler, access]. Later tasks append to this list.
export const ROUTES = [
  ['POST', '/internal/oauth', async (req, env, { tk }) => json(await oauthIntake(env, tk, await readJson(req))), 'internal'],
  ['GET', '/v1/me', me, 'user'],
  ['POST', '/v1/logout', async (req, env) => { await logout(env, req); return json({ ok: true }); }, 'user'],
  ['POST', '/v1/api-key', async (req, env, { ws }) => json({ api_key: await rotateApiKey(env, ws) }), 'user'],
  ['GET', '/v1/accounts', async (req, env, { ws }) => json({ accounts: await listAccounts(env, ws) }), 'user'],
  ['DELETE', '/v1/accounts/:id', async (req, env, { ws, params }) => { await disconnect(env, ws, params.id); return json({ ok: true }); }, 'user'],
  ['GET', '/v1/accounts/:id/creator-info', async (req, env, { ws, params, tk }) => json(await creatorInfoFor(env, tk, ws, params.id)), 'user'],
];

function sameSecret(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

function toResponse(err) {
  if (err instanceof HttpError) return json({ error: err.message, code: err.code }, err.status);
  if (err instanceof TikTokError || err?.code === 'needs_reconnect') {
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
        const context = { params, url, tk: tkFor(env), ws: null };
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
    // Filled in by Task 6 (publisher) and Task 7 (cleanup).
  },
};
```

- [ ] **Step 10: Run to verify pass**

Run: `cd publisher-api && npx vitest run`
Expected: all tests pass (crypto 4, tiktok 6, auth 8, routes 5).

- [ ] **Step 11: Commit**

```bash
git add publisher-api/src publisher-api/test
git commit -m "publisher-api: sign-in intake, sessions, API keys, accounts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 4: Image upload and public serving

**Files:**
- Create: `publisher-api/src/media.js`
- Modify: `publisher-api/src/index.js` (append routes)
- Test: `publisher-api/test/media.test.js`

**Interfaces:**
- Consumes: `HttpError`, `json`, `now` (Task 3); `randomToken` (Task 1); limits.
- Produces:
  - `uploadMedia(env, ws, req) → { key, url, bytes, content_type }` — body is the raw image; `Content-Type` must be `image/jpeg` or `image/png`
  - `serveMedia(env, key) → Response` (public; 404 when missing)
  - `workspaceBytes(env, ws) → number`
  - `mediaUrl(env, key) → string` = `${env.PUBLIC_ORIGIN}/media/${key}`
  - Keys look like `ws_xxxxxxxxxxxxxxxx/<32 hex>.jpg`
  - Routes: `POST /v1/media` (user), `GET /media/:ws/:file` (public)

- [ ] **Step 1: Write the failing tests**

`publisher-api/test/media.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker } from './helpers.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1, 2, 3, 4]);
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 9]);

async function session() {
  const s = await (await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU } })).json();
  return { Cookie: `tt_sid=${s.session_id}` };
}

describe('media', () => {
  beforeEach(() => resetDb(env));

  it('uploads a JPEG, returns a URL on the verified domain, and serves it', async () => {
    const h = await session();
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG });
    expect(res.status).toBe(200);
    const m = await res.json();
    expect(m.url).toBe(`https://arco-publisher.vercel.app/media/${m.key}`);
    expect(m.key).toMatch(/^ws_[0-9a-f]{16}\/[0-9a-f]{32}\.jpg$/);
    const got = await callWorker(`/media/${m.key}`);
    expect(got.status).toBe(200);
    expect(got.headers.get('Content-Type')).toBe('image/jpeg');
    expect(new Uint8Array(await got.arrayBuffer())).toEqual(JPEG);
  });

  it('accepts PNG and stores .png', async () => {
    const h = await session();
    const m = await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/png' }, body: PNG })).json();
    expect(m.key.endsWith('.png')).toBe(true);
  });

  it('rejects a body whose bytes are not JPEG/PNG even if the header says so', async () => {
    const h = await session();
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' },
      body: new TextEncoder().encode('<html>') });
    expect(res.status).toBe(400);
  });

  it('rejects other content types', async () => {
    const h = await session();
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/gif' }, body: JPEG });
    expect(res.status).toBe(400);
  });

  it('rejects images over 5 MB', async () => {
    const h = await session();
    const big = new Uint8Array(5 * 1024 * 1024 + 1); big.set([0xff, 0xd8, 0xff]);
    const res = await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: big });
    expect(res.status).toBe(400);
  });

  it('new uploads expire in 24 hours until attached to a post', async () => {
    const h = await session();
    const m = await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json();
    const row = await env.DB.prepare('SELECT delete_after, created_at FROM media WHERE key = ?').bind(m.key).first();
    expect(row.delete_after - row.created_at).toBe(86400);
  });

  it('unknown media is 404', async () => {
    expect((await callWorker('/media/ws_x/nope.jpg')).status).toBe(404);
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/media.test.js`
Expected: FAIL — `/v1/media` returns 404 (route missing).

- [ ] **Step 3: Implement `media.js`**

`publisher-api/src/media.js`:
```js
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

export async function serveMedia(env, key) {
  const obj = await env.MEDIA.get(key);
  if (!obj) return new Response('Not found', { status: 404 });
  return new Response(obj.body, {
    headers: {
      'Content-Type': obj.httpMetadata?.contentType || 'application/octet-stream',
      'Cache-Control': 'public, max-age=3600',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
```

- [ ] **Step 4: Add the routes**

In `publisher-api/src/index.js`, add the import:
```js
import { uploadMedia, serveMedia } from './media.js';
```
and append to `ROUTES`:
```js
  ['POST', '/v1/media', async (req, env, { ws }) => json(await uploadMedia(env, ws, req)), 'user'],
  ['GET', '/media/:ws/:file', async (req, env, { params }) => serveMedia(env, `${params.ws}/${params.file}`), 'public'],
```

- [ ] **Step 5: Run to verify pass**

Run: `cd publisher-api && npx vitest run`
Expected: all pass, including 7 media tests.

- [ ] **Step 6: Commit**

```bash
git add publisher-api/src/media.js publisher-api/src/index.js publisher-api/test/media.test.js
git commit -m "publisher-api: image upload with type/size checks and public serving

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---

### Task 5: Posts API

**Files:**
- Create: `publisher-api/src/posts.js`
- Modify: `publisher-api/src/index.js` (append routes)
- Test: `publisher-api/test/posts.test.js`

**Interfaces:**
- Consumes: `getAccount`, `accessTokenFor` (Task 3); `mediaUrl` (Task 4); `HttpError`, `json`, `now`, `readJson`; limits.
- Produces:
  - `validatePost(input, t = now()) → { account_id, title, caption, image_keys, cover_index, settings, scheduled_at }` (throws `HttpError(400)`); `scheduled_at === null` in input means "post now" and becomes `t`
  - `createPost(env, tk, ws, input) → postJson` — images must belong to the workspace and be unattached or attached to a `cancelled`/`failed` post (so Edit can reuse them)
  - `listPosts(env, ws, from, to) → postJson[]` (by `scheduled_at` in `[from, to)`)
  - `cancelPost(env, ws, id) → postJson`, `retryPost(env, ws, id) → postJson`
  - `postJson` shape: `{ id, account_id, username, status, title, caption, images: [url], image_keys, cover_index, settings, scheduled_at, attempts, public_post_id, post_url, fail_reason }` where `post_url` is `https://www.tiktok.com/@<username>/photo/<public_post_id>` when published, else `null`
  - `settings` shape: `{ privacy_level, disable_comment, auto_add_music, brand_organic, branded_content }`
  - Routes: `POST /v1/posts`, `GET /v1/posts?from=&to=`, `DELETE /v1/posts/:id`, `POST /v1/posts/:id/retry`

- [ ] **Step 1: Write the failing tests**

`publisher-api/test/posts.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, callWorker, fakeTk } from './helpers.js';
import { validatePost } from '../src/posts.js';

const RU = 'https://arco-publisher.vercel.app/api/auth/callback';
const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 1]);
const T = 1_800_000_000;
const settings = { privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: false, auto_add_music: false,
                   brand_organic: false, branded_content: false };

async function setup() {
  const s = await (await callWorker('/internal/oauth', { method: 'POST',
    headers: { 'X-Internal-Secret': env.INTERNAL_SECRET },
    body: { code: 'c', code_verifier: 'v', redirect_uri: RU } })).json();
  const h = { Cookie: `tt_sid=${s.session_id}` };
  const up = async () => (await (await callWorker('/v1/media', { method: 'POST',
    headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json()).key;
  return { h, account_id: s.account_id, keys: [await up(), await up()] };
}

describe('validatePost', () => {
  const base = { account_id: 'acc_1', image_keys: ['k1'], settings, title: '', caption: '' };

  it('turns scheduled_at null into now', () => {
    expect(validatePost({ ...base, scheduled_at: null }, T).scheduled_at).toBe(T);
  });
  it('rejects a time under 5 minutes ahead', () => {
    expect(() => validatePost({ ...base, scheduled_at: T + 299 }, T)).toThrow(/5 minutes/);
    expect(validatePost({ ...base, scheduled_at: T + 300 }, T).scheduled_at).toBe(T + 300);
  });
  it('requires a privacy level from the known list', () => {
    expect(() => validatePost({ ...base, settings: { ...settings, privacy_level: '' } }, T)).toThrow(/who can view/i);
  });
  it('refuses branded content set to Only me', () => {
    expect(() => validatePost({ ...base, settings: { ...settings, privacy_level: 'SELF_ONLY', branded_content: true } }, T))
      .toThrow(/Branded content/);
  });
  it('limits images, title and caption, counting emoji as one character', () => {
    expect(() => validatePost({ ...base, image_keys: [] }, T)).toThrow(/at least one/i);
    expect(() => validatePost({ ...base, image_keys: Array(36).fill('k') }, T)).toThrow(/35/);
    expect(validatePost({ ...base, title: '😀'.repeat(90) }, T).title).toHaveLength(180);
    expect(() => validatePost({ ...base, title: 'x'.repeat(91) }, T)).toThrow(/90/);
    expect(() => validatePost({ ...base, caption: 'x'.repeat(4001) }, T)).toThrow(/4000/);
  });
  it('rejects a cover index outside the images', () => {
    expect(() => validatePost({ ...base, cover_index: 1 }, T)).toThrow(/cover/i);
  });
});

describe('posts routes', () => {
  beforeEach(() => resetDb(env));

  it('schedules a post, attaches its images, and lists it', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, cover_index: 0, title: 'T', caption: 'C', settings, scheduled_at: at } });
    expect(res.status).toBe(200);
    const p = await res.json();
    expect(p.status).toBe('queued');
    expect(p.images[0]).toMatch(/^https:\/\/arco-publisher\.vercel\.app\/media\//);
    const m = await env.DB.prepare('SELECT post_id, delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m).toEqual({ post_id: p.id, delete_after: null });
    const list = await (await callWorker(`/v1/posts?from=${at - 10}&to=${at + 10}`, { headers: h })).json();
    expect(list.posts.map(x => x.id)).toEqual([p.id]);
  });

  it('rejects a privacy level the creator does not currently offer', async () => {
    const { h, account_id, keys } = await setup();
    const tk = fakeTk({ creatorInfo: async () => ({ privacy_level_options: ['SELF_ONLY'] }) });
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h, tk,
      body: { account_id, image_keys: keys, settings, scheduled_at: null } });
    expect(res.status).toBe(400);
    expect((await res.json()).error).toMatch(/not available for this account/);
  });

  it('refuses images from another workspace or already used by a post', async () => {
    const a = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    await callWorker('/v1/posts', { method: 'POST', headers: a.h,
      body: { account_id: a.account_id, image_keys: a.keys, settings, scheduled_at: at } });
    const again = await callWorker('/v1/posts', { method: 'POST', headers: a.h,
      body: { account_id: a.account_id, image_keys: a.keys, settings, scheduled_at: at } });
    expect(again.status).toBe(400);
  });

  it('an edited post can reuse the images of a cancelled one', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    await callWorker(`/v1/posts/${p.id}`, { method: 'DELETE', headers: h });
    const again = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at + 60 } });
    expect(again.status).toBe(200);
    const m = await env.DB.prepare('SELECT delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m.delete_after).toBeNull();
  });

  it('cancels a queued post and schedules its images for deletion in 7 days', async () => {
    const { h, account_id, keys } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const p = await (await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: keys, settings, scheduled_at: at } })).json();
    const c = await (await callWorker(`/v1/posts/${p.id}`, { method: 'DELETE', headers: h })).json();
    expect(c.status).toBe('cancelled');
    const m = await env.DB.prepare('SELECT delete_after FROM media WHERE key = ?').bind(keys[0]).first();
    expect(m.delete_after).toBeGreaterThan(Math.floor(Date.now() / 1000) + 6 * 86400);
  });

  it('enforces 30 queued posts per workspace', async () => {
    const { h, account_id } = await setup();
    const at = Math.floor(Date.now() / 1000) + 3600;
    const t = Math.floor(Date.now() / 1000);
    const ws = (await env.DB.prepare('SELECT workspace_id FROM accounts WHERE id = ?').bind(account_id).first()).workspace_id;
    for (let i = 0; i < 30; i++) {
      await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings,
          scheduled_at, next_attempt_at, created_at, updated_at) VALUES (?, ?, ?, 'queued', '[]', '{}', ?, ?, ?, ?)`)
        .bind(`pst_${i}`, ws, account_id, at, at, t, t).run();
    }
    const key = (await (await callWorker('/v1/media', { method: 'POST', headers: { ...h, 'Content-Type': 'image/jpeg' }, body: JPEG })).json()).key;
    const res = await callWorker('/v1/posts', { method: 'POST', headers: h,
      body: { account_id, image_keys: [key], settings, scheduled_at: at } });
    expect(res.status).toBe(409);
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/posts.test.js`
Expected: FAIL — cannot resolve `../src/posts.js`.

- [ ] **Step 3: Implement `posts.js`**

`publisher-api/src/posts.js`:
```js
import { HttpError, now } from './http.js';
import { randomToken } from './crypto.js';
import { getAccount, accessTokenFor } from './accounts.js';
import { mediaUrl } from './media.js';
import { MAX_IMAGES, MAX_QUEUED, MIN_LEAD_SECONDS, KEEP_AFTER_DONE, PRIVACY } from './limits.js';

const len = s => [...String(s ?? '')].length;
const bad = msg => { throw new HttpError(400, msg); };

export function validatePost(input, t = now()) {
  const i = input || {};
  if (typeof i.account_id !== 'string' || !i.account_id) bad('Pick an account');
  const keys = Array.isArray(i.image_keys) ? i.image_keys : [];
  if (keys.length < 1) bad('Add at least one image');
  if (keys.length > MAX_IMAGES) bad(`A photo post can have at most ${MAX_IMAGES} images`);
  if (!keys.every(k => typeof k === 'string' && k)) bad('Image list is invalid');
  const cover = i.cover_index == null ? 0 : Number(i.cover_index);
  if (!Number.isInteger(cover) || cover < 0 || cover >= keys.length) bad('The cover must be one of the images');
  const title = String(i.title ?? ''), caption = String(i.caption ?? '');
  if (len(title) > 90) bad('The title can be at most 90 characters');
  if (len(caption) > 4000) bad('The caption can be at most 4000 characters');
  const s = i.settings || {};
  if (!PRIVACY.includes(s.privacy_level)) bad('Choose who can view this post');
  const settings = {
    privacy_level: s.privacy_level,
    disable_comment: !!s.disable_comment,
    auto_add_music: !!s.auto_add_music,
    brand_organic: !!s.brand_organic,
    branded_content: !!s.branded_content,
  };
  if (settings.branded_content && settings.privacy_level === 'SELF_ONLY') {
    bad('Branded content cannot be posted as Only me');
  }
  let at;
  if (i.scheduled_at === null || i.scheduled_at === undefined) at = t;
  else {
    at = Number(i.scheduled_at);
    if (!Number.isInteger(at)) bad('scheduled_at must be epoch seconds or null');
    if (at < t + MIN_LEAD_SECONDS) bad('Pick a time at least 5 minutes from now');
  }
  return { account_id: i.account_id, title, caption, image_keys: keys, cover_index: cover, settings, scheduled_at: at };
}

export function postJson(env, row) {
  const keys = JSON.parse(row.image_keys);
  return {
    id: row.id, account_id: row.account_id, username: row.username ?? '', status: row.status,
    title: row.title, caption: row.caption, images: keys.map(k => mediaUrl(env, k)), image_keys: keys,
    cover_index: row.cover_index, settings: JSON.parse(row.settings), scheduled_at: row.scheduled_at,
    attempts: row.attempts, public_post_id: row.public_post_id, fail_reason: row.fail_reason,
    post_url: row.status === 'published' && row.public_post_id && row.username
      ? `https://www.tiktok.com/@${row.username}/photo/${row.public_post_id}` : null,
  };
}

async function loadPost(env, ws, id) {
  const row = await env.DB.prepare(`SELECT p.*, a.username FROM posts p LEFT JOIN accounts a ON a.id = p.account_id
      WHERE p.id = ? AND p.workspace_id = ?`).bind(id, ws).first();
  if (!row) throw new HttpError(404, 'Post not found');
  return row;
}

export async function createPost(env, tk, ws, input) {
  const p = validatePost(input);
  const account = await getAccount(env, ws, p.account_id);
  if (account.needs_reconnect) throw new HttpError(409, 'Reconnect this account before posting', 'needs_reconnect');

  const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM posts WHERE workspace_id = ? AND status = 'queued'`).bind(ws).first();
  if (n >= MAX_QUEUED) throw new HttpError(409, `You can have at most ${MAX_QUEUED} posts waiting at a time`);

  const marks = p.image_keys.map(() => '?').join(',');
  // Images may come fresh from upload, or from a cancelled/failed post being
  // edited into a new one. Images of a queued or published post are taken.
  const { results } = await env.DB.prepare(`SELECT key FROM media WHERE workspace_id = ? AND key IN (${marks})
      AND (post_id IS NULL OR post_id IN (SELECT id FROM posts WHERE status IN ('cancelled', 'failed')))`)
    .bind(ws, ...p.image_keys).all();
  if (results.length !== new Set(p.image_keys).size || results.length !== p.image_keys.length) {
    bad('One or more images are missing, already used by another post, or listed twice. Upload them again.');
  }

  // The panel already limits privacy to what TikTok offers; check again here
  // because the API can be called without the panel.
  const info = await tk.creatorInfo(await accessTokenFor(env, tk, account));
  if (!(info.privacy_level_options || []).includes(p.settings.privacy_level)) {
    bad('That privacy level is not available for this account right now');
  }

  const id = 'pst_' + randomToken('', 8), t = now();
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, title, caption, image_keys, cover_index,
        settings, scheduled_at, next_attempt_at, created_at, updated_at)
        VALUES (?, ?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, ws, p.account_id, p.title, p.caption, JSON.stringify(p.image_keys), p.cover_index,
            JSON.stringify(p.settings), p.scheduled_at, p.scheduled_at, t, t),
    env.DB.prepare(`UPDATE media SET post_id = ?, delete_after = NULL WHERE workspace_id = ? AND key IN (${marks})`)
      .bind(id, ws, ...p.image_keys),
  ]);
  return postJson(env, await loadPost(env, ws, id));
}

export async function listPosts(env, ws, from, to) {
  const { results } = await env.DB.prepare(`SELECT p.*, a.username FROM posts p LEFT JOIN accounts a ON a.id = p.account_id
      WHERE p.workspace_id = ? AND p.scheduled_at >= ? AND p.scheduled_at < ? ORDER BY p.scheduled_at`)
    .bind(ws, from, to).all();
  return results.map(r => postJson(env, r));
}

export async function cancelPost(env, ws, id) {
  const row = await loadPost(env, ws, id);
  if (row.status !== 'queued') throw new HttpError(409, 'Only posts that have not started can be cancelled');
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET status = 'cancelled', updated_at = ? WHERE id = ? AND status = 'queued'`).bind(t, id),
    env.DB.prepare('UPDATE media SET delete_after = ? WHERE post_id = ?').bind(t + KEEP_AFTER_DONE, id),
  ]);
  return postJson(env, await loadPost(env, ws, id));
}

export async function retryPost(env, ws, id) {
  const row = await loadPost(env, ws, id);
  if (row.status !== 'failed') throw new HttpError(409, 'Only failed posts can be retried');
  const keys = JSON.parse(row.image_keys);
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM media WHERE post_id = ?').bind(id).first();
  if (n !== keys.length) throw new HttpError(409, 'The images for this post were already deleted. Create it again.');
  const t = now();
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET status = 'queued', attempts = 0, next_attempt_at = ?, fail_reason = NULL,
        publish_id = NULL, updated_at = ? WHERE id = ?`).bind(t, t, id),
    env.DB.prepare('UPDATE media SET delete_after = NULL WHERE post_id = ?').bind(id),
  ]);
  return postJson(env, await loadPost(env, ws, id));
}
```

- [ ] **Step 4: Add the routes**

In `publisher-api/src/index.js`, add the import:
```js
import { createPost, listPosts, cancelPost, retryPost } from './posts.js';
```
and append to `ROUTES`:
```js
  ['POST', '/v1/posts', async (req, env, { ws, tk }) => json(await createPost(env, tk, ws, await readJson(req))), 'user'],
  ['GET', '/v1/posts', async (req, env, { ws, url }) => {
    const from = Number(url.searchParams.get('from')), to = Number(url.searchParams.get('to'));
    if (!Number.isInteger(from) || !Number.isInteger(to) || to <= from || to - from > 62 * 86400) {
      throw new HttpError(400, 'from and to must be epoch seconds, at most 62 days apart');
    }
    return json({ posts: await listPosts(env, ws, from, to) });
  }, 'user'],
  ['DELETE', '/v1/posts/:id', async (req, env, { ws, params }) => json(await cancelPost(env, ws, params.id)), 'user'],
  ['POST', '/v1/posts/:id/retry', async (req, env, { ws, params }) => json(await retryPost(env, ws, params.id)), 'user'],
```

- [ ] **Step 5: Run to verify pass**

Run: `cd publisher-api && npx vitest run`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add publisher-api/src/posts.js publisher-api/src/index.js publisher-api/test/posts.test.js
git commit -m "publisher-api: create, list, cancel and retry posts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 6: The publisher cron

**Files:**
- Create: `publisher-api/src/publisher.js`
- Modify: `publisher-api/src/index.js` (`scheduled` handler)
- Test: `publisher-api/test/publisher.test.js`

**Interfaces:**
- Consumes: `accessTokenFor` (Task 3); `buildPhotoBody`, `tkFor` (Tasks 2–3); `mediaUrl` (Task 4); limits.
- Produces:
  - `claimDue(env, t, limit = 25) → rows` — atomically moves due `queued` posts to `publishing` and returns them
  - `tick(env, tk, t = now()) → { started: n, published: n, failed: n, requeued: n }` — one full pass: recover stuck, claim, init, poll
  - Post status transitions: `queued → publishing (publish_id set) → published | failed`; transient errors: `publishing → queued` with `attempts + 1` and `next_attempt_at = t + RETRY_DELAYS[attempts]`

- [ ] **Step 1: Write the failing tests**

`publisher-api/test/publisher.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb, fakeTk } from './helpers.js';
import { claimDue, tick } from '../src/publisher.js';
import { encrypt } from '../src/crypto.js';
import { TikTokError } from '../src/tiktok.js';

const T = 1_800_000_000;
const settings = JSON.stringify({ privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: false,
  auto_add_music: false, brand_organic: false, branded_content: false });

async function seed({ posts = 1, account = 'acc_1', status = 'queued', at = T } = {}) {
  await env.DB.prepare('INSERT OR IGNORE INTO workspaces (id, created_at) VALUES (?, ?)').bind('ws_1', T).run();
  await env.DB.prepare(`INSERT OR IGNORE INTO accounts (id, workspace_id, open_id, username, refresh_token_enc,
      connected_at, token_updated_at) VALUES (?, 'ws_1', ?, 'creator', ?, ?, ?)`)
    .bind(account, `open-${account}`, await encrypt('rt-1', env.TOKEN_KEY), T, T).run();
  for (let i = 0; i < posts; i++) {
    const id = `pst_${account}_${i}`;
    await env.DB.prepare(`INSERT INTO posts (id, workspace_id, account_id, status, image_keys, settings,
        scheduled_at, next_attempt_at, created_at, updated_at) VALUES (?, 'ws_1', ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, account, status, JSON.stringify([`ws_1/${i}.jpg`]), settings, at, at, T, T).run();
    await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, post_id)
        VALUES (?, 'ws_1', 1, 'image/jpeg', ?, ?)`).bind(`ws_1/${i}.jpg`, T, id).run();
  }
}
const post = id => env.DB.prepare('SELECT * FROM posts WHERE id = ?').bind(id).first();

describe('publisher', () => {
  beforeEach(() => resetDb(env));

  it('claims a due post exactly once across overlapping ticks', async () => {
    await seed();
    const a = await claimDue(env, T);
    const b = await claimDue(env, T);
    expect(a).toHaveLength(1);
    expect(b).toHaveLength(0);
  });

  it('does not claim posts that are not due yet', async () => {
    await seed({ at: T + 60 });
    expect(await claimDue(env, T)).toHaveLength(0);
  });

  it('starts a due post with a PULL_FROM_URL body on the verified domain', async () => {
    await seed();
    let body;
    const tk = fakeTk({ initPhoto: async (at, b) => { body = b; return { publish_id: 'pub-9' }; },
                       status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) });
    await tick(env, tk, T);
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('publishing');
    expect(p.publish_id).toBe('pub-9');
    expect(body.source_info.photo_images).toEqual(['https://arco-publisher.vercel.app/media/ws_1/0.jpg']);
  });

  it('marks published when TikTok confirms and schedules image deletion in 7 days', async () => {
    await seed();
    await tick(env, fakeTk(), T);          // init + first poll in the same tick
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('published');
    expect(p.public_post_id).toBe('7500000000000000001');
    const m = await env.DB.prepare('SELECT delete_after FROM media WHERE post_id = ?').bind(p.id).first();
    expect(m.delete_after).toBe(T + 7 * 86400);
  });

  it('fails instead of posting when the chosen privacy is no longer offered', async () => {
    await seed();
    let inited = false;
    const tk = fakeTk({ creatorInfo: async () => ({ privacy_level_options: ['SELF_ONLY'] }),
                        initPhoto: async () => { inited = true; return { publish_id: 'x' }; } });
    await tick(env, tk, T);
    const p = await post('pst_acc_1_0');
    expect(inited).toBe(false);
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/no longer available/);
  });

  it('retries transient errors after 1, 5 and 10 minutes, then fails', async () => {
    await seed();
    const tk = fakeTk({ initPhoto: async () => { throw new TikTokError('content init: boom', { code: 'internal_error', transient: true }); } });
    await tick(env, tk, T);
    let p = await post('pst_acc_1_0');
    expect([p.status, p.attempts, p.next_attempt_at]).toEqual(['queued', 1, T + 60]);
    await tick(env, tk, T + 60);
    p = await post('pst_acc_1_0');
    expect([p.status, p.attempts, p.next_attempt_at]).toEqual(['queued', 2, T + 60 + 300]);
    await tick(env, tk, T + 360);
    p = await post('pst_acc_1_0');
    expect([p.status, p.attempts, p.next_attempt_at]).toEqual(['queued', 3, T + 360 + 600]);
    await tick(env, tk, T + 960);
    p = await post('pst_acc_1_0');
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/boom/);
  });

  it('a revoked account fails all its queued posts and leaves other accounts alone', async () => {
    await seed({ posts: 2, account: 'acc_1' });
    await seed({ posts: 1, account: 'acc_2' });
    const tk = fakeTk({ refresh: async () => { throw new TikTokError('Reconnect this account', { code: 'needs_reconnect' }); } });
    const ok = fakeTk();
    // acc_1 revoked, acc_2 fine: route by which refresh token is asked for is not possible, so
    // give acc_2 a different token and branch on it.
    await env.DB.prepare('UPDATE accounts SET refresh_token_enc = ? WHERE id = ?')
      .bind(await encrypt('rt-2', env.TOKEN_KEY), 'acc_2').run();
    const mixed = fakeTk({ refresh: async rt => rt === 'rt-2' ? ok.refresh(rt) : tk.refresh(rt) });
    await tick(env, mixed, T);
    expect((await post('pst_acc_1_0')).fail_reason).toBe('Reconnect this account');
    expect((await post('pst_acc_1_1')).status).toBe('failed');
    expect((await post('pst_acc_2_0')).status).toBe('published');
    const a1 = await env.DB.prepare('SELECT needs_reconnect FROM accounts WHERE id = ?').bind('acc_1').first();
    expect(a1.needs_reconnect).toBe(1);
  });

  it('starts at most 5 posts per account per tick and leaves the rest queued', async () => {
    await seed({ posts: 7 });
    await tick(env, fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) }), T);
    const { results } = await env.DB.prepare('SELECT status, COUNT(*) AS n FROM posts GROUP BY status').all();
    expect(Object.fromEntries(results.map(r => [r.status, r.n]))).toEqual({ publishing: 5, queued: 2 });
  });

  it('fails a post TikTok never confirms within an hour', async () => {
    await seed();
    const pending = fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) });
    await tick(env, pending, T);
    await tick(env, pending, T + 3601);
    const p = await post('pst_acc_1_0');
    expect(p.status).toBe('failed');
    expect(p.fail_reason).toMatch(/within an hour/);
  });

  it('puts a post stuck in publishing without a publish_id back in the queue after 10 minutes', async () => {
    await seed({ status: 'publishing' });
    await tick(env, fakeTk({ status: async () => ({ status: 'PROCESSING_DOWNLOAD' }) }), T + 601);
    expect((await post('pst_acc_1_0')).publish_id).toBe('pub-1');   // re-queued, then started again
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/publisher.test.js`
Expected: FAIL — cannot resolve `../src/publisher.js`.

- [ ] **Step 3: Implement `publisher.js`**

`publisher-api/src/publisher.js`:
```js
import { now } from './http.js';
import { accessTokenFor } from './accounts.js';
import { buildPhotoBody } from './tiktok.js';
import { mediaUrl } from './media.js';
import { RETRY_DELAYS, PER_ACCOUNT_PER_TICK, KEEP_AFTER_DONE, PUBLISH_TIMEOUT } from './limits.js';

const STUCK_AFTER = 600;

export async function claimDue(env, t, limit = 25) {
  const { results } = await env.DB.prepare(`UPDATE posts SET status = 'publishing', updated_at = ?
      WHERE status = 'queued' AND id IN (SELECT id FROM posts WHERE status = 'queued' AND next_attempt_at <= ?
        ORDER BY next_attempt_at LIMIT ?)
      RETURNING *`).bind(t, t, limit).all();
  return results;
}

async function finish(env, id, t, fields) {
  const sets = Object.keys(fields).map(k => `${k} = ?`).join(', ');
  await env.DB.batch([
    env.DB.prepare(`UPDATE posts SET ${sets}, updated_at = ? WHERE id = ?`).bind(...Object.values(fields), t, id),
    env.DB.prepare('UPDATE media SET delete_after = ? WHERE post_id = ?').bind(t + KEEP_AFTER_DONE, id),
  ]);
}
const fail = (env, id, t, reason) => finish(env, id, t, { status: 'failed', fail_reason: reason });

// One access token per account per tick; a failure is remembered so the
// account's other posts fail the same way without another refresh.
function tokenCache(env, tk) {
  const cache = new Map();
  return async accountId => {
    if (!cache.has(accountId)) {
      cache.set(accountId, (async () => {
        const account = await env.DB.prepare('SELECT * FROM accounts WHERE id = ?').bind(accountId).first();
        if (!account) { const e = new Error('Account disconnected'); e.code = 'gone'; throw e; }
        return accessTokenFor(env, tk, account);
      })());
    }
    return cache.get(accountId);
  };
}

async function start(env, tk, post, token, t) {
  const settings = JSON.parse(post.settings);
  try {
    const access = await token(post.account_id);
    const info = await tk.creatorInfo(access);
    if (!(info.privacy_level_options || []).includes(settings.privacy_level)) {
      await fail(env, post.id, t, `"${settings.privacy_level}" is no longer available for this account. Edit the post and choose again.`);
      return 'failed';
    }
    if (settings.branded_content && settings.privacy_level === 'SELF_ONLY') {
      await fail(env, post.id, t, 'Branded content cannot be posted as Only me');
      return 'failed';
    }
    const keys = JSON.parse(post.image_keys);
    const { publish_id } = await tk.initPhoto(access, buildPhotoBody({
      title: post.title, caption: post.caption, coverIndex: post.cover_index, settings,
      imageUrls: keys.map(k => mediaUrl(env, k)),
    }));
    await env.DB.prepare(`UPDATE posts SET publish_id = ?, attempts = attempts + 1, fail_reason = NULL, updated_at = ?
        WHERE id = ?`).bind(publish_id, t, post.id).run();
    return 'started';
  } catch (err) {
    if (err.code === 'needs_reconnect') {
      await fail(env, post.id, t, 'Reconnect this account');
      const { results } = await env.DB.prepare(`SELECT id FROM posts WHERE account_id = ? AND status = 'queued'`)
        .bind(post.account_id).all();
      for (const r of results) await fail(env, r.id, t, 'Reconnect this account');
      return 'failed';
    }
    if (err.transient && post.attempts < RETRY_DELAYS.length) {
      await env.DB.prepare(`UPDATE posts SET status = 'queued', attempts = attempts + 1, next_attempt_at = ?,
          fail_reason = ?, updated_at = ? WHERE id = ?`)
        .bind(t + RETRY_DELAYS[post.attempts], `Retrying: ${err.message}`, t, post.id).run();
      return 'requeued';
    }
    await fail(env, post.id, t, err.message || 'Publishing failed');
    return 'failed';
  }
}

async function poll(env, tk, post, token, t) {
  try {
    const s = await tk.status(await token(post.account_id), post.publish_id);
    if (s.status === 'PUBLISH_COMPLETE') {
      const ids = s.publicaly_available_post_id || [];
      await finish(env, post.id, t, { status: 'published', public_post_id: ids[0] ? String(ids[0]) : null });
      return 'published';
    }
    if (s.status === 'FAILED') {
      await fail(env, post.id, t, `TikTok rejected the post: ${s.fail_reason || 'no reason given'}`);
      return 'failed';
    }
  } catch (err) {
    if (!err.transient) { await fail(env, post.id, t, err.message); return 'failed'; }
  }
  if (t - post.updated_at > PUBLISH_TIMEOUT) {
    await fail(env, post.id, t, 'TikTok did not confirm the post within an hour. Check the profile before retrying.');
    return 'failed';
  }
  return 'pending';
}

export async function tick(env, tk, t = now()) {
  const counts = { started: 0, published: 0, failed: 0, requeued: 0 };
  const token = tokenCache(env, tk);

  // Recover posts claimed by a tick that died before sending content/init.
  await env.DB.prepare(`UPDATE posts SET status = 'queued', updated_at = ?
      WHERE status = 'publishing' AND publish_id IS NULL AND updated_at < ?`).bind(t, t - STUCK_AFTER).run();

  const claimed = await claimDue(env, t);
  const perAccount = new Map();
  for (const p of claimed) {
    const n = perAccount.get(p.account_id) || 0;
    if (n >= PER_ACCOUNT_PER_TICK) {
      await env.DB.prepare(`UPDATE posts SET status = 'queued', updated_at = ? WHERE id = ?`).bind(t, p.id).run();
      continue;
    }
    perAccount.set(p.account_id, n + 1);
    const r = await start(env, tk, p, token, t);
    if (r === 'started') counts.started++; else counts[r]++;
  }

  const { results: publishing } = await env.DB.prepare(`SELECT * FROM posts
      WHERE status = 'publishing' AND publish_id IS NOT NULL ORDER BY updated_at LIMIT 25`).all();
  for (const p of publishing) {
    const r = await poll(env, tk, p, token, t);
    if (r === 'published') counts.published++;
    else if (r === 'failed') counts.failed++;
  }
  return counts;
}
```

Note on the timeout: `poll` measures from `updated_at`, which `start` sets when `content/init` succeeds and which later polls do not change.

- [ ] **Step 4: Wire the cron**

In `publisher-api/src/index.js`, add the import:
```js
import { tick } from './publisher.js';
```
and replace the `scheduled` method with:
```js
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      const counts = await tick(env, tkFor(env));
      if (counts.started || counts.published || counts.failed) console.log('tick', JSON.stringify(counts));
    })());
  },
```

- [ ] **Step 5: Run to verify pass**

Run: `cd publisher-api && npx vitest run`
Expected: all pass, including 10 publisher tests.

- [ ] **Step 6: Commit**

```bash
git add publisher-api/src/publisher.js publisher-api/src/index.js publisher-api/test/publisher.test.js
git commit -m "publisher-api: cron that publishes due posts once, retries, and polls

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---

### Task 7: Retention and Delete workspace

**Files:**
- Create: `publisher-api/src/cleanup.js`
- Modify: `publisher-api/src/index.js` (route + cron)
- Test: `publisher-api/test/cleanup.test.js`

**Interfaces:**
- Consumes: `now`, `json`; R2 binding `MEDIA`; D1 `DB`.
- Produces: `runCleanup(env, t = now()) → { images: n, sessions: n }`; `deleteWorkspace(env, ws)`; route `DELETE /v1/me`.

- [ ] **Step 1: Write the failing tests**

`publisher-api/test/cleanup.test.js`:
```js
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeEach } from 'vitest';
import { resetDb } from './helpers.js';
import { runCleanup, deleteWorkspace } from '../src/cleanup.js';

const T = 1_800_000_000;
async function img(key, { deleteAfter = null, postId = null, ws = 'ws_1' } = {}) {
  await env.MEDIA.put(key, new Uint8Array([0xff, 0xd8, 0xff]));
  await env.DB.prepare(`INSERT INTO media (key, workspace_id, bytes, content_type, created_at, post_id, delete_after)
      VALUES (?, ?, 3, 'image/jpeg', ?, ?, ?)`).bind(key, ws, T, postId, deleteAfter).run();
}

describe('cleanup', () => {
  beforeEach(() => resetDb(env));

  it('deletes only images whose delete_after has passed', async () => {
    await img('ws_1/old.jpg', { deleteAfter: T - 1 });
    await img('ws_1/later.jpg', { deleteAfter: T + 100 });
    await img('ws_1/queued.jpg', { postId: 'pst_q' });          // attached to a live post: never deleted
    const r = await runCleanup(env, T);
    expect(r.images).toBe(1);
    expect(await env.MEDIA.get('ws_1/old.jpg')).toBeNull();
    expect(await env.MEDIA.get('ws_1/later.jpg')).not.toBeNull();
    expect(await env.MEDIA.get('ws_1/queued.jpg')).not.toBeNull();
  });

  it('removes expired sessions', async () => {
    await env.DB.prepare('INSERT INTO sessions VALUES (?, ?, ?)').bind('h1', 'ws_1', T - 1).run();
    await env.DB.prepare('INSERT INTO sessions VALUES (?, ?, ?)').bind('h2', 'ws_1', T + 1).run();
    expect((await runCleanup(env, T)).sessions).toBe(1);
  });

  it('deleteWorkspace removes every row and image for that workspace only', async () => {
    await env.DB.prepare('INSERT INTO workspaces (id, created_at) VALUES (?, ?), (?, ?)').bind('ws_1', T, 'ws_2', T).run();
    await img('ws_1/a.jpg');
    await img('ws_2/b.jpg', { ws: 'ws_2' });
    await env.DB.prepare('INSERT INTO sessions VALUES (?, ?, ?)').bind('h1', 'ws_1', T + 99).run();
    await deleteWorkspace(env, 'ws_1');
    expect(await env.MEDIA.get('ws_1/a.jpg')).toBeNull();
    expect(await env.MEDIA.get('ws_2/b.jpg')).not.toBeNull();
    for (const t of ['workspaces', 'sessions', 'media']) {
      const { n } = await env.DB.prepare(`SELECT COUNT(*) AS n FROM ${t} WHERE ${t === 'workspaces' ? 'id' : 'workspace_id'} = 'ws_1'`).first();
      expect(n).toBe(0);
    }
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd publisher-api && npx vitest run test/cleanup.test.js`
Expected: FAIL — cannot resolve `../src/cleanup.js`.

- [ ] **Step 3: Implement**

`publisher-api/src/cleanup.js`:
```js
import { now } from './http.js';

export async function runCleanup(env, t = now()) {
  const { results } = await env.DB.prepare(
    'SELECT key FROM media WHERE delete_after IS NOT NULL AND delete_after <= ? LIMIT 500').bind(t).all();
  const keys = results.map(r => r.key);
  if (keys.length) {
    await env.MEDIA.delete(keys);
    const marks = keys.map(() => '?').join(',');
    await env.DB.prepare(`DELETE FROM media WHERE key IN (${marks})`).bind(...keys).run();
  }
  const s = await env.DB.prepare('DELETE FROM sessions WHERE expires_at <= ?').bind(t).run();
  return { images: keys.length, sessions: s.meta.changes };
}

export async function deleteWorkspace(env, ws) {
  for (;;) {
    const { results } = await env.DB.prepare('SELECT key FROM media WHERE workspace_id = ? LIMIT 500').bind(ws).all();
    if (!results.length) break;
    const keys = results.map(r => r.key);
    await env.MEDIA.delete(keys);
    const marks = keys.map(() => '?').join(',');
    await env.DB.prepare(`DELETE FROM media WHERE key IN (${marks})`).bind(...keys).run();
  }
  await env.DB.batch(['posts', 'accounts', 'sessions'].map(t =>
    env.DB.prepare(`DELETE FROM ${t} WHERE workspace_id = ?`).bind(ws))
    .concat(env.DB.prepare('DELETE FROM workspaces WHERE id = ?').bind(ws)));
}
```

- [ ] **Step 4: Route and cron**

In `publisher-api/src/index.js`, add the import:
```js
import { runCleanup, deleteWorkspace } from './cleanup.js';
```
append to `ROUTES`:
```js
  ['DELETE', '/v1/me', async (req, env, { ws }) => { await deleteWorkspace(env, ws); return json({ ok: true }); }, 'user'],
```
and inside `scheduled`, after the `tick` line, add:
```js
      await runCleanup(env);
```

- [ ] **Step 5: Run to verify pass**

Run: `cd publisher-api && npx vitest run`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add publisher-api/src/cleanup.js publisher-api/src/index.js publisher-api/test/cleanup.test.js
git commit -m "publisher-api: image retention, session expiry, delete workspace

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 8: Create the Cloudflare resources and deploy the Worker

**Files:**
- Modify: `publisher-api/wrangler.toml` (real `database_id`)

**Interfaces:**
- Produces: the Worker live at `https://arco-publisher-api.<subdomain>.workers.dev` (call this **WORKER_ORIGIN**; Task 9 needs the exact value), D1 `arco-publisher` with the schema, R2 bucket `arco-publisher-media`, Worker secrets `TOKEN_KEY`, `INTERNAL_SECRET`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`. The same `INTERNAL_SECRET` value is also set on Vercel as a production env var.

- [ ] **Step 1: Log in to Cloudflare (the user does this)**

Run: `cd publisher-api && npx wrangler whoami`
If it says you are not logged in, ask the user to run `! cd ~/SIXSIX/arco-app/publisher-api && npx wrangler login` and approve in the browser. Use the same Cloudflare account that hosts `arco-metrics`.

- [ ] **Step 2: Create D1 and R2**

Run:
```bash
cd publisher-api
npx wrangler d1 create arco-publisher
npx wrangler r2 bucket create arco-publisher-media
```
Expected: the first command prints a block containing `database_id = "<uuid>"`. Put that uuid into `wrangler.toml` in place of `local-dev`.

- [ ] **Step 3: Apply the schema**

Run: `npm run db:migrate`
Expected: `Executed … commands` with no errors.
Verify: `npx wrangler d1 execute arco-publisher --remote --command "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"` lists `accounts, media, posts, sessions, workspaces`.

- [ ] **Step 4: Set the secrets without printing them**

Run from `publisher-api/` (values come from `openssl` or from `../.env`; nothing is echoed):
```bash
openssl rand -base64 32 | tr -d '\n' | npx wrangler secret put TOKEN_KEY
grep '^TIKTOK_CLIENT_KEY=' ../.env | cut -d= -f2- | tr -d '\n' | npx wrangler secret put TIKTOK_CLIENT_KEY
grep '^TIKTOK_CLIENT_SECRET=' ../.env | cut -d= -f2- | tr -d '\n' | npx wrangler secret put TIKTOK_CLIENT_SECRET
S=$(openssl rand -hex 32)
printf %s "$S" | npx wrangler secret put INTERNAL_SECRET
(cd ../publisher && printf %s "$S" | npx -y vercel@latest env add INTERNAL_SECRET production)
unset S
```
Expected: four `✨ Success! Uploaded secret` lines and Vercel's `Added Environment Variable INTERNAL_SECRET`.
Check: `npx wrangler secret list` shows the four names. `TIKTOK_CLIENT_KEY` in `../.env` is the **production** key (starts with `aw`), per the credential split committed in c77e95d.

`TOKEN_KEY` encrypts every stored refresh token. If it is ever lost or changed, every account must reconnect. Do not rotate it casually.

- [ ] **Step 5: Deploy and smoke-test**

Run: `npm run deploy`
Expected: output ends with the Worker URL and `schedule: * * * * *`. Record the URL as WORKER_ORIGIN.

Run:
```bash
curl -s -o /dev/null -w '%{http_code}\n' "$WORKER_ORIGIN/v1/me"          # 401
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$WORKER_ORIGIN/internal/oauth"   # 403
curl -s -o /dev/null -w '%{http_code}\n' "$WORKER_ORIGIN/media/ws_x/none.jpg"      # 404
```
Expected: `401`, `403`, `404`.

Watch one cron run: `npx wrangler tail --format pretty` for ~70 seconds shows a scheduled event with no exception. Stop with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
git add publisher-api/wrangler.toml
git commit -m "publisher-api: point at the real D1 database

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---

### Task 9: Vercel front door — sign-in, Add account, rewrites

**Files:**
- Modify: `publisher/vercel.json`, `publisher/api/_lib.js`, `publisher/api/auth/start.js`, `publisher/api/auth/callback.js`, `publisher/api/auth/logout.js`
- Delete: `publisher/api/creator-info.js`, `publisher/api/publish.js`, `publisher/api/status.js`, `publisher/api/drafts.js`

**Interfaces:**
- Consumes: WORKER_ORIGIN and `INTERNAL_SECRET` (Task 8); Worker `POST /internal/oauth` (Task 3), `POST /v1/logout`.
- Produces:
  - `GET /api/auth/start` → TikTok consent; `GET /api/auth/start?add=1` → same, and the callback attaches the account to the current workspace
  - `GET /api/auth/callback` → sets cookie `tt_sid` (plain session id, httpOnly, Secure, SameSite=Lax, 30 days) and redirects to `/app.html`; on error redirects to `/app.html?auth_error=<message>`; with no `tt_state` cookie keeps the CLI hand-off page
  - `GET /api/auth/logout` → tells the Worker, clears `tt_sid`, redirects to `/`
  - Browser calls `/api/v1/*` and `/media/*` on `arco-publisher.vercel.app`; Vercel rewrites them to the Worker with the Cookie header intact
  - Vercel env: `WORKER_ORIGIN` (new), `INTERNAL_SECRET` (Task 8), existing `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `SESSION_SECRET`

- [ ] **Step 1: Rewrites**

Replace `publisher/vercel.json` with (put the exact WORKER_ORIGIN from Task 8 in both destinations):
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    { "source": "/api/v1/:path*", "destination": "https://arco-publisher-api.SUBDOMAIN.workers.dev/v1/:path*" },
    { "source": "/media/:path*", "destination": "https://arco-publisher-api.SUBDOMAIN.workers.dev/media/:path*" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

- [ ] **Step 2: Add Worker helpers to `_lib.js`**

In `publisher/api/_lib.js`, delete the now-unused `CREATOR_INFO_URL`, `CONTENT_INIT_URL`, `STATUS_FETCH_URL`, `envelope`, `accessTokenFrom` and `fail` exports, and append:
```js
// --- the Worker ------------------------------------------------------------

export const SESSION_COOKIE = 'tt_sid';
const SESSION_MAX_AGE = 30 * 86400;

/** The Worker's session id, as the browser holds it (plain, not signed:
 *  the Worker stores only its hash and is the one that checks it). */
export function rawCookie(req, name) {
  const raw = (req.headers.cookie || '').split(';').map(s => s.trim()).find(s => s.startsWith(`${name}=`));
  return raw ? decodeURIComponent(raw.slice(name.length + 1)) : null;
}

export function setSessionCookie(res, id) {
  append(res, `${SESSION_COOKIE}=${encodeURIComponent(id)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${SESSION_MAX_AGE}`);
}

export async function workerFetch(path, init = {}) {
  return fetch(`${env('WORKER_ORIGIN')}${path}`, init);
}
```

- [ ] **Step 3: `start.js` remembers "add"**

In `publisher/api/auth/start.js`, after the two `setCookie` lines, add:
```js
  // "Add account" keeps the current workspace; a plain sign-in does not.
  const add = new URL(req.url, 'https://x').searchParams.get('add') === '1';
  if (add) setCookie(res, 'tt_add', '1', { maxAge: 600 });
  else clearCookie(res, 'tt_add');
```
and add `clearCookie` to its import from `../_lib.js`.

- [ ] **Step 4: Rewrite the callback**

Replace `publisher/api/auth/callback.js` with:
```js
// Step two: TikTok sends the browser back with ?code=. The Worker does the
// exchange and keeps the tokens; this function only proves the round trip
// was ours (state + PKCE verifier cookies) and hands over the session cookie.

import {
  clearCookie, readCookie, rawCookie, redirectUri, env, setSessionCookie, workerFetch, SESSION_COOKIE,
} from '../_lib.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const denied = url.searchParams.get('error');
  if (denied) return back(res, `TikTok returned ${denied}`);

  const expected = readCookie(req, 'tt_state');
  const verifier = readCookie(req, 'tt_verifier');
  const adding = readCookie(req, 'tt_add') === '1';
  clearCookie(res, 'tt_state');
  clearCookie(res, 'tt_verifier');
  clearCookie(res, 'tt_add');

  if (!code) return back(res, 'no authorization code came back');
  // No state cookie at all: the sign-in was started by the command-line token
  // tool, which keeps its own state and verifier. Leave the code unspent.
  if (!expected) return handoff(res);
  if (state !== expected) return back(res, 'state mismatch, start over');
  if (!verifier) return back(res, 'the sign-in attempt expired, start over');

  let body;
  try {
    const r = await workerFetch('/internal/oauth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Internal-Secret': env('INTERNAL_SECRET') },
      body: JSON.stringify({
        code, code_verifier: verifier, redirect_uri: redirectUri(req),
        session_id: adding ? rawCookie(req, SESSION_COOKIE) || undefined : undefined,
      }),
    });
    body = await r.json();
    if (!r.ok) return back(res, body.error || `sign-in failed (${r.status})`);
  } catch (err) {
    return back(res, 'could not reach the ARCO Publisher service, try again');
  }

  setSessionCookie(res, body.session_id);
  res.redirect(302, adding ? '/app.html#settings' : '/app.html');
}

function back(res, why) {
  res.redirect(302, '/app.html?auth_error=' + encodeURIComponent(why));
}

function handoff(res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.status(200).send(`<!doctype html><meta charset="utf-8">
<meta name="robots" content="noindex"><title>ARCO Publisher</title>
<body style="font:15px/1.6 -apple-system,sans-serif;max-width:560px;margin:15vh auto;padding:0 20px;color:#18181B;background:#F4F4F5">
<h1 style="font-size:20px">Authorized</h1>
<p>Copy the full address from the address bar and paste it back into the terminal
that started this sign-in. This page has not used the code.</p></body>`);
}
```

- [ ] **Step 5: Logout**

Replace `publisher/api/auth/logout.js` with:
```js
import { clearCookie, rawCookie, workerFetch, SESSION_COOKIE } from '../_lib.js';

export default async function handler(req, res) {
  const sid = rawCookie(req, SESSION_COOKIE);
  if (sid) {
    try {
      await workerFetch('/v1/logout', { method: 'POST', headers: { Cookie: `${SESSION_COOKIE}=${encodeURIComponent(sid)}` } });
    } catch { /* the cookie is cleared either way */ }
  }
  clearCookie(res, SESSION_COOKIE);
  clearCookie(res, 'tt_at');
  res.redirect(302, '/');
}
```

- [ ] **Step 6: Remove the old single-user endpoints**

Run: `git rm publisher/api/creator-info.js publisher/api/publish.js publisher/api/status.js publisher/api/drafts.js`

- [ ] **Step 7: Set `WORKER_ORIGIN` on Vercel and deploy**

Run:
```bash
cd publisher
printf %s "$WORKER_ORIGIN" | npx -y vercel@latest env add WORKER_ORIGIN production
npx -y vercel@latest deploy --prod --yes
```

- [ ] **Step 8: Verify through Vercel**

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://arco-publisher.vercel.app/api/v1/me     # 401 from the Worker
curl -s https://arco-publisher.vercel.app/api/v1/me                                        # {"error":"Sign in first"}
curl -s -o /dev/null -w '%{http_code}\n' https://arco-publisher.vercel.app/media/ws_x/n.jpg # 404 from the Worker
curl -s -o /dev/null -w '%{redirect_url}\n' 'https://arco-publisher.vercel.app/api/auth/start?add=1' | grep -o 'client_key=[a-z0-9]\{2\}'   # client_key=aw
curl -s 'https://arco-publisher.vercel.app/api/auth/callback?code=x&state=y' | grep -c Authorized    # 1 (CLI hand-off still works)
```

- [ ] **Step 9: Commit**

```bash
git add publisher/vercel.json publisher/api
git commit -m "publisher: hand sign-in to the Worker, rewrite /api/v1 and /media to it

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 10: The web app (compose, posting panel, calendar, settings)

**Files:**
- Create: `publisher/public/app.html`, `publisher/public/app.js`

**Interfaces:**
- Consumes (all same-origin, cookie `tt_sid` sent automatically): `GET /api/v1/me`, `GET /api/v1/accounts/:id/creator-info`, `POST /api/v1/media`, `POST /api/v1/posts`, `GET /api/v1/posts?from&to`, `DELETE /api/v1/posts/:id`, `POST /api/v1/posts/:id/retry`, `DELETE /api/v1/accounts/:id`, `POST /api/v1/api-key`, `DELETE /api/v1/me`; links `/api/auth/start`, `/api/auth/start?add=1`, `/api/auth/logout`.
- Produces: `/app.html` with hash views `#compose` (default), `#calendar`, `#settings`.

This task is UI; its checks are manual against the deployed site (Step 4). The Content Sharing Guidelines items are listed there as a checklist, because the audit reviewer will look for each one.

- [ ] **Step 1: Write `app.html`**

`publisher/public/app.html`:
```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" sizes="64x64" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>ARCO Publisher</title>
<style>
:root{--bg:#F4F4F5;--surface:#fff;--line:#E4E4E7;--line-2:#D4D4D8;--well:#FAFAFA;
  --text:#18181B;--muted:#52525B;--dim:#71717A;--accent:#0284C7;--ok:#15803D;--warn:#B45309;--bad:#B91C1C}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
a{color:var(--accent)}
button{font:inherit;cursor:pointer}
.wrap{max-width:980px;margin:0 auto;padding:0 20px 64px}
header{display:flex;align-items:center;gap:14px;padding:18px 0;border-bottom:1px solid var(--line);margin-bottom:24px;flex-wrap:wrap}
header h1{font-size:16px;margin:0;display:flex;align-items:center;gap:10px}
header img{width:28px;height:28px;border-radius:7px}
nav.tabs{display:flex;gap:6px;margin-left:auto}
nav.tabs a{padding:7px 12px;border-radius:8px;color:var(--muted);text-decoration:none}
nav.tabs a.on{background:var(--surface);color:var(--text);box-shadow:0 0 0 1px var(--line)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;margin-bottom:18px}
.sec{padding:20px 22px;border-bottom:1px solid var(--line)}
.sec:last-child{border-bottom:0}
.cap{display:block;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:12px}
label.f{display:block;font-size:12px;color:var(--muted);margin:0 0 6px}
input[type=text],input[type=datetime-local],select,textarea{width:100%;background:var(--well);color:var(--text);
  border:1px solid var(--line-2);border-radius:9px;padding:10px 12px;font:inherit}
textarea{min-height:90px;resize:vertical}
.count{font-size:12px;color:var(--dim);text-align:right}
.btn{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:10px 16px;font-weight:600}
.btn.sec{background:#fff;color:var(--text);border:1px solid var(--line-2)}
.btn.danger{background:#fff;color:var(--bad);border:1px solid #FCA5A5}
.btn:disabled{opacity:.45;cursor:not-allowed}
.row{display:flex;align-items:flex-start;gap:16px;padding:12px 0;border-bottom:1px solid var(--line)}
.row:last-child{border-bottom:0}
.row .txt{flex:1}.row .t{font-weight:600}.row .d{display:block;font-size:12.5px;color:var(--dim)}
.who{display:flex;align-items:center;gap:12px}
.who img{width:40px;height:40px;border-radius:50%;object-fit:cover;border:1px solid var(--line-2)}
.thumbs{display:flex;gap:10px;flex-wrap:wrap}
.th{position:relative;width:84px}
.th img{width:84px;height:150px;object-fit:cover;border-radius:8px;border:2px solid transparent;display:block;background:var(--well)}
.th.cover img{border-color:var(--accent)}
.th .ctl{display:flex;justify-content:space-between;margin-top:4px}
.th .ctl button{border:1px solid var(--line-2);background:#fff;border-radius:6px;padding:0 6px;font-size:12px}
.th .badge{position:absolute;top:4px;left:4px;background:var(--accent);color:#fff;font-size:10px;border-radius:5px;padding:1px 5px}
.note{font-size:12.5px;color:var(--dim)}
.note.warn{color:var(--warn)}.note.bad{color:var(--bad)}
.status{padding:12px 14px;border-radius:9px;background:var(--well);border:1px solid var(--line);margin-top:12px}
.status.ok{border-color:#86EFAC;color:var(--ok);background:#F0FDF4}
.status.err{border-color:#FCA5A5;color:var(--bad);background:#FEF2F2}
.consent{font-size:12.5px;color:var(--muted);padding:14px 22px;background:var(--well);border-top:1px solid var(--line)}
.foot{padding:18px 22px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.chip{border:1px solid var(--line-2);background:#fff;border-radius:999px;padding:5px 12px;font-size:12.5px}
.chip.on{background:var(--text);color:#fff;border-color:var(--text)}
.week{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px}
.day{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px;min-height:150px}
.day h4{margin:0 0 8px;font-size:12px;color:var(--dim);font-weight:600}
.day.today h4{color:var(--accent)}
.pc{border:1px solid var(--line);border-radius:9px;padding:6px;margin-bottom:6px;font-size:12px;background:var(--well)}
.pc img{width:100%;height:64px;object-fit:cover;border-radius:6px}
.pill{display:inline-block;font-size:10.5px;border-radius:999px;padding:1px 7px;border:1px solid var(--line-2)}
.pill.published{color:var(--ok);border-color:#86EFAC}.pill.failed{color:var(--bad);border-color:#FCA5A5}
.pill.publishing{color:var(--accent)}.pill.cancelled{color:var(--dim)}
.pc .acts{display:flex;gap:6px;margin-top:4px;flex-wrap:wrap}
.pc .acts button,.pc .acts a{font-size:11px;border:0;background:none;color:var(--accent);padding:0}
@media (max-width:760px){.week{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1><a href="/" style="color:inherit;text-decoration:none;display:flex;gap:10px;align-items:center">
      <img src="/icon.png" alt="">ARCO Publisher</a></h1>
    <nav class="tabs" id="tabs" hidden>
      <a href="#compose" data-v="compose">New post</a>
      <a href="#calendar" data-v="calendar">Calendar</a>
      <a href="#settings" data-v="settings">Settings</a>
    </nav>
  </header>
  <main id="app"><div class="card"><div class="sec">Loading…</div></div></main>
</div>
<script src="/app.js" type="module"></script>
</body>
</html>
```

- [ ] **Step 2: Write `app.js`**

`publisher/public/app.js`:
```js
const PRIVACY_LABEL = { PUBLIC_TO_EVERYONE: 'Everyone', MUTUAL_FOLLOW_FRIENDS: 'Friends',
  FOLLOWER_OF_CREATOR: 'Followers', SELF_ONLY: 'Only me' };
const MAX_SIDE_W = 1080, MAX_SIDE_H = 1920;

const S = {
  me: null, view: 'compose', flash: null,
  images: [], cover: 0, title: '', caption: '',
  account: '', info: null, infoErr: null,
  set: { privacy: '', comment: false, music: false, disclose: false, brand: false, branded: false },
  when: 'now', at: '', busy: false, status: null,
  week: 0, filter: 'all', posts: [], apiKey: null,
};

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const len = s => [...s].length;

async function api(path, opts = {}) {
  const r = await fetch('/api/v1' + path, { credentials: 'same-origin', ...opts });
  let body = {};
  try { body = await r.json(); } catch {}
  if (!r.ok) { const e = new Error(body.error || `Request failed (${r.status})`); e.status = r.status; e.code = body.code; throw e; }
  return body;
}

// ---- boot --------------------------------------------------------------

async function boot() {
  const q = new URL(location.href).searchParams;
  if (q.get('auth_error')) { S.flash = { kind: 'err', text: q.get('auth_error') }; history.replaceState({}, '', location.pathname + location.hash); }
  try { S.me = await api('/me'); } catch (e) { if (e.status !== 401) S.flash = { kind: 'err', text: e.message }; }
  window.addEventListener('hashchange', route);
  route();
}

function route() {
  S.view = (location.hash || '#compose').slice(1);
  if (!['compose', 'calendar', 'settings'].includes(S.view)) S.view = 'compose';
  if (S.view === 'calendar') loadWeek();
  render();
}

// ---- render ------------------------------------------------------------

function render() {
  $('tabs').hidden = !S.me;
  document.querySelectorAll('#tabs a').forEach(a => a.classList.toggle('on', a.dataset.v === S.view));
  const flash = S.flash ? `<div class="status ${S.flash.kind}">${esc(S.flash.text)}</div>` : '';
  if (!S.me) { $('app').innerHTML = flash + signInView(); return; }
  $('app').innerHTML = flash + (S.view === 'calendar' ? calendarView() : S.view === 'settings' ? settingsView() : composeView());
  bind();
}

function signInView() {
  return `<div class="card"><div class="sec">
    <span class="cap">Sign in</span>
    <p style="margin:0 0 16px;color:var(--muted)">Sign in with TikTok to schedule photo posts to your account.
      We show your nickname and avatar so you always know which account will post, and we only post what you
      confirm on the next screens. You can connect more accounts afterwards.</p>
    <a class="btn" href="/api/auth/start" style="text-decoration:none;display:inline-block">Continue with TikTok</a>
  </div></div>`;
}

function composeView() {
  const accts = S.me.accounts;
  if (!accts.length) return `<div class="card"><div class="sec">Connect a TikTok account in <a href="#settings">Settings</a> first.</div></div>`;
  const i = S.info;
  const opts = (i?.privacy_level_options || []).filter(o => !(o === 'SELF_ONLY' && S.set.branded));
  const label = S.set.branded ? 'Paid partnership' : S.set.brand ? 'Promotional content' : '';
  const need = missing();
  return `<div class="card">
    <div class="sec"><span class="cap">Photos</span>
      <div class="thumbs">${S.images.map((m, n) => `<div class="th ${n === S.cover ? 'cover' : ''}">
          ${n === S.cover ? '<span class="badge">Cover</span>' : ''}
          <img src="${esc(m.url)}" alt="Slide ${n + 1}" data-cover="${n}" title="Set as cover">
          <div class="ctl"><button data-mv="${n}:-1" aria-label="Move left">‹</button>
            <button data-rm="${n}" aria-label="Remove">×</button>
            <button data-mv="${n}:1" aria-label="Move right">›</button></div></div>`).join('')}
      </div>
      <p><input type="file" id="files" accept="image/jpeg,image/png" multiple ${S.images.length >= 35 ? 'disabled' : ''}></p>
      <span class="note">JPG or PNG, up to 35 images, 5 MB each. Click an image to make it the cover.</span>
    </div>
    <div class="sec">
      <label class="f" for="title">Title</label>
      <input type="text" id="title" maxlength="200" value="${esc(S.title)}">
      <div class="count ${len(S.title) > 90 ? 'note bad' : ''}">${len(S.title)} / 90</div>
      <label class="f" for="caption">Caption</label>
      <textarea id="caption">${esc(S.caption)}</textarea>
      <div class="count ${len(S.caption) > 4000 ? 'note bad' : ''}">${len(S.caption)} / 4000</div>
    </div>
    <div class="sec"><span class="cap">Posting to TikTok</span>
      <label class="f" for="acct">Account</label>
      <select id="acct"><option value="">Choose an account…</option>
        ${accts.map(a => `<option value="${a.id}" ${S.account === a.id ? 'selected' : ''} ${a.needs_reconnect ? 'disabled' : ''}>@${esc(a.username)}${a.needs_reconnect ? ' (reconnect in Settings)' : ''}</option>`).join('')}
      </select>
      ${i ? `<div class="who" style="margin-top:12px">${i.creator_avatar_url ? `<img src="${esc(i.creator_avatar_url)}" alt="">` : ''}
          <div><b>${esc(i.creator_nickname)}</b><div class="note">@${esc(i.creator_username)}</div></div></div>` : ''}
      ${S.infoErr ? `<p class="note bad">${esc(S.infoErr)}</p>` : ''}
    </div>
    ${i ? `<div class="sec">
      <label class="f" for="privacy">Who can view this post *</label>
      <select id="privacy"><option value="" ${S.set.privacy ? '' : 'selected'}>Select who can view…</option>
        ${opts.map(o => `<option value="${o}" ${S.set.privacy === o ? 'selected' : ''}>${PRIVACY_LABEL[o] || o}</option>`).join('')}
      </select>
      ${S.set.branded && (i.privacy_level_options || []).includes('SELF_ONLY') ? '<p class="note">Branded content cannot be private, so "Only me" is unavailable.</p>' : ''}
    </div>
    <div class="sec"><span class="cap">Interactions</span>
      ${row('Allow comments', i.comment_disabled ? 'Turned off in your TikTok settings.' : '',
        `<input type="checkbox" data-k="comment" ${S.set.comment && !i.comment_disabled ? 'checked' : ''} ${i.comment_disabled ? 'disabled' : ''}>`)}
      ${row('Duet', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
      ${row('Stitch', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
      ${row('Add recommended music', 'Lets TikTok pick a track for the slideshow.', `<input type="checkbox" data-k="music" ${S.set.music ? 'checked' : ''}>`)}
    </div>
    <div class="sec"><span class="cap">Disclosure</span>
      ${row('Disclose post content', 'Turn on if this post promotes yourself, a brand, product or service.',
        `<input type="checkbox" data-k="disclose" ${S.set.disclose ? 'checked' : ''}>`)}
      ${S.set.disclose ? `<div style="padding:8px 0">
        <label><input type="checkbox" data-k="brand" ${S.set.brand ? 'checked' : ''}> Your brand</label>
        &nbsp;&nbsp;<label><input type="checkbox" data-k="branded" ${S.set.branded ? 'checked' : ''}> Branded content</label>
        <p class="note ${label ? 'warn' : ''}">${label ? `Your photo post will be labeled "${label}".` : 'You need to indicate if your content promotes yourself, a third party, or both.'}</p>
      </div>` : ''}
    </div>
    <div class="sec"><span class="cap">Preview</span>
      <div class="thumbs">${S.images.map(m => `<img src="${esc(m.url)}" alt="" style="width:56px;height:100px;object-fit:cover;border-radius:6px">`).join('') || '<span class="note">Add photos to see them here.</span>'}</div>
      ${S.title ? `<p><b>${esc(S.title)}</b></p>` : ''}${S.caption ? `<p class="note" style="white-space:pre-wrap">${esc(S.caption)}</p>` : ''}
    </div>
    <div class="sec"><span class="cap">When</span>
      <label><input type="radio" name="when" value="now" ${S.when === 'now' ? 'checked' : ''}> Post now</label>
      &nbsp;&nbsp;<label><input type="radio" name="when" value="later" ${S.when === 'later' ? 'checked' : ''}> Schedule</label>
      ${S.when === 'later' ? `<p><input type="datetime-local" id="at" value="${esc(S.at)}" min="${localInput(Date.now() + 6 * 60e3)}"></p>
        <span class="note">Your local time. At least 5 minutes from now.</span>` : ''}
    </div>
    <div class="consent">By posting, you agree to TikTok's
      ${S.set.branded ? '<a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank" rel="noopener">Branded Content Policy</a> and ' : ''}
      <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en" target="_blank" rel="noopener">Music Usage Confirmation</a>.</div>` : ''}
    <div class="foot">
      <button class="btn" id="go" ${need || S.busy ? 'disabled' : ''} title="${esc(need || '')}">
        ${S.busy ? 'Working…' : S.when === 'later' ? 'Schedule' : 'Post to TikTok'}</button>
      ${need ? `<span class="note">${esc(need)}</span>` : ''}
      ${S.status ? `<div class="status ${S.status.kind}" style="flex-basis:100%">${esc(S.status.text)}</div>` : ''}
      <span class="note" style="flex-basis:100%">After posting, it may take a few minutes for the post to process and appear on the profile.</span>
    </div>
  </div>`;
}

const row = (t, d, control) => `<div class="row"><span class="txt"><span class="t">${t}</span>${d ? `<span class="d">${d}</span>` : ''}</span>${control}</div>`;

function missing() {
  if (!S.images.length) return 'Add at least one photo';
  if (S.images.some(m => m.uploading)) return 'Waiting for uploads to finish';
  if (len(S.title) > 90) return 'The title is too long';
  if (len(S.caption) > 4000) return 'The caption is too long';
  if (!S.account || !S.info) return 'Choose an account';
  if (!S.set.privacy) return 'Choose who can view this post';
  if (S.set.disclose && !S.set.brand && !S.set.branded) return 'You need to indicate if your content promotes yourself, a third party, or both';
  if (S.when === 'later') {
    const t = S.at ? new Date(S.at).getTime() : NaN;
    if (!Number.isFinite(t)) return 'Pick a date and time';
    if (t < Date.now() + 5 * 60e3) return 'Pick a time at least 5 minutes from now';
  }
  return '';
}

function localInput(ms) {
  const d = new Date(ms), p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

// ---- compose actions ---------------------------------------------------

async function shrink(file) {
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE_W / bmp.width, MAX_SIDE_H / bmp.height);
  if (scale === 1 && file.size <= 5 * 1024 * 1024) return { blob: file, type: file.type };
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.9));
  return { blob, type: 'image/jpeg' };
}

async function addFiles(files) {
  for (const file of [...files].slice(0, 35 - S.images.length)) {
    const slot = { url: URL.createObjectURL(file), uploading: true };
    S.images.push(slot); render();
    try {
      const { blob, type } = await shrink(file);
      const m = await api('/media', { method: 'POST', headers: { 'Content-Type': type }, body: blob });
      Object.assign(slot, { key: m.key, url: m.url, uploading: false });
    } catch (e) {
      S.images.splice(S.images.indexOf(slot), 1);
      S.status = { kind: 'err', text: `${file.name}: ${e.message}` };
    }
    render();
  }
}

async function pickAccount(id) {
  S.account = id; S.info = null; S.infoErr = null; S.set.privacy = ''; render();
  if (!id) return;
  try { S.info = await api(`/accounts/${id}/creator-info`); }
  catch (e) { S.infoErr = e.code === 'needs_reconnect' ? 'Reconnect this account in Settings.' : e.message; }
  render();
}

function setOpt(k, v) {
  S.set[k] = v;
  if (k === 'branded' && v && S.set.privacy === 'SELF_ONLY') S.set.privacy = '';
  if (k === 'disclose' && !v) { S.set.brand = false; S.set.branded = false; }
  render();
}

async function submit() {
  if (missing() || S.busy) return;
  S.busy = true; S.status = { kind: '', text: 'Sending…' }; render();
  try {
    const p = await api('/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
      account_id: S.account, image_keys: S.images.map(m => m.key), cover_index: S.cover,
      title: S.title, caption: S.caption,
      settings: { privacy_level: S.set.privacy, disable_comment: !S.set.comment || !!S.info?.comment_disabled,
        auto_add_music: S.set.music, brand_organic: S.set.disclose && S.set.brand, branded_content: S.set.disclose && S.set.branded },
      scheduled_at: S.when === 'later' ? Math.floor(new Date(S.at).getTime() / 1000) : null,
    }) });
    resetComposer();
    if (p.scheduled_at > Date.now() / 1000 + 60) {
      S.flash = { kind: 'ok', text: `Scheduled for ${new Date(p.scheduled_at * 1000).toLocaleString()}.` };
      location.hash = '#calendar';
    } else {
      S.status = { kind: '', text: 'Posting… TikTok is processing it. This page updates when it is done.' };
      render(); watch(p.id);
    }
  } catch (e) { S.status = { kind: 'err', text: e.message }; }
  S.busy = false; render();
}

async function watch(id) {
  for (let n = 0; n < 60; n++) {
    await new Promise(r => setTimeout(r, 5000));
    const t = Math.floor(Date.now() / 1000);
    const { posts } = await api(`/posts?from=${t - 3600}&to=${t + 60}`);
    const p = posts.find(x => x.id === id);
    if (p?.status === 'published') { S.status = { kind: 'ok', text: 'Published. It may take a few minutes to appear on the profile.' }; return render(); }
    if (p?.status === 'failed') { S.status = { kind: 'err', text: p.fail_reason || 'TikTok rejected the post.' }; return render(); }
  }
  S.status = { kind: '', text: 'Still processing. Check the Calendar for the result.' }; render();
}

function resetComposer() {
  Object.assign(S, { images: [], cover: 0, title: '', caption: '', when: 'now', at: '', status: null });
  S.set = { privacy: '', comment: false, music: false, disclose: false, brand: false, branded: false };
}

// ---- calendar ----------------------------------------------------------

function weekStart() {
  const d = new Date(); d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7) + S.week * 7);
  return d;
}

async function loadWeek() {
  const from = Math.floor(weekStart().getTime() / 1000);
  try { S.posts = (await api(`/posts?from=${from}&to=${from + 7 * 86400}`)).posts; }
  catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}

function calendarView() {
  const start = weekStart();
  const accts = S.me.accounts;
  const posts = S.posts.filter(p => S.filter === 'all' || p.account_id === S.filter);
  const days = [...Array(7)].map((_, i) => { const d = new Date(start); d.setDate(d.getDate() + i); return d; });
  const today = new Date().toDateString();
  return `<div class="chips">
      <button class="chip ${S.filter === 'all' ? 'on' : ''}" data-f="all">All accounts</button>
      ${accts.map(a => `<button class="chip ${S.filter === a.id ? 'on' : ''}" data-f="${a.id}">@${esc(a.username)}</button>`).join('')}
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
      <button class="btn sec" data-wk="-1" ${S.week <= 0 ? 'disabled' : ''}>‹</button>
      <b>${days[0].toLocaleDateString(undefined, { day: 'numeric', month: 'short' })} – ${days[6].toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}</b>
      <button class="btn sec" data-wk="1">›</button>
      <a class="btn" href="#compose" style="margin-left:auto;text-decoration:none">New post</a>
    </div>
    <div class="week">${days.map(d => {
      const ps = posts.filter(p => new Date(p.scheduled_at * 1000).toDateString() === d.toDateString());
      return `<div class="day ${d.toDateString() === today ? 'today' : ''}">
        <h4>${d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })}</h4>
        ${ps.map(p => `<div class="pc">
          ${p.images[p.cover_index] ? `<img src="${esc(p.images[p.cover_index])}" alt="">` : ''}
          <div>${new Date(p.scheduled_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · @${esc(p.username)}</div>
          <span class="pill ${p.status}">${p.status}</span>
          ${p.fail_reason ? `<div class="note ${p.status === 'failed' ? 'bad' : ''}">${esc(p.fail_reason)}</div>` : ''}
          <div class="acts">
            ${p.status === 'queued' ? `<button data-edit="${p.id}">Edit</button><button data-cancel="${p.id}">Cancel</button>` : ''}
            ${p.status === 'failed' ? `<button data-retry="${p.id}">Retry</button><button data-edit="${p.id}">Edit</button>` : ''}
            ${p.post_url ? `<a href="${esc(p.post_url)}" target="_blank" rel="noopener">View</a>` : ''}
          </div></div>`).join('') || '<span class="note">Nothing yet</span>'}
      </div>`;
    }).join('')}</div>`;
}

async function edit(id) {
  const p = S.posts.find(x => x.id === id);
  if (!p) return;
  if (p.status === 'queued') await api(`/posts/${id}`, { method: 'DELETE' });
  resetComposer();
  Object.assign(S, { images: p.image_keys.map((k, n) => ({ key: k, url: p.images[n] })), cover: p.cover_index,
    title: p.title, caption: p.caption, when: 'later', at: localInput(Math.max(p.scheduled_at * 1000, Date.now() + 10 * 60e3)) });
  const s = p.settings;
  S.set = { privacy: '', comment: !s.disable_comment, music: s.auto_add_music,
            disclose: s.brand_organic || s.branded_content, brand: s.brand_organic, branded: s.branded_content };
  location.hash = '#compose';
  await pickAccount(p.account_id);
  // Privacy is chosen again on purpose: the options come from TikTok now, not from when it was first made.
}

// ---- settings ----------------------------------------------------------

function settingsView() {
  const a = S.me.accounts;
  return `<div class="card">
    <div class="sec"><span class="cap">Connected TikTok accounts (${a.length} / ${S.me.limits.accounts})</span>
      ${a.map(x => row(`@${esc(x.username)}`, x.needs_reconnect ? '<span class="note bad">Access was revoked or expired. Reconnect to keep posting.</span>' : esc(x.display_name),
        `${x.needs_reconnect ? '<a class="btn sec" href="/api/auth/start?add=1" style="text-decoration:none">Reconnect</a>' : ''}
         <button class="btn danger" data-disc="${x.id}">Disconnect</button>`)).join('') || '<p class="note">No accounts yet.</p>'}
      <p><a class="btn" href="/api/auth/start?add=1" style="text-decoration:none;display:inline-block">Add account</a></p>
      <span class="note">Disconnecting cancels that account's scheduled posts. You can also revoke access in TikTok under
        Settings and privacy › Security &amp; permissions › Apps and services.</span>
    </div>
    <div class="sec"><span class="cap">API key</span>
      <p class="note">For posting from your own tools. The key can do everything you can do here. Creating a new key disables the old one.</p>
      ${S.apiKey ? `<p><code style="user-select:all">${esc(S.apiKey)}</code></p><p class="note warn">Copy it now. It will not be shown again.</p>` : ''}
      <button class="btn sec" id="apikey">${S.me.api_key_set ? 'Create a new key' : 'Create key'}</button>
    </div>
    <div class="sec"><span class="cap">Your data</span>
      <p class="note">Delete workspace removes your connected accounts, scheduled posts and uploaded images immediately.</p>
      <button class="btn danger" id="delws">Delete workspace</button>
      <a class="btn sec" href="/api/auth/logout" style="text-decoration:none;margin-left:8px">Sign out</a>
    </div></div>`;
}

// ---- events ------------------------------------------------------------

function bind() {
  const on = (sel, ev, fn) => document.querySelectorAll(sel).forEach(el => el.addEventListener(ev, fn));
  on('#files', 'change', e => addFiles(e.target.files));
  on('[data-cover]', 'click', e => { S.cover = Number(e.target.dataset.cover); render(); });
  on('[data-rm]', 'click', e => { const n = Number(e.target.dataset.rm); S.images.splice(n, 1); S.cover = Math.min(S.cover, Math.max(0, S.images.length - 1)); render(); });
  on('[data-mv]', 'click', e => {
    const [n, d] = e.target.dataset.mv.split(':').map(Number), m = n + d;
    if (m < 0 || m >= S.images.length) return;
    [S.images[n], S.images[m]] = [S.images[m], S.images[n]];
    if (S.cover === n) S.cover = m; else if (S.cover === m) S.cover = n;
    render();
  });
  on('#title', 'input', e => { S.title = e.target.value; });
  on('#title', 'change', render);
  on('#caption', 'input', e => { S.caption = e.target.value; });
  on('#caption', 'change', render);
  on('#acct', 'change', e => pickAccount(e.target.value));
  on('#privacy', 'change', e => { S.set.privacy = e.target.value; render(); });
  on('[data-k]', 'change', e => setOpt(e.target.dataset.k, e.target.checked));
  on('input[name=when]', 'change', e => { S.when = e.target.value; render(); });
  on('#at', 'change', e => { S.at = e.target.value; render(); });
  on('#go', 'click', submit);
  on('[data-f]', 'click', e => { S.filter = e.target.dataset.f; render(); });
  on('[data-wk]', 'click', e => { S.week += Number(e.target.dataset.wk); loadWeek(); });
  on('[data-cancel]', 'click', async e => { try { await api(`/posts/${e.target.dataset.cancel}`, { method: 'DELETE' }); } catch (x) { S.flash = { kind: 'err', text: x.message }; } loadWeek(); });
  on('[data-retry]', 'click', async e => { try { await api(`/posts/${e.target.dataset.retry}/retry`, { method: 'POST' }); } catch (x) { S.flash = { kind: 'err', text: x.message }; } loadWeek(); });
  on('[data-edit]', 'click', e => edit(e.target.dataset.edit));
  on('[data-disc]', 'click', async e => {
    if (!confirm('Disconnect this account? Its scheduled posts will be cancelled.')) return;
    await api(`/accounts/${e.target.dataset.disc}`, { method: 'DELETE' }); S.me = await api('/me'); render();
  });
  on('#apikey', 'click', async () => { S.apiKey = (await api('/api-key', { method: 'POST' })).api_key; S.me.api_key_set = true; render(); });
  on('#delws', 'click', async () => {
    if (!confirm('Delete your workspace, accounts, posts and images? This cannot be undone.')) return;
    await api('/me', { method: 'DELETE' }); location.href = '/api/auth/logout';
  });
}

boot();
```

- [ ] **Step 3: Deploy**

Run: `cd publisher && npx -y vercel@latest deploy --prod --yes`

- [ ] **Step 4: Manual check against the Content Sharing Guidelines**

Sign in at `https://arco-publisher.vercel.app/app.html` with a TikTok account and tick each:
- [ ] Creator nickname and avatar appear after choosing the account, and change when switching account.
- [ ] Title field present, counts to 90.
- [ ] Privacy dropdown starts on "Select who can view…"; its options match that account's TikTok settings.
- [ ] Allow comments is shown and unchecked by default; Duet and Stitch are shown and disabled with the "Video posts only" note.
- [ ] Disclosure toggle is off by default; turning it on shows Your brand / Branded content; with neither ticked the button is disabled and the note explains why.
- [ ] Your brand → label "Promotional content"; Branded content → "Paid partnership"; Branded content removes "Only me".
- [ ] Consent line mentions Music Usage Confirmation, plus Branded Content Policy when Branded content is ticked.
- [ ] Every slide appears in the preview before posting.
- [ ] Post now shows "Posting…" and then "Published" only after TikTok confirms.
- [ ] Schedule refuses a time under 5 minutes ahead; a scheduled post appears in Calendar at the same local time.
- [ ] Cancel, Edit and Retry work from the Calendar.
- [ ] No watermark or overlay is added to any image.

- [ ] **Step 5: Commit**

```bash
git add publisher/public/app.html publisher/public/app.js
git commit -m "publisher: web app for composing, scheduling and managing posts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 11: Product page, privacy policy and terms

**Files:**
- Modify: `publisher/public/index.html` (body only; keep the `<head>` and its `<style>`), `publisher/public/privacy.html`, `publisher/public/terms.html` (the `<article class="doc">` contents), `publisher/public/support.html` (one paragraph)

**Interfaces:**
- Consumes: `/app.html` (Task 10).
- Produces: a home page that describes a tool for any creator, with Privacy and Terms linked in the header and footer; policies that match the Worker's stored data and retention exactly.

- [ ] **Step 1: Replace the home page body**

In `publisher/public/index.html`, delete everything from `<body>` to `</html>` (including the old `<script type="module">…</script>` posting tool) and put:
```html
<body>
<div class="wrap">
  <header>
    <h1><a href="/" style="color:inherit;text-decoration:none;display:inline-flex;align-items:center;gap:10px"><img src="/icon.png" alt="" class="logo" width="30" height="30">ARCO Publisher</a></h1>
    <nav>
      <a href="#how">How it works</a>
      <a href="#access">What we access</a>
      <a href="#faq">FAQ</a>
      <a href="/support.html">Support</a>
      <a href="/privacy.html">Privacy</a>
      <a href="/terms.html">Terms</a>
    </nav>
  </header>

  <section class="hero">
    <img src="/icon.png" alt="ARCO" class="logo" width="64" height="64" style="width:64px;height:64px;border-radius:16px;margin-bottom:22px">
    <h2>Schedule your TikTok photo posts. Review every setting first.</h2>
    <p>ARCO Publisher is a free tool for creators. Sign in with TikTok, upload your photos, and post them
      now or at the time you choose. Every post shows your account, who can view it, comments, disclosure and a
      full preview before it goes out, and it publishes through TikTok's official Content Posting API.</p>
    <div class="cta">
      <a class="btn" href="/app.html">Open ARCO Publisher</a>
      <a class="btn sec" href="#how">How it works</a>
    </div>
  </section>

  <section class="s" id="how">
    <h3>How it works</h3>
    <p class="lead">Four steps, and you confirm each post yourself.</p>
    <div class="steps">
      <div class="step"><span class="n">1</span><b>Sign in with TikTok</b>
        <span>No new password. Connect more accounts later with Add account.</span></div>
      <div class="step"><span class="n">2</span><b>Upload your photos</b>
        <span>Up to 35 JPG or PNG images per post. Reorder them and pick the cover.</span></div>
      <div class="step"><span class="n">3</span><b>Review the settings</b>
        <span>Who can view it comes from your TikTok settings and starts empty. Comments, music and disclosure are your choice.</span></div>
      <div class="step"><span class="n">4</span><b>Post now or schedule</b>
        <span>We publish at your time and show TikTok's result in your calendar, with a link to the live post.</span></div>
    </div>
  </section>

  <section class="s" id="access">
    <h3>What we access</h3>
    <p class="lead">Three TikTok permissions, used only for what they say.</p>
    <table class="acc">
      <tr><th>Permission</th><th>Used for</th><th>Details</th></tr>
      <tr><td>user.info.basic</td><td>Showing which account you post to</td>
        <td>Your nickname and avatar, shown on the posting form.</td></tr>
      <tr><td>video.publish</td><td>Publishing the photo posts you confirm</td>
        <td>With the privacy, interaction and disclosure settings you chose for that post.</td></tr>
      <tr><td>video.upload</td><td>Part of TikTok's Content Posting API</td>
        <td>Granted with the API. ARCO Publisher does not send drafts to your inbox.</td></tr>
    </table>
  </section>

  <section class="s" id="limits">
    <h3>Free, with fair limits</h3>
    <p class="lead">Up to 10 connected accounts and 30 scheduled posts at a time. Photos are deleted 7 days after their post
      is published, fails, or is cancelled. You can delete everything at any time in Settings.</p>
  </section>

  <section class="s faq" id="faq">
    <h3>FAQ</h3>
    <details><summary>Do I need a password?</summary>
      <p>No. You sign in with TikTok. We never see your TikTok password.</p></details>
    <details><summary>Which privacy options can I choose?</summary>
      <p>Exactly the ones your TikTok account offers, read from TikTok each time. The choice starts empty so it is always yours.</p></details>
    <details><summary>What do "Promotional content" and "Paid partnership" mean?</summary>
      <p>They are TikTok's disclosure labels. Your brand labels the post as promotional content; Branded content labels it as a
      paid partnership and cannot be posted as Only me.</p></details>
    <details><summary>Why are Duet and Stitch off?</summary>
      <p>They only apply to videos. ARCO Publisher posts photo slideshows.</p></details>
    <details><summary>Can I change a scheduled post?</summary>
      <p>Yes, until it starts publishing: edit or cancel it from the calendar.</p></details>
    <details><summary>Who makes this?</summary>
      <p>The team behind ARCO: Day Planner &amp; Focus. We use ARCO Publisher for our own TikTok accounts too.</p></details>
  </section>

  <footer>
    <span>© 2026 ARCO Publisher</span>
    <span class="sp"></span>
    <a href="/support.html">Support</a>
    <a href="/privacy.html">Privacy</a>
    <a href="/terms.html">Terms</a>
    <a href="https://apps.apple.com/app/id6761037446" target="_blank" rel="noopener">ARCO for iOS</a>
  </footer>
</div>
</body>
</html>
```

- [ ] **Step 2: Replace the privacy policy article**

In `publisher/public/privacy.html`, replace the contents of `<article class="doc">…</article>` with:
```html
    <h2>Privacy Policy</h2>
    <div class="date">Effective 1 October 2026</div>
    <p>ARCO Publisher is a free web tool for scheduling TikTok photo posts, operated by the maker of ARCO: Day Planner &amp; Focus
      ("we"). This policy explains what we store when you use it and for how long.</p>
    <h3>What we store</h3>
    <ul>
      <li><b>For each connected TikTok account:</b> TikTok's account identifier (open_id), your username, nickname and avatar
        link, and a refresh token that lets us publish the posts you schedule. The refresh token is encrypted.</li>
      <li><b>For each post:</b> the photos you uploaded, the title, caption, settings you chose, the scheduled time, and
        TikTok's result (publish id, status, the public post id, or the failure reason).</li>
      <li><b>Sign-in:</b> a session cookie in your browser and, if you create one, an API key. We keep only a one-way hash of each.</li>
    </ul>
    <h3>What we do not do</h3>
    <ul>
      <li>We do not read your other posts, followers, messages or statistics.</li>
      <li>We do not sell or share your data, and we do not run advertising or analytics trackers.</li>
      <li>We never edit your photos beyond resizing large images, and never add watermarks.</li>
    </ul>
    <h3>How long we keep it</h3>
    <ul>
      <li>Photos: deleted 7 days after their post is published, fails, or is cancelled. Photos that never become part of a
        post are deleted after 24 hours.</li>
      <li>Post records: until you delete your workspace.</li>
      <li>Sessions: 30 days.</li>
    </ul>
    <h3>Your choices</h3>
    <p><b>Disconnect</b> an account in Settings to delete its token and cancel its scheduled posts. <b>Delete workspace</b>
      removes all of your accounts, posts and photos immediately. You can also revoke access in TikTok under Settings and
      privacy › Security &amp; permissions › Apps and services.</p>
    <h3>Where it runs</h3>
    <p>The website runs on Vercel and the posting service on Cloudflare. Both keep standard request logs (IP address, time,
      path) for a short period for security and operations.</p>
    <h3>Contact</h3>
    <p><a href="mailto:thinht7110@gmail.com?subject=ARCO%20Publisher%20privacy">thinht7110@gmail.com</a></p>
```

- [ ] **Step 3: Replace the terms article**

In `publisher/public/terms.html`, replace the contents of `<article class="doc">…</article>` with:
```html
    <h2>Terms of Service</h2>
    <div class="date">Effective 1 October 2026</div>
    <h3>1. The service</h3>
    <p>ARCO Publisher lets you publish and schedule photo posts to TikTok accounts you connect. It is free, provided as is,
      without warranty, and may change or stop at any time.</p>
    <h3>2. Your accounts and content</h3>
    <p>Connect only accounts you own or are authorised to manage, and post only content you have the rights to. You are
      responsible for your posts, which remain subject to
      <a href="https://www.tiktok.com/legal/page/global/terms-of-service/en">TikTok's Terms of Service</a>, Community Guidelines,
      <a href="https://www.tiktok.com/legal/page/global/bc-policy/en">Branded Content Policy</a> and
      <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en">Music Usage Confirmation</a>.
      Do not use the service to repost content taken from other creators or platforms.</p>
    <h3>3. Disclosure</h3>
    <p>If a post promotes you, a brand, a product or a service, use the disclosure setting. TikTok's labels cannot be changed
      after posting.</p>
    <h3>4. Limits</h3>
    <p>Free use is limited to 10 connected accounts and 30 scheduled posts per workspace. TikTok's own limits also apply. We may
      suspend workspaces that abuse the service or TikTok's rules.</p>
    <h3>5. Liability</h3>
    <p>To the extent the law allows, we are not liable for posts that fail, are delayed, or are removed by TikTok, or for any
      loss arising from use of the service.</p>
    <h3>6. Changes</h3>
    <p>We may update these terms; the effective date above changes when we do.</p>
    <h3>Contact</h3>
    <p><a href="mailto:thinht7110@gmail.com?subject=ARCO%20Publisher%20terms">thinht7110@gmail.com</a></p>
```

- [ ] **Step 4: Update support**

In `publisher/public/support.html`, replace the paragraph under "Something did not post" with:
```html
    <p>Open the Calendar: a failed post shows TikTok's reason and a Retry button. The usual causes are an account that needs
      reconnecting (Settings › Reconnect), a privacy choice the account no longer offers (Edit the post and choose again), or a
      temporary TikTok error, which we retry automatically three times.</p>
```

- [ ] **Step 5: Deploy and check**

Run: `cd publisher && npx -y vercel@latest deploy --prod --yes`
Check: `curl -s https://arco-publisher.vercel.app/ | grep -c 'Open ARCO Publisher'` → `1`; `curl -s https://arco-publisher.vercel.app/ | grep -c 'our own TikTok accounts\|internal'` → `0`; Privacy and Terms links visible without opening a menu at desktop and 400px widths.

- [ ] **Step 6: Commit**

```bash
git add publisher/public/index.html publisher/public/privacy.html publisher/public/terms.html publisher/public/support.html
git commit -m "publisher: product page and policies for a public tool

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---
### Task 12: The ARCO dashboard posts through ARCO Publisher

**Files:**
- Create: `tools/pubapi.py`, `tools/test_pubapi.py`
- Modify: `tools/dashboard.py` — `run_publish` (around line 753), the `/api/schedule` handler (around line 3843), `card()` action (around line 9056), `scheduleDirect()` text (around line 9545), `tiktokView()` (around line 7784), plus a new `/api/pub/posts` GET route next to `/api/ig`
- Modify: `.env` (user adds `PUBLISHER_API_KEY`)

**Interfaces:**
- Consumes: Worker API through `https://arco-publisher.vercel.app/api/v1` with `Authorization: Key apk_…` (Tasks 3–7, 9).
- Produces (`tools/pubapi.py`):
  - `class PubError(Exception)` with `.status`
  - `class PubAPI(base, key, timeout=60)` with `accounts() → list`, `creator_info(account_id) → dict`, `upload(path) → key`, `create_post(account_id, image_keys, title, caption, settings, scheduled_at=None) → post`, `list_posts(frm, to) → list`, `cancel(post_id) → post`
  - `account_ids(api, dashboard_accounts) → {dashboard_key: api_account_id}` (matched on `username == label`)
  - `api_settings(panel_settings) → API settings dict` (panel keys `privacy, disable_comment, auto_add_music, brand_organic, branded_content`)
  - `title_caption(hooks_path, topic) → (title, caption)` (same rule as autopost: hooks.json entry, else the humanised slug and empty caption)
  - `send_topic(api, account_id, drafts_dir, hooks_path, topic, panel_settings, scheduled_at=None) → post`
- Produces (dashboard): `POST /api/publish_direct` and `POST /api/schedule` with `mode: 'direct'` now create posts on ARCO Publisher; `GET /api/pub/posts?from&to` returns `{posts: [...with 'account' = dashboard key]}`.

- [ ] **Step 1: Write the failing client tests**

`tools/test_pubapi.py`:
```python
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import pubapi


class Fake(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *a):
        pass

    def _reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _record(self):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        Fake.calls.append({'method': self.command, 'path': self.path, 'auth': self.headers.get('Authorization'),
                           'type': self.headers.get('Content-Type'), 'raw': raw})
        return raw

    def do_GET(self):
        self._record()
        if self.path == '/v1/accounts':
            return self._reply(200, {'accounts': [{'id': 'acc_a', 'username': 'arco.app'},
                                                  {'id': 'acc_b', 'username': 'getarcoapp'}]})
        if self.path.startswith('/v1/posts'):
            return self._reply(200, {'posts': []})
        return self._reply(404, {'error': 'Not found'})

    def do_POST(self):
        raw = self._record()
        if self.path == '/v1/media':
            return self._reply(200, {'key': f'ws_1/{len(Fake.calls)}.jpg'})
        if self.path == '/v1/posts':
            body = json.loads(raw)
            if not body['settings'].get('privacy_level'):
                return self._reply(400, {'error': 'Choose who can view this post'})
            return self._reply(200, {'id': 'pst_1', **body})
        return self._reply(404, {'error': 'Not found'})


class PubApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(('127.0.0.1', 0), Fake)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.api = pubapi.PubAPI(f'http://127.0.0.1:{cls.srv.server_port}/v1', 'apk_test')

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Fake.calls.clear()

    def test_account_ids_match_on_username(self):
        ids = pubapi.account_ids(self.api, [{'key': 'vn', 'label': 'arco.app'},
                                            {'key': 'getarco', 'label': 'getarcoapp'},
                                            {'key': 'us', 'label': 'emiliagonzalez389'}])
        self.assertEqual(ids, {'vn': 'acc_a', 'getarco': 'acc_b'})
        self.assertEqual(Fake.calls[0]['auth'], 'Key apk_test')

    def test_api_settings_maps_panel_keys(self):
        self.assertEqual(pubapi.api_settings({'privacy': 'SELF_ONLY', 'disable_comment': True}),
                         {'privacy_level': 'SELF_ONLY', 'disable_comment': True, 'auto_add_music': False,
                          'brand_organic': False, 'branded_content': False})

    def test_send_topic_uploads_slides_in_order_then_creates_the_post(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, 'drafts', 'my-topic'))
            for name in ('10.jpg', '2.jpg', '1.jpg', 'notes.txt'):
                with open(os.path.join(d, 'drafts', 'my-topic', name), 'wb') as f:
                    f.write(b'\xff\xd8\xff' + name.encode())
            hooks = os.path.join(d, 'hooks.json')
            with open(hooks, 'w') as f:
                json.dump({'posts': [{'topic': 'my-topic', 'title': 'Hook', 'caption': 'Cap'}]}, f)
            post = pubapi.send_topic(self.api, 'acc_a', os.path.join(d, 'drafts'), hooks, 'my-topic',
                                     {'privacy': 'PUBLIC_TO_EVERYONE'}, scheduled_at=1_900_000_000)
        uploads = [c for c in Fake.calls if c['path'] == '/v1/media']
        self.assertEqual([c['raw'][3:] for c in uploads], [b'1.jpg', b'2.jpg', b'10.jpg'])
        self.assertTrue(all(c['type'] == 'image/jpeg' for c in uploads))
        self.assertEqual(post['title'], 'Hook')
        self.assertEqual(post['caption'], 'Cap')
        self.assertEqual(post['scheduled_at'], 1_900_000_000)
        self.assertEqual(len(post['image_keys']), 3)

    def test_title_caption_falls_back_to_the_slug(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(pubapi.title_caption(os.path.join(d, 'missing.json'), 'best-for-last-5'),
                             ('Best For Last 5', ''))

    def test_errors_carry_the_server_message(self):
        with self.assertRaises(pubapi.PubError) as ctx:
            self.api.create_post('acc_a', ['k'], 't', 'c', {'privacy_level': ''})
        self.assertEqual(str(ctx.exception), 'Choose who can view this post')
        self.assertEqual(ctx.exception.status, 400)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && python3 -m unittest test_pubapi -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pubapi'`.

- [ ] **Step 3: Implement the client**

`tools/pubapi.py`:
```python
"""A small client for the ARCO Publisher API (the Cloudflare Worker).

The dashboard is one API client among the tool's users: it uploads a topic's
slides and creates the post, and ARCO Publisher publishes it at the chosen
time with no laptop involved. Standard library only, like the dashboard.
"""
import json
import os
import re
import urllib.error
import urllib.request

TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}


class PubError(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status


class PubAPI:
    def __init__(self, base, key, timeout=60):
        self.base = base.rstrip('/')
        self.key = key
        self.timeout = timeout

    def _call(self, method, path, body=None, data=None, ctype=None):
        headers = {'Authorization': f'Key {self.key}'}
        if body is not None:
            data, ctype = json.dumps(body).encode(), 'application/json'
        if ctype:
            headers['Content-Type'] = ctype
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read() or b'{}').get('error')
            except ValueError:
                msg = None
            raise PubError(msg or f'ARCO Publisher returned HTTP {e.code}', e.code) from None
        except urllib.error.URLError as e:
            raise PubError(f'Could not reach ARCO Publisher: {e.reason}') from None

    def accounts(self):
        return self._call('GET', '/accounts')['accounts']

    def creator_info(self, account_id):
        return self._call('GET', f'/accounts/{account_id}/creator-info')

    def upload(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in TYPES:
            raise PubError(f'{os.path.basename(path)} is not a JPG or PNG')
        with open(path, 'rb') as f:
            return self._call('POST', '/media', data=f.read(), ctype=TYPES[ext])['key']

    def create_post(self, account_id, image_keys, title, caption, settings, scheduled_at=None):
        return self._call('POST', '/posts', body={
            'account_id': account_id, 'image_keys': image_keys, 'cover_index': 0,
            'title': title, 'caption': caption, 'settings': settings, 'scheduled_at': scheduled_at})

    def list_posts(self, frm, to):
        return self._call('GET', f'/posts?from={int(frm)}&to={int(to)}')['posts']

    def cancel(self, post_id):
        return self._call('DELETE', f'/posts/{post_id}')


def account_ids(api, dashboard_accounts):
    by_name = {a['username']: a['id'] for a in api.accounts()}
    return {a['key']: by_name[a['label']] for a in dashboard_accounts if a['label'] in by_name}


def api_settings(st):
    return {
        'privacy_level': st.get('privacy') or '',
        'disable_comment': bool(st.get('disable_comment')),
        'auto_add_music': bool(st.get('auto_add_music')),
        'brand_organic': bool(st.get('brand_organic')),
        'branded_content': bool(st.get('branded_content')),
    }


def _natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


def title_caption(hooks_path, topic):
    try:
        with open(hooks_path) as f:
            posts = json.load(f).get('posts') or []
    except (OSError, ValueError):
        posts = []
    post = next((p for p in posts if p.get('topic') == topic), {})
    title = post.get('title') or re.sub(r'\b\w', lambda m: m.group().upper(), re.sub(r'[-_]+', ' ', topic))
    return title, post.get('caption') or ''


def send_topic(api, account_id, drafts_dir, hooks_path, topic, panel_settings, scheduled_at=None):
    folder = os.path.join(drafts_dir, topic)
    slides = sorted((f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in TYPES), key=_natural)
    if not slides:
        raise PubError(f'No JPG or PNG slides in drafts/{topic}')
    keys = [api.upload(os.path.join(folder, f)) for f in slides]
    title, caption = title_caption(hooks_path, topic)
    return api.create_post(account_id, keys, title[:90], caption, api_settings(panel_settings), scheduled_at)
```

- [ ] **Step 4: Run to verify pass**

Run: `cd tools && python3 -m unittest test_pubapi -v`
Expected: 5 tests OK.

- [ ] **Step 5: Wire the dashboard backend**

In `tools/dashboard.py`:

(a) Next to the other imports near the top, add:
```python
import pubapi
```

(b) Directly after `def _env():` (around line 690), add:
```python
PUBLISHER_API = 'https://arco-publisher.vercel.app/api/v1'
_pub_ids = {'at': 0, 'map': {}}


def pub_api():
    key = _env().get('PUBLISHER_API_KEY')
    if not key:
        raise pubapi.PubError('Add PUBLISHER_API_KEY to .env (ARCO Publisher > Settings > API key).')
    return pubapi.PubAPI(_env().get('PUBLISHER_API') or PUBLISHER_API, key)


def pub_account_id(api, key):
    # The mapping only changes when an account is connected or removed.
    if time.time() - _pub_ids['at'] > 600 or key not in _pub_ids['map']:
        _pub_ids['map'] = pubapi.account_ids(api, ACCOUNTS)
        _pub_ids['at'] = time.time()
    if key not in _pub_ids['map']:
        label = next((a['label'] for a in ACCOUNTS if a['key'] == key), key)
        raise pubapi.PubError(f'@{label} is not connected to ARCO Publisher. Add it there under Settings > Add account.')
    return _pub_ids['map'][key]


def pub_send(topic, key, settings, at=None):
    api = pub_api()
    return pubapi.send_topic(api, pub_account_id(api, key), DRAFTS, HOOKS, topic, settings,
                             int(at) if at else None)
```

(c) Replace the whole body of `run_publish(topic, key, settings)` (from `ok, why = pages_ready(topic)` down to just before `print(f'[publish] …`) with:
```python
    # ARCO Publisher does the posting now; this sends the slides and waits a
    # few minutes for the result so the delivery log can say "published".
    try:
        post = pub_send(topic, key, settings)
        rec = {'status': 'SENT', 'detail': 'posting via ARCO Publisher', 'at': time.time(),
               'direct': True, 'pub_post_id': post['id']}
        api = pub_api()
        for _ in range(30):
            time.sleep(10)
            now_ = time.time()
            found = next((p for p in api.list_posts(now_ - 3600, now_ + 60) if p['id'] == post['id']), None)
            if found and found['status'] == 'published':
                rec.update(detail='published directly', published=True, published_at=time.time(),
                           post_url=found.get('post_url'))
                break
            if found and found['status'] == 'failed':
                rec = {'status': 'FAILED', 'detail': found.get('fail_reason') or 'TikTok rejected the post',
                       'at': time.time()}
                break
    except pubapi.PubError as exc:
        rec = {'status': 'FAILED', 'detail': str(exc), 'at': time.time()}
```
Keep the `print(...)`, the `with _lock:` block that saves the delivery log, and `return rec` as they are.

(d) In the `/api/schedule` handler, replace the `if mode == 'direct':` block (the `direct_blocked` loop) and the following `sc.append(...)` so that direct jobs go to ARCO Publisher and only draft jobs stay local:
```python
                    if mode == 'direct':
                        # Scheduled posts live on ARCO Publisher, which fires
                        # them with the laptop closed. Nothing is kept here.
                        try:
                            at = float(body['at'])
                            for n, key in enumerate(body.get('accounts') or []):
                                pub_send(body['topic'], key, st, at + n * 60 * int(body.get('stagger_min') or 0))
                        except pubapi.PubError as exc:
                            return self._send(400, {'error': str(exc)})
                        save_schedules(sc)
                        return self._send(200, {'ok': True, 'where': 'arco-publisher'})
                    sc.append({'topic': body['topic'], 'at': float(body['at']),
                               'accounts': body.get('accounts') or [],
                               'stagger_min': int(body.get('stagger_min') or 0),
                               'mode': mode, 'settings': {},
                               'done': False})
```

(e) Next to `if path == '/api/ig':` in the GET handler, add:
```python
        if path == '/api/pub/posts':
            q = parse_qs(urlparse(self.path).query)
            try:
                api = pub_api()
                ids = {v: k for k, v in pubapi.account_ids(api, ACCOUNTS).items()}
                posts = api.list_posts(float(q['from'][0]), float(q['to'][0]))
            except (pubapi.PubError, KeyError, ValueError) as exc:
                return self._send(200, {'posts': [], 'error': str(exc)})
            for p in posts:
                p['account'] = ids.get(p['account_id'], '')
            return self._send(200, {'posts': posts})
```
If `parse_qs`/`urlparse` are not already imported, add `from urllib.parse import parse_qs, urlparse` at the top.

- [ ] **Step 6: Wire the dashboard UI**

(a) In `card(p)`, replace the "Draft to all" button:
```js
      <button class="cta sec" onclick="cardDraft(event,'${p.topic}')">Draft to all</button></span>`;
```
with:
```js
      <button class="cta" onclick="event.stopPropagation();sendTo('${p.topic}')">Schedule</button></span>`;
```
and drop the `${p.approved ? … : ''}` Approved button before it (scheduling is the approval).

(b) In `scheduleDirect()`, change the modal body text to:
```js
    body:`ARCO Publisher posts it to ${a.label} at the time you pick, visible to `
        +`"${priv}". Your laptop can be closed.`,
```
and the success message to:
```js
      say('Scheduled on ARCO Publisher for '+new Date(at*1000).toLocaleString()+'.');
```

(c) Replace `tiktokView()` with a week calendar above the built list:
```js
let tkWeek = 0, tkPosts = null;
async function loadTkWeek(){
  const d = new Date(); d.setHours(0,0,0,0);
  d.setDate(d.getDate() - ((d.getDay()+6)%7) + tkWeek*7);
  const from = Math.floor(d.getTime()/1000);
  const r = await (await fetch(`/api/pub/posts?from=${from}&to=${from+7*86400}`)).json();
  tkPosts = {from, list: r.posts || [], error: r.error};
  if(filter==='tiktok') render();
}
function tiktokView(){
  if(!tkPosts){ loadTkWeek(); }
  const todo = DATA.posts.filter(p=>stateOf(p)==='review').sort((a,b)=>whenOf(b)-whenOf(a));
  document.getElementById('cnt').textContent = `${todo.length} to schedule`;
  const from = tkPosts ? tkPosts.from : 0;
  const days = [...Array(7)].map((_,i)=>new Date((from+i*86400)*1000));
  const cal = !tkPosts ? '<div class="empty">Reading the schedule…</div>'
    : tkPosts.error ? `<div class="cwarn"><b>ARCO Publisher did not answer.</b> ${esc(tkPosts.error)}</div>`
    : `<div class="wknav">
        <button class="wkarr" onclick="tkWeek--;tkPosts=null;render()" ${tkWeek<=0?'disabled':''}>‹</button>
        <span class="wkr">${days[0].toLocaleDateString('en-GB',{day:'numeric',month:'short'})} – ${days[6].toLocaleDateString('en-GB',{day:'numeric',month:'short'})}</span>
        <button class="wkarr" onclick="tkWeek++;tkPosts=null;render()">›</button></div>
      <div class="weeklist">${days.map(d=>{
        const ps = tkPosts.list.filter(p=>new Date(p.scheduled_at*1000).toDateString()===d.toDateString());
        return `<h4 class="csub">${d.toLocaleDateString('en-GB',{weekday:'long',day:'2-digit',month:'short'})}</h4>`
          + (ps.map(p=>`<div class="qrow ${p.status}">
              <span class="tm">${new Date(p.scheduled_at*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span>
              <img class="sth" src="${esc(p.images[p.cover_index]||'')}" alt="" loading="lazy">
              <span class="sw"><b>${esc(p.title||p.id)}</b><i>@${esc(p.username)}${p.fail_reason?' · '+esc(p.fail_reason):''}</i></span>
              ${p.post_url?`<a class="btn sec sm" href="${esc(p.post_url)}" target="_blank" rel="noopener">View</a>`:''}
              <span class="st ${p.status}">${esc(p.status)}</span></div>`).join('')
             || '<div class="qrow empty"><span class="sw"><i>nothing scheduled</i></span></div>');
      }).join('')}</div>`;
  return `<h4 class="csub">This week on ARCO Publisher</h4>${cal}
    <h4 class="csub">Built, not scheduled</h4>
    ${todo.length ? groups(todo) : '<div class="empty">Nothing waiting — build more.</div>'}`;
}
```
After a successful schedule or post-now, set `tkPosts = null` so the calendar reloads: add `tkPosts = null;` before `await load(); render();` in `scheduleDirect()`'s action and before `await load();` in `publishDirect()`.

- [ ] **Step 7: Restart and check**

Run: `launchctl kickstart -k gui/$(id -u)/com.arco.local && sleep 3 && curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:4501/`
Expected: `200`. Open the TikTok page: the calendar shows "ARCO Publisher did not answer … Add PUBLISHER_API_KEY" until Task 13 Step 2 is done.

- [ ] **Step 8: Commit**

```bash
git add tools/pubapi.py tools/test_pubapi.py tools/dashboard.py
git commit -m "dashboard: schedule and post through ARCO Publisher, show its calendar

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PhByxZHp7hJuhy8g5LLHKH"
```

---

### Task 13: End-to-end check, demo, and the audit submission

**Files:** none (verification and the portal).

**Interfaces:**
- Consumes: everything above.
- Produces: verified public flow, a new demo video, the submitted Direct Post application.

- [ ] **Step 1: Connect ARCO's accounts (the user)**

On `https://arco-publisher.vercel.app/app.html`, sign in with arco.app, then Settings › Add account for getarcoapp, emiliagonzalez389, maxmilian.dev, productivity_god and jackson21.dev (switch the logged-in TikTok account in the browser before each).
Check: Settings lists 6 accounts, none marked Reconnect.

- [ ] **Step 2: API key for the dashboard (the user)**

Settings › Create key. Add `PUBLISHER_API_KEY=apk_…` to `~/SIXSIX/arco-app/.env`.
Check: the dashboard's TikTok page shows this week's (empty) calendar with no error.

- [ ] **Step 3: A stranger's account through the web app**

A TikTok account that is not one of ARCO's six signs in on the web app, uploads 3 photos, fills the panel, and schedules 10 minutes ahead.
Check: the post appears in that workspace's Calendar as `queued`, then `published` within ~2 minutes of its time, and appears on that profile. Before the audit passes TikTok forces it to Only me; that is expected and still proves the flow.

- [ ] **Step 4: ARCO through the dashboard**

In the dashboard, pick a built post, Schedule, choose getarcoapp, a privacy option, and a time 10 minutes ahead. Close the laptop lid until after the time.
Check: on reopening, the dashboard calendar and the web app calendar both show `published`, and the post is on getarcoapp (private until the audit).

- [ ] **Step 5: Record the demo (the user)**

About 90 seconds, screen recording of `arco-publisher.vercel.app` in a normal browser window, password manager hidden:
1. Home page, scroll once to show How it works, What we access, and the Privacy/Terms links.
2. Open ARCO Publisher → Continue with TikTok → consent screen (pause so the permissions are readable) → back in the app.
3. New post: upload 3–5 photos, pick a cover, type a title and caption.
4. Choose the account (nickname and avatar appear), open the "Who can view" dropdown so its options show, pick one.
5. Show Allow comments (off by default), Duet/Stitch disabled, disclosure toggle, turn it on to show the labels, turn it off again.
6. Show the preview and the consent line. Choose Post now → wait for "Published".
7. Open the TikTok profile and show the post.
8. Back in the app, open Calendar, and Settings (Disconnect, API key, Delete workspace visible).

Re-encode for the upload limit:
```bash
ffmpeg -i "<recording>.mov" -vf "scale=1920:-2" -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart -an arco-publisher-demo-v2.mp4
```
Check: the file is under 5 MB; if not, raise `-crf` by 2 and repeat.

- [ ] **Step 6: Submit the Direct Post application**

Open `https://developers.tiktok.com/application/content-posting-api` (the form does not keep drafts). Fill:
- Full Name: `Thinh Tran`; Organization name: `ARCO`; Organization website: `https://chupappi7.github.io/arco-app/`
- Describe your organization's work: `ARCO is an independent developer of consumer apps, including ARCO: Day Planner & Focus on the App Store. We also build ARCO Publisher (arco-publisher.vercel.app), a free web tool that lets TikTok creators publish and schedule their own photo posts.`
- App ID: `7664031914722002960`
- Goal: `ARCO Publisher lets creators sign in with TikTok, upload their own photos, and publish or schedule them as TikTok photo posts. Direct Post lets a post go live at the time the creator chose instead of waiting in their inbox. Every post is confirmed by the creator on our posting page, which follows the Content Sharing Guidelines: creator info, privacy with no default, interaction settings, commercial disclosure, preview, and publish status. We never post content taken from other platforms.`
- Daily users: `Less than 100`; How determined: `ARCO Publisher is a new tool with a small number of creators, including our own accounts. We expect well under 100 publishing users a day in the first months.`
- Video: `arco-publisher-demo-v2.mp4`
- Data saved: `Per creator: TikTok open_id, display name, avatar URL and an encrypted refresh token. Per post: publish_id, status and the public post ID. Uploaded images are deleted 7 days after posting. Creators can disconnect or delete their data at any time.`
Stop on the Review page. The user reads it, ticks the three declarations, and presses Submit.

- [ ] **Step 7: Record the state**

Update `~/.claude/projects/-Users-thinh/memory/project-tiktok-manager.md`: Worker URL, D1/R2 names, that ARCO posts via `PUBLISHER_API_KEY`, and the submission date.
