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

const TIMEOUT_MS = 20_000;

export function tiktok({ clientKey, clientSecret, fetch }) {
  // A dropped connection or a hung request is a blip, not a verdict: retry it.
  // The timeout also keeps one cron tick from outliving the stuck-post window.
  async function send(url, init, label) {
    try {
      return await fetch(url, { ...init, signal: AbortSignal.timeout(TIMEOUT_MS) });
    } catch (err) {
      throw new TikTokError(`${label}: ${err.message || 'network error'}`, { code: 'network', transient: true });
    }
  }

  async function oauth(params, label) {
    const res = await send(OAUTH_TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ client_key: clientKey, client_secret: clientSecret, ...params }).toString(),
    }, label);
    const body = await readBody(res);
    if (body.error === 'invalid_grant') {
      throw new TikTokError('Reconnect this account', { code: 'needs_reconnect', httpStatus: res.status });
    }
    if (!res.ok || body.error || !body.access_token) throw httpFailure(res, body, label);
    return body;
  }

  async function v2(url, accessToken, payload, label) {
    const res = await send(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json; charset=UTF-8' },
      body: payload === undefined ? undefined : JSON.stringify(payload),
    }, label);
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

// Tests put a fake client on env.__tk; production builds a real one.
export const tkFor = env => env.__tk || makeTikTok(env);
