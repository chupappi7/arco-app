// Local stand-in for the Worker API, with sample data around "now", for
// working on the page without the real backend:
//   node publisher/dev/mock.cjs   →   http://localhost:4777/app.html
// Cookies: out=1 shows the sign-in page, empty=1 a workspace with nothing in it.
// New posts publish after ~5 s; Instagram ones fail, to show the failure path.
const http = require('http'), fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..', 'public'), PORT = 4777;
const now = () => Math.floor(Date.now() / 1000), H = h => now() + Math.round(h * 3600);
const me = {
  user: { id: 'u1', email: 'thinh@arco.app' }, needs_email: false,
  workspace: { id: 'ws1', name: 'ARCO Agency', timezone: null, slots: { days: [1, 2, 3, 4, 5], times: ['12:30', '18:00'] }, role: 'owner', brand_scope: null },
  workspaces: [{ id: 'ws1', name: 'ARCO Agency', role: 'owner' }, { id: 'ws2', name: 'Side project', role: 'owner' }],
  accounts: [
    { id: 'a1', platform: 'tiktok', username: 'arco.app', display_name: 'ARCO', avatar_url: '', brand_id: 'b1', needs_reconnect: 0 },
    { id: 'a2', platform: 'instagram', username: 'arco.app', display_name: 'ARCO', avatar_url: '', brand_id: 'b1', needs_reconnect: 0 },
    { id: 'a3', platform: 'facebook', username: 'ARCO Page', display_name: 'ARCO Page', avatar_url: '', brand_id: 'b1', needs_reconnect: 0 },
    { id: 'a4', platform: 'facebook', username: 'Client Bakery', display_name: 'Client Bakery', avatar_url: '', brand_id: 'b2', needs_reconnect: 0 },
    { id: 'a5', platform: 'tiktok', username: 'emilia', display_name: 'Emilia', avatar_url: '', brand_id: null, needs_reconnect: 1 },
    { id: 'a6', platform: 'instagram', username: 'arco.focus', display_name: 'ARCO Focus', avatar_url: '', brand_id: null, needs_reconnect: 0 },
  ],
  brands: [{ id: 'b1', name: 'ARCO', slots: null, voice: '' }, { id: 'b2', name: 'Client Bakery', slots: null, voice: '' }],
  api_key_set: false,
  limits: { accounts: 25, queued: 200, images: 35, image_bytes: 5242880, workspace_bytes: 209715200, min_lead_seconds: 300, ig_images: 10, ig_caption: 2200 },
  facebook_enabled: true, instagram_enabled: true, ai_enabled: true,
};
const acc = id => me.accounts.find(a => a.id === id);
const mk = (id, a, st, h, cap, extra = {}) => ({ id, account_id: a, platform: acc(a).platform, username: acc(a).username, status: st, title: '', caption: cap,
  images: [`/fake/${id}.svg`, `/fake/${id}b.svg`], image_keys: ['k' + id], cover_index: 0, settings: {}, scheduled_at: H(h),
  post_url: st === 'published' ? 'https://example.com/p' : null, fail_reason: st === 'failed' ? 'Instagram could not process the images: aspect ratio not supported' : null,
  group_id: null, updated_at: H(h), stats: null, ...extra });
const posts = [
  mk('p1', 'a3', 'published', -3, 'New drop: Jordan 4 Bred, sizes 40-45 in stock', { stats: { likes: 48, comments: 9, shares: 4 } }),
  mk('p2', 'a2', 'failed', -1.2, '3 apps that saved my mornings this week'),
  mk('p3', 'a2', 'queued', 1.5, 'Block your phone for one hour. Here is how'),
  mk('p4', 'a1', 'queued', 4, 'The 5-minute plan I make every night'),
  mk('p5', 'a4', 'queued', 7, 'Weekend restock: fresh sourdough'),
  mk('p6', 'a1', 'published', -26, 'Focus mode, explained in 6 slides', { stats: { views: 12400, likes: 830, comments: 41, shares: 22 } }),
  mk('p7', 'a6', 'published', -50, 'Morning routine that works', { stats: { likes: 212, comments: 17, views: 4810 } }),
  mk('p8', 'a3', 'queued', 30, 'Tomorrow: new colorway'),
  mk('p9', 'a1', 'queued', 52, 'Study timer setup'),
  mk('d1', 'a2', 'draft', -20, 'Draft: weekend vibes'),
];
const svg = id => { const n = [...id].reduce((s, c) => s + c.charCodeAt(0), 0); const h = [[28, 12], [205, 225], [110, 95], [320, 295], [42, 30], [250, 265]][n % 6];
  return `<svg xmlns='http://www.w3.org/2000/svg' width='400' height='500'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='hsl(${h[0]},60%,78%)'/><stop offset='1' stop-color='hsl(${h[1]},42%,42%)'/></linearGradient></defs><rect width='400' height='500' fill='url(#g)'/></svg>`; };
const media = {};
const body = q => new Promise(r => { let b = ''; q.on('data', d => b += d); q.on('end', () => { try { r(JSON.parse(b || '{}')); } catch { r({}); } }); });
http.createServer(async (q, r) => {
  const u = new URL(q.url, 'http://x'), p = u.pathname, j = (o, s = 200) => { r.statusCode = s; r.setHeader('Content-Type', 'application/json'); r.end(JSON.stringify(o)); };
  const cookie = q.headers.cookie || '', empty = cookie.includes('empty=1'), quiet = cookie.includes('quiet=1');
  if (p.startsWith('/api/v1/') && cookie.includes('out=1')) return j({ error: 'Sign in first' }, 401);
  // New posts "publish" a few seconds after they are due.
  for (const x of posts) if (x.created && x.status === 'queued' && x.scheduled_at <= now() && Date.now() - x.created > 5000) {
    if (x.fail) { x.status = 'failed'; x.fail_reason = 'Instagram could not process the images: aspect ratio not supported'; }
    else { x.status = 'published'; x.post_url = 'https://example.com/p'; } }
  if (p === '/api/v1/me') return j(empty ? { ...me, accounts: [], brands: [], workspace: { ...me.workspace, slots: null } } : me);
  if (p.startsWith('/fake/')) { r.setHeader('Content-Type', 'image/svg+xml'); return r.end(svg(p)); }
  if (p === '/api/v1/posts' && q.method === 'GET') return j({ posts: empty ? [] : quiet ? posts.filter(x => x.status === 'published' || x.status === 'failed').slice(0, 3).map((x, i) => i === 1 ? { ...x, username: '' } : x) : posts.filter(x => x.status !== 'draft') });
  if (p === '/api/v1/posts' && q.method === 'POST') { const o = await body(q), id = 'n' + Math.random().toString(16).slice(2, 8);
    const x = { ...mk(id, o.account_id, 'queued', 0, o.caption || ''), scheduled_at: o.scheduled_at || now(), images: (o.image_keys || []).map(k => '/media/' + k),
      created: Date.now(), fail: acc(o.account_id).platform === 'instagram' };
    posts.push(x); return j(x); }
  if (/^\/api\/v1\/posts\/\w+\/retry$/.test(p)) { const x = posts.find(y => y.id === p.split('/')[4]);
    if (x) Object.assign(x, { status: 'queued', fail: false, created: Date.now(), fail_reason: null }); return j(x || {}); }
  if (p === '/api/v1/drafts') return j({ drafts: empty ? [] : posts.filter(x => x.status === 'draft') });
  if (p === '/api/v1/ai/usage') return j({ limit: 50, remaining: 47 });
  if (p === '/api/v1/members') return j({ members: [{ user_id: 'u1', email: 'thinh@arco.app', role: 'owner', brand_ids: null }, { user_id: 'u2', email: 'freelancer@studio.co', role: 'member', brand_ids: ['b2'] }], invites: [] });
  if (p === '/api/v1/stats') { const d = Number(u.searchParams.get('days') || 30), plat = u.searchParams.get('platform') || 'all';
    const accs = me.accounts.filter(a => plat === 'all' || a.platform === plat);
    const top = posts.filter(x => x.stats && (plat === 'all' || x.platform === plat));
    const series = [...Array(d)].map((_, i) => { const day = new Date((now() - (d - 1 - i) * 86400) * 1000).toISOString().slice(0, 10);
      return { day, posts: i % 3 ? 0 : 1, views: i % 3 ? 0 : 800 + (i * 137) % 900, engagement: i % 3 ? 0 : 40 + (i * 53) % 120, followers: 1700 + Math.round(i * 140 / d) + (i % 5) }; });
    return j({ days: d, platform: plat, published: top.length, tracked: top.length, updated_at: now() - 5400,
      totals: plat === 'facebook' ? {} : { views: 17210, likes: 1090, comments: 67, shares: 26 }, previous: { published: 2, totals: { views: 12400, likes: 1210, comments: 50, shares: 26 } }, followers: { total: 1842, change: 37 }, series,
      by_platform: ['tiktok', 'instagram', 'facebook'].filter(pl => plat === 'all' || pl === plat).map((pl, i) => ({ platform: pl, posts: 3 - i, views: pl === 'facebook' ? null : 9000 - i * 3000, likes: pl === 'facebook' ? null : 700 - i * 200, comments: null, shares: null, followers: [412, 650, 780][i] })),
      platforms: ['tiktok', 'instagram', 'facebook'],
      accounts: accs.map(a => ({ id: a.id, username: a.username, platform: a.platform, avatar_url: '', followers: 300 + a.id.charCodeAt(1) * 7, change: a.id === 'a2' ? 12 : 0, limited: a.id === 'a5' })),
      top, tiktok_pending: false, tiktok_reconnect: true, facebook_limited: true }); }
  if (p.endsWith('/creator-info')) return j({ creator_username: 'arco.app', creator_nickname: 'ARCO', creator_avatar_url: '', comment_disabled: false, privacy_level_options: ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'SELF_ONLY'] });
  if (p === '/api/v1/media' && q.method === 'POST') { const ch = []; q.on('data', d => ch.push(d)); return q.on('end', () => { const key = 'ws1/' + Math.random().toString(16).slice(2) + '.jpg'; media[key] = Buffer.concat(ch); j({ key, url: '/media/' + key }); }); }
  if (p === '/api/v1/media/copy') { const o = await body(q);
    return j({ media: (o.keys || []).map(k => { const key = 'ws1/' + Math.random().toString(16).slice(2) + '.jpg'; media[key] = media[k]; return { key, url: '/media/' + key }; }) }); }
  if (p.startsWith('/media/') && media[p.slice(7)]) { r.setHeader('Content-Type', 'image/jpeg'); return r.end(media[p.slice(7)]); }
  if (p.startsWith('/api/')) { await body(q); return j({ ok: true }); }
  const f = path.join(root, p === '/' ? 'index.html' : p);
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.statusCode = 404; return r.end('not found'); }
  const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml' };
  r.setHeader('Content-Type', (types[path.extname(f)] || 'application/octet-stream') + '; charset=utf-8');
  fs.createReadStream(f).pipe(r);
}).listen(PORT, '127.0.0.1', () => console.log(`mock on http://localhost:${PORT}/app.html`));
