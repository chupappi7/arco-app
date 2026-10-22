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
  set: { music: false, disclose: false, brand: false, branded: false },
  when: 'now', at: '', busy: false, status: null,
  week: 0, month: 0, calMode: 'weeks', fPlat: 'all', fAcct: 'all', fBrand: 'all', posts: [], apiKey: null,
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
  S.targets = []; S.tt = {};
  restoreTargets();
  refreshCounts();
}

// The accounts last posted to come back preselected: someone running ten
// accounts posts to the same set most days.
function restoreTargets() {
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(SAVED) || '[]'); } catch {}
  for (const id of saved) { const a = acct(id); if (a && !a.needs_reconnect) toggleTarget(id, true, false); }
}
function saveTargets() { try { localStorage.setItem(SAVED, JSON.stringify(S.targets)); } catch {} }

const VIEWS = ['overview', 'compose', 'calendar', 'analytics', 'drafts', 'accounts', 'settings'];
function route() {
  S.view = (location.hash || '#overview').slice(1);
  if (!VIEWS.includes(S.view)) S.view = 'overview';
  const signedIn = !!S.me && !S.me.needs_email;
  if (signedIn && S.view === 'overview') loadOverview();
  if (signedIn && S.view === 'calendar') loadWeek();
  if (signedIn && S.view === 'drafts') loadDrafts();
  if (signedIn && S.view === 'analytics') loadStats();
  render();
  window.scrollTo(0, 0);
}

// ---- render ------------------------------------------------------------

// UI icons: one stroke weight everywhere.
const UI = {
  home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m14 6 4 4"/>',
  cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  draft: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/>',
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
  const items = [['overview', 'Overview', 'home'], ['compose', 'Create', 'edit'], ['calendar', 'Calendar', 'cal', S.counts.failed, 'bad'], ['analytics', 'Analytics', 'chart'],
    ['drafts', 'Drafts', 'draft', S.counts.drafts], ...(can('admin') ? [['accounts', 'Accounts', 'users']] : [])];
  const email = S.me.user?.email || '';
  return `<a class="brand-row" href="#overview"><img class="logo" src="/apple-touch-icon.png" alt="" width="30" height="30"><b>ARCO Publisher</b></a>
    ${wsBox()}
    <a class="create-side" href="#compose">${ui('plus', 16)}Create post</a>
    <nav class="nav" aria-label="Main">${items.map(([k, l, i, n, tone]) =>
      `<a href="#${k}" class="${S.view === k ? 'on' : ''}" ${S.view === k ? 'aria-current="page"' : ''}>${ui(i)}${l}${n ? `<span class="n ${tone || ''}" title="${tone === 'bad' ? `${n} failed in the last 7 days` : `${n} waiting`}">${n}</span>` : ''}</a>`).join('')}</nav>
    <div class="grow"></div>
    <nav class="nav"><a href="#settings" class="${S.view === 'settings' ? 'on' : ''}">${ui('gear')}Settings</a></nav>
    <div class="me"><span class="av-me">${esc((email[0] || '?').toUpperCase())}</span>
      <div><b>${esc(email)}</b><a href="/api/auth/logout">Sign out</a></div></div>`;
}

function tabbar() {
  const t = (k, l, i) => `<a href="#${k}" class="${S.view === k ? 'on' : ''}">${ui(i, 20)}${l}</a>`;
  return t('overview', 'Overview', 'home') + t('calendar', 'Calendar', 'cal') +
    `<a href="#compose" aria-label="Create post"><span class="plus">${ui('plus', 22)}</span></a>` +
    t('drafts', 'Drafts', 'draft') + (can('admin') ? t('accounts', 'Accounts', 'users') : t('settings', 'Settings', 'gear'));
}

const HEADS = {
  compose: () => ['Create post', S.targets.length ? `Goes to ${S.targets.length} account${S.targets.length === 1 ? '' : 's'}.` : 'Choose accounts, add photos, write the caption.'],
  calendar: () => ['Calendar', `Everything scheduled and published, in ${tz().replace(/_/g, ' ')} time.`],
  analytics: () => ['Analytics', 'How your posts do, from the numbers each platform shares.'],
  drafts: () => ['Drafts', 'Posts saved for later. Open one to finish and schedule it.'],
  accounts: () => ['Accounts', 'Connect accounts and group them into brands.'],
  settings: () => ['Settings', 'Workspace, people and your account.'],
};
const pageHead = (title, sub, action = '') => `<div class="pagehead"><div><h1>${title}</h1>${sub ? `<p>${sub}</p>` : ''}</div>${action}</div>`;

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
  const views = { analytics: analyticsView, overview: overviewView, calendar: calendarView, drafts: draftsView, accounts: accountsView, settings: settingsView, compose: composeView };
  const head = S.view === 'overview' ? '' : pageHead(...HEADS[S.view]());
  const hadDetail = !!$('overlay'), opener = S.detail && !hadDetail ? document.activeElement?.closest?.('[data-open]')?.dataset.open : null;
  $('app').innerHTML = head + views[S.view]() + (['calendar', 'overview'].includes(S.view) && S.detail ? detailView() : '');
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
    api('/stats?days=7').then(st => { S.ovStats = st; if (S.view === 'overview') render(); }).catch(() => {});
  } catch (e) { S.flash = { kind: 'err', text: e.message }; S.ov = { at: now, err: true }; }
  if (S.view === 'overview') render();
}

function greeting() {
  const h = zoned(Date.now()).h;
  return h < 5 ? 'Good evening' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

const thumbOf = p => p.images?.[p.cover_index] || p.images?.[0];
const at = (sec, o = { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }) => fmt(sec, o);

function overviewView() {
  const acc = S.me.accounts;
  if (!acc.length) return firstRun();
  if (!S.ov) return pageHead(greeting(), 'Loading today…') + '<div class="panel empty">Loading…</div>';
  const now = Math.floor(Date.now() / 1000), todayKey = dayKey(today());
  const live = S.posts.filter(p => p.status !== 'cancelled');
  const todays = live.filter(p => dayOf(p.scheduled_at) === todayKey).sort((a, b) => a.scheduled_at - b.scheduled_at);
  const upcoming = live.filter(p => p.status === 'queued' && p.scheduled_at >= now).sort((a, b) => a.scheduled_at - b.scheduled_at);
  const next = upcoming[0];
  const leftToday = todays.filter(p => p.status === 'queued' && p.scheduled_at >= now).length;
  const sub = next
    ? `${leftToday ? `<b>${leftToday} post${leftToday === 1 ? '' : 's'}</b> still to go out today. ` : ''}Next is <b>${dayOf(next.scheduled_at) === todayKey ? at(next.scheduled_at) : fmtFull(next.scheduled_at)}</b> on ${PLATFORM[next.platform] || 'TikTok'} ${next.platform === 'facebook' ? '' : '@'}${esc(next.username)}.`
    : 'Nothing is scheduled yet.';

  const slot = p => {
    const isNext = next && p.id === next.id;
    const cls = isNext ? 'next' : p.status;
    const label = isNext ? 'Next up' : { published: 'Published', failed: 'Failed', queued: 'Scheduled', publishing: 'Posting', cancelled: 'Cancelled' }[p.status] || p.status;
    const img = thumbOf(p);
    return `<div class="slot ${cls}"><time>${at(p.scheduled_at)}</time><div class="dot"><i></i></div>
      <div class="rpost" data-open="${p.id}" role="button" tabindex="0">${img ? `<img class="thumb" src="${esc(img)}" alt="">` : '<span class="noimg"></span>'}
        <div class="wh"><b>${icon(p.platform || 'tiktok', 14)}${who(p)}</b><span>${esc(p.caption || p.title || 'No caption')}</span></div>
        <span class="st ${cls}">${label}</span></div></div>`;
  };
  const before = todays.filter(p => p.scheduled_at < now), after = todays.filter(p => p.scheduled_at >= now);
  const rail = todays.length
    ? `<div class="rail">${before.map(slot).join('')}<div class="nowline"><time>${at(now)}</time><div class="bar"></div></div>${after.map(slot).join('')}</div>`
    : `<div class="empty"><b>Nothing goes out today.</b>${next ? `The next post is ${fmtFull(next.scheduled_at)}.` : 'Create a post, or add it to the queue to fill your posting times.'}
        <div><a class="btn" href="#compose">${ui('plus', 16)}Create post</a></div></div>`;

  const failed = live.filter(p => p.status === 'failed' && p.scheduled_at > now - 7 * 86400);
  const reconnect = acc.filter(a => a.needs_reconnect);
  const drafts = draftGroups();
  const handle = p => `${who(p)}`;

  // The numbers we already have, each a way into the screen that explains it.
  const week = 7 * 86400;
  const sched7 = upcoming.filter(p => p.scheduled_at < now + week).length;
  const pub7 = live.filter(p => p.status === 'published' && p.scheduled_at >= now - week).length;
  const platforms = new Set(acc.map(platformOf)).size;
  const kpis = [
    ['#calendar', 'Scheduled', sched7, 'in the next 7 days', ''],
    ['#calendar', 'Published', pub7, 'in the last 7 days', ''],
    ['#calendar', 'Failed', failed.length, failed.length ? 'in the last 7 days' : 'nothing failed this week', failed.length ? 'bad' : ''],
    ['#accounts', 'Accounts', acc.length, reconnect.length ? `${reconnect.length} need${reconnect.length === 1 ? 's' : ''} reconnecting` : `on ${platforms} platform${platforms === 1 ? '' : 's'}`, reconnect.length ? 'warn' : ''],
  ];

  const attn = [
    ...failed.slice(0, 3).map(p => `<div class="it" data-open="${p.id}" role="button" tabindex="0"><span class="ic bad">${ui('x', 16)}</span><div><b>Failed on ${handle(p)}</b><span>${esc(p.fail_reason || 'Open it to see why')}</span></div><em>Review</em></div>`),
    ...reconnect.slice(0, 3).map(a => `<a href="#accounts"><span class="ic warn">${ui('retry', 16)}</span><div><b>Reconnect ${who(a)}</b><span>${PLATFORM[platformOf(a)]} access expired or was removed</span></div><em>Reconnect</em></a>`),
  ];

  // After today: the next few posts, so the week ahead is never a surprise.
  const later = upcoming.filter(p => dayOf(p.scheduled_at) !== todayKey).slice(0, 4);
  const laterRow = p => `<div class="rpost" data-open="${p.id}" role="button" tabindex="0">${thumbOf(p) ? `<img class="thumb" src="${esc(thumbOf(p))}" alt="">` : '<span class="noimg"></span>'}
      <div class="wh"><b>${icon(p.platform || 'tiktok', 14)}${handle(p)}</b><span>${esc(p.caption || p.title || 'No caption')}</span></div>
      <time>${fmt(p.scheduled_at, { weekday: 'short' })} ${at(p.scheduled_at)}</time></div>`;

  // This week, Monday to Sunday: how many posts each day, on which platforms.
  const t0 = today(), wd = new Date(Date.UTC(t0.y, t0.m - 1, t0.d)).getUTCDay(), mon = addDays(t0, -((wd + 6) % 7));
  const days = [...Array(7)].map((_, i) => addDays(mon, i));
  const weekPosts = days.map(d => live.filter(p => dayOf(p.scheduled_at) === dayKey(d)));
  const weekTotal = weekPosts.reduce((n, x) => n + x.length, 0);
  const dayCell = (d, i) => {
    const list = weekPosts[i], k = dayKey(d), isToday = k === todayKey, past = !isToday && list.length === 0 && i < (wd + 6) % 7;
    const bad = list.some(p => p.status === 'failed');
    return `<a class="wd ${isToday ? 'today' : ''} ${past ? 'past' : ''}" href="#calendar">
      <span class="wl">${dayLabel(d, { weekday: 'short' })} <b>${d.d}</b></span>
      <span class="wn ${list.length ? "" : "z"}">${list.length || "–"}</span>
      <span class="wp">${ORDER.filter(pl => list.some(p => (p.platform || 'tiktok') === pl)).map(pl => icon(pl, 12)).join('')}${bad ? '<i class="wbad" title="A post failed"></i>' : ''}</span></a>`;
  };

  const published = live.filter(p => p.status === 'published').sort((a, b) => b.scheduled_at - a.scheduled_at).slice(0, 4);
  const pubRow = p => `<div class="rpost" data-open="${p.id}" role="button" tabindex="0">${thumbOf(p) ? `<img class="thumb" src="${esc(thumbOf(p))}" alt="">` : '<span class="noimg"></span>'}
      <div class="wh"><b>${icon(p.platform || 'tiktok', 14)}${handle(p)}</b><span>${fmt(p.scheduled_at, { dateStyle: 'medium' })}${p.stats ? statLine(p.stats) : ''}</span></div>
      ${p.post_url ? `<a class="view" href="${esc(p.post_url)}" target="_blank" rel="noopener">View post</a>` : ''}</div>`;

  return pageHead(greeting(), sub) + `
  <div class="kpis">${kpis.map(([href, l, n, note, tone]) => `<a href="${href}" class="kpi ${tone}"><span>${l}</span><b>${n}</b><small>${note}</small></a>`).join('')}</div>
  <div class="ovw">
    <section class="panel today"><header><h2>Today</h2><a href="#calendar">Open calendar</a></header>${rail}</section>
    <div class="stack">
      ${attn.length ? `<section class="panel"><header><h2>Needs attention</h2></header><div class="attn">${attn.join('')}</div></section>` : ''}
      <section class="panel grow"><header><h2>Coming up</h2>${drafts.length ? `<a href="#drafts">${drafts.length} draft${drafts.length === 1 ? '' : 's'} waiting</a>` : ''}</header>
        ${later.length ? `<div class="list">${later.map(laterRow).join('')}</div>`
          : `<div class="empty"><b>Nothing after today.</b>Schedule a post, or add one to the queue.</div>`}</section>
    </div>
    <section class="panel wide"><header><h2>This week</h2><span class="note">${weekTotal} post${weekTotal === 1 ? '' : 's'}</span></header>
      <div class="wkstrip">${days.map(dayCell).join('')}</div></section>
    <section class="panel"><header><h2>Recently published</h2><a href="#calendar">See all</a></header>
      ${published.length ? `<div class="list">${published.map(pubRow).join('')}</div>`
        : '<div class="empty">Published posts appear here with a link to each one.</div>'}</section>
    ${perfCard()}
  </div>`;
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

async function loadStats(days = S.statsDays || 7) {
  S.statsDays = days;
  try { S.stats = await api(`/stats?days=${days}`); } catch (e) { S.stats = { err: e.message }; }
  if (S.view === 'analytics') render();
}

function perfCard() {
  const st = S.ovStats;
  const head = `<header><h2>Performance</h2><a href="#analytics">Last 7 days</a></header>`;
  if (!st) return `<section class="panel perf">${head}<div class="empty">Loading…</div></section>`;
  const cells = [...['views', 'likes', 'comments', 'shares'].filter(k => st.totals[k] != null).slice(0, 3).map(k => [METRIC[k], num(st.totals[k]), '']),
    ['New followers', st.followers.change == null ? '–' : signed(st.followers.change), st.followers.change > 0 ? 'up' : '']];
  return `<section class="panel perf">${head}
    ${st.tracked || st.followers.total != null ? `<div class="pgrid">${cells.map(([l, v, c]) => `<div><span>${l}</span><b class="${c}">${v}</b></div>`).join('')}</div>`
      : '<div class="empty">Numbers appear a few hours after your first Instagram or Facebook post goes out.</div>'}
    <p class="pnote">${st.facebook_limited ? 'Instagram posts, and followers on Facebook' : 'Instagram and Facebook'}${st.updated_at ? `, updated ${ago(st.updated_at)}` : ''}.${st.tiktok_pending ? ' TikTok numbers come once TikTok approves access.' : ''}</p></section>`;
}

function analyticsView() {
  const st = S.stats, days = S.statsDays || 7;
  const seg = `<div class="seg" role="group" aria-label="Period">${[7, 30].map(d =>
    `<button data-days="${d}" class="${d === days ? 'on' : ''}" aria-pressed="${d === days}">Last ${d} days</button>`).join('')}</div>`;
  if (!st) return `<div class="calbar">${seg}</div><div class="panel empty">Loading…</div>`;
  if (st.err) return `<div class="calbar">${seg}</div><div class="panel empty"><b>Couldn't load the numbers.</b>${esc(st.err)}</div>`;
  const shown = STAT_KEYS.filter(k => st.totals[k] != null);
  const kpis = [['Posts published', num(st.published), st.tracked < st.published ? `${st.tracked} with numbers so far` : 'all with numbers', ''],
    ...shown.slice(0, 3).map(k => [METRIC[k], num(st.totals[k]), st.tracked ? `${num(Math.round(st.totals[k] / st.tracked))} per post` : '', '']),
    ['Followers', num(st.followers.total), st.followers.change == null ? 'change shows after a day' : `${signed(st.followers.change)} in ${days} days`, st.followers.change > 0 ? 'up' : '']];
  const row = p => `<div class="rpost" data-open="${p.id}" role="button" tabindex="0">${thumbOf(p) ? `<img class="thumb" src="${esc(thumbOf(p))}" alt="">` : '<span class="noimg"></span>'}
      <div class="wh"><b>${icon(p.platform || 'tiktok', 14)}${who(p)}</b><span>${esc(p.caption || p.title || 'No caption')}</span></div>
      ${statLine(p.stats)}</div>`;
  const acc = a => `<div class="arow">${icon(a.platform, 14)}<b>${who(a)}</b>
      <span class="fv">${a.followers == null ? (a.platform === 'tiktok' ? '<em>Waiting on TikTok</em>' : '<em>Reading…</em>') : num(a.followers)}</span>
      <span class="fc ${a.change > 0 ? 'up' : a.change < 0 ? 'down' : ''}">${a.change == null ? '' : signed(a.change)}</span></div>`;
  const notes = [
    st.tiktok_pending && 'TikTok views and likes come once TikTok approves the stats permissions for ARCO Publisher.',
    st.facebook_limited && 'Facebook Page likes and comments need one more permission (pages_read_user_content). Followers already show.',
    st.tracked && st.totals.views == null && 'Instagram views, reach and saves need the insights permission; until then you see likes and comments.',
  ].filter(Boolean);
  // Let the pagehead title stand; put the period switch under it.
  return `<div class="calbar">${seg}${st.updated_at ? `<span class="note">Updated ${ago(st.updated_at)}</span>` : ''}</div>
    <div class="kpis">${kpis.map(([l, v, n, c]) => `<div class="kpi"><span>${l}</span><b>${v}</b><small class="${c}">${n}</small></div>`).join('')}</div>
    <div class="ovw">
      <section class="panel"><header><h2>Top posts</h2><span class="note">by views and engagement</span></header>
        ${st.top.length ? `<div class="list">${st.top.map(row).join('')}</div>`
          : `<div class="empty"><b>No numbers yet for this period.</b>Likes and comments show a few hours after a post goes out on Instagram or Facebook.</div>`}</section>
      <section class="panel"><header><h2>Followers</h2><span class="note">change in ${days} days</span></header>
        <div class="alist">${st.accounts.map(acc).join('') || '<div class="empty">Connect an account to see followers.</div>'}</div></section>
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
  <div class="composer">
    <div class="cmain">
      <section class="panel"><header><h2>Post to</h2>${S.targets.length ? `<span class="note">${S.targets.length} selected</span>` : ''}</header>
        <div class="csec">${accountPicker()}</div></section>

      <section class="panel"><header><h2>Photos</h2>${S.images.length ? `<span class="note">${S.images.length} of ${toInstagram() ? IG_MAX : 35}</span>` : ''}</header>
        <div class="csec">${mediaView()}</div></section>

      <section class="panel"><header><h2>Caption</h2>${S.me.ai_enabled && !S.ai.open ? '' : ''}</header>
        <div class="csec">
          ${tts.length ? `<label class="f" for="title">TikTok title</label>
            <input type="text" id="title" maxlength="200" value="${esc(S.title)}" placeholder="A short title for the photo post">
            <div class="count ${len(S.title) > 90 ? 'bad' : ''}">${len(S.title)} / 90</div>` : ''}
          ${S.me.ai_enabled ? aiPanel() : ''}
          ${captionTabs(pls)}
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
          ${row('Duet', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
          ${row('Stitch', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
          ${row('Add recommended music', 'Lets TikTok pick a track for the slideshow.', `<input type="checkbox" data-k="music" ${S.set.music ? 'checked' : ''}>`)}
          ${row('Disclose post content', 'Turn on if this post promotes yourself, a brand, product or service.',
            `<input type="checkbox" data-k="disclose" ${S.set.disclose ? 'checked' : ''}>`)}
          ${S.set.disclose ? `<div class="disc">
            <label><input type="checkbox" data-k="brand" ${S.set.brand ? 'checked' : ''}> Your brand</label>
            <label><input type="checkbox" data-k="branded" ${S.set.branded ? 'checked' : ''}> Branded content</label>
            <p class="note ${label ? 'warn' : ''}">${label ? `Your photo post will be labeled "${label}".` : 'You need to indicate if your content promotes yourself, a third party, or both.'}</p>
          </div>` : ''}
          <p class="consent">By posting, you agree to TikTok's
            ${S.set.branded ? '<a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank" rel="noopener">Branded Content Policy</a> and ' : ''}
            <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en" target="_blank" rel="noopener">Music Usage Confirmation</a>.</p>
        </div></section>` : ''}
    </div>

    <aside class="cside"><section class="panel"><header><h2>Preview</h2></header>
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
    <button class="btn" id="go" ${need || S.busy ? 'disabled' : ''} title="${esc(need || '')}">
      ${S.busy ? 'Working…' : `${S.when === 'later' ? 'Schedule' : S.when === 'queue' ? 'Add to queue' : 'Post now'}${S.targets.length > 1 ? ` · ${S.targets.length}` : ''}`}</button>
  </div>`;
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
  const groups = brandGroups(S.me.accounts.filter(hit)).filter(g => g.accounts.length);
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
    <div class="ddfoot">${can('admin') ? '<a href="#accounts">Manage accounts</a>' : '<span></span>'}<button type="button" class="btn" id="closepick">Done</button></div></div>`;
}

function mediaView() {
  const max = S.images.length >= 35;
  const add = `<label class="addtile ${S.images.length ? '' : 'big'}" id="drop">
      <input type="file" id="files" accept="image/jpeg,image/png" multiple ${max ? 'disabled' : ''}>
      ${ui('plus', S.images.length ? 20 : 24)}<b>${S.images.length ? 'Add' : 'Add photos'}</b>
      ${S.images.length ? '' : '<span>Drop JPG or PNG files here, or click to choose. Up to 5 MB each.</span>'}</label>`;
  return `<div class="mgrid">${S.images.map((m, n) => `<div class="mt ${n === S.cover ? 'cover' : ''} ${m.uploading ? 'up' : ''}">
      <img src="${esc(m.url)}" alt="Photo ${n + 1}" data-cover="${n}" title="Make this the cover">
      <span class="mn">${n + 1}</span>${n === S.cover ? '<span class="badge">Cover</span>' : ''}
      <div class="ctl"><button data-mv="${n}:-1" aria-label="Move left">‹</button>
        <button data-rm="${n}" aria-label="Remove">×</button>
        <button data-mv="${n}:1" aria-label="Move right">›</button></div></div>`).join('')}${add}</div>
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
  const imgs = S.images.map(m => m.url);
  const cap = esc(captionFor(pl) || '');
  const av = withBadge(avatar(a?.avatar_url, name), pl);
  const ph = '<div class="pv-ph">' + ui('plus', 20) + '</div>';
  if (pl === 'instagram') return `<div class="pv ig"><div class="pv-h">${av}<b>${esc(name)}</b></div>
      <div class="pv-media r45">${imgs[0] ? `<img src="${esc(imgs[0])}" alt="">` : ph}${imgs.length > 1 ? `<span class="pv-count">1/${imgs.length}</span>` : ''}</div>
      ${imgs.length > 1 ? `<div class="pv-dots">${imgs.slice(0, 10).map((_, i) => `<i class="${i ? '' : 'on'}"></i>`).join('')}</div>` : ''}
      <div class="pv-acts">${ui('heart', 20)}${ui('comment', 20)}${ui('share', 20)}</div>
      <p class="pv-cap"><b>${esc(name)}</b> ${cap || '<span class="note">Your caption appears here.</span>'}</p></div>`;
  if (pl === 'facebook') return `<div class="pv fb"><div class="pv-h">${av}<div><b>${esc(name)}</b><small>Just now</small></div></div>
      <p class="pv-cap">${cap || '<span class="note">Your caption appears here.</span>'}</p>
      <div class="pv-grid n${Math.min(imgs.length, 4)}">${imgs.slice(0, 4).map((u, i) => `<div><img src="${esc(u)}" alt="">${i === 3 && imgs.length > 4 ? `<span>+${imgs.length - 4}</span>` : ''}</div>`).join('') || ph}</div>
      <div class="pv-acts fb">${ui('heart', 17)}<span>Like</span>${ui('comment', 17)}<span>Comment</span>${ui('share', 17)}<span>Share</span></div></div>`;
  const cover = imgs[S.cover] || imgs[0];
  return `<div class="pv tt"><div class="pv-media r916">${cover ? `<img src="${esc(cover)}" alt="">` : ph}
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
  const dup = (S.me?.accounts || []).filter(a => (a.username || a.display_name || '').toLowerCase() === low).length > 1;
  return `${pl === 'facebook' ? '' : '@'}${esc(name)}${dup ? `<small class="plt">${PLATFORM[pl]}</small>` : ''}`;
}


const brandName = id => S.me.brands.find(b => b.id === id)?.name;
function brandGroups(list = S.me.accounts) {
  const groups = S.me.brands.map(b => ({ id: b.id, name: b.name, accounts: list.filter(a => a.brand_id === b.id) }));
  const loose = list.filter(a => !a.brand_id || !brandName(a.brand_id));
  if (loose.length) groups.push({ id: 'none', name: S.me.brands.length ? 'Not in a brand' : 'All accounts', accounts: loose });
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

// Each platform's count against its own limit, for whichever caption it will
// actually get. Updated as you type, without re-rendering the page.
function limitsLine() {
  return chosenPlatforms().map(pl => {
    const c = captionFor(pl), n = len(c), over = n > CAPTION_MAX[pl] || (pl === 'instagram' && hashtags(c) > IG_HASHTAGS);
    return `<span class="lim ${over ? 'bad' : ''}">${icon(pl, 12)} ${n.toLocaleString()} / ${CAPTION_MAX[pl].toLocaleString()}${
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
  if (!S.images.length) return 'Add at least one photo';
  if (S.images.some(m => m.uploading)) return 'Waiting for uploads to finish';
  for (const pl of chosenPlatforms()) {
    const c = captionFor(pl);
    if (len(c) > CAPTION_MAX[pl]) return `The ${PLATFORM[pl]} caption is too long (${len(c).toLocaleString()} / ${CAPTION_MAX[pl].toLocaleString()})`;
    if (pl === 'instagram' && hashtags(c) > IG_HASHTAGS) return `Instagram allows at most ${IG_HASHTAGS} hashtags`;
  }
  if (toInstagram() && S.images.length > IG_MAX) return `Instagram posts can have at most ${IG_MAX} photos`;
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

async function addFiles(files) {
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

async function submit() {
  if (missing() || S.busy) return;
  S.busy = true; S.status = { kind: '', text: 'Sending…' }; render();
  const jobs = S.targets.map(id => ({ id, platform: platformOf(acct(id)) }))
    .sort((a, b) => ORDER.indexOf(a.platform) - ORDER.indexOf(b.platform));
  const plan = S.when === 'queue' ? queuePlan() : null;
  const at = S.when === 'later' ? Math.floor(inputToMs(S.at) / 1000) : null;
  const made = [], errors = [];
  try {
    if (toInstagram()) { S.status = { kind: '', text: 'Preparing photos for Instagram…' }; render(); }
    const keys = await keysFor(jobs.map(j => j.platform));
    for (const [n, j] of jobs.entries()) {
      if (jobs.length > 1) { S.status = { kind: '', text: `Sending ${n + 1} of ${jobs.length}…` }; render(); }
      const name = `${PLATFORM[j.platform]} ${handle(acct(j.id))}`;
      const t = S.tt[j.id] || {};
      try {
        made.push(await api('/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
          account_id: j.id, image_keys: keys[n], cover_index: S.cover, title: S.title, caption: captionFor(j.platform),
          settings: j.platform !== 'tiktok' ? {} : { privacy_level: t.privacy, disable_comment: !t.comment || !!t.info?.comment_disabled,
            auto_add_music: S.set.music, brand_organic: S.set.disclose && S.set.brand, branded_content: S.set.disclose && S.set.branded },
          scheduled_at: plan ? plan[j.id] : at,
          // An edit replaces the one post it came from.
          replaces: S.replaces && S.replacesAccount === j.id ? S.replaces : undefined,
        }) }));
      } catch (e) { errors.push(`${name}: ${e.message}`); }
    }
  } catch (e) { errors.push(e.message); }
  S.busy = false;
  if (!made.length) { S.status = { kind: 'err', text: errors.join(' · ') }; return render(); }
  if (S.fromDraft && !errors.length) await dropDrafts(S.fromDraft);
  resetComposer();
  const tail = errors.length ? ` Not sent: ${errors.join(' · ')}` : '';
  if (made[0].scheduled_at > Date.now() / 1000 + 60) {
    const first = Math.min(...made.map(p => p.scheduled_at));
    S.flash = { kind: errors.length ? 'err' : 'ok', text: `${made.length > 1 ? `${made.length} posts scheduled, the first for` : 'Scheduled for'} ${fmtFull(first)}.${tail}` };
    S.keepFlash = true;
    location.hash = '#calendar';
  } else {
    S.status = { kind: errors.length ? 'err' : '', text: `Posting… This page updates when it is done.${tail}` };
    render(); watch(made.map(p => p.id), tail);
  }
}

async function watch(ids, tail = '') {
  const done = new Map();
  for (let n = 0; n < 100 && done.size < ids.length; n++) {
    await new Promise(r => setTimeout(r, 3000));
    const t = Math.floor(Date.now() / 1000);
    let posts;
    try { posts = (await api(`/posts?from=${t - 3600}&to=${t + 60}`)).posts; }
    catch { continue; }   // one failed check is not a result; keep watching
    for (const p of posts) if (ids.includes(p.id) && (p.status === 'published' || p.status === 'failed')) done.set(p.id, p);
  }
  const all = [...done.values()];
  const failed = all.filter(p => p.status === 'failed');
  const label = p => `${PLATFORM[p.platform] || 'TikTok'} ${p.platform === 'facebook' ? '' : '@'}${p.username}`;
  if (done.size < ids.length) S.status = { kind: '', text: `Still processing. Check the Calendar for the result.${tail}` };
  else if (failed.length) S.status = { kind: 'err', text: failed.map(p => `${label(p)}: ${p.fail_reason || 'rejected'}`).join(' · ') +
    (all.length > failed.length ? ` · Published to ${all.filter(p => p.status === 'published').map(label).join(', ')}.` : '') };
  else S.status = { kind: 'ok', text: `Published to ${all.map(label).join(', ')}. It may take a few minutes to appear on the profile.${tail}` };
  render();
}

// Targets stay selected for the next post; privacy is chosen again each time.
function resetComposer() {
  Object.assign(S, { images: [], cover: 0, title: '', caption: '', when: 'now', at: '', status: null, replaces: null,
    replacesAccount: null, over: {}, fromDraft: null, draftGroup: null });
  for (const t of Object.values(S.tt)) { t.privacy = ''; t.comment = false; }
  S.set = { music: false, disclose: false, brand: false, branded: false };
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
  if (!S.images.length) return 'Add at least one photo';
  if (S.images.some(m => m.uploading)) return 'Waiting for uploads to finish';
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
    const keys = await keysFor(jobs.map(j => j.platform), { raw: true });
    for (const [n, j] of jobs.entries()) {
      const t = S.tt[j.id] || {};
      try {
        await send('/posts', 'POST', { account_id: j.id, image_keys: keys[n], cover_index: S.cover, title: S.title,
          caption: captionFor(j.platform), draft: true, group_id: group,
          settings: j.platform !== 'tiktok' ? {} : { privacy_level: t.privacy || '', disable_comment: !t.comment,
            auto_add_music: S.set.music, brand_organic: S.set.disclose && S.set.brand, branded_content: S.set.disclose && S.set.branded } });
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
  const groups = draftGroups();
  if (!groups.length) return `<section class="panel empty"><b>No drafts.</b>Use "Save draft" while creating a post to keep it for later.
    <div><a class="btn" href="#compose">${ui('plus', 16)}Create post</a></div></section>`;
  return `<div class="dgrid">${groups.map(g => {
    const d = g[0], cover = d.images[d.cover_index] || d.images[0], key = esc(d.group_id || d.id);
    return `<article class="dcard">
      <button class="dcover" data-opendraft="${key}" aria-label="Open draft">${cover ? `<img src="${esc(cover)}" alt="">` : '<span class="noimg"></span>'}
        ${d.images.length > 1 ? `<span class="dn">${d.images.length}</span>` : ''}</button>
      <div class="dbody">
        <div class="dacc">${g.slice(0, 4).map(x => withBadge(avatar(acct(x.account_id)?.avatar_url, x.username), x.platform || 'tiktok')).join('')}
          <span>${g.length === 1 ? `${g[0].platform === 'facebook' ? '' : '@'}${esc(g[0].username)}` : `${g.length} accounts`}</span></div>
        <p>${esc((d.caption || d.title || 'No caption yet').slice(0, 140))}</p>
        <small>Saved ${fmt(d.updated_at, { month: 'short', day: 'numeric' })}</small></div>
      <div class="dfoot"><button class="btn" data-opendraft="${key}">Open</button>
        <button class="btn ghost danger" data-deldraft="${key}">Delete</button></div></article>`;
  }).join('')}</div>`;
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
    caption: main, title: (tt || src).title || '', fromDraft: g.map(x => x.id), draftGroup: key, targets: [] });
  for (const x of g) if (x.caption !== main) S.over[x.platform] = x.caption;
  const s = tt?.settings || {};
  S.set = { music: !!s.auto_add_music, disclose: !!(s.brand_organic || s.branded_content), brand: !!s.brand_organic, branded: !!s.branded_content };
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

function postCard(p, compact) {
  const time = fmt(p.scheduled_at, { hour: '2-digit', minute: '2-digit' });
  const drag = p.status === 'queued' ? `draggable="true" data-drag="${p.id}"` : '';
  if (compact) {
    const img = p.images[p.cover_index] || p.images[0];
    return `<div class="mp ${p.status}" ${drag} data-open="${p.id}" role="button" tabindex="0"
        title="${esc(`${PLATFORM[p.platform] || 'TikTok'} · ${p.username} · ${p.status}${p.fail_reason ? `: ${p.fail_reason}` : ''}`)}">
      ${img ? `<img src="${esc(img)}" alt="">` : '<span class="noimg"></span>'}${icon(p.platform || 'tiktok', 11)}<b>${at(p.scheduled_at)}</b><span>${who(p)}</span></div>`;
  }
  // Week view: a small row per post. Everything you can do with it is one
  // click away in the drawer.
  const img = p.images[p.cover_index] || p.images[0];
  const label = { published: 'Published', failed: 'Failed', queued: 'Scheduled', publishing: 'Posting', cancelled: 'Cancelled' }[p.status] || p.status;
  return `<div class="pc ${p.status}" ${drag} data-open="${p.id}" role="button" tabindex="0"
      title="${esc(`${label}${p.fail_reason ? `: ${p.fail_reason}` : ''}`)}">
    ${img ? `<img src="${esc(img)}" alt="">` : '<span class="noimg"></span>'}
    <div class="pt"><b>${icon(p.platform || 'tiktok', 12)}${at(p.scheduled_at)}</b>
      <span>${who(p)}</span>
      <em>${label}</em></div></div>`;
}

function calendarView() {
  const r = calRange(), month = S.calMode === 'month', grid = S.calMode !== 'week';
  const accts = S.me.accounts;
  const plats = ORDER.filter(pl => accts.some(a => platformOf(a) === pl));
  const posts = S.posts.filter(p => (S.fPlat === 'all' || (p.platform || 'tiktok') === S.fPlat)
    && (S.fAcct === 'all' || p.account_id === S.fAcct)
    && (S.fBrand === 'all' || acct(p.account_id)?.brand_id === S.fBrand));
  const shown = accts.filter(a => (S.fPlat === 'all' || platformOf(a) === S.fPlat)
    && (S.fBrand === 'all' || a.brand_id === S.fBrand));
  const days = [...Array(r.n)].map((_, i) => addDays(r.start, i));
  const now = dayKey(today()), offset = month ? S.month : S.week;
  const empty = !posts.length;
  const filters = accts.length ? `<div class="chips">
      ${S.me.brands.length ? `<select id="fbrand" style="width:auto;padding:5px 10px">
        <option value="all">All brands</option>
        ${S.me.brands.map(b => `<option value="${b.id}" ${S.fBrand === b.id ? 'selected' : ''}>${esc(b.name)}</option>`).join('')}
      </select>` : ''}
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
      <a class="btn" href="#compose" style="margin-left:auto;text-decoration:none">New post</a>
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
  const p = S.posts.find(x => x.id === S.detail) || S.stats?.top?.find(x => x.id === S.detail);
  if (!p) return '';
  const a = acct(p.account_id), editable = p.status === 'queued', pl = p.platform || 'tiktok';
  const label = { published: 'Published', failed: 'Failed', queued: 'Scheduled', publishing: 'Posting', cancelled: 'Cancelled' }[p.status] || p.status;
  const cover = p.images[p.cover_index] || p.images[0];
  return `<div class="overlay" id="overlay"><aside class="drawer" role="dialog" aria-modal="true" aria-label="Post details">
    <header class="dh">${withBadge(avatar(a?.avatar_url, p.username), pl)}
      <div><b>${pl === 'facebook' ? '' : '@'}${esc(p.username)}</b><span>${PLATFORM[pl]}</span></div>
      <button class="xbtn" id="closedetail" aria-label="Close">${ui('x', 18)}</button></header>
    <div class="dscroll">
      <div class="dwhen"><span class="st ${p.status === 'queued' ? 'queued' : p.status}">${label}</span>
        <b>${fmt(p.scheduled_at, { weekday: 'long', month: 'short', day: 'numeric' })} · ${at(p.scheduled_at)}</b>
        <small>${esc(tz().replace(/_/g, ' '))}</small></div>
      ${p.fail_reason ? `<div class="dfail">${ui('x', 15)}<span>${esc(p.fail_reason)}</span></div>` : ''}
      ${p.stats ? `<div class="dstats">${STAT_KEYS.filter(k => p.stats[k] != null).map(k => `<div><b>${num(p.stats[k])}</b><span>${METRIC[k]}</span></div>`).join('')}</div>` : ''}
      ${cover ? `<div class="dmedia"><img class="big" src="${esc(cover)}" alt="Cover">
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
    when: again ? 'now' : 'later', at: localInput(Math.max(p.scheduled_at * 1000, Date.now() + 10 * 60e3)) });
  const s = p.settings || {};
  S.set = { music: !!s.auto_add_music, disclose: !!(s.brand_organic || s.branded_content),
            brand: !!s.brand_organic, branded: !!s.branded_content };
  S.targets = [];
  toggleTarget(p.account_id, true, false);
  if (S.tt[p.account_id]) S.tt[p.account_id].comment = !s.disable_comment;
  location.hash = '#compose';
  render();
  if (again) {
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
        <option value="">No brand</option>
        ${S.me.brands.map(b => `<option value="${b.id}" ${x.brand_id === b.id ? 'selected' : ''}>${esc(b.name)}</option>`).join('')}
      </select>
      ${x.needs_reconnect && connectHref(pl) ? `<a class="btn" href="${connectHref(pl)}">Reconnect</a>` : ''}
      <button class="btn ghost danger" data-disc="${x.id}">Disconnect</button></div></div>`;
}

function accountsView() {
  const a = S.me.accounts, groups = brandGroups();
  const hint = { tiktok: 'Photo posts with TikTok\'s own privacy and disclosure settings.',
    instagram: 'Business or Creator accounts. No Facebook Page needed.', facebook: 'Every Page you manage, in one go.' };
  return `<section class="panel"><header><h2>Connect an account</h2><span class="note">${a.length} of ${S.me.limits.accounts} connected</span></header>
      <div class="connect">${ORDER.filter(connectHref).map(pl => `<a class="ccard" href="${connectHref(pl)}">
          ${appIcon(pl, 40)}<div><b>${PLATFORM[pl]}</b><span>${hint[pl]}</span></div><span class="go">${ui('plus', 16)}</span></a>`).join('')}</div>
      <details class="hints"><summary>Adding more than one account per platform</summary>
        ${ORDER.map(pl => `<p>${appIcon(pl, 16)}<span>${PLATFORM_HINT[pl]}</span></p>`).join('')}</details></section>

    ${groups.map(g => {
      const b = S.me.brands.find(x => x.id === g.id);
      return `<section class="panel brand">
        <header><h2>${esc(g.name)}</h2><span class="note">${g.accounts.length} account${g.accounts.length === 1 ? '' : 's'}</span>
          ${b ? `<span class="hacts"><button class="btn ghost" data-rename="${g.id}">Rename</button><button class="btn ghost danger" data-delbrand="${g.id}">Delete</button></span>` : ''}</header>
        ${b ? `<div class="bmeta">${slotsEditor(g.id, b.slots, 'Posting times', S.me.workspace.slots)}${voiceLine(g.id)}</div>` : ''}
        <div class="agrid">${g.accounts.map(accountCard).join('') || '<p class="note">No accounts in this brand yet. Pick it in any account\'s brand menu.</p>'}</div></section>`;
    }).join('') || '<section class="panel empty"><b>No accounts yet.</b>Connect TikTok, Instagram or a Facebook Page above.</section>'}

    <form id="newbrand" class="panel newbrand2"><span>${ui('plus', 16)}</span>
      <input type="text" id="brandname" maxlength="60" placeholder="New brand, e.g. Client Bakery" aria-label="New brand name">
      <button class="btn">Create brand</button></form>
    <p class="foot-note">Disconnecting deletes the account's token and cancels its scheduled posts. Deleting a brand only ungroups its accounts.
      You can also revoke access in TikTok, Instagram or Facebook's own settings at any time.</p>`;
}

const SET_TABS = () => [['workspace', 'Workspace'], ...(can('admin') ? [['people', 'People']] : []), ['account', 'Your account'], ...(can('owner') ? [['developer', 'Developer']] : [])];
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
    ${!m ? '<div class="empty">Loading…</div>' : `<div class="plist">
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
  if (tab === 'account') body = `<section class="panel">
    ${srow('Email', 'You sign in with a code sent here.', `<b>${esc(S.me.user?.email || '')}</b>`)}
    ${srow('Sign out', 'On this device, or on every device at once.', '<a class="btn sec" href="/api/auth/logout">Sign out</a><button class="btn ghost" id="logoutall">Sign out everywhere</button>')}
  </section>`;
  if (tab === 'developer') body = `<section class="panel">
    ${srow('API key', 'For posting from your own tools. It can do everything an admin can. A new key disables the old one.',
      `${S.apiKey ? `<code class="key">${esc(S.apiKey)}</code><span class="note warn">Copy it now. It won't be shown again.</span>` : ''}<button class="btn sec" id="apikey">${S.me.api_key_set ? 'Create a new key' : 'Create key'}</button>`)}
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

document.addEventListener('keydown', e => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches?.('[role=button][data-open], .day.open[role=button]')) { e.preventDefault(); e.target.click(); return; }
  if (e.key === 'Tab' && $('overlay')) {
    const f = [...$('overlay').querySelectorAll('button,a[href],textarea,input,select')].filter(x => !x.disabled);
    if (f.length && e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (f.length && !e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  }
  if (e.key !== 'Escape') return;
  if (S.pickOpen) { S.pickOpen = false; render(); $('openpick')?.focus(); } else if (S.detail) { S.detail = null; render(); } });
// The account dropdown closes when you click anywhere outside it.
document.addEventListener('pointerdown', e => { if (S.pickOpen && !e.target.closest('.dd')) { S.pickOpen = false; render(); } });

function bind() {
  const on = (sel, ev, fn) => document.querySelectorAll(sel).forEach(el => el.addEventListener(ev, fn));
  on('#files', 'change', e => addFiles(e.target.files));
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
    if (!confirm(leave ? 'Leave this workspace? You lose access to its accounts and posts.' : 'Remove this person from the workspace?')) return;
    if (leave) { try { await send(`/members/${id}`, 'DELETE'); await loadMe(); S.members = null; route(); } catch (x) { S.flash = { kind: 'err', text: x.message }; render(); } }
    else peopleAction(() => send(`/members/${id}`, 'DELETE'), 'Removed.'); });
  on('[data-transfer]', 'click', async e => {
    const { transfer, email } = e.target.dataset;
    if (prompt(`Make ${email} the owner? You become an admin and cannot undo this yourself. Type their email to confirm.`) !== email) return;
    try { await send('/workspace/transfer', 'POST', { user_id: transfer }); await loadMe(); S.members = null;
      S.flash = { kind: 'ok', text: `${email} now owns this workspace. You are an admin.` }; route(); }
    catch (x) { S.flash = { kind: 'err', text: x.message }; render(); } });
  on('#logoutall', 'click', async () => { if (!confirm('Sign out on every device?')) return;
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
  on('#closepick', 'click', () => { S.pickOpen = false; render(); });
  on('[data-bg]', 'change', e => pickGroup(e.target.dataset.bg, e.target.checked));
  document.querySelectorAll('[data-state=some]').forEach(el => { el.indeterminate = true; });
  on('#pq', 'input', e => { S.pq = e.target.value; const at = e.target.selectionStart; render();
    const el = $('pq'); if (el) { el.focus(); el.setSelectionRange(at, at); } });
  on('#fbrand', 'change', e => { S.fBrand = e.target.value; S.fAcct = 'all'; render(); });
  on('#newbrand', 'submit', e => { e.preventDefault(); const name = $('brandname').value;
    brandAction(() => send('/brands', 'POST', { name })); });
  on('[data-move]', 'change', e => brandAction(() => send(`/accounts/${e.target.dataset.move}`, 'PATCH', { brand_id: e.target.value || null })));
  on('[data-rename]', 'click', e => { const id = e.target.dataset.rename;
    const name = prompt('Rename brand', brandName(id) || ''); if (name) brandAction(() => send(`/brands/${id}`, 'PATCH', { name })); });
  on('[data-delbrand]', 'click', e => { const id = e.target.dataset.delbrand;
    if (confirm(`Delete the brand "${brandName(id)}"? Its accounts stay connected, just ungrouped.`)) brandAction(() => send(`/brands/${id}`, 'DELETE')); });
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
  on('[data-opendraft]', 'click', e => openDraft(e.target.dataset.opendraft));
  on('[data-deldraft]', 'click', async e => {
    const key = e.target.dataset.deldraft, g = draftGroups().find(x => (x[0].group_id || x[0].id) === key);
    if (!g || !confirm('Delete this draft?')) return;
    await dropDrafts(g.map(x => x.id)); loadDrafts(); });
  on('#stopedit', 'click', () => { resetComposer(); location.hash = '#calendar'; });
  on('[data-fp]', 'click', e => { S.fPlat = e.target.dataset.fp; S.fAcct = 'all'; render(); });
  on('#facct', 'change', e => { S.fAcct = e.target.value; render(); });
  on('[data-again]', 'click', e => { S.detail = null; edit(e.target.dataset.again, true); });
  on('[data-wk]', 'click', e => { const d = Number(e.currentTarget.dataset.wk); if (S.calMode === 'month') S.month += d; else S.week += d * (S.calMode === 'weeks' ? 4 : 1); loadWeek(); });
  on('[data-open]', 'click', e => { if (e.target.closest('button,a')) return; S.detail = e.currentTarget.dataset.open; render(); });
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
  on('[data-retry]', 'click', async e => { try { await api(`/posts/${e.target.dataset.retry}/retry`, { method: 'POST' }); S.detail = null; S.flash = { kind: 'ok', text: 'Retrying. It goes out within a minute.' }; } catch (x) { S.flash = { kind: 'err', text: x.message }; } reloadView(); refreshCounts(); });
  on('[data-edit]', 'click', e => { S.detail = null; edit(e.target.dataset.edit); });
  on('[data-disc]', 'click', async e => {
    if (!confirm('Disconnect this account? Its scheduled posts will be cancelled.')) return;
    const id = e.target.dataset.disc;
    await api(`/accounts/${id}`, { method: 'DELETE' }); S.me = await api('/me');
    S.targets = S.targets.filter(x => x !== id); saveTargets(); render();
  });
  on('[data-settab]', 'click', e => { S.setTab = e.currentTarget.dataset.settab; render(); });
  on('#apikey', 'click', async () => { S.apiKey = (await api('/api-key', { method: 'POST' })).api_key; S.me.api_key_set = true; render(); });
  on('#delws', 'click', async () => {
    if (prompt(`Type the workspace name to delete it: ${S.me.workspace.name}`) !== S.me.workspace.name) return;
    await api('/me', { method: 'DELETE' }); location.href = '/api/auth/logout';
  });
}

boot();
