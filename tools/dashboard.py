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
import secrets
import socket
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
TOKEN_FILE = os.path.join(REPO, 'tools', '.dashboard_token')
_lock = threading.Lock()


def access_token():
    """Shared key for anything that is not localhost.

    Reaching this from a phone means binding to the LAN, and these endpoints
    delete posts and push drafts to TikTok using real tokens. Anyone on the
    same Wi-Fi could otherwise hit them, so off-machine access needs the key.
    """
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE).read().strip()
    tok = secrets.token_urlsafe(9)
    with open(TOKEN_FILE, 'w') as fh:
        fh.write(tok)
    os.chmod(TOKEN_FILE, 0o600)
    return tok


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    finally:
        s.close()


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
    st = statuses()
    sched = {}
    for x in schedules():
        if not x.get('done'):
            sched.setdefault(x['topic'], []).append(x)
    redos = {}
    for r in redo_queue():
        if not r.get('done'):
            redos.setdefault(r['topic'], []).append(r)
    out = []
    for topic in sorted(os.listdir(DRAFTS)):
        if topic.startswith('_'):
            continue
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
            'slide_mtimes': {f: int(os.path.getmtime(os.path.join(d, f))) for f in slides},
            'mtime': os.path.getmtime(os.path.join(d, slides[0])),
            'delivery': log.get(topic, {}),
            'liked': bool(fb.get(topic, {}).get('liked')),
            'queued': topic in queued,
            'redos': redos.get(topic, []),
            'approved': bool(st.get(topic, {}).get('approved')),
            'seen': bool(st.get(topic, {}).get('seen')),
            'from_replicate': st.get(topic, {}).get('from_replicate'),
            'schedules': sched.get(topic, []),
            'roster': roster_for(topic),
        })
    out.sort(key=lambda p: p['mtime'], reverse=True)
    return out


PAGES = 'https://chupappi7.github.io/arco-app/drafts'


def pages_ready(topic, tries=12, wait=8):
    """True once Pages serves byte-identical slides.

    autopost preflights that the URLs resolve, not that they are the current
    render, so a post edited after its last push would deliver the old slides.
    """
    import hashlib
    import ssl
    import urllib.request
    import certifi
    # This Python has no usable default trust store, so an unverified fetch
    # raises and the file reads as stale forever. Swallowing that error is how
    # every slide looked out of date while Pages was serving the right bytes.
    ctx = ssl.create_default_context(cafile=certifi.where())
    d = os.path.join(DRAFTS, topic)
    files = sorted(f for f in os.listdir(d) if f.endswith('.jpg'))
    last_err = None
    for _ in range(tries):
        stale = []
        for f in files:
            local = hashlib.md5(open(os.path.join(d, f), 'rb').read()).hexdigest()
            try:
                remote = hashlib.md5(urllib.request.urlopen(
                    f'{PAGES}/{topic}/{f}', timeout=20, context=ctx).read()).hexdigest()
            except Exception as exc:
                remote, last_err = None, exc
            if remote != local:
                stale.append(f)
        if not stale:
            return True, ''
        time.sleep(wait)
    detail = ' (last fetch error: %s)' % last_err if last_err else ''
    return False, 'Pages is not serving the current ' + ', '.join(stale) + detail


def run_draft(topic, keys):
    """Deliver via autopost.js, one attempt per account, and record it."""
    ok, why = pages_ready(topic)
    if not ok:
        return {k: {'status': 'FAILED', 'detail': why + '. Commit and push, then retry.',
                    'at': time.time()} for k in keys}
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


REDO = os.path.join(REPO, 'tools', 'redo_queue.json')
STATUS = os.path.join(REPO, 'tools', 'post_status.json')
BUILD = os.path.join(REPO, 'tools', 'build_queue.json')
HOOK_POOL = os.path.join(REPO, 'tools', 'hook_pool.json')
SCHEDULE = os.path.join(REPO, 'tools', 'schedule.json')


def redo_queue():
    return load(REDO, [])


def statuses():
    return load(STATUS, {})


def build_queue():
    return load(BUILD, [])


def save_builds(q):
    with open(BUILD, 'w') as fh:
        json.dump(q, fh, indent=1, ensure_ascii=False)


BUILD_PROMPT = """Build {count} new {pillar} post(s) for the TikTok pipeline. Work in {repo}.

{note}
Read ~/.claude/skills/tiktok-pipeline/examples.md FIRST for register, and
content.md for the rules. Skipping examples.md is how hooks and copy drift out
of Thinh's voice; it is not optional.

Rules, all enforced in code, so run them rather than trusting memory:

1. Hooks MUST come from tools/hook_pool.json. compose.hook_slide refuses any
   other hook. Mark each one used with compose.mark_hook_used. If there are
   not enough unused hooks, build fewer and say so.
2. Roster from tools/tool_pool.json. ARCO leads at slide 1. Exactly one LLM
   per post, rotated between posts. Every tool must pass
   compose.assert_audience.
3. Call compose.preflight(topic, tools, bgs) before rendering. Pick
   backgrounds with the same approach as tools/gen-daily-batch.py: skip
   hook-only vibes on app slides, reject anything whose copy_band_luma is
   above compose.BAND_MAX_LUMA, no adjacent vibe repeats, at most one person.
4. Both body lines on a slide must teach. First line is the mechanism, second
   is the concrete consequence. Never a verdict. The claim must be a real
   feature of the product named, and must not repeat any teaching point
   already used in tools/hooks.json captions.
5. Write a generator script tools/gen-<topic>.py so the post can be rebuilt,
   render the slides to drafts/<topic>/01.jpg through 06.jpg, then READ every
   rendered JPG back and fix anything that looks wrong. A contact sheet per
   post is fine.
6. Register each post in tools/hooks.json with topic, title and caption.
   Call compose.record_post_tools and compose.record_post_bgs.

7. Commit and push. TikTok pulls the images from GitHub Pages, so a post that
   is only on disk cannot be delivered. After pushing, poll
   https://chupappi7.github.io/arco-app/drafts/<topic>/<nn>.jpg for every slide
   until its md5 matches the local file. Pages lags behind the push; a post is
   not finished until it actually serves.

Do NOT deliver anything to TikTok. Thinh approves and schedules that himself.
Finish by printing: BUILT <topic> [, <topic>...]
"""


PUSH_RULE = """
Commit and push when the slides are final. TikTok pulls the images from GitHub
Pages, so a post that is only on disk cannot be delivered. After pushing, poll
https://chupappi7.github.io/arco-app/drafts/<topic>/<nn>.jpg for every slide
until its md5 matches the local file; Pages lags behind the push.
Do NOT deliver anything to TikTok.
"""

REDO_PROMPT = """Fix ONE slide in an existing TikTok carousel. Work in {repo}.

Post: {topic}
Slide: {slide:02d}.jpg (number {slide} in the carousel)
What Thinh says is wrong with it:
{note}

1. Find tools/gen-*.py referencing '{topic}'. That file is the spec.
2. Change ONLY what slide {slide} needs. Leave the other slides alone.
3. Re-render just that slide through the same compose helper, writing to
   drafts/{topic}/{slide:02d}.jpg, and read the JPG back to confirm the
   complaint is actually fixed.
4. Keep every guard true: both body lines teach and neither is a verdict, the
   claim is a real feature of the product named, the background clears
   compose.copy_band_luma and does not repeat an adjacent vibe, night-desk
   vibes are hook-only, hooks only from tools/hook_pool.json.
5. Update the generator so a rebuild produces the fixed slide too.
""" + PUSH_RULE + """
Finish by printing: FIXED <what changed>
"""

REPLICATE_PROMPT = """Replicate a post that worked. Work in {repo}.

Source post: {source}
Its roster was: {source_roster}
Suggested roster for the new one: {suggested}

Read ~/.claude/skills/tiktok-pipeline/examples.md for register first.

Keep what made the source work: the hook's shape and the roster pattern.
Change everything that would make it a repeat: a different hook from
tools/hook_pool.json, the suggested roster, fresh backgrounds, and teaching
points that appear nowhere in tools/hooks.json captions.

ARCO leads at slide 1, exactly one LLM, every tool must pass
compose.assert_audience, and call compose.preflight(topic, tools, bgs) before
rendering. Write tools/gen-<topic>.py, render six slides, read them back, and
register the post in tools/hooks.json.
""" + PUSH_RULE + """
Finish by printing: BUILT <topic>
"""


def _agent(prompt, mark, ok_token):
    """Run a headless Claude in the repo and record the outcome."""
    mark(status='running', started=time.time())
    try:
        p = subprocess.run(['claude', '-p', prompt], cwd=REPO,
                           capture_output=True, text=True, timeout=3600)
        out = ((p.stdout or '') + (p.stderr or '')).strip()
        good = ok_token in out
        mark(status='done' if good else 'failed', done=good,
             log=out[-1200:] or 'no output', finished=time.time())
    except Exception as exc:
        mark(status='failed', log=str(exc))


def run_redo(job):
    def mark(**kw):
        with _lock:
            q = redo_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            with open(REDO, 'w') as fh:
                json.dump(q, fh, indent=1, ensure_ascii=False)
    _agent(REDO_PROMPT.format(repo=REPO, topic=job['topic'], slide=job['slide'],
                              note=job['note']), mark, 'FIXED')


def run_replicate(job):
    def mark(**kw):
        with _lock:
            q = replicate_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            with open(REPLICATE, 'w') as fh:
                json.dump(q, fh, indent=1, ensure_ascii=False)
    _agent(REPLICATE_PROMPT.format(repo=REPO, source=job['from'],
                                   source_roster=', '.join(job['source_roster']),
                                   suggested=', '.join(job['suggested_roster'])),
           mark, 'BUILT')


def run_build(job):
    """Actually build the posts by handing the job to a headless Claude run.

    Writing a post is judgment, not a transform: hooks, rosters and teaching
    points all need choices. So the button starts an agent rather than
    templating something. It is scoped to writing into drafts/ and hooks.json,
    and explicitly forbidden from committing or delivering.
    """
    note = ('Thinh asked for: ' + job['note'] + '\n') if job.get('note') else ''
    prompt = BUILD_PROMPT.format(count=job['count'], pillar=job.get('pillar', 'tools'),
                                 repo=REPO, note=note)

    def mark(**kw):
        with _lock:
            q = build_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            save_builds(q)

    mark(status='running', started=time.time())
    try:
        p = subprocess.run(['claude', '-p', prompt], cwd=REPO,
                           capture_output=True, text=True, timeout=3600)
        out = ((p.stdout or '') + (p.stderr or '')).strip()
        ok = 'BUILT' in out
        mark(status='done' if ok else 'failed', done=ok,
             log=out[-1200:] or 'no output', finished=time.time())
    except subprocess.TimeoutExpired:
        mark(status='failed', log='timed out after an hour')
    except FileNotFoundError:
        mark(status='failed', log='claude CLI not found on PATH')
    except Exception as exc:
        mark(status='failed', log=str(exc))


def hooks_available():
    """Unused approved hooks. A post cannot be built without one, so this is
    the real ceiling on how many can be made right now."""
    pool = load(HOOK_POOL, {})
    return sum(1 for h in pool.get('hooks', []) if not h.get('used'))


def schedules():
    return load(SCHEDULE, [])


def save_schedules(sc):
    with open(SCHEDULE, 'w') as fh:
        json.dump(sc, fh, indent=1)


def scheduler_loop():
    """Deliver scheduled posts. The dashboard is already long running and
    already owns the delivery path, so it is the natural place for this; the
    session cron died with the session.

    A schedule that comes due while the machine is asleep fires late rather
    than never, which is the honest behaviour for a local server.
    """
    while True:
        try:
            now = time.time()
            due = [x for x in schedules() if not x.get('done') and x['at'] <= now]
            for job in due:
                accts = job.get('accounts') or [a['key'] for a in ACCOUNTS]
                gap = int(job.get('stagger_min') or 0) * 60
                results = {}
                for i, key in enumerate(accts):
                    if i and gap:
                        time.sleep(gap)
                    results.update(run_draft(job['topic'], [key]))
                with _lock:
                    sc = schedules()
                    for x in sc:
                        if x['topic'] == job['topic'] and x['at'] == job['at']:
                            x['done'] = True
                            x['results'] = {k: v['status'] for k, v in results.items()}
                            x['ran_at'] = time.time()
                    save_schedules(sc)
        except Exception as exc:      # never let the loop die on one bad job
            print('scheduler error:', exc)
        time.sleep(30)


def queue_redo(topic, n, note):
    """Record a slide that Thinh wants redone, with his reason.

    Redoing a slide means new copy or a new background, which is judgment, so
    this is a request rather than an action: Claude picks the queue up and does
    the work with the same guards a fresh build runs through.
    """
    with _lock:
        q = redo_queue()
        q = [x for x in q if not (x['topic'] == topic and x['slide'] == n and not x.get('done'))]
        q.append({'topic': topic, 'slide': n, 'note': note.strip(),
                  'at': time.time(), 'done': False})
        with open(REDO, 'w') as fh:
            json.dump(q, fh, indent=1, ensure_ascii=False)
    return len([x for x in q if not x.get('done')])


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def authed(self):
        if self.client_address[0] in ('127.0.0.1', '::1'):
            return True
        tok = access_token()
        if ('k=' + tok) in (urllib.parse.urlparse(self.path).query or ''):
            self._cookie = tok
            return True
        return ('dk=' + tok) in (self.headers.get('Cookie') or '')

    def deny(self):
        self._send(401, '<body style="font:16px system-ui;background:#020617;color:#94A3B8;'
                        'padding:40px">Add the access key to the URL.</body>',
                   'text/html; charset=utf-8')

    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        if getattr(self, '_cookie', None):
            self.send_header('Set-Cookie',
                             'dk=%s; Path=/; Max-Age=31536000; SameSite=Lax' % self._cookie)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authed():
            return self.deny()
        path = urllib.parse.urlparse(self.path).path
        if path == '/':
            return self._send(200, PAGE, 'text/html; charset=utf-8')
        if path == '/api/posts':
            return self._send(200, {'posts': list_posts(), 'accounts': ACCOUNTS,
                                    'pending': pending_counts(), 'cap': CAP,
                                    'hooks_left': hooks_available(),
                                    'builds': [b for b in build_queue()
                                               if not b.get('done') or b.get('status') == 'running']})
        if path == '/icon/arco.png':
            f = os.path.join(REPO, 'tools', 'slides', 'icons', 'icon-arco.png')
            with open(f, 'rb') as fh:
                return self._send(200, fh.read(), 'image/png')
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
        if not self.authed():
            return self.deny()
        path = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(n) or b'{}')
        if path == '/api/draft':
            topic = body['topic']
            keys = body.get('accounts') or [a['key'] for a in ACCOUNTS]
            return self._send(200, {'results': run_draft(topic, keys),
                                    'pending': pending_counts()})
        if path == '/api/build':
            with _lock:
                q = build_queue()
                if body.get('cancel'):
                    q = [b for b in q if b.get('done')]
                else:
                    job = {'count': max(1, min(10, int(body.get('count', 1)))),
                           'pillar': body.get('pillar') or 'tools',
                           'note': (body.get('note') or '').strip(),
                           'at': time.time(), 'done': False, 'status': 'queued'}
                    q.append(job)
                    threading.Thread(target=run_build, args=(job,), daemon=True).start()
                save_builds(q)
            return self._send(200, {'ok': True})
        if path == '/api/seen':
            with _lock:
                st = statuses()
                st.setdefault(body['topic'], {})['seen'] = True
                with open(STATUS, 'w') as fh:
                    json.dump(st, fh, indent=1)
            return self._send(200, {'ok': True})
        if path == '/api/approve':
            with _lock:
                st = statuses()
                st.setdefault(body['topic'], {})['approved'] = bool(body['approved'])
                st[body['topic']]['approved_at'] = time.time()
                with open(STATUS, 'w') as fh:
                    json.dump(st, fh, indent=1)
            return self._send(200, {'ok': True})
        if path == '/api/schedule':
            with _lock:
                sc = schedules()
                if body.get('cancel'):
                    sc = [x for x in sc if not (x['topic'] == body['topic'] and not x.get('done'))]
                else:
                    sc = [x for x in sc if not (x['topic'] == body['topic'] and not x.get('done'))]
                    sc.append({'topic': body['topic'], 'at': float(body['at']),
                               'accounts': body.get('accounts') or [],
                               'stagger_min': int(body.get('stagger_min') or 0),
                               'done': False})
                save_schedules(sc)
            return self._send(200, {'ok': True})
        if path == '/api/delete':
            # Move rather than remove: a post that took a render pass and a
            # review should not vanish because of a misclick.
            topic = body['topic']
            src = os.path.join(DRAFTS, topic)
            if not os.path.isdir(src) or os.path.dirname(os.path.normpath(src)) != DRAFTS:
                return self._send(400, {'error': 'bad topic'})
            with _lock:
                bin_ = os.path.join(DRAFTS, '_deleted')
                os.makedirs(bin_, exist_ok=True)
                dest = os.path.join(bin_, topic)
                if os.path.exists(dest):
                    dest += '-' + str(int(time.time()))
                os.rename(src, dest)
                idx, raw = hooks_index()
                posts = raw['posts'] if isinstance(raw, dict) else raw
                posts[:] = [x for x in posts if x.get('topic') != topic]
                with open(HOOKS, 'w') as fh:
                    json.dump(raw, fh, indent=1, ensure_ascii=False)
            return self._send(200, {'ok': True, 'moved_to': dest})
        if path == '/api/redo':
            n = queue_redo(body['topic'], int(body['slide']), body.get('note', ''))
            job = [x for x in redo_queue() if not x.get('done')][-1]
            threading.Thread(target=run_redo, args=(job,), daemon=True).start()
            return self._send(200, {'ok': True, 'open': n})
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
            threading.Thread(target=run_replicate, args=(q[-1],), daemon=True).start()
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


PAGE = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ARCO pipeline</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#020617; --surface:#0F172A; --surface-2:#1E293B; --line:#1E293B; --line-2:#293548;
  --text:#F8FAFC; --muted:#94A3B8; --dim:#64748B;
  --accent:#38BDF8; --ok:#22C55E; --warn:#F59E0B; --bad:#F43F5E;
  --r:10px; --z-modal:50;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--text);
  font:400 15px/1.6 "Fira Sans",-apple-system,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
code,.mono{font-family:"Fira Code",ui-monospace,monospace}
button{font:inherit;cursor:pointer}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

.app{display:grid;grid-template-columns:232px 1fr;height:100vh}

/* ---------- sidebar ---------- */
aside{background:var(--surface);border-right:1px solid var(--line);
  display:flex;flex-direction:column;padding:20px 14px;gap:26px;overflow:auto}
.brand{display:flex;align-items:center;gap:11px;padding:0 8px}
.brand img{width:34px;height:34px;border-radius:9px}
.brand .n{font-weight:600;font-size:15px;letter-spacing:.01em}
.brand .v{font-size:11px;color:var(--dim)}
nav{display:flex;flex-direction:column;gap:2px}
.navlabel{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);
  padding:0 8px;margin:0 0 8px}
.nav{display:flex;align-items:center;gap:10px;width:100%;text-align:left;background:none;
  border:0;color:var(--muted);padding:9px 10px;border-radius:8px;min-height:40px;
  transition:background .18s,color .18s}
.nav:hover{background:var(--surface-2);color:var(--text)}
.nav[aria-current="true"]{background:var(--surface-2);color:var(--text);font-weight:500}
.nav svg{width:17px;height:17px;flex:none;opacity:.9}
.nav .ct{margin-left:auto;font-size:11px;color:var(--dim);font-family:"Fira Code",monospace}

/* ---------- accounts ---------- */
.accounts{margin-top:auto;display:flex;flex-direction:column;gap:9px}
.acct{background:var(--surface-2);border:1px solid var(--line-2);border-radius:var(--r);padding:11px}
.acct .top{display:flex;align-items:center;gap:8px}
.acct svg{width:15px;height:15px;flex:none}
.acct .h{font-size:12px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acct .num{margin-left:auto;font-size:11px;font-family:"Fira Code",monospace;color:var(--muted)}
.track{height:4px;background:#0b1120;border-radius:3px;margin-top:9px;overflow:hidden}
.track i{display:block;height:100%;background:var(--accent);transition:width .25s}
.track.full i{background:var(--bad)}
.acct button{margin-top:8px;width:100%;background:none;border:1px solid var(--line-2);
  color:var(--muted);border-radius:7px;padding:5px;font-size:11px;min-height:30px;
  transition:border-color .18s,color .18s}
.acct button:hover{border-color:var(--accent);color:var(--text)}

/* ---------- main ---------- */
main{overflow:auto}
.bar{position:sticky;top:0;z-index:10;background:rgba(2,6,23,.92);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);padding:18px 28px;display:flex;align-items:center;gap:16px}
h1{font-size:17px;font-weight:600;margin:0;letter-spacing:.01em}
.sub{color:var(--dim);font-size:12px}
.wrap{padding:24px 28px 60px}

/* ---------- cards ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);
  overflow:hidden;cursor:pointer;transition:border-color .18s,background .18s;
  display:flex;flex-direction:column;text-align:left;padding:0;color:inherit;width:100%}
.card:hover{border-color:var(--line-2);background:var(--surface-2)}
.thumb{aspect-ratio:9/16;background:#0b1120;position:relative;max-height:250px;overflow:hidden}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
.card .meta{padding:11px 12px 13px}
.card .tt{font-size:13px;font-weight:600;margin-bottom:3px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.card .rs{font-size:11px;color:var(--dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pills{display:flex;gap:5px;margin-top:9px;flex-wrap:wrap}

.pill{font-size:10px;letter-spacing:.05em;text-transform:uppercase;padding:3px 8px;
  border-radius:20px;border:1px solid var(--line-2);color:var(--dim);white-space:nowrap;
  display:inline-flex;align-items:center;gap:5px}
.pill::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.pill.create{color:var(--warn);border-color:#5b420f}
.pill.ready{color:#A78BFA;border-color:#3b2f63}
.pill.scheduled{color:#A78BFA;border-color:#3b2f63}
.pill.drafted{color:var(--accent);border-color:#14405a}
.pill.published{color:var(--ok);border-color:#14532d}
.pill.failed{color:var(--bad);border-color:#5c1626}
.pill.liked{color:#F472B6;border-color:#5c2244}

/* ---------- detail ---------- */
.back{background:none;border:1px solid var(--line-2);color:var(--muted);border-radius:8px;
  padding:7px 13px;font-size:13px;min-height:36px;transition:border-color .18s,color .18s}
.back:hover{border-color:var(--accent);color:var(--text)}
.slides{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:6px 0 26px}
.slides img{width:100%;border-radius:9px;border:1px solid var(--line);display:block;cursor:zoom-in;
  transition:border-color .18s}
.slides img:hover{border-color:var(--accent)}
.sl{position:relative;cursor:pointer;padding:0;background:none;border:0;display:block;width:100%}
.sl .num{position:absolute;top:7px;left:7px;background:rgba(2,6,23,.82);color:var(--text);
  font:500 11px/1 "Fira Code",monospace;padding:4px 7px;border-radius:6px}
.sl[aria-pressed="true"] img{border-color:var(--accent);box-shadow:0 0 0 2px rgba(56,189,248,.35)}
.sl[aria-pressed="true"] .num{background:var(--accent);color:#04222f}
.del{position:absolute;top:8px;right:8px;width:32px;height:32px;border-radius:8px;
  background:rgba(2,6,23,.72);border:1px solid var(--line-2);color:var(--muted);
  display:flex;align-items:center;justify-content:center;opacity:.5;z-index:2;
  transition:opacity .18s,color .18s,border-color .18s}
.cardwrap:hover .del{opacity:1}
.del:hover{color:var(--bad);border-color:var(--bad)}
.del svg{width:15px;height:15px}
.cardwrap{position:relative}
.new{position:absolute;top:-5px;left:-5px;width:13px;height:13px;border-radius:50%;
  background:var(--bad);border:2px solid var(--bg);z-index:3}
.nav .badge{margin-left:6px;width:8px;height:8px;border-radius:50%;background:var(--bad);
  display:inline-block}
.hint{color:var(--dim);font-size:12px;margin:-14px 0 20px}
.busy{display:inline-block;width:13px;height:13px;border:2px solid rgba(4,34,47,.35);
  border-top-color:#04222f;border-radius:50%;animation:spin .7s linear infinite;
  vertical-align:-2px;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:16px}
.panel h2{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);
  margin:0 0 14px;font-weight:500}
label{display:block;font-size:12px;color:var(--muted);margin:0 0 6px}
input,textarea,select{width:100%;background:#0b1120;color:var(--text);border:1px solid var(--line-2);
  border-radius:8px;padding:10px 12px;font:inherit;transition:border-color .18s}
select{min-height:42px;cursor:pointer}
input:focus,textarea:focus{border-color:var(--accent);outline:none}
textarea{min-height:132px;resize:vertical;line-height:1.65}
.field{margin-bottom:14px}
.btn{background:var(--accent);color:#04222f;border:0;border-radius:8px;padding:10px 17px;
  font-weight:600;font-size:13px;min-height:42px;transition:filter .18s}
.btn:hover{filter:brightness(1.08)}
.btn.sec{background:var(--surface-2);color:var(--text);border:1px solid var(--line-2)}
.btn.sec:hover{border-color:var(--accent);filter:none}
.btn:disabled{opacity:.4;cursor:not-allowed;filter:none}
.actions{display:flex;gap:9px;flex-wrap:wrap}
.srow{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--line)}
.srow:last-child{border-bottom:0}
.srow .nm{width:180px;font-size:13px;display:flex;align-items:center;gap:8px}
.srow .nm svg{width:14px;height:14px;flex:none;opacity:.75}
.srow .sp{margin-left:auto;display:flex;gap:8px;align-items:center}
.log{font-family:"Fira Code",monospace;font-size:12px;color:var(--muted);white-space:pre-wrap;
  margin-top:14px;padding:12px;background:#0b1120;border-radius:8px;border:1px solid var(--line);display:none}
.log.on{display:block}
.empty{color:var(--dim);padding:56px 0;text-align:center}
.maker{background:var(--surface);border:1px solid var(--line);border-radius:12px;
  padding:18px 20px;margin-bottom:20px;display:flex;gap:18px;align-items:flex-end;flex-wrap:wrap}
.maker .grow{flex:1;min-width:210px}
.maker .cnt{font:600 30px/1 "Fira Code",monospace;color:var(--accent);min-width:44px;text-align:center}
input[type=range]{-webkit-appearance:none;appearance:none;background:none;padding:0;
  height:26px;border:0;width:100%}
input[type=range]::-webkit-slider-runnable-track{height:5px;border-radius:3px;background:var(--line-2)}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;
  border-radius:50%;background:var(--accent);margin-top:-8px;cursor:pointer;
  border:2px solid var(--bg)}
input[type=range]:focus-visible::-webkit-slider-thumb{outline:2px solid var(--text);outline-offset:2px}
#modal{position:fixed;inset:0;background:rgba(2,6,23,.8);display:none;align-items:center;
  justify-content:center;z-index:60;padding:24px}
#modal .box{background:var(--surface);border:1px solid var(--line-2);border-radius:14px;
  padding:24px;max-width:460px;width:100%;box-shadow:0 24px 60px rgba(0,0,0,.55)}
#modal h3{margin:0 0 10px;font-size:16px;font-weight:600}
#modal p{margin:0 0 18px;color:var(--muted);font-size:13px;line-height:1.6}
#modal .foot{display:flex;gap:9px;justify-content:flex-end;margin-top:20px}
#modal .danger{background:var(--bad);color:#fff}
.sched{display:grid;gap:12px}
.sched .accts{display:flex;gap:8px;flex-wrap:wrap}
.chk{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line-2);
  border-radius:8px;padding:8px 12px;font-size:13px;cursor:pointer;min-height:40px}
.chk input{width:auto;margin:0}
.when{color:var(--accent);font-family:"Fira Code",monospace;font-size:12px}
#zoom{position:fixed;inset:0;background:rgba(2,6,23,.94);display:none;align-items:center;
  justify-content:center;z-index:var(--z-modal);padding:24px}
#zoom img{max-height:88vh;max-width:min(88vw,520px);border-radius:12px}
#zoom .nav{position:absolute;top:50%;transform:translateY(-50%);width:52px;height:52px;
  border-radius:50%;background:rgba(30,41,59,.9);border:1px solid var(--line-2);color:var(--text);
  display:flex;align-items:center;justify-content:center;transition:background .18s,border-color .18s}
#zoom .nav:hover{background:var(--surface-2);border-color:var(--accent)}
#zoom .nav svg{width:22px;height:22px}
#zoom .prev{left:24px}#zoom .next{right:24px}
#zoom .count{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);
  font:500 13px/1 "Fira Code",monospace;color:var(--muted);background:rgba(2,6,23,.8);
  padding:8px 14px;border-radius:20px;border:1px solid var(--line-2)}
#zoom .close{position:absolute;top:22px;right:24px;width:42px;height:42px;border-radius:50%;
  background:rgba(30,41,59,.9);border:1px solid var(--line-2);color:var(--text)}
.toolbar{display:flex;align-items:center;gap:10px;margin:0 0 14px}
.toggle{background:var(--surface-2);border:1px solid var(--line-2);color:var(--muted);
  border-radius:8px;padding:9px 15px;font-size:13px;min-height:42px;font-weight:500;
  display:inline-flex;align-items:center;gap:8px;transition:border-color .18s,color .18s,background .18s}
.toggle:hover{border-color:var(--accent);color:var(--text)}
.toggle[aria-pressed="true"]{background:var(--accent);color:#04222f;border-color:var(--accent)}
.toggle svg{width:16px;height:16px}
@media (max-width:900px){
  .app{grid-template-columns:1fr;height:auto;min-height:100vh}
  /* The sidebar becomes a scrolling strip at the top: hiding it left a phone
     with no filters and no account state, which is most of the tool. */
  aside{border-right:0;border-bottom:1px solid var(--line);padding:14px;gap:14px}
  .brand{padding:0}
  nav{overflow-x:auto;-webkit-overflow-scrolling:touch}
  #nav{display:flex;gap:8px;min-width:max-content}
  .nav{width:auto;white-space:nowrap;padding:9px 13px;border:1px solid var(--line-2)}
  .nav .ct{margin-left:6px}
  .navlabel{display:none}
  .accounts{margin-top:0;flex-direction:row;overflow-x:auto;gap:8px}
  .acct{min-width:172px;flex:none}
  .bar{padding:14px 16px}
  .wrap{padding:16px 16px 48px}
  .grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:11px}
  .slides{grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:9px}
  .srow{flex-wrap:wrap}
  .srow .nm{width:auto}
  .srow .sp{margin-left:0;width:100%}
  .srow .sp .btn{flex:1}
  #zoom .prev{left:8px}#zoom .next{right:8px}
  #zoom .nav{width:44px;height:44px}
  #zoom img{max-width:82vw}
  .toolbar{flex-wrap:wrap}
}
</style></head><body>
<div class="app">
<aside>
  <div class="brand">
    <img src="/icon/arco.png" alt="ARCO app icon">
    <div><div class="n">ARCO</div><div class="v">content pipeline</div></div>
  </div>
  <nav aria-label="Filter posts">
    <p class="navlabel">Pipeline</p>
    <div id="nav"></div>
  </nav>
  <div class="accounts" id="accounts"></div>
</aside>
<main>
  <div class="bar"><h1 id="ttl">Needs review</h1><span class="sub" id="cnt"></span></div>
  <div class="wrap" id="view"></div>
</main>
</div>
<div id="modal" role="dialog" aria-modal="true" aria-labelledby="mt"><div class="box">
  <h3 id="mt"></h3><p id="mb"></p><div id="mx"></div>
  <div class="foot"><button class="btn sec" onclick="closeModal()">Cancel</button>
    <button class="btn" id="mok"></button></div></div></div>
<div id="zoom" role="dialog" aria-modal="true" aria-label="Slide preview">
  <button class="nav prev" onclick="step(-1,event)" aria-label="Previous slide">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg></button>
  <img id="zoomimg" alt="">
  <button class="nav next" onclick="step(1,event)" aria-label="Next slide">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg></button>
  <button class="close" onclick="closeZoom()" aria-label="Close preview">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
  <div class="count" id="zcount"></div>
</div>
<script>
const TIKTOK = 'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z';
const ICONS = {
  review:'<path d="M12 9v4m0 4h.01M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.4 0Z"/>',
  drafted:'<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/>',
  published:'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
  liked:'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1L12 21l7.7-7.6 1.1-1a5.5 5.5 0 0 0 0-7.8Z"/>',
  all:'<path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>'
};
const ic = k => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[k]}</svg>`;
const tk = c => `<svg viewBox="0 0 24 24" fill="${c||'currentColor'}" aria-hidden="true"><path d="${TIKTOK}"/></svg>`;
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

let DATA=null, cur=null, filter='create', sel=0, redoMode=false, zi=-1;
const PILLARS=[['tools','Tools'],['screentime','Screen time'],['discipline','Discipline'],
               ['build','Building'],['learn','Studying']];
const FILTERS=[['create','Create posts'],['drafted','Drafted'],['published','Published'],
               ['liked','Liked'],['archive','Archive'],['all','All posts']];

const DAY=86400;
function stateOf(p){
  const rs = DATA.accounts.map(a => (p.delivery||{})[a.key]);
  if (rs.some(r => r && r.published)) return 'published';
  if (rs.some(r => r && r.status==='SENT')) return 'drafted';
  if (rs.some(r => r && r.status==='FAILED')) return 'failed';
  // Never sent and older than three days: history from before the log existed,
  // not something waiting on Thinh. Keeping these in Needs review buried the
  // handful of posts that genuinely need a decision.
  // Approved posts stay on Create rather than moving to a page of their own:
  // the list is short, and a second page hid work that was one click from going out.
  if ((Date.now()/1000 - p.mtime) > 3*DAY) return 'archive';
  return 'create';
}
const match = p => filter==='all' ? true : filter==='liked' ? p.liked : stateOf(p)===filter;

async function load(){
  DATA = await (await fetch('/api/posts')).json();
  const unseen = DATA.posts.some(p => !p.seen && stateOf(p)==='create');
  const counts = Object.fromEntries(FILTERS.map(([k]) => [k,
    DATA.posts.filter(p => k==='all'?true:k==='liked'?p.liked:stateOf(p)===k).length]));
  ICONS.archive = ICONS.archive || '<path d="M21 8v13H3V8M1 3h22v5H1zM10 12h4"/>';
  ICONS.create = ICONS.create || '<path d="M12 5v14M5 12h14"/>';
  ICONS.ready = ICONS.ready || '<path d="M12 6v6l4 2"/><circle cx="12" cy="12" r="9"/>';
  document.getElementById('nav').innerHTML = FILTERS.map(([k,lab]) =>
    `<button class="nav" aria-current="${filter===k}" onclick="setFilter('${k}')">
       ${ic(ICONS[k]?k:'all')}<span>${lab}</span>
       ${k==='create'&&unseen?'<span class="badge"></span>':''}
       <span class="ct">${counts[k]}</span></button>`).join('');
  document.getElementById('accounts').innerHTML =
    `<p class="navlabel">Accounts</p>` + DATA.accounts.map(a=>{
      const n=DATA.pending[a.key]||0, full=n>=DATA.cap;
      return `<div class="acct">
        <div class="top">${tk('#F8FAFC')}<span class="h">${esc(a.label)}</span>
          <span class="num">${Math.min(n,DATA.cap)}/${DATA.cap}${n>DATA.cap?'+':''}</span></div>
        <div class="track ${full?'full':''}"><i style="width:${Math.min(100,n/DATA.cap*100)}%"></i></div>
        <button onclick="publishedAll('${a.key}')" aria-label="Mark all drafts published on ${esc(a.label)}">
          mark all published</button></div>`;}).join('');
  render();
}

function setFilter(k){ filter=k; cur=null; load(); }

function render(){ try{ render_(); }catch(err){
  // A blank page tells you nothing. Surface the failure where the list goes.
  document.getElementById('view').innerHTML =
    '<div class="empty">Something broke while drawing this view.<br><br><code>'+
    (err && err.message ? err.message : err)+'</code></div>';
  console.error(err);
} }
function render_(){
  const view=document.getElementById('view');
  document.getElementById('ttl').textContent =
    cur ? cur : (FILTERS.find(f=>f[0]===filter)||[])[1];
  if (cur) return detail();
  const list = DATA.posts.filter(match);
  document.getElementById('cnt').textContent = `${list.length} post${list.length===1?'':'s'}`;
  view.innerHTML = (filter==='create' ? maker() : '')
    + (list.length ? `<div class="grid">${list.map(card).join('')}</div>`
                   : `<div class="empty">Nothing here yet.</div>`);
  const r=document.getElementById('nrange');
  if(r) r.oninput = e => document.getElementById('ncount').textContent = e.target.value;
  // poll while a build is running so finished posts appear without a refresh
  const running = (DATA.builds||[]).some(b=>['queued','running'].includes(b.status));
  clearTimeout(window._poll);
  if(running) window._poll = setTimeout(()=>load().then(render), 6000);
}

function poll(){
  clearTimeout(window._poll2);
  window._poll2 = setTimeout(()=>load().then(()=>{ render(); poll(); }), 8000);
}

const TRASH='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"'
  +' stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>'
  +'<path d="M10 11v6M14 11v6"/></svg>';

function maker(){
  const left = DATA.hooks_left, jobs = (DATA.builds||[]);
  const live = jobs.find(x=>['queued','running'].includes(x.status));
  if(live){
    const mins = live.started ? Math.round((Date.now()/1000-live.started)/60) : 0;
    return `<div class="maker"><div class="grow">
      <div style="font-size:14px;font-weight:600;margin-bottom:4px">
        <span class="busy"></span>Building ${live.count} post${live.count===1?'':'s'}</div>
      <div class="sub">${esc((PILLARS.find(x=>x[0]===live.pillar)||[])[1]||live.pillar||'tools')}${live.note?' · '+esc(live.note):''}
        — writing and checking slides${mins?', '+mins+' min so far':''}. This page updates itself.</div>
      </div><button class="btn sec" onclick="cancelBuild()">Stop tracking</button></div>`;
  }
  // A finished or interrupted job is a notice, never a state: it must not sit
  // where the slider goes or you cannot start another build until you clear it.
  const dead = jobs.length ? jobs[jobs.length-1] : null;
  let strip = '';
  if(dead){
    const msg = dead.status==='interrupted'
      ? 'A build was interrupted by a restart. Anything it finished is in the list below.'
      : dead.status==='failed' ? 'The last build failed.' : 'Last build finished.';
    strip = `<div class="maker" style="padding:12px 16px"><div class="grow">
      <div class="sub">${msg}${dead.log?' '+esc(dead.log.slice(0,120)):''}</div></div>
      <button class="btn sec" onclick="cancelBuild()">Dismiss</button></div>`;
  }
  const max = Math.min(10, left);
  if(!max) return strip + `<div class="maker"><div class="grow">
      <div style="font-size:14px;font-weight:600;margin-bottom:4px">No approved hooks left</div>
      <div class="sub">Every hook in the pool has been used. Give Claude new ones and they
        become selectable here.</div></div></div>`;
  return strip + `<div class="maker">
    <div class="grow">
      <label for="nrange">How many posts</label>
      <input type="range" id="nrange" min="1" max="${max}" value="${Math.min(3,max)}">
      <div class="sub">${left} approved hook${left===1?'':'s'} left, so ${max} at most.</div>
    </div>
    <div class="cnt" id="ncount">${Math.min(3,max)}</div>
    <div class="grow"><label for="npil">Niche</label>
      <select id="npil">${PILLARS.map(([v,l])=>
        `<option value="${v}">${l}</option>`).join('')}</select></div>
    <div class="grow"><label for="nnote">Anything specific? (optional)</label>
      <input id="nnote" placeholder="e.g. lean on focus and blocking"></div>
    <button class="btn" onclick="requestBuild()">Create posts</button>
  </div>`;
}

async function requestBuild(){
  const count=parseInt(document.getElementById('nrange').value,10);
  const note=document.getElementById('nnote').value;
  const pillar=document.getElementById('npil').value;
  await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({count,note,pillar})});
  await load();
}
async function cancelBuild(){
  await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cancel:true})});
  await load();
}

function card(p){
  const st=stateOf(p);
  return `<div class="cardwrap">
    ${p.seen?'':`<span class="new" title="${p.from_replicate?'Replicated from '+esc(p.from_replicate):'Not opened yet'}"></span>`}
    <button class="del" onclick="del(event,'${p.topic}')"
      aria-label="Delete ${esc(p.topic)}">${TRASH}</button>
    <button class="card" onclick="open_('${p.topic}')">
    <div class="thumb"><img loading="lazy" src="/slide/${p.topic}/${p.slides[0]}"
      alt="First slide of ${esc(p.topic)}"></div>
    <div class="meta">
      <div class="tt">${esc(p.topic)}</div>
      <div class="rs">${p.from_replicate?'replicated from '+esc(p.from_replicate)+' · ':''}${esc(p.roster.join(' · ')||'roster not recorded')}</div>
      <div class="pills"><span class="pill ${p.approved&&st==='create'?'ready':st}">${
          st==='create' ? (p.approved?'ready':'to review') : st}</span>
        ${(p.schedules||[]).length?`<span class="pill scheduled">${fmt(p.schedules[0].at)}</span>`:''}
        ${p.liked?'<span class="pill liked">liked</span>':''}
        ${p.queued?'<span class="pill">replicating</span>':''}
        ${(p.redos||[]).length?`<span class="pill">${p.redos.length} redo</span>`:''}</div>
    </div></button></div>`;
}

function del(e,topic){
  e.stopPropagation();
  const p=DATA.posts.find(x=>x.topic===topic);
  const sent=DATA.accounts.some(a=>(p.delivery||{})[a.key]);
  showModal({
    title:`Delete ${topic}?`, ok:'Delete', danger:true,
    body:(sent?'This post has already been drafted to TikTok. Deleting it here does not remove those drafts. ':'')
      +'Slides move to drafts/_deleted, so it can be recovered.',
    action: async()=>{
      await fetch('/api/delete',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({topic})});
      if(cur===topic) back(); else await load();
    }});
}

function open_(t){
  cur=t; sel=0; redoMode=false; location.hash=t; render();
  const p=DATA.posts.find(x=>x.topic===t);
  if(p && !p.seen){
    fetch('/api/seen',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:t})}).then(()=>{ p.seen=true; });
  }
}
function back(){ cur=null; sel=0; redoMode=false; location.hash=''; render(); }

function detail(){
  const p=DATA.posts.find(x=>x.topic===cur);
  if(!p) return back();
  document.getElementById('cnt').textContent='';
  document.getElementById('view').innerHTML = `
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px">
      <button class="back" onclick="back()">&larr; Back</button>
      <span class="sub">${esc(p.note||'')}</span>
      <button class="back" style="margin-left:auto" onclick="del(event,'${p.topic}')"
        aria-label="Delete this post">Delete post</button></div>
    <div class="toolbar">
      <button class="toggle" aria-pressed="${redoMode}" onclick="toggleRedo()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v6h6"/>
          <path d="M3 13a9 9 0 1 0 3-7.7L3 8"/></svg>
        ${redoMode?'Done redoing':'Redo a slide'}</button>
      <span class="sub">${redoMode
        ? 'Pick the slide that is wrong.'
        : 'Click a slide to open it. Arrow keys move between slides.'}</span>
    </div>
    <div class="slides">${p.slides.map((s,i)=>
      `<button class="sl" aria-pressed="${redoMode && sel===i+1}"
         onclick="${redoMode?`pick(${i+1})`:`zoomAt(${i})`}"
         aria-label="${redoMode?'Select':'Open'} slide ${i+1}">
         <img loading="lazy" src="/slide/${p.topic}/${s}?v=${(p.slide_mtimes||{})[s]||0}"
              alt="Slide ${i+1}">
         <span class="num">${i+1}${(p.redos||[]).some(r=>r.slide===i+1)?' redo':''}</span>
       </button>`).join('')}</div>
    ${!redoMode ? '' : `
    <div class="panel"><h2>Redo a slide</h2>
      <div class="field">
        <label for="note">${sel?`What is wrong with slide ${sel}?`:'Select a slide above first'}</label>
        <textarea id="note" style="min-height:84px" ${sel?'':'disabled'}
          placeholder="e.g. background is too bright, the copy is washed out"></textarea>
      </div>
      <div class="actions">
        <button class="btn" id="rgb" onclick="redo()" ${sel?'':'disabled'}>Redo slide ${sel||''}</button>
        <button class="btn sec" onclick="zoomSel()" ${sel?'':'disabled'}>View full size</button>
      </div>
      <div class="log ${(p.redos||[]).length?'on':''}" id="rlog">${
        (p.redos||[]).map(r=>'slide '+r.slide+': '+esc(r.note)).join('\n')}</div>
    </div>`}

    ${p.approved ? `
    <div class="panel"><h2>Schedule</h2>
      ${(p.schedules||[]).length
        ? `<p style="margin:0 0 14px;color:var(--muted);font-size:13px">Queued for
             <span class="when">${fmt(p.schedules[0].at)}</span>
             to ${esc((p.schedules[0].accounts||[]).map(k=>label(k)).join(', ')||'all accounts')}
             ${p.schedules[0].stagger_min?`, ${p.schedules[0].stagger_min} min apart`:''}.
             The dashboard must be running when it comes due.</p>
           <div class="actions">
             <button class="btn sec" onclick="askSchedule()">Change</button>
             <button class="btn sec" onclick="cancelSchedule()">Cancel schedule</button></div>`
        : `<p style="margin:0 0 14px;color:var(--muted);font-size:13px">Approved and ready.
             Schedule the drafting, or send it now from Delivery below.</p>
           <div class="actions"><button class="btn" onclick="askSchedule()">Schedule drafting</button>
             <button class="btn sec" onclick="approve(false)">Move back to Create</button></div>`}
    </div>` : `
    <div class="panel"><h2>Review</h2>
      <p style="margin:0 0 14px;color:var(--muted);font-size:13px">
        Check the slides and the copy. Approving moves it to Ready, where you can schedule drafting.</p>
      <div class="actions"><button class="btn" onclick="approve(true)">Approve</button></div>
    </div>`}

    <div class="panel"><h2>Delivery</h2>
      ${DATA.accounts.map(a=>{
        const r=(p.delivery||{})[a.key];
        const st=!r?'review':r.published?'published':r.status==='SENT'?'drafted':'failed';
        const lab=st==='review'?'not sent':st;
        return `<div class="srow">
          <span class="nm">${tk('#94A3B8')}${esc(a.label)}</span>
          <span class="pill ${st}">${lab}</span>
          <span class="sp">
            ${r&&r.status==='SENT'?`<button class="btn sec" onclick="publish('${a.key}',${r.published?'false':'true'})">
                ${r.published?'Mark unpublished':'Mark published'}</button>`:''}
            <button class="btn sec" onclick="draft(['${a.key}'])"
              ${(DATA.pending[a.key]||0)>=DATA.cap?'disabled':''}>Draft</button>
          </span></div>`;}).join('')}
      <div class="actions" style="margin-top:16px">
        <button class="btn" onclick="draft(null)">Draft to all accounts</button>
      </div>
      <div class="log" id="log"></div>
    </div>

    <div class="panel"><h2>Copy</h2>
      <div class="field"><label for="ti">Title</label><input id="ti" value="${esc(p.title)}"></div>
      <div class="field"><label for="ca">Caption</label><textarea id="ca">${esc(p.caption)}</textarea></div>
      <div class="actions">
        <button class="btn sec" onclick="save()">Save copy</button>
        <button class="btn sec" onclick="like(${p.liked?'false':'true'})">
          ${p.liked?'Unlike':'Like'}</button>
        <button class="btn sec" onclick="replicate()" ${p.queued?'disabled':''}>
          ${p.queued?'Queued to replicate':'Replicate concept'}</button>
      </div></div>`;
}

function label(k){ return (DATA.accounts.find(a=>a.key===k)||{}).label || k; }
function fmt(ts){ const d=new Date(ts*1000);
  return d.toLocaleString([], {weekday:'short', day:'numeric', month:'short',
                               hour:'2-digit', minute:'2-digit'}); }

let onOK=null;
function showModal({title, body='', extra='', ok='Confirm', danger=false, action}){
  document.getElementById('mt').textContent=title;
  document.getElementById('mb').textContent=body;
  document.getElementById('mx').innerHTML=extra;
  const b=document.getElementById('mok');
  b.textContent=ok; b.className='btn'+(danger?' danger':'');
  onOK=action; document.getElementById('modal').style.display='flex';
  const f=document.querySelector('#mx input,#mx select'); if(f) f.focus();
}
function closeModal(){ document.getElementById('modal').style.display='none'; onOK=null; }
document.getElementById('mok').onclick=async()=>{ const f=onOK; closeModal(); if(f) await f(); };
document.getElementById('modal').onclick=e=>{ if(e.target.id==='modal') closeModal(); };

async function approve(v){
  await fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,approved:v})});
  await load(); render();
}

function askSchedule(){
  const d=new Date(Date.now()+3600e3); d.setSeconds(0,0);
  const iso=new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);
  showModal({
    title:'Schedule drafting',
    body:'The dashboard delivers these at the chosen time. It has to be running when they come due.',
    ok:'Schedule',
    extra:`<div class="sched">
      <div><label for="sdt">When</label><input type="datetime-local" id="sdt" value="${iso}"></div>
      <div><label>Accounts</label><div class="accts">${DATA.accounts.map(a=>
        `<label class="chk"><input type="checkbox" class="sa" value="${a.key}" checked>${esc(a.label)}</label>`
        ).join('')}</div></div>
      <div><label for="sg">Minutes between accounts</label>
        <input type="number" id="sg" min="0" max="720" step="15" value="0"></div></div>`,
    action: async()=>{
      const at=new Date(document.getElementById('sdt').value).getTime()/1000;
      const accounts=[...document.querySelectorAll('.sa')].filter(c=>c.checked).map(c=>c.value);
      const stagger_min=parseInt(document.getElementById('sg').value||'0',10);
      await fetch('/api/schedule',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({topic:cur,at,accounts,stagger_min})});
      await load(); render();
    }});
}
async function cancelSchedule(){
  await fetch('/api/schedule',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,cancel:true})});
  await load(); render();
}

function toggleRedo(){ redoMode=!redoMode; if(!redoMode) sel=0; render(); }

function zoomAt(i){
  const p=DATA.posts.find(x=>x.topic===cur); if(!p) return;
  location.hash = cur + '/' + (i+1);
  if(!p.slides || !p.slides.length) return;
  zi=Math.max(0,Math.min(i,p.slides.length-1));
  const f=p.slides[zi]; if(!f) return;
  const v=(p.slide_mtimes||{})[f]||0;
  const img=document.getElementById('zoomimg');
  img.src=`/slide/${p.topic}/${f}?v=${v}`;
  img.alt=`Slide ${zi+1} of ${p.slides.length}`;
  document.getElementById('zcount').textContent=`${zi+1} / ${p.slides.length}`;
  document.getElementById('zoom').style.display='flex';
}
function step(d,e){
  if(e) e.stopPropagation();
  const p=DATA.posts.find(x=>x.topic===cur); if(!p) return;
  zoomAt((zi+d+p.slides.length)%p.slides.length);
}
function closeZoom(){ document.getElementById('zoom').style.display='none'; zi=-1;
  if(cur) location.hash = cur; }
function zoom(src){ const z=document.getElementById('zoom');
  document.getElementById('zoomimg').src=src; z.style.display='flex'; }
document.getElementById('zoom').onclick=e=>{ if(e.target.id==='zoom') closeZoom(); };
document.addEventListener('keydown',e=>{
  const open = document.getElementById('zoom').style.display==='flex';
  if(e.key==='Escape'){ closeModal(); closeZoom(); return; }
  if(!cur) return;
  if(e.target.tagName==='TEXTAREA'||e.target.tagName==='INPUT') return;
  if(e.key==='ArrowRight'){ e.preventDefault(); open?step(1):zoomAt(0); }
  if(e.key==='ArrowLeft'){ e.preventDefault(); open?step(-1):zoomAt(0); }
});

function pick(n){ sel = (sel===n?0:n); render(); }
function zoomSel(){ if(sel) zoomAt(sel-1); }
async function redo(){
  const note=document.getElementById('note').value.trim();
  if(!note){ document.getElementById('note').focus(); return; }
  const r = await (await fetch('/api/redo',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,slide:sel,note})})).json();
  const keep=sel; await load(); sel=keep; render();
  const l=document.getElementById('rlog');
  if(l){ l.classList.add('on');
    l.textContent='Rebuilding slide '+keep+' now. It re-renders, checks the result and pushes, '
      +'so give it a few minutes. This page updates itself.'; }
  poll();
}

function say(t){const l=document.getElementById('log');if(l){l.textContent=t;l.classList.add('on');}}

async function save(){
  await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,title:ti.value,caption:ca.value})});
  await load(); say('Saved to hooks.json. Commit and push before drafting so Pages serves it.');
}
async function like(v){
  await fetch('/api/like',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,liked:v})}); await load();
}
async function replicate(){
  await fetch('/api/replicate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur})}); await load();
  say('Replicating now: same hook shape and roster pattern, different tools,\nfresh backgrounds and new teaching points. It appears in Create posts when done.');
  poll();
}
async function publish(key,v){
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,account:key,published:v})}); await load();
}
async function publishedAll(key){
  await fetch('/api/published',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({account:key})}); await load();
}
async function draft(accts){
  document.querySelectorAll('.panel button').forEach(b=>b.disabled=true);
  say('Sending. Each account polls to SEND_TO_USER_INBOX, so this takes a moment.');
  let txt;
  try{
    const res = await fetch('/api/draft',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:cur,accounts:accts})});
    if(!res.ok) throw new Error('server returned '+res.status);
    const r = await res.json();
    txt = Object.entries(r.results||{}).map(([k,v])=>
      `${k}: ${v.status}${v.detail?'  '+v.detail:''}`).join('\n') || 'no accounts attempted';
  }catch(err){
    txt = 'Draft failed: '+err.message+'\nNothing was recorded. The server log has the detail.';
  }
  await load();            // always re-render so buttons come back enabled
  say(txt);
}

load().then(()=>{
  // hash is <topic> or <topic>/<slide>, so a single slide is linkable
  const raw = decodeURIComponent(location.hash.slice(1));
  if(!raw) return;
  const [t, n] = raw.split('/');
  if(DATA.posts.some(p=>p.topic===t)){
    cur=t; render();
    if(n) zoomAt(parseInt(n,10)-1);
  }
});
</script></body></html>"""


if __name__ == '__main__':
    # A restart orphans any in-flight build: the thread that would mark it done
    # is gone, so the job would read as running forever.
    for path_, loader in ((BUILD, build_queue), (REDO, redo_queue), (REPLICATE, replicate_queue)):
        items = loader()
        if any(b.get('status') == 'running' for b in items):
            for b in items:
                if b.get('status') == 'running':
                    b['status'] = 'interrupted'
                    b['log'] = 'the dashboard restarted mid-run; check drafts/'
            with open(path_, 'w') as fh:
                json.dump(items, fh, indent=1, ensure_ascii=False)
    threading.Thread(target=scheduler_loop, daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    tok = access_token()
    with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as srv:
        print(f'this mac   http://localhost:{PORT}')
        try:
            print(f'wifi       http://{lan_ip()}:{PORT}/?k={tok}   (same network)')
        except Exception:
            print('wifi       no LAN address found')
        try:
            ts = subprocess.run(['tailscale', 'ip', '-4'], capture_output=True,
                                text=True, timeout=5).stdout.strip().split('\n')[0]
            if ts:
                print(f'anywhere   http://{ts}:{PORT}/?k={tok}   (tailscale)')
        except Exception:
            pass
        print('ctrl-c to stop')
        srv.serve_forever()
