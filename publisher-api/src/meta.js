// Facebook Pages through Facebook Login, Instagram through Instagram Login.
//
// The Page token /me/accounts hands back for a long-lived user token does not
// expire. Instagram Login needs no Facebook Page at all (any professional
// account connects directly), but its token lives 60 days and must be
// refreshed before then; see refreshInstagramTokens.

const GRAPH_FB = 'https://graph.facebook.com/v23.0';
const GRAPH_IG = 'https://graph.instagram.com/v23.0';

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

export function meta({ appId, appSecret, igAppId, igAppSecret, fetch }) {
  async function call(path, { method = 'GET', params = {}, label, base = GRAPH_FB }) {
    const url = new URL(base.startsWith('https://') && path.startsWith('https://') ? path : base + path);
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
    // api.instagram.com reports failures flat: { error_type, code, error_message }.
    const e = body.error || (body.error_message ? { message: body.error_message, code: body.code } : null);
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
      fields: 'id,name,access_token,picture{url}' } }),

    // Instagram Login: the short-lived token is swapped for a 60-day one at once.
    igExchangeCode: ({ code, redirectUri }) => call('https://api.instagram.com/oauth/access_token', {
      method: 'POST', label: 'instagram code exchange',
      params: { client_id: igAppId, client_secret: igAppSecret, grant_type: 'authorization_code',
        redirect_uri: redirectUri, code } })
      .then(b => (Array.isArray(b.data) ? b.data[0] : b)),
    igLongLived: token => call('https://graph.instagram.com/access_token', { label: 'instagram token exchange',
      params: { grant_type: 'ig_exchange_token', client_secret: igAppSecret, access_token: token } }),
    igRefresh: token => call('https://graph.instagram.com/refresh_access_token', { label: 'instagram token refresh',
      params: { grant_type: 'ig_refresh_token', access_token: token } }),
    igMe: token => call('/me', { base: GRAPH_IG, label: 'instagram profile',
      params: { fields: 'id,user_id,username,name,profile_picture_url,account_type', access_token: token } }),

    // Instagram publishing: one container per image, a carousel around them, then publish.
    igImage: (token, igId, imageUrl, { carouselItem = false, caption } = {}) => call(`/${igId}/media`, {
      base: GRAPH_IG, method: 'POST', label: 'instagram image',
      params: { image_url: imageUrl, access_token: token,
        ...(carouselItem ? { is_carousel_item: 'true' } : {}), ...(caption ? { caption } : {}) } }),
    igCarousel: (token, igId, children, caption) => call(`/${igId}/media`, {
      base: GRAPH_IG, method: 'POST', label: 'instagram carousel',
      params: { media_type: 'CAROUSEL', children: children.join(','), caption, access_token: token } }),
    igContainerStatus: (token, id) => call(`/${id}`, { base: GRAPH_IG, label: 'instagram status',
      params: { fields: 'status_code,status', access_token: token } }),
    igPublish: (token, igId, creationId) => call(`/${igId}/media_publish`, {
      base: GRAPH_IG, method: 'POST', label: 'instagram publish', params: { creation_id: creationId, access_token: token } }),
    igPermalink: (token, mediaId) => call(`/${mediaId}`, { base: GRAPH_IG, label: 'instagram permalink',
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
  appId: env.META_APP_ID, appSecret: env.META_APP_SECRET,
  igAppId: env.IG_APP_ID, igAppSecret: env.IG_APP_SECRET, fetch: (...a) => fetch(...a),
});

// Tests put a fake client on env.__meta; production builds a real one.
export const metaFor = env => env.__meta || makeMeta(env);
