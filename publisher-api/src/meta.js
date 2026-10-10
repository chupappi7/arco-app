// Facebook Pages and Instagram professional accounts, through one Facebook
// Login. The Page token that /me/accounts hands back for a long-lived user
// token does not expire, and it is also the token that publishes to the
// Instagram account linked to that Page — so there is nothing to refresh.

const GRAPH = 'https://graph.facebook.com/v23.0';
export const META_SCOPE = ['pages_show_list', 'pages_read_engagement', 'pages_manage_posts',
  'business_management', 'instagram_basic', 'instagram_content_publish'].join(',');

// Graph error codes that mean "try again", not "this will never work".
const TRANSIENT_CODES = new Set([1, 2, 4, 17, 32, 341, 613]);
const TIMEOUT_MS = 20_000;

export class MetaError extends Error {
  constructor(message, { code = 'unknown', httpStatus = 0, transient = false } = {}) {
    super(message);
    this.code = code;
    this.httpStatus = httpStatus;
    this.transient = transient;
  }
}

export function meta({ appId, appSecret, fetch }) {
  async function call(path, { method = 'GET', params = {}, label }) {
    const url = new URL(GRAPH + path);
    const init = { method, signal: AbortSignal.timeout(TIMEOUT_MS) };
    if (method === 'GET') for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
    else {
      init.headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
      init.body = new URLSearchParams(params).toString();
    }
    let res;
    try { res = await fetch(url.toString(), init); }
    catch (err) { throw new MetaError(`${label}: ${err.message || 'network error'}`, { code: 'network', transient: true }); }
    let body = {};
    try { body = JSON.parse(await res.text()); } catch {}
    const e = body.error;
    if (e || !res.ok) {
      // 190 is an expired, revoked or password-changed token: only a new
      // login fixes it.
      if (e?.code === 190) throw new MetaError('Reconnect this account', { code: 'needs_reconnect', httpStatus: res.status });
      const msg = e?.error_user_msg || e?.message || `HTTP ${res.status}`;
      throw new MetaError(`${label}: ${msg}`, { code: String(e?.code ?? `http_${res.status}`), httpStatus: res.status,
        transient: res.status >= 500 || res.status === 429 || TRANSIENT_CODES.has(e?.code) || !!e?.is_transient });
    }
    return body;
  }

  return {
    exchangeCode: ({ code, redirectUri }) => call('/oauth/access_token', { label: 'code exchange',
      params: { client_id: appId, client_secret: appSecret, redirect_uri: redirectUri, code } }),
    longLived: token => call('/oauth/access_token', { label: 'token exchange',
      params: { grant_type: 'fb_exchange_token', client_id: appId, client_secret: appSecret, fb_exchange_token: token } }),
    me: token => call('/me', { label: 'profile', params: { fields: 'id,name', access_token: token } }),
    pages: token => call('/me/accounts', { label: 'pages', params: { limit: '100', access_token: token,
      fields: 'id,name,access_token,picture{url},instagram_business_account{id,username,name,profile_picture_url}' } }),

    // Instagram: one container per image, a carousel around them, then publish.
    igImage: (token, igId, imageUrl, { carouselItem = false, caption } = {}) => call(`/${igId}/media`, {
      method: 'POST', label: 'instagram image',
      params: { image_url: imageUrl, access_token: token,
        ...(carouselItem ? { is_carousel_item: 'true' } : {}), ...(caption ? { caption } : {}) } }),
    igCarousel: (token, igId, children, caption) => call(`/${igId}/media`, {
      method: 'POST', label: 'instagram carousel',
      params: { media_type: 'CAROUSEL', children: children.join(','), caption, access_token: token } }),
    igContainerStatus: (token, id) => call(`/${id}`, { label: 'instagram status',
      params: { fields: 'status_code,status', access_token: token } }),
    igPublish: (token, igId, creationId) => call(`/${igId}/media_publish`, {
      method: 'POST', label: 'instagram publish', params: { creation_id: creationId, access_token: token } }),
    igPermalink: (token, mediaId) => call(`/${mediaId}`, { label: 'instagram permalink',
      params: { fields: 'permalink', access_token: token } }),

    // Facebook: unpublished photos, then one feed post that attaches them.
    fbPhoto: (token, pageId, url, { published, caption } = {}) => call(`/${pageId}/photos`, {
      method: 'POST', label: 'facebook photo',
      params: { url, published: published ? 'true' : 'false', access_token: token,
        ...(caption ? { caption } : {}) } }),
    fbFeed: (token, pageId, message, photoIds) => call(`/${pageId}/feed`, {
      method: 'POST', label: 'facebook post',
      params: { message, access_token: token,
        ...Object.fromEntries(photoIds.map((id, i) => [`attached_media[${i}]`, JSON.stringify({ media_fbid: id })])) } }),
  };
}

export const makeMeta = env => meta({
  appId: env.META_APP_ID, appSecret: env.META_APP_SECRET, fetch: (...a) => fetch(...a),
});

// Tests put a fake client on env.__meta; production builds a real one.
export const metaFor = env => env.__meta || makeMeta(env);
