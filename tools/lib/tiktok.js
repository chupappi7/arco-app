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
const CREATOR_INFO_URL = 'https://open.tiktokapis.com/v2/post/publish/creator_info/query/';
const VIDEO_LIST_URL = 'https://open.tiktokapis.com/v2/video/list/';
const USER_INFO_URL = 'https://open.tiktokapis.com/v2/user/info/';

// Account-level numbers, for the analytics view. follower_count needs the
// user.info.stats scope; the profile fields need user.info.profile.
const USER_FIELDS = ['open_id', 'display_name', 'avatar_url',
                     'follower_count', 'following_count', 'likes_count',
                     'video_count'];

// Display API fields worth having: enough to match a post to a topic and to
// judge whether it performed.
const VIDEO_FIELDS = ['id', 'title', 'video_description', 'create_time',
                      'share_url', 'cover_image_url', 'view_count',
                      'like_count', 'comment_count', 'share_count'];

// TikTok's photo post_info contract. title is capped at 90 UTF-16 runes for
// photo posts (video allows more), description at 4000.
const PHOTO_TITLE_MAX = 90;
const PHOTO_DESC_MAX = 4000;
const PRIVACY_LEVELS = ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS',
                        'FOLLOWER_OF_CREATOR', 'SELF_ONLY'];

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
 * Query the creator's own settings before showing any posting UI.
 *
 * TikTok's content-sharing guidelines require this: the privacy options you
 * offer must be the ones this creator actually has, and comment/duet/stitch
 * controls must be greyed out where the creator has disabled them. Calling it
 * is a condition of passing the Content Posting API audit, not an optimisation.
 */
async function fetchCreatorInfo({ accessToken }) {
  const res = await fetchWithRetry(
    CREATOR_INFO_URL,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
    },
    { label: 'creator info' }
  );
  const body = await parseEnvelope(res, 'creator info');
  return body.data;
}

/** Account-level stats: followers, total likes, how many posts exist. */
async function fetchUserInfo({ accessToken, fields = USER_FIELDS }) {
  const url = `${USER_INFO_URL}?fields=${encodeURIComponent(fields.join(','))}`;
  const res = await fetchWithRetry(
    url,
    { method: 'GET', headers: { Authorization: `Bearer ${accessToken}` } },
    { label: 'user info' }
  );
  const env = await parseEnvelope(res, 'user info');
  return (env.data || {}).user || env.data;
}

/**
 * List the authorized user's own recent posts, newest first.
 *
 * Needs the `video.list` scope. The endpoint is named for video; whether it
 * also returns photo carousels is undocumented, which is the whole reason
 * this exists — call it and look.
 */
async function fetchVideoList({ accessToken, cursor, max = 20, fields = VIDEO_FIELDS }) {
  const url = `${VIDEO_LIST_URL}?fields=${encodeURIComponent(fields.join(','))}`;
  const body = { max_count: Math.min(max, 20) };
  if (cursor) body.cursor = cursor;
  const res = await fetchWithRetry(
    url,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify(body),
    },
    { label: 'video list' }
  );
  const env = await parseEnvelope(res, 'video list');
  return env.data;
}

/**
 * Initialize a PHOTO post.
 *
 * post_mode MEDIA_UPLOAD drops the post into the creator's TikTok inbox as a
 * draft (requires the `video.upload` scope). DIRECT_POST publishes immediately,
 * requires `video.publish`, and must carry the full disclosure set below —
 * TikTok rejects a direct post that omits the brand toggles.
 */
async function initPhotoPost({
  accessToken,
  photoUrls,
  title,
  description,
  coverIndex = 0,
  postMode = 'MEDIA_UPLOAD',
  privacyLevel,
  disableComment = false,
  autoAddMusic = false,
  brandOrganic = false,
  brandedContent = false,
}) {
  const postInfo = {};
  if (title) {
    if ([...title].length > PHOTO_TITLE_MAX) {
      throw new TikTokError(
        `title is ${[...title].length} characters; TikTok caps photo titles at ${PHOTO_TITLE_MAX}`
      );
    }
    postInfo.title = title;
  }
  if (description) {
    if ([...description].length > PHOTO_DESC_MAX) {
      throw new TikTokError(
        `description is ${[...description].length} characters; the cap is ${PHOTO_DESC_MAX}`
      );
    }
    postInfo.description = description;
  }
  // These fields are mandatory for DIRECT_POST and rejected as noise otherwise.
  if (postMode === 'DIRECT_POST') {
    const level = privacyLevel || 'SELF_ONLY';
    if (!PRIVACY_LEVELS.includes(level)) {
      throw new TikTokError(`privacy_level must be one of ${PRIVACY_LEVELS.join(', ')}, got ${level}`);
    }
    // TikTok's rule, and a hard audit item: branded content cannot be private.
    if (brandedContent && level === 'SELF_ONLY') {
      throw new TikTokError('branded content cannot be posted with privacy SELF_ONLY');
    }
    postInfo.privacy_level = level;
    postInfo.disable_comment = !!disableComment;
    postInfo.auto_add_music = !!autoAddMusic;
    postInfo.brand_organic_toggle = !!brandOrganic;
    postInfo.brand_content_toggle = !!brandedContent;
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
  fetchCreatorInfo,
  fetchVideoList,
  fetchUserInfo,
  fetchPostStatus,
  VIDEO_FIELDS,
  PRIVACY_LEVELS,
  PHOTO_TITLE_MAX,
  PHOTO_DESC_MAX,
};
