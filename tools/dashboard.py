#!/usr/bin/env python3
"""Local review dashboard for the TikTok pipeline.

  python3 tools/dashboard.py        # http://localhost:4500

Shows every built post, what has been delivered where, and how many pending
slots each account has left. Drafting runs the same autopost.js path the cron
job uses, so nothing here is a second implementation that can drift.

Stdlib only, no install. Binds to localhost.
"""
import http.server
import json
import mimetypes
import os
import socketserver
import subprocess
import threading
import time
import urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFTS = os.path.join(REPO, 'drafts')
HOOKS = os.path.join(REPO, 'tools', 'hooks.json')
LOG = os.path.join(REPO, 'tools', 'delivery_log.json')
FEEDBACK = os.path.join(REPO, 'tools', 'post_feedback.json')
REPLICATE = os.path.join(REPO, 'tools', 'replicate_queue.json')
TOOL_USAGE = os.path.join(REPO, 'tools', 'tool_usage.json')
TOOL_POOL = os.path.join(REPO, 'tools', 'tool_pool.json')
PORT = 4500

ACCOUNTS = [
    {'key': 'vn', 'label': 'arco.app'},
    {'key': 'getarco', 'label': 'getarcoapp'},
    {'key': 'us', 'label': 'emiliagonzalez389'},
]
CAP = 5                      # pending shares per account per rolling 24h
_lock = threading.Lock()


def load(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return default


def hooks_index():
    d = load(HOOKS, {})
    posts = d['posts'] if isinstance(d, dict) else d
    return {p['topic']: p for p in posts}, d


def delivery_log():
    return load(LOG, {})


def save_log(log):
    with open(LOG, 'w') as fh:
        json.dump(log, fh, indent=1)


def pending_counts():
    """Sends inside the rolling 24h window, which is what the cap counts.

    Publishing frees a slot but TikTok exposes no way to see that, so this is
    an upper bound: it can show an account as fuller than it really is, never
    emptier. Treat it as 'at most this many slots used'.
    """
    now = time.time()
    counts = {a['key']: 0 for a in ACCOUNTS}
    for topic, accts in delivery_log().items():
        for key, rec in accts.items():
            if (rec.get('status') == 'SENT' and not rec.get('published')
                    and now - rec.get('at', 0) < 86400):
                counts[key] = counts.get(key, 0) + 1
    return counts


def roster_for(topic):
    d = load(TOOL_USAGE, [])
    entries = d if isinstance(d, list) else d.get('posts', [])
    for e in entries:
        if e.get('topic') == topic:
            return e.get('tools', [])
    return []


def sibling_roster(tools):
    """Same shape, different names: keep ARCO where it is, keep one LLM, and
    draw the rest from the same audience tags as the originals, excluding what
    the source post already used. The concept survives, the roster does not
    repeat."""
    pool = load(TOOL_POOL, {})
    tags = pool.get('audience', {})
    groups = {k: v for k, v in pool.items() if isinstance(v, list)}
    used = set(tools)
    out = []
    for t in tools:
        if t == 'ARCO':
            out.append(t)
            continue
        want = tags.get(t)
        cands = [c for g in groups.values() for c in g
                 if tags.get(c) == want and c not in used and c != 'ARCO']
        if want == 'any':                      # the LLM slot
            cands = [c for c in pool.get('llm', []) if c not in used]
        out.append(cands[0] if cands else t)
        used.add(out[-1])
    return out


def replicate_queue():
    return load(REPLICATE, [])


def list_posts():
    idx, _ = hooks_index()
    log = delivery_log()
    fb = load(FEEDBACK, {})
    queued = {q['from'] for q in replicate_queue() if not q.get('done')}
    out = []
    for topic in sorted(os.listdir(DRAFTS)):
        d = os.path.join(DRAFTS, topic)
        if not os.path.isdir(d):
            continue
        slides = sorted(f for f in os.listdir(d) if f.endswith('.jpg'))
        if not slides:
            continue
        meta = idx.get(topic, {})
        out.append({
            'topic': topic,
            'title': meta.get('title', ''),
            'caption': meta.get('caption', ''),
            'note': meta.get('_note', ''),
            'registered': topic in idx,
            'slides': slides,
            'mtime': os.path.getmtime(os.path.join(d, slides[0])),
            'delivery': log.get(topic, {}),
            'liked': bool(fb.get(topic, {}).get('liked')),
            'queued': topic in queued,
            'roster': roster_for(topic),
        })
    out.sort(key=lambda p: p['mtime'], reverse=True)
    return out


def run_draft(topic, keys):
    """Deliver via autopost.js, one attempt per account, and record it."""
    results = {}
    env = dict(os.environ)
    for line in open(os.path.join(REPO, '.env')):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
    for key in keys:
        try:
            p = subprocess.run(
                ['node', 'tools/autopost.js', topic, '--account', key, '--wait'],
                cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
            out = p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            out = 'timeout'
        if 'SEND_TO_USER_INBOX' in out:
            status, detail = 'SENT', ''
        elif 'spam_risk' in out.lower():
            status, detail = 'CAPPED', 'five unpublished drafts on this account'
        else:
            reason = [l.strip() for l in out.splitlines() if 'fail_reason' in l]
            status, detail = 'FAILED', (reason[0] if reason else out.strip()[-160:])
        results[key] = {'status': status, 'detail': detail, 'at': time.time()}
    with _lock:
        log = delivery_log()
        log.setdefault(topic, {}).update(results)
        save_log(log)
    return results


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/':
            return self._send(200, PAGE, 'text/html; charset=utf-8')
        if path == '/api/posts':
            return self._send(200, {'posts': list_posts(), 'accounts': ACCOUNTS,
                                    'pending': pending_counts(), 'cap': CAP})
        if path.startswith('/slide/'):
            rel = path[len('/slide/'):]
            f = os.path.normpath(os.path.join(DRAFTS, rel))
            if not f.startswith(DRAFTS) or not os.path.isfile(f):
                return self._send(404, {'error': 'not found'})
            ctype = mimetypes.guess_type(f)[0] or 'application/octet-stream'
            with open(f, 'rb') as fh:
                return self._send(200, fh.read(), ctype)
        return self._send(404, {'error': 'not found'})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(n) or b'{}')
        if path == '/api/draft':
            topic = body['topic']
            keys = body.get('accounts') or [a['key'] for a in ACCOUNTS]
            return self._send(200, {'results': run_draft(topic, keys),
                                    'pending': pending_counts()})
        if path == '/api/like':
            with _lock:
                fb = load(FEEDBACK, {})
                fb.setdefault(body['topic'], {})['liked'] = bool(body['liked'])
                fb[body['topic']]['at'] = time.time()
                with open(FEEDBACK, 'w') as fh:
                    json.dump(fb, fh, indent=1)
            return self._send(200, {'ok': True})
        if path == '/api/replicate':
            topic = body['topic']
            idx, _ = hooks_index()
            src = idx.get(topic, {})
            tools = roster_for(topic)
            with _lock:
                q = replicate_queue()
                if any(x['from'] == topic and not x.get('done') for x in q):
                    return self._send(200, {'ok': True, 'already': True})
                q.append({
                    'from': topic,
                    'title': src.get('title', ''),
                    'source_roster': tools,
                    'suggested_roster': sibling_roster(tools),
                    'at': time.time(),
                    'done': False,
                })
                with open(REPLICATE, 'w') as fh:
                    json.dump(q, fh, indent=1, ensure_ascii=False)
            return self._send(200, {'ok': True})
        if path == '/api/publish':
            # Publishing happens by hand in the TikTok app and the API cannot
            # see it, so it is recorded here. A published draft stops counting
            # against the cap, which is the whole reason this state exists.
            with _lock:
                log = delivery_log()
                rec = log.get(body['topic'], {}).get(body['account'])
                if rec:
                    rec['published'] = bool(body['published'])
                    rec['published_at'] = time.time() if body['published'] else None
                    save_log(log)
            return self._send(200, {'pending': pending_counts()})
        if path == '/api/published':
            # TikTok exposes no way to read how many drafts are still pending,
            # so publishing is recorded here by hand. Clearing an account drops
            # its SENT records, which is what publishing does to the cap.
            with _lock:
                log = delivery_log()
                key = body['account']
                for topic in log:
                    rec = log[topic].get(key)
                    if rec and rec.get('status') == 'SENT':
                        rec['published'] = True
                        rec['published_at'] = time.time()
                save_log(log)
            return self._send(200, {'pending': pending_counts()})
        if path == '/api/save':
            with _lock:
                idx, raw = hooks_index()
                posts = raw['posts'] if isinstance(raw, dict) else raw
                for p in posts:
                    if p['topic'] == body['topic']:
                        p['title'] = body.get('title', p.get('title', ''))
                        p['caption'] = body.get('caption', p.get('caption', ''))
                        break
                else:
                    posts.append({'topic': body['topic'],
                                  'title': body.get('title', ''),
                                  'caption': body.get('caption', '')})
                with open(HOOKS, 'w') as fh:
                    json.dump(raw, fh, indent=1, ensure_ascii=False)
            return self._send(200, {'ok': True})
        return self._send(404, {'error': 'not found'})


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>ARCO pipeline</title><style>
*{box-sizing:border-box}
body{margin:0;background:#0d0d0f;color:#e8e8ea;font:14px/1.5 -apple-system,system-ui,sans-serif}
header{padding:18px 24px;border-bottom:1px solid #232327;display:flex;gap:28px;align-items:center;flex-wrap:wrap}
h1{font-size:15px;margin:0;letter-spacing:.02em}
.acct{display:flex;gap:14px}
.chip{background:#17171b;border:1px solid #26262b;border-radius:8px;padding:6px 11px;font-size:12px}
.chip b{font-weight:600}
.bar{display:inline-block;width:52px;height:5px;background:#26262b;border-radius:3px;margin-left:7px;vertical-align:middle;overflow:hidden}
.bar i{display:block;height:100%;background:#4ea1ff}
.bar.full i{background:#ff5f56}
main{display:grid;grid-template-columns:300px 1fr;height:calc(100vh - 61px)}
#list{overflow:auto;border-right:1px solid #232327}
.item{padding:12px 16px;border-bottom:1px solid #1b1b1f;cursor:pointer}
.item:hover{background:#141418}
.item.on{background:#17171d;box-shadow:inset 3px 0 0 #4ea1ff}
.item .t{font-weight:600;font-size:13px}
.item .s{color:#8b8b93;font-size:11px;margin-top:3px}
.dots{margin-top:6px;display:flex;gap:4px}
.dot{width:7px;height:7px;border-radius:50%;background:#33333a}
.dot.drafted{background:#4ea1ff}.dot.published{background:#3fb950}
.dot.capped{background:#d29922}.dot.failed{background:#ff5f56}
.state{display:flex;gap:9px;align-items:center;padding:7px 0;border-bottom:1px solid #1b1b1f}
.state .nm{width:170px;font-size:13px}
.tag{font-size:11px;padding:2px 8px;border-radius:20px;border:1px solid #2e2e35;color:#8b8b93}
.tag.drafted{color:#4ea1ff;border-color:#25476b}
.tag.published{color:#3fb950;border-color:#1f4429}
.tag.capped{color:#d29922;border-color:#5c4410}
.tag.failed{color:#ff5f56;border-color:#6b2420}
.state button{padding:4px 10px;font-size:12px}
#pane{overflow:auto;padding:22px 26px}
.slides{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:12px;margin:16px 0 22px}
.slides img{width:100%;border-radius:9px;border:1px solid #26262b;cursor:zoom-in;display:block}
label{display:block;color:#8b8b93;font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 5px}
input,textarea{width:100%;background:#131317;color:#e8e8ea;border:1px solid #2a2a30;border-radius:8px;padding:9px 11px;font:inherit}
textarea{min-height:120px;resize:vertical}
button{background:#4ea1ff;color:#06121f;border:0;border-radius:8px;padding:9px 15px;font-weight:600;cursor:pointer;font-size:13px}
button.ghost{background:#1c1c22;color:#e8e8ea;border:1px solid #2e2e35}
button:disabled{opacity:.45;cursor:not-allowed}
.row{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-top:14px}
.res{margin-top:12px;font-size:12px;white-space:pre-wrap;color:#a6a6ae}
#zoom{position:fixed;inset:0;background:#000d;display:none;align-items:center;justify-content:center;z-index:9}
#zoom img{max-height:94vh;max-width:94vw;border-radius:10px}
.empty{color:#6d6d75;padding:40px 0}
</style></head><body>
<header><h1>ARCO pipeline</h1><div class="acct" id="acct"></div></header>
<main><div id="list"></div><div id="pane"><div class="empty">Select a post.</div></div></main>
<div id="zoom" onclick="this.style.display='none'"><img id="zoomimg"></div>
<script>
let DATA=null, cur=null;
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

async function load(){
  DATA = await (await fetch('/api/posts')).json();
  document.getElementById('acct').innerHTML = DATA.accounts.map(a=>{
    const n = DATA.pending[a.key]||0, full = n>=DATA.cap;
    return `<div class="chip"><b>${esc(a.label)}</b> ${n}/${DATA.cap}
      <span class="bar ${full?'full':''}"><i style="width:${Math.min(100,n/DATA.cap*100)}%"></i></span>
      <a href="#" onclick="published('${a.key}');return false"
         style="margin-left:9px;color:#6d8fb8;text-decoration:none">published</a></div>`;
  }).join('');
  document.getElementById('list').innerHTML = DATA.posts.map(p=>{
    const dots = DATA.accounts.map(a=>{
      const r=(p.delivery||{})[a.key];
      const c = !r ? '' : r.published ? 'published'
              : r.status==='SENT' ? 'drafted'
              : r.status==='CAPPED' ? 'capped' : 'failed';
      return `<span class="dot ${c}" title="${esc(a.label)}: ${c||'not sent'}"></span>`;
    }).join('');
    return `<div class="item ${cur===p.topic?'on':''}" onclick="open_('${p.topic}')">
      <div class="t">${esc(p.topic)}</div>
      <div class="s">${p.liked?'♥ ':''}${p.queued?'⟳ ':''}${p.slides.length} slides${p.registered?'':' · unregistered'}</div>
      <div class="dots">${dots}</div></div>`;
  }).join('') || '<div class="empty" style="padding:20px">No posts built yet.</div>';
}

function open_(topic){
  cur = topic; location.hash = topic; const p = DATA.posts.find(x=>x.topic===topic); load();
  document.getElementById('pane').innerHTML = `
    <div style="font-size:17px;font-weight:600">${esc(p.topic)}</div>
    <div style="color:#8b8b93;font-size:12px;margin-top:3px">${esc(p.note)}</div>
    <div class="slides">${p.slides.map(s=>
      `<img src="/slide/${p.topic}/${s}" onclick="zoom(this.src)">`).join('')}</div>
    <label>Title</label><input id="ti" value="${esc(p.title)}">
    <label>Caption</label><textarea id="ca">${esc(p.caption)}</textarea>
    <div class="row">
      <button class="ghost" onclick="save()">Save text</button>
      <button class="ghost" onclick="like(${p.liked?'false':'true'})">${p.liked?'♥ Liked':'♡ Like'}</button>
      <button class="ghost" onclick="replicate()" ${p.queued?'disabled':''}>
        ${p.queued?'⟳ Queued to replicate':'Replicate this concept'}</button>
    </div>
    <div class="res">${p.roster.length?'Roster: '+esc(p.roster.join(', ')):''}</div>
    <label>Status</label>
    ${DATA.accounts.map(a=>{
      const r=(p.delivery||{})[a.key];
      const st = !r ? 'not sent' : r.published ? 'published'
               : r.status==='SENT' ? 'drafted' : r.status.toLowerCase();
      const cls = st==='not sent' ? '' : st;
      return `<div class="state">
        <span class="nm">${esc(a.label)}</span>
        <span class="tag ${cls}">${st}</span>
        ${r&&r.status==='SENT' ? `<button class="ghost" onclick="publish('${a.key}',${r.published?'false':'true'})">
            ${r.published?'mark unpublished':'mark published'}</button>` : ''}
        ${r&&r.detail?`<span style="color:#6d6d75;font-size:11px">${esc(r.detail)}</span>`:''}
      </div>`;}).join('')}
    <label>Draft to</label>
    <div class="row">
      ${DATA.accounts.map(a=>{
        const n=DATA.pending[a.key]||0;
        return `<button class="ghost" onclick="draft(['${a.key}'])" ${n>=DATA.cap?'disabled':''}>
          ${esc(a.label)}${n>=DATA.cap?' · full':''}</button>`;}).join('')}
      <button onclick="draft(null)">Draft to all</button>
    </div>
    <div class="res" id="res"></div>`;
}

async function published(key){
  await fetch('/api/published',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({account:key})});
  await load(); if(cur) open_(cur);
}

async function publish(key,v){
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,account:key,published:v})});
  DATA=await(await fetch('/api/posts')).json(); await load(); open_(cur);
}

async function like(v){
  await fetch('/api/like',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,liked:v})});
  DATA=await(await fetch('/api/posts')).json(); open_(cur);
}

async function replicate(){
  await fetch('/api/replicate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur})});
  DATA=await(await fetch('/api/posts')).json(); open_(cur);
  document.getElementById('res').textContent =
    'Queued. The next batch builds it: same hook shape and roster pattern, different tools, '+
    'new backgrounds and new teaching points. Say "run replicates" to build it now.';
}

function zoom(src){document.getElementById('zoomimg').src=src;document.getElementById('zoom').style.display='flex';}

async function save(){
  await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,title:ti.value,caption:ca.value})});
  document.getElementById('res').textContent='Saved to hooks.json. Commit and push before drafting so Pages serves it.';
  DATA=await(await fetch('/api/posts')).json();
}

async function draft(accts){
  const el=document.getElementById('res');
  el.textContent='Sending. Each account is polled to SEND_TO_USER_INBOX, so this takes a moment.';
  document.querySelectorAll('#pane button').forEach(b=>b.disabled=true);
  const r = await (await fetch('/api/draft',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,accounts:accts})})).json();
  el.textContent = Object.entries(r.results).map(([k,v])=>
    `${k}: ${v.status}${v.detail?' — '+v.detail:''}`).join('\n');
  DATA = await (await fetch('/api/posts')).json(); open_(cur);
  document.getElementById('res').textContent = el.textContent;
}
load().then(()=>{const t=decodeURIComponent(location.hash.slice(1));
  if(t && DATA.posts.some(p=>p.topic===t)) open_(t);});
</script></body></html>"""


if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as srv:
        print(f'dashboard on http://localhost:{PORT}  (ctrl-c to stop)')
        srv.serve_forever()
