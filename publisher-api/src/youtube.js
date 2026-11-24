// YouTube through Google sign-in. The refresh token does not rotate and does
// not expire while the person keeps Publisher's access, so it is kept like
// TikTok's and exchanged for a one-hour access token when one is needed.
//
// Uploads are resumable: one call opens an upload session (nothing exists on
// YouTube yet, so it is safe to repeat), the second sends the bytes and
// creates the video.

const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const API = 'https://www.googleapis.com/youtube/v3';
const UPLOAD = 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status';
const TIMEOUT_MS = 20_000;

export class YouTubeError extends Error {
  constructor(message, { code = 'unknown', httpStatus = 0, transient = false } = {}) {
    super(message);
    this.code = code;
    this.httpStatus = httpStatus;
    this.transient = transient;
  }
}

// What Google's error reasons mean for the person.
const REASONS = {
  quotaExceeded: "YouTube's daily upload allowance for ARCO Publisher is used up. Try again tomorrow.",
  uploadLimitExceeded: 'This YouTube channel has reached its upload limit for now. Try again later.',
  youtubeSignupRequired: 'This Google account has no YouTube channel yet. Create one on YouTube, then connect again.',
  forbidden: 'YouTube refused the upload for this channel.',
};

async function fail(res, label) {
  let body = {};
  try { body = JSON.parse(await res.text()); } catch {}
  const err = body.error;
  const oauthCode = typeof err === 'string' ? err : null;
  const reason = typeof err === 'object' ? err?.errors?.[0]?.reason || err?.status : null;
  const msg = typeof err === 'object' ? err?.message : body.error_description;
  if (oauthCode === 'invalid_grant' || res.status === 401) {
    return new YouTubeError('Reconnect this account', { code: 'needs_reconnect', httpStatus: res.status });
  }
  return new YouTubeError(REASONS[reason] || `${label}: ${msg || oauthCode || `HTTP ${res.status}`}`,
    { code: reason || oauthCode || `http_${res.status}`, httpStatus: res.status, transient: res.status >= 500 || res.status === 429 });
}

export function youtube({ clientId, clientSecret, fetch }) {
  async function send(url, init, label) {
    try { return await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS), ...init }); }
    catch (err) { throw new YouTubeError(`${label}: ${err.message || 'network error'}`, { code: 'network', transient: true }); }
  }
  async function json(url, init, label) {
    const res = await send(url, init, label);
    if (!res.ok) throw await fail(res, label);
    return res.json();
  }
  const auth = token => ({ Authorization: `Bearer ${token}` });
  const form = params => ({ method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(params).toString() });

  return {
    exchangeCode: ({ code, redirectUri }) => json(TOKEN_URL, form({ code, client_id: clientId, client_secret: clientSecret,
      redirect_uri: redirectUri, grant_type: 'authorization_code' }), 'code exchange'),
    refresh: refreshToken => json(TOKEN_URL, form({ refresh_token: refreshToken, client_id: clientId, client_secret: clientSecret,
      grant_type: 'refresh_token' }), 'token refresh'),
    // The signed-in person's own channel: id, name, picture, subscribers.
    myChannel: async token => {
      const r = await json(`${API}/channels?part=snippet,statistics&mine=true`, { headers: auth(token) }, 'channel');
      const c = r.items?.[0];
      if (!c) throw new YouTubeError(REASONS.youtubeSignupRequired, { code: 'no_channel' });
      const thumbs = c.snippet?.thumbnails || {};
      return { id: c.id, title: c.snippet?.title || '', custom_url: String(c.snippet?.customUrl || '').replace(/^@/, ''),
        avatar_url: (thumbs.medium || thumbs.default || thumbs.high || {}).url || '',
        subscribers: c.statistics?.hiddenSubscriberCount ? null : Number(c.statistics?.subscriberCount ?? NaN) };
    },
    // Opens an upload session; returns its URL. Nothing is on YouTube yet.
    startUpload: async (token, { title, description, privacy, madeForKids = false, bytes, contentType }) => {
      const res = await send(UPLOAD, { method: 'POST', headers: { ...auth(token), 'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Length': String(bytes), 'X-Upload-Content-Type': contentType },
        body: JSON.stringify({ snippet: { title, description, categoryId: '22' },
          status: { privacyStatus: privacy, selfDeclaredMadeForKids: !!madeForKids } }) }, 'upload start');
      if (!res.ok) throw await fail(res, 'upload start');
      const location = res.headers.get('Location');
      if (!location) throw new YouTubeError('upload start: YouTube gave no upload address', { code: 'no_location', transient: true });
      return location;
    },
    // Sends the file; YouTube answers with the new video.
    putUpload: async (location, body, bytes, contentType) => {
      let res;
      try {
        res = await fetch(location, { method: 'PUT', headers: { 'Content-Type': contentType, 'Content-Length': String(bytes) }, body });
      } catch (err) { throw new YouTubeError(`upload: ${err.message || 'network error'}`, { code: 'network', transient: true }); }
      if (!res.ok) throw await fail(res, 'upload');
      return res.json();
    },
    // Someone else's channel, by id or @handle, with a plain API key: public numbers only.
    publicChannel: async (key, { id, handle }) => {
      const q = id ? `id=${encodeURIComponent(id)}` : `forHandle=${encodeURIComponent('@' + handle)}`;
      const r = await json(`${API}/channels?part=snippet,statistics,contentDetails&${q}&key=${encodeURIComponent(key)}`, {}, 'channel');
      const c = r.items?.[0];
      if (!c) return null;
      const thumbs = c.snippet?.thumbnails || {}, st = c.statistics || {};
      return { id: c.id, title: c.snippet?.title || '', handle: String(c.snippet?.customUrl || '').replace(/^@/, ''),
        avatar_url: (thumbs.medium || thumbs.default || thumbs.high || {}).url || '',
        subscribers: st.hiddenSubscriberCount ? null : Number(st.subscriberCount ?? NaN), views: Number(st.viewCount ?? NaN),
        videos: Number(st.videoCount ?? NaN), uploads: c.contentDetails?.relatedPlaylists?.uploads || null };
    },
    // A channel's newest uploads with their numbers, newest first.
    publicRecent: async (key, uploads, n = 12) => {
      const pl = await json(`${API}/playlistItems?part=contentDetails&maxResults=${n}&playlistId=${encodeURIComponent(uploads)}&key=${encodeURIComponent(key)}`, {}, 'uploads');
      const ids = (pl.items || []).map(i => i.contentDetails?.videoId).filter(Boolean);
      if (!ids.length) return [];
      const v = await json(`${API}/videos?part=snippet,statistics,contentDetails&id=${ids.join(',')}&key=${encodeURIComponent(key)}`, {}, 'videos');
      return (v.items || []).map(x => ({ id: x.id, title: x.snippet?.title || '', published_at: Math.floor(Date.parse(x.snippet?.publishedAt) / 1000) || null,
        thumb: (x.snippet?.thumbnails?.medium || x.snippet?.thumbnails?.default || {}).url || '',
        views: Number(x.statistics?.viewCount ?? NaN) || 0, likes: x.statistics?.likeCount == null ? null : Number(x.statistics.likeCount),
        comments: x.statistics?.commentCount == null ? null : Number(x.statistics.commentCount), duration: x.contentDetails?.duration || '' }))
        .sort((a, b) => (b.published_at || 0) - (a.published_at || 0));
    },
    // Views, likes and comments for up to 50 videos.
    videoStats: async (token, ids) => {
      const r = await json(`${API}/videos?part=statistics,status&id=${ids.slice(0, 50).map(encodeURIComponent).join(',')}`,
        { headers: auth(token) }, 'video stats');
      return r.items || [];
    },
  };
}

export const ytFor = env => env.__yt || youtube({
  clientId: env.GOOGLE_CLIENT_ID, clientSecret: env.GOOGLE_CLIENT_SECRET, fetch: (...a) => fetch(...a),
});
