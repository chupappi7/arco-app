const PRIVACY_LABEL = { PUBLIC_TO_EVERYONE: 'Everyone', MUTUAL_FOLLOW_FRIENDS: 'Friends',
  FOLLOWER_OF_CREATOR: 'Followers', SELF_ONLY: 'Only me' };
const MAX_SIDE_W = 1080, MAX_SIDE_H = 1920;

const S = {
  me: null, view: 'compose', flash: null,
  images: [], cover: 0, title: '', caption: '',
  account: '', info: null, infoErr: null,
  set: { privacy: '', comment: false, music: false, disclose: false, brand: false, branded: false },
  when: 'now', at: '', busy: false, status: null,
  week: 0, filter: 'all', posts: [], apiKey: null,
};

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
  if (q.get('auth_error')) { S.flash = { kind: 'err', text: q.get('auth_error') }; history.replaceState({}, '', location.pathname + location.hash); }
  try { S.me = await api('/me'); } catch (e) { if (e.status !== 401) S.flash = { kind: 'err', text: e.message }; }
  window.addEventListener('hashchange', route);
  route();
}

function route() {
  S.view = (location.hash || '#compose').slice(1);
  if (!['compose', 'calendar', 'settings'].includes(S.view)) S.view = 'compose';
  if (S.view === 'calendar') loadWeek();
  render();
}

// ---- render ------------------------------------------------------------

function render() {
  $('tabs').hidden = !S.me;
  document.querySelectorAll('#tabs a').forEach(a => a.classList.toggle('on', a.dataset.v === S.view));
  const flash = S.flash ? `<div class="status ${S.flash.kind}">${esc(S.flash.text)}</div>` : '';
  if (!S.me) { $('app').innerHTML = flash + signInView(); return; }
  $('app').innerHTML = flash + (S.view === 'calendar' ? calendarView() : S.view === 'settings' ? settingsView() : composeView());
  bind();
}

function signInView() {
  return `<div class="card"><div class="sec">
    <span class="cap">Sign in</span>
    <p style="margin:0 0 16px;color:var(--muted)">Sign in with TikTok to schedule photo posts to your account.
      We show your nickname and avatar so you always know which account will post, and we only post what you
      confirm on the next screens. You can connect more accounts afterwards.</p>
    <a class="btn" href="/api/auth/start" style="text-decoration:none;display:inline-block">Continue with TikTok</a>
  </div></div>`;
}

function composeView() {
  const accts = S.me.accounts;
  if (!accts.length) return `<div class="card"><div class="sec">Connect a TikTok account in <a href="#settings">Settings</a> first.</div></div>`;
  const i = S.info;
  const opts = (i?.privacy_level_options || []).filter(o => !(o === 'SELF_ONLY' && S.set.branded));
  const label = S.set.branded ? 'Paid partnership' : S.set.brand ? 'Promotional content' : '';
  const need = missing();
  return `${S.replaces ? `<div class="status">Editing a scheduled post. The original stays scheduled until you save this one.
      <button class="btn sec" id="stopedit" style="margin-left:8px">Stop editing</button></div>` : ''}
  <div class="card">
    <div class="sec"><span class="cap">Photos</span>
      <div class="thumbs">${S.images.map((m, n) => `<div class="th ${n === S.cover ? 'cover' : ''}">
          ${n === S.cover ? '<span class="badge">Cover</span>' : ''}
          <img src="${esc(m.url)}" alt="Slide ${n + 1}" data-cover="${n}" title="Set as cover">
          <div class="ctl"><button data-mv="${n}:-1" aria-label="Move left">‹</button>
            <button data-rm="${n}" aria-label="Remove">×</button>
            <button data-mv="${n}:1" aria-label="Move right">›</button></div></div>`).join('')}
      </div>
      <p><input type="file" id="files" accept="image/jpeg,image/png" multiple ${S.images.length >= 35 ? 'disabled' : ''}></p>
      <span class="note">JPG or PNG, up to 35 images, 5 MB each. Click an image to make it the cover.</span>
    </div>
    <div class="sec">
      <label class="f" for="title">Title</label>
      <input type="text" id="title" maxlength="200" value="${esc(S.title)}">
      <div class="count ${len(S.title) > 90 ? 'note bad' : ''}">${len(S.title)} / 90</div>
      <label class="f" for="caption">Caption</label>
      <textarea id="caption">${esc(S.caption)}</textarea>
      <div class="count ${len(S.caption) > 4000 ? 'note bad' : ''}">${len(S.caption)} / 4000</div>
    </div>
    <div class="sec"><span class="cap">Posting to TikTok</span>
      <label class="f" for="acct">Account</label>
      <select id="acct"><option value="">Choose an account…</option>
        ${accts.map(a => `<option value="${a.id}" ${S.account === a.id ? 'selected' : ''} ${a.needs_reconnect ? 'disabled' : ''}>@${esc(a.username)}${a.needs_reconnect ? ' (reconnect in Settings)' : ''}</option>`).join('')}
      </select>
      ${i ? `<div class="who" style="margin-top:12px">${i.creator_avatar_url ? `<img src="${esc(i.creator_avatar_url)}" alt="">` : ''}
          <div><b>${esc(i.creator_nickname)}</b><div class="note">@${esc(i.creator_username)}</div></div></div>` : ''}
      ${S.infoErr ? `<p class="note bad">${esc(S.infoErr)}</p>` : ''}
    </div>
    ${i ? `<div class="sec">
      <label class="f" for="privacy">Who can view this post *</label>
      <select id="privacy"><option value="" ${S.set.privacy ? '' : 'selected'}>Select who can view…</option>
        ${opts.map(o => `<option value="${o}" ${S.set.privacy === o ? 'selected' : ''}>${PRIVACY_LABEL[o] || o}</option>`).join('')}
      </select>
      ${S.set.branded && (i.privacy_level_options || []).includes('SELF_ONLY') ? '<p class="note">Branded content cannot be private, so "Only me" is unavailable.</p>' : ''}
    </div>
    <div class="sec"><span class="cap">Interactions</span>
      ${row('Allow comments', i.comment_disabled ? 'Turned off in your TikTok settings.' : '',
        `<input type="checkbox" data-k="comment" ${S.set.comment && !i.comment_disabled ? 'checked' : ''} ${i.comment_disabled ? 'disabled' : ''}>`)}
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
    </div>
    <div class="sec"><span class="cap">Preview</span>
      <div class="thumbs">${S.images.map(m => `<img src="${esc(m.url)}" alt="" style="width:56px;height:100px;object-fit:cover;border-radius:6px">`).join('') || '<span class="note">Add photos to see them here.</span>'}</div>
      ${S.title ? `<p><b>${esc(S.title)}</b></p>` : ''}${S.caption ? `<p class="note" style="white-space:pre-wrap">${esc(S.caption)}</p>` : ''}
    </div>
    <div class="sec"><span class="cap">When</span>
      <label><input type="radio" name="when" value="now" ${S.when === 'now' ? 'checked' : ''}> Post now</label>
      &nbsp;&nbsp;<label><input type="radio" name="when" value="later" ${S.when === 'later' ? 'checked' : ''}> Schedule</label>
      ${S.when === 'later' ? `<p><input type="datetime-local" id="at" value="${esc(S.at)}" min="${localInput(Date.now() + 6 * 60e3)}"></p>
        <span class="note">Your local time. At least 5 minutes from now.</span>` : ''}
    </div>
    <div class="consent">By posting, you agree to TikTok's
      ${S.set.branded ? '<a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank" rel="noopener">Branded Content Policy</a> and ' : ''}
      <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en" target="_blank" rel="noopener">Music Usage Confirmation</a>.</div>` : ''}
    <div class="foot">
      <button class="btn" id="go" ${need || S.busy ? 'disabled' : ''} title="${esc(need || '')}">
        ${S.busy ? 'Working…' : S.when === 'later' ? 'Schedule' : 'Post to TikTok'}</button>
      ${need ? `<span class="note">${esc(need)}</span>` : ''}
      ${S.status ? `<div class="status ${S.status.kind}" style="flex-basis:100%">${esc(S.status.text)}</div>` : ''}
      <span class="note" style="flex-basis:100%">After posting, it may take a few minutes for the post to process and appear on the profile.</span>
    </div>
  </div>`;
}

const row = (t, d, control) => `<div class="row"><span class="txt"><span class="t">${t}</span>${d ? `<span class="d">${d}</span>` : ''}</span>${control}</div>`;

function missing() {
  if (!S.images.length) return 'Add at least one photo';
  if (S.images.some(m => m.uploading)) return 'Waiting for uploads to finish';
  if (len(S.title) > 90) return 'The title is too long';
  if (len(S.caption) > 4000) return 'The caption is too long';
  if (!S.account || !S.info) return 'Choose an account';
  if (!S.set.privacy) return 'Choose who can view this post';
  if (S.set.disclose && !S.set.brand && !S.set.branded) return 'You need to indicate if your content promotes yourself, a third party, or both';
  if (S.when === 'later') {
    const t = S.at ? new Date(S.at).getTime() : NaN;
    if (!Number.isFinite(t)) return 'Pick a date and time';
    if (t < Date.now() + 5 * 60e3) return 'Pick a time at least 5 minutes from now';
  }
  return '';
}

function localInput(ms) {
  const d = new Date(ms), p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

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

async function pickAccount(id) {
  S.account = id; S.info = null; S.infoErr = null; S.set.privacy = ''; render();
  if (!id) return;
  try { S.info = await api(`/accounts/${id}/creator-info`); }
  catch (e) { S.infoErr = e.code === 'needs_reconnect' ? 'Reconnect this account in Settings.' : e.message; }
  render();
}

function setOpt(k, v) {
  S.set[k] = v;
  if (k === 'branded' && v && S.set.privacy === 'SELF_ONLY') S.set.privacy = '';
  if (k === 'disclose' && !v) { S.set.brand = false; S.set.branded = false; }
  render();
}

async function submit() {
  if (missing() || S.busy) return;
  S.busy = true; S.status = { kind: '', text: 'Sending…' }; render();
  try {
    const p = await api('/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
      account_id: S.account, image_keys: S.images.map(m => m.key), cover_index: S.cover,
      title: S.title, caption: S.caption,
      settings: { privacy_level: S.set.privacy, disable_comment: !S.set.comment || !!S.info?.comment_disabled,
        auto_add_music: S.set.music, brand_organic: S.set.disclose && S.set.brand, branded_content: S.set.disclose && S.set.branded },
      scheduled_at: S.when === 'later' ? Math.floor(new Date(S.at).getTime() / 1000) : null,
      replaces: S.replaces || undefined,
    }) });
    resetComposer();
    if (p.scheduled_at > Date.now() / 1000 + 60) {
      S.flash = { kind: 'ok', text: `Scheduled for ${new Date(p.scheduled_at * 1000).toLocaleString()}.` };
      location.hash = '#calendar';
    } else {
      S.status = { kind: '', text: 'Posting… TikTok is processing it. This page updates when it is done.' };
      render(); watch(p.id);
    }
  } catch (e) { S.status = { kind: 'err', text: e.message }; }
  S.busy = false; render();
}

async function watch(id) {
  for (let n = 0; n < 60; n++) {
    await new Promise(r => setTimeout(r, 5000));
    const t = Math.floor(Date.now() / 1000);
    const { posts } = await api(`/posts?from=${t - 3600}&to=${t + 60}`);
    const p = posts.find(x => x.id === id);
    if (p?.status === 'published') { S.status = { kind: 'ok', text: 'Published. It may take a few minutes to appear on the profile.' }; return render(); }
    if (p?.status === 'failed') { S.status = { kind: 'err', text: p.fail_reason || 'TikTok rejected the post.' }; return render(); }
  }
  S.status = { kind: '', text: 'Still processing. Check the Calendar for the result.' }; render();
}

function resetComposer() {
  Object.assign(S, { images: [], cover: 0, title: '', caption: '', when: 'now', at: '', status: null, replaces: null });
  S.set = { privacy: '', comment: false, music: false, disclose: false, brand: false, branded: false };
}

// ---- calendar ----------------------------------------------------------

function weekStart() {
  const d = new Date(); d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7) + S.week * 7);
  return d;
}

async function loadWeek() {
  const from = Math.floor(weekStart().getTime() / 1000);
  try { S.posts = (await api(`/posts?from=${from}&to=${from + 7 * 86400}`)).posts; }
  catch (e) { S.flash = { kind: 'err', text: e.message }; }
  render();
}

function calendarView() {
  const start = weekStart();
  const accts = S.me.accounts;
  const posts = S.posts.filter(p => S.filter === 'all' || p.account_id === S.filter);
  const days = [...Array(7)].map((_, i) => { const d = new Date(start); d.setDate(d.getDate() + i); return d; });
  const today = new Date().toDateString();
  return `<div class="chips">
      <button class="chip ${S.filter === 'all' ? 'on' : ''}" data-f="all">All accounts</button>
      ${accts.map(a => `<button class="chip ${S.filter === a.id ? 'on' : ''}" data-f="${a.id}">@${esc(a.username)}</button>`).join('')}
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
      <button class="btn sec" data-wk="-1" ${S.week <= 0 ? 'disabled' : ''}>‹</button>
      <b>${days[0].toLocaleDateString(undefined, { day: 'numeric', month: 'short' })} – ${days[6].toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}</b>
      <button class="btn sec" data-wk="1">›</button>
      <a class="btn" href="#compose" style="margin-left:auto;text-decoration:none">New post</a>
    </div>
    <div class="week">${days.map(d => {
      const ps = posts.filter(p => new Date(p.scheduled_at * 1000).toDateString() === d.toDateString());
      return `<div class="day ${d.toDateString() === today ? 'today' : ''}">
        <h4>${d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })}</h4>
        ${ps.map(p => `<div class="pc">
          ${p.images[p.cover_index] ? `<img src="${esc(p.images[p.cover_index])}" alt="">` : ''}
          <div>${new Date(p.scheduled_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · @${esc(p.username)}</div>
          <span class="pill ${p.status}">${p.status}</span>
          ${p.fail_reason ? `<div class="note ${p.status === 'failed' ? 'bad' : ''}">${esc(p.fail_reason)}</div>` : ''}
          <div class="acts">
            ${p.status === 'queued' ? `<button data-edit="${p.id}">Edit</button><button data-cancel="${p.id}">Cancel</button>` : ''}
            ${p.status === 'failed' ? `<button data-retry="${p.id}">Retry</button><button data-edit="${p.id}">Edit</button>` : ''}
            ${p.post_url ? `<a href="${esc(p.post_url)}" target="_blank" rel="noopener">View</a>` : ''}
          </div></div>`).join('') || '<span class="note">Nothing yet</span>'}
      </div>`;
    }).join('')}</div>`;
}

async function edit(id) {
  const p = S.posts.find(x => x.id === id);
  if (!p) return;
  resetComposer();
  // A queued post stays scheduled until the edited version is saved.
  S.replaces = p.status === 'queued' ? p.id : null;
  Object.assign(S, { images: p.image_keys.map((k, n) => ({ key: k, url: p.images[n] })), cover: p.cover_index,
    title: p.title, caption: p.caption, when: 'later', at: localInput(Math.max(p.scheduled_at * 1000, Date.now() + 10 * 60e3)) });
  const s = p.settings;
  S.set = { privacy: '', comment: !s.disable_comment, music: s.auto_add_music,
            disclose: s.brand_organic || s.branded_content, brand: s.brand_organic, branded: s.branded_content };
  location.hash = '#compose';
  await pickAccount(p.account_id);
  // Privacy is chosen again on purpose: the options come from TikTok now, not from when it was first made.
}

// ---- settings ----------------------------------------------------------

function settingsView() {
  const a = S.me.accounts;
  return `<div class="card">
    <div class="sec"><span class="cap">Connected TikTok accounts (${a.length} / ${S.me.limits.accounts})</span>
      ${a.map(x => row(`@${esc(x.username)}`, x.needs_reconnect ? '<span class="note bad">Access was revoked or expired. Reconnect to keep posting.</span>' : esc(x.display_name),
        `${x.needs_reconnect ? '<a class="btn sec" href="/api/auth/start?add=1" style="text-decoration:none">Reconnect</a>' : ''}
         <button class="btn danger" data-disc="${x.id}">Disconnect</button>`)).join('') || '<p class="note">No accounts yet.</p>'}
      <p><a class="btn" href="/api/auth/start?add=1" style="text-decoration:none;display:inline-block">Add account</a></p>
      <span class="note">Disconnecting cancels that account's scheduled posts. You can also revoke access in TikTok under
        Settings and privacy › Security &amp; permissions › Apps and services.</span>
    </div>
    <div class="sec"><span class="cap">API key</span>
      <p class="note">For posting from your own tools. The key can do everything you can do here. Creating a new key disables the old one.</p>
      ${S.apiKey ? `<p><code style="user-select:all">${esc(S.apiKey)}</code></p><p class="note warn">Copy it now. It will not be shown again.</p>` : ''}
      <button class="btn sec" id="apikey">${S.me.api_key_set ? 'Create a new key' : 'Create key'}</button>
    </div>
    <div class="sec"><span class="cap">Your data</span>
      <p class="note">Delete workspace removes your connected accounts, scheduled posts and uploaded images immediately.</p>
      <button class="btn danger" id="delws">Delete workspace</button>
      <a class="btn sec" href="/api/auth/logout" style="text-decoration:none;margin-left:8px">Sign out</a>
    </div></div>`;
}

// ---- events ------------------------------------------------------------

function bind() {
  const on = (sel, ev, fn) => document.querySelectorAll(sel).forEach(el => el.addEventListener(ev, fn));
  on('#files', 'change', e => addFiles(e.target.files));
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
  on('#caption', 'input', e => { S.caption = e.target.value; });
  on('#caption', 'change', render);
  on('#acct', 'change', e => pickAccount(e.target.value));
  on('#privacy', 'change', e => { S.set.privacy = e.target.value; render(); });
  on('[data-k]', 'change', e => setOpt(e.target.dataset.k, e.target.checked));
  on('input[name=when]', 'change', e => { S.when = e.target.value; render(); });
  on('#at', 'change', e => { S.at = e.target.value; render(); });
  on('#go', 'click', submit);
  on('#stopedit', 'click', () => { resetComposer(); location.hash = '#calendar'; });
  on('[data-f]', 'click', e => { S.filter = e.target.dataset.f; render(); });
  on('[data-wk]', 'click', e => { S.week += Number(e.target.dataset.wk); loadWeek(); });
  on('[data-cancel]', 'click', async e => { try { await api(`/posts/${e.target.dataset.cancel}`, { method: 'DELETE' }); } catch (x) { S.flash = { kind: 'err', text: x.message }; } loadWeek(); });
  on('[data-retry]', 'click', async e => { try { await api(`/posts/${e.target.dataset.retry}/retry`, { method: 'POST' }); } catch (x) { S.flash = { kind: 'err', text: x.message }; } loadWeek(); });
  on('[data-edit]', 'click', e => edit(e.target.dataset.edit));
  on('[data-disc]', 'click', async e => {
    if (!confirm('Disconnect this account? Its scheduled posts will be cancelled.')) return;
    await api(`/accounts/${e.target.dataset.disc}`, { method: 'DELETE' }); S.me = await api('/me'); render();
  });
  on('#apikey', 'click', async () => { S.apiKey = (await api('/api-key', { method: 'POST' })).api_key; S.me.api_key_set = true; render(); });
  on('#delws', 'click', async () => {
    if (!confirm('Delete your workspace, accounts, posts and images? This cannot be undone.')) return;
    await api('/me', { method: 'DELETE' }); location.href = '/api/auth/logout';
  });
}

boot();
