// Publish a photo post. The page collects the choices; this re-checks them
// before spending them, because a browser is not a place to enforce a rule.

import { CONTENT_INIT_URL, accessTokenFrom, envelope, fail } from './_lib.js';

const PRIVACY = [
  'PUBLIC_TO_EVERYONE',
  'MUTUAL_FOLLOW_FRIENDS',
  'FOLLOWER_OF_CREATOR',
  'SELF_ONLY',
];

export default async function handler(req, res) {
  if (req.method !== 'POST') return fail(res, 405, 'POST only');
  const token = await accessTokenFrom(req);
  if (!token) return fail(res, 401, 'not connected', 'no_session');

  const {
    title = '',
    description = '',
    privacy_level: privacy,
    photo_images: images,
    photo_cover_index: cover = 0,
    disable_comment = false,
    auto_add_music = false,
    brand_organic_toggle = false,
    brand_content_toggle = false,
  } = req.body || {};

  if (!PRIVACY.includes(privacy)) return fail(res, 400, 'pick a privacy level');
  // TikTok's rule, and the reason the page removes "Only me" once branded
  // content is declared. Restated here so the API cannot be talked past.
  if (brand_content_toggle && privacy === 'SELF_ONLY')
    return fail(res, 400, 'branded content cannot be posted privately');
  if (!Array.isArray(images) || !images.length)
    return fail(res, 400, 'no images');
  if (images.length > 35) return fail(res, 400, 'at most 35 images');
  if (!images.every(u => typeof u === 'string' && u.startsWith('https://')))
    return fail(res, 400, 'every image must be an https URL');
  if (!Number.isInteger(cover) || cover < 0 || cover >= images.length)
    return fail(res, 400, 'cover index is outside the images');
  if ([...title].length > 90) return fail(res, 400, 'title is over 90 characters');
  if ([...description].length > 4000)
    return fail(res, 400, 'description is over 4000 characters');

  try {
    const r = await fetch(CONTENT_INIT_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify({
        media_type: 'PHOTO',
        post_mode: 'DIRECT_POST',
        post_info: {
          title,
          description,
          privacy_level: privacy,
          disable_comment: !!disable_comment,
          auto_add_music: !!auto_add_music,
          brand_organic_toggle: !!brand_organic_toggle,
          brand_content_toggle: !!brand_content_toggle,
        },
        source_info: {
          source: 'PULL_FROM_URL',
          photo_images: images,
          photo_cover_index: cover,
        },
      }),
    });
    const body = await envelope(r, 'content init');
    res.status(200).json({ publish_id: body.data?.publish_id });
  } catch (err) {
    fail(res, 502, err.message, err.code);
  }
}
