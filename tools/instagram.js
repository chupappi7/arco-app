#!/usr/bin/env node
'use strict';

/**
 * instagram.js — publish a rendered post to Instagram as a carousel.
 *
 *   node tools/instagram.js <topic> --account vn
 *   node tools/instagram.js <topic> --account vn --dry-run
 *   node tools/instagram.js --refresh              (all accounts)
 *
 * Three calls, in order: one container per image, one carousel container
 * holding them, then publish. Instagram fetches the images itself over public
 * HTTPS, exactly as TikTok does, so the slides must be live on GitHub Pages
 * before this runs.
 *
 * Two things differ from the TikTok path and both matter:
 *
 *   - There is no draft inbox. media_publish puts the post on the profile
 *     immediately. Nothing here is reversible, so --dry-run prints the plan
 *     and the dashboard asks before it calls this.
 *   - Images must be 4:5 or wider. The 9:16 slides are refused, which is why
 *     this reads drafts/<topic>/ig/ and refuses to fall back to the originals.
 */
const fs = require('fs');
const path = require('path');
const https = require('https');

const REPO = path.resolve(__dirname, '..');
const PAGES = process.env.ARCO_PAGES_REPO || REPO;
const BASE_URL = process.env.ARCO_BASE_URL || 'https://chupappi7.github.io/arco-app/';
const HOOKS = path.join(__dirname, 'hooks.json');
const GRAPH = 'graph.instagram.com';
const API = '/v21.0';
const MAX_ITEMS = 10;           // Instagram's carousel ceiling
const POLL_MS = 3000;
const POLL_TRIES = 40;

const ACCOUNTS = {
  vn:      { token: 'IG_TOKEN',         user: 'IG_USER_ID',         minted: 'IG_TOKEN_MINTED' },
  getarco: { token: 'IG_TOKEN_GETARCO', user: 'IG_USER_ID_GETARCO', minted: 'IG_TOKEN_MINTED_GETARCO' },
  us:      { token: 'IG_TOKEN_US',      user: 'IG_USER_ID_US',      minted: 'IG_TOKEN_MINTED_US' },
};

function arg(name, fallback) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith('--')
    ? process.argv[i + 1] : fallback;
}
const has = (name) => process.argv.includes('--' + name);

function req(method, pathname, form) {
  const body = form ? new URLSearchParams(form).toString() : null;
  const opts = { host: GRAPH, path: pathname, method,
                 headers: body ? { 'Content-Type': 'application/x-www-form-urlencoded',
                                   'Content-Length': Buffer.byteLength(body) } : {} };
  return new Promise((resolve, reject) => {
    const r = https.request(opts, (res) => {
      let out = '';
      res.on('data', (d) => { out += d; });
      res.on('end', () => {
        let j;
        try { j = JSON.parse(out); } catch (e) {
          return reject(new Error(`${res.statusCode}: ${out.slice(0, 300)}`));
        }
        if (j.error) {
          // Meta's errors are readable; passing the message straight through
          // beats wrapping it in one of ours.
          return reject(new Error(`${j.error.message}${j.error.error_user_msg
            ? ' — ' + j.error.error_user_msg : ''}`));
        }
        resolve(j);
      });
    });
    r.on('error', reject);
    if (body) r.write(body);
    r.end();
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function creds(account) {
  const map = ACCOUNTS[account];
  if (!map) throw new Error(`unknown account "${account}" (vn, getarco, us)`);
  const token = process.env[map.token];
  const user = process.env[map.user];
  if (!token || !user) {
    throw new Error(`${map.token} / ${map.user} not set — run `
      + `node tools/instagram-auth.js --account ${account}`);
  }
  return { token, user, map };
}

function slideUrls(topic) {
  const dir = path.join(PAGES, 'drafts', topic, 'ig');
  if (!fs.existsSync(dir)) {
    throw new Error(`no drafts/${topic}/ig — run `
      + `python3 tools/variants.py ${topic} --ig first. The 9:16 originals are `
      + 'refused by the publishing API.');
  }
  const files = fs.readdirSync(dir)
    .filter((f) => /^\d+\.jpg$/.test(f)).sort();
  if (!files.length) throw new Error(`drafts/${topic}/ig is empty`);
  if (files.length > MAX_ITEMS) {
    throw new Error(`${files.length} slides; Instagram carousels hold ${MAX_ITEMS}`);
  }
  return files.map((f) => new URL(`drafts/${topic}/ig/${f}`, BASE_URL).href);
}

function caption(topic) {
  const raw = JSON.parse(fs.readFileSync(HOOKS, 'utf8'));
  const posts = Array.isArray(raw) ? raw : raw.posts;
  const rec = posts.find((p) => p.topic === topic);
  if (!rec || !(rec.caption || '').trim()) {
    throw new Error(`${topic} has no caption in hooks.json`);
  }
  // #creatorsearchinsights is a TikTok search-programme tag and does nothing
  // here, so it is dropped rather than shipped as noise.
  return rec.caption.replace(/#creatorsearchinsights/gi, '').replace(/\s+/g, ' ').trim();
}

async function reachable(urls) {
  // Pages lags a push. Publishing before the images serve fails on Meta's
  // side with a fetch error that reads like an account problem.
  for (const u of urls) {
    const ok = await new Promise((resolve) => {
      https.request(u, { method: 'HEAD' }, (res) => resolve(res.statusCode === 200))
        .on('error', () => resolve(false)).end();
    });
    if (!ok) throw new Error(`not serving yet: ${u}`);
  }
}

async function publish(topic, account) {
  // Slides and caption are checked before credentials on purpose: a dry run
  // is how you find out a post is not ready, and it should answer that
  // question on a machine that has never been authorised.
  const urls = slideUrls(topic);
  const text = caption(topic);

  if (has('dry-run')) {
    let auth = 'ok';
    try { creds(account); } catch (e) { auth = e.message; }
    console.log(JSON.stringify({ topic, account, slides: urls.length, auth,
                                 caption: text.slice(0, 120) + '…', urls }, null, 1));
    await reachable(urls);
    console.log('\nall slide urls serve. Nothing was sent.');
    return;
  }
  const { token, user } = creds(account);
  await reachable(urls);

  const children = [];
  for (const url of urls) {
    const r = await req('POST', `${API}/${user}/media`,
      { image_url: url, is_carousel_item: 'true', access_token: token });
    children.push(r.id);
  }
  const carousel = await req('POST', `${API}/${user}/media`,
    { media_type: 'CAROUSEL', children: children.join(','),
      caption: text, access_token: token });

  // A container is not ready the moment it is created; publishing too early
  // fails with a status that reads like a permissions problem.
  for (let i = 0; i < POLL_TRIES; i++) {
    const s = await req('GET',
      `${API}/${carousel.id}?fields=status_code,status&access_token=${encodeURIComponent(token)}`);
    if (s.status_code === 'FINISHED') break;
    if (s.status_code === 'ERROR' || s.status_code === 'EXPIRED') {
      throw new Error(`container ${s.status_code}: ${s.status || ''}`);
    }
    await sleep(POLL_MS);
  }

  const out = await req('POST', `${API}/${user}/media_publish`,
    { creation_id: carousel.id, access_token: token });
  const perma = await req('GET',
    `${API}/${out.id}?fields=permalink&access_token=${encodeURIComponent(token)}`)
    .catch(() => ({}));
  console.log(JSON.stringify({ ok: true, topic, account, id: out.id,
                               permalink: perma.permalink || null }));
}

async function refresh() {
  const out = {};
  for (const [account, map] of Object.entries(ACCOUNTS)) {
    const token = process.env[map.token];
    if (!token) { out[account] = 'no token'; continue; }
    try {
      const r = await req('GET', `${API}/refresh_access_token`
        + `?grant_type=ig_refresh_token&access_token=${encodeURIComponent(token)}`);
      out[account] = { days: Math.round((r.expires_in || 0) / 86400),
                       env: `${map.token}=${r.access_token}`,
                       minted: `${map.minted}=${Math.floor(Date.now() / 1000)}` };
    } catch (e) { out[account] = e.message; }
  }
  console.log(JSON.stringify(out, null, 1));
  console.log('\nPut the printed env lines back in .env. Tokens last 60 days '
    + 'from the refresh, and a token must be 24h old before it can be refreshed.');
}

async function main() {
  if (has('refresh')) return refresh();
  const topic = process.argv.slice(2).find((a) => !a.startsWith('--')
    && process.argv[process.argv.indexOf(a) - 1] !== '--account');
  const account = arg('account');
  if (!topic || !account) {
    console.error('usage: node tools/instagram.js <topic> --account vn [--dry-run]');
    console.error('       node tools/instagram.js --refresh');
    process.exit(1);
  }
  await publish(topic, account);
}

main().catch((e) => { console.error(e.message); process.exit(1); });
