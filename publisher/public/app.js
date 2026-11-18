const PRIVACY_LABEL = { PUBLIC_TO_EVERYONE: 'Everyone', MUTUAL_FOLLOW_FRIENDS: 'Friends',
  FOLLOWER_OF_CREATOR: 'Followers', SELF_ONLY: 'Only me' };
const MAX_SIDE_W = 1080, MAX_SIDE_H = 1920;
const PLATFORM = { tiktok: 'TikTok', instagram: 'Instagram', facebook: 'Facebook' };
// Platform marks (Simple Icons, CC0), inlined so the page loads nothing from a third party.
const MARK = {
  tiktok: 'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z',
  instagram: 'M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077',
  facebook: 'M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z',
};
const icon = (pl, size = 16, cls = '') => `<svg class="pi ${pl} ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true"><path d="${MARK[pl]}"/></svg>`;
// The platform's own app icon, in its colors: TikTok's black tile with the
// cyan and red offset, Instagram's gradient, Facebook's blue circle.
const appIcon = (pl, size = 32) => {
  const g = `<path d="${MARK[pl]}"/>`;
  const inner = pl === 'tiktok'
    ? `<g transform="translate(5.6 5.4) scale(.53)"><g fill="#25F4EE" transform="translate(-.9 -.9)">${g}</g><g fill="#FE2C55" transform="translate(.9 .9)">${g}</g><g fill="#fff">${g}</g></g>`
    : pl === 'instagram' ? `<g fill="#fff" transform="translate(5.5 5.5) scale(.54)">${g}</g>`
    : `<circle cx="12" cy="12" r="9.2" fill="#fff"/><g fill="#0866FF" transform="translate(1.5 1.5) scale(.875)">${g}</g>`;
  const bg = pl === 'tiktok' ? '<rect width="24" height="24" rx="6" fill="#000"/>'
    : pl === 'instagram' ? `<defs><radialGradient id="igg${size}" cx="30%" cy="107%" r="150%"><stop offset="0" stop-color="#fdf497"/><stop offset=".05" stop-color="#fdf497"/><stop offset=".45" stop-color="#fd5949"/><stop offset=".6" stop-color="#d6249f"/><stop offset=".9" stop-color="#285AEB"/></radialGradient></defs><rect width="24" height="24" rx="6" fill="url(#igg${size})"/>`
    : '<rect width="24" height="24" rx="6" fill="#fff"/>';
  return `<svg class="appicon ${pl}" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true">${bg}${inner}</svg>`;
};
// The platform's mark pinned to the corner of an account's avatar.
const withBadge = (av, pl) => `<span class="avw">${av}<span class="badge-pl ${pl}">${icon(pl, 10)}</span></span>`;
// Instagram takes JPEG between 4:5 (portrait) and 1.91:1 (landscape), 10 per post.
const IG_MIN_RATIO = 4 / 5, IG_MAX_RATIO = 1.91, IG_MAX = 10, IG_CAPTION = 2200;
const CAPTION_MAX = { tiktok: 4000, instagram: IG_CAPTION, facebook: 63206 };
const IG_HASHTAGS = 30;
const hashtags = s => (String(s).match(/#[^\s#]+/g) || []).length;

const S = {
  me: null, view: 'overview', flash: null, counts: { drafts: 0, failed: 0 }, ov: null,
  images: [], cover: 0, title: '', caption: '',
  // A video post instead: one library video, { key, url, name, duration_ms }.
  video: null,
  // Every account the post goes to, any platform. TikTok accounts each carry
  // their own creator info, privacy and comment choice in S.tt.
  targets: [], tt: {},
  // A caption per platform, when it should differ from the main one. Absent
  // means "same as the main caption".
  over: {},
  drafts: [], fromDraft: null, draftGroup: null,
  slotEdit: null, queuePosts: null, detail: null,
  ai: { open: false, brief: '', tone: 'friendly', length: 'medium', emoji: true, hashtags: true, cta: '', language: '', busy: false, err: '', remaining: null },
  voiceEdit: null,
  set: { music: false, duet: false, stitch: false, disclose: false, brand: false, branded: false },
  when: 'now', at: '', busy: false, status: null,
  week: 0, month: 0, calMode: 'weeks', fPlat: 'all', fAcct: 'all', posts: [], apiKey: null,
  pq: '', pickOpen: false, capTab: 'all', prevTab: null,
  login: { step: 'email', email: '', code: '', busy: false, err: '' }, members: null, invited: null,
};
const ORDER = ['tiktok', 'instagram', 'facebook'];
const platformOf = a => a?.platform || 'tiktok';
const SAVED = 'arco-publisher.targets';
const INVITE = 'arco-publisher.invite';
const RANK = { member: 1, admin: 2, owner: 3 };
const can = role => !!S.me && RANK[S.me.workspace?.role || 'member'] >= RANK[role];

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const len = s => [...s].length;

async function api(path, opts = {}) {
  const r = await fetch('/api/v1' + path, { credentials: 'same-origin', ...opts });
  let body = {};
  try { body = await r.json(); } catch {}
  if (!r.ok) { const e = new Error(body.error || `Request failed (${r.status})`); e.status = r.status; e.code = body.code; throw e; }
  return body;
}

// ---- boot --------------------------------------------------------------

async function boot() {
  const q = new URL(location.href).searchParams;
  if (q.get('auth_error')) S.flash = { kind: 'err', text: q.get('auth_error') };
  else if (q.get('connected')) S.flash = { kind: 'ok', text: `Connected ${q.get('connected')} account${q.get('connected') === '1' ? '' : 's'}.` };
  // An invite link: kept through sign-in, accepted once signed in.
  if (q.get('invite')) { try { sessionStorage.setItem(INVITE, q.get('invite')); } catch {} }
  if (q.get('auth_error') || q.get('connected') || q.get('invite')) history.replaceState({}, '', location.pathname + location.hash);
  await loadMe();
  // A message belongs to the page it was shown on, unless it was set for the
  // page being opened (S.keepFlash).
  window.addEventListener('hashchange', () => { if (!S.keepFlash) S.flash = null; S.keepFlash = false; S.detail = null; route(); });
  route();
}

async function loadMe() {
  try { S.me = await api('/me'); } catch (e) { S.me = null; if (e.status !== 401) S.flash = { kind: 'err', text: e.message }; }
  if (!S.me || S.me.needs_email) return;
  let token = null;
  try { token = sessionStorage.getItem(INVITE); } catch {}
  if (token) {
    try { sessionStorage.removeItem(INVITE); } catch {}
    try { await send('/invites/accept', 'POST', { token }); S.me = await api('/me');
      S.flash = { kind: 'ok', text: `You joined ${S.me.workspace.name}.` }; }
    catch (e) { S.flash = { kind: 'err', text: e.message }; }
  }
  await fileNewAccounts();
  S.targets = []; S.tt = {};
  restoreTargets();
  const b = curBrand();
  if (b !== 'all') { S.targets = S.targets.filter(id => inBrand(acct(id), b));
    if (!S.targets.length) for (const a of brandAccounts(b)) if (!a.needs_reconnect) toggleTarget(a.id, true, false); }
  refreshCounts();
}

// The accounts last posted to come back preselected: someone running ten
// accounts posts to the same set most days.
function restoreTargets() {
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(SAVED) || '[]'); } catch {}
  for (const id of saved) { const a = acct(id); if (a && !a.needs_reconnect) toggleTarget(id, true, false); }
}
// Back from connecting: accounts that are new and in no brand go into the
// brand that was chosen when the connect started.
const PENDING_BRAND = 'arco-publisher.connect-brand';
async function fileNewAccounts() {
  let p = null;
  try { p = JSON.parse(localStorage.getItem(PENDING_BRAND) || 'null'); localStorage.removeItem(PENDING_BRAND); } catch {}
  if (!p || Date.now() - p.at > 30 * 60e3 || !brandName(p.brand) || !can('admin')) return;
  const fresh = S.me.accounts.filter(a => !p.known.includes(a.id) && !a.brand_id).map(a => a.id);
  // Nothing new: the platform connected an account that was already here
  // (TikTok picks whoever is signed in on tiktok.com).
  if (!fresh.length) {
    if (p.pl) S.flash = { kind: 'err', text: `${PLATFORM[p.pl]} connected an account that is already here, so nothing was added to ${brandName(p.brand)}. `
      + (p.pl === 'tiktok' ? 'To add a different TikTok account, choose "Switch account" on TikTok\'s screen, or sign out of tiktok.com first, then try again.'
        : 'To add a different one, log in with it on the platform\'s screen.') };
    return;
  }
  try { await send(`/brands/${p.brand}/accounts`, 'POST', { account_ids: fresh }); S.me = await api('/me');
    S.flash = { kind: 'ok', text: `Added to ${brandName(p.brand)}.` }; } catch {}
}
function saveTargets() { try { localStorage.setItem(SAVED, JSON.stringify(S.targets)); } catch {} }

const VIEWS = ['overview', 'compose', 'library', 'calendar', 'analytics', 'drafts', 'accounts', 'ai', 'settings'];
function route() {
  S.view = (location.hash || '#overview').slice(1);
  if (!VIEWS.includes(S.view)) S.view = 'overview';
  const signedIn = !!S.me && !S.me.needs_email;
  if (signedIn && S.view === 'overview') loadOverview();
  if (signedIn && S.view === 'calendar') loadWeek();
  if (signedIn && S.view === 'ai') loadAi();
  if (signedIn && S.view === 'drafts') loadDrafts();
  if (signedIn && S.view === 'analytics') loadStats();
  if (signedIn && S.view === 'library') { if (S.lastView !== 'library') S.folderOpen = null; loadLibrary(); }
  S.anim = S.lastView !== S.view; S.lastView = S.view;
  render();
  window.scrollTo(0, 0);
}

// ---- render ------------------------------------------------------------

// UI icons: one stroke weight everywhere.
const UI = {
  play: '<path d="M7 4.5v15l12-7.5z" fill="currentColor" stroke="none"/>',
  spark: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m14 6 4 4"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/>',
  warn: '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4M12 17.5v.01"/>',
  more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
  cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  draft: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20a6.5 6.5 0 0 0-4-6"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', x: '<path d="M18 6 6 18M6 6l12 12"/>',
  retry: '<path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 21v-5h5"/>',
  chev: '<path d="m7 15 5 5 5-5M7 9l5-5 5 5"/>', check: '<path d="m5 12 5 5 9-10"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  heart: '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>',
  comment: '<path d="M4 5h16v11H9l-5 4z"/>', share: '<path d="M4 13v6h16v-6M12 3v12M7 8l5-5 5 5"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
};
const ui = (n, s = 18) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${UI[n]}</svg>`;

// The workspace and its switcher, shown at the top of the menu.
function wsBox() {
  const w = S.me.workspace, list = S.me.workspaces || [];
  const label = w.role === 'owner' ? 'Owner' : w.role === 'admin' ? 'Admin' : w.brand_scope ? 'Member, some brands' : 'Member';
  return `<div class="ws"><div class="wsbox"><span class="sq">${esc((w.name || 'W')[0].toUpperCase())}</span>
      <span class="nm"><span>${esc(w.name)}</span><small>${label}</small></span>${list.length > 1 ? ui('chev', 16) : ''}</div>
    ${list.length > 1 ? `<select id="wsswitch" aria-label="Switch workspace">${list.map(x =>
      `<option value="${x.id}" ${x.id === w.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>` : ''}</div>`;
}

function menu() {
  const items = [['overview', 'Overview', 'home'], ['compose', 'Schedule', 'edit'], ['library', 'Library', 'image'], ['calendar', 'Calendar', 'cal', S.counts.failed, 'bad'], ['analytics', 'Analytics', 'chart'],
    ['drafts', 'Drafts', 'draft', S.counts.drafts], ...(can('admin') ? [['accounts', 'Accounts', 'users']] : []), ['ai', 'MCP', 'spark']];
  const email = S.me.user?.email || '';
  return `<a class="brand-row" href="#overview"><img class="logo" src="/apple-touch-icon.png" alt="" width="30" height="30"><b>ARCO Publisher</b></a>
    ${wsBox()}
    ${brandNav()}
    <a class="create-side" href="#compose" title="Schedule post">${ui('plus', 16)}<span class="lb">Schedule post</span></a>
    <nav class="nav" aria-label="Main">${items.map(([k, l, i, n, tone]) =>
      `<a href="#${k}" title="${l}" class="${S.view === k ? 'on' : ''}" ${S.view === k ? 'aria-current="page"' : ''}>${ui(i)}<span class="lb">${l}</span>${n ? `<span class="n ${tone || ''}" title="${tone === 'bad' ? `${n} failed in the last 7 days` : `${n} waiting`}">${n}</span>` : ''}</a>`).join('')}</nav>
    <div class="grow"></div>
    <nav class="nav"><a href="#settings" title="Settings" class="${S.view === 'settings' ? 'on' : ''}">${ui('gear')}<span class="lb">Settings</span></a></nav>
    <div class="me"><span class="av-me">${esc((email[0] || '?').toUpperCase())}</span>
      <div><b>${esc(email)}</b><a href="/api/auth/logout">Sign out</a></div></div>`;
}

function tabbar() {
  const t = (k, l, i) => `<a href="#${k}" class="${S.view === k ? 'on' : ''}">${ui(i, 20)}${l}</a>`;
  return t('overview', 'Overview', 'home') + t('calendar', 'Calendar', 'cal') +
    `<a href="#compose" aria-label="Schedule post"><span class="plus">${ui('plus', 22)}</span></a>` +
    t('drafts', 'Drafts', 'draft') + (can('admin') ? t('accounts', 'Accounts', 'users') : t('settings', 'Settings', 'gear'));
}

const HEADS = {
  compose: () => ['Schedule post', S.targets.length ? `Goes to ${S.targets.length} account${S.targets.length === 1 ? '' : 's'}.` : 'Pick a brand, add photos, write the caption.'],
  library: () => ['Library', 'Upload photos and videos ahead of time, filed by brand. Pick from them when you schedule.'],
  calendar: () => ['Calendar', `Everything scheduled and published, in ${tz().replace(/_/g, ' ')} time.`, `<a class="btn" href="#compose">${ui('plus', 16)}New post</a>`],
  analytics: () => ['Analytics', 'How your posts do, from the numbers each platform shares.'],
  drafts: () => ['Drafts', 'Posts saved for later. Open one to finish and schedule it.', `<a class="btn" href="#compose">${ui('plus', 16)}New post</a>`],
  accounts: () => ['Brands & accounts', `Each brand holds its TikTok, Instagram and Facebook accounts. Pick a brand when you schedule and its accounts come with it. ${S.me.accounts.length} of ${S.me.limits.accounts} accounts connected.`, `<button class="btn" id="newbrandbtn">${ui('plus', 15)}New brand</button>`],
  settings: () => ['Settings', 'Workspace, people and your account.'],
  ai: () => ['MCP', 'Plan and schedule posts by chatting with your AI.', ''],
};
// Grey shapes in the layout of what is coming, instead of the word Loading.
const sk = (w = '100%', h = 14, cls = '') => `<span class="sk ${cls}" style="width:${w};height:${h}px"></span>`;
const skRows = n => [...Array(n)].map(() => `<div class="skrow">${sk('40px', 40, 'sq')}<div>${sk('55%', 13)}${sk('80%', 11)}</div></div>`).join('');
const skKpis = n => `<div class="kpis ${n === 5 ? 'five' : ''}">${[...Array(n)].map(() => `<div class="kpi">${sk('50%', 12)}${sk('40%', 30)}${sk('60%', 11)}</div>`).join('')}</div>`;
const pageHead = (title, sub, action = '') => `<div class="pagehead"><div><h1>${title}</h1>${sub ? `<p>${sub}</p>` : ''}</div>${action}</div>`;

// The app's own confirm and prompt: says what will happen and what will
// not, names the thing, and puts the risky action in red. Resolves to true
// (or the typed value), or false when cancelled. `type` asks the person to type
// a word first for things that cannot be undone.
function ask({ title, body = '', ok = 'Confirm', danger = false, icon = '', list = [], input = null, type = null }) {
  return new Promise(resolve => {
    const box = $('dialogs'), back = document.activeElement;
    box.innerHTML = `<div class="dlg-bg"><div class="dlg" role="alertdialog" aria-modal="true" aria-labelledby="dlgt" aria-describedby="dlgb">
      ${icon ? `<div class="dlg-ic ${danger ? 'bad' : ''}">${icon}</div>` : ''}
      <h2 id="dlgt">${title}</h2>${body ? `<p id="dlgb">${body}</p>` : ''}
      ${list.length ? `<ul class="dlg-list">${list.map(([good, t]) => `<li class="${good ? 'ok' : 'no'}">${ui(good ? 'check' : 'x', 14)}<span>${t}</span></li>`).join('')}</ul>` : ''}
      ${input ? `<input type="text" id="dlgin" value="${esc(input.value || '')}" placeholder="${esc(input.placeholder || '')}" aria-label="${esc(input.label || title)}" maxlength="60">` : ''}
      ${type ? `<label class="dlg-type" for="dlgin">Type <b>${esc(type)}</b> to confirm</label><input type="text" id="dlgin" autocomplete="off" spellcheck="false">` : ''}
      <div class="dlg-acts"><button class="btn sec" data-dlg="no">Cancel</button><button class="btn ${danger ? 'red' : ''}" data-dlg="yes" ${type ? 'disabled' : ''}>${ok}</button></div></div></div>`;
    const inp = $('dlgin'), yes = box.querySelector('[data-dlg=yes]');
    const done = v => { box.innerHTML = ''; document.removeEventListener('keydown', key, true); back?.focus?.(); resolve(v); };
    const go = () => { if (yes.disabled) return; done(input ? inp.value.trim() || false : true); };
    const key = e => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); done(false); }
      else if (e.key === 'Enter' && (input || type) && document.activeElement === inp) { e.preventDefault(); go(); }
      else if (e.key === 'Tab') { const f = [...box.querySelectorAll('input,button:not(:disabled)')];
        if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f.at(-1).focus(); }
        else if (!e.shiftKey && document.activeElement === f.at(-1)) { e.preventDefault(); f[0].focus(); } }
    };
    document.addEventListener('keydown', key, true);
    if (type) inp.addEventListener('input', () => { yes.disabled = inp.value.trim() !== type; });
    box.querySelector('[data-dlg=no]').onclick = () => done(false);
    yes.onclick = go;
    box.querySelector('.dlg-bg').onclick = e => { if (e.target.classList.contains('dlg-bg')) done(false); };
    (inp || (danger ? box.querySelector('[data-dlg=no]') : yes)).focus();
    if (input) inp.select();
  });
}

function toast(text, kind = '') {
  const el = document.createElement('div');
  el.className = `toast ${kind === 'err' ? 'err' : ''}`;
  el.setAttribute('role', kind === 'err' ? 'alert' : 'status');
  el.innerHTML = `<span>${esc(text)}</span><button aria-label="Dismiss">${ui('x', 14)}</button>`;
  el.querySelector('button').onclick = () => el.remove();
  $('toasts').appendChild(el);
  setTimeout(() => el.remove(), kind === 'err' ? 9000 : 5000);
}

function render() {
  const signedIn = !!S.me && !S.me.needs_email;
  // Messages become toasts; the page keeps only inline errors.
  if (S.flash) { toast(S.flash.text, S.flash.kind); S.flash = null; }
  $('shell').classList.toggle('bare', !signedIn);
  $('side').hidden = $('mtop').hidden = $('tabbar').hidden = !signedIn;
  if (!signedIn) { $('app').innerHTML = signInView(); bind(); return; }
  if (S.view === 'accounts' && !can('admin')) S.view = 'overview';
  $('side').innerHTML = menu();
  $('mtop').innerHTML = `<img class="logo" src="/apple-touch-icon.png" alt="" width="30" height="30">${wsBox()}`;
  $('tabbar').innerHTML = tabbar();
  $('tabbar').classList.toggle('flat', S.view === 'compose');
  const views = { ai: aiView, library: libraryView, analytics: analyticsView, overview: overviewView, calendar: calendarView, drafts: draftsView, accounts: accountsView, settings: settingsView, compose: composeView };
  const head = S.view === 'overview' ? '' : pageHead(...HEADS[S.view]());
  const hadDetail = !!$('overlay'), opener = S.detail && !hadDetail ? document.activeElement?.closest?.('[data-open]')?.dataset.open : null;
  if (S.anim) { $('app').classList.remove('in'); void $('app').offsetWidth; $('app').classList.add('in'); S.anim = false;
    clearTimeout(S.animT); S.animT = setTimeout(() => $('app').classList.remove('in'), 400); }
  $('app').innerHTML = head + (['calendar', 'analytics', 'drafts', 'library'].includes(S.view) ? brandChips('phone') : '') + views[S.view]() + (['calendar', 'overview'].includes(S.view) && S.detail ? detailView() : '') + resultView();
  bind();
  if (S.detail && !hadDetail) { S.opener = opener; $('closedetail')?.focus(); }
  if (!S.detail && hadDetail && S.opener) { document.querySelector(`[data-open="${S.opener}"]`)?.focus(); S.opener = null; }
}

// ---- overview ----------------------------------------------------------------
// What goes out today, what needs a hand, how the week looks, what just went
// live. Built from the posts, drafts and accounts the workspace already has.

async function loadOverview() {
  const now = Math.floor(Date.now() / 1000);
  try {
    const [posts, drafts] = await Promise.all([
      api(`/posts?from=${now - 14 * 86400}&to=${now + 14 * 86400}`), api('/drafts')]);
    S.posts = posts.posts;
    S.drafts = drafts.drafts;
    S.counts = { drafts: draftGroups().length, failed: S.posts.filter(p => p.status === 'failed' && p.scheduled_at > now - 7 * 86400).length };
    S.ov = { at: now };
    api(`/stats?days=7&brand=${encodeURIComponent(curBrand())}`).then(st => { S.ovStats = st; if (S.view === 'overview') render(); }).catch(() => {});
  } catch (e) { S.flash = { kind: 'err', text: e.message }; S.ov = { at: now, err: true }; }
  if (S.view === 'overview') render();
}

function greeting() {
  const h = zoned(Date.now()).h;
  return h < 5 ? 'Good evening' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

const thumbOf = p => p.images?.[p.cover_index] || p.images?.[0] || p.video;
// TikTok's own cover once stats are in; its link expires, so the post's media stays behind it.
const thumb = (p, attrs = 'alt=""') => {
  const own = thumbOf(p), cover = p.stats?.cover;
  return cover ? `<img src="${esc(cover)}" ${own ? `data-fb="${esc(own)}"` : ''} ${attrs}>` : own ? pic(own, attrs) : '';
};
const isVid = u => /\.(mp4|mov)(#|$)/i.test(String(u || ''));
// An image, or for a video its first frame.
const pic = (u, attrs = 'alt=""', still = true) => !isVid(u) ? `<img src="${esc(u)}" ${attrs}>`
  : still ? `<img src="${esc(u)}.jpg" data-fb="${esc(u)}" data-vid="1" ${attrs}>`
  : `<video src="${esc(u)}#t=0.1" preload="metadata" muted playsinline ${attrs.replace(/\balt="[^"]*"/, '')}></video>`;
const mmss = ms => { const t = Math.round((ms || 0) / 1000); return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`; };
const at = (sec, o = { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }) => fmt(sec, o);

// The brand the whole app is narrowed to: 'all', a brand id, or 'none' (in no
// brand). Overview, Calendar, Analytics, Drafts and Create all follow it.
const BRAND_KEY = 'arco-publisher.brand';
const BRAND_HUES = ['#6D5BD0', '#D9822B', '#0E9384', '#D4537E', '#3B5BDB', '#7A9A01'];
const brandHue = id => { const i = S.me.brands.findIndex(b => b.id === id); return i < 0 ? 'var(--soft)' : BRAND_HUES[i % BRAND_HUES.length]; };
function curBrand() {
  if (S.brand === undefined) { try { S.brand = localStorage.getItem(BRAND_KEY) || 'all'; } catch { S.brand = 'all'; } }
  if (!S.me?.brands.length) return 'all';
  const ok = S.brand === 'all' || (S.brand === 'none' ? S.me.accounts.some(a => !brandName(a.brand_id)) : !!brandName(S.brand));
  return ok ? S.brand : 'all';
}
const brandAccounts = (b = curBrand()) => S.me.accounts.filter(a => inBrand(a, b));
const brandLabel = b => (b === 'all' ? 'All brands' : b === 'none' ? 'Personal' : brandName(b));
// The choices: every brand, plus "Personal" while some account is in none.
const brandOpts = () => [['all', 'All brands', S.me.accounts.length], ...S.me.brands.map(x => [x.id, x.name, brandAccounts(x.id).length]),
  ...(S.me.accounts.some(a => !brandName(a.brand_id)) ? [['none', 'Personal', brandAccounts('none').length]] : [])];
const brandDot = k => (k === 'all' ? '' : `<i style="background:${k === 'none' ? 'var(--soft)' : brandHue(k)}"></i>`);

// Switching brand: the Create page picks that brand's accounts, and the
// numbers on Analytics are read again for it.
function setBrand(k) {
  S.brand = k; try { localStorage.setItem(BRAND_KEY, k); } catch {}
  S.fAcct = 'all'; S.pq = '';
  if (k !== 'all') {
    if (!S.replaces && !S.fromDraft) {
      for (const id of [...S.targets]) toggleTarget(id, false, false);
      for (const a of brandAccounts(k)) if (!a.needs_reconnect) toggleTarget(a.id, true, false);
    } else for (const id of [...S.targets]) if (!inBrand(acct(id), k)) toggleTarget(id, false, false);
  }
  if (S.view === 'analytics') { S.stats = null; loadStats(); }
  render();
}

// The switch: a list in the menu, chips on a phone (where there is no menu).
function brandNav() {
  if (!S.me.brands.length) return can('admin') && S.me.accounts.length ? `<div class="bnav"><span class="bnh">Brands</span>
    <a class="bnew" href="#accounts" title="New brand"><span class="bsq">${ui('plus', 14)}</span><span class="lb">New brand</span></a></div>` : '';
  const b = curBrand();
  return `<div class="bnav" role="group" aria-label="Brand"><span class="bnh">Brands</span>${brandOpts().map(([k, l, n]) =>
    `<button class="${b === k ? 'on' : ''}" data-brand="${k}" aria-pressed="${b === k}" title="${esc(l)}">
      <span class="bsq" style="${k === 'all' ? '' : `background:${k === 'none' ? 'var(--soft)' : brandHue(k)}`}">${k === 'all' ? ui('users', 14) : esc((l[0] || '?').toUpperCase())}</span>
      <span class="lb">${esc(l)}</span><span class="bn">${n}</span></button>`).join('')}</div>`;
}
function brandChips(cls = '') {
  if (!S.me.brands.length) return '';
  const b = curBrand();
  return `<div class="bchips ${cls}" role="group" aria-label="Brand">${brandOpts().map(([k, l]) =>
    `<button class="bchip ${b === k ? 'on' : ''}" data-brand="${k}" aria-pressed="${b === k}">${brandDot(k)}${esc(l)}</button>`).join('')}</div>`;
}
const inBrand = (a, b) => b === 'all' || (b === 'none' ? !brandName(a?.brand_id) : a?.brand_id === b);
const engOf = s => (s.likes || 0) + (s.comments || 0) + (s.shares || 0) + (s.saves || 0);

function overviewView() {
  const all = S.me.accounts;
  if (!all.length) return firstRun();
  const brands = S.me.brands, loose = all.some(a => !brandName(a.brand_id)), b = curBrand();
  const chips = brandChips('phone');
  if (!S.ov) return `<div class="ohead"><div><h1>${greeting()}</h1><p>${sk('260px', 14)}</p></div>${chips}</div>${skKpis(4)}
    <section class="panel"><header><h2>This week</h2></header><div class="wk">${[...Array(7)].map(() => `<div class="owd">${sk('60%', 14)}${sk('100%', 50)}</div>`).join('')}</div></section>`;

  const acc = all.filter(a => inBrand(a, b)), ids = new Set(acc.map(a => a.id));
  const now = Math.floor(Date.now() / 1000), week = 7 * 86400, t0 = today(), todayKey = dayKey(t0);
  const live = S.posts.filter(p => p.status !== 'cancelled' && ids.has(p.account_id));
  const upcoming = live.filter(p => p.status === 'queued' && p.scheduled_at >= now).sort((x, y) => x.scheduled_at - y.scheduled_at);
  const next = upcoming[0];
  const leftToday = upcoming.filter(p => dayOf(p.scheduled_at) === todayKey).length;
  const sub = next
    ? `${leftToday ? `${leftToday} post${leftToday === 1 ? '' : 's'} left today · ` : ''}next at <b>${at(next.scheduled_at)}</b>${dayOf(next.scheduled_at) === todayKey ? '' : ` ${fmt(next.scheduled_at, { weekday: 'short' })}`} on ${who(next)}`
    : 'Nothing scheduled yet.';

  // Problems only: failed posts and accounts that lost access.
  const failed = live.filter(p => p.status === 'failed' && p.scheduled_at > now - week);
  const reconnect = acc.filter(a => a.needs_reconnect);
  const probs = [...failed.slice(0, 3).map(p => `<button class="aitem" data-open="${p.id}"><b>Failed on ${who(p)}</b><span title="${esc(p.fail_reason || '')}">${esc(p.fail_reason || 'Open it to see why')}</span></button>`),
    ...(failed.length > 3 ? [`<a class="aitem" href="#calendar"><b>${failed.length - 3} more failed</b></a>`] : []),
    ...reconnect.map(a => `<a class="aitem" href="#accounts"><b>Reconnect ${who(a)}</b><span>${PLATFORM[platformOf(a)]} access expired</span></a>`)];
  const alert = probs.length ? `<div class="oalert" role="status"><span class="ic">${ui('x', 15)}</span><div class="aitems">${probs.join('')}</div></div>` : '';

  // Results, from each published post's own numbers: last 7 days against the 7 before.
  const pub = live.filter(p => p.status === 'published');
  const cur = pub.filter(p => p.scheduled_at > now - week), prev = pub.filter(p => p.scheduled_at <= now - week && p.scheduled_at > now - 2 * week);
  const sum = (list, f) => { const s = list.filter(p => p.stats); return s.length ? s.reduce((n, p) => n + f(p.stats), 0) : null; };
  const hasViews = cur.some(p => p.stats?.views != null);
  const views = hasViews ? sum(cur, s => s.views || 0) : null, pviews = sum(prev, s => s.views || 0);
  const eng = sum(cur, engOf), peng = sum(prev, engOf);
  const pct = (v, pv) => (v == null || !pv ? null : Math.round((v - pv) / pv * 100));
  const trend = p => (p == null ? '' : `<span class="${p > 0 ? 'up' : p < 0 ? 'dn' : ''}">${p > 0 ? '↑' : p < 0 ? '↓' : '='} ${Math.abs(p)}%</span> vs previous 7 days`);
  const days7 = [...Array(7)].map((_, i) => dayKey(addDays(t0, i - 6)));
  const spark = f => { const v = days7.map(k => cur.filter(p => dayOf(p.scheduled_at) === k && p.stats).reduce((n, p) => n + f(p.stats), 0)), m = Math.max(...v);
    return m ? `<span class="spark" aria-hidden="true">${v.map(x => `<i style="height:${Math.max(6, Math.round(x / m * 100))}%"></i>`).join('')}</span>` : ''; };
  const sacc = (S.ovStats?.accounts || []).filter(a => ids.has(a.id));
  const fchg = sacc.filter(a => a.change != null), ftot = sacc.filter(a => a.followers != null);
  const followers = fchg.length ? fchg.reduce((n, a) => n + a.change, 0) : null;
  const next7 = upcoming.filter(p => p.scheduled_at < now + week).length;
  // Platforms count differently (Facebook has no views), so each figure also shows its parts.
  const oplats = ORDER.filter(pl => acc.some(a => platformOf(a) === pl));
  const split = key => oplats.length < 2 ? '' : ksplit(oplats.map(pl => {
    const list = cur.filter(p => (p.platform || 'tiktok') === pl && p.stats && key(p.stats) != null);
    return [pl, list.length ? list.reduce((n, p) => n + key(p.stats), 0) : null]; }));
  const kpis = [
    ['#analytics', 'Views · 7 days', num(views), views == null ? (S.ovStats?.tiktok_reconnect ? 'Reconnect TikTok for views' : 'Shows once platforms share it') : trend(pct(views, pviews)) || `${cur.length} post${cur.length === 1 ? '' : 's'}`, spark(s => s.views || 0), split(s => s.views)],
    ['#analytics', 'Engagement', num(eng), eng == null ? 'Likes, comments and shares' : trend(pct(eng, peng)) || (views ? `${(eng / views * 100).toFixed(1)}% of views` : 'likes, comments, shares'), spark(engOf), split(engOf)],
    ['#analytics', 'New followers', followers == null ? '–' : signed(followers), ftot.length ? `${num(ftot.reduce((n, a) => n + a.followers, 0))} in total` : S.ovStats ? 'Shows after a day' : '', ''],
    ['#calendar', 'Published · 7 days', String(cur.length), `${next7} scheduled next 7 days${failed.length ? ` · <span class="dn">${failed.length} failed</span>` : ''}`, ''],
  ];

  // The week: today and the six days after, every post as a tile.
  const days = [...Array(7)].map((_, i) => addDays(t0, i));
  const onDay = d => live.filter(p => dayOf(p.scheduled_at) === dayKey(d)).sort((x, y) => x.scheduled_at - y.scheduled_at);
  const tile = p => { const st = next && p.id === next.id ? 'next' : p.status, a = all.find(x => x.id === p.account_id);
    return `<button class="opt ${st}" data-open="${p.id}" style="--bc:${brandHue(a?.brand_id)}" title="Open post">
      <span class="oth">${thumb(p)}<span class="pb">${icon(p.platform || 'tiktok', 9)}</span></span>
      <span class="tx"><b>${at(p.scheduled_at)}${st === 'failed' ? ' · failed' : st === 'next' ? ' · next' : ''}</b><span>${who(p)}</span></span></button>`; };
  const nowLine = `<div class="nowl"><time>${at(now)}</time><i></i></div>`;
  const col = (d, i) => { const k = dayKey(d), list = onDay(d), isT = i === 0;
    const before = isT ? list.filter(p => p.scheduled_at < now) : [], after = isT ? list.filter(p => p.scheduled_at >= now) : list;
    return `<div class="owd ${isT ? 'today' : ''}"><div class="wdh"><span>${i === 0 ? 'Today' : dayLabel(d, { weekday: 'short' })} <b>${d.d}</b></span><em class="${list.length ? '' : 'z'}">${list.length || '–'}</em></div>
      <div class="wdl">${before.map(tile).join('')}${isT && list.length ? nowLine : ''}${after.map(tile).join('')}</div>
      <button class="wadd" data-newon="${k}" aria-label="Schedule a post on ${esc(dayLabel(d, { weekday: 'long' }))}">${ui('plus', 13)}<span>Schedule</span></button></div>`; };
  const weekEmpty = days.every(d => !onDay(d).length);
  const legend = brands.length && b === 'all' ? `<span class="legend">${brands.map(x => `<span><i style="background:${brandHue(x.id)}"></i>${esc(x.name)}</span>`).join('')}${loose ? '<span><i style="background:var(--soft)"></i>Personal</span>' : ''}</span>` : '';
  const weekCard = `<section class="panel owk"><header><h2>This week</h2>${legend}<a href="#calendar">Open calendar</a></header>
    ${weekEmpty ? `<div class="splan"><span class="splan-ic">${ui('cal', 22)}</span><b>Nothing scheduled this week</b>
      <span>Plan a post for any day, or set posting times and let "Add to queue" fill them for you.</span>
      <div><button class="btn" data-newon="${todayKey}">${ui('plus', 15)}Schedule a post</button>${!S.me.workspace.slots && can('admin') ? '<a class="btn sec" href="#settings">Set posting times</a>' : ''}</div></div>`
      : `<div class="wk">${days.map(col).join('')}</div>`}</section>`;

  // Each account: what it has coming, what went out, and how it did.
  const rows = brandGroups(acc).flatMap(g => g.accounts).map(a => {
    const mine = live.filter(p => p.account_id === a.id), sa = sacc.find(x => x.id === a.id);
    const sched = mine.filter(p => p.status === 'queued' && p.scheduled_at >= now && p.scheduled_at < now + week).length;
    const out = mine.filter(p => p.status === 'published' && p.scheduled_at > now - week);
    const v = out.some(p => p.stats?.views != null) ? out.reduce((n, p) => n + (p.stats?.views || 0), 0) : null;
    const fails = mine.filter(p => p.status === 'failed' && p.scheduled_at > now - week).length;
    return `<tr><td><span class="acc"><i style="background:${brandHue(a.brand_id)}"></i>${withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))}
        <span class="an"><b>${handle(a)}</b><small>${PLATFORM[platformOf(a)]}</small></span>
        ${a.needs_reconnect ? '<a class="tag warn" href="#accounts">Reconnect</a>' : fails ? `<span class="tag bad">${fails} failed</span>` : ''}</span></td>
      <td class="n ${sched || a.needs_reconnect ? '' : 'z'}" title="${sched ? '' : 'Nothing scheduled in the next 7 days'}">${sched}</td><td class="n">${out.length}</td>
      <td class="n">${num(v)}</td><td class="n ${sa?.change > 0 ? 'up' : sa?.change < 0 ? 'dn' : ''}">${sa?.change == null ? '–' : signed(sa.change)}</td></tr>`; }).join('');
  const accCard = `<section class="panel oacc"><header><h2>By account</h2><span class="note">next and last 7 days</span><a href="#analytics">Analytics</a></header>
    <table class="atab"><thead><tr><th>Account</th><th class="n">Scheduled</th><th class="n">Published</th><th class="n">Views</th><th class="n">Followers</th></tr></thead><tbody>${rows}</tbody></table></section>`;

  // Best of the last 7 days by views (or engagement where views are not shared), else the latest.
  const scored = cur.filter(p => p.stats).sort((x, y) => (y.stats.views || 0) - (x.stats.views || 0) || engOf(y.stats) - engOf(x.stats));
  const top = (scored.length ? scored : pub.slice().sort((x, y) => y.scheduled_at - x.scheduled_at)).slice(0, 3);
  const ttile = p => `<button class="tp" data-open="${p.id}"><span class="im">${thumb(p)}<span class="pbadge">${appIcon(p.platform || 'tiktok', 20)}</span></span>
    <b>${p.stats?.views != null ? `${num(p.stats.views)} views` : p.stats ? `${num(engOf(p.stats))} engagements` : fmt(p.scheduled_at, { month: 'short', day: 'numeric' })}</b>
    <span>${who(p)}</span></button>`;
  const topCard = `<section class="panel otop"><header><h2>${scored.length ? 'Top posts' : 'Recently published'}</h2><span class="note">${scored.length ? 'last 7 days' : ''}</span><a href="#analytics">See all</a></header>
    ${top.length ? `<div class="tops">${top.map(ttile).join('')}</div>`
      : `<div class="snone"><span>Published posts show here with their numbers.</span><a class="btn sec" href="#compose">${ui('plus', 15)}Create post</a></div>`}</section>`;

  return `<div class="ohead"><div><h1>${greeting()}</h1><p>${sub}</p></div>${chips}</div>
  ${alert}
  <div class="kpis">${kpis.map(([href, l, v, note, sp, parts = '']) => `<a href="${href}" class="kpi"><span>${l}</span><b>${v}</b><small>${note}</small>${parts}${sp}</a>`).join('')}</div>
  ${weekCard}
  <div class="obot">${accCard}${topCard}</div>`;
}

// ---- stats ---------------------------------------------------------------
// Numbers the platforms share: Instagram and Facebook today, TikTok once its
// review grants the stats scopes. Read by the Worker every few hours.

const METRIC = { views: 'Views', reach: 'Reach', likes: 'Likes', comments: 'Comments', shares: 'Shares', saves: 'Saves' };
const STAT_KEYS = ['views', 'reach', 'likes', 'comments', 'shares', 'saves'];
const STAT_ICON = { views: 'eye', reach: 'eye', likes: 'heart', comments: 'comment', shares: 'share', saves: 'draft' };
const num = n => (n == null ? '–' : new Intl.NumberFormat(undefined, n >= 10000 ? { notation: 'compact', maximumFractionDigits: 1 } : {}).format(n));
const signed = n => (n == null ? '' : `${n > 0 ? '+' : n < 0 ? '−' : ''}${num(Math.abs(n))}`);
const statLine = st => `<span class="sline">${['views', 'likes', 'comments', 'shares'].filter(k => st[k] != null)
  .map(k => `<span title="${METRIC[k]}">${ui(STAT_ICON[k], 12)}${num(st[k])}</span>`).join('')}</span>`;
const ago = sec => { const m = Math.round((Date.now() / 1000 - sec) / 60);
  return m < 60 ? `${Math.max(1, m)} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} days ago`; };

const statsCache = new Map();
async function loadStats(days = S.statsDays || 30, plat = S.statsPlat || 'all') {
  S.statsDays = days; S.statsPlat = plat;
  const key = `${days}|${plat}|${curBrand()}`;
  S.stats = statsCache.get(key) || null;
  if (S.view === 'analytics') render();
  let st;
  try { st = await api(`/stats?days=${days}&platform=${plat}&brand=${encodeURIComponent(curBrand())}`); statsCache.set(key, st); } catch (e) { st = statsCache.get(key) || { err: e.message }; }
  if (key !== `${S.statsDays}|${S.statsPlat}|${curBrand()}`) return;
  S.stats = st;
  if (S.view === 'analytics') render();
}

// A small chart: one series, one axis, a hover tooltip per day. Bars for
// counts per day, a line for a running total.
function chart(series, key, { kind = 'bar', label, fmtv = num } = {}) {
  const vals = series.map(d => d[key]);
  const known = vals.filter(v => v != null);
  if (!known.length || (kind === 'bar' && !known.some(v => v > 0))) return `<div class="cempty2">No ${label.toLowerCase()} in this period yet.</div>`;
  const W = 600, Hh = 180, n = series.length;
  let lo = kind === 'line' ? Math.min(...known) : 0, hi = Math.max(...known);
  if (kind === 'line') { const pad = Math.max(1, (hi - lo) * 0.15); lo = Math.max(0, lo - pad); hi += pad; }
  if (hi === lo) hi = lo + 1;
  const y = v => Hh - ((v - lo) / (hi - lo)) * Hh, step = W / n;
  const grid = [0, .5, 1].map(f => `<line x1="0" x2="${W}" y1="${Hh * f}" y2="${Hh * f}" class="g"/>`).join('');
  let marks = '';
  if (kind === 'bar') {
    const bw = Math.max(1, step - 2);
    marks = vals.map((v, i) => v ? `<rect class="b" x="${i * step + 1}" y="${y(v)}" width="${bw}" height="${Hh - y(v)}"/>` : '').join('');
  } else {
    let d = '', on = false;
    vals.forEach((v, i) => { if (v == null) { on = false; return; } d += `${on ? 'L' : 'M'}${(i + .5) * step},${y(v)}`; on = true; });
    marks = `<path class="l" d="${d}"/>`;
  }
  const hits = series.map((d, i) => `<rect class="hit" x="${i * step}" y="0" width="${step}" height="${Hh}"
      data-tip="${esc(`${new Date(d.day + 'T12:00:00Z').toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' })} · ${d[key] == null ? 'no data' : `${fmtv(d[key])} ${label.toLowerCase()}`}`)}" data-x="${((i + .5) / n * 100).toFixed(2)}"/>`).join('');
  const ticks = [0, Math.floor((n - 1) / 2), n - 1].map(i => `<span style="left:${((i + .5) / n * 100).toFixed(2)}%">${new Date(series[i].day + 'T12:00:00Z').toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' })}</span>`).join('');
  return `<div class="chart"><div class="yax"><span>${fmtv(Math.round(hi))}</span><span>${fmtv(Math.round(lo))}</span></div>
    <div class="plot"><svg viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="none" role="img" aria-label="${esc(label)} per day">${grid}${marks}${hits}</svg>
      <i class="cx"></i><div class="ctip" role="status"></div><div class="xax">${ticks}</div></div></div>`;
}

// One figure's parts per platform; "–" where that platform does not report it.
const ksplit = parts => `<span class="ksplit">${parts.map(([pl, v]) =>
  `<span title="${PLATFORM[pl]}${v == null ? ': not reported' : ''}">${icon(pl, 11)}${v == null ? '–' : num(v)}</span>`).join('')}</span>`;

function analyticsView() {
  const st = S.stats, days = S.statsDays || 30, plat = S.statsPlat || 'all';
  const plats = ORDER.filter(pl => brandAccounts().some(a => platformOf(a) === pl));
  const filters = `<div class="afilters">
    <div class="pchips" role="group" aria-label="Platform">${[['all', 'All platforms'], ...plats.map(pl => [pl, PLATFORM[pl]])].map(([k, l]) =>
      `<button class="pchip ${plat === k ? 'on' : ''}" data-aplat="${k}" aria-pressed="${plat === k}">${k === 'all' ? '' : appIcon(k, 18)}${l}</button>`).join('')}</div>
    <div class="seg" role="group" aria-label="Period">${[7, 30, 90].map(d => `<button data-days="${d}" class="${d === days ? 'on' : ''}" aria-pressed="${d === days}">${d} days</button>`).join('')}</div></div>`;
  if (!st) return `${filters}${skKpis(5)}<section class="panel atrend"><div class="chart">${sk('100%', 160)}</div></section><div class="an2"><section class="panel aposts"><header><h2>Posts</h2></header><div class="oscroll">${skRows(6)}</div></section><div class="aside"><section class="panel ocard"><header><h2>Followers</h2></header><div class="oscroll">${skRows(3)}</div></section></div></div>`;
  if (st.err) return `${filters}<div class="panel empty"><b>Couldn't load the numbers.</b>${esc(st.err)}</div>`;

  const T = st.totals, F = st.followers;
  const P = st.previous?.totals || {};
  const delta = (v, pv) => { if (v == null) return ['not shared yet', '']; if (!pv) return [st.tracked ? `${num(Math.round(v / st.tracked))} per post` : `no posts in the previous ${days} days`, ''];
    const pct = Math.round((v - pv) / pv * 100); return [`${pct > 0 ? '↑' : pct < 0 ? '↓' : '='} ${Math.abs(pct)}%<span class="vs"> vs previous ${days} days</span>`, pct > 0 ? 'up' : pct < 0 ? 'down' : '']; };
  const kpis = [['Views', T.views], ['Likes', T.likes], ['Comments', T.comments], ['Shares', T.shares]]
    .map(([l, v]) => [l, v == null ? '–' : num(v), ...delta(v, P[l.toLowerCase()])])
    .map(k => [...k, plat === 'all' && st.by_platform.length > 1 ? ksplit(st.by_platform.map(x => [x.platform, x[k[0].toLowerCase()]])) : '']);
  const rate = t => t.views ? engOf(t) / t.views * 100 : null;
  const er = rate(T), per = rate(P);
  kpis.push(['Engagement rate', er == null ? '–' : `${er.toFixed(1)}%`,
    er == null ? 'needs views' : per == null ? 'likes, comments, shares per view' : `${er >= per ? '↑' : '↓'} ${Math.abs(er - per).toFixed(1)} pts<span class="vs"> vs previous ${days} days</span>`,
    er == null || per == null || er === per ? '' : er > per ? 'up' : 'down']);

  // Which weekdays and times of day get the most views per post.
  const scored = (st.posts || []).filter(p => p.stats);
  const useViews = scored.some(p => p.stats.views != null);
  const val = p => useViews ? p.stats.views || 0 : engOf(p.stats);
  const avgBy = (keys, keyOf) => { const m = new Map(keys.map(k => [k, []])); for (const p of scored) m.get(keyOf(p))?.push(val(p));
    return keys.map(k => [k, m.get(k).length ? m.get(k).reduce((a, b) => a + b, 0) / m.get(k).length : null, m.get(k).length]); };
  const WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const byDay = avgBy(WD, p => new Intl.DateTimeFormat('en-US', { timeZone: tz(), weekday: 'short' }).format(new Date(p.scheduled_at * 1000)));
  const hourOf = p => Number(new Intl.DateTimeFormat('en-GB', { timeZone: tz(), hour: '2-digit', hourCycle: 'h23' }).format(new Date(p.scheduled_at * 1000)));
  const TOD = [['Morning', '5–12'], ['Afternoon', '12–17'], ['Evening', '17–22'], ['Night', '22–5']];
  const byTod = avgBy(TOD.map(t => t[0]), p => { const h = hourOf(p); return h >= 5 && h < 12 ? 'Morning' : h >= 12 && h < 17 ? 'Afternoon' : h >= 17 && h < 22 ? 'Evening' : 'Night'; });
  const bars = (rows, sub = () => '') => { const hi = Math.max(0, ...rows.map(r => r[1] || 0)) || 1, best = rows.reduce((b, r) => r[1] != null && (b == null || r[1] > b[1]) ? r : b, null);
    return rows.map(r => `<div class="brow ${best && r[0] === best[0] ? 'best' : ''}"><span>${r[0]}${sub(r)}</span><i><em style="width:${r[1] == null ? 0 : Math.max(2, r[1] / hi * 100).toFixed(1)}%"></em></i><b>${r[1] == null ? '–' : num(Math.round(r[1]))}</b></div>`).join(''); };
  const bestDay = byDay.reduce((b, r) => r[1] != null && (!b || r[1] > b[1]) ? r : b, null), bestTod = byTod.reduce((b, r) => r[1] != null && (!b || r[1] > b[1]) ? r : b, null);
  const when = scored.length < 3 ? '<div class="cempty2">Shows once a few posts have numbers.</div>'
    : `<p class="wbest">Best: <b>${bestDay[0]}</b>, <b>${bestTod[0].toLowerCase()}</b></p>
      <div class="bars">${bars(byDay)}</div><div class="bars">${bars(byTod, r => ` <small>${TOD.find(t => t[0] === r[0])[1]}</small>`)}</div>`;

  const TRENDS = [['views', 'Views'], ['engagement', 'Engagement'], ['posts', 'Posts']];
  const trend = S.statsTrend || 'views';

  const row = p => `<div class="rpost" data-open="${p.id}" role="button" tabindex="0">${thumb(p, 'class="thumb" alt=""') || '<span class="noimg"></span>'}
      <div class="wh"><b>${icon(p.platform || 'tiktok', 14)}${who(p)}</b><span>${fmt(p.scheduled_at, { month: 'short', day: 'numeric', year: 'numeric' })}</span></div>
      <span class="scols">${['views', 'likes', 'comments', 'shares'].map(k => `<span>${p.stats?.[k] == null ? '–' : num(p.stats[k])}</span>`).join('')}</span></div>`;
  const sort = S.statsSort || 'new';
  const SORTS = [['new', 'Newest'], ['views', 'Most views'], ['eng', 'Engagement']];
  const posts = [...(st.posts || st.top || [])].sort(sort === 'new' ? (a, b) => b.scheduled_at - a.scheduled_at
    : sort === 'views' ? (a, b) => (b.stats?.views ?? -1) - (a.stats?.views ?? -1) || b.scheduled_at - a.scheduled_at
    : (a, b) => (b.stats ? engOf(b.stats) : -1) - (a.stats ? engOf(a.stats) : -1) || b.scheduled_at - a.scheduled_at);
  const acc = a => `<div class="arow">${icon(a.platform, 14)}<b>${who(a)}</b>
      <span class="fv">${a.limited && a.platform === 'tiktok' ? `<a class="rc" href="/api/auth/start?add=1">Reconnect</a>` : a.followers == null ? '<em>Reading…</em>' : num(a.followers)}</span>
      <span class="fc ${a.change > 0 ? 'up' : a.change < 0 ? 'down' : ''}">${a.change == null || a.change === 0 ? '' : signed(a.change)}</span></div>`;
  const notes = [
    st.tiktok_reconnect && `TikTok accounts connected before stats were added need one reconnect.${can('admin') ? ' <a href="/api/auth/start?add=1">Reconnect TikTok</a>' : ''}`,
    st.facebook_limited && (plat === 'all' || plat === 'facebook') && `Facebook Pages connected before post numbers were added need one reconnect.${can('admin') ? ' <a href="/api/auth/meta/start?add=1">Reconnect Facebook</a>' : ''}`,
  ].filter(Boolean);

  const fch = F.change == null ? '' : `<small class="${F.change > 0 ? 'up' : F.change < 0 ? 'down' : ''}">${signed(F.change)} in ${days} days</small>`;
  return `${filters}
    <div class="kpis five">${kpis.map(([l, v, n, c, parts = '']) => `<div class="kpi"><span>${l}</span><b>${v}</b><small class="${c}">${n}</small>${parts}</div>`).join('')}</div>
    <section class="panel atrend"><header><h2>Trend</h2><span class="note">by publish day</span>
        <div class="seg" role="group" aria-label="Chart">${TRENDS.map(([k, l]) => `<button data-atrend="${k}" class="${k === trend ? 'on' : ''}" aria-pressed="${k === trend}">${l}</button>`).join('')}</div></header>
      ${chart(st.series, trend, { label: TRENDS.find(t => t[0] === trend)[1] })}</section>
    <div class="an2">
      <section class="panel aposts"><header><h2>Posts</h2><span class="note">${st.published} published</span>
        <div class="seg" role="group" aria-label="Sort posts">${SORTS.map(([k, l]) => `<button data-asort="${k}" class="${k === sort ? 'on' : ''}" aria-pressed="${k === sort}">${l}</button>`).join('')}</div></header>
        ${posts.length ? `<div class="phead"><span>Post</span><span class="scols">${['views', 'likes', 'comments', 'shares'].map(k => `<span title="${METRIC[k]}">${ui(STAT_ICON[k], 13)}</span>`).join('')}</span></div>
          <div class="list">${posts.map(row).join('')}</div>` : `<div class="cempty2">No posts published in the last ${days} days.</div>`}
        ${posts.length && !st.tracked ? '<p class="note pnote">Numbers show a few hours after a post goes out.</p>' : ''}</section>
      <div class="aside">
        <section class="panel ocard"><header><h2>Followers</h2><span class="note">${st.updated_at ? `updated ${ago(st.updated_at)}` : ''}</span></header>
          <div class="ftot"><b>${F.total == null ? '–' : num(F.total)}</b>${fch}</div>
          <div class="fspark">${chart(st.series, 'followers', { kind: 'line', label: 'Followers' })}</div>
          <div class="alist">${st.accounts.map(acc).join('') || '<div class="cempty2">Connect an account to see followers.</div>'}</div></section>
        <section class="panel ocard"><header><h2>When posts do best</h2><span class="note">${useViews ? 'avg views' : 'avg interactions'} per post</span></header>${when}</section>
      </div>
    </div>
    ${notes.length ? `<div class="snotes">${notes.map(n => `<p>${n}</p>`).join('')}</div>` : ''}
    ${S.detail ? detailView() : ''}`;
}

// Until the workspace has an account, the overview is a short path to the
// first scheduled post.
function firstRun() {
  const admin = can('admin');
  const steps = [
    [S.me.accounts.length > 0, 'Connect an account', 'You sign in on the platform\'s own screen. We never see your password.',
      admin ? `<div class="frc">${ORDER.filter(connectHref).map(pl => `<a class="frbtn" href="${connectHref(pl)}">${appIcon(pl, 22)}${PLATFORM[pl]}</a>`).join('')}</div>`
        : '<p class="note">Ask a workspace admin to connect an account or give you a brand.</p>'],
    [false, 'Create your first post', 'Add photos, write a caption, and see how it looks on each platform before it goes out.', ''],
    [!!S.me.workspace.slots, 'Set your posting times', 'Pick the days and times you like to post. "Add to queue" then fills them for you.', ''],
  ];
  return `<div class="welcome"><h1>Welcome to ARCO Publisher</h1><p>Three steps to your first scheduled post.</p></div>
    <section class="panel"><ol class="frsteps">${steps.map(([done, t, d, extra], i) => `<li class="${done ? 'done' : ''} ${i === 0 && !done ? 'cur' : ''}">
      <span class="num">${done ? ui('check', 14) : i + 1}</span><div><b>${t}</b><span>${d}</span>${!done ? extra : ''}</div></li>`).join('')}</ol></section>`;
}

// ---- sign in: email, then the 6-digit code it receives ---------------------

function signInView() {
  const L = S.login, claiming = S.me?.needs_email;
  let invited = false;
  try { invited = !!sessionStorage.getItem(INVITE); } catch {}
  return `<div class="signwrap"><div class="signside">
    <a class="brand-row" href="/"><img class="logo" src="/apple-touch-icon.png" alt="" width="30" height="30"><b>ARCO Publisher</b></a>
    <div class="card signin"><div class="sec">
    <h1>${claiming ? 'Add your email' : 'Sign in or create an account'}</h1>
    <p class="lead">${claiming
      ? 'ARCO Publisher now signs in with email. Add yours to keep this workspace, its accounts and its posts. From then on you sign in with it, and you can invite teammates.'
      : invited ? 'Sign in with the email the invite was sent to, and you will join the workspace.'
      : 'Schedule photo posts to TikTok, Instagram and Facebook Pages, one account or many. No password: we email you a code.'}</p>
    ${L.step === 'email' ? `<form id="loginemail" class="loginform">
        <label class="f" for="le">Email</label>
        <input type="email" id="le" autocomplete="email" required value="${esc(L.email)}" placeholder="you@company.com">
        <button class="btn" ${L.busy ? 'disabled' : ''}>${L.busy ? 'Sending…' : 'Email me a code'}</button>
      </form>`
    : `<form id="logincode" class="loginform">
        <label class="f" for="lc">Enter the 6-digit code we sent to <b>${esc(L.email)}</b></label>
        <input type="text" id="lc" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required value="${esc(L.code)}">
        <button class="btn" ${L.busy ? 'disabled' : ''}>${L.busy ? 'Checking…' : claiming ? 'Add email' : 'Sign in'}</button>
        <p class="note"><button type="button" class="link" id="loginback">Use a different email</button> ·
          <button type="button" class="link" id="loginresend">Send a new code</button></p>
      </form>`}
    ${L.err ? `<div class="status err">${esc(L.err)}</div>` : ''}
    ${claiming ? '' : `<p class="note" style="margin-top:18px">Signed up with TikTok before email sign-in existed?
      <a href="/api/auth/start">Continue with TikTok</a> once, then add your email.</p>`}
    <p class="note">By continuing you agree to the <a href="/terms.html">terms</a> and <a href="/privacy.html">privacy policy</a>.</p>
  </div></div></div>
  <div class="signart" aria-hidden="true"><div class="mini"><h3>Today</h3>
    ${[['07:30', 'facebook', 'Your Page', 'published', 'Published'], ['now'], ['09:00', 'instagram', '@yourbrand', 'next', 'Next up'], ['18:00', 'tiktok', '@yourbrand', 'queued', 'Scheduled']].map(r => r[0] === 'now'
      ? '<div class="nowline"><time>Now</time><div class="bar"></div></div>'
      : `<div class="slot ${r[3]}"><time>${r[0]}</time><div class="dot"><i></i></div><div class="rpost"><span class="noimg"></span><div class="wh"><b>${icon(r[1], 14)}${r[2]}</b><span>Photo post</span></div><span class="st ${r[3]}">${r[4]}</span></div></div>`).join('')}
  </div></div></div>`;
}

async function sendCode() {
  const L = S.login;
  L.busy = true; L.err = ''; render();
  try { await send('/auth/email/start', 'POST', { email: L.email }); L.step = 'code'; L.code = ''; }
  catch (e) { L.err = e.message; }
  L.busy = false; render();
  $('lc')?.focus();
}

async function verifyCode() {
  const L = S.login;
  L.busy = true; L.err = ''; render();
  try {
    const r = await fetch('/api/auth/email/verify', { method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: L.email, code: L.code }) });
    const b = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(b.error || 'Sign-in failed');
    S.login = { step: 'email', email: '', code: '', busy: false, err: '' };
    await loadMe(); route(); return;
  } catch (e) { L.err = e.message; }
  L.busy = false; render();
}

// The workspace you are in, and a switch when you belong to several.
function wsBar() {
  const w = S.me.workspace, list = S.me.workspaces || [];
  const label = w.role === 'owner' ? 'Owner' : w.role === 'admin' ? 'Admin' : w.brand_scope ? 'Member · some brands' : 'Member';
  return `${list.length > 1 ? `<select id="wsswitch" aria-label="Workspace">
      ${list.map(x => `<option value="${x.id}" ${x.id === w.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>`
    : `<b>${esc(w.name)}</b>`}<span class="note">${label}${S.me.user ? ` · ${esc(S.me.user.email)}` : ''}</span>`;
}

function composeView() {
  if (!S.me.accounts.length) return `<div class="panel empty"><b>No accounts yet.</b>${can('admin')
    ? 'Connect TikTok, Instagram or a Facebook Page first.<div><a class="btn" href="#accounts">Connect account</a></div>'
    : 'No accounts are shared with you yet. Ask a workspace admin to give you access to a brand.'}</div>`;
  const tts = ttTargets();
  const label = S.set.branded ? 'Paid partnership' : S.set.brand ? 'Promotional content' : '';
  const need = missing();
  const pls = chosenPlatforms();
  const banner = S.fromDraft ? ['Editing a draft. Scheduling or posting it replaces the draft.', 'Close draft']
    : S.replaces ? ['Editing a scheduled post. The original stays scheduled until you save this one.', 'Stop editing'] : null;
  const when = [['now', 'Post now'], ['queue', 'Add to queue'], ['later', 'Schedule']];
  return `${banner ? `<div class="cbanner">${banner[0]}<button class="btn sec" id="stopedit">${banner[1]}</button></div>` : ''}
  <div class="composer ${S.busy ? 'busy' : ''}" ${S.busy ? 'aria-busy="true"' : ''}>
    <div class="cmain">
      ${brandPickSection()}
      <section class="panel"><header><h2>Post to</h2>${S.targets.length ? `<span class="note">${S.targets.length} selected</span>` : ''}</header>
        <div class="csec">${accountPicker()}</div></section>

      <section class="panel"><header><h2>${S.video ? 'Video' : S.images.length ? 'Photos' : 'Media'}</h2>${S.images.length ? `<span class="note">${S.images.length} of ${toInstagram() ? IG_MAX : 35}</span>` : ''}</header>
        <div class="csec">${mediaView()}</div></section>

      <section class="panel"><header><h2>Caption</h2>${S.me.ai_enabled && !S.ai.open ? aiPanel() : ''}</header>
        <div class="csec">
          ${tts.length && !S.video ? `<label class="f" for="title">TikTok title</label>
            <input type="text" id="title" maxlength="200" value="${esc(S.title)}" placeholder="A short title for the photo post">
            <div class="count ${len(S.title) > 90 ? 'bad' : ''}">${len(S.title)} / 90</div>` : ''}
          ${S.me.ai_enabled && S.ai.open ? aiPanel() : ''}
          ${folderHint()}${captionTabs(pls)}
          <div class="limits" id="caplimits">${limitsLine()}</div>
          ${S.me.ai_enabled && S.caption.trim() ? `<div class="rewrites"><span class="note">Rewrite</span>${Object.entries(REWRITE_LABEL)
            .map(([k, l]) => `<button type="button" class="chip" data-rewrite="${k}" ${S.ai.busy ? 'disabled' : ''}>${l}</button>`).join('')}</div>` : ''}
        </div></section>

      ${tts.length ? `<section class="panel"><header><h2>${icon('tiktok', 15)} TikTok settings</h2><span class="note">${tts.length} account${tts.length === 1 ? '' : 's'}</span></header>
        <div class="csec">
          ${tts.length > 1 ? `<div class="bulk"><label class="f" for="bulkpriv">Set who can view for every TikTok account</label>
            <select id="bulkpriv"><option value="">Choose…</option>
              ${Object.keys(PRIVACY_LABEL).filter(o => !(o === 'SELF_ONLY' && S.set.branded)).map(o => `<option value="${o}">${PRIVACY_LABEL[o]}</option>`).join('')}
            </select><span class="note">Accounts that do not offer that option keep their own choice.</span></div>` : ''}
          ${tts.map(ttCard).join('')}
          ${S.video ? row('Allow Duet', '', `<input type="checkbox" data-k="duet" ${S.set.duet ? 'checked' : ''}>`)
            : row('Duet', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
          ${S.video ? row('Allow Stitch', '', `<input type="checkbox" data-k="stitch" ${S.set.stitch ? 'checked' : ''}>`)
            : row('Stitch', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
          ${S.video ? '' : row('Add recommended music', 'Lets TikTok pick a track for the slideshow.', `<input type="checkbox" data-k="music" ${S.set.music ? 'checked' : ''}>`)}
          ${row('Disclose post content', 'Turn on if this post promotes yourself, a brand, product or service.',
            `<input type="checkbox" data-k="disclose" ${S.set.disclose ? 'checked' : ''}>`)}
          ${S.set.disclose ? `<div class="disc">
            <label><input type="checkbox" data-k="brand" ${S.set.brand ? 'checked' : ''}> Your brand</label>
            <label><input type="checkbox" data-k="branded" ${S.set.branded ? 'checked' : ''}> Branded content</label>
            <p class="note ${label ? 'warn' : ''}">${label ? `Your ${S.video ? 'video' : 'photo post'} will be labeled "${label}".` : 'You need to indicate if your content promotes yourself, a third party, or both.'}</p>
          </div>` : ''}
          <p class="consent">By posting, you agree to TikTok's
            ${S.set.branded ? '<a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank" rel="noopener">Branded Content Policy</a> and ' : ''}
            <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en" target="_blank" rel="noopener">Music Usage Confirmation</a>.</p>
        </div></section>` : ''}
    </div>

    <aside class="cside"><section class="panel"><header><h2>Preview</h2>${S.targets.length ? `<span class="note">${S.targets.length} account${S.targets.length === 1 ? '' : 's'}</span>` : ''}</header>
      ${S.targets.length ? `<div class="goes">${S.targets.map(acct).filter(Boolean).map(a => `<span class="goesto" title="${esc(PLATFORM[platformOf(a)])}">${withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))}<span>${handle(a)}</span></span>`).join('')}</div>` : ''}
      ${pls.length > 1 ? `<div class="ptabs">${pls.map(pl => `<button data-prev="${pl}" class="${previewPl(pls) === pl ? 'on' : ''}">${icon(pl, 13)}${PLATFORM[pl]}</button>`).join('')}</div>` : ''}
      <div id="preview">${previewView()}</div></section></aside>
  </div>

  <div class="cbar">
    <div class="when" role="radiogroup" aria-label="When">${when.map(([v, l]) =>
      `<label class="${S.when === v ? 'on' : ''}"><input type="radio" name="when" value="${v}" ${S.when === v ? 'checked' : ''}>${l}</label>`).join('')}</div>
    ${S.when === 'later' ? `<input type="datetime-local" id="at" value="${esc(S.at)}" min="${localInput(Date.now() + 6 * 60e3)}" aria-label="Date and time">
      <span class="note">${esc(tz().replace(/_/g, ' '))}</span>` : ''}
    ${S.when === 'queue' ? `<span class="qline">${queuePreview()}</span>` : ''}
    <span class="grow"></span>
    ${need ? `<span class="need">${esc(need)}</span>` : S.status ? `<span class="need ${S.status.kind}">${esc(S.status.text)}</span>` : ''}
    <button class="btn sec" id="savedraft" ${draftBlocker() || S.busy ? 'disabled' : ''} title="${esc(draftBlocker())}">Save draft</button>
    ${S.targets.length ? `<span class="stack bar" aria-hidden="true">${S.targets.slice(0, 4).map(acct).filter(Boolean).map(a => withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))).join('')}${S.targets.length > 4 ? `<span class="more">+${S.targets.length - 4}</span>` : ''}</span>` : ''}
    <button class="btn" id="go" ${need || S.busy ? 'disabled' : ''} title="${esc(need || '')}">
      ${S.busy ? 'Working…' : `${S.when === 'later' ? 'Schedule' : S.when === 'queue' ? 'Add to queue' : 'Post now'}${S.targets.length > 1 ? ` · ${S.targets.length}` : ''}`}</button>
  </div>`;
}

// The brand comes first: picking one picks all of its accounts.
function brandPickSection() {
  if (!S.me.brands.length) return can('admin') ? `<div class="bhint">${ui('users', 16)}<span>Group accounts into brands on the <a href="#accounts">Brands &amp; accounts</a> page, then pick a brand here to post to all of its accounts at once.</span></div>` : '';
  const b = curBrand();
  return `<section class="panel"><header><h2>Brand</h2><span class="note">${b === 'all' ? 'Pick one to choose its accounts' : `${brandAccounts(b).length} account${brandAccounts(b).length === 1 ? '' : 's'}`}</span></header>
    <div class="csec"><div class="bpick" role="radiogroup" aria-label="Brand">${brandOpts().filter(([k]) => k !== 'all').map(([k, l, n]) =>
      `<button type="button" role="radio" aria-checked="${b === k}" class="${b === k ? 'on' : ''}" data-brand="${k}">
        <span class="bsq" style="background:${k === 'none' ? 'var(--soft)' : brandHue(k)}">${esc((l[0] || '?').toUpperCase())}</span>
        <span class="nm"><b>${esc(l)}</b><span>${marks(brandAccounts(k))} ${n} account${n === 1 ? '' : 's'}</span></span></button>`).join('')}
      ${b !== 'all' ? '<button type="button" class="link" data-brand="all">Pick accounts from any brand</button>' : ''}</div></div></section>`;
}

// "Post to" is a dropdown: the closed button shows who is chosen; the list
// opens grouped by brand with a search box, like Business Suite's switcher.
function accountPicker() {
  const chosen = S.targets.map(acct).filter(Boolean);
  const stack = chosen.slice(0, 5).map(a => withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))).join('');
  const label = !chosen.length ? 'Choose accounts'
    : chosen.length === 1 ? who(chosen[0])
    : chosen.length === 2 ? `${who(chosen[0])}, ${who(chosen[1])}` : `${who(chosen[0])} and ${chosen.length - 1} more`;
  return `<div class="dd ${S.pickOpen ? 'open' : ''}">
    <button type="button" class="ddbtn" id="openpick" aria-haspopup="listbox" aria-expanded="${!!S.pickOpen}">
      ${chosen.length ? `<span class="stack">${stack}${chosen.length > 5 ? `<span class="more">+${chosen.length - 5}</span>` : ''}</span>` : `<span class="ddph">${ui('users', 18)}</span>`}
      <span class="ddl ${chosen.length ? '' : 'mute'}">${label}</span>${ui('chev', 16)}</button>
    ${S.pickOpen ? pickList() : ''}</div>`;
}

function pickList() {
  const q = S.pq.trim().toLowerCase();
  const hit = a => !q || [a.username, a.display_name, PLATFORM[platformOf(a)], brandName(a.brand_id)]
    .some(v => String(v || '').toLowerCase().includes(q));
  const b = curBrand(), mine = S.me.accounts.filter(a => inBrand(a, b) || S.targets.includes(a.id) || (S.pickAll && b !== 'all'));
  const groups = brandGroups(mine.filter(hit)).filter(g => g.accounts.length);
  const more = b !== 'all' && !S.pickAll && S.me.accounts.length > mine.length;
  return `<div class="ddpop" role="listbox" aria-multiselectable="true">
    ${S.me.accounts.length > 6 ? `<input type="text" id="pq" class="pq" placeholder="Search accounts or brands" value="${esc(S.pq)}" autocomplete="off">` : ''}
    <div class="ddlist">${groups.map(g => {
      const usable = g.accounts.filter(a => !a.needs_reconnect);
      const on = usable.filter(a => S.targets.includes(a.id)).length;
      const state = !on ? 'none' : on === usable.length ? 'all' : 'some';
      return `<div class="ddg"><label class="ddgh"><input type="checkbox" data-bg="${g.id}" data-state="${state}" ${state === 'all' ? 'checked' : ''} ${usable.length ? '' : 'disabled'}>
          <b>${esc(g.name)}</b><span>${on ? `${on} of ` : ''}${g.accounts.length}</span></label>
        ${g.accounts.map(a => `<label class="ddi ${a.needs_reconnect ? 'off' : ''}">
          <input type="checkbox" data-t="${a.id}" ${S.targets.includes(a.id) ? 'checked' : ''} ${a.needs_reconnect ? 'disabled' : ''}>
          ${withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))}
          <span class="nm"><b>${handle(a)}</b><span>${PLATFORM[platformOf(a)]}${a.needs_reconnect ? ' · reconnect needed' : ''}</span></span></label>`).join('')}</div>`;
    }).join('') || '<p class="note" style="padding:10px">No account matches.</p>'}</div>
    ${more ? `<button type="button" class="link ddmore" id="pickall">Show accounts from other brands</button>` : ''}
    <div class="ddfoot">${can('admin') ? '<a href="#accounts">Manage accounts</a>' : '<span></span>'}<button type="button" class="btn" id="closepick">Done</button></div></div>`;
}

// ---- library: photos uploaded ahead of time, filed by brand ---------------

async function loadLibrary() {
  try { [S.lib, S.folders] = await Promise.all([api('/library'), api('/folders').then(r => r.folders)]); }
  catch (e) { S.lib = S.lib || { items: [] }; S.folders = S.folders || []; S.flash = { kind: 'err', text: e.message }; }
  render();
}
const reloadLibrary = async () => { [S.lib, S.folders] = await Promise.all([api('/library'), api('/folders').then(r => r.folders)]); };

// ---- AI assistant: connect an assistant over MCP --------------------------
async function loadAi() {
  try { const [f, d] = await Promise.all([api('/folders'), api('/drafts')]); S.folders = f.folders; S.drafts = d.drafts; }
  catch (e) { S.folders = S.folders || []; S.drafts = S.drafts || []; }
  if (S.view === 'ai') render();
}
const mcpUrl = () => `${location.origin}/mcp`;
const copyBtn = (text, label = 'Copy') => `<button type="button" class="btn sec sm" data-copy="${esc(text)}">${label}</button>`;
// Shown with the key masked; Copy takes the real thing.
const codeBlock = (text, shown = text) => `<div class="cblock"><pre><code>${esc(shown)}</code></pre>${copyBtn(text)}</div>`;
const maskKey = k => (k ? `${k.slice(0, 8)}••••••••${k.slice(-4)}` : k);
// The apps that can connect, as small app tiles.
const APP_TILE = {
  code: ['#1b1b1b', '<path d="M7 9l3 3-3 3" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M12.5 15.5h4.5" stroke="#D97757" stroke-width="2" stroke-linecap="round"/>'],
  desktop: ['#D97757', '<g stroke="#fff" stroke-width="2.1" stroke-linecap="round"><path d="M12 5v14M5 12h14M7.1 7.1l9.8 9.8M16.9 7.1l-9.8 9.8"/></g>'],
  cursor: ['#0f0f0f', '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"><path d="M12 4l7 4v8l-7 4-7-4V8z"/><path d="M5 8l7 4 7-4M12 12v8"/></g>'],
  other: ['#3b4252', '<g fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round"><path d="M9 4v4M15 4v4M7 8h10v3a5 5 0 0 1-10 0zM12 16v4"/></g>'],
};
const appTile = (id, s = 36) => `<svg class="apptile" width="${s}" height="${s}" viewBox="0 0 24 24" aria-hidden="true"><rect width="24" height="24" rx="6" fill="${APP_TILE[id][0]}"/>${APP_TILE[id][1]}</svg>`;
const CLIENTS = [['desktop', 'Claude app & claude.ai'], ['code', 'Claude Code'], ['cursor', 'Cursor'], ['other', 'VS Code & others']];
// What a key-holding Copy button puts on the clipboard: the connector link, or a config around it.
const linkText = (kind, key) => { const link = `${mcpUrl()}/${key}`;
  return kind === 'link' ? link : JSON.stringify({ mcpServers: { 'arco-publisher': { url: link } } }, null, 2); };

// What to copy for each app, and the one line that says where it goes.
// Step by step for each app, written for someone who has never opened a
// terminal or a config file. Mac and Windows differ in keys and menus.
const isWin = () => /Windows/.test(navigator.userAgent);
function clientSetup(key) {
  const url = mcpUrl(), c = CLIENTS.some(x => x[0] === S.aiClient) ? S.aiClient : 'desktop';
  const os = S.aiOS || (isWin() ? 'win' : 'mac'), mac = os === 'mac';
  const kb = (m, w) => `<kbd>${mac ? m : w}</kbd>`;
  const canCopy = !!key || (S.me.api_key_set && S.me.api_key_copyable);
  const keyCopy = (kind, label) => canCopy ? `<button type="button" class="btn sm" data-keycopy="${kind}">${ui('copy', 14)}${label}</button>`
    : `<span class="note warn">${S.me.api_key_set ? 'Make a new key in step 1 first, so it can be copied.' : 'Create your key in step 1 first.'}</span>`;
  const cmd = mac
    ? `printf 'Paste your Publisher API key: '; read -rs ARCO_KEY; echo; claude mcp add --scope user --transport http arco-publisher ${url} --header "Authorization: Bearer $ARCO_KEY"; unset ARCO_KEY`
    : `$k = Read-Host 'Paste your Publisher API key' -AsSecureString; $p = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k)); claude mcp add --scope user --transport http arco-publisher ${url} --header "Authorization: Bearer $p"; Remove-Variable k, p`;
  const copy = (text, label) => copyBtn(text, `${ui('copy', 14)}${label}`).replace('btn sec sm', 'btn sm');
  const shell = mac ? '<b>Terminal</b>' : '<b>PowerShell</b>';
  const steps = {
    desktop: [
      `Copy your connector link: ${keyCopy('link', 'Copy link')}`,
      `In Claude, open <b>Settings</b> → <b>Connectors</b>. ${mac ? 'In the app: the <b>Claude</b> menu at the top.' : 'In the app: the <b>☰</b> menu → <b>File</b> → <b>Settings</b>.'} On claude.ai: click your name at the bottom left.`,
      `Click <b>Add custom connector</b>. Name it <b>ARCO Publisher</b>, paste the link with ${kb('⌘ V', 'Ctrl V')} and click <b>Add</b>.`,
      `Start a new chat and ask. If it doesn't reply with your posts, open the <b>+</b> menu in the chat box and switch <b>ARCO Publisher</b> on.`,
    ],
    code: [
      `Install Claude Code if you don't have it: follow <a href="https://code.claude.com/docs/en/setup" target="_blank" rel="noopener">Anthropic's install guide</a>.`,
      mac ? `Open ${shell}: press ${kb('⌘ Space')}, type <b>Terminal</b>, press ${kb('Return')}.` : `Open ${shell}: press the ${kb('', 'Windows')} key, type <b>PowerShell</b>, press ${kb('', 'Enter')}.`,
      `Copy the setup command: ${copy(cmd, 'Copy command')} then paste it in with ${kb('⌘ V', 'Ctrl V')} and press ${kb('Return', 'Enter')}.`,
      `It asks for your key: copy it in step 1, paste and press ${kb('Return', 'Enter')}. Nothing shows while you paste; that is on purpose.`,
      `Type <code>claude</code> and press ${kb('Return', 'Enter')}, then ask.`,
    ],
    cursor: [
      `Open Cursor, then ${mac ? '<b>Cursor</b> menu → <b>Settings</b> → <b>Cursor Settings</b>' : '<b>File</b> → <b>Preferences</b> → <b>Cursor Settings</b>'} → <b>MCP</b> → <b>Add new MCP server</b>.`,
      `Copy the settings: ${keyCopy('config', 'Copy settings')}`,
      `In the file that opens, select all with ${kb('⌘ A', 'Ctrl A')}, paste with ${kb('⌘ V', 'Ctrl V')}, save with ${kb('⌘ S', 'Ctrl S')}. A green dot means it's connected.`,
    ],
    other: [
      `Open your app's MCP settings. VS Code: ${kb('⌘ ⇧ P', 'Ctrl Shift P')}, then <b>MCP: Add Server</b> → <b>HTTP</b>.`,
      `Copy your connector link: ${keyCopy('link', 'Copy link')} and paste it as the server address.`,
      `Name it <b>arco-publisher</b>, save, and ask in the app's chat.`,
    ],
  }[c];
  return `<div class="mapps" role="tablist">${CLIENTS.map(([id, l]) => `<button role="tab" class="mapp ${c === id ? 'on' : ''}" data-aiclient="${id}" aria-selected="${c === id}">${appTile(id, 30)}<span>${l}</span></button>`).join('')}</div>
    <div class="howto"><div class="howhead"><b>${CLIENTS.find(x => x[0] === c)[1]} on</b>
        <div class="seg" role="group" aria-label="Computer">${[['mac', 'Mac'], ['win', 'Windows']].map(([o, l]) => `<button data-aios="${o}" class="${o === os ? 'on' : ''}" aria-pressed="${o === os}">${l}</button>`).join('')}</div></div>
      <ol class="hsteps">${steps.map(t => `<li>${t}</li>`).join('')}</ol>
      ${c === 'code' ? '' : '<p class="note">The link holds your key, so keep it private. Making a new key or deleting it in step 1 switches the link off.</p>'}</div>`;
}

async function newApiKey() {
  if (S.me.api_key_set && !await ask({ title: 'Make a new API key?', ok: 'Make a new key', danger: true, icon: ui('spark', 22),
    list: [[false, 'The current key stops working at once'], [false, 'Any AI app using it needs the new key']] })) return;
  try { S.apiKey = (await api('/api-key', { method: 'POST' })).api_key;
    Object.assign(S.me, { api_key_set: true, api_key_hint: S.apiKey.slice(-4), api_key_copyable: true, api_key_at: Math.floor(Date.now() / 1000), api_key_name: S.me.api_key_name || 'Main key' }); }
  catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}
async function deleteApiKey() {
  if (!await ask({ title: 'Delete the API key?', ok: 'Delete key', danger: true, icon: ui('spark', 22),
    list: [[false, 'Any AI app using it stops working at once'], [true, 'Posts already scheduled still go out'], [true, 'You can create a new key any time']] })) return;
  try { await api('/api-key', { method: 'DELETE' }); Object.assign(S.me, { api_key_set: false, api_key_hint: null, api_key_name: null, api_key_at: null, api_key_copyable: false }); S.apiKey = null; }
  catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}

function aiView() {
  const owner = can('owner'), admin = can('admin'), keySet = !!S.me.api_key_set, key = S.apiKey;
  const unused = (S.folders || []).filter(f => f.status === 'unused' && f.items.length).length;
  const waiting = (S.drafts || []).filter(d => d.source === 'ai').length;
  const review = S.me.ai_review !== false;
  const prompts = [
    ['cal', 'Schedule', 'Schedule my newest library post on Sunday at 10 am to my TikTok account.'],
    ['cal', 'Plan', 'Plan next week from my library: one post a day at 6 pm on Instagram. Show me the plan first.'],
    ['edit', 'Write', 'Write a short, friendly caption for each of those posts, with three hashtags.'],
    ['chart', 'Learn', 'Which of my posts did best this month, and why?'],
    ['warn', 'Fix', 'A post failed yesterday. Find out why and post it again.'],
    ['x', 'Undo', 'Cancel everything you scheduled for Sunday.'],
  ];
  const numbered = (n, title, sub, body, aside = '') => `<section class="panel mnum"><header><span class="stepn">${n}</span><div><h2>${title}</h2><span class="note">${sub}</span></div>${aside}</header>${body}</section>`;
  return `<section class="panel mhero">
      <div class="mintro"><span class="eyebrow">MCP</span>
        <h2>Schedule posts by asking your AI</h2>
        <p>Connect Claude or Cursor to ARCO Publisher. Ask in plain words, and it plans captions and times from your library, then schedules them once you say go.</p>
        <ul class="mperks"><li>${ui('edit', 15)}Writes captions from your photos, notes and brand voice</li><li>${ui('cal', 15)}Fills your free posting times</li><li>${ui('check', 15)}You see the plan before anything is scheduled</li></ul>
        <div class="mappr"><div><b>Approve AI posts first</b><span class="note">${review ? 'Posts your AI schedules wait in Drafts for you' : 'Posts your AI schedules go straight onto the calendar'}${waiting ? ` · <a href="#drafts">${waiting} waiting</a>` : ''}</span></div>
          ${admin ? `<label class="sw"><input type="checkbox" id="aireview" ${review ? 'checked' : ''} aria-label="Approve AI posts first"><span></span></label>` : ''}</div></div>
      <div class="mchat" aria-label="Example conversation">
        <div class="bub me">Schedule my new videos for next week.</div>
        <div class="bub ai"><b>5 posts</b>, Mon to Fri at 6 pm on TikTok and Instagram. Captions are drafted from each video's note. Go?</div>
        <div class="bub me">Go</div>
        <div class="bub ai">${ui('check', 13)} Scheduled. ${review ? 'They wait in Drafts for your approval.' : 'They are on the calendar.'}</div></div>
    </section>
    ${numbered(1, 'Create your API key', 'Your AI signs in with it. Treat it like a password.', `<div class="kbody">
      ${keySet ? `<div class="ktable" role="table" aria-label="API key">
          <div class="khead" role="row"><span>Name</span><span>Key</span><span>Created</span><span></span></div>
          <div class="kline ${key ? 'fresh' : ''}" role="row">
            <span class="kname">${ui('spark', 14)}<b>${esc(S.me.api_key_name || 'Main key')}</b></span>
            <code>apk_••••••••••••${esc(S.me.api_key_hint || '')}</code>
            <span class="note">${S.me.api_key_at ? fmt(S.me.api_key_at, { day: 'numeric', month: 'short', year: 'numeric' }) : '–'}</span>
            <span class="kacts">${owner ? `${key || S.me.api_key_copyable ? `<button type="button" class="btn sm" id="keycopy">${ui('copy', 14)}Copy</button>` : ''}
              <label class="amenu" title="Key options">${ui('more', 16)}<select id="keymenu" aria-label="Key options"><option value="" selected disabled hidden></option>
                <option value="rename">Rename</option><option value="new">Make a new key</option><option value="delete">Delete key…</option></select></label>` : ''}</span></div></div>
        ${key ? '<p class="note">New key made. Copy it into your app in step 2.</p>' : !S.me.api_key_copyable && owner ? '<p class="note">This key was made before keys could be copied here. Make a new key from the ⋯ menu to be able to copy it.</p>' : ''}`
      : `<div class="kempty"><span>${ui('spark', 18)}</span><div><b>No API key yet</b><span class="note">Create one, then paste it into your AI app in step 2.</span></div>
          ${owner ? `<button class="btn" id="apikey">${ui('plus', 14)}Create API key</button>` : ''}</div>`}
      ${owner ? '' : '<p class="note">Only the workspace owner can create, copy or delete it.</p>'}</div>`)}
    ${numbered(2, 'Connect your app', 'Pick the app you use and follow the steps.', `<div class="msetup">${clientSetup(key)}</div>`)}
    ${numbered(3, 'Ask', `Copy one into your AI. It uses the posts in your <a href="#library">Library</a>${unused ? ` (${unused} ready)` : ''}.`,
      `<div class="mprompts">${prompts.map(([ic, tag, p]) => `<button type="button" class="mprompt" data-copy="${esc(p)}" title="Copy">
          <span class="mtag">${ui(ic, 13)}${tag}</span><span class="mpt">${esc(p)}</span><span class="mcopy">${ui('copy', 14)}</span></button>`).join('')}</div>`)}
    <div class="mfoot">
      <p class="note">It can't connect accounts, invite people or delete brands; those stay here. <a href="/ai.html" target="_blank" rel="noopener">Full guide</a> · <a href="/ai.html#help" target="_blank" rel="noopener">Troubleshooting</a></p></div>`;
}

// ---- library folders: one folder = one post, ready to schedule -------------
const FSTATUS = { unused: 'Not used yet', awaiting_approval: 'Waiting for approval', scheduled: 'Scheduled', posted: 'Posted' };
const folderStatus = f => (f.status === 'scheduled' && f.next_at ? `Scheduled ${fmt(f.next_at, { weekday: 'short', day: 'numeric', month: 'short' })}`
  : f.status === 'posted' && f.posted_at ? `Posted ${fmt(f.posted_at, { day: 'numeric', month: 'short' })}` : FSTATUS[f.status]);
const foldersShown = (b = curBrand()) => (S.folders || []).filter(f => b === 'all' || (b === 'none' ? !f.brand_id : f.brand_id === b || !f.brand_id));
const folderOf = id => (S.folders || []).find(f => f.id === id);
const itemPic = (i, attrs = '') => (i.kind === 'video' || isVideoItem(i)) ? pic(i.url, `alt="" loading="lazy" ${attrs}`) : `<img src="${esc(i.url)}" alt="" loading="lazy" ${attrs}>`;

function folderCard(f) {
  const n = f.items.length, kind = f.kind === 'video' ? 'Video' : `${n} photo${n === 1 ? '' : 's'}`;
  return `<div class="fcard" data-folder="${f.id}" role="button" tabindex="0">
    <div class="fthumbs">${f.items.slice(0, 3).map(i => itemPic(i)).join('') || `<span class="fempty">${ui('image', 22)}</span>`}${n > 3 ? `<span class="fmore">+${n - 3}</span>` : ''}</div>
    <div class="fbody"><b>${esc(f.name)}</b>
      <span class="fmeta">${f.brand_id && brandName(f.brand_id) ? `<i class="hdot" style="background:${brandHue(f.brand_id)}"></i>${esc(brandName(f.brand_id))} · ` : ''}${n ? kind : 'Empty'}</span>
      ${f.note ? `<p class="fnote">${esc(f.note)}</p>` : ''}
      <span class="fst ${f.status}">${folderStatus(f)}</span></div></div>`;
}

function folderDetail(f) {
  const n = f.items.length, isVid = f.kind === 'video';
  return `<section class="panel fdetail">
    <header><button class="btn ghost sm" id="fback">${ui('chev', 14)}Library</button><span class="fst ${f.status}">${folderStatus(f)}</span>
      <span class="hacts">${n ? `<button class="btn" data-fsched="${f.id}">${ui('plus', 15)}Schedule</button>` : ''}<button class="btn ghost danger" data-fdel="${f.id}">Delete post</button></span></header>
    <div class="fform">
      <label class="f" for="fname">Name</label><input type="text" id="fname" maxlength="80" value="${esc(f.name)}">
      ${S.me.brands.length ? `<label class="f" for="fbrandsel">Brand</label><select id="fbrandsel"><option value="">Shared, every brand</option>
        ${S.me.brands.map(x => `<option value="${x.id}" ${f.brand_id === x.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>` : ''}
      <label class="f" for="fnoteinp">Note <span class="note">for whoever writes the caption: the offer, a code, what to stress, "not before Friday"</span></label>
      <textarea id="fnoteinp" maxlength="2000" placeholder="e.g. 20% off with code BF20. Don't post before Friday.">${esc(f.note || '')}</textarea>
      <div class="fsave"><button class="btn sec" id="fsave">Save</button></div>
    </div>
    <div class="fitems">${n ? `<p class="note">${isVid ? 'One video.' : 'Posted in this order. The first photo is the cover.'}</p>
      <div class="mgrid lib">${f.items.map((i, k) => `<div class="mt fi">${itemPic(i)}${!isVid ? `<span class="mn">${k + 1}</span>` : ''}
        <div class="ctl">${!isVid ? `<button data-fmv="${k}:-1" aria-label="Move earlier" ${k ? '' : 'disabled'}>‹</button>` : ''}
          <button data-fout="${esc(i.key)}" aria-label="Take out of the folder" title="Take out of the folder">×</button>
          ${!isVid ? `<button data-fmv="${k}:1" aria-label="Move later" ${k < n - 1 ? '' : 'disabled'}>›</button>` : ''}</div></div>`).join('')}</div>`
      : '<p class="note">Empty. Upload into it above, or select photos further down the Library and use "Move to folder".</p>'}</div>
  </section>`;
}

// Above the caption: the note of the folder this post comes from.
function folderHint() {
  const f = folderOf(S.fromFolder);
  return f ? `<div class="fhint">${ui('image', 14)}<span>From <b>${esc(f.name)}</b>${f.note ? `: ${esc(f.note)}` : ''}</span></div>` : '';
}

async function scheduleFolder(id) {
  const f = folderOf(id);
  if (!f || !f.items.length) return;
  resetComposer();
  if (f.brand_id && brandName(f.brand_id) && curBrand() !== f.brand_id) setBrand(f.brand_id);
  location.hash = '#compose';
  await useFromLibrary(f.items.map(i => i.key));
  S.fromFolder = f.id;
  render();
}
// A brand's own photos plus the shared ones (in no brand).
const libShown = (b = curBrand()) => (S.lib?.items || []).filter(i => b === 'all' || (b === 'none' ? !i.brand_id : i.brand_id === b || !i.brand_id));
const isVideoItem = i => /^video\//.test(i?.content_type || '') || isVid(i?.key);
const libTile = (i, sel, attr) => `<label class="mt lt ${sel ? 'sel' : ''}">${isVideoItem(i)
    ? `${pic(i.url)}<span class="vd">${ui('play', 11)}${i.duration_ms ? mmss(i.duration_ms) : 'Video'}</span>`
    : `<img src="${esc(i.url)}" alt="${esc(i.name || '')}" loading="lazy">`}
  <input type="checkbox" ${attr}="${esc(i.key)}" ${sel ? 'checked' : ''} aria-label="Select ${esc(i.name || 'photo')}">
  ${i.brand_id && brandName(i.brand_id) ? `<span class="ltb" style="background:${brandHue(i.brand_id)}" title="${esc(brandName(i.brand_id))}"></span>` : ''}</label>`;

// The library as a board: a column per brand, each with its own drop zone.
// One post = its photos in order, or one video. Scheduled and posted ones sit
// in their own tabs so the board shows only what still needs a date.
const LTABS = [['todo', 'To schedule', f => f.status === 'unused' || f.status === 'awaiting_approval'],
  ['scheduled', 'Scheduled', f => f.status === 'scheduled'], ['posted', 'Posted', f => f.status === 'posted']];

function libCard(f, tab) {
  const n = f.items.length, first = f.items[0];
  const kind = !n ? 'No photos yet' : f.kind === 'video' ? `Video${first?.duration_ms ? ` · ${mmss(first.duration_ms)}` : ''}` : `${n} photo${n === 1 ? '' : 's'}`;
  const when = f.status === 'scheduled' && f.next_at ? fmt(f.next_at, { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
    : f.status === 'posted' && f.posted_at ? `Posted ${fmt(f.posted_at, { day: 'numeric', month: 'short' })}` : '';
  return `<div class="lcard" data-folder="${f.id}" role="button" tabindex="0" title="Open">
    <div class="lthumb">${first ? itemPic(first) : `<span class="fempty">${ui('image', 18)}</span>`}${f.kind === 'video' && n ? `<span class="lplay">${ui('play', 10)}</span>` : n > 1 ? `<span class="lcount">${n}</span>` : ''}</div>
    <div class="lbody"><b>${esc(f.name)}</b>
      <span class="lmeta">${kind}${f.status === 'awaiting_approval' ? ' · <em class="wait">Waiting for approval</em>' : ''}</span>
      ${f.note ? `<span class="lnote">${esc(f.note)}</span>` : ''}</div>
    ${tab === 'todo' ? (n ? `<button class="btn sm lsched" data-fsched="${f.id}">Schedule</button>` : '')
      : `<span class="lwhen ${f.status}">${f.status === 'scheduled' ? ui('cal', 12) : ''}${when || FSTATUS[f.status]}</span>`}</div>`;
}

function libraryView() {
  const open = S.folderOpen && folderOf(S.folderOpen);
  const b = curBrand(), items = libShown(b).filter(i => !i.folder_id), sel = (S.libSel || []).filter(k => items.some(i => i.key === k));
  const groups = b === 'all' ? [...S.me.brands.map(x => [x.id, x.name]), ['', 'Shared']] : [[b === 'none' ? '' : b, brandLabel(b)], ...(b === 'none' ? [] : [['', 'Shared']])];
  const inGroup = (x, id) => (x.brand_id || '') === id || (!id && x.brand_id && !brandName(x.brand_id));
  const brandSel = (id, val, first) => `<select id="${id}" aria-label="Brand">${first}${S.me.brands.map(x => `<option value="${x.id}" ${val === x.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>`;
  const up = col => (S.libUp || []).filter(u => col === undefined || (u.col ?? null) === col).map(u => `<div class="mt up">${u.video ? `<video src="${esc(u.url)}" muted playsinline preload="metadata"></video>` : `<img src="${esc(u.url)}" alt="">`}</div>`).join('');

  if (open) return `<form class="panel libup" id="libdrop" onsubmit="return false">
      <label class="libdz"><input type="file" id="libfiles" accept="${ACCEPT}" multiple>${ui('plus', 22)}<b>Add photos or a video to "${esc(open.name)}"</b><span>Drop files here, or click to choose. JPG or PNG photos up to 5 MB, MP4 or MOV videos up to ${videoMb()} MB.</span></label>
      ${up() ? `<div class="mgrid">${up()}</div>` : ''}</form>${folderDetail(open)}`;

  const all = foldersShown(b), tab = S.libTab || 'todo', test = LTABS.find(t => t[0] === tab)[2];
  const tabs = `<div class="ltop"><div class="seg" role="group" aria-label="Show">${LTABS.map(([k, l, fn]) => `<button data-ltab="${k}" class="${k === tab ? 'on' : ''}" aria-pressed="${k === tab}">${l}<span class="lc">${all.filter(fn).length}</span></button>`).join('')}</div>
    <span class="note">One post is its photos in order, or one video. Drop files on a brand to make a new post.</span></div>`;
  if (!S.lib || !S.folders) return `${tabs}<div class="lboard">${[0, 1, 2].map(() => `<section class="lcol">${skRows(4)}</section>`).join('')}</div>`;

  const cols = groups.map(([id, name]) => {
    const list = all.filter(f => inGroup(f, id) && test(f)).sort((x, y) => tab === 'posted' ? (y.posted_at || 0) - (x.posted_at || 0) : tab === 'scheduled' ? (x.next_at || 0) - (y.next_at || 0) : 0);
    const loose = items.filter(i => inGroup(i, id));
    if (!id && b === 'all' && S.me.brands.length && !list.length && !loose.length && !up(null)) return '';
    const looseOpen = (S.libLoose || []).includes(id);
    return `<section class="lcol" data-colbrand="${id}">
      <header><h3>${id ? `<i class="hdot" style="background:${brandHue(id)}"></i>` : ''}${esc(name)}</h3><span class="lnum">${list.length}</span>
        <label class="btn ghost sm lnew" title="New post from photos or a video"><input type="file" data-colup="${id}" accept="${ACCEPT}" multiple>${ui('plus', 14)}New post</label></header>
      ${up(id || null) ? `<div class="mgrid lup">${up(id || null)}</div>` : ''}
      ${list.length ? `<div class="lclist">${list.map(f => libCard(f, tab)).join('')}</div>`
        : tab === 'todo' ? `<label class="lcdrop"><input type="file" data-colup="${id}" accept="${ACCEPT}" multiple>${ui('plus', 22)}<b>Nothing waiting for a date</b><span>Drop photos or a video here to make a new ${esc(id ? name : 'shared')} post${id ? '' : ' that every brand can use'}.</span></label>`
        : `<p class="lempty">${tab === 'scheduled' ? 'Nothing scheduled.' : 'Nothing posted yet.'}</p>`}
      ${tab === 'todo' && loose.length ? `<button class="lloose" data-lloose="${id}" aria-expanded="${looseOpen}">${ui('chev', 12)}${libCount(loose)} not in a post</button>
        ${looseOpen ? `<div class="mgrid lib">${loose.map(i => libTile(i, sel.includes(i.key), 'data-lsel')).join('')}</div>` : ''}` : ''}
    </section>`;
  }).join('');
  return `${tabs}<div class="lboard ${groups.length === 1 || cols.split('class="lcol"').length === 2 ? 'one' : ''}">${cols}</div>
    ${sel.length ? `<div class="libbar"><b>${sel.length} selected</b>
      <button class="btn" id="libsched">${ui('plus', 15)}Schedule</button>
      ${all.length ? `<select id="libtofolder" aria-label="Add to post"><option value="" disabled selected>Add to post…</option>${all.filter(f => f.status === 'unused').map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join('')}</select>` : ''}
      ${S.me.brands.length ? `${brandSel('libmove', '', '<option value="" disabled selected>Move to…</option><option value="-">Shared</option>')}` : ''}
      <button class="btn ghost danger" id="librm">Remove</button><button class="btn ghost" id="libclear">Clear</button></div>` : ''}`;
}

// Dropped files become posts in that brand: all the photos as one post, each
// video as a post of its own.
async function newPostsFrom(files, brand) {
  files = [...files].filter(f => isVideoFile(f) || /^image\/(jpeg|png)$/.test(f.type) || /\.(jpe?g|png)$/i.test(f.name));
  if (!files.length) { toast('JPG or PNG photos, or MP4 or MOV videos.', 'err'); return; }
  const photos = files.filter(f => !isVideoFile(f)), sets = [...(photos.length ? [photos] : []), ...files.filter(isVideoFile).map(v => [v])];
  for (const set of sets) {
    try {
      const name = set[0].name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').trim().slice(0, 80) || 'New post';
      const f = await send('/folders', 'POST', { name, brand_id: brand || null });
      await uploadToLibrary(set, { brand: brand || null, folderId: f.id });
    } catch (e) { S.flash = { kind: 'err', text: e.message }; render(); }
  }
  await reloadLibrary(); render();
}

const ACCEPT = 'image/jpeg,image/png,video/mp4,video/quicktime';
const videoMb = () => Math.round((S.me?.limits?.video_bytes || 100 * 1024 * 1024) / 1024 / 1024);
const libCount = list => { const v = list.filter(isVideoItem).length, ph = list.length - v;
  return [ph && `${ph} photo${ph === 1 ? '' : 's'}`, v && `${v} video${v === 1 ? '' : 's'}`].filter(Boolean).join(' · '); };
const isVideoFile = f => /^video\//.test(f.type) || /\.(mp4|mov)$/i.test(f.name);

// Length and size as the browser reads them; the platforms check the rest.
function videoMeta(file) {
  return new Promise(res => {
    const v = document.createElement('video'), url = URL.createObjectURL(file);
    const done = m => { URL.revokeObjectURL(url); res(m); };
    v.preload = 'metadata'; v.muted = true;
    v.onloadedmetadata = () => done({ duration_ms: Number.isFinite(v.duration) ? Math.round(v.duration * 1000) : null,
      width: v.videoWidth || null, height: v.videoHeight || null });
    v.onerror = () => done({});
    v.src = url;
  });
}

// One frame of the video as a small JPG, the still pages show instead of the video.
function videoStill(src) {
  return new Promise(res => {
    const v = document.createElement('video'), url = typeof src === 'string' ? src : URL.createObjectURL(src);
    const done = b => { if (typeof src !== 'string') URL.revokeObjectURL(url); v.removeAttribute('src'); v.load(); res(b); };
    v.muted = true; v.playsInline = true; v.preload = 'auto'; v.crossOrigin = 'anonymous';
    v.onloadeddata = () => { v.currentTime = Math.min(0.1, (v.duration || 1) / 2); };
    v.onseeked = () => {
      const w = Math.min(540, v.videoWidth || 540), c = document.createElement('canvas');
      c.width = w; c.height = Math.round(w * (v.videoHeight || 960) / (v.videoWidth || 540));
      try { c.getContext('2d').drawImage(v, 0, 0, c.width, c.height); c.toBlob(b => done(b), 'image/jpeg', 0.8); } catch { done(null); }
    };
    v.onerror = () => done(null);
    setTimeout(() => done(null), 20000);
    v.src = url;
  });
}
const putStill = async (key, src) => { const b = await videoStill(src);
  if (b) await api(`/media/poster?key=${encodeURIComponent(key)}`, { method: 'PUT', headers: { 'Content-Type': 'image/jpeg' }, body: b }); };

// Videos skip the site's proxy: a ticket from the API, then one PUT straight
// to the Worker, which streams it into the library.
async function uploadVideoFile(file, brand, folderId) {
  const type = file.type === 'video/quicktime' || /\.mov$/i.test(file.name) ? 'video/quicktime' : 'video/mp4';
  if (file.size > videoMb() * 1024 * 1024) throw new Error(`Each video must be ${videoMb()} MB or smaller`);
  const meta = await videoMeta(file);
  const t = await send('/media/video', 'POST', { content_type: type, bytes: file.size, name: file.name, brand_id: brand, folder_id: folderId || undefined, ...meta });
  let r;
  try { r = await fetch(t.upload_url, { method: 'PUT', headers: { 'Content-Type': type }, body: file }); }
  catch { throw new Error('The upload did not go through. Check the connection and try again.'); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `Upload failed (${r.status})`);
  await putStill(j.key, file).catch(() => {});
  return { key: j.key, url: j.url, name: file.name, content_type: type, ...meta };
}

async function uploadToLibrary(files, to) {
  const folder = to ? (to.folderId ? { id: to.folderId, brand_id: to.brand } : null) : S.folderOpen && folderOf(S.folderOpen);
  const brand = to ? to.brand : folder ? folder.brand_id : $('libbrand')?.value || null;
  S.libBrand = brand || '';
  S.libUp = S.libUp || [];
  for (const file of [...files].slice(0, 100)) {
    const u = { url: URL.createObjectURL(file), video: isVideoFile(file), col: brand || null };
    S.libUp.push(u); render();
    try {
      if (u.video) { await uploadVideoFile(file, brand, folder?.id); await reloadLibrary(); S.libUp.splice(S.libUp.indexOf(u), 1); render(); continue; }
      const { blob, type } = await shrink(file);
      const m = await api('/media', { method: 'POST', headers: { 'Content-Type': type }, body: blob });
      S.lib = await send('/library', 'POST', { keys: [m.key], brand_id: brand, folder_id: folder?.id, names: { [m.key]: file.name } });
      if (folder) S.folders = (await api('/folders')).folders;
    } catch (e) { S.flash = { kind: 'err', text: `${file.name}: ${e.message}` }; }
    S.libUp.splice(S.libUp.indexOf(u), 1); render();
  }
}

// Photos are scheduled as copies (the library keeps the original); a video
// is used as it is, and takes the place of any photos.
async function useFromLibrary(keys) {
  const items = (S.lib?.items || []).filter(i => keys.includes(i.key));
  const vids = items.filter(isVideoItem);
  if (vids.length) {
    if (keys.length > 1) { S.status = S.flash = { kind: 'err', text: 'A post can have photos or one video. Pick a single video.' }; return; }
    const v = vids[0];
    S.images = []; S.cover = 0;
    S.video = { key: v.key, url: v.url, name: v.name, duration_ms: v.duration_ms };
    return;
  }
  S.video = null;
  keys = keys.slice(0, 35 - S.images.length);
  if (!keys.length) return;
  try {
    const { media } = await send('/media/copy', 'POST', { keys });
    for (const m of media) S.images.push({ key: m.key, url: m.url });
  } catch (e) { S.status = { kind: 'err', text: e.message }; }
}

function libPicker() {
  const items = libShown().filter(i => !i.folder_id), sel = S.libPickSel || [];
  const fs = foldersShown().filter(f => f.items.length).sort((a, b) => (a.status !== 'unused') - (b.status !== 'unused'));
  return `<div class="libpick"><div class="lph"><b>From library${curBrand() !== 'all' ? ` · ${esc(brandLabel(curBrand()))}` : ''}</b><span class="note">${sel.length ? `${sel.length} selected` : 'Pick photos in order, or one video'}</span></div>
    ${fs.length ? `<p class="note lpsub">Folders · one tap adds the whole post</p><div class="fgrid lpf2">${fs.map(f => folderCard(f).replace('data-folder=', 'data-usefolder=')).join('')}</div><p class="note lpsub">Single photos and videos</p>` : ''}
    ${!S.lib ? `<div class="mgrid">${[...Array(6)].map(() => `<div class="mt">${sk('100%', 120)}</div>`).join('')}</div>`
      : items.length ? `<div class="mgrid lib">${items.map(i => libTile(i, sel.includes(i.key), 'data-lpick')).join('')}</div>`
      : `<p class="note">The library is empty${curBrand() !== 'all' ? ' for this brand' : ''}. <a href="#library">Upload photos or videos to it</a>.</p>`}
    <div class="lpf"><button type="button" class="btn sec" id="libcancel">Cancel</button>
      <button type="button" class="btn" id="libadd" ${sel.length ? '' : 'disabled'}>Add ${sel.length > 1 ? sel.length : ''} ${sel.length === 1 && isVideoItem((S.lib?.items || []).find(i => i.key === sel[0])) ? 'video' : `photo${sel.length === 1 ? '' : 's'}`}</button></div></div>`;
}

function mediaView() {
  if (S.libPick) return libPicker();
  const v = S.video;
  if (v) return `<div class="vpick ${v.uploading ? 'up' : ''}"><video src="${esc(v.url)}" ${v.uploading ? 'muted' : 'controls'} ${/^blob:/.test(v.url) ? 'preload="metadata"' : `poster="${esc(v.url)}.jpg" preload="none"`} playsinline></video>
      <div class="vinfo"><b>${esc(v.name || 'Video')}</b><span class="note">${v.uploading ? 'Uploading to the library…' : `${v.duration_ms ? `${mmss(v.duration_ms)} · ` : ''}from the library`}</span>
        <div class="vact"><button type="button" class="btn sec sm" id="fromlib" ${v.uploading ? 'disabled' : ''}>Replace</button>
        <button type="button" class="btn ghost sm" id="rmvideo" ${v.uploading ? 'disabled' : ''}>Remove</button></div></div></div>
    <p class="note">A post holds photos or one video. ${toInstagram() ? 'It goes to Instagram as a Reel. ' : ''}</p>`;
  const max = S.images.length >= 35;
  const add = `<label class="addtile ${S.images.length ? '' : 'big'}" id="drop">
      <input type="file" id="files" accept="${S.images.length ? 'image/jpeg,image/png' : ACCEPT}" multiple ${max ? 'disabled' : ''}>
      ${ui('plus', S.images.length ? 20 : 24)}<b>${S.images.length ? 'Add' : 'Add photos or a video'}</b>
      ${S.images.length ? '' : `<span>Drop JPG or PNG photos (up to 5 MB) or one MP4 or MOV video (up to ${videoMb()} MB).</span>`}</label>`;
  const fromLib = `<button type="button" class="addtile lib ${S.images.length ? '' : 'big'}" id="fromlib" ${max ? 'disabled' : ''}>${ui('image', S.images.length ? 20 : 24)}<b>${S.images.length ? 'Library' : 'From library'}</b>${S.images.length ? '' : '<span>Photos and videos you uploaded ahead of time.</span>'}</button>`;
  return `<div class="mgrid ${S.images.length ? '' : 'two'}">${S.images.map((m, n) => `<div class="mt ${n === S.cover ? 'cover' : ''} ${m.uploading ? 'up' : ''}">
      <img src="${esc(m.url)}" alt="Photo ${n + 1}" data-cover="${n}" title="Make this the cover">
      <span class="mn">${n + 1}</span>${n === S.cover ? '<span class="badge">Cover</span>' : ''}
      <div class="ctl"><button data-mv="${n}:-1" aria-label="Move left">‹</button>
        <button data-rm="${n}" aria-label="Remove">×</button>
        <button data-mv="${n}:1" aria-label="Move right">›</button></div></div>`).join('')}${add}${fromLib}</div>
    ${S.images.length ? `<p class="note">Click a photo to make it the cover.${toInstagram() ? ' Tall photos are padded to 4:5 for Instagram, never cropped.' : ''}</p>` : ''}`;
}

// Everywhere, plus one tab per platform; a dot marks a platform with its own caption.
function captionTabs(pls) {
  const tab = pls.includes(S.capTab) ? S.capTab : 'all';
  const tabs = pls.length > 1 ? `<div class="ctabs">${['all', ...pls].map(k => `<button type="button" data-captab="${k}" class="${tab === k ? 'on' : ''}">
      ${k === 'all' ? 'Everywhere' : `${icon(k, 13)}${PLATFORM[k]}`}${k !== 'all' && S.over[k] != null ? '<i class="dot"></i>' : ''}</button>`).join('')}</div>` : '';
  if (tab === 'all') return `${tabs}<textarea id="caption" placeholder="Write your caption…">${esc(S.caption)}</textarea>`;
  return `${tabs}${S.over[tab] == null
    ? `<div class="cempty"><span>${PLATFORM[tab]} uses the caption from Everywhere.</span>
        <button type="button" class="btn sec" data-custom="${tab}">Write a different one</button></div>`
    : `<textarea id="ov-${tab}" data-ov="${tab}" aria-label="${PLATFORM[tab]} caption">${esc(S.over[tab])}</textarea>
       <button type="button" class="link" data-uncustom="${tab}">Use the Everywhere caption instead</button>`}`;
}

// How the post will look, per platform, updated as you type.
const previewPl = pls => (pls.includes(S.prevTab) ? S.prevTab : pls[0]);
function previewView() {
  const pls = chosenPlatforms(), pl = previewPl(pls);
  if (!pl) return `<div class="pv-empty">${ui('eye', 22)}<span>Choose an account to see how the post will look.</span></div>`;
  const a = acct(S.targets.find(id => platformOf(acct(id)) === pl));
  const name = a?.username || a?.display_name || PLATFORM[pl];
  const imgs = S.video ? [S.video.url] : S.images.map(m => m.url);
  const cap = esc(captionFor(pl) || '');
  const shot = u => S.video && !/^blob:/.test(u) ? pic(u) : S.video ? `<video src="${esc(u)}#t=0.1" muted playsinline preload="metadata"></video>` : `<img src="${esc(u)}" alt="">`;
  const av = withBadge(avatar(a?.avatar_url, name), pl);
  const ph = '<div class="pv-ph">' + ui('plus', 20) + '</div>';
  if (pl === 'instagram') return `<div class="pv ig"><div class="pv-h">${av}<b>${esc(name)}</b></div>
      <div class="pv-media ${S.video ? 'r916' : 'r45'}">${imgs[0] ? shot(imgs[0]) : ph}${imgs.length > 1 ? `<span class="pv-count">1/${imgs.length}</span>` : ''}</div>
      ${imgs.length > 1 ? `<div class="pv-dots">${imgs.slice(0, 10).map((_, i) => `<i class="${i ? '' : 'on'}"></i>`).join('')}</div>` : ''}
      <div class="pv-acts">${ui('heart', 20)}${ui('comment', 20)}${ui('share', 20)}</div>
      <p class="pv-cap"><b>${esc(name)}</b> ${cap || '<span class="note">Your caption appears here.</span>'}</p></div>`;
  if (pl === 'facebook') return `<div class="pv fb"><div class="pv-h">${av}<div><b>${esc(name)}</b><small>Just now</small></div></div>
      <p class="pv-cap">${cap || '<span class="note">Your caption appears here.</span>'}</p>
      <div class="pv-grid n${Math.min(imgs.length, 4)}">${imgs.slice(0, 4).map((u, i) => `<div>${shot(u)}${i === 3 && imgs.length > 4 ? `<span>+${imgs.length - 4}</span>` : ''}</div>`).join('') || ph}</div>
      <div class="pv-acts fb">${ui('heart', 17)}<span>Like</span>${ui('comment', 17)}<span>Comment</span>${ui('share', 17)}<span>Share</span></div></div>`;
  const cover = imgs[S.cover] || imgs[0];
  return `<div class="pv tt"><div class="pv-media r916">${cover ? shot(cover) : ph}
      <div class="pv-side">${ui('heart', 22)}${ui('comment', 22)}${ui('share', 22)}</div>
      <div class="pv-over"><b>@${esc(name)}</b>${S.title ? `<span class="t">${esc(S.title)}</span>` : ''}<span>${cap}</span></div>
      ${imgs.length > 1 ? `<div class="pv-dots tt">${imgs.slice(0, 12).map((_, i) => `<i class="${i ? '' : 'on'}"></i>`).join('')}</div>` : ''}</div></div>`;
}
const refreshPreview = () => { const el = $('preview'); if (el) el.innerHTML = previewView(); };

const avatar = (url, name) => url
  ? `<img class="av" src="${esc(url)}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'av ini',textContent:'${esc((name || '?')[0].toUpperCase())}'}))">`
  : `<span class="av ini">${esc((name || '?')[0].toUpperCase())}</span>`;
const handle = a => `${platformOf(a) === 'facebook' ? '' : '@'}${esc(a.username || a.display_name)}`;
// A handle that says which platform it is when two accounts share a name
// (the same brand on TikTok and Instagram is often both @brand).
function who(x) {
  const name = x.username || x.display_name || '', pl = x.platform || 'tiktok', low = name.toLowerCase();
  if (!name) return `<span class="gone">${PLATFORM[pl]} account removed</span>`;
  const dup = (S.me?.accounts || []).filter(a => (a.username || a.display_name || '').toLowerCase() === low).length > 1;
  return `${pl === 'facebook' ? '' : '@'}${esc(name)}${dup ? `<small class="plt">${PLATFORM[pl]}</small>` : ''}`;
}


const brandName = id => S.me.brands.find(b => b.id === id)?.name;
function brandGroups(list = S.me.accounts) {
  const groups = S.me.brands.map(b => ({ id: b.id, name: b.name, accounts: list.filter(a => a.brand_id === b.id) }));
  const loose = list.filter(a => !a.brand_id || !brandName(a.brand_id));
  if (loose.length) groups.push({ id: 'none', name: S.me.brands.length ? 'Personal' : 'All accounts', accounts: loose });
  const byPlatform = (a, b) => ORDER.indexOf(platformOf(a)) - ORDER.indexOf(platformOf(b));
  return groups.map(g => ({ ...g, accounts: g.accounts.sort(byPlatform) }));
}
const marks = accounts => [...new Set(accounts.map(platformOf))].sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b))
  .map(pl => icon(pl, 13)).join('');

function pickGroup(id, on) {
  const g = brandGroups().find(x => x.id === id);
  for (const a of (g?.accounts || []).filter(a => !a.needs_reconnect)) toggleTarget(a.id, on, false);
  render();
}

// The audited part, once per TikTok account: whose account it is, read live
// from TikTok, and a privacy choice with no default.
function ttCard(id) {
  const a = acct(id), t = S.tt[id] || {}, i = t.info;
  if (t.err) return `<div class="ttcard"><b>${handle(a)}</b><p class="note bad">${esc(t.err)}</p></div>`;
  if (!i) return `<div class="ttcard"><b>${handle(a)}</b><p class="note">Loading account settings…</p></div>`;
  const opts = (i.privacy_level_options || []).filter(o => !(o === 'SELF_ONLY' && S.set.branded));
  return `<div class="ttcard">
    <div class="who">${withBadge(avatar(i.creator_avatar_url, i.creator_nickname), 'tiktok')}
      <div><b>${esc(i.creator_nickname)}</b><div class="note">@${esc(i.creator_username)}</div></div></div>
    <label class="f" for="pv-${id}" style="margin-top:10px">Who can view this post *</label>
    <select id="pv-${id}" data-pv="${id}"><option value="" ${t.privacy ? '' : 'selected'}>Select who can view…</option>
      ${opts.map(o => `<option value="${o}" ${t.privacy === o ? 'selected' : ''}>${PRIVACY_LABEL[o] || o}</option>`).join('')}
    </select>
    ${S.set.branded && (i.privacy_level_options || []).includes('SELF_ONLY') ? '<p class="note">Branded content cannot be private, so "Only me" is unavailable.</p>' : ''}
    ${row('Allow comments', i.comment_disabled ? 'Turned off in this account\'s TikTok settings.' : '',
      `<input type="checkbox" data-cm="${id}" ${t.comment && !i.comment_disabled ? 'checked' : ''} ${i.comment_disabled ? 'disabled' : ''}>`)}
  </div>`;
}

const row = (t, d, control) => `<div class="row"><span class="txt"><span class="t">${t}</span>${d ? `<span class="d">${d}</span>` : ''}</span>${control}</div>`;

const acct = id => S.me.accounts.find(a => a.id === id);
const ttTargets = () => S.targets.filter(id => platformOf(acct(id)) === 'tiktok');
const toInstagram = () => S.targets.some(id => acct(id)?.platform === 'instagram');
const chosenPlatforms = () => ORDER.filter(pl => S.targets.some(id => platformOf(acct(id)) === pl));
const captionFor = pl => (S.over[pl] ?? S.caption);
// A TikTok video's caption is its title, which holds 2,200 characters.
const capMax = pl => (pl === 'tiktok' && S.video ? 2200 : CAPTION_MAX[pl]);

// Each platform's count against its own limit, for whichever caption it will
// actually get. Updated as you type, without re-rendering the page.
function limitsLine() {
  return chosenPlatforms().map(pl => {
    const c = captionFor(pl), n = len(c), over = n > capMax(pl) || (pl === 'instagram' && hashtags(c) > IG_HASHTAGS);
    return `<span class="lim ${over ? 'bad' : ''}">${icon(pl, 12)} ${n.toLocaleString()} / ${capMax(pl).toLocaleString()}${
      pl === 'instagram' ? ` · ${hashtags(c)}/${IG_HASHTAGS} #` : ''}${S.over[pl] != null ? ' · custom' : ''}</span>`;
  }).join('') || `<span class="lim">${len(S.caption)} characters</span>`;
}

const refreshLimits = () => { const el = $('caplimits'); if (el) el.innerHTML = limitsLine(); };
function goLabel() {
  if (S.targets.length > 3) return `${S.targets.length} accounts`;
  return S.targets.map(id => `${PLATFORM[platformOf(acct(id))]} ${handle(acct(id)).replace(/&amp;/g, '&')}`).join(', ');
}

function missing() {
  if (!S.targets.length) return 'Choose where to post';
  if (!S.images.length && !S.video) return 'Add photos or a video';
  if (S.images.some(m => m.uploading) || S.video?.uploading) return 'Waiting for uploads to finish';
  const ms = S.video?.duration_ms;
  if (ms && toInstagram() && (ms < 3000 || ms > 15 * 60e3)) return 'Instagram Reels must be 3 seconds to 15 minutes long';
  if (ms && chosenPlatforms().includes('facebook') && ms > 20 * 60e3) return 'Facebook Page videos can be up to 20 minutes here';
  for (const pl of chosenPlatforms()) {
    const c = captionFor(pl);
    if (len(c) > capMax(pl)) return `The ${PLATFORM[pl]} caption is too long (${len(c).toLocaleString()} / ${capMax(pl).toLocaleString()})`;
    if (pl === 'instagram' && hashtags(c) > IG_HASHTAGS) return `Instagram allows at most ${IG_HASHTAGS} hashtags`;
  }
  if (toInstagram() && !S.video && S.images.length > IG_MAX) return `Instagram posts can have at most ${IG_MAX} photos`;
  const tts = ttTargets();
  if (tts.length) {
    if (len(S.title) > 90) return 'The title is too long';
    for (const id of tts) {
      const t = S.tt[id] || {};
      if (t.err) return `${handle(acct(id))}: ${t.err}`;
      if (!t.info) return 'Loading TikTok account settings…';
      if (!t.privacy) return `Choose who can view the post on @${t.info.creator_username}`;
    }
    if (S.set.disclose && !S.set.brand && !S.set.branded) return 'You need to indicate if your content promotes yourself, a third party, or both';
  }
  if (S.when === 'queue') {
    if (!S.queuePosts) return 'Finding the next free slots…';
    const plan = queuePlan();
    const none = S.targets.find(id => !plan[id]);
    if (none) return `${handle(acct(none))} has no posting times. Set them in ${can('admin') ? 'Accounts' : 'the brand (ask an admin)'}.`;
  }
  if (S.when === 'later') {
    const t = S.at ? inputToMs(S.at) : NaN;
    if (!Number.isFinite(t)) return 'Pick a date and time';
    if (t < Date.now() + 5 * 60e3) return 'Pick a time at least 5 minutes from now';
  }
  return '';
}

// ---- time, always in the workspace's zone ---------------------------------
// A post scheduled for "9:00" is 9:00 where the workspace says, whoever looks.

const tz = () => S.me?.workspace?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
const fmt = (sec, opts) => new Intl.DateTimeFormat(undefined, { timeZone: tz(), ...opts }).format(new Date(sec * 1000));
const fmtFull = sec => fmt(sec, { dateStyle: 'medium', timeStyle: 'short' });

function zoned(ms) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: tz(), hourCycle: 'h23', year: 'numeric',
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).formatToParts(new Date(ms)).map(x => [x.type, x.value]));
  return { y: +p.year, m: +p.month, d: +p.day, h: +p.hour % 24, mi: +p.minute };
}
// Wall-clock time in the workspace's zone -> epoch ms (two passes settle DST edges).
function zonedToMs(y, m, d, h = 0, mi = 0) {
  const want = Date.UTC(y, m - 1, d, h, mi);
  let guess = want;
  for (let i = 0; i < 2; i++) { const p = zoned(guess); guess += want - Date.UTC(p.y, p.m - 1, p.d, p.h, p.mi); }
  return guess;
}
const pad = n => String(n).padStart(2, '0');
function localInput(ms) { const p = zoned(ms); return `${p.y}-${pad(p.m)}-${pad(p.d)}T${pad(p.h)}:${pad(p.mi)}`; }
function inputToMs(str) {
  const [date, time] = String(str).split('T');
  if (!date || !time) return NaN;
  const [y, m, d] = date.split('-').map(Number), [h, mi] = time.split(':').map(Number);
  return zonedToMs(y, m, d, h, mi);
}
// A calendar day as plain numbers, and the date one is in.
const dayOf = sec => { const p = zoned(sec * 1000); return `${p.y}-${p.m}-${p.d}`; };
const addDays = (day, n) => { const t = new Date(Date.UTC(day.y, day.m - 1, day.d + n)); return { y: t.getUTCFullYear(), m: t.getUTCMonth() + 1, d: t.getUTCDate() }; };
const dayKey = day => `${day.y}-${day.m}-${day.d}`;
const ymd = day => day.y * 10000 + day.m * 100 + day.d;
const dayLabel = (day, opts) => new Intl.DateTimeFormat(undefined, { timeZone: 'UTC', ...opts }).format(new Date(Date.UTC(day.y, day.m - 1, day.d)));
const today = () => { const p = zoned(Date.now()); return { y: p.y, m: p.m, d: p.d }; };

// ---- compose actions ---------------------------------------------------

async function shrink(file) {
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE_W / bmp.width, MAX_SIDE_H / bmp.height);
  if (scale === 1 && file.size <= 5 * 1024 * 1024) return { blob: file, type: file.type };
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.9));
  return { blob, type: 'image/jpeg' };
}

// A video goes into the library (under the brand in view) and becomes the post's media.
async function addVideo(file) {
  const b = curBrand(), brand = b === 'all' || b === 'none' ? null : b;
  S.images = []; S.cover = 0;
  const slot = S.video = { url: URL.createObjectURL(file), name: file.name, uploading: true };
  render();
  try {
    const v = await uploadVideoFile(file, brand);
    if (S.video === slot) S.video = v;
    S.lib = null;
  } catch (e) {
    if (S.video === slot) S.video = null;
    S.status = { kind: 'err', text: `${file.name}: ${e.message}` };
  }
  render();
}

async function addFiles(files) {
  const vid = [...files].find(isVideoFile);
  if (vid) {
    if (files.length > 1) S.status = { kind: 'err', text: 'A post can have photos or one video. Only the video was added.' };
    return addVideo(vid);
  }
  for (const file of [...files].slice(0, 35 - S.images.length)) {
    const slot = { url: URL.createObjectURL(file), uploading: true };
    S.images.push(slot); render();
    try {
      const { blob, type } = await shrink(file);
      const m = await api('/media', { method: 'POST', headers: { 'Content-Type': type }, body: blob });
      Object.assign(slot, { key: m.key, url: m.url, uploading: false });
    } catch (e) {
      S.images.splice(S.images.indexOf(slot), 1);
      S.status = { kind: 'err', text: `${file.name}: ${e.message}` };
    }
    render();
  }
}

function toggleTarget(id, on, draw = true) {
  S.targets = S.targets.filter(x => x !== id);
  if (on) S.targets.push(id);
  if (on && platformOf(acct(id)) === 'tiktok' && !S.tt[id]?.info) loadInfo(id);
  saveTargets();
  if (draw) render();
}

// Creator info is read fresh each time an account is picked, never reused
// from an earlier session: the options are TikTok's, as of now.
async function loadInfo(id) {
  S.tt[id] = { ...(S.tt[id] || {}), info: null, err: null, privacy: '' };
  try { S.tt[id].info = await api(`/accounts/${id}/creator-info`); }
  catch (e) { S.tt[id].err = e.code === 'needs_reconnect' ? 'Reconnect this account in Accounts.' : e.message; }
  render();
}

function setOpt(k, v) {
  S.set[k] = v;
  if (k === 'disclose' && !v) { S.set.brand = false; S.set.branded = false; }
  if (S.set.branded) for (const t of Object.values(S.tt)) if (t.privacy === 'SELF_ONLY') t.privacy = '';
  render();
}

function bulkPrivacy(level) {
  for (const id of ttTargets()) {
    const t = S.tt[id];
    if (t?.info && (t.info.privacy_level_options || []).includes(level)) t.privacy = level;
  }
  render();
}

// Instagram refuses images outside 4:5..1.91:1, and a 9:16 slide is outside.
// Padding (over a blurred copy of the photo) keeps every line of slide text,
// where a crop would cut the top and bottom off.
// Instagram also crops every carousel image to the FIRST image's ratio, so
// all of them are padded to that one ratio, not merely into the allowed range.
const bitmap = async m => createImageBitmap(await (await fetch(m.url)).blob());
const clampRatio = r => Math.min(IG_MAX_RATIO, Math.max(IG_MIN_RATIO, r));
async function forInstagram(m, ratio) {
  const bmp = await bitmap(m);
  const r = bmp.width / bmp.height;
  if (Math.abs(r - ratio) < 0.01 && m.key.endsWith('.jpg')) return null;   // usable as is
  const W = 1080, H = Math.round(W / ratio);
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const cover = Math.max(W / bmp.width, H / bmp.height);
  g.filter = 'blur(40px) brightness(0.7)';
  g.drawImage(bmp, (W - bmp.width * cover) / 2, (H - bmp.height * cover) / 2, bmp.width * cover, bmp.height * cover);
  g.filter = 'none';
  const fit = Math.min(W / bmp.width, H / bmp.height);
  g.drawImage(bmp, (W - bmp.width * fit) / 2, (H - bmp.height * fit) / 2, bmp.width * fit, bmp.height * fit);
  const blob = await new Promise(res => c.toBlob(res, 'image/jpeg', 0.92));
  return (await api('/media', { method: 'POST', headers: { 'Content-Type': 'image/jpeg' }, body: blob })).key;
}

// Each post owns its images, so the first post takes the uploads and every
// other one gets server-side copies.
async function keysFor(platforms, { raw = false } = {}) {
  const plain = S.images.map(m => m.key);
  // Images opened from a draft belong to that draft until it is deleted, so
  // every new post gets its own copy.
  let plainUsed = !!S.fromDraft, igKeys = null, igUsed = false;
  const copy = async keys => (await api('/media/copy', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keys }) })).media.map(m => m.key);
  const out = [];
  for (const p of platforms) {
    if (p === 'instagram' && !raw) {
      if (!igKeys) {
        const first = await bitmap(S.images[0]);
        const ratio = clampRatio(first.width / first.height);
        const made = [];
        for (const m of S.images) made.push(await forInstagram(m, ratio));
        // Images that needed no change are copies of the upload, not the upload itself.
        const reuse = made.map((k, n) => k ? null : plain[n]).filter(Boolean);
        const copies = reuse.length ? await copy(reuse) : [];
        igKeys = made.map(k => k || copies.shift());
      }
      out.push(igUsed ? await copy(igKeys) : igKeys); igUsed = true;
    } else {
      out.push(plainUsed ? await copy(plain) : plain); plainUsed = true;
    }
  }
  return out;
}

// What a TikTok post sends: music for photos, duet and stitch for a video.
const ttSettings = (t, privacy) => ({ privacy_level: privacy, disable_comment: !t.comment || !!t.info?.comment_disabled,
  ...(S.video ? { disable_duet: !S.set.duet, disable_stitch: !S.set.stitch } : { auto_add_music: S.set.music }),
  brand_organic: S.set.disclose && S.set.brand, branded_content: S.set.disclose && S.set.branded });

async function submit() {
  if (missing() || S.busy) return;
  S.busy = true; S.status = { kind: '', text: 'Sending…' }; render();
  const jobs = S.targets.map(id => ({ id, platform: platformOf(acct(id)) }))
    .sort((a, b) => ORDER.indexOf(a.platform) - ORDER.indexOf(b.platform));
  const plan = S.when === 'queue' ? queuePlan() : null;
  const at = S.when === 'later' ? Math.floor(inputToMs(S.at) / 1000) : null;
  const made = [], errors = [];
  try {
    if (toInstagram() && !S.video) { S.status = { kind: '', text: 'Preparing photos for Instagram…' }; render(); }
    const keys = S.video ? jobs.map(() => []) : await keysFor(jobs.map(j => j.platform));
    for (const [n, j] of jobs.entries()) {
      if (jobs.length > 1) { S.status = { kind: '', text: `Sending ${n + 1} of ${jobs.length}…` }; render(); }
      const name = `${PLATFORM[j.platform]} ${handle(acct(j.id))}`;
      const t = S.tt[j.id] || {};
      try {
        made.push(await api('/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
          account_id: j.id, image_keys: keys[n], video_key: S.video?.key, cover_index: S.cover, title: S.video ? '' : S.title, caption: captionFor(j.platform),
          settings: j.platform !== 'tiktok' ? {} : ttSettings(t, t.privacy),
          scheduled_at: plan ? plan[j.id] : at, folder_id: S.fromFolder || undefined,
          // An edit replaces the one post it came from.
          replaces: S.replaces && S.replacesAccount === j.id ? S.replaces : undefined,
        }) }));
      } catch (e) { errors.push(`${name}: ${e.message}`); }
    }
  } catch (e) { errors.push(e.message); }
  S.busy = false;
  if (!made.length) { S.status = { kind: 'err', text: errors.join(' · ') }; return render(); }
  if (S.fromDraft && !errors.length) await dropDrafts(S.fromDraft);
  const cover = S.images[S.cover]?.url || S.images[0]?.url || '';
  const scheduled = made[0].scheduled_at > Date.now() / 1000 + 60;
  resetComposer();
  S.status = null;
  S.result = { scheduled, cover, posts: made, errors, open: true };
  render();
  if (!scheduled) watch(made.map(p => p.id));
  refreshCounts();
}

async function watch(ids) {
  const R = S.result;
  for (let n = 0; n < 100; n++) {
    await new Promise(r => setTimeout(r, 3000));
    const t = Math.floor(Date.now() / 1000);
    let posts;
    try { posts = (await api(`/posts?from=${t - 3600}&to=${t + 60}`)).posts; }
    catch { continue; }   // one failed check is not a result; keep watching
    for (const p of posts) { const i = R.posts.findIndex(x => x.id === p.id); if (i >= 0) R.posts[i] = p; }
    if (S.result === R && R.open) render();
    if (R.posts.every(p => p.status === 'published' || p.status === 'failed')) break;
  }
  if (S.result === R && R.open) return;
  // The sheet was closed: say how it went in a toast.
  const failed = R.posts.filter(p => p.status === 'failed'), ok = R.posts.filter(p => p.status === 'published');
  if (failed.length) toast(`${failed.length} post${failed.length === 1 ? '' : 's'} failed: ${failed.map(p => `${PLATFORM[p.platform]} @${p.username}`).join(', ')}. Open the calendar to retry.`, 'err');
  else if (ok.length === R.posts.length) toast(`Published to ${ok.length === 1 ? `${PLATFORM[ok[0].platform]} @${ok[0].username}` : `${ok.length} accounts`}.`);
}

// After Post now or Schedule: what happened, per account, and where to go next.
function resultView() {
  const R = S.result;
  if (!R?.open) return '';
  const done = R.posts.filter(p => p.status === 'published').length, failed = R.posts.filter(p => p.status === 'failed').length;
  const pending = R.posts.length - done - failed;
  const first = Math.min(...R.posts.map(p => p.scheduled_at));
  const title = R.scheduled ? `Scheduled for ${fmt(first, { weekday: 'short', month: 'short', day: 'numeric' })} · ${at(first)}`
    : pending ? `Posting to ${R.posts.length} account${R.posts.length === 1 ? '' : 's'}…`
    : failed ? `${done} published, ${failed} failed` : `Published to ${done} account${done === 1 ? '' : 's'}`;
  const state = R.scheduled ? 'ok' : pending ? 'busy' : failed ? 'bad' : 'ok';
  const row = p => {
    const a = acct(p.account_id);
    const right = R.scheduled ? `<span class="rs">${at(p.scheduled_at)}${dayOf(p.scheduled_at) !== dayOf(first) ? ` ${fmt(p.scheduled_at, { weekday: 'short' })}` : ''}</span>`
      : p.status === 'published' ? `<span class="rs ok">${ui('check', 14)}Published</span>${p.post_url ? `<a class="btn sec sm" href="${esc(p.post_url)}" target="_blank" rel="noopener">View</a>` : ''}`
      : p.status === 'failed' ? `<span class="rs bad">Failed</span><button class="btn sec sm" data-retry="${p.id}">Retry</button>`
      : '<span class="rs"><i class="spin"></i>Posting…</span>';
    return `<div class="rrow">${withBadge(avatar(a?.avatar_url, p.username), p.platform || 'tiktok')}
      <div class="rn"><b>${who(p)}</b>${p.status === 'failed' ? `<span title="${esc(p.fail_reason || '')}">${esc(p.fail_reason || 'Rejected')}</span>` : `<span>${PLATFORM[p.platform || 'tiktok']}</span>`}</div>${right}</div>`;
  };
  return `<div class="rsheet-bg" id="rsheetbg"><div class="rsheet" role="dialog" aria-modal="true" aria-labelledby="rtitle">
    <div class="rtop">${R.cover ? `<img src="${esc(R.cover)}" alt="">` : ''}<span class="rbadge ${state}">${state === 'busy' ? '<i class="spin"></i>' : ui(state === 'bad' ? 'x' : 'check', 18)}</span></div>
    <h2 id="rtitle">${title}</h2>
    <p class="rsub">${R.scheduled ? 'It goes out automatically, even with your laptop closed.' : pending ? 'You can close this. It keeps going, and you get a message when it is done.' : failed ? 'Retry the failed ones, or fix them from the calendar.' : 'It may take a minute to show on each profile.'}</p>
    <div class="rlist">${R.posts.map(row).join('')}${R.errors.map(e => `<div class="rrow"><span class="ic bad">${ui('x', 14)}</span><div class="rn"><b>Not sent</b><span title="${esc(e)}">${esc(e)}</span></div></div>`).join('')}</div>
    <div class="racts"><button class="btn sec" data-res="${R.scheduled ? 'calendar' : 'overview'}">${R.scheduled ? 'See in calendar' : 'Go to overview'}</button>
      <button class="btn" data-res="another">Create another</button></div>
    <button class="xbtn rclose" data-res="close" aria-label="Close">${ui('x', 18)}</button></div></div>`;
}

// Targets stay selected for the next post; privacy is chosen again each time.
function resetComposer() {
  Object.assign(S, { images: [], video: null, cover: 0, title: '', caption: '', when: 'now', at: '', status: null, replaces: null,
    replacesAccount: null, over: {}, fromDraft: null, draftGroup: null, fromFolder: null });
  for (const t of Object.values(S.tt)) { t.privacy = ''; t.comment = false; }
  S.set = { music: false, duet: false, stitch: false, disclose: false, brand: false, branded: false };
}

// ---- AI writing ------------------------------------------------------------
// Writes from the photos and a one-line brief; the result lands in the editor
// for the person to read and change. Nothing is posted by it.

const TONES = ['friendly', 'professional', 'playful', 'bold', 'inspirational', 'educational'];
const REWRITE_LABEL = { shorter: 'Shorter', punchier: 'Punchier', professional: 'More professional', casual: 'More casual', grammar: 'Fix grammar', hashtags: 'Add hashtags' };
const cap1 = s => s[0].toUpperCase() + s.slice(1);

// The brand to write for: the one most of the chosen accounts belong to.
function aiBrand() {
  const counts = {};
  for (const id of S.targets) { const b = acct(id)?.brand_id; if (b) counts[b] = (counts[b] || 0) + 1; }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
}

function aiPanel() {
  const A = S.ai;
  if (!A.open) return `<button type="button" class="btn sec aibtn" id="aiopen">✨ Write with AI</button>`;
  const brand = aiBrand(), bname = brand && S.me.brands.find(b => b.id === brand);
  return `<div class="aipanel">
    <div class="phead"><b>✨ Write with AI</b>${A.remaining != null ? `<span class="note">${A.remaining} left today</span>` : ''}
      <button type="button" class="link" id="aiclose" style="margin-left:auto">Close</button></div>
    <label class="f" for="aibrief">What is this post about? <span class="note">(optional with photos)</span></label>
    <textarea id="aibrief" maxlength="1000" placeholder="e.g. New sourdough is out, only on weekends">${esc(A.brief)}</textarea>
    <div class="aiopts">
      <label>Tone <select id="aitone">${TONES.map(t => `<option value="${t}" ${A.tone === t ? 'selected' : ''}>${cap1(t)}</option>`).join('')}</select></label>
      <label>Length <select id="ailen">${['short', 'medium', 'long'].map(t => `<option value="${t}" ${A.length === t ? 'selected' : ''}>${cap1(t)}</option>`).join('')}</select></label>
      <label>Language <input type="text" id="ailang" maxlength="40" placeholder="Auto" value="${esc(A.language)}"></label>
      <label class="chk"><input type="checkbox" id="aiemoji" ${A.emoji ? 'checked' : ''}> Emoji</label>
      <label class="chk"><input type="checkbox" id="aitags" ${A.hashtags ? 'checked' : ''}> Hashtags</label>
    </div>
    <label class="f" for="aicta">Call to action <span class="note">(optional)</span></label>
    <input type="text" id="aicta" maxlength="200" placeholder="e.g. Order in the link in bio" value="${esc(A.cta)}">
    <p class="note">${S.images.length ? `Reads ${Math.min(S.images.length, 6)} photo${S.images.length === 1 ? '' : 's'}. ` : ''}Writes for ${chosenPlatforms().map(p => PLATFORM[p]).join(', ') || 'the platforms you choose'}${
      bname ? ` in ${esc(bname.name)}'s voice${bname.voice ? '' : ' (no brand voice set yet)'}` : ''}. Replaces the caption and title below.</p>
    ${A.err ? `<div class="status err">${esc(A.err)}</div>` : ''}
    <button type="button" class="btn" id="aigo" ${A.busy || !S.targets.length ? 'disabled' : ''}>${A.busy ? 'Writing…' : 'Write it'}</button>
  </div>`;
}

async function aiWrite() {
  const A = S.ai;
  A.busy = true; A.err = ''; render();
  try {
    const r = await send('/ai/captions', 'POST', { platforms: chosenPlatforms(), image_keys: S.images.filter(m => m.key).map(m => m.key),
      brief: A.brief, tone: A.tone, length: A.length, emoji: A.emoji, hashtags: A.hashtags, cta: A.cta, language: A.language, brand_id: aiBrand() });
    const pls = chosenPlatforms();
    // TikTok's (or Facebook's) text is the main caption; the others become
    // per-platform captions where they differ, Instagram usually the short one.
    const main = ['tiktok', 'facebook', 'instagram'].find(p => pls.includes(p));
    S.caption = r.captions[main] || '';
    S.over = {};
    for (const pl of pls) if (pl !== main && r.captions[pl] && r.captions[pl] !== S.caption) S.over[pl] = r.captions[pl];
    if (r.title) S.title = r.title;
    A.remaining = r.remaining; A.open = false;
    S.status = { kind: 'ok', text: 'Written. Read it over and edit anything before posting.' };
  } catch (e) { A.err = e.message; }
  A.busy = false; render();
}

async function aiRewrite(kind) {
  const A = S.ai;
  A.busy = true; render();
  try {
    const r = await send('/ai/captions', 'POST', { mode: 'rewrite', text: S.caption, instruction: kind, brand_id: aiBrand(),
      platform: chosenPlatforms().length === 1 ? chosenPlatforms()[0] : undefined });
    S.caption = r.text; A.remaining = r.remaining;
  } catch (e) { S.status = { kind: 'err', text: e.message }; }
  A.busy = false; render();
}

// ---- posting slots and the queue -------------------------------------------

const DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const slotsOf = a => (a && S.me.brands.find(b => b.id === a.brand_id)?.slots) || S.me.workspace.slots || null;
function slotsText(sl) {
  if (!sl) return 'not set';
  const days = sl.days.length === 7 ? 'Every day' : sl.days.join() === '1,2,3,4,5' ? 'Mon–Fri' : sl.days.map(d => DAY[d]).join(', ');
  return `${days} · ${sl.times.join(', ')}`;
}

// The posts already lined up, so the queue skips taken slots.
async function loadQueue() {
  S.queuePosts = null; render();
  const from = Math.floor(Date.now() / 1000);
  try { S.queuePosts = (await api(`/posts?from=${from}&to=${from + 60 * 86400}`)).posts.filter(p => ['queued', 'publishing'].includes(p.status)); }
  catch (e) { S.queuePosts = []; S.flash = { kind: 'err', text: e.message }; }
  render();
}

// Each account's next free slot in its brand's posting times (or the
// workspace default), in the workspace's zone, at least 6 minutes ahead,
// and not within 30 minutes of another post on that account.
function queuePlan() {
  const plan = {}, taken = {};
  for (const p of S.queuePosts || []) (taken[p.account_id] ||= []).push(p.scheduled_at);
  const soonest = Date.now() / 1000 + 6 * 60, t0 = today();
  for (const id of S.targets) {
    const sl = slotsOf(acct(id));
    plan[id] = null;
    if (!sl) continue;
    for (let i = 0; i < 60 && !plan[id]; i++) {
      const day = addDays(t0, i), wd = new Date(Date.UTC(day.y, day.m - 1, day.d)).getUTCDay();
      if (!sl.days.includes(wd)) continue;
      for (const time of sl.times) {
        const [h, mi] = time.split(':').map(Number), at = Math.floor(zonedToMs(day.y, day.m, day.d, h, mi) / 1000);
        if (at < soonest || (taken[id] || []).some(x => Math.abs(x - at) < 1800)) continue;
        plan[id] = at; (taken[id] ||= []).push(at); break;
      }
    }
  }
  return plan;
}

function queuePreview() {
  if (!S.queuePosts) return '<p class="note">Finding the next free slots…</p>';
  const plan = queuePlan();
  return `<div class="qplan">${S.targets.map(id => { const a = acct(id);
    return `<div>${icon(platformOf(a), 12)} ${handle(a)}: <b>${plan[id] ? fmtFull(plan[id]) : 'no posting times set'}</b></div>`; }).join('')
    || '<span class="note">Choose accounts first.</span>'}
    <span class="note">Each account takes its next free posting time (${esc(tz().replace(/_/g, ' '))}).</span></div>`;
}

function slotsEditor(key, current, label, fallback) {
  const x = S.slotEdit;
  if (!x || x.key !== key) {
    return `<div class="slotline"><span class="note">${label}: <b>${esc(slotsText(current || fallback))}</b>${!current && fallback ? ' <em class="dflt">workspace default</em>' : ''}</span>
      ${can('admin') ? `<button class="link" data-slotedit="${key}">Edit posting times</button>` : ''}</div>`;
  }
  return `<div class="sloted">
    <div class="days">${[1, 2, 3, 4, 5, 6, 0].map(d => `<button type="button" class="chip ${x.days.includes(d) ? 'on' : ''}" data-slotday="${d}">${DAY[d]}</button>`).join('')}</div>
    <div class="times">${x.times.map((t, n) => `<span class="tm"><input type="time" value="${t}" data-slottime="${n}" aria-label="Posting time ${n + 1}">
      <button type="button" class="link" data-slotrm="${n}" aria-label="Remove">×</button></span>`).join('')}
      <button type="button" class="btn sec" id="slotadd">Add time</button></div>
    <div class="acts2"><button type="button" class="btn" id="slotsave">Save</button>
      <button type="button" class="btn sec" id="slotcancel">Cancel</button>
      ${key !== 'ws' && current ? '<button type="button" class="link" id="slotclear">Use the workspace default</button>' : ''}</div>
    <span class="note">Times are in ${esc(tz().replace(/_/g, ' '))}.</span></div>`;
}

function voiceLine(id) {
  const b = S.me.brands.find(x => x.id === id);
  if (S.voiceEdit?.id === id) {
    return `<div class="sloted"><label class="f" for="voicetext">Brand voice for AI writing</label>
      <textarea id="voicetext" maxlength="2000" placeholder="How the brand sounds, words it uses or avoids, and one or two example posts">${esc(S.voiceEdit.text)}</textarea>
      <div class="acts2"><button type="button" class="btn" id="voicesave">Save</button><button type="button" class="btn sec" id="voicecancel">Cancel</button></div></div>`;
  }
  return `<div class="slotline"><span class="note">Brand voice: <b>${b?.voice ? esc(b.voice.slice(0, 80)) + (b.voice.length > 80 ? '…' : '') : 'not set'}</b></span>
    ${S.me.ai_enabled && can('admin') ? `<button class="link" data-voice="${id}">${b?.voice ? 'Edit' : 'Add'} brand voice</button>` : ''}</div>`;
}

function openSlots(key) {
  const cur = key === 'ws' ? S.me.workspace.slots : S.me.brands.find(b => b.id === key)?.slots;
  const base = cur || S.me.workspace.slots || { days: [1, 2, 3, 4, 5], times: ['09:00', '18:00'] };
  S.slotEdit = { key, days: [...base.days], times: [...base.times] };
  render();
}

async function saveSlots(slots) {
  const key = S.slotEdit.key;
  try {
    await send(key === 'ws' ? '/workspace' : `/brands/${key}`, 'PATCH', { slots });
    S.slotEdit = null; S.flash = { kind: 'ok', text: 'Posting times saved.' };
  } catch (e) { S.flash = { kind: 'err', text: e.message }; }
  await refreshMe();
}

// ---- drafts --------------------------------------------------------------

function draftBlocker() {
  if (!S.targets.length) return 'Choose where it will go';
  if (!S.images.length && !S.video) return 'Add photos or a video';
  if (S.images.some(m => m.uploading) || S.video?.uploading) return 'Waiting for uploads to finish';
  return '';
}

const newGroup = () => 'grp_' + [...crypto.getRandomValues(new Uint8Array(8))].map(b => b.toString(16).padStart(2, '0')).join('');

// A draft is one row per account, sharing a group, each with its own caption.
async function saveDraft() {
  if (draftBlocker() || S.busy) return;
  S.busy = true; S.status = { kind: '', text: 'Saving draft…' }; render();
  const jobs = S.targets.map(id => ({ id, platform: platformOf(acct(id)) }));
  const group = newGroup(), errors = [];
  try {
    const keys = S.video ? jobs.map(() => []) : await keysFor(jobs.map(j => j.platform), { raw: true });
    for (const [n, j] of jobs.entries()) {
      const t = S.tt[j.id] || {};
      try {
        await send('/posts', 'POST', { account_id: j.id, image_keys: keys[n], video_key: S.video?.key, cover_index: S.cover, title: S.video ? '' : S.title,
          caption: captionFor(j.platform), draft: true, group_id: group, folder_id: S.fromFolder || undefined,
          settings: j.platform !== 'tiktok' ? {} : ttSettings(t, t.privacy || '') });
      } catch (e) { errors.push(`${handle(acct(j.id))}: ${e.message}`); }
    }
  } catch (e) { errors.push(e.message); }
  S.busy = false;
  if (errors.length) { S.status = { kind: 'err', text: errors.join(' · ') }; return render(); }
  if (S.fromDraft) await dropDrafts(S.fromDraft);
  resetComposer();
  S.flash = { kind: 'ok', text: 'Draft saved.' }; S.keepFlash = true;
  location.hash = '#drafts';
}

async function dropDrafts(ids) {
  for (const id of ids) { try { await send(`/posts/${id}`, 'DELETE'); } catch {} }
}

async function loadDrafts() {
  try { S.drafts = (await api('/drafts')).drafts; S.counts.drafts = draftGroups().length; } catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}

// The menu's counts (drafts waiting, posts failed this week), kept fresh
// whichever page is open.
async function refreshCounts() {
  const now = Math.floor(Date.now() / 1000);
  try {
    const [d, p] = await Promise.all([api('/drafts'), api(`/posts?from=${now - 7 * 86400}&to=${now + 60}`)]);
    const groups = new Set(d.drafts.map(x => x.group_id || x.id));
    S.counts = { drafts: groups.size, failed: p.posts.filter(x => x.status === 'failed').length };
    if (S.me && !S.me.needs_email) $('side').innerHTML = menu();
  } catch {}
}
const reloadView = () => (S.view === 'overview' ? loadOverview() : loadWeek());

// Drafts saved together come back as one card.
function draftGroups() {
  const groups = new Map();
  for (const d of S.drafts) {
    const k = d.group_id || d.id;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(d);
  }
  return [...groups.values()];
}

function draftsView() {
  const b = curBrand(), groups = draftGroups().filter(g => g.some(d => inBrand(acct(d.account_id), b)));
  if (!groups.length) return `<section class="panel empty"><b>No drafts${b === 'all' ? '' : ` for ${esc(brandLabel(b))}`}.</b>Use "Save draft" while creating a post to keep it for later.
    <div><a class="btn" href="#compose">${ui('plus', 16)}Create post</a></div></section>`;
  const ai = groups.filter(g => g[0].source === 'ai'), own = groups.filter(g => g[0].source !== 'ai');
  const list = gs => `<div class="list drafts">${gs.map(g => {
    const d = g[0], cover = thumbOf(d), key = esc(d.group_id || d.id), isAi = d.source === 'ai';
    const due = isAi && d.scheduled_at > Date.now() / 1000;
    return `<div class="drow ${S.approving === key ? 'open' : ''}" data-opendraft="${key}" role="button" tabindex="0">
      ${cover ? pic(cover, 'class="thumb" alt=""') : '<span class="noimg"></span>'}
      <div class="wh"><b>${isAi ? '<em class="aib">AI</em>' : ''}${esc(d.caption || d.title || 'No caption yet')}</b>
        <span>${g.length === 1 ? who(g[0]) : `${g.length} accounts`} · ${d.video ? 'Video' : `${d.images.length} photo${d.images.length === 1 ? '' : 's'}`} · ${isAi
          ? (due ? `planned for ${fmt(d.scheduled_at, { weekday: 'short', day: 'numeric', month: 'short' })} ${at(d.scheduled_at)}` : '<span class="late">planned time has passed</span>')
          : `saved ${fmt(d.updated_at, { month: 'short', day: 'numeric' })}`}</span></div>
      <span class="dacc">${g.slice(0, 4).map(x => withBadge(avatar(acct(x.account_id)?.avatar_url, x.username), x.platform || 'tiktok')).join('')}</span>
      ${isAi && due ? `<button class="btn sm" data-approve="${key}">Approve</button>` : ''}
      <button class="btn sec sm" data-opendraft="${key}">${isAi ? 'Edit' : 'Open'}</button>
      <button class="btn ghost danger sm" data-deldraft="${key}" aria-label="Delete draft">${ui('x', 14)}</button></div>
      ${S.approving === key ? approvePanel(g) : ''}`;
  }).join('')}</div>`;
  return `${ai.length ? `<section class="panel"><header><h2>From AI, waiting for approval</h2><span class="note">${ai.length} post${ai.length === 1 ? '' : 's'} · they go out only after you approve them</span>
      ${ai.length > 1 ? `<span class="hacts"><button class="btn sec" id="approveall">Approve all</button></span>` : ''}</header>${list(ai)}</section>` : ''}
    ${own.length ? `<div class="panel">${ai.length ? '<header><h2>Your drafts</h2></header>' : ''}${list(own)}</div>` : ''}`;
}

// Approving an AI draft: it goes out at its planned time; TikTok asks who
// can see it, every time, as its rules require.
function approvePanel(g) {
  const tts = g.filter(x => x.platform === 'tiktok'), key = esc(g[0].group_id || g[0].id);
  return `<div class="apanel" data-stop="1"><p>Goes out <b>${fmt(g[0].scheduled_at, { weekday: 'long', day: 'numeric', month: 'short' })} at ${at(g[0].scheduled_at)}</b> to ${g.map(x => who(x)).join(', ')}.</p>
    ${tts.map(x => `<label class="f" for="apv-${x.id}">Who can see it on TikTok ${who(x)}</label>
      <select id="apv-${x.id}" data-apriv="${x.id}"><option value="">Choose…</option>${Object.entries(PRIVACY_LABEL).map(([k, l]) => `<option value="${k}" ${x.settings?.privacy_level === k ? 'selected' : ''}>${l}</option>`).join('')}</select>`).join('')}
    <div class="aacts"><button class="btn ghost" id="apcancel">Cancel</button><button class="btn" data-apgo="${key}">Approve ${g.length > 1 ? `${g.length} posts` : 'post'}</button></div></div>`;
}

async function approveGroup(g, privacy = {}) {
  const errs = [];
  for (const x of g) {
    try { await send(`/posts/${x.id}/approve`, 'POST', x.platform === 'tiktok' ? { privacy_level: privacy[x.id] || x.settings?.privacy_level || undefined } : {}); }
    catch (e) { errs.push(`${PLATFORM[x.platform]} ${handle(x)}: ${e.message}`); }
  }
  return errs;
}

function openDraft(key) {
  const g = draftGroups().find(x => (x[0].group_id || x[0].id) === key);
  if (!g) return;
  resetComposer();
  // Photos from a non-Instagram copy when there is one: Instagram's may be padded.
  const src = g.find(x => x.platform !== 'instagram') || g[0];
  // The main caption is the one most copies share; on a tie, TikTok's, then
  // Facebook's, since Instagram is the one people usually shorten.
  const counts = {}, rank = { tiktok: 0, facebook: 1, instagram: 2 };
  for (const x of g) counts[x.caption] = (counts[x.caption] || 0) + 1;
  const main = [...g].sort((a, b) => (counts[b.caption] - counts[a.caption]) || (rank[a.platform] - rank[b.platform]))[0].caption;
  const tt = g.find(x => x.platform === 'tiktok');
  Object.assign(S, { images: src.image_keys.map((k, n) => ({ key: k, url: src.images[n] })), cover: src.cover_index,
    caption: main, title: (tt || src).title || '', fromDraft: g.map(x => x.id), draftGroup: key, targets: [],
    video: src.video_key ? { key: src.video_key, url: src.video } : null, fromFolder: src.folder_id || null });
  if (src.source === 'ai' && src.scheduled_at > Date.now() / 1000 + 6 * 60) { S.when = 'later'; S.at = localInput(src.scheduled_at * 1000); }
  for (const x of g) if (x.caption !== main) S.over[x.platform] = x.caption;
  const s = tt?.settings || {};
  S.set = { music: !!s.auto_add_music, duet: s.disable_duet === false, stitch: s.disable_stitch === false,
    disclose: !!(s.brand_organic || s.branded_content), brand: !!s.brand_organic, branded: !!s.branded_content };
  for (const x of g) {
    toggleTarget(x.account_id, true, false);
    if (x.platform === 'tiktok' && S.tt[x.account_id]) S.tt[x.account_id].comment = !x.settings?.disable_comment;
  }
  location.hash = '#compose';
  render();
}

// ---- calendar ----------------------------------------------------------

// ---- calendar: week or month, in the workspace's zone; drag to reschedule --

function calRange() {
  const t = today();
  if (S.calMode === 'month') {
    let y = t.y, m = t.m + S.month;
    while (m < 1) { m += 12; y--; } while (m > 12) { m -= 12; y++; }
    const first = { y, m, d: 1 };
    const wd = new Date(Date.UTC(y, m - 1, 1)).getUTCDay();
    const start = addDays(first, -((wd + 6) % 7));
    return { start, n: 42, month: m, title: dayLabel(first, { month: 'long', year: 'numeric' }) };
  }
  const wd = new Date(Date.UTC(t.y, t.m - 1, t.d)).getUTCDay();
  const start = addDays(t, -((wd + 6) % 7) + S.week * 7);
  const n = S.calMode === 'weeks' ? 28 : 7;
  const end = addDays(start, n - 1);
  return { start, n, title: `${dayLabel(start, { day: 'numeric', month: 'short' })} – ${dayLabel(end, { day: 'numeric', month: 'short' })}` };
}

async function loadWeek() {
  const r = calRange();
  const from = Math.floor(zonedToMs(r.start.y, r.start.m, r.start.d) / 1000);
  const endDay = addDays(r.start, r.n);
  const to = Math.floor(zonedToMs(endDay.y, endDay.m, endDay.d) / 1000);
  try { S.posts = (await api(`/posts?from=${from}&to=${to}`)).posts; }
  catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}

// Which brand a post is for, as a coloured dot, so brands stay apart on the calendar.
const bdot = p => { const id = acct(p.account_id)?.brand_id; return id && brandName(id) ? `<i class="bdot" style="background:${brandHue(id)}" title="${esc(brandName(id))}"></i>` : ''; };
function postCard(p, compact) {
  const time = fmt(p.scheduled_at, { hour: '2-digit', minute: '2-digit' });
  const drag = p.status === 'queued' ? `draggable="true" data-drag="${p.id}"` : '';
  if (compact) {
    return `<div class="mp ${p.status}" ${drag} data-open="${p.id}" role="button" tabindex="0"
        title="${esc(`${PLATFORM[p.platform] || 'TikTok'} · ${p.username} · ${p.status}${p.fail_reason ? `: ${p.fail_reason}` : ''}`)}">
      ${thumb(p) || '<span class="noimg"></span>'}<div><b>${icon(p.platform || 'tiktok', 11)}${at(p.scheduled_at)}</b><span>${bdot(p)}${p.platform === 'facebook' ? '' : '@'}${esc(p.username)}</span></div></div>`;
  }
  // Week view: a small row per post. Everything you can do with it is one
  // click away in the drawer.
  const label = { published: 'Published', failed: 'Failed', queued: 'Scheduled', publishing: 'Posting', cancelled: 'Cancelled' }[p.status] || p.status;
  return `<div class="pc ${p.status}" ${drag} data-open="${p.id}" role="button" tabindex="0"
      title="${esc(`${label}${p.fail_reason ? `: ${p.fail_reason}` : ''}`)}">
    ${thumb(p) || '<span class="noimg"></span>'}
    <div class="pt"><b>${icon(p.platform || 'tiktok', 12)}${at(p.scheduled_at)}</b>
      <span>${bdot(p)}${who(p)}</span>
      <em>${label}</em></div></div>`;
}

function calendarView() {
  const r = calRange(), month = S.calMode === 'month', grid = S.calMode !== 'week';
  const accts = S.me.accounts;
  const plats = ORDER.filter(pl => accts.some(a => platformOf(a) === pl));
  const posts = S.posts.filter(p => (S.fPlat === 'all' || (p.platform || 'tiktok') === S.fPlat)
    && (S.fAcct === 'all' || p.account_id === S.fAcct)
    && inBrand(acct(p.account_id), curBrand()));
  const shown = accts.filter(a => (S.fPlat === 'all' || platformOf(a) === S.fPlat)
    && inBrand(a, curBrand()));
  const days = [...Array(r.n)].map((_, i) => addDays(r.start, i));
  const now = dayKey(today()), offset = month ? S.month : S.week;
  const empty = !posts.length;
  const legend = S.me.brands.length && curBrand() === 'all' ? `<span class="legend">${S.me.brands.map(x => `<span><i style="background:${brandHue(x.id)}"></i>${esc(x.name)}</span>`).join('')}</span>` : '';
  const filters = accts.length ? `<div class="chips">${legend}
      <button class="chip ${S.fPlat === 'all' ? 'on' : ''}" data-fp="all">All platforms</button>
      ${plats.map(pl => `<button class="chip ${S.fPlat === pl ? 'on' : ''}" data-fp="${pl}">${icon(pl, 13)}${PLATFORM[pl]}</button>`).join('')}
      ${shown.length > 1 ? `<select id="facct" style="width:auto;padding:5px 10px">
        <option value="all">All accounts</option>
        ${shown.map(a => `<option value="${a.id}" ${S.fAcct === a.id ? 'selected' : ''}>${PLATFORM[platformOf(a)]} · ${handle(a)}</option>`).join('')}
      </select>` : ''}
    </div>` : '';
  return `${filters}
    <div class="calbar">
      <span class="navg"><button class="btn sec" data-wk="-1" aria-label="Previous">‹</button>
      <button class="btn sec" data-wk="1" aria-label="Next">›</button></span>
      <b class="ctitle">${r.title}</b>
      ${offset ? '<button class="btn ghost" data-today>Today</button>' : ''}
      <span class="seg">${[['week', 'Week'], ['weeks', '4 weeks'], ['month', 'Month']].map(([k, l]) =>
        `<button class="${S.calMode === k ? 'on' : ''}" data-mode="${k}">${l}</button>`).join('')}</span>
      <span class="note">${esc(tz().replace(/_/g, ' '))}</span>
    </div>
    ${empty ? `<div class="calempty">${ui('cal', 18)}<span>Nothing scheduled here yet. Click a day to create a post for it.</span></div>` : ''}
    ${grid ? `<div class="monthhead">${days.slice(0, 7).map(d => `<span>${dayLabel(d, { weekday: 'short' })}</span>`).join('')}</div>` : ''}
    <div class="${grid ? 'month' : 'week'}">${days.map((d, i) => {
      const ps = posts.filter(p => dayOf(p.scheduled_at) === dayKey(d)).sort((a, b) => a.scheduled_at - b.scheduled_at);
      const out = month && d.m !== r.month, past = ymd(d) < ymd(today());
      const label = grid ? (d.d === 1 || i === 0 ? dayLabel(d, { month: 'short', day: 'numeric' }) : d.d) : `<span>${dayLabel(d, { weekday: 'short' })}</span><b>${d.d}</b>`;
      return `<div class="day ${dayKey(d) === now ? 'today' : ''} ${out ? 'out' : ''} ${past ? 'past' : 'open'}" data-day="${d.y}-${d.m}-${d.d}" ${past ? '' : `tabindex="0" role="button" aria-label="Create a post for ${dayLabel(d, { weekday: 'long', month: 'long', day: 'numeric' })}" title="Create a post for this day"`}>
        <h4>${label}</h4>
        ${ps.slice(0, grid ? 4 : 99).map(p => postCard(p, grid)).join('')}${grid && ps.length > 4 ? `<button class="more" data-moreday="${d.y}-${d.m}-${d.d}">+${ps.length - 4} more</button>` : ''}
      </div>`;
    }).join('')}</div>`;
}

// The whole post, from the calendar: photos, every word of the caption, what
// happened, and what can still be done. A post that has not started can have
// its caption fixed right here.
function detailView() {
  const p = S.posts.find(x => x.id === S.detail) || (S.stats?.posts || S.stats?.top)?.find(x => x.id === S.detail);
  if (!p) return '';
  const a = acct(p.account_id), editable = p.status === 'queued', pl = p.platform || 'tiktok';
  const label = { published: 'Published', failed: 'Failed', queued: 'Scheduled', publishing: 'Posting', cancelled: 'Cancelled' }[p.status] || p.status;
  const cover = p.images[p.cover_index] || p.images[0];
  return `<div class="overlay" id="overlay"><aside class="drawer" role="dialog" aria-modal="true" aria-label="Post">
    <header class="dh">${withBadge(avatar(a?.avatar_url, p.username), pl)}
      <div><b>${pl === 'facebook' ? '' : '@'}${esc(p.username)}</b><span>${PLATFORM[pl]}</span></div>
      <button class="xbtn" id="closedetail" aria-label="Close">${ui('x', 18)}</button></header>
    <div class="dscroll">
      <div class="dwhen"><span class="st ${p.status === 'queued' ? 'queued' : p.status}">${label}</span>
        <b>${fmt(p.scheduled_at, { weekday: 'long', month: 'short', day: 'numeric' })} · ${at(p.scheduled_at)}</b>
        <small>${esc(tz().replace(/_/g, ' '))}</small></div>
      ${p.fail_reason ? `<div class="dfail">${ui('x', 15)}<span>${esc(p.fail_reason)}</span></div>` : ''}
      ${p.stats ? `<div class="dstats">${STAT_KEYS.filter(k => p.stats[k] != null).map(k => `<div><b>${num(p.stats[k])}</b><span>${METRIC[k]}</span></div>`).join('')}</div>` : ''}
      ${p.video ? `<div class="dmedia"><video class="big" src="${esc(p.video)}" poster="${esc(p.video)}.jpg" controls preload="none" playsinline></video></div>`
        : cover ? `<div class="dmedia"><img class="big" src="${esc(cover)}" alt="Cover">
        ${p.images.length > 1 ? `<div class="dthumbs">${p.images.map((u, n) => `<img src="${esc(u)}" alt="Photo ${n + 1}" class="${n === p.cover_index ? 'cv' : ''}">`).join('')}</div>` : ''}</div>`
        : `<p class="note">${['published', 'failed', 'cancelled'].includes(p.status) ? 'The photos were deleted 7 days after the post finished.' : 'No photos.'}</p>`}
      ${p.title ? `<p class="dtitle">${esc(p.title)}</p>` : ''}
      <label class="f" for="dcap">Caption</label>
      ${editable ? `<textarea id="dcap">${esc(p.caption)}</textarea>`
        : `<p class="cap-full">${esc(p.caption) || '<span class="note">No caption</span>'}</p>`}
    </div>
    <footer class="df">
      ${editable ? `<button class="btn" id="savecap">Save caption</button><button class="btn sec" data-edit="${p.id}">Open in editor</button>
        <button class="btn ghost danger" data-cancel="${p.id}">Cancel post</button>` : ''}
      ${p.status === 'failed' ? `<button class="btn" data-retry="${p.id}">Retry</button><button class="btn sec" data-edit="${p.id}">Edit</button>` : ''}
      ${p.status === 'published' || p.status === 'cancelled' ? `<button class="btn sec" data-again="${p.id}">Post again</button>` : ''}
      ${p.post_url ? `<a class="btn ${p.status === 'published' ? '' : 'sec'}" href="${esc(p.post_url)}" target="_blank" rel="noopener">View live post</a>` : ''}
    </footer></aside></div>`;
}

// Dropping a post on another day keeps its time of day, in the workspace's zone.
async function movePost(id, dayStr) {
  const p = S.posts.find(x => x.id === id);
  if (!p) return;
  const [y, m, d] = dayStr.split('-').map(Number), t = zoned(p.scheduled_at * 1000);
  const at = Math.floor(zonedToMs(y, m, d, t.h, t.mi) / 1000);
  if (at === p.scheduled_at) return;
  try {
    await send(`/posts/${id}`, 'PATCH', { scheduled_at: at });
    S.flash = { kind: 'ok', text: `Moved to ${fmtFull(at)}.` };
  } catch (e) { S.flash = { kind: 'err', text: e.message }; }
  loadWeek();
}

// Edit (a queued or failed post) or Post again (a finished one): the post's
// content and account come back into the composer, and more accounts can be
// added to it. Privacy is chosen again on purpose: the options come from
// TikTok now, not from when the post was first made.
async function edit(id, again = false) {
  const p = S.posts.find(x => x.id === id);
  if (!p) return;
  resetComposer();
  S.replaces = !again && p.status === 'queued' ? p.id : null;
  S.replacesAccount = p.account_id;
  const images = again ? [] : p.image_keys.map((k, n) => ({ key: k, url: p.images[n] }));
  Object.assign(S, { images, cover: again ? 0 : p.cover_index, title: p.title, caption: p.caption,
    video: p.video_key ? { key: p.video_key, url: p.video } : null,
    when: again ? 'now' : 'later', at: localInput(Math.max(p.scheduled_at * 1000, Date.now() + 10 * 60e3)) });
  const s = p.settings || {};
  S.set = { music: !!s.auto_add_music, duet: s.disable_duet === false, stitch: s.disable_stitch === false,
            disclose: !!(s.brand_organic || s.branded_content), brand: !!s.brand_organic, branded: !!s.branded_content };
  S.targets = [];
  toggleTarget(p.account_id, true, false);
  if (S.tt[p.account_id]) S.tt[p.account_id].comment = !s.disable_comment;
  location.hash = '#compose';
  render();
  if (again && !p.video_key) {
    // Images live for 7 days after a post is done; copy them while they do.
    try {
      const { media } = await api('/media/copy', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keys: p.image_keys }) });
      S.images = media.map(m => ({ key: m.key, url: m.url })); S.cover = p.cover_index;
    } catch { S.status = { kind: '', text: 'The photos of that post were already deleted. Caption copied; add the photos again.' }; }
    render();
  }
}

// ---- settings ----------------------------------------------------------

// ---- accounts manager: brands as cards, each holding its accounts.

const PLATFORM_HINT = {
  tiktok: 'TikTok connects the account signed in on tiktok.com. For another one, switch accounts on TikTok\'s screen or sign out of tiktok.com first.',
  instagram: 'Any professional (Business or Creator) account, no Facebook Page needed. Instagram asks for the login each time, so you can add accounts one after another.',
  facebook: 'Pick every Page you manage on Facebook\'s screen. Pages connected before stay connected.',
};
const connectHref = pl => pl === 'tiktok' ? '/api/auth/start?add=1'
  : pl === 'instagram' ? (S.me.instagram_enabled ? '/api/auth/instagram/start?add=1' : '')
  : (S.me.facebook_enabled ? '/api/auth/meta/start?add=1' : '');

function accountCard(x) {
  const pl = platformOf(x);
  return `<div class="acard ${x.needs_reconnect ? 'bad' : ''}">
    <div class="atop">${withBadge(avatar(x.avatar_url, x.username || x.display_name), pl)}
      <div class="aname"><b>${handle(x)}</b><span>${PLATFORM[pl]}${x.display_name && x.display_name !== x.username ? ` · ${esc(x.display_name)}` : ''}</span></div>
      <span class="state ${x.needs_reconnect ? 'bad' : 'ok'}">${x.needs_reconnect ? 'Reconnect' : 'Connected'}</span></div>
    ${x.needs_reconnect ? '<p class="awarn">Access expired or was removed. Reconnect to keep posting.</p>' : ''}
    <div class="aact">
      <select data-move="${x.id}" aria-label="Brand for ${esc(x.username)}">
        <option value="">Personal</option>
        ${S.me.brands.map(b => `<option value="${b.id}" ${x.brand_id === b.id ? 'selected' : ''}>${esc(b.name)}</option>`).join('')}
      </select>
      ${x.needs_reconnect && connectHref(pl) ? `<a class="btn" href="${connectHref(pl)}">Reconnect</a>` : ''}
      <button class="btn ghost danger" data-disc="${x.id}">Disconnect</button></div></div>`;
}

// One row per account; a small menu moves it, takes it out of the brand, or disconnects it.
function acctRow(x, brandId) {
  const pl = platformOf(x), others = S.me.brands.filter(b => b.id !== brandId);
  return `<div class="brow2 ${x.needs_reconnect ? 'bad' : ''}">${withBadge(avatar(x.avatar_url, x.username || x.display_name), pl)}
    <div class="aname"><b>${handle(x)}</b><span>${x.needs_reconnect ? '<em class="st bad">Reconnect needed</em>' : `${PLATFORM[pl]}${x.display_name && x.display_name !== x.username ? ` · ${esc(x.display_name)}` : ''}`}</span></div>
    ${x.needs_reconnect && connectHref(pl) ? `<a class="btn sm" href="${connectHref(pl)}">Reconnect</a>` : ''}
    <label class="amenu" title="Manage ${esc(x.username || '')}">${ui('more', 16)}<select data-amenu="${x.id}" aria-label="Manage ${esc(x.username || 'account')}"><option value="" selected disabled hidden></option>
      ${others.length ? `<optgroup label="${brandId ? 'Move to' : 'Add to brand'}">${others.map(b => `<option value="b:${b.id}">${esc(b.name)}</option>`).join('')}</optgroup>` : ''}
      ${brandId ? '<option value="out">Remove from brand</option>' : ''}<option value="disc">Disconnect…</option></select></label></div>`;
}

// Add buttons per brand: one app icon per platform, each connects a new
// account straight into that brand. Moving an existing one is in its own menu.
function addButtons(brandId) {
  const pls = ORDER.filter(connectHref);
  return pls.length ? `<div class="badds"><span class="note">Add</span>${pls.map(pl => `<a class="bplat" href="${connectHref(pl)}" data-cbrand="${brandId || 'none'}" title="Connect a ${PLATFORM[pl]} account${brandId ? ` to ${esc(brandName(brandId))}` : ''}. ${esc(PLATFORM_HINT[pl])}" aria-label="Connect a ${PLATFORM[pl]} account">${appIcon(pl, 26)}<span class="bplus">${ui('plus', 10)}</span></a>`).join('')}</div>` : '';
}

async function renameBrand(id) {
  const name = await ask({ title: 'Rename brand', ok: 'Save', input: { value: brandName(id) || '', label: 'Brand name' } });
  if (name && name !== brandName(id)) brandAction(() => send(`/brands/${id}`, 'PATCH', { name }));
}
async function deleteBrand(id) {
  if (await ask({ title: `Delete the brand ${esc(brandName(id))}?`, ok: 'Delete brand', danger: true, icon: ui('users', 22),
    list: [[true, 'Its accounts stay connected, just not grouped'], [true, 'Scheduled posts still go out'], [false, 'Its posting times and brand voice are removed']] }))
    brandAction(() => send(`/brands/${id}`, 'DELETE'));
}
async function disconnectAcct(id) {
    const a = acct(id), pl = platformOf(a), t = Math.floor(Date.now() / 1000);
    let n = null;
    try { n = (await api(`/posts?from=${t}&to=${t + 62 * 86400}`)).posts.filter(p => p.account_id === id && p.status === 'queued').length; } catch {}
    const ok = await ask({ title: `Disconnect ${handle(a)}?`, ok: 'Disconnect', danger: true,
      icon: withBadge(avatar(a.avatar_url, a.username || a.display_name), pl),
      body: `ARCO Publisher stops posting to this ${PLATFORM[pl]} account.`,
      list: [[false, n ? `${n} scheduled post${n === 1 ? ' is' : 's are'} cancelled` : 'Any scheduled posts are cancelled'],
        [true, `Posts already published stay on ${PLATFORM[pl]}`], [true, 'You can connect it again any time']] });
    if (!ok) return;
    await api(`/accounts/${id}`, { method: 'DELETE' }); S.me = await api('/me');
    S.targets = S.targets.filter(x => x !== id); saveTargets(); render();
  }

function accountsView() {
  const a = S.me.accounts, cb = curBrand();
  const loose = a.filter(x => !brandName(x.brand_id));
  const brands = [...S.me.brands].sort((x, y) => (y.id === cb) - (x.id === cb));
  const byPl = list => list.sort((x, y) => ORDER.indexOf(platformOf(x)) - ORDER.indexOf(platformOf(y)) || String(x.username).localeCompare(String(y.username)));
  const mix = list => `<span class="bmix">${ORDER.map(pl => [pl, list.filter(x => platformOf(x) === pl).length]).filter(([, n]) => n).map(([pl, n]) => `<span title="${PLATFORM[pl]}">${icon(pl, 12)}${n}</span>`).join('')}</span>`;
  const card = b => {
    const list = byPl(a.filter(x => x.brand_id === b.id));
    return `<section class="bcard">
      <header><span class="bsq big" style="background:${brandHue(b.id)}">${esc((b.name[0] || '?').toUpperCase())}</span>
        <div class="bt"><h2>${esc(b.name)}</h2><span class="note">${list.length ? `${list.length} account${list.length === 1 ? '' : 's'}` : 'No accounts yet'}</span></div>${mix(list)}
        <label class="amenu" title="Brand options">${ui('more', 16)}<select data-bmenu="${b.id}" aria-label="Options for ${esc(b.name)}"><option value="" selected disabled hidden></option><option value="rename">Rename</option><option value="settings">Posting times &amp; voice</option><option value="delete">Delete brand…</option></select></label></header>
      <div class="blist">${list.map(x => acctRow(x, b.id)).join('') || '<p class="bnone">Add its TikTok, Instagram or Facebook below. Scheduling for this brand then picks them all at once.</p>'}</div>
      <footer>${addButtons(b.id)}</footer></section>`;
  };
  return `${!S.me.brands.length && a.length ? `<div class="bhint">${ui('users', 16)}<span>Make a brand for each business you post for, then add its TikTok, Instagram and Facebook to it. Scheduling for a brand then picks all of them at once.</span></div>` : ''}
    <div class="acc2"><div class="bgrid">
      ${brands.map(card).join('')}
      ${loose.length || !S.me.brands.length || a.length ? `<section class="bcard loose"><header><span class="bsq big none">${ui('users', 16)}</span><div class="bt"><h2>${S.me.brands.length ? 'Personal' : 'Your accounts'}</h2><span class="note">${!loose.length ? 'No accounts' : S.me.brands.length ? 'In no brand yet' : `${loose.length} account${loose.length === 1 ? '' : 's'}`}</span></div>${mix(loose)}</header>
        <div class="blist">${byPl(loose).map(x => acctRow(x, null)).join('') || `<p class="bnone">${S.me.brands.length ? 'Accounts that aren\'t in a brand show here. Connect one below, or pick "Remove from brand" in an account\'s menu.' : 'Connect your TikTok, Instagram or Facebook below.'}</p>`}</div>
        <footer>${addButtons(null)}</footer></section>` : ''}
    </div></div>`;
}

const SET_TABS = () => [['workspace', 'Workspace'], ...(can('admin') && S.me.brands.length ? [['brands', 'Brands']] : []), ...(can('admin') ? [['people', 'People']] : []), ['account', 'Your account'], ...(can('owner') ? [['developer', 'Developer']] : [])];
const srow = (label, desc, control) => `<div class="srow"><div class="sl"><b>${label}</b>${desc ? `<span>${desc}</span>` : ''}</div><div class="sc">${control}</div></div>`;

function settingsView() {
  const w = S.me.workspace, owner = can('owner'), admin = can('admin');
  if (admin && S.members === null) loadMembers();
  const tabs = SET_TABS(), tab = tabs.some(t => t[0] === S.setTab) ? S.setTab : 'workspace';
  const brandPick = (name, chosen) => S.me.brands.length ? `<div class="scope">
      <label><input type="radio" name="${name}" value="all" ${!chosen ? 'checked' : ''}> All brands</label>
      <label><input type="radio" name="${name}" value="some" ${chosen ? 'checked' : ''}> Only</label>
      ${S.me.brands.map(b => `<label class="bchk"><input type="checkbox" data-scope="${name}" value="${b.id}" ${chosen?.includes(b.id) ? 'checked' : ''}> ${esc(b.name)}</label>`).join('')}
    </div>` : '';
  const m = S.members;
  const nav = `<div class="stabs" role="tablist">${tabs.map(([k, l]) => `<button role="tab" aria-selected="${k === tab}" class="${k === tab ? 'on' : ''}" data-settab="${k}">${l}</button>`).join('')}</div>`;
  let body = '';
  if (tab === 'workspace') body = `<section class="panel">
    ${admin ? srow('Name', 'Shown in the menu and in invites.', `<form id="wsname" class="inline"><input type="text" id="wsnamein" maxlength="60" value="${esc(w.name)}" aria-label="Workspace name"><button class="btn sec">Save</button></form>`)
      + srow('Time zone', 'Every scheduled time and the calendar use it.', `<select id="wstz"><option value="">Each person's own (${esc(Intl.DateTimeFormat().resolvedOptions().timeZone)})</option>
          ${(Intl.supportedValuesOf ? Intl.supportedValuesOf('timeZone') : []).map(z => `<option value="${z}" ${w.timezone === z ? 'selected' : ''}>${z.replace(/_/g, ' ')}</option>`).join('')}</select>`)
      + srow('Posting times', '"Add to queue" uses these for accounts whose brand has none.', slotsEditor('ws', w.slots, 'Default'))
      : srow('Workspace', '', `<b>${esc(w.name)}</b> · ${esc(tz().replace(/_/g, ' '))}`)}
    ${srow('Your workspaces', 'Keep clients fully separate. Nothing is shared between workspaces.', `<div class="wslist">${(S.me.workspaces || []).map(x =>
        `<div class="wsrow"><span>${esc(x.name)}${x.id === w.id ? ' <em>Current</em>' : ''}</span>${x.id !== w.id ? `<button class="btn sec" data-switch="${x.id}">Open</button>` : ''}</div>`).join('')}
      <form id="newws" class="inline"><input type="text" id="newwsname" maxlength="60" placeholder="New workspace name"><button class="btn sec">Create</button></form></div>`)}
    ${w.role !== 'owner' ? srow('Leave workspace', 'You lose access to its accounts and posts.', `<button class="btn ghost danger" data-remove="${S.me.user?.id}" data-leave="1">Leave</button>`) : ''}
    ${owner ? srow('Delete workspace', 'Removes its accounts, brands, posts, images and members now. This cannot be undone.', '<button class="btn danger" id="delws">Delete workspace</button>') : ''}
  </section>`;
  if (tab === 'people') body = `<section class="panel">
    ${!m ? `<div class="plist">${skRows(2)}</div>` : `<div class="plist">
      ${m.members.map(x => `<div class="prow2"><span class="av-me">${esc(x.email[0].toUpperCase())}</span>
        <div class="pn"><b>${esc(x.email)}${x.user_id === S.me.user?.id ? ' <em>You</em>' : ''}</b>
          <span>${x.role === 'owner' ? 'Owner' : x.role === 'admin' ? 'Admin' : x.brand_ids
            ? `Member · ${x.brand_ids.map(id => esc(S.me.brands.find(b => b.id === id)?.name || 'removed brand')).join(', ')}` : 'Member · all brands'}</span></div>
        ${x.role !== 'owner' && x.user_id !== S.me.user?.id ? `<div class="pa"><select data-role="${x.user_id}" aria-label="Role for ${esc(x.email)}">
            <option value="member" ${x.role === 'member' ? 'selected' : ''}>Member</option><option value="admin" ${x.role === 'admin' ? 'selected' : ''}>Admin</option></select>
          ${x.role === 'member' && S.me.brands.length ? `<button class="btn sec" data-editscope="${x.user_id}">Brands</button>` : ''}
          ${owner ? `<button class="btn ghost" data-transfer="${x.user_id}" data-email="${esc(x.email)}">Make owner</button>` : ''}
          <button class="btn ghost danger" data-remove="${x.user_id}">Remove</button></div>` : ''}
        ${S.editScope === x.user_id ? `<div class="pscope">${brandPick('sc-' + x.user_id, x.brand_ids)}<button class="btn" data-savescope="${x.user_id}">Save access</button></div>` : ''}
      </div>`).join('')}
      ${m.invites.map(x => `<div class="prow2"><span class="av-me pend">${esc(x.email[0].toUpperCase())}</span>
        <div class="pn"><b>${esc(x.email)} <em>Invited</em></b><span>${x.role === 'admin' ? 'Admin' : 'Member'}${x.brand_ids ? ` · ${x.brand_ids.length} brand${x.brand_ids.length === 1 ? '' : 's'}` : ''} · expires ${fmt(x.expires_at, { dateStyle: 'medium' })}</span></div>
        <div class="pa"><button class="btn ghost" data-uninvite="${x.id}">Cancel invite</button></div></div>`).join('')}</div>
      <form id="inviteform" class="invite2"><b>Invite someone</b>
        <div class="irow"><input type="email" id="invemail" required placeholder="teammate@company.com" aria-label="Email to invite">
          <select id="invrole" aria-label="Role"><option value="member">Member</option><option value="admin">Admin</option></select>
          <button class="btn">Send invite</button></div>
        ${brandPick('inv', null)}
        <p class="note"><b>Admins</b> connect accounts, manage brands and invite people. <b>Members</b> post and schedule, and can be limited to some brands: they never see the others.</p>
      </form>`}</section>`;
  if (tab === 'brands') body = S.me.brands.map(x => `<section class="panel"><header><span class="bsq big" style="background:${brandHue(x.id)}">${esc((x.name[0] || '?').toUpperCase())}</span><h2>${esc(x.name)}</h2>
      <span class="note">${marks(brandAccounts(x.id))} ${brandAccounts(x.id).length} account${brandAccounts(x.id).length === 1 ? '' : 's'}</span></header>
      <div class="bmeta">${slotsEditor(x.id, x.slots, 'Posting times', S.me.workspace.slots)}${voiceLine(x.id)}</div></section>`).join('')
    + '<p class="foot-note">A brand without its own posting times uses the workspace default from the Workspace tab. The voice guides Write with AI.</p>';
  if (tab === 'account') body = `<section class="panel">
    ${srow('Email', 'You sign in with a code sent here.', `<b>${esc(S.me.user?.email || '')}</b>`)}
    ${srow('Sign out', 'On this device, or on every device at once.', '<a class="btn sec" href="/api/auth/logout">Sign out</a><button class="btn ghost" id="logoutall">Sign out everywhere</button>')}
  </section>`;
  if (tab === 'developer') body = `<section class="panel">
    ${srow('API key', 'For AI assistants and your own tools. It can do everything an admin can. A new key disables the old one.',
      `${S.apiKey ? `<code class="key">${esc(maskKey(S.apiKey))}</code>${copyBtn(S.apiKey)}<span class="note warn">Copy it now. It won't be shown again.</span>` : ''}<button class="btn sec" id="apikey">${S.me.api_key_set ? 'Create a new key' : 'Create key'}</button>`)}
    ${srow('Schedule with AI', 'Connect Claude or another assistant over MCP. It plans posts from your library folders.',
      '<a class="btn sec" href="#ai">Set up the AI assistant</a>')}
    ${srow('AI posts need approval', S.me.ai_review !== false ? 'On: posts an AI schedules wait in Drafts until someone approves them.' : 'Off: posts an AI schedules go straight onto the calendar.',
      `<label class="sw"><input type="checkbox" id="aireview" ${S.me.ai_review !== false ? 'checked' : ''} aria-label="AI posts need approval"><span></span></label>`)}
  </section>`;
  return nav + body;
}

async function loadMembers() {
  S.members = undefined;
  try { S.members = await api('/members'); } catch (e) { S.members = { members: [], invites: [] }; S.flash = { kind: 'err', text: e.message }; }
  render();
}
const scopeFrom = name => {
  const mode = document.querySelector(`input[name="${name}"]:checked`)?.value;
  if (mode !== 'some') return null;
  return [...document.querySelectorAll(`[data-scope="${name}"]:checked`)].map(x => x.value);
};
async function peopleAction(fn, ok) {
  try { await fn(); if (ok) S.flash = { kind: 'ok', text: ok }; } catch (e) { S.flash = { kind: 'err', text: e.message }; }
  S.editScope = null; await loadMembers();
}

async function refreshMe() { S.me = await api('/me'); render(); }
async function switchTo(id) {
  try { await send('/session/workspace', 'POST', { workspace_id: id }); await loadMe(); S.members = null; S.posts = []; route(); }
  catch (e) { S.flash = { kind: 'err', text: e.message }; render(); }
}
const send = (path, method, body) => api(path, { method, headers: { 'Content-Type': 'application/json' },
  body: body === undefined ? undefined : JSON.stringify(body) });
async function brandAction(fn) {
  try { await fn(); } catch (e) { S.flash = { kind: 'err', text: e.message }; }
  await refreshMe();
}

// ---- events ------------------------------------------------------------

// An expired TikTok cover falls back to the post's own photo or video still; a missing still to the video.
document.addEventListener('error', e => {
  const el = e.target, fb = el?.dataset?.fb;
  if (el?.tagName === 'IMG' && fb) el.outerHTML = pic(fb, [...el.attributes].filter(x => !['src', 'data-fb', 'data-vid'].includes(x.name)).map(x => `${x.name}="${esc(x.value)}"`).join(' '), !el.dataset.vid);
}, true);
document.addEventListener('keydown', e => {
  // C opens Create from anywhere, unless you are typing.
  if (e.key === 'c' && !e.metaKey && !e.ctrlKey && !e.altKey && !e.target.closest('input,textarea,select,[contenteditable]') && S.me && !S.me.needs_email && !$('overlay') && !$('dialogs').firstChild) { location.hash = '#compose'; return; }
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches?.('[role=button][data-open], .day.open[role=button]')) { e.preventDefault(); e.target.click(); return; }
  if (e.key === 'Tab' && $('overlay')) {
    const f = [...$('overlay').querySelectorAll('button,a[href],textarea,input,select')].filter(x => !x.disabled);
    if (f.length && e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (f.length && !e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  }
  if (e.key !== 'Escape') return;
  if (S.result?.open) { S.result.open = false; render(); } else if (S.pickOpen) { S.pickOpen = false; render(); $('openpick')?.focus(); } else if (S.detail) { S.detail = null; render(); } });
// The account dropdown closes when you click anywhere outside it.
document.addEventListener('pointerdown', e => { if (S.pickOpen && !e.target.closest('.dd')) { S.pickOpen = false; render(); } });

function bind() {
  const on = (sel, ev, fn) => document.querySelectorAll(sel).forEach(el => el.addEventListener(ev, fn));
  on('#files', 'change', e => addFiles(e.target.files));
  on('#rmvideo', 'click', () => { S.video = null; render(); });
  on('#loginemail', 'submit', e => { e.preventDefault(); S.login.email = $('le').value.trim(); sendCode(); });
  on('#logincode', 'submit', e => { e.preventDefault(); S.login.code = $('lc').value.trim(); verifyCode(); });
  on('#lc', 'input', e => { S.login.code = e.target.value.replace(/\D/g, ''); if (S.login.code.length === 6) verifyCode(); });
  on('#loginback', 'click', () => { S.login = { step: 'email', email: S.login.email, code: '', busy: false, err: '' }; render(); });
  on('#loginresend', 'click', sendCode);
  on('#wsswitch', 'change', e => switchTo(e.target.value));
  on('[data-switch]', 'click', e => switchTo(e.target.dataset.switch));
  on('#newws', 'submit', async e => { e.preventDefault();
    try { await send('/workspaces', 'POST', { name: $('newwsname').value || 'New workspace' }); await loadMe(); S.members = null; location.hash = '#accounts'; route(); }
    catch (x) { S.flash = { kind: 'err', text: x.message }; render(); } });
  on('#wstz', 'change', e => brandAction(() => send('/workspace', 'PATCH', { timezone: e.target.value || null })));
  on('#wsname', 'submit', e => { e.preventDefault(); brandAction(() => send('/workspace', 'PATCH', { name: $('wsnamein').value })); });
  on('#inviteform', 'submit', e => { e.preventDefault(); const email = $('invemail').value, role = $('invrole').value;
    peopleAction(() => send('/invites', 'POST', { email, role, brand_ids: role === 'member' ? scopeFrom('inv') : null }), `Invite sent to ${email}.`); });
  on('[data-uninvite]', 'click', e => peopleAction(() => send(`/invites/${e.target.dataset.uninvite}`, 'DELETE')));
  on('[data-role]', 'change', e => peopleAction(() => send(`/members/${e.target.dataset.role}`, 'PATCH', { role: e.target.value })));
  on('[data-editscope]', 'click', e => { S.editScope = S.editScope === e.target.dataset.editscope ? null : e.target.dataset.editscope; render(); });
  on('[data-savescope]', 'click', e => { const id = e.target.dataset.savescope;
    peopleAction(() => send(`/members/${id}`, 'PATCH', { role: 'member', brand_ids: scopeFrom('sc-' + id) }), 'Access updated.'); });
  on('[data-remove]', 'click', async e => { const id = e.target.dataset.remove, leave = e.target.dataset.leave;
    const email = S.members?.members.find(m => m.user_id === id)?.email || 'this person';
    if (!await ask(leave ? { title: `Leave ${esc(S.me.workspace.name)}?`, ok: 'Leave workspace', danger: true, icon: ui('users', 22),
        list: [[false, 'You lose access to its accounts, posts and drafts'], [true, 'Everything stays for the rest of the team'], [true, 'An admin can invite you back']] }
      : { title: `Remove ${esc(email)}?`, ok: 'Remove', danger: true, icon: ui('users', 22),
        list: [[false, 'They lose access to this workspace right away'], [true, 'Posts they scheduled still go out'], [true, 'You can invite them again later']] })) return;
    if (leave) { try { await send(`/members/${id}`, 'DELETE'); await loadMe(); S.members = null; route(); } catch (x) { S.flash = { kind: 'err', text: x.message }; render(); } }
    else peopleAction(() => send(`/members/${id}`, 'DELETE'), 'Removed.'); });
  on('[data-transfer]', 'click', async e => {
    const { transfer, email } = e.target.dataset;
    if (!await ask({ title: `Make ${esc(email)} the owner?`, ok: 'Transfer ownership', danger: true, icon: ui('users', 22), type: email,
      list: [[false, 'You become an admin and cannot undo this yourself'], [true, 'Only the new owner can give it back']] })) return;
    try { await send('/workspace/transfer', 'POST', { user_id: transfer }); await loadMe(); S.members = null;
      S.flash = { kind: 'ok', text: `${email} now owns this workspace. You are an admin.` }; route(); }
    catch (x) { S.flash = { kind: 'err', text: x.message }; render(); } });
  on('#logoutall', 'click', async () => { if (!await ask({ title: 'Sign out everywhere?', ok: 'Sign out everywhere', icon: ui('x', 22),
      body: 'Every browser and device signed in to your account is signed out, including this one. Sign in again with a code by email.' })) return;
    await send('/logout-all', 'POST'); location.href = '/api/auth/logout'; });
  on('[data-cover]', 'click', e => { S.cover = Number(e.target.dataset.cover); render(); });
  on('[data-rm]', 'click', e => { const n = Number(e.target.dataset.rm); S.images.splice(n, 1); S.cover = Math.min(S.cover, Math.max(0, S.images.length - 1)); render(); });
  on('[data-mv]', 'click', e => {
    const [n, d] = e.target.dataset.mv.split(':').map(Number), m = n + d;
    if (m < 0 || m >= S.images.length) return;
    [S.images[n], S.images[m]] = [S.images[m], S.images[n]];
    if (S.cover === n) S.cover = m; else if (S.cover === m) S.cover = n;
    render();
  });
  on('#title', 'input', e => { S.title = e.target.value; refreshPreview(); });
  on('#title', 'change', render);
  on('#caption', 'input', e => { S.caption = e.target.value; refreshLimits(); refreshPreview(); });
  on('#aiopen', 'click', async () => { S.ai.open = true; render(); $('aibrief')?.focus();
    if (S.ai.remaining == null) { try { S.ai.remaining = (await api('/ai/usage')).remaining; render(); } catch {} } });
  on('#aiclose', 'click', () => { S.ai.open = false; render(); });
  on('#aibrief', 'input', e => { S.ai.brief = e.target.value; });
  on('#aicta', 'input', e => { S.ai.cta = e.target.value; });
  on('#ailang', 'input', e => { S.ai.language = e.target.value; });
  on('#aitone', 'change', e => { S.ai.tone = e.target.value; });
  on('#ailen', 'change', e => { S.ai.length = e.target.value; });
  on('#aiemoji', 'change', e => { S.ai.emoji = e.target.checked; });
  on('#aitags', 'change', e => { S.ai.hashtags = e.target.checked; });
  on('#aigo', 'click', aiWrite);
  on('[data-rewrite]', 'click', e => aiRewrite(e.target.dataset.rewrite));
  on('[data-voice]', 'click', e => { const id = e.target.dataset.voice; S.voiceEdit = { id, text: S.me.brands.find(b => b.id === id)?.voice || '' }; render(); });
  on('#voicetext', 'input', e => { S.voiceEdit.text = e.target.value; });
  on('#voicecancel', 'click', () => { S.voiceEdit = null; render(); });
  on('#voicesave', 'click', async () => {
    try { await send(`/brands/${S.voiceEdit.id}`, 'PATCH', { voice: S.voiceEdit.text }); S.voiceEdit = null; S.flash = { kind: 'ok', text: 'Brand voice saved.' }; }
    catch (x) { S.flash = { kind: 'err', text: x.message }; }
    await refreshMe(); });
  on('[data-ov]', 'input', e => { S.over[e.target.dataset.ov] = e.target.value; refreshLimits(); refreshPreview(); });
  on('[data-ov]', 'change', render);
  on('[data-custom]', 'click', e => { const pl = e.currentTarget.dataset.custom; S.over[pl] = S.caption; S.capTab = pl; render(); $(`ov-${pl}`)?.focus(); });
  on('[data-captab]', 'click', e => { S.capTab = e.currentTarget.dataset.captab; if (S.capTab !== 'all') S.prevTab = S.capTab; render(); });
  on('[data-prev]', 'click', e => { S.prevTab = e.currentTarget.dataset.prev; render(); });
  on('#drop', 'dragover', e => { e.preventDefault(); e.currentTarget.classList.add('over'); });
  on('#drop', 'dragleave', e => e.currentTarget.classList.remove('over'));
  on('#drop', 'drop', e => { e.preventDefault(); e.currentTarget.classList.remove('over'); addFiles(e.dataTransfer.files); });
  on('[data-uncustom]', 'click', e => { delete S.over[e.target.dataset.uncustom]; S.capTab = 'all'; render(); });
  on('#caption', 'change', render);
  on('[data-t]', 'change', e => toggleTarget(e.target.dataset.t, e.target.checked));
  on('#openpick', 'click', () => { S.pickOpen = !S.pickOpen; render(); if (S.pickOpen) $('pq')?.focus(); });
  on('#closepick', 'click', () => { S.pickOpen = false; S.pickAll = false; render(); });
  on('#pickall', 'click', () => { S.pickAll = true; render(); });
  on('#libfiles', 'change', e => uploadToLibrary(e.target.files));
  on('[data-folder]', 'click', e => { if (e.target.closest('button')) return; S.folderOpen = e.currentTarget.dataset.folder; S.libSel = []; render(); window.scrollTo(0, 0); });
  on('[data-folder]', 'keydown', e => { if (e.key === 'Enter') e.currentTarget.click(); });
  on('#fback', 'click', () => { S.folderOpen = null; render(); });
  on('[data-ltab]', 'click', e => { S.libTab = e.currentTarget.dataset.ltab; S.libSel = []; render(); });
  on('[data-lloose]', 'click', e => { const id = e.currentTarget.dataset.lloose, m = S.libLoose || []; S.libLoose = m.includes(id) ? m.filter(x => x !== id) : [...m, id]; render(); });
  on('[data-colup]', 'change', e => newPostsFrom(e.target.files, e.currentTarget.dataset.colup));
  on('[data-colbrand]', 'dragover', e => { e.preventDefault(); e.currentTarget.classList.add('over'); });
  on('[data-colbrand]', 'dragleave', e => { if (!e.currentTarget.contains(e.relatedTarget)) e.currentTarget.classList.remove('over'); });
  on('[data-colbrand]', 'drop', e => { e.preventDefault(); e.currentTarget.classList.remove('over'); newPostsFrom(e.dataTransfer.files, e.currentTarget.dataset.colbrand); });
  on('[data-ffilter]', 'click', e => { S.fFilter = e.currentTarget.dataset.ffilter; render(); });
  on('#fnew', 'click', () => { S.newFolder = true; render(); $('fnewname')?.focus(); });
  on('#fnewcancel', 'click', () => { S.newFolder = false; render(); });
  on('#fnewform', 'submit', async e => { e.preventDefault();
    const b = curBrand(), name = $('fnewname').value.trim(), note = $('fnewnote').value.trim();
    try { const f = await send('/folders', 'POST', { name, note: note || undefined, brand_id: b === 'all' || b === 'none' ? ($('libbrand')?.value ?? S.libBrand) || null : b });
      S.newFolder = false; await reloadLibrary(); S.folderOpen = f.id; } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    render(); });
  on('#fsave', 'click', async () => { const f = folderOf(S.folderOpen); if (!f) return;
    try { await send(`/folders/${f.id}`, 'PATCH', { name: $('fname').value, note: $('fnoteinp').value, ...($('fbrandsel') ? { brand_id: $('fbrandsel').value || null } : {}) });
      await reloadLibrary(); toast('Folder saved.'); } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    render(); });
  on('[data-fmv]', 'click', async e => { const f = folderOf(S.folderOpen); if (!f) return;
    const [k, d] = e.currentTarget.dataset.fmv.split(':').map(Number), order = f.items.map(i => i.key);
    [order[k], order[k + d]] = [order[k + d], order[k]];
    f.items = order.map(key => f.items.find(i => i.key === key)); render();
    try { await send(`/folders/${f.id}`, 'PATCH', { order }); } catch (er) { S.flash = { kind: 'err', text: er.message }; await reloadLibrary(); render(); } });
  on('[data-fout]', 'click', async e => { const f = folderOf(S.folderOpen); if (!f) return;
    try { await send('/library', 'PATCH', { keys: [e.currentTarget.dataset.fout], brand_id: f.brand_id }); await reloadLibrary(); } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    render(); });
  on('[data-fsched]', 'click', e => scheduleFolder(e.currentTarget.dataset.fsched));
  on('[data-fdel]', 'click', async e => { const f = folderOf(e.currentTarget.dataset.fdel); if (!f) return;
    if (!await ask({ title: `Delete "${f.name}"?`, ok: 'Delete folder', danger: true, icon: ui('image', 22),
      list: [[true, 'Its photos and video stay in the library, outside any folder'], [true, 'Posts already scheduled from it are not touched']] })) return;
    try { await send(`/folders/${f.id}`, 'DELETE'); S.folderOpen = null; await reloadLibrary(); } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    render(); });
  on('#libtofolder', 'change', async e => { const id = e.target.value;
    try { await send('/library', 'PATCH', { keys: S.libSel || [], folder_id: id }); S.libSel = []; await reloadLibrary(); } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    render(); });
  on('[data-approve]', 'click', e => { e.stopPropagation(); S.approving = e.currentTarget.dataset.approve; render(); });
  on('[data-stop]', 'click', e => e.stopPropagation());
  on('#apcancel', 'click', e => { e.stopPropagation(); S.approving = null; render(); });
  on('[data-apgo]', 'click', async e => { e.stopPropagation();
    const g = draftGroups().find(x => (x[0].group_id || x[0].id) === e.currentTarget.dataset.apgo); if (!g) return;
    const privacy = Object.fromEntries([...document.querySelectorAll('[data-apriv]')].map(el => [el.dataset.apriv, el.value]));
    if (g.some(x => x.platform === 'tiktok' && !privacy[x.id])) { toast('Choose who can see it on TikTok first.', 'err'); return; }
    e.currentTarget.disabled = true;
    const errs = await approveGroup(g, privacy);
    S.approving = null;
    if (errs.length) S.flash = { kind: 'err', text: errs.join(' · ') }; else toast(`Approved. It goes out ${fmt(g[0].scheduled_at, { weekday: 'short' })} at ${at(g[0].scheduled_at)}.`);
    await loadDrafts(); refreshCounts(); });
  on('#approveall', 'click', async () => {
    const gs = draftGroups().filter(g => g[0].source === 'ai' && g[0].scheduled_at > Date.now() / 1000);
    const tt = gs.flat().filter(x => x.platform === 'tiktok' && !x.settings?.privacy_level);
    if (tt.length) { toast(`${tt.length} TikTok post${tt.length === 1 ? ' needs' : 's need'} a "who can see it" choice. Approve those one by one.`, 'err'); return; }
    if (!await ask({ title: `Approve ${gs.length} posts?`, ok: 'Approve all', icon: ui('check', 22), body: 'Each goes out at its planned time.' })) return;
    const errs = []; for (const g of gs) errs.push(...await approveGroup(g));
    if (errs.length) S.flash = { kind: 'err', text: errs.join(' · ') }; else toast('All approved.');
    await loadDrafts(); refreshCounts(); });
  on('#aireview', 'change', async e => { const v = e.target.checked;
    try { await send('/workspace', 'PATCH', { ai_review: v }); S.me.ai_review = v; } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    render(); });
  on('#libdrop', 'dragover', e => { e.preventDefault(); e.currentTarget.classList.add('over'); });
  on('#libdrop', 'dragleave', e => e.currentTarget.classList.remove('over'));
  on('#libdrop', 'drop', e => { e.preventDefault(); e.currentTarget.classList.remove('over'); uploadToLibrary(e.dataTransfer.files); });
  on('#libbrand', 'change', e => { S.libBrand = e.target.value; });
  on('[data-lsel]', 'change', e => { const k = e.target.dataset.lsel; S.libSel = (S.libSel || []).filter(x => x !== k).concat(e.target.checked ? [k] : []); render(); });
  on('#libclear', 'click', () => { S.libSel = []; render(); });
  on('#libsched', 'click', async () => { const keys = S.libSel || []; S.libSel = []; await useFromLibrary(keys); location.hash = '#compose'; });
  on('#librm', 'click', async () => { const keys = S.libSel || [];
    if (!await ask({ title: `Remove ${keys.length} photo${keys.length === 1 ? '' : 's'} from the library?`, body: 'Scheduled photo posts keep their own copies. A video still used by a scheduled post stays until that post is done.', ok: 'Remove', danger: true, icon: ui('image', 22) })) return;
    try { await send('/library/remove', 'POST', { keys }); S.libSel = []; } catch (e) { S.flash = { kind: 'err', text: e.message }; }
    loadLibrary(); });
  on('#libmove', 'change', async e => { const v = e.target.value;
    try { await send('/library', 'PATCH', { keys: S.libSel || [], brand_id: v === '-' ? null : v }); S.libSel = []; } catch (er) { S.flash = { kind: 'err', text: er.message }; }
    loadLibrary(); });
  on('#fromlib', 'click', () => { S.libPick = true; S.libPickSel = []; render(); if (!S.lib || !S.folders) loadLibrary(); });
  on('[data-usefolder]', 'click', async e => { const f = folderOf(e.currentTarget.dataset.usefolder); if (!f) return;
    S.libPick = false; S.images = []; S.video = null; S.cover = 0; render();
    await useFromLibrary(f.items.map(i => i.key)); S.fromFolder = f.id; render(); });
  on('[data-lpick]', 'change', e => { const k = e.target.dataset.lpick; S.libPickSel = (S.libPickSel || []).filter(x => x !== k).concat(e.target.checked ? [k] : []); render(); });
  on('#libcancel', 'click', () => { S.libPick = false; render(); });
  on('#libadd', 'click', async () => { const keys = S.libPickSel || []; S.libPick = false; S.libPickSel = []; render(); await useFromLibrary(keys); render(); });
  on('[data-unbrand]', 'click', e => brandAction(() => send(`/accounts/${e.currentTarget.dataset.unbrand}`, 'PATCH', { brand_id: null })));
  on('[data-settab-link]', 'click', e => { S.setTab = e.currentTarget.dataset.settabLink; });
  on('[data-addpl]', 'change', e => { const v = e.target.value, brand = e.target.dataset.addpl; if (!v) return;
    if (v.startsWith('new:')) {
      try { localStorage.setItem(PENDING_BRAND, JSON.stringify({ brand, pl: v.slice(4), known: S.me.accounts.map(a => a.id), at: Date.now() })); } catch {}
      location.href = connectHref(v.slice(4)); return;
    }
    brandAction(() => send(`/accounts/${v}`, 'PATCH', { brand_id: brand })); });
  on('[data-addto]', 'change', e => { const id = e.target.value; if (id) brandAction(() => send(`/accounts/${id}`, 'PATCH', { brand_id: e.target.dataset.addto })); });
  // Connecting while a brand is chosen files the new account under it.
  on('a[href*="/api/auth/"][href*="add=1"]', 'click', e => {
    const b = e.currentTarget.dataset.cbrand || curBrand();
    if (b === 'all' || b === 'none' || !can('admin')) return;
    const href = e.currentTarget.getAttribute('href'), pl = href.includes('/meta/') ? 'facebook' : href.includes('/instagram/') ? 'instagram' : 'tiktok';
    try { localStorage.setItem(PENDING_BRAND, JSON.stringify({ brand: b, pl, known: S.me.accounts.map(a => a.id), at: Date.now() })); } catch {}
  });
  on('[data-bg]', 'change', e => pickGroup(e.target.dataset.bg, e.target.checked));
  document.querySelectorAll('[data-state=some]').forEach(el => { el.indeterminate = true; });
  on('#pq', 'input', e => { S.pq = e.target.value; const at = e.target.selectionStart; render();
    const el = $('pq'); if (el) { el.focus(); el.setSelectionRange(at, at); } });
  on('#newbrandbtn', 'click', async () => {
    const name = await ask({ title: 'New brand', ok: 'Create brand', body: 'One per business you post for. Add its accounts after.', input: { value: '', label: 'Brand name, e.g. Client Bakery' } });
    if (name?.trim()) brandAction(() => send('/brands', 'POST', { name: name.trim() })); });
  on('[data-move]', 'change', e => brandAction(() => send(`/accounts/${e.target.dataset.move}`, 'PATCH', { brand_id: e.target.value || null })));
  on('[data-bmenu]', 'change', e => { const id = e.target.dataset.bmenu, v = e.target.value; e.target.value = ''; if (v === 'settings') { S.setTab = 'brands'; location.hash = '#settings'; } else (v === 'rename' ? renameBrand : deleteBrand)(id); });
  on('[data-rename]', 'click', e => renameBrand(e.currentTarget.dataset.rename));
  on('[data-delbrand]', 'click', e => deleteBrand(e.currentTarget.dataset.delbrand));
  on('[data-pv]', 'change', e => { S.tt[e.target.dataset.pv].privacy = e.target.value; render(); });
  on('[data-cm]', 'change', e => { S.tt[e.target.dataset.cm].comment = e.target.checked; render(); });
  on('#bulkpriv', 'change', e => e.target.value && bulkPrivacy(e.target.value));
  on('[data-k]', 'change', e => setOpt(e.target.dataset.k, e.target.checked));
  on('input[name=when]', 'change', e => { S.when = e.target.value; if (S.when === 'queue') loadQueue(); render(); });
  on('[data-slotedit]', 'click', e => openSlots(e.target.dataset.slotedit));
  on('[data-slotday]', 'click', e => { const d = +e.target.dataset.slotday, x = S.slotEdit;
    x.days = x.days.includes(d) ? x.days.filter(v => v !== d) : [...x.days, d]; render(); });
  on('[data-slottime]', 'change', e => { S.slotEdit.times[+e.target.dataset.slottime] = e.target.value; });
  on('[data-slotrm]', 'click', e => { S.slotEdit.times.splice(+e.target.dataset.slotrm, 1); render(); });
  on('#slotadd', 'click', () => { S.slotEdit.times.push('12:00'); render(); });
  on('#slotcancel', 'click', () => { S.slotEdit = null; render(); });
  on('#slotclear', 'click', () => saveSlots(null));
  on('#slotsave', 'click', () => saveSlots({ days: S.slotEdit.days, times: S.slotEdit.times.filter(Boolean) }));
  on('#at', 'change', e => { S.at = e.target.value; render(); });
  on('#go', 'click', submit);
  on('#savedraft', 'click', saveDraft);
  on('[data-days]', 'click', e => loadStats(Number(e.currentTarget.dataset.days)));
  on('[data-atrend]', 'click', e => { S.statsTrend = e.currentTarget.dataset.atrend; render(); });
  on('[data-asort]', 'click', e => { S.statsSort = e.currentTarget.dataset.asort; render(); });
  on('[data-aplat]', 'click', e => loadStats(undefined, e.currentTarget.dataset.aplat));
  on('.chart .hit', 'mouseenter', e => { const pl = e.target.closest('.plot'), tip = pl.querySelector('.ctip'), cx = pl.querySelector('.cx'), x = e.target.dataset.x;
    tip.textContent = e.target.dataset.tip; tip.style.left = `${x}%`; tip.classList.add('on'); cx.style.left = `${x}%`; cx.classList.add('on'); });
  on('.chart .plot', 'mouseleave', e => { e.currentTarget.querySelector('.ctip').classList.remove('on'); e.currentTarget.querySelector('.cx').classList.remove('on'); });
  on('[data-opendraft]', 'click', e => { if (e.target.closest('[data-deldraft]')) return; openDraft(e.currentTarget.dataset.opendraft); });
  on('[data-deldraft]', 'click', async e => {
    e.stopPropagation(); const key = e.currentTarget.dataset.deldraft, g = draftGroups().find(x => (x[0].group_id || x[0].id) === key);
    if (!g || !await ask({ title: 'Delete this draft?', ok: 'Delete draft', danger: true, icon: ui('draft', 22),
      body: esc((g[0].caption || g[0].title || 'No caption yet').slice(0, 90)), list: [[false, 'Its caption and photos are removed for good']] })) return;
    await dropDrafts(g.map(x => x.id)); loadDrafts(); });
  on('#stopedit', 'click', () => { resetComposer(); location.hash = '#calendar'; });
  on('[data-fp]', 'click', e => { S.fPlat = e.target.dataset.fp; S.fAcct = 'all'; render(); });
  on('#facct', 'change', e => { S.fAcct = e.target.value; render(); });
  on('[data-again]', 'click', e => { S.detail = null; edit(e.target.dataset.again, true); });
  on('[data-wk]', 'click', e => { const d = Number(e.currentTarget.dataset.wk); if (S.calMode === 'month') S.month += d; else S.week += d * (S.calMode === 'weeks' ? 4 : 1); loadWeek(); });
  on('[data-open]', 'click', e => { if (e.target.closest('button,a') !== e.currentTarget && e.target.closest('button,a')) return; S.detail = e.currentTarget.dataset.open; render(); });
  on('#closedetail', 'click', () => { S.detail = null; render(); });
  on('#overlay', 'click', e => { if (e.target.id === 'overlay') { S.detail = null; render(); } });
  on('#savecap', 'click', async () => {
    try { await send(`/posts/${S.detail}`, 'PATCH', { caption: $('dcap').value }); S.flash = { kind: 'ok', text: 'Caption saved.' }; }
    catch (x) { S.flash = { kind: 'err', text: x.message }; }
    reloadView(); });
  on('.day.open', 'click', e => {
    if (e.target.closest('[data-open],button,a')) return;
    const [y, m, d] = e.currentTarget.dataset.day.split('-').map(Number);
    // 9:00 that day, or the next whole hour if today is already past 9.
    const n = zoned(Date.now()), isToday = n.y === y && n.m === m && n.d === d;
    const h = isToday ? Math.max(9, n.h + 1) : 9;
    if (h > 23) return;
    resetComposer(); S.when = 'later'; S.at = `${y}-${pad(m)}-${pad(d)}T${pad(h)}:00`; location.hash = '#compose';
  });
  on('[data-brand]', 'click', e => setBrand(e.currentTarget.dataset.brand));
  on('[data-newon]', 'click', e => { const [y, m, d] = e.currentTarget.dataset.newon.split('-').map(Number);
    const n = zoned(Date.now()), isToday = n.y === y && n.m === m && n.d === d, h = isToday ? Math.max(9, n.h + 1) : 9;
    resetComposer(); if (h <= 23) { S.when = 'later'; S.at = `${y}-${pad(m)}-${pad(d)}T${pad(h)}:00`; } location.hash = '#compose'; });
  on('[data-res]', 'click', e => { const k = e.currentTarget.dataset.res; if (!S.result) return; S.result.open = false;
    if (k === 'overview') location.hash = '#overview'; else if (k === 'calendar') location.hash = '#calendar';
    else { render(); if (k === 'another') $('openpick')?.focus(); } });
  on('#rsheetbg', 'click', e => { if (e.target.id === 'rsheetbg') { S.result.open = false; render(); } });
  on('[data-today]', 'click', () => { S.week = 0; S.month = 0; loadWeek(); });
  on('[data-moreday]', 'click', e => { const [y, m, d] = e.currentTarget.dataset.moreday.split('-').map(Number);
    const t = today(), mon = x => { const wd = new Date(Date.UTC(x.y, x.m - 1, x.d)).getUTCDay(); return addDays(x, -((wd + 6) % 7)); };
    S.calMode = 'week'; S.week = Math.round((Date.UTC(...Object.values(mon({ y, m, d })).map((v, k) => k === 1 ? v - 1 : v)) - Date.UTC(...Object.values(mon(t)).map((v, k) => k === 1 ? v - 1 : v))) / 6048e5); loadWeek(); });
  on('[data-mode]', 'click', e => { S.calMode = e.target.dataset.mode; S.week = 0; S.month = 0; loadWeek(); });
  on('[data-drag]', 'dragstart', e => { e.dataTransfer.setData('text/plain', e.currentTarget.dataset.drag); e.dataTransfer.effectAllowed = 'move'; });
  on('[data-day]', 'dragover', e => { e.preventDefault(); e.currentTarget.classList.add('drop'); });
  on('[data-day]', 'dragleave', e => e.currentTarget.classList.remove('drop'));
  on('[data-day]', 'drop', e => { e.preventDefault(); e.currentTarget.classList.remove('drop');
    const id = e.dataTransfer.getData('text/plain'); if (id) movePost(id, e.currentTarget.dataset.day); });
  on('[data-cancel]', 'click', async e => { try { await api(`/posts/${e.target.dataset.cancel}`, { method: 'DELETE' }); S.detail = null; S.flash = { kind: 'ok', text: 'Post cancelled.' }; } catch (x) { S.flash = { kind: 'err', text: x.message }; } reloadView(); refreshCounts(); });
  on('[data-retry]', 'click', async e => { const id = e.currentTarget.dataset.retry;
    try { await api(`/posts/${id}/retry`, { method: 'POST' });
      const R = S.result; const p = R?.open && R.posts.find(x => x.id === id);
      if (p) { p.status = 'queued'; render(); watch([id]); return; }
      S.detail = null; S.flash = { kind: 'ok', text: 'Retrying. It goes out within a minute.' }; } catch (x) { S.flash = { kind: 'err', text: x.message }; } reloadView(); refreshCounts(); });
  on('[data-edit]', 'click', e => { S.detail = null; edit(e.target.dataset.edit); });
  on('[data-disc]', 'click', e => disconnectAcct(e.currentTarget.dataset.disc));
  on('[data-amenu]', 'change', e => { const id = e.target.dataset.amenu, v = e.target.value; e.target.value = '';
    if (v === 'disc') disconnectAcct(id);
    else if (v === 'out') brandAction(() => send(`/accounts/${id}`, 'PATCH', { brand_id: null }));
    else if (v.startsWith('b:')) brandAction(() => send(`/accounts/${id}`, 'PATCH', { brand_id: v.slice(2) })); });
  on('[data-settab]', 'click', e => { S.setTab = e.currentTarget.dataset.settab; render(); });
  on('[data-copy]', 'click', async e => { const b = e.currentTarget;
    try { await navigator.clipboard.writeText(b.dataset.copy); if (b.classList.contains('copied')) return; const t = b.innerHTML;
      if (b.classList.contains('mprompt')) b.classList.add('copied'); else b.textContent = 'Copied';
      setTimeout(() => { b.innerHTML = t; b.classList.remove('copied'); }, 1400); }
    catch { toast('Copy did not work here. Select the text and copy it.', 'err'); } });
  on('[data-aiclient]', 'click', e => { S.aiClient = e.currentTarget.dataset.aiclient; render(); });
  on('[data-aios]', 'click', e => { S.aiOS = e.currentTarget.dataset.aios; render(); });
  on('[data-keycopy]', 'click', async e => { const b = e.currentTarget, kind = b.dataset.keycopy;
    try { const k = (S.apiKey ? Promise.resolve(S.apiKey) : api('/api-key').then(r => r.api_key)).then(x => linkText(kind, x));
      if (window.ClipboardItem) await navigator.clipboard.write([new ClipboardItem({ 'text/plain': k.then(t => new Blob([t], { type: 'text/plain' })) })]);
      else await navigator.clipboard.writeText(await k);
      const t = b.innerHTML; b.textContent = 'Copied'; setTimeout(() => { b.innerHTML = t; }, 1400); }
    catch (er) { toast(er.message && !/clipboard|denied|document/i.test(er.message) ? er.message : 'Copy did not work here. Try again.', 'err'); } });
  on('#keycopy', 'click', async e => { const b = e.currentTarget;
    // ClipboardItem takes the key as a promise, so Safari keeps the click's permission while it loads.
    try { const k = S.apiKey ? Promise.resolve(S.apiKey) : api('/api-key').then(r => r.api_key);
      if (window.ClipboardItem) await navigator.clipboard.write([new ClipboardItem({ 'text/plain': k.then(t => new Blob([t], { type: 'text/plain' })) })]);
      else await navigator.clipboard.writeText(await k);
      const t = b.innerHTML; b.textContent = 'Copied'; setTimeout(() => { b.innerHTML = t; }, 1400); }
    catch (er) { toast(er.message && !/clipboard|denied|document/i.test(er.message) ? er.message : 'Copy did not work here. Try again.', 'err'); } });
  on('#keymenu', 'change', async e => { const v = e.target.value; e.target.value = '';
    if (v === 'new') newApiKey();
    else if (v === 'delete') deleteApiKey();
    else if (v === 'rename') { const name = await ask({ title: 'Rename the key', ok: 'Save', input: { value: S.me.api_key_name || '', label: 'Key name, e.g. Claude on my Mac' } });
      if (name?.trim()) { try { await send('/api-key', 'PATCH', { name: name.trim() }); S.me.api_key_name = name.trim(); } catch (er) { S.flash = { kind: 'err', text: er.message }; } render(); } } });
  on('#apikeydel', 'click', () => deleteApiKey());
  on('#apikey', 'click', () => newApiKey());
  on('#delws', 'click', async () => {
    if (!await ask({ title: `Delete ${esc(S.me.workspace.name)}?`, ok: 'Delete workspace', danger: true, icon: ui('x', 22), type: S.me.workspace.name,
      list: [[false, 'All its accounts, brands, posts, photos and members are removed now'], [false, 'Scheduled posts never go out'], [false, 'This cannot be undone']] })) return;
    await api('/me', { method: 'DELETE' }); location.href = '/api/auth/logout';
  });
}

boot();
