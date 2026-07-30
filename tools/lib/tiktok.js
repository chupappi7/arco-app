'use strict';

/**
 * Shared TikTok Open API helpers.
 *
 * Docs:
 *   OAuth        https://developers.tiktok.com/doc/oauth-user-access-token-management/
 *   Photo post   https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
 *   Media pull   https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
 */

const OAUTH_TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/';
const AUTHORIZE_URL = 'https://www.tiktok.com/v2/auth/authorize/';
const CONTENT_INIT_URL = 'https://open.tiktokapis.com/v2/post/publish/content/init/';
const STATUS_FETCH_URL = 'https://open.tiktokapis.com/v2/post/publish/status/fetch/';

// TikTok's media-transfer guide tells clients to retry 5xx. The pipeline sees
// 503/504 in practice (gateway/pull-service blips); 500/502 are the same class.
const RETRYABLE_STATUS = new Set([500, 502, 503, 504]);
const MAX_ATTEMPTS = 5;
const BASE_BACKOFF_MS = 1000;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class TikTokError extends Error {
  constructor(message, { status, code, logId, retryable = false } = {}) {
    super(message);
    this.name = 'TikTokError';
    this.status = status;
    this.code = code;
    this.logId = logId;
    this.retryable = retryable;
  }
}

/**
 * fetch() with retry/backoff on transient failures.
 *
 * Retries on 500/502/503/504 and on network-level errors. Everything else
 * (including 4xx) fails fast — retrying a bad request never helps.
 */
async function fetchWithRetry(url, options, { label = 'request', maxAttempts = MAX_ATTEMPTS } = {}) {
  let lastErr;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    let res;
    try {
      res = await fetch(url, options);
    } catch (err) {
      // DNS failure, socket hang-up, TLS error, etc.
      lastErr = new TikTokError(`${label}: network error — ${err.message}`, { retryable: true });
      if (attempt === maxAttempts) break;
      const wait = BASE_BACKOFF_MS * 2 ** (attempt - 1);
      console.warn(`  ! ${label} network error (attempt ${attempt}/${maxAttempts}), retrying in ${wait}ms`);
      await sleep(wait);
      continue;
    }

    if (RETRYABLE_STATUS.has(res.status)) {
      lastErr = new TikTokError(`${label}: HTTP ${res.status}`, { status: res.status, retryable: true });
      if (attempt === maxAttempts) break;
      // Honour Retry-After when TikTok sends one, else exponential backoff.
      const retryAfter = Number(res.headers.get('retry-after'));
      const wait = Number.isFinite(retryAfter) && retryAfter > 0
        ? retryAfter * 1000
        : BASE_BACKOFF_MS * 2 ** (attempt - 1);
      console.warn(`  ! ${label} HTTP ${res.status} (attempt ${attempt}/${maxAttempts}), retrying in ${wait}ms`);
      await sleep(wait);
      continue;
    }

    return res;
  }

  throw lastErr;
}

/**
 * Parse a TikTok JSON envelope. TikTok returns HTTP 200 with a populated
 * `error` object for most business failures, so status alone is not enough.
 */
async function parseEnvelope(res, label) {
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    throw new TikTokError(`${label}: non-JSON response (HTTP ${res.status}) — ${text.slice(0, 300)}`, {
      status: res.status,
    });
  }

  const err = body.error;
  // The success sentinel is error.code === 'ok'.
  if (err && err.code && err.code !== 'ok') {
    throw new TikTokError(`${label}: ${err.code} — ${err.message || '(no message)'}`, {
      status: res.status,
      code: err.code,
      logId: err.log_id,
    });
  }

  if (!res.ok) {
    throw new TikTokError(`${label}: HTTP ${res.status} — ${text.slice(0, 300)}`, { status: res.status });
  }

  return body;
}

/**
 * Exchange a long-lived refresh token for a fresh access token.
 *
 * TikTok may rotate the refresh token — the caller must persist
 * `refresh_token` from the response if it differs from what was sent.
 */
async function refreshAccessToken({ clientKey, clientSecret, refreshToken }) {
  const res = await fetchWithRetry(
    OAUTH_TOKEN_URL,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_key: clientKey,
        client_secret: clientSecret,
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
      }),
    },
    { label: 'token refresh' }
  );

  const body = await parseEnvelope(res, 'token refresh');

  if (!body.access_token) {
    throw new TikTokError(`token refresh: response had no access_token — ${JSON.stringify(body).slice(0, 300)}`);
  }

  return {
    accessToken: body.access_token,
    refreshToken: body.refresh_token,
    expiresIn: body.expires_in,
    scope: body.scope,
    openId: body.open_id,
  };
}

/** Exchange a one-time authorization code for tokens. */
async function exchangeCode({ clientKey, clientSecret, code, redirectUri, codeVerifier }) {
  const params = {
    client_key: clientKey,
    client_secret: clientSecret,
    code,
    grant_type: 'authorization_code',
    redirect_uri: redirectUri,
  };
  if (codeVerifier) params.code_verifier = codeVerifier;

  const res = await fetchWithRetry(
    OAUTH_TOKEN_URL,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(params),
    },
    { label: 'code exchange' }
  );

  return parseEnvelope(res, 'code exchange');
}

/**
 * Initialize a PHOTO post.
 *
 * post_mode MEDIA_UPLOAD drops the post into the creator's TikTok inbox as a
 * draft (requires the `video.upload` scope). DIRECT_POST publishes immediately
 * and requires `video.publish` plus a privacy_level.
 */
async function initPhotoPost({ accessToken, photoUrls, title, description, coverIndex = 0, postMode = 'MEDIA_UPLOAD', privacyLevel }) {
  const postInfo = {};
  if (title) postInfo.title = title;
  if (description) postInfo.description = description;
  // privacy_level is mandatory for DIRECT_POST and rejected as noise otherwise.
  if (postMode === 'DIRECT_POST') {
    postInfo.privacy_level = privacyLevel || 'SELF_ONLY';
  }

  const payload = {
    media_type: 'PHOTO',
    post_mode: postMode,
    post_info: postInfo,
    source_info: {
      source: 'PULL_FROM_URL',
      photo_images: photoUrls,
      photo_cover_index: coverIndex,
    },
  };

  const res = await fetchWithRetry(
    CONTENT_INIT_URL,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify(payload),
    },
    { label: 'content init' }
  );

  const body = await parseEnvelope(res, 'content init');
  return body.data;
}

/** Poll the publish status for a publish_id. */
async function fetchPostStatus({ accessToken, publishId }) {
  const res = await fetchWithRetry(
    STATUS_FETCH_URL,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify({ publish_id: publishId }),
    },
    { label: 'status fetch' }
  );

  const body = await parseEnvelope(res, 'status fetch');
  return body.data;
}

module.exports = {
  AUTHORIZE_URL,
  TikTokError,
  RETRYABLE_STATUS,
  sleep,
  fetchWithRetry,
  parseEnvelope,
  refreshAccessToken,
  exchangeCode,
  initPhotoPost,
  fetchPostStatus,
};
