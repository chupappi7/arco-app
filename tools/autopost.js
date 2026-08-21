#!/usr/bin/env node
'use strict';

/**
 * autopost.js — push a drafts/<topic>/ folder of JPGs to the TikTok inbox
 * as a photo draft, via the Content Posting API using PULL_FROM_URL.
 *
 * Usage:
 *   node tools/autopost.js <topic> [options]
 *
 * Options:
 *   --title "..."        Post title       (default: topic slug, humanised)
 *   --description "..."  Post description (default: from tools/hooks.json caption)
 *   --cover N            0-based cover slide index (default 0)
 *   --base-url URL       Override the public base URL
 *   --direct-post        Publish immediately instead of drafting to the inbox.
 *                        Requires the video.publish scope; drafts only need video.upload.
 *   --privacy LEVEL      Privacy level for --direct-post (default SELF_ONLY)
 *   --wait               Poll publish status until it leaves PROCESSING
 *   --dry-run            Run every check and print the payload, but don't post
 *
 * Env (secrets live here and nowhere else):
 *   TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN
 *
 * Mint TIKTOK_REFRESH_TOKEN once with: node tools/tiktok-auth.js
 */

const fs = require('fs');
const path = require('path');
const {
  refreshAccessToken,
  initPhotoPost,
  fetchPostStatus,
  fetchWithRetry,
  TikTokError,
  sleep,
} = require('./lib/tiktok');

const REPO_ROOT = path.resolve(__dirname, '..');
const DEFAULT_BASE_URL = 'https://chupappi7.github.io/arco-app/';
const HOOKS_PATH = path.join(__dirname, 'hooks.json');

// TikTok limits: max 35 images per photo post, max 20MB per image.
const MAX_IMAGES = 35;
const MAX_IMAGE_BYTES = 20 * 1024 * 1024;

function parseArgs(argv) {
  const opts = {
    topic: null,
    title: null,
    description: null,
    cover: 0,
    baseUrl: process.env.ARCO_BASE_URL || DEFAULT_BASE_URL,
    directPost: false,
    privacy: 'SELF_ONLY',
    wait: false,
    dryRun: false,
    account: 'vn',
  };

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--title': opts.title = argv[++i]; break;
      case '--description': opts.description = argv[++i]; break;
      case '--cover': opts.cover = Number(argv[++i]); break;
      case '--base-url': opts.baseUrl = argv[++i]; break;
      case '--direct-post': opts.directPost = true; break;
      case '--privacy': opts.privacy = argv[++i]; break;
      case '--wait': opts.wait = true; break;
      case '--dry-run': opts.dryRun = true; break;
      case '--us': opts.account = 'us'; break;
      case '--account': opts.account = argv[++i]; break;
      case '-h':
      case '--help': opts.help = true; break;
      default:
        if (a.startsWith('-')) throw new Error(`unknown option: ${a}`);
        if (opts.topic) throw new Error(`unexpected argument: ${a}`);
        opts.topic = a;
    }
  }
  return opts;
}

function usage() {
  console.log(`
Usage: node tools/autopost.js <topic> [options]

  --title "..."        post title (default: humanised topic slug)
  --description "..."  post description (default: caption from hooks.json)
  --cover N            0-based cover slide index (default 0)
  --base-url URL       public base URL (default ${DEFAULT_BASE_URL})
  --direct-post        publish now instead of drafting to inbox (needs video.publish)
  --privacy LEVEL      privacy for --direct-post (default SELF_ONLY)
  --wait               poll publish status until processing finishes
  --dry-run            validate and print the payload without posting
  --us                 post to the US account (getarcoapp) instead of arco.app
  --account NAME       vn (default, arco.app) or us (getarcoapp)

Env: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN (vn),
     TIKTOK_REFRESH_TOKEN_US (us)
`);
}

function requireEnv(name) {
  const v = process.env[name];
  if (!v || !v.trim()) {
    throw new Error(`missing required env var ${name} (see tools/README.md)`);
  }
  return v.trim();
}

/** Natural-sort the slide files so 02.jpg sorts before 10.jpg. */
function listSlides(topicDir) {
  if (!fs.existsSync(topicDir)) {
    throw new Error(`no such draft folder: ${path.relative(REPO_ROOT, topicDir)}`);
  }
  const files = fs
    .readdirSync(topicDir)
    .filter((f) => /\.jpe?g$/i.test(f))
    .sort((a, b) => a.localeCompare(b, 'en', { numeric: true, sensitivity: 'base' }));

  if (files.length === 0) {
    throw new Error(`no .jpg files in ${path.relative(REPO_ROOT, topicDir)}`);
  }
  if (files.length > MAX_IMAGES) {
    throw new Error(`${files.length} slides exceeds TikTok's ${MAX_IMAGES}-image limit`);
  }
  return files;
}

function humanise(slug) {
  return slug.replace(/[-_]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function readHooks() {
  if (!fs.existsSync(HOOKS_PATH)) return null;
  try {
    return JSON.parse(fs.readFileSync(HOOKS_PATH, 'utf8'));
  } catch (err) {
    console.warn(`  ! could not parse hooks.json (${err.message}) — continuing without it`);
    return null;
  }
}

/**
 * TikTok's pull service fails opaquely on unreachable, redirecting, or
 * oversized URLs, so verify every one locally before spending a post slot.
 * Requirements per the media-transfer guide: https, no 3xx, <=20MB each.
 */
async function preflight(urls) {
  console.log(`  verifying ${urls.length} public URL(s)...`);
  const problems = [];

  for (const url of urls) {
    if (!url.startsWith('https://')) {
      problems.push(`${url} — must be https`);
      continue;
    }

    let res;
    try {
      res = await fetchWithRetry(url, { method: 'HEAD', redirect: 'manual' }, { label: `HEAD ${url}` });
    } catch (err) {
      problems.push(`${url} — unreachable (${err.message})`);
      continue;
    }

    if (res.status >= 300 && res.status < 400) {
      problems.push(`${url} — redirects (HTTP ${res.status}); TikTok rejects redirecting URLs`);
      continue;
    }
    if (res.status !== 200) {
      problems.push(`${url} — HTTP ${res.status}`);
      continue;
    }

    const len = Number(res.headers.get('content-length'));
    if (Number.isFinite(len) && len > MAX_IMAGE_BYTES) {
      problems.push(`${url} — ${(len / 1024 / 1024).toFixed(1)}MB exceeds the 20MB per-image limit`);
    }
  }

  if (problems.length) {
    throw new Error(
      `preflight failed for ${problems.length} URL(s):\n    - ${problems.join('\n    - ')}\n` +
        `  If these were just committed, GitHub Pages may not have rebuilt yet.`
    );
  }
  console.log('  all URLs reachable, non-redirecting, and within size limits');
}

async function pollStatus({ accessToken, publishId }) {
  const DEADLINE_MS = 5 * 60 * 1000;
  const started = Date.now();
  let delay = 3000;

  while (Date.now() - started < DEADLINE_MS) {
    await sleep(delay);
    const data = await fetchPostStatus({ accessToken, publishId });
    const status = data.status;
    console.log(`  status: ${status}`);

    if (status !== 'PROCESSING_UPLOAD' && status !== 'PROCESSING_DOWNLOAD') {
      if (data.fail_reason) console.error(`  fail_reason: ${data.fail_reason}`);
      return data;
    }
    delay = Math.min(delay * 1.5, 15000);
  }

  console.warn('  ! still processing after 5 minutes — check the TikTok app');
  return null;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  if (opts.help || !opts.topic) {
    usage();
    process.exit(opts.topic ? 0 : 1);
  }

  const topicDir = path.join(REPO_ROOT, 'drafts', opts.topic);
  const files = listSlides(topicDir);

  if (!Number.isInteger(opts.cover) || opts.cover < 0 || opts.cover >= files.length) {
    throw new Error(`--cover must be between 0 and ${files.length - 1}`);
  }

  const baseUrl = opts.baseUrl.endsWith('/') ? opts.baseUrl : `${opts.baseUrl}/`;
  const urls = files.map((f) => `${baseUrl}drafts/${encodeURIComponent(opts.topic)}/${encodeURIComponent(f)}`);

  const hooks = readHooks();
  const post = hooks?.posts?.find((p) => p.topic === opts.topic);
  const title = opts.title || post?.title || humanise(opts.topic);
  const description = opts.description ?? post?.caption ?? '';

  console.log(`\nARCO -> TikTok  |  topic: ${opts.topic}`);
  console.log(`  slides: ${files.length} (${files.join(', ')})`);
  console.log(`  mode:   ${opts.directPost ? `DIRECT_POST (${opts.privacy})` : 'MEDIA_UPLOAD -> inbox draft'}`);
  console.log(`  title:  ${title}`);
  if (description) console.log(`  desc:   ${description.slice(0, 120)}${description.length > 120 ? '…' : ''}`);
  console.log(`  cover:  slide ${opts.cover} (${files[opts.cover]})`);

  // Fail on missing credentials before spending time on network preflight.
  // --dry-run deliberately needs no secrets.
  const ACCOUNTS = {
    vn: { env: 'TIKTOK_REFRESH_TOKEN', label: 'arco.app (VN)' },
    us: { env: 'TIKTOK_REFRESH_TOKEN_US', label: 'emiliagonzalez389 (US)' },
    getarco: { env: 'TIKTOK_REFRESH_TOKEN_GETARCO', label: 'getarcoapp' },
  };
  if (!ACCOUNTS[opts.account]) {
    throw new Error(`--account must be one of ${Object.keys(ACCOUNTS).join('/')}, got: ${opts.account}`);
  }
  const tokenVar = ACCOUNTS[opts.account].env;
  console.log(`  account: ${ACCOUNTS[opts.account].label}`);
  const creds = opts.dryRun
    ? null
    : {
        clientKey: requireEnv('TIKTOK_CLIENT_KEY'),
        clientSecret: requireEnv('TIKTOK_CLIENT_SECRET'),
        refreshToken: requireEnv(tokenVar),
      };

  await preflight(urls);

  if (opts.dryRun) {
    console.log('\n  --dry-run: payload that would be posted:\n');
    console.log(
      JSON.stringify(
        {
          media_type: 'PHOTO',
          post_mode: opts.directPost ? 'DIRECT_POST' : 'MEDIA_UPLOAD',
          post_info: {
            title,
            ...(description ? { description } : {}),
            ...(opts.directPost ? { privacy_level: opts.privacy } : {}),
          },
          source_info: { source: 'PULL_FROM_URL', photo_images: urls, photo_cover_index: opts.cover },
        },
        null,
        2
      )
    );
    console.log('\n  nothing was posted.');
    return;
  }

  console.log('\n  refreshing access token...');
  const tokens = await refreshAccessToken(creds);
  console.log(`  access token ok (expires in ${tokens.expiresIn}s, scope: ${tokens.scope})`);

  // TikTok rotates refresh tokens. If we don't surface the new one, the next
  // run fails with an expired-token error that looks like a config problem.
  if (tokens.refreshToken && tokens.refreshToken !== creds.refreshToken) {
    console.warn(
      `\n  ! TikTok rotated your refresh token. Update ${tokenVar} in your env to:\n` +
        `    ${tokens.refreshToken}\n`
    );
  }

  const requiredScope = opts.directPost ? 'video.publish' : 'video.upload';
  if (tokens.scope && !tokens.scope.split(/[,\s]+/).includes(requiredScope)) {
    console.warn(`  ! token scope is missing "${requiredScope}" — the post will likely fail`);
  }

  console.log('  initializing photo post...');
  const data = await initPhotoPost({
    accessToken: tokens.accessToken,
    photoUrls: urls,
    title,
    description,
    coverIndex: opts.cover,
    postMode: opts.directPost ? 'DIRECT_POST' : 'MEDIA_UPLOAD',
    privacyLevel: opts.privacy,
  });

  console.log(`\n  posted. publish_id: ${data.publish_id}`);
  if (!opts.directPost) {
    console.log('  open TikTok -> Profile -> Inbox/Drafts to review and publish.');
  }

  if (opts.wait) {
    console.log('\n  polling status...');
    await pollStatus({ accessToken: tokens.accessToken, publishId: data.publish_id });
  }
}

main().catch((err) => {
  if (err instanceof TikTokError) {
    console.error(`\nERROR  ${err.message}`);
    if (err.logId) console.error(`  log_id: ${err.logId}`);
    // The failure modes that actually bite in this pipeline.
    if (err.code === 'spam_risk_too_many_pending_share') {
      console.error('  TikTok allows at most 5 pending inbox shares per 24h. Publish or clear some drafts.');
    } else if (err.code === 'spam_risk_too_many_posts') {
      console.error('  Daily post limit reached. Try again tomorrow.');
    } else if (err.code === 'scope_not_authorized') {
      console.error('  Re-run tools/tiktok-auth.js and grant the video.upload scope.');
    } else if (err.code === 'url_ownership_unverified') {
      console.error('  Verify the domain under URL properties at developers.tiktok.com.');
    } else if (err.code === 'app_version_check_failed') {
      console.error('  The TikTok app on the target device must be v31.8 or newer for inbox drafts.');
    }
  } else {
    console.error(`\nERROR  ${err.message}`);
  }
  process.exit(1);
});
