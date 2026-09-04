#!/usr/bin/env node
'use strict';

/**
 * tiktok-auth.js — one-time helper to mint a TIKTOK_REFRESH_TOKEN.
 *
 * Run this once, stash the printed refresh token in your env, and never run it
 * again until the token expires (refresh tokens last 365 days).
 *
 * Usage:
 *   TIKTOK_CLIENT_KEY=... TIKTOK_CLIENT_SECRET=... \
 *   TIKTOK_REDIRECT_URI="https://..." node tools/tiktok-auth.js
 *
 * Options:
 *   --redirect URI   Redirect URI (overrides TIKTOK_REDIRECT_URI). Must match a
 *                    "Redirect URI" registered on your app at developers.tiktok.com
 *                    byte for byte.
 *   --scope "a,b"    Scopes to request (default: user.info.basic,video.upload,video.publish)
 *   --pkce           Send an S256 code_challenge. Required if your app is
 *                    registered as a desktop/mobile client; harmless to omit for web.
 *
 * Two capture modes, chosen automatically from the redirect URI:
 *   http://localhost:PORT/...  -> spins up a local server and captures the code
 *   anything else              -> prints the URL, you paste the redirected URL back
 *
 * Split (non-interactive) mode, for when stdin isn't a terminal:
 *   --print-url            Print the authorize URL and remember the state/PKCE
 *                          in tools/.auth-state.json, then exit.
 *   --redirected "<url>"   Finish the exchange using the URL you were redirected
 *                          to. Consumes tools/.auth-state.json.
 *
 * The refresh token is written straight into .env (TIKTOK_REFRESH_TOKEN=) rather
 * than printed, so it never lands in a scrollback buffer or a transcript. Pass
 * --print-token if you'd rather see it.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const readline = require('readline');
const { spawn } = require('child_process');
const { URL } = require('url');
const { AUTHORIZE_URL, exchangeCode } = require('./lib/tiktok');

// video.upload drafts to the creator's inbox; video.publish is what Direct
// Post needs, and creator_info/query refuses without it. Granting both keeps
// one token good for either mode.
// video.upload drafts to the inbox, video.publish is Direct Post,
// video.list reads the account's own posts back (views, likes, and
// therefore whether a draft was ever actually published).
const DEFAULT_SCOPE = 'user.info.basic,user.info.stats,video.upload,video.publish,video.list';
const STATE_FILE = path.join(__dirname, '.auth-state.json');
const ENV_FILE = path.join(__dirname, '..', '.env');

function parseArgs(argv) {
  const opts = {
    redirectUri: process.env.TIKTOK_REDIRECT_URI || null,
    scope: process.env.TIKTOK_SCOPE || DEFAULT_SCOPE,
    pkce: false,
    printUrl: false,
    redirected: null,
    printToken: false,
  };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case '--redirect': opts.redirectUri = argv[++i]; break;
      case '--scope': opts.scope = argv[++i]; break;
      case '--pkce': opts.pkce = true; break;
      case '--print-url': opts.printUrl = true; break;
      case '--redirected': opts.redirected = argv[++i]; break;
      case '--print-token': opts.printToken = true; break;
      case '-h':
      case '--help': opts.help = true; break;
      default: throw new Error(`unknown option: ${argv[i]}`);
    }
  }
  return opts;
}

function requireEnv(name) {
  const v = process.env[name];
  if (!v || !v.trim()) throw new Error(`missing required env var ${name}`);
  return v.trim();
}

function base64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function makePkce() {
  const verifier = base64url(crypto.randomBytes(48));
  const challenge = base64url(crypto.createHash('sha256').update(verifier).digest());
  return { verifier, challenge };
}

function buildAuthorizeUrl({ clientKey, redirectUri, scope, state, pkce }) {
  const u = new URL(AUTHORIZE_URL);
  u.searchParams.set('client_key', clientKey);
  u.searchParams.set('scope', scope);
  u.searchParams.set('response_type', 'code');
  u.searchParams.set('redirect_uri', redirectUri);
  u.searchParams.set('state', state);
  if (pkce) {
    u.searchParams.set('code_challenge', pkce.challenge);
    u.searchParams.set('code_challenge_method', 'S256');
  }
  return u.toString();
}

function openBrowser(url) {
  const cmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start' : 'xdg-open';
  try {
    spawn(cmd, [url], { detached: true, stdio: 'ignore' }).unref();
  } catch {
    /* the URL is printed anyway */
  }
}

/** Capture ?code= by running a throwaway server on the redirect URI's port. */
function captureViaLocalServer(redirect, expectedState) {
  return new Promise((resolve, reject) => {
    const port = Number(redirect.port) || 80;
    const server = http.createServer((req, res) => {
      const incoming = new URL(req.url, `http://${req.headers.host}`);
      if (incoming.pathname !== redirect.pathname) {
        res.writeHead(404).end('not found');
        return;
      }

      const code = incoming.searchParams.get('code');
      const state = incoming.searchParams.get('state');
      const error = incoming.searchParams.get('error');

      const finish = (msg) => {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`<!doctype html><meta charset="utf-8"><body style="font:16px system-ui;padding:3rem">${msg}</body>`);
        server.close();
      };

      if (error) {
        finish(`<h2>Authorization failed</h2><p>${incoming.searchParams.get('error_description') || error}</p>`);
        reject(new Error(`authorization denied: ${error}`));
      } else if (!code) {
        finish('<h2>No code in callback</h2>');
        reject(new Error('callback had no ?code= parameter'));
      } else if (state !== expectedState) {
        finish('<h2>State mismatch</h2><p>Possible CSRF. Start over.</p>');
        reject(new Error('state mismatch — aborting'));
      } else {
        finish('<h2>Authorized.</h2><p>You can close this tab and return to the terminal.</p>');
        resolve(code);
      }
    });

    server.on('error', reject);
    server.listen(port, () => console.log(`  listening on ${redirect.origin}${redirect.pathname} for the callback...`));
    setTimeout(() => {
      server.close();
      reject(new Error('timed out after 5 minutes waiting for the callback'));
    }, 5 * 60 * 1000).unref();
  });
}

/** Fallback for https redirect URIs we can't listen on: paste the URL back. */
function captureViaPaste(expectedState) {
  return new Promise((resolve, reject) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question('\n  Paste the FULL URL you were redirected to:\n  > ', (answer) => {
      rl.close();
      let parsed;
      try {
        parsed = new URL(answer.trim());
      } catch {
        return reject(new Error('that is not a valid URL'));
      }
      const code = parsed.searchParams.get('code');
      const state = parsed.searchParams.get('state');
      const error = parsed.searchParams.get('error');

      if (error) return reject(new Error(`authorization denied: ${error}`));
      if (!code) return reject(new Error('no ?code= parameter in that URL'));
      if (state !== expectedState) return reject(new Error('state mismatch — aborting'));
      resolve(code);
    });
  });
}

/** Pull ?code= out of a redirected URL, checking state against what we stored. */
function codeFromRedirectUrl(raw, expectedState) {
  let parsed;
  try {
    parsed = new URL(raw.trim());
  } catch {
    throw new Error('that is not a valid URL');
  }
  const error = parsed.searchParams.get('error');
  if (error) {
    throw new Error(`authorization denied: ${parsed.searchParams.get('error_description') || error}`);
  }
  const code = parsed.searchParams.get('code');
  if (!code) throw new Error('no ?code= parameter in that URL');
  const state = parsed.searchParams.get('state');
  if (expectedState && state !== expectedState) throw new Error('state mismatch — start over');
  return code;
}

/**
 * Set TIKTOK_REFRESH_TOKEN= in .env, replacing any existing line.
 *
 * Writing rather than printing keeps a 365-day credential out of terminal
 * scrollback. The file is already gitignored and chmod 600.
 */
function writeRefreshTokenToEnv(token) {
  let text = '';
  try {
    text = fs.readFileSync(ENV_FILE, 'utf8');
  } catch {
    /* no .env yet — we'll create one */
  }
  const line = `TIKTOK_REFRESH_TOKEN=${token}`;
  const existing = /^TIKTOK_REFRESH_TOKEN=.*$/m;
  text = existing.test(text)
    ? text.replace(existing, line)
    : `${text.replace(/\n*$/, '')}\n${line}\n`;
  fs.writeFileSync(ENV_FILE, text, { mode: 0o600 });
  return ENV_FILE;
}

/** Shared success reporting for both the interactive and split flows. */
function reportTokens(tokens, opts) {
  const granted = (tokens.scope || '').split(/[,\s]+/).filter(Boolean);
  console.log('\n  Success.');
  console.log(`  open_id: ${tokens.open_id}`);
  console.log(`  scopes:  ${granted.join(', ') || '(none reported)'}`);
  console.log(
    `  refresh token expires in ${tokens.refresh_expires_in}s (~${Math.round(tokens.refresh_expires_in / 86400)} days)`
  );

  if (!granted.includes('video.upload')) {
    console.warn('\n  ! video.upload was not granted — autopost.js cannot create inbox drafts without it.');
  }

  if (opts.printToken) {
    console.log(`\n    export TIKTOK_REFRESH_TOKEN='${tokens.refresh_token}'\n`);
  } else {
    const written = writeRefreshTokenToEnv(tokens.refresh_token);
    console.log(`\n  Refresh token written to ${written} (not printed).`);
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  // Step 2 of the split flow: finish an exchange started by --print-url.
  if (opts.redirected) {
    let saved;
    try {
      saved = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    } catch {
      throw new Error(`no pending authorization — run with --print-url first (missing ${STATE_FILE})`);
    }
    const code = codeFromRedirectUrl(opts.redirected, saved.state);
    console.log('\n  got authorization code, exchanging for tokens...');
    const tokens = await exchangeCode({
      clientKey: requireEnv('TIKTOK_CLIENT_KEY'),
      clientSecret: requireEnv('TIKTOK_CLIENT_SECRET'),
      code,
      redirectUri: saved.redirectUri,
      codeVerifier: saved.codeVerifier || undefined,
    });
    fs.unlinkSync(STATE_FILE);   // single-use
    reportTokens(tokens, opts);
    return;
  }

  if (opts.help) {
    console.log(require('fs').readFileSync(__filename, 'utf8').split('*/')[0].replace(/^[\s\S]*?\/\*\*/, ''));
    return;
  }

  const clientKey = requireEnv('TIKTOK_CLIENT_KEY');
  const clientSecret = requireEnv('TIKTOK_CLIENT_SECRET');

  if (!opts.redirectUri) {
    throw new Error(
      'no redirect URI. Pass --redirect "<uri>" or set TIKTOK_REDIRECT_URI.\n' +
        '  It must exactly match a Redirect URI registered on your app at\n' +
        '  developers.tiktok.com -> your app -> Login Kit -> Redirect URI.'
    );
  }

  const redirect = new URL(opts.redirectUri);
  const isLocal = redirect.protocol === 'http:' && /^(localhost|127\.0\.0\.1)$/.test(redirect.hostname);
  const state = base64url(crypto.randomBytes(16));
  const pkce = opts.pkce ? makePkce() : null;

  const authUrl = buildAuthorizeUrl({
    clientKey,
    redirectUri: opts.redirectUri,
    scope: opts.scope,
    state,
    pkce,
  });

  console.log('\nTikTok OAuth — one-time refresh token setup');
  console.log(`  redirect: ${opts.redirectUri}`);
  console.log(`  scope:    ${opts.scope}`);
  console.log(`  capture:  ${isLocal ? 'local server' : 'manual paste'}${pkce ? ' + PKCE' : ''}`);
  console.log(`\n  Open this URL and approve:\n\n  ${authUrl}\n`);

  // Step 1 of the split flow: remember what we'll need to verify and exchange,
  // then get out of the way. Used when stdin isn't a terminal.
  if (opts.printUrl) {
    fs.writeFileSync(
      STATE_FILE,
      JSON.stringify({ state, redirectUri: opts.redirectUri, codeVerifier: pkce?.verifier || null }, null, 2),
      { mode: 0o600 }
    );
    console.log('  After approving, re-run with:');
    console.log('    node tools/tiktok-auth.js --redirected "<the URL you landed on>"\n');
    return;
  }

  openBrowser(authUrl);

  const code = isLocal ? await captureViaLocalServer(redirect, state) : await captureViaPaste(state);

  console.log('\n  got authorization code, exchanging for tokens...');
  const tokens = await exchangeCode({
    clientKey,
    clientSecret,
    code,
    redirectUri: opts.redirectUri,
    codeVerifier: pkce?.verifier,
  });

  reportTokens(tokens, opts);
}

main().catch((err) => {
  console.error(`\nERROR  ${err.message}`);
  process.exit(1);
});
