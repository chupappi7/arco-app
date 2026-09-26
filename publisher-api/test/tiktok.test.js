import { describe, it, expect } from 'vitest';
import { tiktok, buildPhotoBody, TikTokError } from '../src/tiktok.js';

function fakeFetch(responses) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url: String(url), init });
    const r = responses.shift();
    return new Response(JSON.stringify(r.body), { status: r.status ?? 200 });
  };
  fn.calls = calls;
  return fn;
}

describe('tiktok client', () => {
  it('exchangeCode posts form fields and returns tokens', async () => {
    const f = fakeFetch([{ body: { access_token: 'at', refresh_token: 'rt', open_id: 'o1',
      scope: 'user.info.basic,video.publish', expires_in: 86400, refresh_expires_in: 31536000 } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const t = await tk.exchangeCode({ code: 'c', codeVerifier: 'v', redirectUri: 'https://x/cb' });
    expect(t.open_id).toBe('o1');
    const body = new URLSearchParams(f.calls[0].init.body);
    expect(body.get('grant_type')).toBe('authorization_code');
    expect(body.get('code_verifier')).toBe('v');
    expect(body.get('client_key')).toBe('ck');
  });

  it('refresh maps invalid_grant to a non-transient needs_reconnect error', async () => {
    const f = fakeFetch([{ status: 400, body: { error: 'invalid_grant', error_description: 'Refresh token is invalid or expired.' } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const err = await tk.refresh('rt').catch(e => e);
    expect(err).toBeInstanceOf(TikTokError);
    expect(err.code).toBe('needs_reconnect');
    expect(err.transient).toBe(false);
  });

  it('v2 envelope errors carry the code and mark internal_error transient', async () => {
    const f = fakeFetch([{ body: { data: {}, error: { code: 'internal_error', message: 'boom', log_id: 'L' } } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const err = await tk.creatorInfo('at').catch(e => e);
    expect(err.code).toBe('internal_error');
    expect(err.transient).toBe(true);
  });

  it('HTTP 5xx and 429 are transient', async () => {
    const f = fakeFetch([{ status: 503, body: {} }, { status: 429, body: {} }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    expect((await tk.creatorInfo('at').catch(e => e)).transient).toBe(true);
    expect((await tk.status('at', 'p1').catch(e => e)).transient).toBe(true);
  });

  it('initPhoto sends the bearer token and returns publish_id', async () => {
    const f = fakeFetch([{ body: { data: { publish_id: 'p_123' }, error: { code: 'ok' } } }]);
    const tk = tiktok({ clientKey: 'ck', clientSecret: 'cs', fetch: f });
    const r = await tk.initPhoto('at', { any: 1 });
    expect(r.publish_id).toBe('p_123');
    expect(f.calls[0].init.headers.Authorization).toBe('Bearer at');
  });

  it('buildPhotoBody produces a DIRECT_POST PHOTO PULL_FROM_URL body', () => {
    const b = buildPhotoBody({
      title: 't', caption: 'c', imageUrls: ['https://a/1.jpg', 'https://a/2.jpg'], coverIndex: 1,
      settings: { privacy_level: 'PUBLIC_TO_EVERYONE', disable_comment: true, auto_add_music: false,
                  brand_organic: true, branded_content: false },
    });
    expect(b).toEqual({
      media_type: 'PHOTO', post_mode: 'DIRECT_POST',
      post_info: { title: 't', description: 'c', privacy_level: 'PUBLIC_TO_EVERYONE',
        disable_comment: true, auto_add_music: false,
        brand_organic_toggle: true, brand_content_toggle: false },
      source_info: { source: 'PULL_FROM_URL', photo_images: ['https://a/1.jpg', 'https://a/2.jpg'],
        photo_cover_index: 1 },
    });
  });
});
