// Warm-up: how far a new account is from getting shown to people, from the
// views its posts already have. Nothing here calls a platform.
//
// new      under 3 days connected, or under 3 posts out
// ready    the last 5 posts' median is at least 200 views
// stuck    10+ days in and the last 5 posts all under 50 views
// warming  everything in between

const DAY = 86400;
export const SETTLED = 6 * 3600;   // views read earlier than this are not final
export const NEW_DAYS = 3, NEW_POSTS = 3;
export const READY = 200, STUCK = 50, STUCK_DAYS = 10;
const KEEP = 10, WINDOW = 5;

const median = v => { const s = [...v].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : null; };

const NEXT = {
  new: 'Post once a day this first week. Scroll your niche for a few minutes before and after each post.',
  warming: { up: 'Views are climbing. Keep posting daily.', down: 'Views dipped. Keep posting daily and try a stronger first second.',
    flat: 'Keep posting daily. Views usually pick up after a week or two.' },
  ready: 'Warmed up. Post your best formats and test new hooks.',
  stuck: 'Last 5 posts are under 50 views. Check the account region and post fresh clips, not reposts.',
  noviews: 'This platform hasn\'t shared views for this account yet.',
};

// account: { connected_at, published (all-time count), posts: [{ scheduled_at, views, stats_at }] }
export function warmup({ connected_at, published = 0, posts = [] }, t) {
  const days = Math.max(0, Math.floor((t - connected_at) / DAY));
  const measured = posts.filter(p => p.views != null && (p.stats_at || 0) - p.scheduled_at >= SETTLED)
    .sort((a, b) => a.scheduled_at - b.scheduled_at).slice(-KEEP);
  const views = measured.map(p => p.views), last = views.slice(-WINDOW), med = median(last);
  let trend = null;
  if (views.length >= 6) {
    const now3 = median(views.slice(-3)), before = median(views.slice(-6, -3));
    trend = now3 > before * 1.25 + 5 ? 'up' : now3 < before * 0.8 - 5 ? 'down' : 'flat';
  }
  const stage = days < NEW_DAYS || published < NEW_POSTS ? 'new'
    : last.length >= 3 && med >= READY ? 'ready'
    : days >= STUCK_DAYS && last.length >= WINDOW && Math.max(...last) < STUCK ? 'stuck' : 'warming';
  const next = stage === 'warming' ? (!views.length ? NEXT.noviews : NEXT.warming[trend || 'flat']) : NEXT[stage];
  return { stage, days, posts: published, views, median: med, trend, next };
}
