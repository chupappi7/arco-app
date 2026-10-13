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
// The platform's mark pinned to the corner of an account's avatar.
const withBadge = (av, pl) => `<span class="avw">${av}<span class="badge-pl ${pl}">${icon(pl, 10)}</span></span>`;
const connectBtn = (pl, href, text) => `<a class="btn brand ${pl}" href="${href}">${icon(pl, 16)}<span>${text}</span></a>`;
// Instagram takes JPEG between 4:5 (portrait) and 1.91:1 (landscape), 10 per post.
const IG_MIN_RATIO = 4 / 5, IG_MAX_RATIO = 1.91, IG_MAX = 10, IG_CAPTION = 2200;
const CAPTION_MAX = { tiktok: 4000, instagram: IG_CAPTION, facebook: 63206 };
const IG_HASHTAGS = 30;
const hashtags = s => (String(s).match(/#[^\s#]+/g) || []).length;

const S = {
  me: null, view: 'compose', flash: null,
  images: [], cover: 0, title: '', caption: '',
  // Every account the post goes to, any platform. TikTok accounts each carry
  // their own creator info, privacy and comment choice in S.tt.
  targets: [], tt: {},
  // A caption per platform, when it should differ from the main one. Absent
  // means "same as the main caption".
  over: {},
  drafts: [], fromDraft: null, draftGroup: null,
  slotEdit: null, queuePosts: null,
  set: { music: false, disclose: false, brand: false, branded: false },
  when: 'now', at: '', busy: false, status: null,
  week: 0, month: 0, calMode: 'week', fPlat: 'all', fAcct: 'all', fBrand: 'all', posts: [], apiKey: null,
  pickOpen: false, pq: '',
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
  window.addEventListener('hashchange', () => { if (!S.keepFlash) S.flash = null; S.keepFlash = false; route(); });
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
}

// The accounts last posted to come back preselected: someone running ten
// accounts posts to the same set most days.
function restoreTargets() {
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(SAVED) || '[]'); } catch {}
  for (const id of saved) { const a = acct(id); if (a && !a.needs_reconnect) toggleTarget(id, true, false); }
}
function saveTargets() { try { localStorage.setItem(SAVED, JSON.stringify(S.targets)); } catch {} }

function route() {
  S.view = (location.hash || '#compose').slice(1);
  if (!['compose', 'calendar', 'drafts', 'accounts', 'settings'].includes(S.view)) S.view = 'compose';
  if (S.view === 'calendar') loadWeek();
  if (S.view === 'drafts') loadDrafts();
  render();
}

// ---- render ------------------------------------------------------------

function render() {
  const signedIn = !!S.me && !S.me.needs_email;
  $('tabs').hidden = !signedIn;
  $('wsbar').innerHTML = signedIn ? wsBar() : '';
  document.querySelectorAll('#tabs a').forEach(a => {
    a.classList.toggle('on', a.dataset.v === S.view);
    a.hidden = a.dataset.v === 'accounts' && !can('admin');
  });
  const flash = S.flash ? `<div class="status ${S.flash.kind}">${esc(S.flash.text)}</div>` : '';
  if (!signedIn) { $('app').innerHTML = flash + signInView(); bind(); return; }
  if (S.view === 'accounts' && !can('admin')) S.view = 'compose';
  const views = { calendar: calendarView, drafts: draftsView, accounts: accountsView, settings: settingsView, compose: composeView };
  $('app').innerHTML = flash + views[S.view]();
  bind();
}

// ---- sign in: email, then the 6-digit code it receives ---------------------

function signInView() {
  const L = S.login, claiming = S.me?.needs_email;
  let invited = false;
  try { invited = !!sessionStorage.getItem(INVITE); } catch {}
  return `<div class="card signin"><div class="sec">
    <span class="cap">${claiming ? 'Add your email' : 'Sign in or create an account'}</span>
    <p style="margin:0 0 16px;color:var(--muted)">${claiming
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
  </div></div>`;
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
  if (!S.me.accounts.length) return `<div class="card"><div class="sec">${can('admin')
    ? 'Connect an account in <a href="#accounts">Accounts</a> first.'
    : 'No accounts are shared with you yet. Ask a workspace admin to give you access to a brand.'}</div></div>`;
  const tts = ttTargets();
  const label = S.set.branded ? 'Paid partnership' : S.set.brand ? 'Promotional content' : '';
  const need = missing();
  return `${S.fromDraft ? `<div class="status">Editing a draft. Scheduling or posting it replaces the draft.
      <button class="btn sec" id="stopedit" style="margin-left:8px">Close draft</button></div>` : ''}${S.replaces ? `<div class="status">Editing a scheduled post. The original stays scheduled until you save this one.
      <button class="btn sec" id="stopedit" style="margin-left:8px">Stop editing</button></div>` : ''}
  <div class="card">
    <div class="sec"><span class="cap">Post to</span>${postToView()}</div>
    <div class="sec"><span class="cap">Photos</span>
      <div class="thumbs">${S.images.map((m, n) => `<div class="th ${n === S.cover ? 'cover' : ''}">
          ${n === S.cover ? '<span class="badge">Cover</span>' : ''}
          <img src="${esc(m.url)}" alt="Slide ${n + 1}" data-cover="${n}" title="Set as cover">
          <div class="ctl"><button data-mv="${n}:-1" aria-label="Move left">‹</button>
            <button data-rm="${n}" aria-label="Remove">×</button>
            <button data-mv="${n}:1" aria-label="Move right">›</button></div></div>`).join('')}
      </div>
      <p><input type="file" id="files" accept="image/jpeg,image/png" multiple ${S.images.length >= 35 ? 'disabled' : ''}></p>
      <span class="note">JPG or PNG, up to ${toInstagram() ? `${IG_MAX} for Instagram` : 35} images, 5 MB each. Click an image to make it the cover.
        ${toInstagram() ? 'Tall slides are padded to 4:5 for Instagram, never cropped.' : ''}</span>
    </div>
    <div class="sec">
      ${tts.length ? `<label class="f" for="title">Title <span class="note">(TikTok only)</span></label>
      <input type="text" id="title" maxlength="200" value="${esc(S.title)}">
      <div class="count ${len(S.title) > 90 ? 'note bad' : ''}">${len(S.title)} / 90</div>` : ''}
      <label class="f" for="caption">Caption${chosenPlatforms().length > 1 ? ' <span class="note">(used everywhere unless customized below)</span>' : ''}</label>
      <textarea id="caption">${esc(S.caption)}</textarea>
      <div class="limits" id="caplimits">${limitsLine()}</div>
      ${overridesView()}
    </div>
    ${tts.length ? `<div class="sec"><span class="cap">TikTok settings</span>
      ${tts.length > 1 ? `<div class="bulk"><label class="f" for="bulkpriv">Set who can view for every account</label>
        <select id="bulkpriv"><option value="">Choose…</option>
          ${Object.keys(PRIVACY_LABEL).filter(o => !(o === 'SELF_ONLY' && S.set.branded)).map(o => `<option value="${o}">${PRIVACY_LABEL[o]}</option>`).join('')}
        </select><span class="note">Accounts that do not offer that option keep their own choice.</span></div>` : ''}
      ${tts.map(ttCard).join('')}
      ${row('Duet', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
      ${row('Stitch', 'Video posts only, not available for photo posts.', '<input type="checkbox" disabled>')}
      ${row('Add recommended music', 'Lets TikTok pick a track for the slideshow.', `<input type="checkbox" data-k="music" ${S.set.music ? 'checked' : ''}>`)}
    </div>
    <div class="sec"><span class="cap">Disclosure</span>
      ${row('Disclose post content', 'Turn on if this post promotes yourself, a brand, product or service.',
        `<input type="checkbox" data-k="disclose" ${S.set.disclose ? 'checked' : ''}>`)}
      ${S.set.disclose ? `<div style="padding:8px 0">
        <label><input type="checkbox" data-k="brand" ${S.set.brand ? 'checked' : ''}> Your brand</label>
        &nbsp;&nbsp;<label><input type="checkbox" data-k="branded" ${S.set.branded ? 'checked' : ''}> Branded content</label>
        <p class="note ${label ? 'warn' : ''}">${label ? `Your photo post will be labeled "${label}".` : 'You need to indicate if your content promotes yourself, a third party, or both.'}</p>
      </div>` : ''}
    </div>` : ''}
    <div class="sec"><span class="cap">Preview</span>
      <div class="thumbs">${S.images.map(m => `<img src="${esc(m.url)}" alt="" style="width:56px;height:100px;object-fit:cover;border-radius:6px">`).join('') || '<span class="note">Add photos to see them here.</span>'}</div>
      ${S.title && tts.length ? `<p><b>${esc(S.title)}</b></p>` : ''}${S.caption ? `<p class="note" style="white-space:pre-wrap">${esc(S.caption)}</p>` : ''}
    </div>
    <div class="sec"><span class="cap">When</span>
      <label><input type="radio" name="when" value="now" ${S.when === 'now' ? 'checked' : ''}> Post now</label>
      &nbsp;&nbsp;<label><input type="radio" name="when" value="queue" ${S.when === 'queue' ? 'checked' : ''}> Add to queue</label>
      &nbsp;&nbsp;<label><input type="radio" name="when" value="later" ${S.when === 'later' ? 'checked' : ''}> Pick a time</label>
      ${S.when === 'queue' ? queuePreview() : ''}
      ${S.when === 'later' ? `<p><input type="datetime-local" id="at" value="${esc(S.at)}" min="${localInput(Date.now() + 6 * 60e3)}"></p>
        <span class="note">In ${esc(tz().replace(/_/g, ' '))} time${S.me.workspace.timezone ? ' (the workspace\'s zone)' : ''}. At least 5 minutes from now.</span>` : ''}
    </div>
    ${tts.length ? `<div class="consent">By posting, you agree to TikTok's
      ${S.set.branded ? '<a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank" rel="noopener">Branded Content Policy</a> and ' : ''}
      <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en" target="_blank" rel="noopener">Music Usage Confirmation</a>.</div>` : ''}
    <div class="foot">
      <button class="btn" id="go" ${need || S.busy ? 'disabled' : ''} title="${esc(need || '')}">
        ${S.busy ? 'Working…' : `${S.when === 'later' ? 'Schedule' : 'Post'}${S.targets.length ? ` to ${goLabel()}` : ''}`}</button>
      <button class="btn sec" id="savedraft" ${draftBlocker() || S.busy ? 'disabled' : ''} title="${esc(draftBlocker())}">Save draft</button>
      ${need ? `<span class="note">${esc(need)}</span>` : ''}
      ${S.status ? `<div class="status ${S.status.kind}" style="flex-basis:100%">${esc(S.status.text)}</div>` : ''}
      <span class="note" style="flex-basis:100%">After posting, it may take a few minutes for the post to process and appear on the profile.</span>
    </div>
  </div>`;
}

const avatar = (url, name) => url
  ? `<img class="av" src="${esc(url)}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'av ini',textContent:'${esc((name || '?')[0].toUpperCase())}'}))">`
  : `<span class="av ini">${esc((name || '?')[0].toUpperCase())}</span>`;
const handle = a => `${platformOf(a) === 'facebook' ? '' : '@'}${esc(a.username || a.display_name)}`;

// ---- the "Post to" picker: chips for what is chosen, and a searchable
// panel grouped by brand, like Business Suite's account switcher.

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

function postToView() {
  const chosen = S.targets.map(acct).filter(Boolean);
  return `<div class="chosen">
      ${chosen.map(a => `<span class="chipacc">${withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))}
        <span>${handle(a)}</span><button class="x" data-unpick="${a.id}" aria-label="Remove ${esc(a.username)}">×</button></span>`).join('')
        || '<span class="note">No accounts chosen yet.</span>'}
      <button class="btn sec" id="openpick" aria-expanded="${S.pickOpen}">${S.pickOpen ? 'Done' : chosen.length ? 'Change accounts' : 'Choose accounts'}</button>
    </div>
    ${S.pickOpen ? pickPanel() : ''}`;
}

function pickPanel() {
  const q = S.pq.trim().toLowerCase();
  const hit = a => !q || [a.username, a.display_name, PLATFORM[platformOf(a)], brandName(a.brand_id)]
    .some(v => String(v || '').toLowerCase().includes(q));
  const groups = brandGroups(S.me.accounts.filter(hit)).filter(g => g.accounts.length);
  return `<div class="pickpanel">
    <input type="text" id="pq" placeholder="Search accounts or brands" value="${esc(S.pq)}" autocomplete="off">
    ${groups.map(g => {
      const usable = g.accounts.filter(a => !a.needs_reconnect);
      const on = usable.filter(a => S.targets.includes(a.id)).length;
      const state = !on ? 'none' : on === usable.length ? 'all' : 'some';
      return `<div class="bgroup">
        <label class="bhead"><input type="checkbox" data-bg="${g.id}" data-state="${state}" ${state === 'all' ? 'checked' : ''} ${usable.length ? '' : 'disabled'}>
          <b>${esc(g.name)}</b><span class="marks">${marks(g.accounts)}</span><span class="note">${on ? `${on} of ` : ''}${g.accounts.length}</span></label>
        ${g.accounts.map(a => `<label class="prow ${a.needs_reconnect ? 'off' : ''}">
          <input type="checkbox" data-t="${a.id}" ${S.targets.includes(a.id) ? 'checked' : ''} ${a.needs_reconnect ? 'disabled' : ''}>
          ${withBadge(avatar(a.avatar_url, a.username || a.display_name), platformOf(a))}
          <span class="nm"><b>${handle(a)}</b><span class="note">${PLATFORM[platformOf(a)]}${a.needs_reconnect
            ? ' · <a href="#accounts">reconnect</a>' : a.display_name && a.display_name !== a.username ? ` · ${esc(a.display_name)}` : ''}</span></span>
        </label>`).join('')}
      </div>`;
    }).join('') || '<p class="note">No account matches.</p>'}
    ${can('admin') ? '<p class="note" style="margin:8px 0 0"><a href="#accounts">Manage accounts and brands</a></p>' : ''}
  </div>`;
}

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

function overridesView() {
  const pls = chosenPlatforms();
  if (pls.length < 2 && !pls.some(pl => S.over[pl] != null)) return '';
  return `<div class="overrides">${pls.map(pl => S.over[pl] == null
    ? `<button type="button" class="chip" data-custom="${pl}">${icon(pl, 13)} Customize for ${PLATFORM[pl]}</button>`
    : `<div class="ov"><label class="f" for="ov-${pl}">${icon(pl, 13)} ${PLATFORM[pl]} caption</label>
        <textarea id="ov-${pl}" data-ov="${pl}">${esc(S.over[pl])}</textarea>
        <button type="button" class="link" data-uncustom="${pl}">Use the main caption for ${PLATFORM[pl]}</button></div>`).join('')}</div>`;
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

function slotsEditor(key, current, label) {
  const x = S.slotEdit;
  if (!x || x.key !== key) {
    return `<div class="slotline"><span class="note">${label}: <b>${esc(slotsText(current))}</b></span>
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
  try { S.drafts = (await api('/drafts')).drafts; } catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}

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
  return `<div class="drafts">${groups.map(g => {
    const d = g[0], cover = d.images[d.cover_index] || d.images[0];
    return `<div class="card draft"><div class="sec">
      ${cover ? `<img src="${esc(cover)}" alt="">` : ''}
      <div class="dtxt"><div class="marks">${g.map(x => icon(x.platform, 13)).join('')}
        <span class="note">${g.map(x => `${x.platform === 'facebook' ? '' : '@'}${esc(x.username)}`).join(', ')}</span></div>
        <p>${esc((d.caption || d.title || 'No caption yet').slice(0, 160))}</p>
        <span class="note">${d.images.length} photo${d.images.length === 1 ? '' : 's'} · saved ${fmtFull(d.updated_at)}</span></div>
      <div class="dacts"><button class="btn" data-opendraft="${esc(d.group_id || d.id)}">Open</button>
        <button class="btn danger" data-deldraft="${esc(d.group_id || d.id)}">Delete</button></div>
    </div></div>`;
  }).join('') || `<div class="card"><div class="sec"><p class="note" style="margin:0">No drafts. Use "Save draft" in
    <a href="#compose">New post</a> to keep a post for later.</p></div></div>`}</div>`;
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
  const end = addDays(start, 6);
  return { start, n: 7, title: `${dayLabel(start, { day: 'numeric', month: 'short' })} – ${dayLabel(end, { day: 'numeric', month: 'short' })}` };
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
    return `<div class="pill-post ${p.status}" ${drag} title="${esc(`${PLATFORM[p.platform] || 'TikTok'} · ${p.username} · ${p.status}`)}">
      ${icon(p.platform || 'tiktok', 11)}<span>${time}</span></div>`;
  }
  return `<div class="pc" ${drag}>
    ${p.images[p.cover_index] ? `<img src="${esc(p.images[p.cover_index])}" alt="">` : ''}
    <div class="when" title="${PLATFORM[p.platform] || 'TikTok'}">${icon(p.platform || 'tiktok', 13)}${time}</div>
    <div class="note">${p.platform === 'facebook' ? '' : '@'}${esc(p.username)}</div>
    <span class="pill ${p.status}">${p.status}</span>
    ${p.fail_reason ? `<div class="note ${p.status === 'failed' ? 'bad' : ''}">${esc(p.fail_reason)}</div>` : ''}
    <div class="acts">
      ${p.status === 'queued' ? `<button data-edit="${p.id}">Edit</button><button data-cancel="${p.id}">Cancel</button>` : ''}
      ${p.status === 'failed' ? `<button data-retry="${p.id}">Retry</button><button data-edit="${p.id}">Edit</button>` : ''}
      ${p.status === 'published' || p.status === 'cancelled' ? `<button data-again="${p.id}">Post again</button>` : ''}
      ${p.post_url ? `<a href="${esc(p.post_url)}" target="_blank" rel="noopener">View</a>` : ''}
    </div></div>`;
}

function calendarView() {
  const r = calRange(), month = S.calMode === 'month';
  const accts = S.me.accounts;
  const plats = ORDER.filter(pl => accts.some(a => platformOf(a) === pl));
  const posts = S.posts.filter(p => (S.fPlat === 'all' || (p.platform || 'tiktok') === S.fPlat)
    && (S.fAcct === 'all' || p.account_id === S.fAcct)
    && (S.fBrand === 'all' || acct(p.account_id)?.brand_id === S.fBrand));
  const shown = accts.filter(a => (S.fPlat === 'all' || platformOf(a) === S.fPlat)
    && (S.fBrand === 'all' || a.brand_id === S.fBrand));
  const days = [...Array(r.n)].map((_, i) => addDays(r.start, i));
  const now = dayKey(today()), offset = month ? S.month : S.week;
  return `<div class="chips">
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
    </div>
    <div class="calbar">
      <button class="btn sec" data-wk="-1" ${offset <= 0 ? 'disabled' : ''} aria-label="Previous">‹</button>
      <b>${r.title}</b>
      <button class="btn sec" data-wk="1" aria-label="Next">›</button>
      <span class="seg"><button class="${month ? '' : 'on'}" data-mode="week">Week</button><button class="${month ? 'on' : ''}" data-mode="month">Month</button></span>
      <span class="note">${esc(tz().replace(/_/g, ' '))} · drag a scheduled post to move it</span>
      <a class="btn" href="#compose" style="margin-left:auto;text-decoration:none">New post</a>
    </div>
    ${month ? `<div class="monthhead">${days.slice(0, 7).map(d => `<span>${dayLabel(d, { weekday: 'short' })}</span>`).join('')}</div>` : ''}
    <div class="${month ? 'month' : 'week'}">${days.map(d => {
      const ps = posts.filter(p => dayOf(p.scheduled_at) === dayKey(d));
      const out = month && d.m !== r.month;
      return `<div class="day ${dayKey(d) === now ? 'today' : ''} ${out ? 'out' : ''}" data-day="${d.y}-${d.m}-${d.d}">
        <h4>${month ? d.d : dayLabel(d, { weekday: 'short', day: 'numeric' })}</h4>
        ${ps.map(p => postCard(p, month)).join('') || (month ? '' : '<span class="note">Nothing yet</span>')}
      </div>`;
    }).join('')}</div>`;
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

function accountRow(x) {
  const pl = platformOf(x);
  return `<div class="row acctrow"><span class="txt who">${withBadge(avatar(x.avatar_url, x.username || x.display_name), pl)}
      <span><span class="t">${handle(x)}</span><span class="d">${x.needs_reconnect
        ? '<span class="note bad">Access was revoked or expired. Reconnect to keep posting.</span>'
        : `${PLATFORM[pl]}${x.display_name && x.display_name !== x.username ? ` · ${esc(x.display_name)}` : ''}`}</span></span></span>
    <select data-move="${x.id}" aria-label="Brand for ${esc(x.username)}" class="move">
      <option value="">Not in a brand</option>
      ${S.me.brands.map(b => `<option value="${b.id}" ${x.brand_id === b.id ? 'selected' : ''}>${esc(b.name)}</option>`).join('')}
    </select>
    ${x.needs_reconnect && connectHref(pl) ? `<a class="btn sec" href="${connectHref(pl)}" style="text-decoration:none">Reconnect</a>` : ''}
    <button class="btn danger" data-disc="${x.id}">Disconnect</button></div>`;
}

function accountsView() {
  const a = S.me.accounts;
  const groups = brandGroups();
  return `<div class="card"><div class="sec">
      <div class="phead"><b>Connect accounts</b><span class="note">${a.length} of ${S.me.limits.accounts} connected</span></div>
      <div class="brands">${ORDER.filter(connectHref).map(pl => connectBtn(pl, connectHref(pl), `Add ${PLATFORM[pl]}`)).join('')}</div>
      <details class="hints"><summary>Tips for adding more than one account</summary>
        ${ORDER.map(pl => `<p class="note">${icon(pl, 12)} ${PLATFORM_HINT[pl]}</p>`).join('')}</details>
    </div>
    <div class="sec"><div class="phead"><b>Brands</b><span class="note">Group each client's or product's accounts, then post to the whole brand in one click.</span></div>
      <form id="newbrand" class="newbrand"><input type="text" id="brandname" maxlength="60" placeholder="New brand name, e.g. Client Bakery">
        <button class="btn">Create brand</button></form>
    </div></div>
    ${groups.map(g => `<div class="card brandcard">
      <div class="sec"><div class="phead">
        <b>${esc(g.name)}</b><span class="marks">${marks(g.accounts)}</span><span class="note">${g.accounts.length} account${g.accounts.length === 1 ? '' : 's'}</span>
        ${g.id !== 'none' ? `<span class="bacts"><button class="link" data-rename="${g.id}">Rename</button>
          <button class="link danger" data-delbrand="${g.id}">Delete</button></span>` : ''}</div>
        ${g.id !== 'none' ? slotsEditor(g.id, S.me.brands.find(b => b.id === g.id)?.slots,
          S.me.brands.find(b => b.id === g.id)?.slots ? 'Posting times' : `Posting times (workspace default: ${slotsText(S.me.workspace.slots)})`) : ''}
        ${g.accounts.map(accountRow).join('') || '<p class="note">No accounts yet. Use "Brand" on any account below to move it here.</p>'}
      </div></div>`).join('') || '<div class="card"><div class="sec"><p class="note">No accounts connected yet.</p></div></div>'}
    <p class="note">Disconnecting an account deletes its token and cancels its scheduled posts. Deleting a brand only ungroups its accounts.
      Revoke access any time in TikTok (Settings and privacy › Security &amp; permissions › Apps and services),
      Instagram (Settings › Website permissions › Apps and websites) or Facebook (Settings › Business integrations).</p>`;
}

function settingsView() {
  const w = S.me.workspace, owner = can('owner'), admin = can('admin');
  if (admin && S.members === null) loadMembers();
  const brandPick = (name, chosen) => S.me.brands.length ? `<div class="scope">
      <label><input type="radio" name="${name}" value="all" ${!chosen ? 'checked' : ''}> All brands</label>
      <label><input type="radio" name="${name}" value="some" ${chosen ? 'checked' : ''}> Only:</label>
      ${S.me.brands.map(b => `<label class="bchk"><input type="checkbox" data-scope="${name}" value="${b.id}" ${chosen?.includes(b.id) ? 'checked' : ''}> ${esc(b.name)}</label>`).join('')}
    </div>` : '';
  const m = S.members;
  return `<div class="card">
    <div class="sec"><span class="cap">Workspace</span>
      ${admin ? `<form id="wsname" class="newbrand"><input type="text" id="wsnamein" maxlength="60" value="${esc(w.name)}" aria-label="Workspace name">
        <button class="btn sec">Rename</button></form>
        <label class="f" for="wstz" style="margin-top:12px">Time zone for scheduling and the calendar</label>
        <select id="wstz"><option value="">Each person's own (${esc(Intl.DateTimeFormat().resolvedOptions().timeZone)})</option>
          ${(Intl.supportedValuesOf ? Intl.supportedValuesOf('timeZone') : []).map(z => `<option value="${z}" ${w.timezone === z ? 'selected' : ''}>${z.replace(/_/g, ' ')}</option>`).join('')}
        </select>
        <label class="f" style="margin-top:12px">Default posting times for "Add to queue"</label>
        ${slotsEditor('ws', w.slots, 'Every account not in a brand with its own times')}` : `<p style="margin:0"><b>${esc(w.name)}</b> · ${esc(tz().replace(/_/g, ' '))}</p>`}
      <p class="note">Everything here (accounts, brands, posts and images) belongs to this workspace only. No other workspace can see it.</p>
    </div>
    ${admin ? `<div class="sec"><span class="cap">People</span>
      ${!m ? '<p class="note">Loading…</p>' : `
      ${m.members.map(x => `<div class="row acctrow"><span class="txt"><span class="t">${esc(x.email)}${x.user_id === S.me.user?.id ? ' (you)' : ''}</span>
          <span class="d">${x.role === 'owner' ? 'Owner' : x.role === 'admin' ? 'Admin · accounts, brands, posts and invites' : x.brand_ids
            ? `Member · ${x.brand_ids.map(id => esc(S.me.brands.find(b => b.id === id)?.name || 'removed brand')).join(', ')}` : 'Member · all brands'}</span></span>
        ${x.role !== 'owner' && x.user_id !== S.me.user?.id ? `<select data-role="${x.user_id}" class="move" aria-label="Role for ${esc(x.email)}">
            <option value="member" ${x.role === 'member' ? 'selected' : ''}>Member</option>
            <option value="admin" ${x.role === 'admin' ? 'selected' : ''}>Admin</option></select>
          ${x.role === 'member' && S.me.brands.length ? `<button class="btn sec" data-editscope="${x.user_id}">Brands</button>` : ''}
          <button class="btn danger" data-remove="${x.user_id}">Remove</button>` : ''}
        ${S.editScope === x.user_id ? `<div style="flex-basis:100%">${brandPick('sc-' + x.user_id, x.brand_ids)}
          <button class="btn" data-savescope="${x.user_id}">Save access</button></div>` : ''}
      </div>`).join('')}
      ${m.invites.map(x => `<div class="row acctrow"><span class="txt"><span class="t">${esc(x.email)}</span>
          <span class="d">Invited as ${x.role}${x.brand_ids ? ` · ${x.brand_ids.length} brand${x.brand_ids.length === 1 ? '' : 's'}` : ''} · expires ${fmt(x.expires_at, { dateStyle: 'medium' })}</span></span>
        <button class="btn sec" data-uninvite="${x.id}">Cancel invite</button></div>`).join('')}
      <form id="inviteform" class="invite">
        <input type="email" id="invemail" required placeholder="teammate@company.com" aria-label="Email to invite">
        <select id="invrole" aria-label="Role"><option value="member">Member</option><option value="admin">Admin</option></select>
        <button class="btn">Send invite</button>
        ${brandPick('inv', null)}
      </form>
      <p class="note"><b>Admins</b> connect accounts, manage brands and invite people. <b>Members</b> post and schedule,
        and can be limited to some brands: they never see the others, their accounts or their posts.</p>`}
    </div>` : ''}
    <div class="sec"><span class="cap">Your workspaces</span>
      ${(S.me.workspaces || []).map(x => `<div class="row"><span class="txt"><span class="t">${esc(x.name)}${x.id === w.id ? ' (current)' : ''}</span>
          <span class="d">${x.role}</span></span>
        ${x.id !== w.id ? `<button class="btn sec" data-switch="${x.id}">Open</button>` : ''}</div>`).join('')}
      <form id="newws" class="newbrand"><input type="text" id="newwsname" maxlength="60" placeholder="New workspace, e.g. a separate client">
        <button class="btn sec">Create workspace</button></form>
      ${w.role !== 'owner' ? `<p><button class="btn danger" data-remove="${S.me.user?.id}" data-leave="1">Leave this workspace</button></p>` : ''}
    </div>
    ${owner ? `<div class="sec"><span class="cap">API key</span>
      <p class="note">For posting from your own tools. The key can do everything an admin can do here. Creating a new key disables the old one.</p>
      ${S.apiKey ? `<p><code style="user-select:all">${esc(S.apiKey)}</code></p><p class="note warn">Copy it now. It will not be shown again.</p>` : ''}
      <button class="btn sec" id="apikey">${S.me.api_key_set ? 'Create a new key' : 'Create key'}</button>
    </div>` : ''}
    <div class="sec"><span class="cap">Security</span>
      <p class="note">Signed in as ${esc(S.me.user?.email || '')}. Signing out everywhere ends every session on every device.</p>
      <a class="btn sec" href="/api/auth/logout" style="text-decoration:none">Sign out</a>
      <button class="btn sec" id="logoutall" style="margin-left:8px">Sign out everywhere</button>
    </div>
    ${owner ? `<div class="sec"><span class="cap">Delete workspace</span>
      <p class="note">Removes this workspace's accounts, brands, posts, images and members immediately. It cannot be undone.</p>
      <button class="btn danger" id="delws">Delete workspace</button>
    </div>` : ''}
  </div>`;
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
  on('#title', 'input', e => { S.title = e.target.value; });
  on('#title', 'change', render);
  on('#caption', 'input', e => { S.caption = e.target.value; refreshLimits(); });
  on('[data-ov]', 'input', e => { S.over[e.target.dataset.ov] = e.target.value; refreshLimits(); });
  on('[data-ov]', 'change', render);
  on('[data-custom]', 'click', e => { const pl = e.currentTarget.dataset.custom; S.over[pl] = S.caption; render(); $(`ov-${pl}`)?.focus(); });
  on('[data-uncustom]', 'click', e => { delete S.over[e.target.dataset.uncustom]; render(); });
  on('#caption', 'change', render);
  on('[data-t]', 'change', e => toggleTarget(e.target.dataset.t, e.target.checked));
  on('#openpick', 'click', () => { S.pickOpen = !S.pickOpen; render(); if (S.pickOpen) $('pq')?.focus(); });
  on('[data-unpick]', 'click', e => toggleTarget(e.currentTarget.dataset.unpick, false));
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
  on('[data-opendraft]', 'click', e => openDraft(e.target.dataset.opendraft));
  on('[data-deldraft]', 'click', async e => {
    const key = e.target.dataset.deldraft, g = draftGroups().find(x => (x[0].group_id || x[0].id) === key);
    if (!g || !confirm('Delete this draft?')) return;
    await dropDrafts(g.map(x => x.id)); loadDrafts(); });
  on('#stopedit', 'click', () => { resetComposer(); location.hash = '#calendar'; });
  on('[data-fp]', 'click', e => { S.fPlat = e.target.dataset.fp; S.fAcct = 'all'; render(); });
  on('#facct', 'change', e => { S.fAcct = e.target.value; render(); });
  on('[data-again]', 'click', e => edit(e.target.dataset.again, true));
  on('[data-wk]', 'click', e => { if (S.calMode === 'month') S.month += Number(e.target.dataset.wk); else S.week += Number(e.target.dataset.wk); loadWeek(); });
  on('[data-mode]', 'click', e => { S.calMode = e.target.dataset.mode; loadWeek(); });
  on('[data-drag]', 'dragstart', e => { e.dataTransfer.setData('text/plain', e.currentTarget.dataset.drag); e.dataTransfer.effectAllowed = 'move'; });
  on('[data-day]', 'dragover', e => { e.preventDefault(); e.currentTarget.classList.add('drop'); });
  on('[data-day]', 'dragleave', e => e.currentTarget.classList.remove('drop'));
  on('[data-day]', 'drop', e => { e.preventDefault(); e.currentTarget.classList.remove('drop');
    const id = e.dataTransfer.getData('text/plain'); if (id) movePost(id, e.currentTarget.dataset.day); });
  on('[data-cancel]', 'click', async e => { try { await api(`/posts/${e.target.dataset.cancel}`, { method: 'DELETE' }); } catch (x) { S.flash = { kind: 'err', text: x.message }; } loadWeek(); });
  on('[data-retry]', 'click', async e => { try { await api(`/posts/${e.target.dataset.retry}/retry`, { method: 'POST' }); } catch (x) { S.flash = { kind: 'err', text: x.message }; } loadWeek(); });
  on('[data-edit]', 'click', e => edit(e.target.dataset.edit));
  on('[data-disc]', 'click', async e => {
    if (!confirm('Disconnect this account? Its scheduled posts will be cancelled.')) return;
    const id = e.target.dataset.disc;
    await api(`/accounts/${id}`, { method: 'DELETE' }); S.me = await api('/me');
    S.targets = S.targets.filter(x => x !== id); saveTargets(); render();
  });
  on('#apikey', 'click', async () => { S.apiKey = (await api('/api-key', { method: 'POST' })).api_key; S.me.api_key_set = true; render(); });
  on('#delws', 'click', async () => {
    if (prompt(`Type the workspace name to delete it: ${S.me.workspace.name}`) !== S.me.workspace.name) return;
    await api('/me', { method: 'DELETE' }); location.href = '/api/auth/logout';
  });
}

boot();
