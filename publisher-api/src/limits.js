export const MAX_ACCOUNTS = 25;
export const MAX_QUEUED = 200;
export const MAX_IMAGES = 35;
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const MAX_WORKSPACE_BYTES = 200 * 1024 * 1024;
export const MIN_LEAD_SECONDS = 5 * 60;
export const KEEP_AFTER_DONE = 7 * 86400;
export const KEEP_UNATTACHED = 86400;
export const SESSION_TTL = 30 * 86400;
export const RETRY_DELAYS = [60, 300, 600]; // seconds before retries 1, 2, 3
export const PER_ACCOUNT_PER_TICK = 5;
export const PUBLISH_TIMEOUT = 3600;
export const PRIVACY = ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR', 'SELF_ONLY'];

// Instagram's content publishing API: carousels hold 10, captions 2,200
// characters with at most 30 hashtags, and images must be JPEG.
export const IG_MAX_IMAGES = 10;
export const IG_MAX_CAPTION = 2200;
export const IG_MAX_HASHTAGS = 30;

// Outbound calls (TikTok, Meta) one cron tick may make. Workers on the free
// plan allow 50 per invocation, and one post to ten accounts at the same
// minute would blow straight through that; whatever does not fit waits a minute.
export const TICK_FETCH_BUDGET = 45;
export const POLL_RESERVE = 10;

export const MAX_BRANDS = 25;
export const FB_MAX_CAPTION = 63206;
