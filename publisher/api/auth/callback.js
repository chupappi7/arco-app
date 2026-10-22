// Step two: TikTok sends the browser back with ?code=. The Worker does the
// exchange and keeps the tokens; this function only proves the round trip
// was ours (state + PKCE verifier cookies) and hands over the session cookie.

import {
  clearCookie, readCookie, rawCookie, redirectUri, env, setSessionCookie, workerFetch, SESSION_COOKIE,
} from '../_lib.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const denied = url.searchParams.get('error');
  if (denied) return back(res, `TikTok returned ${denied}`);

  const expected = readCookie(req, 'tt_state');
  const verifier = readCookie(req, 'tt_verifier');
  const adding = readCookie(req, 'tt_add') === '1';
  clearCookie(res, 'tt_state');
  clearCookie(res, 'tt_verifier');
  clearCookie(res, 'tt_add');

  if (!code) return back(res, 'no authorization code came back');
  // No state cookie at all: the sign-in was started by the command-line token
  // tool, which keeps its own state and verifier. Leave the code unspent.
  if (!expected) return handoff(res);
  if (state !== expected) return back(res, 'state mismatch, start over');
  if (!verifier) return back(res, 'the sign-in attempt expired, start over');

  let body;
  try {
    const r = await workerFetch('/internal/oauth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Internal-Secret': env('INTERNAL_SECRET') },
      body: JSON.stringify({
        code, code_verifier: verifier, redirect_uri: redirectUri(req),
        session_id: rawCookie(req, SESSION_COOKIE) || undefined,
      }),
    });
    body = await r.json();
    if (!r.ok) return back(res, body.error || `sign-in failed (${r.status})`);
  } catch (err) {
    return back(res, 'could not reach the ARCO Publisher service, try again');
  }

  setSessionCookie(res, body.session_id);
  res.redirect(302, adding ? '/app.html?connected=1#accounts' : '/app.html');
}

function back(res, why) {
  res.redirect(302, '/app.html?auth_error=' + encodeURIComponent(why));
}

// The command-line tool keeps its own state, so there is nothing for this
// function to exchange. Its whole job is moving one string from the address
// bar to a terminal, which the browser can simply do -- the old page asked
// the reader to do it by hand and gave them no way to check they had got all
// of it. The code is shown masked: it is in the address bar either way, but a
// screenshot of this page should not be a credential.
function handoff(res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.status(200).send(`<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Authorized &middot; ARCO Publisher</title>
<link rel="icon" type="image/png" sizes="64x64" href="/favicon.png?v=2">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/app.css">
<style>
  /* app.css carries the tokens and the dark mode; this is only the page. */
  .wrap{max-width:540px;margin:0 auto;padding:12vh 20px 60px}
  .mark{display:flex;align-items:center;gap:9px;margin-bottom:26px}
  .mark .dot{width:7px;height:7px;border-radius:50%;background:var(--success);flex:none}
  .mark .who{font-weight:600;font-size:13px;letter-spacing:.01em}
  .mark .who span{color:var(--mute);font-weight:500}
  h1{font:700 27px/1.18 var(--display);margin:0 0 7px;letter-spacing:-.015em}
  .lede{color:var(--mute);margin:0 0 26px;font-size:14.5px}
  .act{display:flex;gap:9px;align-items:stretch;margin-bottom:11px}
  .copy{flex:1;display:flex;align-items:center;justify-content:center;gap:9px;
    background:var(--graphite);color:var(--on-dark);border:0;border-radius:var(--r-ctl);
    padding:13px 16px;font-weight:700;font-size:14.5px;transition:opacity .12s}
  .copy:hover{opacity:.88}
  .copy.done{background:var(--success);color:var(--canvas)}
  .copy svg{width:16px;height:16px;flex:none}
  .url{border:1px solid var(--line);background:var(--well);border-radius:var(--r-ctl);
    padding:11px 13px;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
    color:var(--mute);word-break:break-all;margin:0 0 26px}
  .url b{color:var(--graphite);font-weight:600}
  .url .mask{color:var(--soft)}
  .next{border-top:1px solid var(--line-2);padding-top:18px}
  .next p{margin:0 0 9px;color:var(--mute);font-size:13.5px}
  .cmd{font:12.5px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--graphite);
    background:var(--well);border:1px solid var(--line);border-radius:var(--r-ctl);
    padding:10px 12px;margin:0;overflow-x:auto}
  .cmd .arg{color:var(--link)}
  .safe{display:flex;gap:8px;margin-top:22px;color:var(--soft);font-size:12.5px}
  .safe svg{width:14px;height:14px;flex:none;margin-top:2px}
</style></head>
<body><div class="wrap">

  <div class="mark">
    <span class="dot"></span>
    <span class="who">TikTok <span>&middot; ARCO Publisher</span></span>
  </div>

  <h1>Authorized</h1>
  <p class="lede">One step left &mdash; the terminal that started this sign-in
    needs the address you landed on.</p>

  <div class="act">
    <button class="copy" id="copy" type="button">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="9" y="9" width="13" height="13" rx="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      <span id="copylabel">Copy callback URL</span>
    </button>
  </div>

  <p class="url" id="url"></p>

  <div class="next">
    <p>Paste it back as the <code>--redirected</code> argument:</p>
    <pre class="cmd">node tools/tiktok-auth.js <span class="arg">--account &lt;key&gt;</span> <span class="arg">--redirected</span> "&hellip;"</pre>
  </div>

  <p class="safe">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="3" y="11" width="18" height="11" rx="2"></rect>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
    </svg>
    <span>This page has not spent the code, and the code above is masked &mdash;
      the copy button still carries the whole thing.</span>
  </p>

</div>
<script>
  // Masked for display only. The address bar holds the real thing regardless,
  // but this page gets screenshotted and pasted into chats.
  var href = location.href;
  var el = document.getElementById('url');
  var m = href.match(/^(.*?[?&]code=)([^&]{0,8})([^&]*)([^&]{4})((?:&.*)?)$/);
  el.innerHTML = m
    ? '<b>' + esc(m[1]) + esc(m[2]) + '</b><span class="mask">'
        + (m[3] ? '\\u2026' + m[3].length + ' more\\u2026' : '') + '</span><b>'
        + esc(m[4]) + '</b>' + esc(m[5])
    : esc(href);

  function esc(s){ return s.replace(/[&<>]/g, function(c){
    return { '&':'&amp;', '<':'&lt;', '>':'&gt;' }[c]; }); }

  var btn = document.getElementById('copy');
  var label = document.getElementById('copylabel');
  btn.addEventListener('click', function(){
    // Clipboard needs a secure context; this is served over https. If it is
    // ever blocked, fall back to selecting the text so the reader can still
    // copy by hand rather than being left with a dead button.
    var done = function(){
      btn.classList.add('done');
      label.textContent = 'Copied \\u2014 paste it in your terminal';
      setTimeout(function(){
        btn.classList.remove('done');
        label.textContent = 'Copy callback URL';
      }, 2600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(href).then(done, fallback);
    } else { fallback(); }
    function fallback(){
      var r = document.createRange();
      r.selectNodeContents(el);
      var s = getSelection(); s.removeAllRanges(); s.addRange(r);
      label.textContent = 'Press \\u2318C to copy';
    }
  });
</script>
</body></html>`);
}
