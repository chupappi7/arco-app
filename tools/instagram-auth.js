#!/usr/bin/env node
'use strict';

/**
 * instagram-auth.js — one-time helper to mint a long-lived Instagram token.
 *
 * Run once per account. The token it prints lasts 60 days and is refreshed
 * in place after that by tools/instagram.js --refresh, so this is the only
 * step that needs a browser.
 *
 * Usage:
 *   node tools/instagram-auth.js --account vn
 *   node tools/instagram-auth.js --account vn --redirected "<the URL you landed on>"
 *
 * Needs IG_APP_ID and IG_APP_SECRET in .env, and the redirect URI below
 * registered on the app at developers.facebook.com byte for byte.
 *
 * Unlike TikTok's year-long refresh token, Instagram's expires in 60 days and
 * there is no auto-renew. Miss the window and every account goes silent, so
 * the dashboard warns from day 50.
 */
const fs = require('fs');
const path = require('path');
const https = require('https');

const REPO = path.resolve(__dirname, '..');
const STATE = path.join(__dirname, '.ig-auth-state.json');
const REDIRECT = process.env.IG_REDIRECT_URI
  || 'https://chupappi7.github.io/arco-app/';
// Everything content publishing needs and nothing else. instagram_business_basic
// reads the account id; _content_publish creates and publishes containers.
const SCOPES = 'instagram_business_basic,instagram_business_content_publish';

function arg(name, fallback) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

function post(host, pathname, form) {
  const body = new URLSearchParams(form).toString();
  return new Promise((resolve, reject) => {
    const req = https.request({
      host, path: pathname, method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded',
                 'Content-Length': Buffer.byteLength(body) },
    }, (res) => {
      let out = '';
      res.on('data', (d) => { out += d; });
      res.on('end', () => {
        try { resolve(JSON.parse(out)); }
        catch (e) { reject(new Error(`${res.statusCode}: ${out.slice(0, 300)}`)); }
      });
    });
    req.on('error', reject);
    req.end(body);
  });
}

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let out = '';
      res.on('data', (d) => { out += d; });
      res.on('end', () => {
        try { resolve(JSON.parse(out)); }
        catch (e) { reject(new Error(`${res.statusCode}: ${out.slice(0, 300)}`)); }
      });
    }).on('error', reject);
  });
}

async function main() {
  const appId = process.env.IG_APP_ID;
  const secret = process.env.IG_APP_SECRET;
  const account = arg('account');
  if (!appId || !secret) {
    console.error('Set IG_APP_ID and IG_APP_SECRET in .env first.');
    process.exit(1);
  }
  if (!account) {
    console.error('Which account? --account vn|getarco|us');
    process.exit(1);
  }

  const redirected = arg('redirected');
  if (!redirected) {
    const state = Math.random().toString(36).slice(2);
    fs.writeFileSync(STATE, JSON.stringify({ state, account }), { mode: 0o600 });
    const url = 'https://www.instagram.com/oauth/authorize'
      + `?client_id=${encodeURIComponent(appId)}`
      + `&redirect_uri=${encodeURIComponent(REDIRECT)}`
      + `&scope=${encodeURIComponent(SCOPES)}`
      + `&response_type=code&state=${state}`;
    console.log(`\n1. Log into Instagram as the ${account} account (use a private window`);
    console.log('   so you do not have to log the others out).');
    console.log('\n2. Open this and approve:\n');
    console.log(url);
    console.log('\n3. You land on the arco-app page with ?code=... in the address bar.');
    console.log('   Copy the WHOLE url and run:\n');
    console.log(`   node tools/instagram-auth.js --account ${account} --redirected "<paste>"\n`);
    return;
  }

  let saved = {};
  try { saved = JSON.parse(fs.readFileSync(STATE, 'utf8')); } catch (e) {}
  const u = new URL(redirected);
  const code = u.searchParams.get('code');
  if (!code) {
    console.error('No ?code= in that url. If it says error_reason=user_denied, approve it.');
    process.exit(1);
  }
  if (saved.state && u.searchParams.get('state') && u.searchParams.get('state') !== saved.state) {
    console.error('state does not match the one this script issued — start again.');
    process.exit(1);
  }

  // Instagram hands back a code with a #_ suffix when it round-trips through
  // a browser. Left on, the exchange fails with a useless "invalid code".
  const clean = code.replace(/#_$/, '');
  const short = await post('api.instagram.com', '/oauth/access_token', {
    client_id: appId, client_secret: secret,
    grant_type: 'authorization_code', redirect_uri: REDIRECT, code: clean,
  });
  if (!short.access_token) {
    console.error('Exchange failed:', JSON.stringify(short).slice(0, 400));
    process.exit(1);
  }

  const long = await get('https://graph.instagram.com/access_token'
    + '?grant_type=ig_exchange_token'
    + `&client_secret=${encodeURIComponent(secret)}`
    + `&access_token=${encodeURIComponent(short.access_token)}`);
  if (!long.access_token) {
    console.error('Long-lived exchange failed:', JSON.stringify(long).slice(0, 400));
    process.exit(1);
  }

  const me = await get('https://graph.instagram.com/v21.0/me'
    + `?fields=id,username&access_token=${encodeURIComponent(long.access_token)}`);

  try { fs.unlinkSync(STATE); } catch (e) {}
  const suffix = account === 'vn' ? '' : '_' + account.toUpperCase();
  const days = Math.round((long.expires_in || 0) / 86400);
  console.log(`\nAuthorised @${me.username || '?'} (id ${me.id || '?'}), good for ${days} days.`);
  console.log('\nPut these two lines in .env:\n');
  console.log(`IG_TOKEN${suffix}=${long.access_token}`);
  console.log(`IG_USER_ID${suffix}=${me.id}`);
  console.log(`IG_TOKEN_MINTED${suffix}=${Math.floor(Date.now() / 1000)}`);
  console.log('\nchmod 600 .env afterwards. Never paste these into a chat.\n');
}

main().catch((e) => { console.error(e.message); process.exit(1); });
