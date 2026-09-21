#!/usr/bin/env python3
"""Local review dashboard for the TikTok pipeline.

  python3 tools/dashboard.py        # http://localhost:4500

Shows every built post, what has been delivered where, and how many pending
slots each account has left. Drafting runs the same autopost.js path the cron
job uses, so nothing here is a second implementation that can drift.

Stdlib only, no install. Binds to localhost.
"""
import base64
import gzip
import http.client
import http.server
import json
import random
import secrets
import signal
import socket
import mimetypes
import os
import re
import socketserver
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request

import hook_rules

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFTS = os.path.join(REPO, 'drafts')
HOOKS = os.path.join(REPO, 'tools', 'hooks.json')
IDEAS = os.path.join(REPO, 'tools', 'ideas.json')
IDEA_IMG = os.path.join(REPO, 'tools', 'ideas_img')
LOG = os.path.join(REPO, 'tools', 'delivery_log.json')
FEEDBACK = os.path.join(REPO, 'tools', 'post_feedback.json')
REPLICATE = os.path.join(REPO, 'tools', 'replicate_queue.json')
TOOL_USAGE = os.path.join(REPO, 'tools', 'tool_usage.json')
TOOL_POOL = os.path.join(REPO, 'tools', 'tool_pool.json')
PORT = int(os.environ.get('ARCO_PORT') or 4500)

# A second instance for UI work. It serves the same data read-only: no
# automatic sync, no scheduled builds. Two schedulers against one TikTok
# account and one subscription quota is the thing that must not happen.
DEV = os.environ.get('ARCO_DEV') == '1'

# Run a second instance beside the real one without a second copy of the
# truth. The page, its CSS and the slide JPGs come off local disk at no
# latency; every /api call is forwarded to the host that owns the state, so
# there is still one sync, one scheduler, and one delivery log. Two instances
# each holding their own state is how a post gets sent twice.
UPSTREAM = (os.environ.get('ARCO_UPSTREAM') or '').rstrip('/')
UPSTREAM_KEY = os.environ.get('ARCO_UPSTREAM_KEY') or ''
# A shared pool, not thread-local: the server makes a thread per connection,
# so a thread-local one is a fresh socket almost every time. Borrowed and
# returned around each call, and warmed at startup so the first request of the
# session does not pay the handshake either.
SLIDE_CACHE = os.path.join(REPO, 'tools', '.slide-cache')
# Where the app's daily usage snapshots are collected. Empty means the
# Users tab says so rather than showing an empty chart that looks like
# nobody is using the app.
METRICS_URL = (os.environ.get('ARCO_METRICS_URL') or '').rstrip('/')
METRICS_KEY = os.environ.get('ARCO_METRICS_KEY') or ''
# Writing to the Instagram queue is a different privilege from reading it.
METRICS_WRITE = os.environ.get('ARCO_METRICS_WRITE') or ''
# Instagram is its own lane. TikTok's ACCOUNTS carry a 5-draft cap, a
# delivery log and analytics cohorts, none of which mean anything here —
# Instagram publishes immediately and the Worker owns the result.
IG_ACCOUNTS = [{'key': 'getarco', 'label': 'get.arco'}]
BG_DIR = os.path.join(REPO, 'tools', 'slides', 'bg')
BG_INDEX = os.path.join(BG_DIR, '.index.json')
BG_THUMBS = os.path.join(REPO, 'tools', '.bg-thumbs')
ICON_DIR = os.path.join(REPO, 'tools', 'slides', 'icons')
API_CACHE = os.path.join(REPO, 'tools', '.api-cache')
# Reads worth keeping a copy of. Holding no state is what stops two hosts
# disagreeing about what was sent — but that only has to bind WRITES. A
# read-only snapshot means the link dropping costs you the ability to act,
# not the ability to look.
CACHEABLE = ('/api/posts', '/api/analytics')


def _api_cache_path(path, query):
    key = re.sub(r'[^a-z0-9]+', '-', (path + '?' + query).lower()).strip('-')
    return os.path.join(API_CACHE, key[:120] + '.json')
_pool, _pool_lock = [], threading.Lock()
POOL_MAX = 4


def _new_conn(timeout):
    u = urllib.parse.urlparse(UPSTREAM)
    cls = (http.client.HTTPSConnection if u.scheme == 'https'
           else http.client.HTTPConnection)
    return cls(u.hostname, u.port, timeout=timeout)


def _upstream_borrow(timeout=25):
    with _pool_lock:
        if _pool:
            c = _pool.pop()
            c.timeout = timeout
            if getattr(c, 'sock', None):
                try:
                    c.sock.settimeout(timeout)
                except Exception:
                    pass
            return c
    return _new_conn(timeout)


def _upstream_return(conn):
    with _pool_lock:
        if len(_pool) < POOL_MAX:
            _pool.append(conn)
            return
    try:
        conn.close()
    except Exception:
        pass


def warm_upstream(k=2):
    """Open the connections now so the first page load does not."""
    for _ in range(k):
        try:
            c = _upstream_borrow()
            c.request('GET', '/?k=' + UPSTREAM_KEY)
            c.getresponse().read()
            _upstream_return(c)
        except Exception as exc:
            print('[proxy] warm-up failed: %s' % exc, flush=True)
            return

ACCOUNTS = [
    # `short` is what fits on a card chip; three of them sit side by side.
    {'key': 'vn', 'label': 'arco.app', 'short': 'arco.app'},
    {'key': 'getarco', 'label': 'getarcoapp', 'short': 'getarco'},
    {'key': 'us', 'label': 'emiliagonzalez389', 'short': 'emilia'},
    {'key': 'max', 'label': 'maxmilian.dev', 'short': 'maxmilian'},
    {'key': 'prodgod', 'label': 'productivity_god', 'short': 'prodgod'},
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


# ---------------------------------------------------------------- ideas
#
# The board that feeds the pipeline: things to make, lines to open with,
# pictures to steal from, codes to give away. One flat list with a kind on
# each row rather than four files, because a note often turns out to be a
# hook and retyping it into another store is how notes get lost.

def load_ideas():
    try:
        with open(IDEAS, encoding='utf-8') as fh:
            rows = json.load(fh)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def save_ideas(rows):
    tmp = IDEAS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, IDEAS)


# The four that ship with the board. A kind is just a label, so anything
# typed into the kind field is as valid as these — the colour is derived from
# the string rather than looked up, which is what makes custom kinds free.
IDEA_KINDS = ('idea', 'hook', 'ref', 'code')


def clean_kind(k):
    k = re.sub(r'[^a-z0-9 _-]', '', (k or '').strip().lower())[:24]
    return k or 'idea'


def idea_apply(body):
    """One writer for every edit, so the file is read and written once."""
    rows = load_ideas()
    op = body.get('op')
    if op == 'add':
        row = {'id': 'i%d' % (time.time() * 1000),
               'kind': clean_kind(body.get('kind')),
               'text': (body.get('text') or '').strip()[:2000],
               'note': (body.get('note') or '').strip()[:2000],
               'pillar': body.get('pillar') or '',
               'img': body.get('img') or '',
               'used': False,
               'x': int(body.get('x') or 0),
               'y': int(body.get('y') or 0),
               'links': [],
               'at': int(time.time())}
        parent = body.get('from')
        if parent and any(r.get('id') == parent for r in rows):
            row['links'] = [parent]
        rows.insert(0, row)
    else:
        row = next((r for r in rows if r.get('id') == body.get('id')), None)
        if not row:
            return {'error': 'not found'}
        if op == 'del':
            # The picture goes with the card; nothing else references it.
            if row.get('img'):
                f = os.path.join(IDEA_IMG, os.path.basename(row['img']))
                if os.path.isfile(f):
                    try:
                        os.remove(f)
                    except OSError:
                        pass
            rows = [r for r in rows if r is not row]
            for r in rows:
                if r.get('links'):
                    r['links'] = [x for x in r['links'] if x != row['id']]
        elif op == 'edit':
            for k in ('text', 'note', 'pillar'):
                if k in body:
                    row[k] = (body.get(k) or '').strip()[:2000]
            if 'kind' in body:
                row['kind'] = clean_kind(body.get('kind'))
            if 'img' in body:
                # Swapping a picture leaves the old file with no card on it.
                old = row.get('img')
                row['img'] = os.path.basename(body.get('img') or '')
                if old and old != row['img']:
                    f = os.path.join(IDEA_IMG, os.path.basename(old))
                    if os.path.isfile(f):
                        try:
                            os.remove(f)
                        except OSError:
                            pass
        elif op == 'move':
            row['x'] = int(body.get('x') or 0)
            row['y'] = int(body.get('y') or 0)
        elif op == 'link':
            # One edge, stored once, on whichever end was dragged from. Both
            # ends draw it, so which end holds it never matters.
            other = body.get('to')
            if other == row['id'] or not any(r.get('id') == other for r in rows):
                return {'error': 'bad link'}
            for r in rows:
                r.setdefault('links', [])
            has = other in row['links'] or row['id'] in next(
                (r['links'] for r in rows if r.get('id') == other), [])
            if has:
                row['links'] = [x for x in row['links'] if x != other]
                for r in rows:
                    if r.get('id') == other:
                        r['links'] = [x for x in r['links'] if x != row['id']]
            else:
                row['links'].append(other)
        elif op == 'used':
            row['used'] = bool(body.get('used'))
        else:
            return {'error': 'bad op'}
    save_ideas(rows)
    return {'rows': rows}


def idea_save_image(data_url):
    """A pasted screenshot, straight off the clipboard. Returns its filename."""
    if not data_url.startswith('data:image/'):
        return None
    head, _, b64 = data_url.partition(',')
    ext = {'jpeg': 'jpg', 'png': 'png', 'gif': 'gif',
           'webp': 'webp'}.get(head.split('/')[1].split(';')[0], '')
    if not ext:
        return None
    raw = base64.b64decode(b64)
    if len(raw) > 12 * 1024 * 1024:
        return None
    os.makedirs(IDEA_IMG, exist_ok=True)
    name = '%d.%s' % (time.time() * 1000, ext)
    with open(os.path.join(IDEA_IMG, name), 'wb') as fh:
        fh.write(raw)
    return name


def save_log(log):
    with open(LOG, 'w') as fh:
        json.dump(log, fh, indent=1)


def published_today():
    """Posts that went out since local midnight, per account.

    A repost is a post going out, so it counts here. published_at is the
    FIRST outing and never moves, which is why a day spent reposting read as
    zero posts published — the work happened and the counter denied it.
    """
    midnight = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
    out = {a['key']: 0 for a in ACCOUNTS}
    for _t, accts in delivery_log().items():
        for key, rec in accts.items():
            if not rec.get('published'):
                continue
            when = max(rec.get('published_at') or 0, rec.get('last_out') or 0)
            if when >= midnight:
                out[key] = out.get(key, 0) + 1
    return out


def account_summary():
    """Followers now and the change since the oldest sample we hold.

    The sidebar used to say nothing but "published today", which is the least
    interesting fact about an account.
    """
    stats = load(ACCT_STATS, {})
    last = last_posted()
    out = {}
    for a in ACCOUNTS:
        v = stats.get(a['key']) or {}
        hist = v.get('history') or []
        first = hist[0]['followers'] if hist else None
        now = v.get('follower_count')
        out[a['key']] = {
            'followers': now,
            'delta': (now - first) if (now is not None and first is not None) else None,
            'days': len(hist),
            'total_likes': v.get('likes_count'),
            'posts': v.get('video_count'),
            'last_at': (last.get(a['key']) or {}).get('at'),
            'last_topic': (last.get(a['key']) or {}).get('topic'),
        }
    return out


def last_posted():
    """When each account last published, from TikTok's own timestamps.

    The sync records posted_at per post per account, so the newest of those is
    the real answer — not when a draft was sent, which can sit in the inbox
    for hours.
    """
    out = {}
    for topic, per in load(STATS, {}).items():
        for key, rec in (per or {}).items():
            at = rec.get('posted_at')
            if not at:
                continue
            if key not in out or at > out[key]['at']:
                out[key] = {'at': at, 'topic': topic}
    return out


def active_runs():
    """Every background job still going, plus anything that just failed.

    A failed job used to simply leave the list, and the page reads a job that
    disappeared as one that finished — so a redo that died on a usage limit
    showed a green tick for six seconds and then nothing at all. A failure has
    to outlive the run that caused it.
    """
    runs = []
    # A day, not a few hours: a run that dies overnight on a usage limit is
    # exactly the one you find out about in the morning.
    recent = time.time() - 36 * 3600
    for label, items in (('build', build_queue()), ('redo', redo_queue()),
                         ('replicate', replicate_queue()), ('gen', gen_queue())):
        for x in items:
            bad = (x.get('status') in ('failed', 'interrupted')
                   and (x.get('finished') or x.get('at') or 0) > recent
                   and not x.get('dismissed'))
            if x.get('status') in ('queued', 'running') or bad:
                if label == 'build':
                    what = '%d post%s' % (x['count'], '' if x['count'] == 1 else 's')
                elif label == 'redo':
                    ns = [n for n in (x.get('slides') or [x.get('slide')]) if n]
                    # No slides picked is now the normal case: the complaint
                    # decides which, so the label says the post, not "slide None".
                    what = ('%s slide%s %s' % (x['topic'], '' if len(ns) == 1 else 's',
                                               ', '.join(str(n) for n in ns))
                            if ns else 'redoing %s' % x['topic'])
                elif label == 'gen':
                    what = ('writing hooks' if x.get('what') == 'hooks'
                            else 'writing the post' if x.get('what') == 'post'
                            else 'writing %s' % (x.get('tool') or 'a slide'))
                else:
                    what = 'replicating %s' % x['from']
                log = str(x.get('log') or '')
                runs.append({'kind': label, 'what': what,
                             'topic': x.get('topic') or x.get('from'),
                             'mode': x.get('mode'),
                             'status': x.get('status', 'queued'),
                             'at': x.get('at'),
                             # The first line of the log is the reason; the
                             # rest is the agent thinking aloud.
                             'why': log.strip().split('\n')[0][:160] if bad else None,
                             # only a running job has an elapsed time worth
                             # showing; a queued one has not begun
                             'started': x.get('started') if x.get('status') == 'running' else None,
                             'queued_at': x.get('at')})
    return runs


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


def _days_since_published(rec_map):
    """Days since this post last went public anywhere, or None.

    Cards use it to offer a repost only once a post is old enough that running
    it again reads as a repeat rather than a double-post."""
    stamps = [r.get('published_at') for r in rec_map.values() if r.get('published_at')]
    for r in rec_map.values():
        stamps += [h.get('published_at') for h in (r.get('history') or [])
                   if h.get('published_at')]
    return (time.time() - max(stamps)) / 86400 if stamps else None


def list_posts():
    idx, _ = hooks_index()
    log = delivery_log()
    fb = load(FEEDBACK, {})
    stats = load(STATS, {})
    LIVE = ('queued', 'running')
    queued = {q['from'] for q in replicate_queue()
              if not q.get('done') and q.get('status', 'queued') in LIVE}
    st = statuses()
    sched = {}
    for x in schedules():
        if not x.get('done'):
            sched.setdefault(x['topic'], []).append(x)
    redos = {}
    for r in redo_queue():
        if not r.get('done') and r.get('status', 'queued') in LIVE:
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
            # A post's age, not its file's. git clone stamps every file with
            # the moment it cloned, so on a fresh host every post looked hours
            # old, nothing aged into Archive, and Review filled with work from
            # weeks ago. built_at is recorded once and travels with the state.
            'mtime': (st.get(topic, {}).get('built_at')
                      or os.path.getmtime(os.path.join(d, slides[0]))),
            'delivery': log.get(topic, {}),
            # How this post is tied to what is live: by an id TikTok gave us,
            # by an id we read off its url, or only by its caption — which is
            # the one that breaks when a caption is edited.
            'ident': {a['key']: (
                'tiktok' if (log.get(topic, {}).get(a['key']) or {}).get('video_id')
                else 'id' if ((stats.get(topic) or {}).get(a['key']) or {}).get('id')
                else 'caption' if ((stats.get(topic) or {}).get(a['key']))
                else None) for a in ACCOUNTS},
            'liked': bool(fb.get(topic, {}).get('liked')),
            'days_since': _days_since_published(log.get(topic, {})),
            'stats': stats.get(topic),
            'queued': topic in queued,
            'redos': redos.get(topic, []),
            'approved': bool(st.get(topic, {}).get('approved')),
            'seen': bool(st.get(topic, {}).get('seen')),
            'from_replicate': st.get(topic, {}).get('from_replicate'),
            'replicate_mode': st.get(topic, {}).get('replicate_mode'),
            'replicated': sum(1 for v in st.values()
                              if v.get('from_replicate') == topic),
            'schedules': sched.get(topic, []),
            'roster': roster_for(topic),
        })
    out.sort(key=lambda p: p['mtime'], reverse=True)
    return out


PAGES = 'https://chupappi7.github.io/arco-app/drafts'


def backfill_built_at():
    """Date every draft from the commit that added it.

    Cheap, one pass over history, and it only fills what is missing — so it
    costs nothing on a host that already has the dates.
    """
    with _lock:
        st = load(STATUS, {})
    have = {t for t, v in st.items() if v.get('built_at')}
    topics = {d for d in os.listdir(DRAFTS)
              if not d.startswith('_') and os.path.isdir(os.path.join(DRAFTS, d))}
    if not topics - have:
        return 0
    # A shallow clone has one commit, so every draft would be dated to the
    # moment of the clone — which is exactly the wrong answer, and worse than
    # no answer because it gets written down and then travels.
    try:
        shallow = subprocess.run(['git', 'rev-parse', '--is-shallow-repository'],
                                 cwd=REPO, capture_output=True, text=True,
                                 timeout=30).stdout.strip()
        if shallow == 'true':
            print('[built_at] shallow clone: cannot date posts from history. '
                  'Run `git fetch --unshallow` here, or copy post_status.json '
                  'from a host that has it.', flush=True)
            return 0
    except Exception:
        pass
    try:
        r = subprocess.run(
            ['git', 'log', '--diff-filter=A', '--name-only', '--format=%ct', '--', 'drafts/'],
            cwd=REPO, capture_output=True, text=True, timeout=180)
    except Exception as exc:
        print('[built_at] git unavailable: %s' % exc, flush=True)
        return 0
    first, ts = {}, None
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            ts = int(line)
            continue
        parts = line.split('/')
        if len(parts) >= 3 and parts[0] == 'drafts':
            t = parts[1]
            if t not in first or ts < first[t]:
                first[t] = ts
    added = 0
    with _lock:
        st = load(STATUS, {})
        for t in topics - have:
            if t in first:
                st.setdefault(t, {})['built_at'] = first[t]
                added += 1
        if added:
            with open(STATUS, 'w') as fh:
                json.dump(st, fh, indent=1, ensure_ascii=False)
    if added:
        print('[built_at] dated %d posts from git history' % added, flush=True)
    return added


def pages_ready(topic, tries=12, wait=8):
    """True once Pages serves byte-identical slides.

    autopost preflights that the URLs resolve, not that they are the current
    render, so a post edited after its last push would deliver the old slides.
    """
    import hashlib
    import ssl
    import urllib.request
    # This Python has no usable default trust store, so an unverified fetch
    # raises and the file reads as stale forever. Swallowing that error is how
    # every slide looked out of date while Pages was serving the right bytes.
    # certifi is not stdlib, and a host without it used to take the whole
    # draft down with an unhandled ModuleNotFoundError instead of saying so.
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return False, ('certifi is not installed on this host, so the slides '
                       'cannot be verified against Pages. Run: '
                       'python3 -m pip install --user certifi')
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


def _env():
    env = dict(os.environ)
    for line in open(os.path.join(REPO, '.env')):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
    return env


_creator_cache = {}


def creator_info(key, max_age=300):
    """The creator's own posting settings, straight from TikTok.

    The content-sharing guidelines require the posting UI to be built from
    this: only the privacy levels this creator actually has may be offered,
    and a control the creator has disabled must be shown disabled. Cached
    briefly because it is queried every time the publish panel opens.
    """
    hit = _creator_cache.get(key)
    if hit and time.time() - hit[0] < max_age:
        return hit[1]
    try:
        p = subprocess.run(
            ['node', 'tools/autopost.js', '--creator-info', '--account', key],
            cwd=REPO, env=_env(), capture_output=True, text=True, timeout=60)
        out = (p.stdout or '').strip()
        data = json.loads(out[out.index('{'):]) if '{' in out else {}
        if not data:
            # Surface the one line that says what went wrong, not the tail of
            # a multi-line hint, which is what a slice gives you.
            blob = ((p.stderr or '') + out).strip()
            line = next((l.strip() for l in blob.splitlines() if 'ERROR' in l), '')
            data = {'error': (line or blob[:200] or 'no response')}
    except Exception as exc:
        data = {'error': str(exc)}
    _creator_cache[key] = (time.time(), data)
    return data


def direct_blocked(key, settings):
    """Why this direct post must not go out, or '' if it may.

    The same three rules the panel enforces, re-checked at send time because a
    scheduled job carries choices made long before it fires.
    """
    priv = settings.get('privacy')
    if not priv:
        return 'no privacy level was chosen'
    if settings.get('branded_content') and priv == 'SELF_ONLY':
        return 'branded content cannot be posted privately'
    info = creator_info(key, max_age=0)
    if info.get('error'):
        return 'could not read the creator settings: %s' % info['error']
    opts = info.get('privacy_level_options') or []
    if priv not in opts:
        return '%s is no longer offered by this creator (has: %s)' % (
            priv, ', '.join(opts) or 'none')
    return ''


def run_publish(topic, key, settings):
    """Publish straight to the account, with the disclosures the user chose.

    Direct Post is only reachable once the app has passed TikTok's audit; an
    unaudited client has every post forced private, which is why this is a
    separate path from run_draft rather than a flag on it.
    """
    ok, why = pages_ready(topic)
    if not ok:
        return {'status': 'FAILED', 'detail': why, 'at': time.time()}
    cmd = ['node', 'tools/autopost.js', topic, '--account', key, '--direct-post',
           '--privacy', settings.get('privacy', ''), '--wait']
    if settings.get('disable_comment'):
        cmd.append('--disable-comment')
    if settings.get('auto_add_music'):
        cmd.append('--auto-add-music')
    if settings.get('brand_organic'):
        cmd.append('--brand-organic')
    if settings.get('branded_content'):
        cmd.append('--branded-content')
    print(f'[publish] {topic} -> {key}: {" ".join(cmd[3:])}', flush=True)
    try:
        p = subprocess.run(cmd, cwd=REPO, env=_env(), capture_output=True,
                           text=True, timeout=900)
        out = p.stdout + p.stderr
    except Exception as exc:
        out = f'runner error: {exc}'
    # TikTok reports a finished direct post as PUBLISH_COMPLETE; some
    # responses use PUBLICLY_AVAILABLE_POST for the same terminal state.
    if 'PUBLISH_COMPLETE' in out or 'PUBLICLY_AVAILABLE_POST' in out:
        rec = {'status': 'SENT', 'detail': 'published directly', 'at': time.time(),
               'published': True, 'published_at': time.time(), 'direct': True}
    else:
        reason = [l.strip() for l in out.splitlines() if 'ERROR' in l or 'fail_reason' in l]
        rec = {'status': 'FAILED', 'detail': (reason[0] if reason else out.strip()[-200:]),
               'at': time.time()}
    print(f'[publish] {topic} {key}: {rec["status"]} {rec["detail"][:90]}', flush=True)
    with _lock:
        log = delivery_log()
        log.setdefault(topic, {})[key] = rec
        save_log(log)
    return rec


def _keep_history(prev, rec):
    """Carry a previous delivery forward before it is overwritten.

    A repost sends the same slides to the same account a second time. Without
    this the first outing's published_at is lost, and with it the "posted 9
    days ago" signal that makes reposting worth offering at all.
    """
    if not prev:
        return rec
    past = list(prev.get('history') or [])
    past.append({k: v for k, v in prev.items() if k != 'history'})
    rec['history'] = past[-10:]
    return rec


STATS = os.path.join(REPO, 'tools', 'post_stats.json')
STATS_HISTORY = os.path.join(REPO, 'tools', 'stats_history.json')
# Daily closes. The raw file answers "what did the first 48 hours look like";
# this one answers "what changed yesterday", and unlike raw points it stays
# small forever, so no cap can quietly eat the week.
STATS_DAILY = os.path.join(REPO, 'tools', 'stats_daily.json')
UNTRACKED = os.path.join(REPO, 'tools', 'untracked_posts.json')
PROMOTED = os.path.join(REPO, 'tools', 'promoted.json')
PERFORMING_VIEWS = 1000       # what counts as a post that worked
REQUIRED_TAG = '#creatorsearchinsights'
SYNC_EVERY = 1800             # seconds between automatic syncs
RAW_KEEP = 72 * 3600          # how long raw snapshots live, for trajectories


def _norm(t):
    """Captions round-trip through TikTok with whitespace changes."""
    return ' '.join((t or '').lower().split())


def claim_published_ids(key):
    """Ask TikTok which video each of our drafts became.

    Identity today starts with a caption, and a caption is editable on both
    sides — which is how a post published to three accounts ended up as three
    unmatched rows. TikTok knows the answer: once a draft is published, its
    status carries the real post id. Asked once per draft, then never again.
    """
    log = delivery_log()
    todo = [(t, r) for t, per in log.items()
            for k, r in per.items()
            if k == key and r.get('publish_id') and not r.get('video_id')]
    if not todo:
        return 0
    found = 0
    for topic, rec in todo[:12]:          # a slow drip, not a stampede
        try:
            p = subprocess.run(
                ['node', 'tools/autopost.js', '--status', rec['publish_id'],
                 '--account', key],
                cwd=REPO, env=_env(), capture_output=True, text=True, timeout=90)
            out = (p.stdout or '')
            data = json.loads(out[out.index('{'):]) if '{' in out else {}
        except Exception:
            continue
        ids = data.get('publicaly_available_post_id') or data.get(
            'publicly_available_post_id') or []
        if ids:
            rec['video_id'] = str(ids[0])
            found += 1
    if found:
        with _lock:
            cur = delivery_log()
            for topic, per in log.items():
                for k, r in per.items():
                    if r.get('video_id'):
                        cur.setdefault(topic, {}).setdefault(k, {})['video_id'] = r['video_id']
            save_log(cur)
        print('[sync] %s: TikTok named %d published post(s)' % (key, found), flush=True)
    return found


def sync_account(key):
    """Read an account's own posts back and reconcile what we believe.

    TikTok cannot tell us whether an inbox draft was ever published, but the
    Display API lists what is actually on the profile. A post that appears
    there is published, by definition. Matching is on the caption, which comes
    back verbatim as video_description.
    """
    try:
        p = subprocess.run(
            ['node', 'tools/autopost.js', '--list-posts', '--account', key],
            cwd=REPO, env=_env(), capture_output=True, text=True, timeout=120)
        out = (p.stdout or '').strip()
        data = json.loads(out[out.index('{'):]) if '{' in out else {}
    except Exception as exc:
        return {'error': str(exc)}
    if not data.get('videos'):
        return {'error': ((p.stderr or '') + out).strip()[-160:] or 'no videos returned'}
    try:
        claim_published_ids(key)
    except Exception as exc:
        print('[sync] %s: id claim skipped: %s' % (key, exc), flush=True)

    idx, _ = hooks_index()
    # A caption can belong to more than one topic: a reshoot keeps the copy
    # byte-identical on purpose, so `ship-alone` and `ship-alone-2` look the
    # same here. One entry per caption meant the second silently overwrote the
    # first and a dozen uploads vanished from the numbers.
    # Hashtags are the part of a caption most likely to change after a post
    # has gone out — a tag gets added to the pool, or edited in the app — and
    # an exact match then fails forever. The body is what actually identifies
    # the post, so it gets its own index as a fallback.
    def _body(t):
        return re.sub(r'#\w+', '', _norm(t) or '').strip()

    by_caption, by_body = {}, {}
    for topic, post in idx.items():
        cap = _norm(post.get('caption'))
        if cap:
            by_caption.setdefault(cap, []).append(topic)
            b = _body(post.get('caption'))
            if len(b) >= 40:
                by_body.setdefault(b[:120], []).append(topic)
    log_now = delivery_log()

    def pick_topic(cap, key, posted_at, taken):
        """Of the topics sharing this caption, the one this upload came from.

        Decided by delivery time: whichever topic was sent to this account
        closest before the post appeared. Falls back to any unclaimed topic.
        """
        cands = [t for t in by_caption.get(cap, []) if (t, key) not in taken]
        if not cands:
            # Same words, different tags: still the same post.
            cands = [t for t in by_body.get(_body(cap)[:120], [])
                     if (t, key) not in taken]
        if not cands:
            return None
        if len(cands) == 1 or not posted_at:
            return cands[0]
        def gap(t):
            rec = (log_now.get(t) or {}).get(key) or {}
            sent = rec.get('at')
            return abs((sent or 0) - posted_at) if sent else float('inf')
        cands.sort(key=gap)
        return cands[0]

    matched, marked = 0, []
    with _lock:
        log = delivery_log()
        stats = load(STATS, {})
        hist = load(STATS_HISTORY, {})
        daily = load(STATS_DAILY, {})
        fb = load(FEEDBACK, {})
        promoted = set(load(PROMOTED, []))
        unmatched = load(UNTRACKED, {})

        # Match by TikTok's own video id, not by caption. A reshoot keeps the
        # copy byte-identical on purpose, so two live videos share a caption
        # and caption matching is order-dependent: whichever the API lists
        # first takes whichever sibling sorts first. That crossed the two
        # series and corrupted a third of the history file. An id never ties.
        pinned = {}
        # Ids TikTok told us outright, which beat anything inferred.
        for t, per_ in log.items():
            r = (per_ or {}).get(key) or {}
            if r.get('video_id'):
                pinned[str(r['video_id'])] = t
        for t, per_ in stats.items():
            # Never pin an untracked video to its own placeholder. Doing so
            # made the orphan permanent: the id claimed it back on every pass,
            # so it never got another chance to match a caption, and a post
            # that failed to match once could never be adopted afterwards.
            if t.startswith('tiktok:'):
                continue
            cell = per_.get(key) or {}
            if cell.get('id'):
                pinned[str(cell['id'])] = t
            elif cell.get('url'):
                m = re.search(r'/video/(\d+)', cell['url'] or '')
                if m:
                    pinned[m.group(1)] = t

        claimed = set()          # (topic, account) already taken this pass
        topic_of = {}
        for v in data['videos']:
            t = pinned.get(str(v.get('id') or ''))
            if t and (t, key) not in claimed:
                topic_of[str(v.get('id'))] = t
                claimed.add((t, key))
        # Captions decide only for uploads never seen before.
        for v in data['videos']:
            vid = str(v.get('id') or '')
            if vid in topic_of:
                continue
            cap = _norm(v.get('video_description') or v.get('title'))
            t = pick_topic(cap, key, v.get('create_time'), claimed)
            if t:
                topic_of[vid] = t
                claimed.add((t, key))

        # Reposting is a button in this dashboard, so the same post really can
        # be live twice on one account. Those extra runs used to match nothing
        # and surface as separate untracked rows — the same slides, the same
        # caption, three more lines in the list.
        reruns = {}
        for v in data['videos']:
            vid = str(v.get('id') or '')
            if vid in topic_of:
                continue
            cap = _norm(v.get('video_description') or v.get('title'))
            for t in (by_caption.get(cap) or by_body.get(_body(cap)[:120]) or []):
                if (t, key) in claimed:
                    topic_of[vid] = t
                    reruns.setdefault((t, key), []).append(v)
                    break

        rerun_ids = {str(e.get('id')) for lst in reruns.values() for e in lst}
        for v in data['videos']:
            if str(v.get('id') or '') in rerun_ids:
                continue                       # folded in below, not its own cell
            topic = topic_of.get(str(v.get('id') or ''))
            # Pins keep untracked posts stable across syncs, but they are not
            # matches: counting them would report 59/59 for an account where
            # twenty posts predate the pipeline.
            if topic and not topic.startswith('tiktok:'):
                matched += 1
            elif not topic:
                # Posts that predate the pipeline, or whose caption was edited
                # on TikTok. They are still this account's real performance —
                # dropping them under-reported the account, and the single
                # best post on arco.app was one of them.
                topic = 'tiktok:' + str(v.get('id'))
                unmatched.setdefault(topic, {'caption': (v.get('video_description')
                                                         or v.get('title') or '')[:120]})
            # Per account: the same post runs on all three and they perform
            # very differently. One record per topic hid that completely.
            # Snapshot before overwriting. Views in the first 24h is what
            # separates a push from a kill, and a cumulative-only file can
            # never show it.
            prev = (stats.get(topic) or {}).get(key) or {}
            now_v = v.get('view_count', 0)
            point = {'views': now_v, 'likes': v.get('like_count', 0),
                     'comments': v.get('comment_count', 0),
                     'shares': v.get('share_count', 0)}
            if prev.get('views') != now_v:
                arr = hist.setdefault(topic, {}).setdefault(key, [])
                last = arr[-1]['views'] if arr else None
                if last is not None and now_v < last * 0.9:
                    # Views only go up. A real fall means this series got
                    # crossed with another video, so refuse the point and say
                    # so — a visible warning beats silent corruption.
                    print('[sync] %s/%s views fell %s to %s, point rejected'
                          % (topic, key, last, now_v), flush=True)
                else:
                    arr.append(dict(point, at=time.time()))
                    # Time-based, not count-based. The old 200-point cap was
                    # about four days at a 30-minute beat, so it silently ate
                    # the week before the week could be drawn.
                    floor = time.time() - RAW_KEEP
                    hist[topic][key] = [x for x in arr if x['at'] >= floor][-400:]
            # One close per calendar day, overwritten as the day goes on.
            day = time.strftime('%Y-%m-%d', time.localtime())
            daily.setdefault(topic, {}).setdefault(key, {})[day] = point
            # A video adopted by a real topic must stop existing as its own
            # placeholder, or its views are counted twice: once against the
            # post and once against tiktok:<id>.
            ph = 'tiktok:' + str(v.get('id') or '')
            if not topic.startswith('tiktok:') and ph in stats:
                stats[ph].pop(key, None)
                if not stats[ph]:
                    stats.pop(ph, None)
                    unmatched.pop(ph, None)
            stats.setdefault(topic, {})[key] = dict(
                point, id=str(v.get('id') or '') or None,
                url=v.get('share_url'), cover=v.get('cover_image_url'),
                posted_at=v.get('create_time'), synced=time.time())
            acc = log.setdefault(topic, {})
            rec = acc.get(key)
            if rec is None:
                # Live on the account with nothing in the delivery log: sent
                # before the log existed, or from another machine. Without this
                # the post sits in Review forever asking to be drafted again.
                acc[key] = {'status': 'SENT', 'detail': 'found live by sync',
                            'at': v.get('create_time') or time.time(),
                            'published': True,
                            'published_at': v.get('create_time') or time.time()}
                marked.append(topic)
            elif rec.get('status') == 'SENT' and not rec.get('published'):
                rec['published'] = True
                rec['published_at'] = v.get('create_time') or time.time()
                marked.append(topic)
            # The flag drives the hook cooldown, so let the numbers set it
            # rather than waiting to be told.
            best = max((r.get('views', 0) for r in stats[topic].values()), default=0)
            # Paid reach is not a signal. The flag feeds the hook cooldown and
            # the replicate suggestions, so letting a promoted post set it
            # tells the pipeline an ad-boosted concept earned its numbers.
            if topic in promoted:
                if (fb.get(topic) or {}).get('by') == 'sync':
                    fb[topic]['liked'] = False
                    fb[topic]['by'] = 'sync:promoted'
            elif best >= PERFORMING_VIEWS and not fb.get(topic, {}).get('liked'):
                fb.setdefault(topic, {}).update({'liked': True, 'at': time.time(),
                                                 'by': 'sync'})
        # One row per post, carrying what every run of it earned. A repost is
        # the same post reaching more people, not a different post.
        FIELDS = (('views', 'view_count'), ('likes', 'like_count'),
                  ('comments', 'comment_count'), ('shares', 'share_count'))
        for (topic, k), extra in reruns.items():
            cell = (stats.get(topic) or {}).get(k)
            if not cell:
                continue
            for e in extra:
                for ours, theirs in FIELDS:
                    cell[ours] = (cell.get(ours) or 0) + (e.get(theirs) or 0)
            cell['runs'] = [{'id': str(e.get('id')), 'views': e.get('view_count', 0),
                             'posted_at': e.get('create_time')} for e in extra]
            # When it FIRST went out and when it was LAST out are different
            # dates, and folding a repost into its original row kept only the
            # first. A post reposted today then sorted to nine days ago and
            # looked like sync had missed it. posted_at stays the first
            # outing, because that is what the analytics cohorts count; this
            # is what the Published list sorts and dates by.
            cell['last_out'] = max([cell.get('posted_at') or 0]
                                   + [e.get('create_time') or 0 for e in extra])
            rec = (log.get(topic) or {}).get(k)
            if rec:
                rec['last_out'] = cell['last_out']
            # A run folded into a post must stop existing as its own orphan,
            # or the row it was meant to replace stays in the list.
            for e in extra:
                ph = 'tiktok:' + str(e.get('id'))
                if ph in stats:
                    stats[ph].pop(k, None)
                    if not stats[ph]:
                        stats.pop(ph, None)
                        unmatched.pop(ph, None)
            print('[sync] %s/%s: folded in %d repost(s)' % (topic, k, len(extra)), flush=True)

        save_log(log)
        with open(STATS, 'w') as fh:
            json.dump(stats, fh, indent=1, ensure_ascii=False)
        with open(STATS_HISTORY, 'w') as fh:
            json.dump(hist, fh, ensure_ascii=False)
        with open(STATS_DAILY, 'w') as fh:
            json.dump(daily, fh, ensure_ascii=False)
        with open(UNTRACKED, 'w') as fh:
            json.dump(unmatched, fh, indent=1, ensure_ascii=False)
        with open(FEEDBACK, 'w') as fh:
            json.dump(fb, fh, indent=1, ensure_ascii=False)
    return {'seen': len(data['videos']), 'matched': matched,
            'newly_published': marked, 'has_more': data.get('has_more')}


ACCT_STATS = os.path.join(REPO, 'tools', 'account_stats.json')


def sync_account_stats(key):
    """Follower and like totals for the account itself, not its posts."""
    try:
        p = subprocess.run(
            ['node', 'tools/autopost.js', '--account-stats', '--account', key],
            cwd=REPO, env=_env(), capture_output=True, text=True, timeout=60)
        out = (p.stdout or '').strip()
        return json.loads(out[out.index('{'):]) if '{' in out else {}
    except Exception:
        return {}


def sync_all():
    out = {}
    with _lock:
        acct = load(ACCT_STATS, {})
    for a in ACCOUNTS:
        info = sync_account_stats(a['key'])
        if info:
            hist = (acct.get(a['key']) or {}).get('history') or []
            # One row per calendar day, rewritten as the day goes on, so
            # "+N followers today" is today's close minus yesterday's rather
            # than a diff against whenever the last sample happened to land.
            today = time.strftime('%Y-%m-%d', time.localtime())
            row = {'at': time.time(), 'day': today,
                   'followers': info.get('follower_count', 0),
                   'likes': info.get('likes_count', 0),
                   'posts': info.get('video_count', 0)}
            if hist and hist[-1].get('day') == today:
                hist[-1] = row
            else:
                hist.append(row)
            info['history'] = hist[-120:]
            acct[a['key']] = info
    with _lock:
        with open(ACCT_STATS, 'w') as fh:
            json.dump(acct, fh, indent=1, ensure_ascii=False)
    for a in ACCOUNTS:
        out[a['key']] = sync_account(a['key'])
        r = out[a['key']]
        print('[sync] %s: %s' % (a['key'], r.get('error') or
              'matched %d of %d, published %d' % (r['matched'], r['seen'],
                                                  len(r['newly_published']))), flush=True)
    return out


PERIODS = {'1': 1, '7': 7, '28': 28, '60': 60, '365': 365}



def analytics(period='7', only=None, frm=None, to=None):
    """Everything the Analytics tab needs, computed here rather than in JS.

    The shape is deliberately opinionated: a hit rate rather than a total, a
    median rather than a mean, and per-account rows kept separate. One post
    swings 30x between accounts, so any figure that averages them away is
    describing something that does not exist.
    """
    stats = load(STATS, {})
    accts = load(ACCT_STATS, {})
    idx, _ = hooks_index()
    st = statuses()
    # Filtering happens here rather than in the browser so every figure —
    # medians, cohorts, the matrix — comes from one place.
    keys = [a['key'] for a in ACCOUNTS if not only or a['key'] in only]
    if not keys:
        keys = [a['key'] for a in ACCOUNTS]

    hook_of = {}
    for e in load(os.path.join(REPO, 'tools', 'hook_history.json'), []):
        if e.get('topic'):
            hook_of[e['topic']] = ' / '.join(e['hook'])
    pillar_of = {' / '.join(h['lines']).lower(): h.get('pillar')
                 for h in load(HOOK_POOL, {}).get('hooks', [])}

    untracked = load(UNTRACKED, {})
    promoted = set(load(PROMOTED, []))
    rows, flat = [], []
    for topic, per in stats.items():
        cells = {k: (per.get(k) or {}).get('views') for k in keys}
        vals = [v for v in cells.values() if v is not None]
        if not vals:
            continue
        hook = hook_of.get(topic, '')
        # A thumbnail says which post this is faster than any slug. Local
        # slide when we still have the draft, TikTok's own cover when we do not.
        thumb = None
        d = os.path.join(DRAFTS, topic)
        if os.path.isdir(d):
            shots = sorted(f for f in os.listdir(d) if f.lower().endswith('.jpg'))
            if shots:
                thumb = '/slide/%s/%s' % (topic, shots[0])
        if not thumb:
            thumb = next((c.get('cover') for c in per.values() if c.get('cover')), None)

        rows.append({
            'topic': topic,
            'thumb': thumb,
            'untracked': topic.startswith('tiktok:'),
            'promoted': topic in promoted,
            'title': (idx.get(topic) or {}).get('title', '')
                     or (untracked.get(topic) or {}).get('caption', ''),
            # A video we cannot tie to a post has no slug, and forty
            # characters of its caption is not a name — it wraps, it collides
            # with the next row's, and two different posts can open the same
            # way. A short slug from its opening words reads like every other
            # row and still says which post it is.
            'name': topic if not topic.startswith('tiktok:')
                    else _slugish((untracked.get(topic) or {}).get('caption', ''),
                                  topic),
            'cells': cells,
            'likes': {k: (per.get(k) or {}).get('likes') for k in keys},
            'comments': {k: (per.get(k) or {}).get('comments') for k in keys},
            'shares': {k: (per.get(k) or {}).get('shares') for k in keys},
            'at': {k: (per.get(k) or {}).get('posted_at') for k in keys},
            # First out and last out are different dates once a post has been
            # reposted, and "the posts I put out today" means the second one.
            'out': {k: max((per.get(k) or {}).get('posted_at') or 0,
                           (per.get(k) or {}).get('last_out') or 0) or None
                    for k in keys},
            'urls': {k: (per.get(k) or {}).get('url') for k in keys},
            'best': max(vals), 'worst': min(vals),
            'spread': round(max(vals) / max(1, min(vals)), 1),
            'breakouts': sum(1 for v in vals if v >= PERFORMING_VIEWS),
            'pillar': pillar_of.get(hook.lower()),
            'mode': (st.get(topic) or {}).get('replicate_mode'),
            'source': (st.get(topic) or {}).get('from_replicate'),
            'posted_at': max((per[k].get('posted_at') or 0) for k in per),
        })
        for k, v in cells.items():
            if v is not None:
                flat.append({'account': k, 'views': v, 'promoted': topic in promoted,
                             'likes': (per.get(k) or {}).get('likes', 0),
                             'at': (per.get(k) or {}).get('posted_at')})
    rows.sort(key=lambda r: -r['best'])

    def median(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else 0

    organic = [f for f in flat if not f['promoted']]
    paid = [f for f in flat if f['promoted']]
    per_account = {}
    for k in keys:
        vs = [f['views'] for f in organic if f['account'] == k]
        pv = [f['views'] for f in paid if f['account'] == k]
        per_account[k] = {
            'posts': len(vs), 'wins': sum(1 for v in vs if v >= PERFORMING_VIEWS),
            'median': median(vs), 'total': sum(vs),
            'followers': (accts.get(k) or {}).get('follower_count'),
            'history': (accts.get(k) or {}).get('history') or [],
            # Kept apart rather than hidden: TikTok's own analytics counts
            # these, so a number that silently omits them looks wrong.
            'paid_posts': len(pv),
            'paid_wins': sum(1 for v in pv if v >= PERFORMING_VIEWS),
            'paid_views': sum(pv),
        }

    # Worth replicating: broke out on more than one account, and has not been
    # used as a source already.
    already = {r['source'] for r in rows if r['source']}
    queued = {q['from'] for q in replicate_queue() if not q.get('done')}
    suggest = [r['topic'] for r in rows
               if r['breakouts'] >= 2 and r['topic'] not in already
               and r['topic'] not in queued][:6]
    # High like rate but low views: people who saw it liked it, TikTok just
    # never showed it to many. The clearest "repost this" signal there is.
    rated = [f for f in organic if f['views'] >= 50]
    rates = sorted(f['likes'] / f['views'] for f in rated)
    med_rate = rates[len(rates) // 2] if rates else 0
    buried = []
    for r in rows:
        if r['promoted'] or r['best'] >= PERFORMING_VIEWS:
            continue
        for k in keys:
            v, lk = r['cells'].get(k), (r['likes'] or {}).get(k)
            if v and lk and v >= 50 and (lk / v) > med_rate * 1.5:
                buried.append({'topic': r['topic'], 'views': v, 'likes': lk,
                               'rate': round(100 * lk / v, 1),
                               'title': r['title'], 'untracked': r['untracked']})
                break
    buried.sort(key=lambda b: -b['rate'])

    # The finding worth watching: one account buried while another was pushed.
    suppressed = [r for r in rows if r['best'] >= PERFORMING_VIEWS and r['worst'] < 100]

    # Cohort comparison: posts published in this window against the window
    # before it. Views are cumulative, so a "views this week" figure would need
    # history we have only just started collecting; cohorts work from day one.
    days = PERIODS.get(period, 7)
    now = time.time()
    cut, prev_cut = now - days * 86400, now - 2 * days * 86400

    def cohort(lo, hi):
        rs = [r for r in rows if not r['promoted'] and lo <= (r['posted_at'] or 0) < hi]
        vs, lk, cm, sh = [], 0, 0, 0
        for r in rs:
            for k in keys:
                cell = (stats.get(r['topic']) or {}).get(k)
                if not cell:
                    continue
                vs.append(cell.get('views', 0))
                lk += cell.get('likes', 0)
                cm += cell.get('comments', 0)
                sh += cell.get('shares', 0)
        return {
            'posts': len(rs), 'account_posts': len(vs),
            'views': sum(vs), 'likes': lk, 'comments': cm, 'shares': sh,
            'median': median(vs),
            'broke_out': sum(1 for r in rs if r['breakouts']),
            'hit_rate': round(100 * sum(1 for v in vs if v >= PERFORMING_VIEWS)
                              / max(1, len(vs))),
        }

    this, prev = cohort(cut, now + 1), cohort(prev_cut, cut)

    fol_now = sum((per_account[k]['followers'] or 0) for k in keys)
    fol_then = 0
    for k in keys:
        h = per_account[k]['history']
        past = [x for x in h if x['at'] <= cut]
        fol_then += (past[-1]['followers'] if past else 0)

    return {
        'rows': rows, 'flat': flat,
        'published': _published_cohort(rows, flat, frm, to, keys),
        'stale': _stale_drafts(),
        'undelivered': _undelivered(),
        'top_per_account': _top_per_account(rows, keys),
        'accounts': [a for a in ACCOUNTS if a['key'] in keys],
        'all_accounts': ACCOUNTS, 'selected': keys,
        'period': period, 'days': days,
        'window': {'this': this, 'prev': prev,
                   'followers': fol_now,
                   'followers_delta': (fol_now - fol_then) if fol_then else None,
                   'from': cut, 'to': now,
                   'daily': _daily_views(rows, cut, now, keys, stats)},
        'per_account': per_account,
        'threshold': PERFORMING_VIEWS,
        'kpi': {
            'hit_rate': round(100 * sum(1 for f in organic if f['views'] >= PERFORMING_VIEWS)
                              / max(1, len(organic))),
            'account_posts': len(organic),
            'promoted': len(flat) - len(organic),
            'broke_out': sum(1 for r in rows if r['breakouts']),
            'topics': len(rows),
            'median': median([f['views'] for f in organic]),
            'total': sum(f['views'] for f in flat),
        },
        'suggest': suggest,
        'buried': buried[:6],
        'like_rate': round(100 * med_rate, 1),
        'suppressed': [{'topic': r['topic'], 'best': r['best'], 'worst': r['worst'],
                        'spread': r['spread']} for r in suppressed[:6]],
        'pillars': _pillar_table(rows),
        'pairs': [{'copy': r['topic'], 'mode': r['mode'], 'source': r['source'],
                   'copy_best': r['best'],
                   'source_best': next((x['best'] for x in rows
                                        if x['topic'] == r['source']), None),
                   'source_live': any(x['topic'] == r['source'] for x in rows)}
                  for r in rows if r['source']],
    }


def _undelivered():
    """Posts that reached some accounts and not others.

    Two shapes, and the second is the one that hides: a delivery that failed
    outright, and an account with no record at all. Nothing errors in the
    second case, so it never surfaced anywhere — a post simply ran on two
    accounts instead of three and the numbers looked merely weak.
    """
    log = delivery_log()
    keys = [a['key'] for a in ACCOUNTS]
    # An account that did not exist yet cannot have been missed. getarco and
    # us start on 22 Aug; without this every July post reads as a gap.
    born = {}
    for per_ in log.values():
        for k, r in per_.items():
            a = r.get('at') or 0
            if a and (k not in born or a < born[k]):
                born[k] = a
    out = []
    for topic, per in log.items():
        if topic.startswith('tiktok:'):
            continue
        # A post nobody has yet is not a failure, it is unreviewed.
        if not any((per.get(k) or {}).get('status') in ('SENT', 'FAILED') for k in keys):
            continue
        at = max((r.get('at') or 0) for r in per.values())
        failed = [k for k in keys if (per.get(k) or {}).get('status') == 'FAILED']
        missing = [k for k in keys if k not in per and at > born.get(k, float('inf'))]
        if failed or missing:
            out.append({
                'topic': topic, 'failed': failed, 'missing': missing,
                'detail': next((str((per.get(k) or {}).get('detail') or '')[:90]
                                for k in failed), ''),
                'at': at,
            })
    out.sort(key=lambda x: -x['at'])
    return out[:10]


def _stale_drafts():
    """Sent, never published, and old enough to be costing a slot.

    Five pending shares per account per rolling day, and only publishing frees
    one — so an unpublished draft is an expiring asset, not a to-do.
    """
    out = []
    for topic, per in delivery_log().items():
        for k, rec in per.items():
            if rec.get('published') or rec.get('status') != 'SENT':
                continue
            age = time.time() - (rec.get('at') or 0)
            if age > 20 * 3600:
                out.append({'topic': topic, 'account': k,
                            'hours': round(age / 3600)})
    out.sort(key=lambda x: -x['hours'])
    return out[:8]


def _top_per_account(rows, keys):
    """The three posts each account actually got reach on."""
    out = {}
    for k in keys:
        got = [{'topic': r['topic'], 'title': r['title'], 'thumb': r['thumb'],
                'untracked': r['untracked'],
                'views': r['cells'][k], 'likes': r['likes'].get(k) or 0}
               for r in rows if not r['promoted'] and r['cells'].get(k)]
        got.sort(key=lambda x: -x['views'])
        for g in got:
            g['rate'] = round(100 * g['likes'] / max(1, g['views']), 1)
        out[k] = got[:3]
    return out


def _slugish(caption, fallback):
    """A short, slug-shaped name from a caption's opening words."""
    words = re.findall(r"[a-z0-9']+", (caption or '').lower())
    drop = {'the', 'a', 'an', 'and', 'of', 'to', 'in', 'is', 'it', 'my', 'i',
            'for', 'on', 'that', 'this', 'with', 'you', 'your'}
    keep = [w for w in words if w not in drop][:3] or words[:3]
    return '-'.join(keep) or fallback[-8:]


def _published_cohort(rows, flat, lo, hi, keys):
    """Posts whose publish date falls in the window, with totals to date.

    Deliberately not the same question as "views gained this week". These are
    running totals since publish, so a post from Monday carries five days of
    views and one from this morning carries three hours. Every figure here is
    cohort; nothing on this screen is a delta.
    """
    if lo is None:
        return None
    hi = hi if hi is not None else time.time()

    out = []
    for r in rows:
        when = r.get('out') or r['at']
        ats = {k: t for k, t in when.items() if t and lo <= t < hi}
        if not ats:
            continue
        tot = {m: sum((r[m].get(k) or 0) for k in ats)
               for m in ('cells', 'likes', 'comments', 'shares')}
        vs = [r['cells'][k] for k in ats if r['cells'].get(k) is not None]
        out.append({
            'topic': r['topic'], 'thumb': r['thumb'], 'title': r['title'],
            'untracked': r['untracked'], 'promoted': r['promoted'],
            'pillar': r['pillar'],
            # Per account, never summed: one post swings 30x between them and
            # a total hides the only thing worth seeing.
            'cells': {k: r['cells'].get(k) for k in ats},
            'urls': {k: r['urls'].get(k) for k in ats},
            'per': {k: {'likes': r['likes'].get(k) or 0,
                        'comments': r['comments'].get(k) or 0,
                        'shares': r['shares'].get(k) or 0} for k in ats},
            'at': ats,
            # When it last went out, not when it first did.
            'last_at': max(ats.values()), 'first_at': min(ats.values()),
            'views': tot['cells'], 'likes': tot['likes'],
            'comments': tot['comments'], 'shares': tot['shares'],
            'best': max(vs) if vs else 0,
            'rate': round(100 * tot['likes'] / max(1, tot['cells']), 1),
        })
    out.sort(key=lambda x: -x['last_at'])

    org = [x for x in out if not x['promoted']]
    ups = [(x, k) for x in org for k in x['at']]
    vals = sorted(x['cells'][k] or 0 for x, k in ups)
    paid = [x for x in out if x['promoted']]
    return {
        'from': lo, 'to': hi, 'rows': out,
        'totals': {
                # Every post that went up, promoted included: "how many did I
            # publish" is a fact about the day, not a quality measure.
            'posts': len(out), 'uploads': sum(len(x['at']) for x in out),
            'views': sum(x['views'] for x in org),
            'likes': sum(x['likes'] for x in org),
            'comments': sum(x['comments'] for x in org),
            'shares': sum(x['shares'] for x in org),
            'median': vals[len(vals) // 2] if vals else 0,
            'hits': sum(1 for v in vals if v >= PERFORMING_VIEWS),
            'paid_posts': len(paid),
            'paid_views': sum(x['views'] for x in paid),
        },
    }


def _daily_views(rows, lo, hi, keys, stats):
    """Views grouped by the day the post went out.

    Not the same as TikTok's daily views — the API gives a running total per
    post, never a per-day series — so this answers "what did the posts I
    published that day earn", which is the question that maps to a decision.
    """
    buckets = {}
    for r in rows:
        if r['promoted'] or not r['posted_at'] or not (lo <= r['posted_at'] < hi):
            continue
        day = time.strftime('%Y-%m-%d', time.localtime(r['posted_at']))
        b = buckets.setdefault(day, {'views': 0, 'posts': 0})
        b['posts'] += 1
        for k in keys:
            cell = (stats.get(r['topic']) or {}).get(k)
            if cell:
                b['views'] += cell.get('views', 0)
    return [{'day': d, **v} for d, v in sorted(buckets.items())]


def _pillar_table(rows):
    out = {}
    for r in rows:
        p = r['pillar'] or 'unknown'
        e = out.setdefault(p, {'posts': 0, 'broke_out': 0, 'bests': []})
        e['posts'] += 1
        e['broke_out'] += 1 if r['breakouts'] else 0
        e['bests'].append(r['best'])
    for e in out.values():
        b = sorted(e.pop('bests'))
        e['median_best'] = b[len(b) // 2] if b else 0
    return out


def run_draft(topic, keys):
    """Deliver via autopost.js, one attempt per account, and record it."""
    ok, why = pages_ready(topic)
    if not ok:
        return {k: {'status': 'FAILED', 'detail': why + '. Commit and push, then retry.',
                    'at': time.time()} for k in keys}
    results = {}
    env = _env()
    print(f'[draft] {topic} -> {", ".join(keys)}', flush=True)
    for key in keys:
        try:
            p = subprocess.run(
                ['node', 'tools/autopost.js', topic, '--account', key, '--wait'],
                cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
            out = p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            out = 'timeout after 10 minutes'
        except Exception as exc:
            out = f'runner error: {exc}'
        if 'SEND_TO_USER_INBOX' in out:
            status, detail = 'SENT', ''
        elif 'spam_risk' in out.lower():
            status, detail = 'CAPPED', 'five unpublished drafts on this account'
        else:
            reason = [l.strip() for l in out.splitlines() if 'fail_reason' in l]
            status, detail = 'FAILED', (reason[0] if reason else out.strip()[-160:])
        # autopost prints the publish id and then discards it. Keeping it is
        # what lets TikTok name the video later: once the draft is published,
        # the status endpoint returns the real post id, and a post identified
        # by its id can never be lost to a caption edit.
        m = re.search(r'publish_id:\s*(\S+)', out)
        results[key] = {'status': status, 'detail': detail, 'at': time.time()}
        if m:
            results[key]['publish_id'] = m.group(1)
        elif status == 'SENT':
            # A send with no id means this post can only ever be found again by
            # its caption, which is the thing that keeps breaking. Say so on
            # the send rather than discovering it weeks later in the numbers.
            results[key]['detail'] = (detail + ' · no publish_id captured, so '
                                      'this one falls back to caption matching').strip(' ·')
            print('[draft] %s %s: NO publish_id in autopost output' % (topic, key),
                  flush=True)
        print(f'[draft] {topic} {key}: {status} {detail[:80]}', flush=True)
    with _lock:
        log = delivery_log()
        acc = log.setdefault(topic, {})
        for k, rec in results.items():
            acc[k] = _keep_history(acc.get(k), rec)
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


GEN = os.path.join(REPO, 'tools', 'gen_queue.json')
GEN_OUT = os.path.join(REPO, 'tools', '.gen')


def gen_queue():
    return load(GEN, [])


def save_gen(q):
    # Only the last fifty. These are drafts of two lines, not history.
    with open(GEN, 'w') as fh:
        json.dump(q[-50:], fh, indent=1, ensure_ascii=False)


GEN_HOOKS_PROMPT = """Write {n} candidate hooks for the {pillar} pillar of Thinh's TikTok account. Work in {repo}.

Read ~/.claude/skills/tiktok-pipeline/content.md, the "Copy rules" section, and
examples.md. The register there is the target and it is not negotiable: quiet,
lowercase, a stated result, no founder framing, no rhetorical questions, no
vague teases. A hook that could be about anything is not a hook.

Two lines, each under 42 characters, because they are set in SF Bold 74 on a
1080 canvas and are never shrunk. The break between the lines is a real
decision: line one sets up, line two lands the result.

These already exist — write nothing close to them:
{existing}

{ask}
Write ONLY this JSON to {out} and nothing else:
{{"hooks": [{{"lines": ["first line", "second line"]}}, ...]}}
Then print DONE. Do not render slides, do not touch hook_pool.json, do not
commit. This is a list of candidates for Thinh to choose from.
"""

GEN_SLIDE_PROMPT = """Write the copy for ONE slide of a TikTok carousel. Work in {repo}.

Read ~/.claude/skills/tiktok-pipeline/content.md first — the copy rules there
are what this is judged against.

The post: {pillar} pillar, hook "{hook}".
{about}

What the other slides already say, so this one does not repeat them:
{others}

Rules for this slide, all of which compose enforces at render time:
- Two body lines. The first is the MECHANISM — what the thing actually does.
  The second is the CONSEQUENCE — what that gets you, concretely. Never a
  verdict, never an adjective doing the work of a claim.
- It must ANSWER THE HOOK. If the slide would sit unchanged under a different
  hook, it is not answering this one.
- The claim must be a real capability, not an invention.
- First person ("I use this every day") ONLY for tools Thinh actually uses:
  Claude, Codex, ARCO, GitHub, Notion, Obsidian, ClickUp, Google Calendar,
  Endel, Higgsfield, RevenueCat, Shopify, OpenClaw. Everything else gets the
  neutral teaching voice.
- Sentence case. Roughly 34 characters a line; a title over about 22 characters
  gets shrunk, so keep it short.

Write ONLY this JSON to {out} and nothing else:
{{"title": "the slide's heading", "lines": ["mechanism", "consequence"]}}
Then print DONE. Do not render anything, do not write to hooks.json, do not
commit. Thinh is composing the post and this is one field in it.
"""


GEN_POST_PROMPT = """Write the copy for the slides of ONE TikTok carousel that are still blank. Work in {repo}.

Read ~/.claude/skills/tiktok-pipeline/content.md first — the copy rules there
are what this is judged against — and examples.md for the register.

The post: {pillar} pillar, hook "{hook}".

Here is the whole post. Slides marked WRITE THIS are the ones to fill; the
rest are Thinh's and are shown so the ones you write do not repeat them and
do read as one post rather than five unrelated cards:
{plan}

For every slide you write:
- Two body lines. The first is the MECHANISM — what the thing actually does.
  The second is the CONSEQUENCE — what that gets you, concretely. Never a
  verdict, never an adjective doing the work of a claim.
- It must ANSWER THE HOOK. If a slide would sit unchanged under a different
  hook, it is not answering this one.
- The claim must be a real capability, not an invention.
- First person ("I use this every day") ONLY for tools Thinh actually uses:
  Claude, Codex, ARCO, GitHub, Notion, Obsidian, ClickUp, Google Calendar,
  Endel, Higgsfield, RevenueCat, Shopify, OpenClaw. Everything else gets the
  neutral teaching voice.
- No two slides may teach the same thing, and none may repeat a teaching
  point already used in a tools/hooks.json caption.
- Sentence case, roughly 34 characters a line. A title over about 22
  characters gets shrunk, so keep titles short.

Write ONLY this JSON to {out} and nothing else, one entry per slide you were
asked to write, using the slide numbers above:
{{"slides": [{{"n": 2, "title": "...", "lines": ["mechanism", "consequence"]}}, ...]}}
Then print DONE. Do not render anything, do not write to hooks.json, do not
commit. Thinh is composing this post and these are fields in it.
"""


def _gen_clean(job, data):
    """Keep what the agent returned only if it is the shape that was asked for.

    A generator that quietly returns something else fills the composer with
    fields nobody checked. Better to fail the run and say so.
    """
    if job['what'] == 'hooks':
        out = []
        for h in (data.get('hooks') or [])[:8]:
            lines = [str(x).strip().lower() for x in (h.get('lines') or []) if str(x).strip()]
            if len(lines) != 2 or any(len(l) > 42 for l in lines):
                continue
            # The pool decides what counts as the same hook; reuse that rather
            # than a second opinion about it.
            if hook_rules.parent(lines):
                continue
            out.append({'lines': lines, 'pillar': job.get('pillar')})
        return {'hooks': out} if out else None
    if job['what'] == 'post':
        out = []
        for sl in (data.get('slides') or [])[:12]:
            lines = [str(x).strip() for x in (sl.get('lines') or []) if str(x).strip()]
            if len(lines) != 2:
                continue
            try:
                n = int(sl.get('n'))
            except (TypeError, ValueError):
                continue
            out.append({'n': n, 'title': str(sl.get('title') or '').strip(),
                        'lines': lines})
        return {'slides': out} if out else None
    lines = [str(x).strip() for x in (data.get('lines') or []) if str(x).strip()]
    if len(lines) != 2:
        return None
    return {'title': str(data.get('title') or '').strip(), 'lines': lines}


def run_gen(job):
    def mark(**kw):
        with _lock:
            q = gen_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            save_gen(q)

    os.makedirs(GEN_OUT, exist_ok=True)
    out_file = os.path.join(GEN_OUT, '%s.json' % str(job['at']).replace('.', '_'))
    if job['what'] == 'hooks':
        el = hook_rules.pool()
        existing = '\n'.join('  "%s" / "%s"' % (h['lines'][0], h['lines'][1])
                              for h in el if h.get('pillar') == job.get('pillar'))
        prompt = GEN_HOOKS_PROMPT.format(
            n=job.get('n', 5), pillar=job.get('pillar', 'tools'), repo=REPO,
            existing=existing or '  (none yet for this pillar)',
            ask=('Thinh asked for: %s\n' % job['note']) if job.get('note') else '',
            out=out_file)
    elif job['what'] == 'post':
        prompt = GEN_POST_PROMPT.format(
            repo=REPO, pillar=job.get('pillar', 'tools'),
            hook=job.get('hook') or '(not chosen yet — write to the pillar)',
            plan=job.get('plan') or '  (nothing yet)', out=out_file)
    else:
        about = (('This slide is about %s. Use its real name as the title.'
                  % job['tool']) if job.get('tool')
                 else ('This slide is point %d of the post — a step or reason '
                       'that answers the hook, not a tool.' % job.get('n', 2)))
        if job.get('note'):
            about += '\nThinh asked for: %s' % job['note']
        prompt = GEN_SLIDE_PROMPT.format(
            repo=REPO, pillar=job.get('pillar', 'tools'),
            hook=job.get('hook') or '(not chosen yet — write to the pillar)',
            about=about, others=job.get('others') or '  (nothing yet)',
            out=out_file)

    def check(out, good):
        if not good:
            return good, out
        try:
            with open(out_file) as fh:
                data = json.load(fh)
        except Exception as exc:
            return False, 'it said DONE but wrote no usable JSON: %s' % exc
        clean = _gen_clean(job, data)
        if not clean:
            return False, 'what it wrote was not the shape asked for'
        mark(result=clean)
        return True, out

    _agent(prompt, mark, 'DONE', kind='gen', job=job, check=check)


def spec_brief(spec):
    """Turn the composed post into instructions, slide by slide.

    A sentence in a textarea was the only way to reach the build path, so
    every choice arrived as prose an agent had to interpret — and the parts
    it interpreted loosely are the parts that came back wrong. A slide he
    filled in is a slide the agent renders; a slide he left blank is a slide
    it writes. Nothing in between.
    """
    if not spec:
        return ''
    slides = spec.get('slides') or []
    out = []
    hook = next((sl for sl in slides if sl.get('kind') == 'hook'), None)
    if hook:
        lines = [l for l in (hook.get('lines') or []) if str(l).strip()]
        if lines:
            out.append('HOOK — use this one, exactly as written. Do not reword '
                       'it and do not pick another:\n  "%s"\n  "%s"\n'
                       'It is in tools/hook_pool.json. Call '
                       'compose.mark_hook_used(HOOK, TOPIC) once the post is saved.'
                       % (lines[0], lines[1] if len(lines) > 1 else ''))
    body = []
    for i, sl in enumerate(slides):
        n = i + 1
        kind = sl.get('kind')
        bits = []
        if sl.get('bg'):
            bits.append('background %s' % sl['bg'])
        if kind == 'hook':
            bits.append('the hook slide')
        elif kind == 'cta':
            bits.append('the closing card — compose.cta_slide, app icon and '
                        'full store name')
        elif sl.get('tool'):
            bits.append('the tool is %s' % sl['tool'])
        if sl.get('title'):
            bits.append('title "%s"' % sl['title'])
        copy = [l for l in (sl.get('lines') or []) if str(l).strip()]
        if copy and kind != 'hook':
            bits.append('body:\n' + '\n'.join('      - %s' % l for l in copy))
        if not bits:
            bits.append('yours to fill in under the usual rules')
        elif kind != 'hook' and not copy:
            bits.append('the copy is yours to write')
        body.append('  slide %d: %s' % (n, '; '.join(bits)))
    if body:
        out.append('SLIDES — this is the post, in this order. Where he named a '
                   'background use that file and do not substitute; where he '
                   'wrote copy keep his words and his order, tightening only a '
                   'line that will not fit; where a slide is blank, write it:\n'
                   + '\n'.join(body)
                   + '\nRender exactly %d slide%s.'
                     % (len(body), '' if len(body) == 1 else 's'))
    if (spec.get('caption') or '').strip():
        out.append('CAPTION — write it around this angle: %s'
                   % spec['caption'].strip())
    if not out:
        return ''
    return ('Thinh composed this post in the dashboard. Everything below is '
            'decided — follow it exactly. Anything he left open, choose under '
            'the usual rules.\n\n' + '\n\n'.join(out) + '\n')


BUILD_PROMPT = """Build {count} new {pillar} post(s) for the TikTok pipeline. Work in {repo}.

{note}
Read ~/.claude/skills/tiktok-pipeline/examples.md FIRST for register, and
content.md for the rules. Skipping examples.md is how hooks and copy drift out
of Thinh's voice; it is not optional.

Rules, all enforced in code, so run them rather than trusting memory:

1. Hooks MUST come from tools/hook_pool.json, and only ones that are
   eligible for THIS pillar: call hook_rules.eligible(pillar='{pillar}').
   Never take a hook tagged with another pillar — the hook decides the shape
   of the post, and compose refuses a roster of apps under a screentime,
   discipline or learn hook. Those get rule_slide: numbered steps that answer
   the hook. Hooks are reusable but sit out a cooldown, so read
   hook_rules.eligible() rather than the `used` flag. Rewording a hook a
   little is allowed; inventing one is not. compose.hook_slide
   refuses anything else. Record each with compose.mark_hook_used(HOOK,
   TOPIC) — pass the topic, it is what ties the hook to its performance.
   If there are not enough eligible hooks, build fewer and say so.
2. The hook slide carries the ICON SHELF: call compose.hook_slide(..., icons=[...])
   with the roster's icons, so the apps appear under the hook. This is the
   look of the account, not a variation to choose between — a hook with no
   shelf reads as a different series. Use it on every tools post.
3. Roster from tools/tool_pool.json. ARCO leads at slide 1. Exactly one LLM
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
4b. The slide must ANSWER THE HOOK, and that includes ARCO's. Pass the hook's
   theme to compose.next_arco_angle(theme) -- focus, study, screentime,
   discipline, planning, build, business or insights -- so a hook about
   studying without touching your phone gets the blocking copy, not the
   "plan the day in 30 seconds" copy. The same applies to every other tool:
   pick the capability that answers what the hook promised. If a slide would
   sit unchanged under a different hook, it is not answering this one.
5. Write a generator script tools/gen-<topic>.py so the post can be rebuilt,
   render the slides to drafts/<topic>/01.jpg through 06.jpg, then READ every
   rendered JPG back and fix anything that looks wrong. A contact sheet per
   post is fine. Undersized hook text, copy washed out over a bright frame and
   a wrong icon are all obvious by eye and invisible in the code.
6. Register each post in tools/hooks.json with topic, title and caption.
   Call compose.record_post_tools and compose.record_post_bgs.

7. Commit and push. TikTok pulls the images from GitHub Pages, so a post that
   is only on disk cannot be delivered. After pushing, poll
   https://chupappi7.github.io/arco-app/drafts/<topic>/<nn>.jpg for every slide
   until its md5 matches the local file. Pages lags behind the push; a post is
   not finished until it actually serves.

Do NOT ingest new backgrounds and do NOT touch tools/slides/bg. The pool is
curated by Thinh; a build picks from what is already there. Adding images he
has not approved puts a look he never chose into his feed.

Do NOT deliver anything to TikTok. Thinh approves and schedules that himself.
Finish by printing: BUILT <topic> [, <topic>...]
"""


PUSH_RULE = """
Commit and push when the slides are final. TikTok pulls the images from GitHub
Pages, so a post that is only on disk cannot be delivered.

Do NOT wait for Pages to catch up and do NOT poll it. The dashboard checks
md5 parity itself before every delivery, so a push is all you owe. An agent
that polls here has no deadline and will sit burning quota for hours.

Do NOT deliver anything to TikTok. Print the finish line below as the very
last thing you output.

Registering the post is part of building it, not an afterthought. Append an
entry to the "posts" array in tools/hooks.json with the topic, a title, a
caption and the slide list, then read the file back and confirm your entry is
there with a non-empty caption. A post with no caption cannot be delivered:
autopost has nothing to send, and the dashboard marks it broken. This is
checked after you finish, so skipping it fails the run rather than passing it.
"""

REDO_PROMPT = """Fix specific slides in an existing TikTok carousel. Work in {repo}.

Post: {topic}
{slides}
What Thinh says is wrong:
{note}

1. Find tools/gen-*.py referencing '{topic}'. That file is the spec.
2. Fix it in this one run, and change NOTHING else — every slide you do not
   have to touch must come out byte-identical. If the complaint names slides,
   those are the slides. If it does not, read the post and work out which
   slides it is actually about, then say which you chose and why. Fixing more
   than the complaint asks for is the failure here: a re-render that quietly
   rewrites a slide he was happy with costs him the version he liked.
3. Re-render each listed slide through the same compose helper, writing to
   drafts/{topic}/<NN>.jpg, and read each JPG back to confirm the complaint is
   actually fixed.
4. Keep every guard true: both body lines teach and neither is a verdict, the
   claim is a real feature of the product named, the background clears
   compose.copy_band_luma and does not repeat an adjacent vibe, night-desk
   vibes are hook-only, hooks only from tools/hook_pool.json and only ones
   hook_rules.eligible() returns.
5. Update the generator so a rebuild produces the fixed slides too.
""" + PUSH_RULE + """
Finish by printing: FIXED <what changed>
"""

REWORD_PROMPT = """Reword a post that worked, keeping the concept. Work in {repo}.

Source post: {source}
Its roster was: {source_roster}

Read ~/.claude/skills/tiktok-pipeline/examples.md for register first.

Keep the concept, the roster and the teaching points. Change the wording: a
different but eligible hook from tools/hook_pool.json covering the same idea
(a light rewording of the source's own hook is allowed and preferred, see
hook_rules.parent), and slide copy rephrased so it does not read as the same
post. Backgrounds may change; they must still pass every guard.

The hook decides the shape of the post: keep the same pillar as the source.
Call compose.preflight(topic, tools, bgs, pillar, hook=HOOK) before rendering.
Write tools/gen-<topic>.py, render six slides, read them back, and register
the post in tools/hooks.json.
""" + PUSH_RULE + """
Finish by printing: BUILT <topic>
"""

RESHOOT_PROMPT = """Re-shoot a post: identical words, different photographs.
Work in {repo}.

Source post: {source}

This is deliberately mechanical. Copy tools/gen-<source>.py to a generator for
the new topic and change NOTHING except the backgrounds and the topic slug.
Every hook line, title, body line, roster entry and caption must come out
byte-identical to the source.

Pick new backgrounds from the approved pool the same way tools/gen-daily-batch.py
does: skip hook-only vibes on non-hook slides, reject anything whose
compose.copy_band_luma exceeds compose.BAND_MAX_LUMA, no adjacent vibe repeats,
at most one background with a person, and none that assert_bg_fresh rejects.
Never generate or ingest a new image; the pool is fixed.

Because the hook is reused verbatim, call compose.mark_hook_used(HOOK, TOPIC)
so the cooldown counts it. Render six slides, read them back, and register the
post in tools/hooks.json with the same title and caption as the source.
""" + PUSH_RULE + """
Finish by printing: BUILT <topic>
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


# Agents rewrite the same shared JSON — hooks.json, hook_history.json,
# bg_history.json — with plain read-modify-write. Two at once silently lose
# one of the writes: a reshoot's registration vanished exactly this way. They
# also pick hooks and backgrounds from state the other has not written yet, so
# running them in parallel breaks the cooldowns as well as the bookkeeping.
_agent_gate = threading.Semaphore(1)
AGENT_LOGS = os.path.join(REPO, 'tools', '.agent-logs')


def _alive(pid):
    """True if pid is still one of our claude runs, not a recycled number."""
    try:
        os.kill(int(pid), 0)
    except (OSError, TypeError, ValueError):
        return False
    try:
        cmd = subprocess.run(['ps', '-p', str(int(pid)), '-o', 'command='],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return True                    # it answered kill(0); believe that
    return 'claude' in cmd


def _agent_log(kind, at):
    """Where one run's output goes, plus a prune so these do not pile up."""
    os.makedirs(AGENT_LOGS, exist_ok=True)
    try:
        old = sorted(os.path.join(AGENT_LOGS, f) for f in os.listdir(AGENT_LOGS)
                     if f.endswith('.log'))
        for f in old[:-60]:
            os.remove(f)
    except Exception:
        pass
    return os.path.join(AGENT_LOGS, '%s-%s.log' % (kind, str(at).replace('.', '_')))


def _read_log(path):
    try:
        with open(path, 'rb') as fh:
            return fh.read().decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def ensure_tag(topic):
    """Put the search tag on a caption that is missing it.

    Every post needs it and the agents mostly remember. Mostly is not a
    guarantee: a run that rendered six good slides died on the one word it
    forgot. Writing the word is cheaper than throwing the run away, so the
    guard below is now a backstop rather than the enforcement.
    """
    try:
        idx, raw = hooks_index()
    except Exception:
        return False
    rec = idx.get(topic)
    if not rec:
        return False
    cap = (rec.get('caption') or '').strip()
    if not cap or REQUIRED_TAG.lower() in cap.lower():
        return False
    rec['caption'] = cap + ' ' + REQUIRED_TAG
    with _lock:
        with open(HOOKS, 'w') as fh:
            json.dump(raw, fh, indent=1, ensure_ascii=False)
    return True


def _post_check(topic):
    """A build that rendered slides and skipped the caption is not done."""
    def check(out, good):
        if not good:
            return good, out
        built = re.search(r'BUILT\s+([a-z0-9][a-z0-9-]*)', out)
        name = built.group(1) if built else topic
        if name:
            ensure_tag(name)
        why = (unregistered(name) if name else '') or unpushed()
        if why:
            return False, ('Slides built, but %s: %s.\n\n%s'
                           % (name or 'the run', why, out[-900:]))
        return True, out
    return check


def _build_check(out, good):
    """Same, for a batch: any one post missing its caption fails the run."""
    if not good:
        return good, out
    made = set(re.findall(r'BUILT\s+([a-z0-9][a-z0-9-]*)', out))
    for t in made:
        ensure_tag(t)
    broken = [t for t in made if unregistered(t)]
    push = unpushed()
    if not (broken or push):
        return True, out
    why = []
    if broken:
        why.append('No caption on: ' + ', '.join(sorted(broken))
                   + '. They cannot be delivered until hooks.json has one.')
    if push:
        why.append(push.capitalize() + '.')
    return False, ' '.join(why) + '\n\n' + out[-900:]


# The hooks Thinh calibrated as good on 2026-08-25, which live in the skill as
# prose examples and nowhere the UI can reach. Offered as suggestions minus
# anything already pooled: writing a hook from a blank box is the hardest part
# of a post, and his own approved register is the right thing to start from.
CALIBRATED = [
    ('tools', 'the 5 apps i would keep', 'if i had to delete everything'),
    ('tools', 'i pay for 12 apps', 'these 5 do all the work'),
    ('tools', 'the tools i use to do', 'a full day of work by noon'),
    ('tools', '5 apps i wish someone', 'showed me at 17'),
    ('screentime', 'i cut 3 hours of screen time', 'without deleting one app'),
    ('screentime', 'my phone is boring now', 'and it changed everything'),
    ('screentime', 'how i stopped picking up my phone', 'the second i wake up'),
    ('screentime', '47 minutes a day', 'this is the whole system'),
    ('discipline', 'this is how you lock in', "when you don't feel like it"),
    ('discipline', 'discipline is a schedule', 'not a personality'),
    ('discipline', 'how i stopped needing', 'motivation to start'),
    ('discipline', 'the 4 hours', 'that decide your whole day'),
    ('build', 'how i ship in a weekend', 'what used to take a month'),
    ('build', 'everything i run', 'my business on at 19'),
    ('build', 'one person, no team', 'this is the setup'),
    ('build', "give me seven days", "and i'd build it like this"),
    ('learn', 'how i study 4 hours', 'without touching my phone'),
    ('learn', 'the study setup that got me', 'through exam season'),
    ('learn', 'i stopped rereading notes', 'and my grades moved'),
    ('learn', '4 study apps', 'that actually did something'),
]


def hook_suggestions():
    """Calibrated hooks that are not in the pool yet."""
    # hook_rules.parent already decides when two hooks are the same hook —
    # it is what compose uses to accept a rewording. Reusing it means the
    # gallery cannot drift from the rule it is meant to reflect, and a
    # differently-broken or slightly reworded line does not come back as new.
    return [{'lines': [a, b], 'pillar': pillar} for pillar, a, b in CALIBRATED
            if hook_rules.parent([a, b]) is None]


_users_cache = {'at': 0, 'days': 0, 'data': None}


def _https():
    """A verifying SSL context that works on a python.org framework build.

    Those builds do not read the system keychain, so urlopen fails every
    HTTPS call with CERTIFICATE_VERIFY_FAILED until someone runs Install
    Certificates.command. certifi is already a dependency of the pipeline;
    if it is missing the default context still verifies, it just may not
    find a root here.
    """
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _metrics(path, payload=None, write=False, timeout=40):
    """Talk to the metrics worker. Returns the parsed body or an {'error'}."""
    if not METRICS_URL:
        return {'error': 'ARCO_METRICS_URL is not set'}
    key = METRICS_WRITE if write else METRICS_KEY
    if not key:
        return {'error': 'no %s key configured' % ('write' if write else 'read')}
    url = '%s%s%sk=%s' % (METRICS_URL, path, '&' if '?' in path else '?',
                          urllib.parse.quote(key))
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'arco-dashboard/1',
        'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_https()) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        try:
            return json.load(exc)
        except Exception:
            return {'error': 'HTTP %s' % exc.code}
    except Exception as exc:
        return {'error': str(exc)}


def ig_slide_urls(topic):
    """Public URLs for a topic's 4:5 crops, or [] if they have not been made."""
    d = os.path.join(DRAFTS, topic, 'ig')
    if not os.path.isdir(d):
        return []
    files = sorted(f for f in os.listdir(d) if re.match(r'^\d+\.jpg$', f))
    return ['%s/%s/ig/%s' % (PAGES.rstrip('/'), topic, f) for f in files]


# Instagram captions are shorter than TikTok's. A TikTok caption carries a
# teaching line per tool because the search index reads it; on Instagram that
# is a wall of text under a picture and the slides already say all of it.
def ig_caption(topic):
    """One sentence saying what the post is, plus its hashtags.

    The title is that sentence and already exists on every post — "5 tools
    that replace a whole team", "the 5 apps i would keep if i deleted
    everything else". Truncating the TikTok caption instead was unreliable:
    its opening sentence is usually the hook but sometimes a tool detail,
    so `saved-hours` would have led with a line about Perplexity rather
    than anything describing the post.

    #creatorsearchinsights is TikTok's search programme and does nothing
    here, so it comes off with the rest.
    """
    idx, _ = hooks_index()
    rec = idx.get(topic) or {}
    cap = rec.get('caption') or ''
    tags = [t for t in re.findall(r'#\w+', cap)
            if t.lower() != '#creatorsearchinsights']
    line = (rec.get('title') or '').strip()
    if not line:
        # No title: fall back to the caption's first sentence rather than
        # posting nothing.
        body = re.sub(r'#\w+', '', cap).strip()
        line = re.split(r'(?<=\.)\s', body)[0].strip() if body else ''
    if not line:
        return ''
    line = line.rstrip(' .') + '.'
    return (line + ('\n\n' + ' '.join(tags) if tags else '')).strip()


def ig_blocked(topic):
    """Why this post cannot go to Instagram, or '' if it can.

    Deliberately NOT unregistered(): that guard requires the TikTok search
    tag, which this platform strips anyway — so reusing it rejected posts
    for missing a hashtag that would never have been sent.
    """
    if not ig_caption(topic):
        return 'no caption in hooks.json, so there is nothing to post with'
    if not ig_slide_urls(topic):
        return 'no 4:5 crops yet'
    return ''


def ig_prepare_many(topics):
    """Crop everything that needs it, then commit and push once.

    ig_prepare does a commit and a push per topic. Filling a week means
    about seventeen of them, which is seventeen Pages builds queued behind
    each other and minutes of waiting for something git can do in one go.
    """
    made, failed = [], {}
    for t in topics:
        if ig_slide_urls(t):
            continue
        r = subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'variants.py'),
                            t, '--ig'], cwd=os.path.join(REPO, 'tools'),
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            failed[t] = (r.stderr or r.stdout).strip()[-160:]
        else:
            made.append(t)

    def git(*a):
        return subprocess.run(('git',) + a, cwd=REPO, capture_output=True,
                              text=True, timeout=600)
    pushed = False
    if made:
        for t in made:
            git('add', os.path.join('drafts', t, 'ig'))
        if git('diff', '--cached', '--name-only').stdout.strip():
            c = git('commit', '-m',
                    '4:5 crops for %d post%s, so Instagram can fetch them'
                    % (len(made), '' if len(made) == 1 else 's'))
            if c.returncode != 0:
                return {'error': (c.stdout + c.stderr).strip()[-200:]}
        pu = git('push', 'origin', 'HEAD')
        if pu.returncode != 0:
            return {'error': 'push failed: ' + (pu.stdout + pu.stderr).strip()[-200:]}
        pushed = True
    return {'ok': True, 'cropped': made, 'failed': failed, 'pushed': pushed}


def ig_prepare(topic):
    """Crop, commit and push, so Instagram can fetch the slides.

    The Worker cannot crop and cannot read this disk, so this is the one part
    of scheduling that has to happen here. It pushes because Instagram pulls
    the images from Pages — a post whose slides are only on this laptop
    cannot be published by anything.
    """
    out = []
    r = subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'variants.py'),
                        topic, '--ig'], cwd=os.path.join(REPO, 'tools'),
                       capture_output=True, text=True, timeout=300)
    out.append((r.stdout or r.stderr).strip()[-200:])
    if r.returncode != 0:
        return {'error': out[-1] or 'variants.py failed'}

    def git(*a):
        return subprocess.run(('git',) + a, cwd=REPO, capture_output=True,
                              text=True, timeout=300)
    git('add', os.path.join('drafts', topic, 'ig'))
    st = git('diff', '--cached', '--name-only').stdout.strip()
    if st:
        c = git('commit', '-m', '4:5 crops for %s, so Instagram can fetch them' % topic)
        if c.returncode != 0:
            return {'error': (c.stdout + c.stderr).strip()[-200:]}
    p = git('push', 'origin', 'HEAD')
    if p.returncode != 0:
        return {'error': 'push failed: ' + (p.stdout + p.stderr).strip()[-200:]}
    return {'ok': True, 'urls': ig_slide_urls(topic), 'log': ' / '.join(out)}


def ig_serving(urls):
    """Which of these are actually live on Pages. Pages lags a push."""
    live = 0
    for u in urls:
        try:
            req = urllib.request.Request(u, method='HEAD',
                                         headers={'User-Agent': 'arco-dashboard/1'})
            with urllib.request.urlopen(req, timeout=15, context=_https()) as r:
                live += 1 if r.status == 200 else 0
        except Exception:
            pass
    return live


def user_summary(days=30):
    """What the app's own users are doing, from the metrics worker.

    Read through a short cache: the numbers move once a day per install, so
    hitting the worker on every page load would be a request per refresh for
    data that cannot have changed.
    """
    if not METRICS_URL or not METRICS_KEY:
        return {'off': True, 'why': 'Set ARCO_METRICS_URL and ARCO_METRICS_KEY '
                                   'to the deployed metrics worker.'}
    now = time.time()
    if (_users_cache['data'] and _users_cache['days'] == days
            and now - _users_cache['at'] < 600):
        return dict(_users_cache['data'], cached=True)
    url = '%s/summary?days=%d&k=%s' % (METRICS_URL, days,
                                       urllib.parse.quote(METRICS_KEY))
    # Cloudflare turns away the default Python-urllib agent with its own 403
    # (error 1010, a browser-signature block), which reads exactly like a bad
    # read key and is not one.
    req = urllib.request.Request(url, headers={'User-Agent': 'arco-dashboard/1'})
    try:
        with urllib.request.urlopen(req, timeout=25, context=_https()) as r:
            data = json.load(r)
    except Exception as exc:
        # A stale answer beats an empty screen; the worker being unreachable
        # is a fact about the worker, not about the app's users.
        if _users_cache['data']:
            return dict(_users_cache['data'], stale=True, why=str(exc))
        return {'error': str(exc)}
    _users_cache.update({'at': now, 'days': days, 'data': data})
    return data


def bg_catalog():
    """The background pool as the gallery needs to see it.

    Facts come from three places that nothing else joins up: .index.json for
    what the photo is (vibe, person, luma), bg/hook_usage.json for whether it
    has already opened a post, and bg_history.json for what the last post
    used. Picking well needs all three at once — a beautiful frame you used
    yesterday is the wrong pick, and the UI could not tell you that before.
    """
    try:
        with open(BG_INDEX) as fh:
            idx = json.load(fh)
    except Exception:
        return {'bgs': [], 'stale': True,
                'why': 'no background index yet — run tools/bg_index.py'}
    hook_used = set(load(os.path.join(BG_DIR, 'hook_usage.json'), []) or [])
    hist = load(os.path.join(REPO, 'tools', 'bg_history.json'), []) or []
    recent = set()
    for entry in hist[-BG_COOLDOWN_POSTS:]:
        recent.update(entry.get('bgs') or [])
    for b in idx['bgs']:
        b['hook_used'] = b['name'] in hook_used
        b['recent'] = b['name'] in recent
    on_disk = set(f for f in os.listdir(BG_DIR) if f.endswith('.jpg'))
    known = set(b['name'] for b in idx['bgs'])
    idx['bgs'] = [b for b in idx['bgs'] if b['name'] in on_disk]
    idx['missing'] = sorted(on_disk - known)
    # A photo he dropped into the pool since the last index has no luma and no
    # vibe, so the gallery cannot say whether it holds copy. Measure it in the
    # background rather than making him remember to run a script.
    if idx['missing']:
        threading.Thread(target=reindex_bgs, daemon=True).start()
    idx['hook_left'] = len([b for b in idx['bgs'] if not b['hook_used']])
    return idx


_reindexing = threading.Lock()


def reindex_bgs():
    if not _reindexing.acquire(blocking=False):
        return
    try:
        subprocess.run([sys.executable,
                        os.path.join(REPO, 'tools', 'bg_index.py')],
                       cwd=os.path.join(REPO, 'tools'), timeout=900,
                       capture_output=True)
    except Exception as exc:
        print('[bg] reindex failed: %s' % exc, flush=True)
    finally:
        _reindexing.release()


# One post, matching compose.BG_COOLDOWN: a photo may come back, it just must
# not appear in the very next post.
BG_COOLDOWN_POSTS = 1
THUMB_W = 260


def bg_thumb(name):
    """A gallery-sized copy of one background, made once and kept.

    The pool is 51MB. Eighty-three of those over a phone connection is not a
    gallery, it is a download, so the grid gets 260px copies. PIL is the
    pipeline's dependency, not the dashboard's, so if it is somehow absent
    the full frame is served rather than nothing.
    """
    src = os.path.join(BG_DIR, os.path.basename(name))
    if not os.path.isfile(src):
        return None, None
    dst = os.path.join(BG_THUMBS, os.path.basename(name))
    if (os.path.isfile(dst)
            and os.path.getmtime(dst) >= os.path.getmtime(src)):
        with open(dst, 'rb') as fh:
            return fh.read(), 'image/jpeg'
    try:
        from PIL import Image
        os.makedirs(BG_THUMBS, exist_ok=True)
        im = Image.open(src).convert('RGB')
        im.thumbnail((THUMB_W, THUMB_W * 4), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=78, optimize=True)
        with open(dst, 'rb') as fh:
            return fh.read(), 'image/jpeg'
    except Exception:
        with open(src, 'rb') as fh:
            return fh.read(), 'image/jpeg'


# Tools that answer a different reader. The pool is a menu, not a target.
OFF_LANE = {'seller'}
LLM_NAMES = {'Claude', 'Codex', 'ChatGPT', 'Gemini', 'Perplexity', 'Manus',
             'Antigravity', 'Cursor', 'Copilot', 'Grok', 'DeepSeek', 'v0',
             'Lovable'}


def _recent_bgs():
    """What the last post used. A photo may come back, just not next."""
    hist = load(os.path.join(REPO, 'tools', 'bg_history.json'), []) or []
    return set(hist[-1].get('bgs') or []) if hist else set()


def _tool_rank():
    """Every pooled tool with how long ago it last appeared.

    Reusing a tool is fine — the audience is not reading every post and a
    stack that changes completely each time reads as invented. What this
    buys is rotation: the one that has been rested longest comes up first,
    so an autofilled roster is not the same five names every time.
    """
    hist = load(os.path.join(REPO, 'tools', 'tool_usage.json'), []) or []
    last = {}
    for i, entry in enumerate(hist):
        for t in entry.get('tools') or []:
            last[t] = i
    return last, set(hist[-1].get('tools') or []) if hist else set()


def autofill_bgs(slides, only=None):
    """Choose the photos the way a build would, and say nothing about copy.

    Every rule here is one compose enforces at render time: the hook gets a
    frame nothing has opened with, body slides get one that holds five lines
    of white text, no two neighbours share a vibe, at most one person in the
    post, and nothing the last post used. Doing it here rather than in the
    agent makes it instant and free — the picking was never the judgment
    call, the words are.
    """
    cat = bg_catalog()
    pool = cat.get('bgs') or []
    if not pool:
        return slides
    recent = _recent_bgs()
    keep = {i: sl.get('bg') for i, sl in enumerate(slides)
            if sl.get('bg') and only is not None and i != only}
    people = sum(1 for b in keep.values() if (next((x for x in pool if x['name'] == b), {}) or {}).get('person'))
    out = []
    for i, sl in enumerate(slides):
        if i in keep:
            out.append(keep[i])
            continue
        taken = set(x for x in out if x) | set(keep.values())
        prev = out[-1] if out else None
        nxt = keep.get(i + 1)
        def vibe(n):
            return (next((x for x in pool if x['name'] == n), {}) or {}).get('vibe')
        cands = [b for b in pool
                 if b['name'] not in taken
                 and b['name'] not in recent
                 and b['vibe'] != vibe(prev) and b['vibe'] != vibe(nxt)
                 and (people < 1 or not b['person'])]
        if i == 0:
            # The first slide decides the scroll, so it must never look
            # familiar: a frame nothing has opened with, and by preference a
            # night desk, which is the note that slide wants and is barred
            # from every other slide anyway.
            fresh = [b for b in cands if not b['hook_used']] or cands
            best = [b for b in fresh if b['hook_only']] or fresh
        else:
            best = [b for b in cands if b['copy_ok'] and not b['hook_only']]
        if not best:
            best = cands or [b for b in pool if b['name'] not in taken]
        if not best:
            out.append(None)
            continue
        pick = random.choice(best)
        if pick['person']:
            people += 1
        out.append(pick['name'])
    return out


# Which readers each pillar is actually talking to. Rest time alone put a
# background remover and a video generator in a post about productivity: both
# were simply the tools rested longest. A roster has to answer the hook too.
PILLAR_AUDIENCE = {
    'tools': ('focus', 'build', 'any', 'content'),
    'build': ('build', 'any', 'focus'),
    'learn': ('focus', 'any', 'content'),
    'discipline': ('focus', 'any'),
    'screentime': ('focus', 'any'),
}


def autofill_roster(slides, pillar='tools'):
    """ARCO first, exactly one model, then what fits the pillar and is rested."""
    pool = load(os.path.join(REPO, 'tools', 'tool_pool.json'), {})
    aud = pool.get('audience', {})
    names = []
    for cat, items in pool.items():
        if cat.startswith('_') or cat in ('icons', 'audience') or not isinstance(items, list):
            continue
        names += items
    names = [n for n in dict.fromkeys(names)
             if aud.get(n) not in OFF_LANE and n in aud and n != 'ARCO']
    last, in_last = _tool_rank()
    want = PILLAR_AUDIENCE.get(pillar, PILLAR_AUDIENCE['tools'])
    def fit(n):
        tag = aud.get(n)
        return want.index(tag) if tag in want else len(want)
    # Fit to the pillar first, then rested longest — and shuffled inside each
    # band, because strict ordering gave the same four names every time,
    # which is the opposite of what rotation is for.
    rested = sorted(names, key=lambda n: (fit(n), n in in_last, last.get(n, -1), n))
    head, tail = rested[:14], rested[14:]
    random.shuffle(head)
    rested = head + tail
    slots = [i for i, sl in enumerate(slides) if sl.get('kind') == 'tool']
    out = dict((i, slides[i].get('tool')) for i in slots if slides[i].get('tool'))
    if slots and not out.get(slots[0]):
        out[slots[0]] = 'ARCO'
    have = set(out.values())
    # Exactly one model, never zero: zero reads as a post that skipped the
    # thing everyone is actually curious about.
    if not (have & LLM_NAMES):
        # Rotate which model appears rather than always the same one: the
        # rested half of them, picked at random.
        llms = [n for n in rested if n in LLM_NAMES]
        llm = random.choice(llms[:max(1, len(llms) // 2)]) if llms else None
        empty = [i for i in slots if not out.get(i)]
        if llm and empty:
            out[empty[0]] = llm
            have.add(llm)
    for i in slots:
        if out.get(i):
            continue
        pick = next((n for n in rested
                     if n not in have and n not in LLM_NAMES), None)
        if not pick:
            break
        out[i] = pick
        have.add(pick)
    return out


def autofill(pillar, slides, only='all'):
    """Fill in everything that is still blank, or re-roll what was asked."""
    slides = [dict(sl) for sl in slides]
    if only in ('all', 'bgs') or isinstance(only, int):
        bgs = autofill_bgs(slides, None if only in ('all', 'bgs') else only)
        for sl, b in zip(slides, bgs):
            if only == 'all' and sl.get('bg'):
                continue
            sl['bg'] = b
    if only in ('all', 'tools') and any(sl.get('kind') == 'tool' for sl in slides):
        for i, t in autofill_roster(slides, pillar).items():
            slides[i]['tool'] = t
            if not slides[i].get('title'):
                slides[i]['title'] = t
    hook = None
    if only == 'all' or only == 'hook':
        first = slides[0] if slides else {}
        if not [l for l in (first.get('lines') or []) if str(l).strip()]:
            el = hook_rules.eligible(pillar=pillar)
            if el:
                pick = random.choice(el)
                hook = {'lines': pick['lines'], 'pillar': pillar}
                slides[0]['lines'] = list(pick['lines'])
    return {'slides': slides, 'hook': hook}


def spec_bgs(spec):
    """The chosen backgrounds in slide order, skipping slides left open."""
    return [sl['bg'] for sl in ((spec or {}).get('slides') or []) if sl.get('bg')]


def bg_problems(bgs):
    """The same rules compose enforces, said early instead of at render time.

    These all used to surface as a SystemExit an agent hit ten minutes into a
    build. Checking them while you are still choosing is the whole point of
    having a gallery.
    """
    try:
        with open(BG_INDEX) as fh:
            by = {b['name']: b for b in json.load(fh)['bgs']}
    except Exception:
        return []
    out = []
    people = [b for b in bgs if (by.get(b) or {}).get('person')]
    if len(people) > 1:
        out.append('%d backgrounds have a person in them (%s). One per post, '
                   'or the carousel reads as stock photography.'
                   % (len(people), ', '.join(people)))
    for i, b in enumerate(bgs):
        info = by.get(b) or {}
        if i > 0 and info.get('hook_only'):
            out.append('slide %d: %s is a %s — those are hook-only, they are '
                       'too busy to hold body copy.' % (i + 1, b, info.get('vibe')))
        if i > 0 and info.get('luma') is not None and not info.get('copy_ok'):
            out.append('slide %d: %s is too bright behind the copy (luma %s, '
                       'limit %d).' % (i + 1, b, info['luma'], 70))
    for i, (a, b) in enumerate(zip(bgs, bgs[1:])):
        va, vb = (by.get(a) or {}).get('vibe'), (by.get(b) or {}).get('vibe')
        if va and va == vb:
            out.append('slides %d and %d are both %s — the eye needs a change '
                       'of scene between cards.' % (i + 1, i + 2, va))
    return out


def unpushed():
    """'' if HEAD is on the remote, else why the slides are not on Pages.

    Every build commits and pushes, because TikTok pulls the images from
    GitHub Pages. On this host the push was failing and the agents were
    reporting success anyway: eight builds sat unpushed while their posts
    looked finished. Delivery would have caught it much later, as a URL
    preflight failure that reads like a TikTok problem.
    """
    def git(*a):
        return subprocess.run(('git',) + a, cwd=REPO, capture_output=True,
                              text=True, timeout=120)
    try:
        git('fetch', '--quiet', 'origin')
        head = git('rev-parse', 'HEAD').stdout.strip()
        merged = git('branch', '-r', '--contains', head).stdout
        if 'origin/main' in merged:
            return ''
        ahead = git('rev-list', '--count', 'origin/main..HEAD').stdout.strip()
        return ('%s commit(s) are not on origin, so GitHub Pages is not '
                'serving these slides yet' % (ahead or '?'))
    except Exception as exc:
        return 'could not check the push: %s' % exc


def unregistered(topic):
    """Why this post cannot be delivered, or '' if it can.

    The prompts have always asked for a hooks.json entry and the agents have
    always mostly written one. Mostly is not a guarantee: three posts built
    this week have no caption, so autopost has nothing to send. Asking in
    prose was never going to hold — the rule has to be checked.
    """
    idx, _ = hooks_index()
    rec = idx.get(topic)
    if not rec:
        return 'not registered in hooks.json, so it has no caption to post with'
    cap = (rec.get('caption') or '').strip()
    if not cap:
        return 'registered with an empty caption'
    # The search tag is how a post reaches people looking for something rather
    # than only the feed. Asked for in the skill, checked here, because prose
    # has not been enough in this pipeline before.
    if REQUIRED_TAG.lower() not in cap.lower():
        return 'its caption is missing %s' % REQUIRED_TAG
    return ''


def _agent(prompt, mark, ok_token, topic=None, kind='run', job=None, check=None):
    """Start a headless Claude that outlives this process, then wait on it.

    This used to be a plain subprocess.run, which made the agent a child of
    the dashboard: restarting the dashboard — a deploy, a crash, launchd —
    killed whatever was mid-run, and three good runs were thrown away that
    way in one night. The run is now detached into its own session with its
    output going to a file, so a restart only loses the thread that was
    watching it. reconcile_queues finds the pid again and picks it back up.
    """
    at = (job or {}).get('at') or time.time()
    prior = (job or {}).get('status') == 'running'
    # Left behind by an earlier dashboard and still going: wait, do not
    # start a second one against the same files.
    if prior and _alive(job.get('pid')):
        out_path = job.get('out') or _agent_log(kind, at)
        with _agent_gate:
            print('[adopt] %s %s still running as pid %s'
                  % (kind, at, job.get('pid')), flush=True)
            return _wait_agent(job['pid'], out_path, mark, ok_token, topic,
                               check, (job.get('started') or time.time()) + 3600)
    # It finished while we were down. The log holds the whole answer.
    if prior and job.get('out') and os.path.exists(job['out']):
        out = _read_log(job['out'])
        if out:
            print('[adopt] %s %s finished while we were down' % (kind, at), flush=True)
            return _settle(out, mark, ok_token, check)
    mark(status='queued')
    with _agent_gate:
        out_path = _agent_log(kind, at)
        try:
            with open(out_path, 'wb') as fh:
                p = subprocess.Popen(['claude', '-p', prompt], cwd=REPO,
                                     stdout=fh, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL,
                                     start_new_session=True)
        except FileNotFoundError:
            return mark(status='failed', log='claude CLI not found on PATH')
        except Exception as exc:
            return mark(status='failed', log=str(exc))
        mark(status='running', started=time.time(), pid=p.pid, out=out_path)
        _wait_agent(p.pid, out_path, mark, ok_token, topic, check,
                    time.time() + 3600)


def _settle(out, mark, ok_token, check):
    good = ok_token in out
    if check:
        good, out = check(out, good)
    mark(status='done' if good else 'failed', done=good,
         log=out[-1200:] or 'no output', finished=time.time())


def _wait_agent(pid, out_path, mark, ok_token, topic, check, deadline):
    """Poll until the detached run exits, then read its log and score it.

    Polling rather than wait(), because after a restart the process is no
    longer our child and waitpid would refuse it.
    """
    while _alive(pid):
        if time.time() > deadline:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except Exception:
                pass
            return mark(status='failed', log='timed out after an hour',
                        finished=time.time())
        time.sleep(2)
    _settle(_read_log(out_path), mark, ok_token, check)


def run_redo(job):
    def mark(**kw):
        with _lock:
            q = redo_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            with open(REDO, 'w') as fh:
                json.dump(q, fh, indent=1, ensure_ascii=False)
    slides = job.get('slides') or ([job['slide']] if job.get('slide') else [])
    _agent(REDO_PROMPT.format(
        repo=REPO, topic=job['topic'], note=job['note'],
        slides=('Slides to fix: '
                + ', '.join('%02d.jpg (number %d)' % (n, n) for n in slides))
               if slides else
               'He did not pick slides, so decide from the complaint alone.'),
        mark, 'FIXED', kind='redo', job=job)


def run_replicate(job):
    def mark(**kw):
        with _lock:
            q = replicate_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            with open(REPLICATE, 'w') as fh:
                json.dump(q, fh, indent=1, ensure_ascii=False)
        # The agent signs off with "BUILT <topic>", which is the only place the
        # new topic's name exists. Without capturing it here nothing ever links
        # the copy back to what it came from.
        if kw.get('status') == 'done' and kw.get('log'):
            m = re.search(r'BUILT\s+([a-z0-9][a-z0-9-]*)', kw['log'])
            if m:
                with _lock:
                    st = load(STATUS, {})
                    st.setdefault(m.group(1), {}).update({
                        'from_replicate': job['from'],
                        'replicate_mode': job.get('mode') or 'new'})
                    with open(STATUS, 'w') as fh:
                        json.dump(st, fh, indent=1, ensure_ascii=False)
    # Three ways to reuse a post that worked, and they are genuinely different
    # jobs: reword keeps the concept, reshoot keeps the words, new-take keeps
    # only the shape.
    mode = job.get('mode') or 'new'
    if mode == 'reword':
        prompt = REWORD_PROMPT.format(repo=REPO, source=job['from'],
                                      source_roster=', '.join(job['source_roster']))
    elif mode == 'reshoot':
        prompt = RESHOOT_PROMPT.format(repo=REPO, source=job['from'])
    else:
        prompt = REPLICATE_PROMPT.format(
            repo=REPO, source=job['from'],
            source_roster=', '.join(job['source_roster']),
            suggested=', '.join(job['suggested_roster']))
    _agent(prompt, mark, 'BUILT', topic=job.get('topic'),
           kind='replicate', job=job, check=_post_check(job.get('topic')))


def run_build(job):
    """Actually build the posts by handing the job to a headless Claude run.

    Writing a post is judgment, not a transform: hooks, rosters and teaching
    points all need choices. So the button starts an agent rather than
    templating something. It is scoped to writing into drafts/ and hooks.json,
    and explicitly forbidden from committing or delivering.
    """
    note = ('Thinh asked for: ' + job['note'] + '\n') if job.get('note') else ''
    brief = spec_brief(job.get('spec'))
    prompt = BUILD_PROMPT.format(count=job['count'], pillar=job.get('pillar', 'tools'),
                                 repo=REPO, note=brief + note)

    def mark(**kw):
        with _lock:
            q = build_queue()
            for x in q:
                if x['at'] == job['at']:
                    x.update(kw)
            save_builds(q)

    _agent(prompt, mark, 'BUILT', kind='build', job=job, check=_build_check)


INBOX_SEEN = os.path.join(REPO, 'tools', 'inbox_seen.json')


def inbox_items():
    """Everything waiting on a decision, in one list.

    Each of these already existed somewhere — a panel on Act, a colour on a
    card, a line in a log — which meant noticing them was a matter of being on
    the right tab at the right time. A delivery that failed on one account sat
    unnoticed for two days that way.

    Only things that end in an action belong here. "Views went up" is not a
    notification; "this post never reached an account" is.
    """
    out = []
    now = time.time()
    log = delivery_log()
    stats = load(STATS, {})
    idx, _ = hooks_index()
    label = {a['key']: a['short'] for a in ACCOUNTS}

    def add(kind, sev, title, detail, topic=None, at=None):
        out.append({'id': '%s:%s:%s' % (kind, topic or '', title[:40]),
                    'kind': kind, 'sev': sev, 'title': title,
                    'detail': detail, 'topic': topic, 'at': at or now})

    # A send that failed. The slides are fine; TikTok did not fetch them.
    for topic, per in log.items():
        for k, r in (per or {}).items():
            if r.get('status') == 'FAILED':
                add('delivery', 'bad', '%s never reached %s' % (topic, label.get(k, k)),
                    str(r.get('detail') or '')[:120] + ' — draft it again',
                    topic, r.get('at'))

    # Live on some accounts and not others, with nothing recorded at all.
    for g in _undelivered():
        gaps = [label.get(x, x) for x in (g['failed'] + g['missing'])]
        if not g['failed']:
            add('gap', 'warn', '%s is missing from %s' % (g['topic'], ', '.join(gaps)),
                'Nothing was ever sent there, so it ran on fewer accounts than it looks.',
                g['topic'], g.get('at'))

    # A draft nobody published is a slot nobody can use.
    for d in _stale_drafts():
        add('stale', 'warn', '%s has been waiting %dh on %s'
            % (d['topic'], d['hours'], label.get(d['account'], d['account'])),
            'Publish it in TikTok, or the slot stays spent — deleting does not free one.',
            d['topic'])

    # No caption means it cannot be sent at all.
    for topic in idx:
        if os.path.isdir(os.path.join(DRAFTS, topic)):
            why = unregistered(topic)
            if why and not any((r or {}).get('status') for r in (log.get(topic) or {}).values()):
                add('caption', 'warn', '%s cannot be drafted' % topic, why.capitalize(), topic)

    # Accounts with no room left.
    for k, used in (pending_counts() or {}).items():
        if used >= 5:
            add('slots', 'bad', '%s has no draft slots left' % label.get(k, k),
                'Five pending is the cap. Only publishing frees one.', None)

    # Slides that are not on Pages cannot be pulled by TikTok.
    push = unpushed()
    if push:
        add('push', 'bad', 'Slides are not on GitHub yet', push.capitalize() + '.', None)

    # Nothing left to build with.
    if not hooks_available():
        add('hooks', 'warn', 'No hooks are free',
            'Every approved hook is inside its cooldown. Add new ones, or wait.', None)

    seen = set(load(INBOX_SEEN, []))
    for x in out:
        x['read'] = x['id'] in seen
    out.sort(key=lambda x: (x['read'], {'bad': 0, 'warn': 1}.get(x['sev'], 2), -(x['at'] or 0)))
    return out


def hooks_available():
    """Approved hooks eligible right now. Hooks are not burn-once: one sits
    out a cooldown and comes back, so this number recovers on its own. It is
    still the ceiling on how many posts can be built in one go."""
    return len(hook_rules.eligible())


def schedules():
    return load(SCHEDULE, [])


def save_schedules(sc):
    with open(SCHEDULE, 'w') as fh:
        json.dump(sc, fh, indent=1)


def settle_orphans():
    """Finish rows whose agent is gone but whose watcher never noticed.

    reconcile_queues only runs at startup. A run whose watching thread died
    with a restart, and whose process then exited while the server stayed
    up, has nobody left to mark it done — so it reads as running forever and
    the job panel shows a spinner for work that finished an hour ago. This
    is the same settle the watcher would have done, on a slow beat.
    """
    for path, load_, save_ in ((BUILD, build_queue, save_builds),
                               (REDO, redo_queue, None),
                               (REPLICATE, replicate_queue, None),
                               (GEN, gen_queue, save_gen)):
        q, dirty = load_(), False
        for x in q:
            if x.get('status') != 'running' or _alive(x.get('pid')):
                continue
            out = _read_log(x.get('out') or '')
            token = {'build': 'BUILT', 'gen': 'DONE'}.get(x.get('what') and 'gen'
                                                          or ('build' if path == BUILD else ''), '')
            if out:
                x['status'] = 'done' if (token and token in out) or 'BUILT' in out or 'DONE' in out \
                              else 'failed'
                x['done'] = x['status'] == 'done'
                x['log'] = out[-1200:]
            else:
                x['status'] = 'interrupted'
                x['log'] = 'the run ended and nothing was watching it'
            x['finished'] = time.time()
            dirty = True
            print('[sweep] settled %s as %s' % (x.get('topic') or x.get('from')
                                                or x.get('what') or 'a build', x['status']),
                  flush=True)
        if dirty:
            if save_:
                save_(q)
            else:
                with open(path, 'w') as fh:
                    json.dump(q, fh, indent=1, ensure_ascii=False)


def reconcile_queues():
    """Sort out jobs left behind by a previous server.

    Two different cases, and treating them the same threw work away: a
    'running' job has an orphaned subprocess nobody is waiting on, so it is
    closed. A 'queued' job never started at all — its work is still owed, so
    it is picked back up. Agents are serialised, so a queue of eight can sit
    waiting for a long time and a restart used to delete all of it.
    """
    closed, resumed = 0, 0
    # Builds belong here too. Leaving them out meant a queued build sat
    # forever after a restart with nothing to start it.
    for path, load, runner, save in (
            (REDO, redo_queue, run_redo, None),
            (REPLICATE, replicate_queue, run_replicate, None),
            (BUILD, build_queue, run_build, save_builds),
            (GEN, gen_queue, run_gen, save_gen)):
        q = load()
        pending = []
        for x in q:
            if x.get('status') == 'running':
                # Still alive, or it left a log behind: hand it back to the
                # runner, which waits on the pid rather than starting again.
                if _alive(x.get('pid')) or (x.get('out') and os.path.exists(x['out'])):
                    pending.append((x, runner))
                else:
                    x['status'] = 'interrupted'
                    x['log'] = 'the server restarted while this was running'
                    closed += 1
            elif x.get('status') == 'queued':
                pending.append((x, runner))
        if closed or pending:
            if save:
                save(q)
            else:
                with open(path, 'w') as fh:
                    json.dump(q, fh, indent=1, ensure_ascii=False)
        for job, fn in pending:
            threading.Thread(target=fn, args=(job,), daemon=True).start()
            resumed += 1
    if closed or resumed:
        print('[startup] closed %d orphaned, resumed %d queued'
              % (closed, resumed), flush=True)


_last_sync = [0.0]


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
            # A finished run with no watcher left reads as running forever.
            try:
                settle_orphans()
            except Exception as exc:
                print('[sweep] failed: %s' % exc, flush=True)
            # Reconcile with TikTok on a slow beat. It is an HTTPS call, not an
            # agent, so it costs nothing but a token refresh.
            if now - _last_sync[0] > SYNC_EVERY:
                _last_sync[0] = now
                try:
                    sync_all()
                except Exception as exc:
                    print('[sync] failed: %s' % exc, flush=True)
            due = [x for x in schedules() if not x.get('done') and x['at'] <= now]
            for job in due:
                accts = job.get('accounts') or [a['key'] for a in ACCOUNTS]
                gap = int(job.get('stagger_min') or 0) * 60
                results = {}
                direct = job.get('mode') == 'direct'
                for i, key in enumerate(accts):
                    if i and gap:
                        time.sleep(gap)
                    if not direct:
                        results.update(run_draft(job['topic'], [key]))
                        continue
                    # The settings were chosen when the job was made, which may
                    # be days ago. A privacy level the creator has since given
                    # up would be refused by TikTok anyway; failing here says
                    # why instead of leaving a bare API error in the log.
                    st = job.get('settings') or {}
                    why = direct_blocked(key, st)
                    if why:
                        results[key] = {'status': 'FAILED', 'detail': why,
                                        'at': time.time()}
                        print(f'[schedule] {job["topic"]} -> {key}: {why}', flush=True)
                        continue
                    results[key] = run_publish(job['topic'], key, st)
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


def queue_redo(topic, slides, note):
    """Record the slides Thinh wants redone, with his reason.

    Takes a list: three bad slides used to mean three separate agent runs,
    each re-reading the repo from scratch. One run fixes them together.
    """
    slides = sorted({int(n) for n in slides})
    with _lock:
        q = redo_queue()
        q = [x for x in q
             if not (x['topic'] == topic and not x.get('done')
                     and set(x.get('slides') or [x.get('slide')]) == set(slides))]
        q.append({'topic': topic, 'slides': slides, 'note': note.strip(),
                  'at': time.time(), 'done': False})
        with open(REDO, 'w') as fh:
            json.dump(q, fh, indent=1, ensure_ascii=False)
    return len([x for x in q if not x.get('done')])


class Handler(http.server.BaseHTTPRequestHandler):
    # HTTP/1.0 closes the socket after every response, so each of the three
    # requests a page makes paid a fresh TCP handshake — two extra round trips
    # apiece, which is most of a second when the server is 9,000km away.
    # Safe because _send always sets an accurate Content-Length.
    protocol_version = 'HTTP/1.1'

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
        # The page and its two payloads are ~477KB of HTML and JSON. On the
        # same machine that is free; from the other side of the world it is
        # most of the wait. Both compress to roughly a tenth.
        enc = None
        if (len(body) > 1400
                and 'gzip' in (self.headers.get('Accept-Encoding') or '')
                and not ctype.startswith(('image/', 'video/'))):
            body, enc = gzip.compress(body, 6), 'gzip'
        self.send_response(code)
        if getattr(self, '_cookie', None):
            self.send_header('Set-Cookie',
                             'dk=%s; Path=/; Max-Age=31536000; SameSite=Lax' % self._cookie)
        self.send_header('Content-Type', ctype)
        if enc:
            self.send_header('Content-Encoding', enc)
            self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self, payload=None, cache_to=None):
        """Hand this request to the host that owns the state."""
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        q.pop('k', None)
        if UPSTREAM_KEY:
            q['k'] = [UPSTREAM_KEY]
        path = u.path + '?' + urllib.parse.urlencode(q, doseq=True)
        method = 'POST' if payload is not None else 'GET'
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'gzip'}
        snap = (_api_cache_path(u.path, u.query)
                if payload is None and u.path in CACHEABLE else None)
        # Reading is quick — the other host answers in tens of milliseconds, so
        # anything past a few seconds means the link is gone and the page
        # should say so rather than spin. Writing can genuinely take minutes:
        # a draft waits on TikTok, a build waits on an agent.
        timeout = 300 if payload is not None else 25
        last = None
        # A pooled connection can have been closed at the far end since it was
        # last used; that shows up only on the next write, so one retry on a
        # fresh socket is the difference between working and looking broken.
        for attempt in (0, 1):
            c = None
            try:
                c = _upstream_borrow(timeout) if not attempt else _new_conn(timeout)
                c.request(method, path, body=payload, headers=headers)
                r = c.getresponse()
                raw = r.read()
                ctype = r.getheader('Content-Type', 'application/json')
                enc = r.getheader('Content-Encoding')
                _upstream_return(c)
                if enc == 'gzip':
                    raw = gzip.decompress(raw)
                # Cached outside drafts/ on purpose: those paths are tracked,
                # and writing them here would collide with the next git pull.
                for dest in (cache_to, snap):
                    if dest and r.status == 200 and raw:
                        try:
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            with open(dest, 'wb') as fh:
                                fh.write(raw)
                        except Exception:
                            pass
                return self._send(r.status, raw, ctype)
            except Exception as exc:
                last = exc
                if c is not None:
                    try:
                        c.close()
                    except Exception:
                        pass
                # The retry is for a pooled socket the far end closed, which
                # fails the moment it is written to. A timeout means the host
                # is gone, and trying again just doubles the wait.
                if isinstance(exc, (socket.timeout, TimeoutError)):
                    break
        # Serve the last good copy rather than nothing. Marked stale with the
        # time it was taken, so the page can say so and refuse to act on it.
        if snap and os.path.isfile(snap):
            try:
                d = json.load(open(snap))
                d['from_cache'] = True
                d['cached_at'] = os.path.getmtime(snap)
                d['upstream_down'] = True
                return self._send(200, d)
            except Exception:
                pass
        # Say which host failed. "Failed to fetch" on a proxied dashboard
        # otherwise looks like the local server is broken when it is not.
        return self._send(502, {'error': 'upstream %s unreachable: %s'
                                         % (UPSTREAM, last),
                                'upstream_down': True})

    def do_GET(self):
        if not self.authed():
            return self.deny()
        path = urllib.parse.urlparse(self.path).path
        if path == '/api/hooks':
            # A build fails if no hook is eligible, and which pillars are open
            # is not guessable from anywhere else in the UI.
            el = hook_rules.eligible()
            return self._send(200, {
                'eligible': [{'lines': h['lines'], 'pillar': h.get('pillar')}
                             for h in el],
                'blocked': [{'lines': l, 'why': w} for l, w in hook_rules.blocked()],
                'suggested': hook_suggestions(),
            })
        if path == '/api/ideas':
            return self._send(200, {'rows': load_ideas()})
        if path.startswith('/ideas_img/'):
            f = os.path.normpath(os.path.join(
                IDEA_IMG, os.path.basename(path[len('/ideas_img/'):])))
            if not f.startswith(IDEA_IMG) or not os.path.isfile(f):
                return self._send(404, {'error': 'not found'})
            with open(f, 'rb') as fh:
                return self._send(200, fh.read(),
                                  mimetypes.guess_type(f)[0] or 'image/png')
        if path == '/api/bgs':
            return self._send(200, bg_catalog())
        if path == '/api/ig':
            # The queue, plus which posts on this disk are ready to join it.
            q = _metrics('/ig/queue')
            ready = {}
            for topic in sorted(os.listdir(DRAFTS)):
                if topic.startswith('_'):
                    continue
                urls = ig_slide_urls(topic)
                if urls:
                    ready[topic] = len(urls)
            return self._send(200, {'queue': q.get('rows') or [],
                                    'error': q.get('error'),
                                    'prepared': ready,
                                    'accounts': IG_ACCOUNTS})
        if path == '/api/users':
            return self._send(200, user_summary(
                int((urllib.parse.parse_qs(
                    urllib.parse.urlparse(self.path).query).get('days')
                    or [30])[0] or 30)))
        if path == '/api/gen':
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            at = float((q.get('at') or [0])[0] or 0)
            row = next((x for x in gen_queue() if x['at'] == at), None)
            if not row:
                return self._send(404, {'error': 'no such run'})
            return self._send(200, {'status': row.get('status'),
                                    'result': row.get('result'),
                                    'why': str(row.get('log') or '').strip().split(chr(10))[0][:200]})
        if path == '/api/tools':
            # The roster picker needs the pool and, for each name, whether an
            # icon actually exists: a tool with no mark cannot go on a slide,
            # and finding that out at render time wastes a whole run.
            pool = load(os.path.join(REPO, 'tools', 'tool_pool.json'), {})
            have = set(os.listdir(ICON_DIR)) if os.path.isdir(ICON_DIR) else set()
            def slug(n):
                return re.sub(r'[^a-z0-9]', '', n.lower())
            by_slug = {slug(f[5:-4]): f for f in have if f.startswith('icon-')}
            out = []
            for cat, names in sorted(pool.items()):
                if cat.startswith('_') or not isinstance(names, list):
                    continue
                for n in names:
                    out.append({'name': n, 'cat': cat,
                                'icon': by_slug.get(slug(n))})
            return self._send(200, {'tools': out,
                                    'cats': sorted(k for k in pool
                                                   if not k.startswith('_')
                                                   and isinstance(pool[k], list))})
        if path == '/':
            return self._send(200, PAGE, 'text/html; charset=utf-8')
        if path == '/phone':
            # A device frame so the phone layout can be designed on the desktop.
            # The iframe is same-origin, so it authenticates as localhost and
            # needs no key of its own.
            return self._send(200, PHONE_FRAME, 'text/html; charset=utf-8')
        if path == '/favicon.png':
            # The real app icon, so the tab is findable among twenty others.
            try:
                with open(os.path.join(REPO, 'tools', 'slides', 'icons',
                                       'icon-arco.png'), 'rb') as fh:
                    return self._send(200, fh.read(), 'image/png')
            except IOError:
                return self._send(404, {'error': 'no icon'})
        if path == '/api/sync':
            return self._send(200, sync_all())
        if path == '/api/analytics':
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            only = [x for x in (q.get('accounts') or [''])[0].split(',') if x]
            num = lambda k: (float(q[k][0]) if q.get(k) and q[k][0] else None)
            return self._send(200, analytics((q.get('period') or ['7'])[0], only,
                                             num('from'), num('to')))
        if path == '/api/promoted':
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            t = (q.get('topic') or [''])[0]
            with _lock:
                cur = set(load(PROMOTED, []))
                cur.symmetric_difference_update({t}) if t else None
                with open(PROMOTED, 'w') as fh:
                    json.dump(sorted(cur), fh, indent=1)
            return self._send(200, {'promoted': sorted(cur)})
        if path == '/api/creator_info':
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            key = (q.get('account') or [''])[0]
            if key not in [a['key'] for a in ACCOUNTS]:
                return self._send(400, {'error': 'unknown account'})
            return self._send(200, creator_info(key))
        if path == '/api/posts':
            return self._send(200, {'posts': list_posts(), 'accounts': ACCOUNTS,
                                    'pending': pending_counts(), 'cap': CAP,
                                    'published_today': published_today(),
                                    'account_stats': account_summary(),
                                    'runs': active_runs(),
                                    'hooks_left': hooks_available(),
                                    'builds': [b for b in build_queue()
                                               if not b.get('done') or b.get('status') == 'running']})
        if path.startswith('/icon/'):
            f = os.path.normpath(os.path.join(ICON_DIR,
                                              os.path.basename(path[len('/icon/'):])))
            if path == '/icon/arco.png':
                f = os.path.join(ICON_DIR, 'icon-arco.png')
            if not f.startswith(ICON_DIR) or not os.path.isfile(f):
                return self._send(404, {'error': 'not found'})
            with open(f, 'rb') as fh:
                return self._send(200, fh.read(),
                                  mimetypes.guess_type(f)[0] or 'image/png')
        if path.startswith('/bg/'):
            body, ctype = bg_thumb(path[len('/bg/'):])
            if body is None:
                return self._send(404, {'error': 'not found'})
            return self._send(200, body, ctype)
        if path.startswith('/slide/'):
            rel = path[len('/slide/'):]
            f = os.path.normpath(os.path.join(DRAFTS, rel))
            if not f.startswith(DRAFTS) or not os.path.isfile(f):
                # Built upstream and not pulled here yet. Fetch once, keep it,
                # serve it from disk after that: the newest posts are exactly
                # the ones being reviewed, and half a megabyte from the other
                # side of the world is the whole wait.
                if UPSTREAM:
                    cached = os.path.normpath(os.path.join(SLIDE_CACHE, rel))
                    if cached.startswith(SLIDE_CACHE) and os.path.isfile(cached):
                        with open(cached, 'rb') as fh:
                            return self._send(200, fh.read(),
                                              mimetypes.guess_type(cached)[0]
                                              or 'image/jpeg')
                    return self._proxy(cache_to=cached)
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
        raw = self.rfile.read(n) or b'{}'
        # Actions run where the state lives, so drafting from either instance
        # writes to one delivery log.
        if UPSTREAM and path.startswith('/api/'):
            return self._proxy(raw)
        body = json.loads(raw)
        if path == '/api/draft':
            topic = body['topic']
            keys = body.get('accounts') or [a['key'] for a in ACCOUNTS]
            return self._send(200, {'results': run_draft(topic, keys),
                                    'pending': pending_counts()})
        if path == '/api/ideas':
            return self._send(200, idea_apply(body))
        if path == '/api/ideas/img':
            name = idea_save_image(body.get('data') or '')
            if not name:
                return self._send(400, {'error': 'not an image'})
            return self._send(200, {'img': name})
        if path == '/api/autofill':
            # Choosing was never the judgment call — the words are. So the
            # photos, the roster and the hook come straight from the rules,
            # instantly and for free, and the agent is left with the writing.
            only = body.get('only')
            if isinstance(only, str) and only.isdigit():
                only = int(only)
            return self._send(200, autofill(body.get('pillar') or 'tools',
                                            body.get('slides') or [],
                                            only if only is not None else 'all'))
        if path == '/api/gen':
            # Writing copy is judgment, so it is an agent — but a small one
            # that answers into the composer instead of building a post.
            what = body.get('what')
            job = {'what': what if what in ('hooks', 'post') else 'slide',
                   'plan': body.get('plan') or '',
                   'pillar': body.get('pillar') or 'tools',
                   'hook': body.get('hook') or '',
                   'tool': body.get('tool') or '',
                   'others': body.get('others') or '',
                   'note': (body.get('note') or '').strip(),
                   'n': max(1, min(8, int(body.get('n') or 5))),
                   'at': time.time(), 'done': False, 'status': 'queued'}
            with _lock:
                q = gen_queue()
                q.append(job)
                save_gen(q)
            threading.Thread(target=run_gen, args=(job,), daemon=True).start()
            return self._send(200, {'ok': True, 'at': job['at']})
        if path == '/api/ig/prepare':
            return self._send(200, ig_prepare(body['topic']))
        if path == '/api/ig/prepare_many':
            return self._send(200, ig_prepare_many(body.get('topics') or []))
        if path == '/api/ig/caption':
            t = body['topic']
            return self._send(200, {'caption': ig_caption(t),
                                    'blocked': ig_blocked(t)})
        if path == '/api/ig/check':
            urls = ig_slide_urls(body['topic'])
            return self._send(200, {'urls': urls, 'live': ig_serving(urls),
                                    'total': len(urls)})
        if path == '/api/ig/schedule':
            topic = body['topic']
            urls = ig_slide_urls(topic)
            if not urls:
                return self._send(400, {'error': 'no 4:5 crops yet — prepare it first'})
            # What he typed in the sheet wins; the stored caption is only
            # the starting point, because Instagram wants its own hashtags.
            cap = (body.get('caption') or '').strip() or ig_caption(topic)
            if not cap:
                return self._send(400, {'error': 'no caption to post with'})
            return self._send(200, _metrics('/ig/schedule', {
                'topic': topic, 'account': body.get('account') or 'getarco',
                'at': int(body.get('at') or 0), 'urls': urls, 'caption': cap},
                write=True))
        if path == '/api/ig/cancel':
            return self._send(200, _metrics('/ig/cancel', {'id': body['id']}, write=True))
        if path == '/api/ig/run':
            return self._send(200, _metrics('/ig/run', {}, write=True))
        if path == '/api/hook':
            # hook_slide refuses anything that is not in the pool, so a hook
            # he writes in the composer has to land there before the build
            # starts, or the run dies at the first slide.
            lines = [str(l).strip().lower() for l in (body.get('lines') or []) if str(l).strip()]
            if len(lines) != 2:
                return self._send(400, {'error': 'a hook is two lines'})
            if any(len(l) > 42 for l in lines):
                return self._send(400, {'error': 'each line has to fit SF Bold 74 '
                                                 'on a 1080 canvas — keep it under 42 characters'})
            with _lock:
                pool = load(os.path.join(REPO, 'tools', 'hook_pool.json'), {})
                hooks = pool.setdefault('hooks', [])
                if any([str(x).lower() for x in h.get('lines', [])] == lines for h in hooks):
                    return self._send(200, {'ok': True, 'already': True})
                hooks.append({'lines': lines, 'used': False,
                              'pillar': body.get('pillar') or 'tools',
                              'added': time.time()})
                with open(os.path.join(REPO, 'tools', 'hook_pool.json'), 'w') as fh:
                    json.dump(pool, fh, indent=1, ensure_ascii=False)
            return self._send(200, {'ok': True})
        if path == '/api/build':
            # A background set that breaks the rules fails at render, ten
            # minutes and one agent run later. The gallery says so as you
            # pick; this is the one that actually stops it.
            probs = bg_problems(spec_bgs(body.get('spec')))
            if probs:
                return self._send(400, {'error': probs[0], 'problems': probs})
            with _lock:
                q = build_queue()
                if body.get('cancel'):
                    q = [b for b in q if b.get('done')]
                else:
                    job = {'count': max(1, min(10, int(body.get('count', 1)))),
                           'pillar': body.get('pillar') or 'tools',
                           'note': (body.get('note') or '').strip(),
                           'spec': body.get('spec') or None,
                           'at': time.time(), 'done': False, 'status': 'queued'}
                    q.append(job)
                    threading.Thread(target=run_build, args=(job,), daemon=True).start()
                save_builds(q)
            return self._send(200, {'ok': True})
        if path == '/api/retry':
            # Run the same job again rather than making him rebuild the
            # request from memory. The old row is marked dismissed so the
            # panel does not show the failure and its retry side by side.
            at = float(body.get('at') or 0)
            kind = body.get('kind')
            spec = {'build': (BUILD, build_queue, run_build),
                    'redo': (REDO, redo_queue, run_redo),
                    'replicate': (REPLICATE, replicate_queue, run_replicate)}.get(kind)
            if not spec:
                return self._send(400, {'error': 'unknown kind'})
            path_, loader, runner = spec
            with _lock:
                items = loader()
                old = next((x for x in items if abs((x.get('at') or 0) - at) < 1), None)
                if not old:
                    return self._send(404, {'error': 'that run is gone'})
                old['dismissed'] = True
                job = {k: v for k, v in old.items()
                       if k not in ('status', 'log', 'done', 'started',
                                    'finished', 'dismissed')}
                job.update({'at': time.time(), 'status': 'queued', 'done': False})
                items.append(job)
                with open(path_, 'w') as fh:
                    json.dump(items, fh, indent=1, ensure_ascii=False)
            threading.Thread(target=runner, args=(job,), daemon=True).start()
            return self._send(200, {'ok': True})
        if path == '/api/dismiss':
            with _lock:
                for path_, loader in ((BUILD, build_queue), (REDO, redo_queue),
                                      (REPLICATE, replicate_queue)):
                    items = loader()
                    hit = False
                    for x in items:
                        if x.get('status') in ('failed', 'interrupted'):
                            x['dismissed'] = True
                            hit = True
                    if hit:
                        with open(path_, 'w') as fh:
                            json.dump(items, fh, indent=1, ensure_ascii=False)
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
                    mode = 'direct' if body.get('mode') == 'direct' else 'draft'
                    st = body.get('settings') or {}
                    if mode == 'direct':
                        # Refuse an unpostable job at the point it is made,
                        # rather than letting it sit until it fires and fails.
                        for key in (body.get('accounts') or [a['key'] for a in ACCOUNTS]):
                            why = direct_blocked(key, st)
                            if why:
                                return self._send(400, {'error': '%s: %s' % (key, why)})
                    sc.append({'topic': body['topic'], 'at': float(body['at']),
                               'accounts': body.get('accounts') or [],
                               'stagger_min': int(body.get('stagger_min') or 0),
                               'mode': mode, 'settings': st if mode == 'direct' else {},
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
                hook_rules.forget(topic)
            return self._send(200, {'ok': True, 'moved_to': dest})
        if path == '/api/redo':
            slides = body.get('slides') or [body.get('slide')]
            n = queue_redo(body['topic'], [int(x) for x in slides if x],
                           body.get('note', ''))
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
                    'mode': body.get('mode') or 'new',
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
        if path == '/api/publish_direct':
            topic, key = body['topic'], body['account']
            st = body.get('settings') or {}
            if not st.get('privacy'):
                return self._send(400, {'error': 'pick a privacy level first'})
            if st.get('branded_content') and st['privacy'] == 'SELF_ONLY':
                return self._send(400, {'error': 'branded content cannot be private'})
            threading.Thread(target=run_publish, args=(topic, key, st),
                             daemon=True).start()
            return self._send(200, {'ok': True})
        if path == '/api/publish':
            # Publishing happens by hand in the TikTok app and the API cannot
            # see it, so it is recorded here. A published draft stops counting
            # against the cap, which is the whole reason this state exists.
            with _lock:
                log = delivery_log()
                recs = log.get(body['topic'], {})
                # No account named means the whole post: the top bar marks it
                # published everywhere in one click.
                keys = [body['account']] if body.get('account') else [
                    k for k, r in recs.items() if r.get('status') == 'SENT']
                for k in keys:
                    rec = recs.get(k)
                    if not rec:
                        continue
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
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  /* Near-black with a blue cast rather than neutral black — the reference
     reads as glass lit from behind, not as paper inverted. Panels are
     translucent over it so the ground shows through and the whole thing
     sits on one surface instead of many stacked cards. */
  /* One channel drives the whole theme: --accent-rgb. Every tint, hairline
     and glow is mixed from it, so changing the palette is one line rather
     than hunting twenty-five hardcoded rgba() calls. */
  --accent-rgb:232,237,250;
  /* Black, with the light arriving as glow rather than as paint. Panels and
     type stay neutral so the only colour on screen comes from the accent —
     tinting every surface made the whole page look washed instead of lit.
     White reads far brighter than a hue at the same alpha, so the hairlines
     sit lower than they would for a coloured accent. */
  --bg:#040507; --ink-rgb:4,5,7;
  --bg:#040507; --surface:rgba(16,17,22,.93); --surface-2:rgba(27,29,36,.95);
  --line:rgba(var(--accent-rgb),.14); --line-2:rgba(var(--accent-rgb),.3);
  --text:#ECEEF4; --muted:#979BA6; --dim:#5D616C;
  --accent:#E8EDFA; --glow:rgba(var(--accent-rgb),.42);
  /* Status keeps its own hues: these carry meaning and must not all be cyan. */
  --ok:#34E39B; --warn:#F5B945; --bad:#FF5C7A;
  --r:3px; --z-modal:50;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
/* A faint grid, the way a HUD sits on a surface rather than on nothing.
   Two hairlines at 64px; far enough apart to read as structure, faint
   enough that nothing on top of it has to fight. */
/* Rings leaving the eye. Three, staggered, so one is always mid-flight —
   the page reads as lit from a source rather than tinted at the corners. */
@keyframes ping{
  0%{transform:scale(.06);opacity:0}
  12%{opacity:.5}
  100%{transform:scale(1);opacity:0}}
.bgfx{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden}
.bgfx .ring{position:absolute;left:60px;top:60px;width:2400px;height:2400px;
  margin:-1200px 0 0 -1200px;border-radius:50%;
  border:1px solid rgba(var(--accent-rgb),.5);
  animation:ping 14s cubic-bezier(.2,.5,.3,1) infinite}
.bgfx .ring:nth-child(2){animation-delay:-4.6s}
.bgfx .ring:nth-child(3){animation-delay:-9.3s}
/* Grain. Flat black on a wide screen bands; a little noise kills that and
   gives the surfaces something to sit on. */
.bgfx .grain{position:absolute;inset:-50%;opacity:.5;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='.035'/%3E%3C/svg%3E")}
/* A large dial assembly behind the work. It is the same construct as the
   reticle in the corner, drawn at twenty times the size and a twentieth the
   contrast — present when you look for it, invisible when you are reading a
   caption. Everything here is a fraction of a percent of alpha; raising it
   turns a background into wallpaper. */
.hud{position:absolute;left:58%;top:50%;width:860px;height:860px;
  margin:-430px 0 0 -430px;opacity:.55}
.hud i{position:absolute;inset:0;border-radius:50%}
.hud i.m{-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - var(--w)),#000 0);
         mask:radial-gradient(farthest-side,transparent calc(100% - var(--w)),#000 0)}
/* thin outer ring, broken on the diagonals */
.hud .h1{--w:1px;inset:0;
  background:conic-gradient(from -40deg,
    rgba(var(--accent-rgb),.16) 0deg 80deg,transparent 80deg 90deg,
    rgba(var(--accent-rgb),.16) 90deg 170deg,transparent 170deg 180deg,
    rgba(var(--accent-rgb),.16) 180deg 260deg,transparent 260deg 270deg,
    rgba(var(--accent-rgb),.16) 270deg 350deg,transparent 350deg 360deg);
  animation:spin 190s linear infinite}
/* the long tick comb — 120 teeth */
.hud .h2{--w:16px;inset:26px;
  background:repeating-conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.11) 0deg .7deg,transparent .7deg 3deg);
  animation:spinback 240s linear infinite}
/* segment band */
.hud .h3{--w:30px;inset:74px;
  background:repeating-conic-gradient(from 6deg,
    rgba(var(--accent-rgb),.055) 0deg 16deg,transparent 16deg 24deg);
  animation:spin 300s linear infinite}
/* two long arcs, the brightest thing in the assembly and still barely there */
.hud .h4{--w:2px;inset:132px;
  background:conic-gradient(from 20deg,
    rgba(var(--accent-rgb),.2) 0deg 104deg,transparent 104deg 190deg,
    rgba(var(--accent-rgb),.13) 190deg 244deg,transparent 244deg 360deg);
  animation:spinback 120s linear infinite}
/* spokes, cut back to a ring so the middle stays clear */
.hud .h5{--w:120px;inset:180px;
  background:repeating-conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.06) 0deg .35deg,transparent .35deg 15deg);
  animation:spin 400s linear infinite}
/* inner comb and edge */
.hud .h6{--w:9px;inset:308px;
  background:repeating-conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.1) 0deg 1.4deg,transparent 1.4deg 6deg);
  animation:spinback 150s linear infinite}
.hud .h7{inset:352px;border:1px solid rgba(var(--accent-rgb),.11)}
@media(max-width:900px){.hud{display:none}}

/* Satellite dials. Each is three rings: a comb, a broken ring and an arc,
   turning against each other the way the big one does. */
.sat{position:absolute;border-radius:50%;opacity:.5}
.sat i{position:absolute;inset:0;border-radius:50%;
  -webkit-mask:radial-gradient(farthest-side,transparent calc(100% - var(--w)),#000 0);
          mask:radial-gradient(farthest-side,transparent calc(100% - var(--w)),#000 0)}
.sat .s1{--w:1px;inset:0;
  background:conic-gradient(from -30deg,
    rgba(var(--accent-rgb),.22) 0deg 120deg,transparent 120deg 150deg,
    rgba(var(--accent-rgb),.22) 150deg 270deg,transparent 270deg 300deg,
    rgba(var(--accent-rgb),.22) 300deg 360deg);
  animation:spin 80s linear infinite}
.sat .s2{--w:6px;inset:11%;
  background:repeating-conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.13) 0deg 1.1deg,transparent 1.1deg 5deg);
  animation:spinback 110s linear infinite}
.sat .s3{--w:2px;inset:30%;
  background:conic-gradient(from 60deg,
    rgba(var(--accent-rgb),.26) 0deg 88deg,transparent 88deg 360deg);
  animation:spin 46s linear infinite}
.sat .s4{inset:46%;background:rgba(var(--accent-rgb),.18);-webkit-mask:none;mask:none}
.sat.a{left:16%;top:13%;width:168px;height:168px;margin:-84px 0 0 -84px}
.sat.b{left:80%;top:74%;width:224px;height:224px;margin:-112px 0 0 -112px}
.sat.c{left:70%;top:9%;width:96px;height:96px;margin:-48px 0 0 -48px}
@media(max-width:1200px){.sat.c{display:none}}
@media(max-width:900px){.sat{display:none}}

/* Readouts. A console shows numbers. These are the real ones — the same
   figures the pages are built from — set low enough to be texture until you
   choose to read them, which is the only reason to put text in a background.
   Hidden on a narrow screen, where the panels cover this corner. */
.hudread{position:fixed;right:30px;bottom:26px;z-index:0;pointer-events:none;
  text-align:right;font-family:"Fira Code",monospace;
  color:rgba(var(--accent-rgb),.42);user-select:none}
/* Lit, not merely lighter: the halo is what makes a readout look powered.
   Values carry more of it than their labels, so the figures come forward. */
.hudread .clk{font-size:56px;font-weight:600;line-height:.95;letter-spacing:-.01em;
  font-variant-numeric:tabular-nums;color:rgba(var(--accent-rgb),.5);
  text-shadow:0 0 26px rgba(var(--accent-rgb),.34),0 0 8px rgba(var(--accent-rgb),.22)}
.hudread .clk span{font-size:22px;color:rgba(var(--accent-rgb),.3);margin-left:4px}
.hudread .dt{font-size:10.5px;font-weight:700;letter-spacing:.22em;
  text-transform:uppercase;margin-top:5px;color:rgba(var(--accent-rgb),.38);
  text-shadow:0 0 14px rgba(var(--accent-rgb),.25)}
.hudread .rows{margin-top:13px;display:grid;gap:4px;font-size:10px;font-weight:700;
  letter-spacing:.14em}
.hudread .rows div{display:flex;justify-content:flex-end;gap:10px}
.hudread .rows i{font-style:normal;color:rgba(var(--accent-rgb),.3)}
.hudread .rows b{font-weight:700;font-variant-numeric:tabular-nums;
  color:rgba(var(--accent-rgb),.62);min-width:56px;text-align:right;
  text-shadow:0 0 16px rgba(var(--accent-rgb),.4)}
@media(max-width:1200px){.hudread{display:none}}

/* Hairlines between the dials. A console is wired together; without these
   the circles float. */
.wire{position:absolute;background:rgba(var(--accent-rgb),.08)}
.wire.w1{left:16%;top:13%;width:54%;height:1px}
.wire.w2{left:70%;top:13%;width:1px;height:61%}
.wire.w3{left:24%;top:74%;width:56%;height:1px}
@media(max-width:900px){.wire{display:none}}
@media(prefers-reduced-motion:reduce){.hud i{animation:none}}

/* Corner brackets — the frame that makes the page an instrument panel. */
/* The brackets ride above the panels — a frame drawn behind the sidebar is
   not a frame. Nothing else in .bgfx leaves z-index 0. */
.bgfx .br{position:fixed;z-index:200;width:26px;height:26px;
  border:1px solid rgba(var(--accent-rgb),.28)}
.bgfx .br.tl{top:10px;left:10px;border-right:0;border-bottom:0}
.bgfx .br.tr{top:10px;right:10px;border-left:0;border-bottom:0}
.bgfx .br.bl{bottom:10px;left:10px;border-right:0;border-top:0}
.bgfx .br.br2{bottom:10px;right:10px;border-left:0;border-top:0}
@media(prefers-reduced-motion:reduce){
  .bgfx .ring{animation:none;opacity:0}}

/* The bloom comes from the eye. It is anchored at the reticle in the top
   left and breathes on a slow cycle, so the light on the page has a source
   you can point at rather than being a wash applied to the corners. A far
   fainter second source keeps the opposite side from going flat black. */
@keyframes breathe{
  0%,100%{opacity:.85;transform:scale(1)}
  50%{opacity:1;transform:scale(1.06)}}
body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  transform-origin:60px 60px;
  background:
    radial-gradient(38% 52% at 60px 60px,rgba(var(--accent-rgb),.17),transparent 72%),
    radial-gradient(70% 60% at 60px 60px,rgba(var(--accent-rgb),.07),transparent 76%),
    radial-gradient(50% 45% at 92% 104%,rgba(var(--accent-rgb),.055),transparent 72%);
  animation:breathe 7s ease-in-out infinite}
.app{position:relative;z-index:1}
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
/* The reticle. Six layers, because the look comes from density rather than
   from any one ring: a comb of fine ticks, two bright arcs turning against
   each other, a dashed hairline, a coarser tick ring, and a lit inner edge.
   All CSS — repeating-conic-gradient draws the combs, and a radial mask
   punches each one back to a ring so the middle stays clear for the mark. */
.eye{position:relative;display:grid;place-items:center;width:76px;height:76px;flex:none}
.eye i{position:absolute;border-radius:50%;pointer-events:none}
/* ring() — keep only the outer Npx of a filled circle, so a conic gradient
   painted across the whole disc reads as a band of ticks */
.eye .r1,.eye .r2,.eye .r4,.eye .r5,.eye .r7,.eye .r8{
  -webkit-mask:radial-gradient(farthest-side,transparent calc(100% - var(--w)),#000 0);
          mask:radial-gradient(farthest-side,transparent calc(100% - var(--w)),#000 0)}

/* outermost: four heavy bracket arcs with gaps on the diagonals. Static —
   it is the frame the moving parts are read against. */
.eye .r1{--w:2px;inset:0;
  background:conic-gradient(from -38deg,
    rgba(var(--accent-rgb),.8) 0deg 76deg,transparent 76deg 90deg,
    rgba(var(--accent-rgb),.8) 90deg 166deg,transparent 166deg 180deg,
    rgba(var(--accent-rgb),.8) 180deg 256deg,transparent 256deg 270deg,
    rgba(var(--accent-rgb),.8) 270deg 346deg,transparent 346deg 360deg)}
/* fine comb: 72 ticks, turning slowly */
.eye .r2{--w:3.5px;inset:3px;
  background:repeating-conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.5) 0deg 1.2deg,transparent 1.2deg 5deg);
  animation:spin 30s linear infinite}
/* dashed hairline, still */
.eye .r3{inset:7.5px;border:1px dashed rgba(var(--accent-rgb),.34)}
/* segmented band: twelve blocks, the slowest thing on the dial */
.eye .r7{--w:3px;inset:9px;
  background:repeating-conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.32) 0deg 22deg,transparent 22deg 30deg);
  animation:spin 44s linear infinite}
/* the sweep — one short bright arc, the fastest thing on it */
.eye .r8{--w:1.5px;inset:12.5px;
  background:conic-gradient(from 0deg,
    rgba(var(--accent-rgb),1) 0deg 26deg,transparent 26deg 360deg);
  animation:spin 3.4s linear infinite;
  filter:drop-shadow(0 0 7px rgba(var(--accent-rgb),.9))}
/* two bright arcs, the other way and slower */
.eye .r4{--w:2px;inset:14.5px;
  background:conic-gradient(from 0deg,
    rgba(var(--accent-rgb),.95) 0deg 52deg,transparent 52deg 132deg,
    rgba(var(--accent-rgb),.75) 132deg 164deg,transparent 164deg 360deg);
  animation:spinback 7.5s linear infinite;
  filter:drop-shadow(0 0 5px rgba(var(--accent-rgb),.8))}
/* coarse comb of 24 ticks, slow, the other way again */
.eye .r5{--w:1.5px;inset:17px;
  background:repeating-conic-gradient(from 7.5deg,
    rgba(var(--accent-rgb),.5) 0deg 2.6deg,transparent 2.6deg 15deg);
  animation:spinback 22s linear infinite}

/* the orbiting tabs — eight blocks pushed out on a radius, turning as a
   group, plus four larger ones going the other way further in */
.eye .tb,.eye .tb2{position:absolute;inset:0;border-radius:50%}
.eye .tb{animation:spin 17s linear infinite}
.eye .tb2{animation:spinback 11s linear infinite}
.eye .tb b,.eye .tb2 b{position:absolute;left:50%;top:50%;display:block;
  background:rgba(var(--accent-rgb),.62);
  box-shadow:0 0 6px -1px rgba(var(--accent-rgb),.8)}
.eye .tb b{width:6px;height:2.5px;margin:-1.25px 0 0 -3px;
  transform:rotate(var(--a)) translateY(-33px)}
.eye .tb2 b{width:3px;height:5px;margin:-2.5px 0 0 -1.5px;
  background:rgba(var(--accent-rgb),.85);
  transform:rotate(var(--a)) translateY(-25px)}

/* the lit edge the mark sits inside */
.eye .r6{inset:19px;border:1px solid rgba(var(--accent-rgb),.55);
  box-shadow:0 0 14px -2px rgba(var(--accent-rgb),.6),
    inset 0 0 10px -4px rgba(var(--accent-rgb),.6)}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes spinback{to{transform:rotate(-360deg)}}
.brand img{position:relative;z-index:1;width:38px;height:38px;border-radius:10px;
  box-shadow:0 0 22px -6px var(--glow)}
.brand{gap:9px}
/* The one piece of type that is allowed to be an object rather than a
   label — it is the only thing on the page that never changes. */
.brand .n{font-weight:600;font-size:17px;letter-spacing:.06em;color:#EAFBFF;
  text-shadow:0 0 14px rgba(var(--accent-rgb),.55),0 0 34px rgba(var(--accent-rgb),.28)}
.brand .v{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
/* A property of the subtitle, not a third thing in the stack: a dot in the
   host's colour and the name beside it, on the same line. */
/* The laptop is the one that can be closed mid-task, so it gets the warmer
   colour. */
/* Upstream gone: the dot stops glowing and goes red, so a stale page is
   visibly stale rather than quietly wrong. */
.compose{max-width:720px}
.compose h3{font:600 16px/1.3 system-ui;margin:0 0 6px}
.compose textarea{width:100%;min-height:132px;resize:vertical;margin:12px 0 0;
  background:var(--surface);border:1px solid var(--line-2);border-radius:11px;
  color:var(--text);font:400 13.5px/1.6 system-ui;padding:13px 14px}
.compose textarea:focus{outline:none;border-color:var(--accent)}
.compose textarea::placeholder{color:var(--dim)}
.crow{display:flex;align-items:center;gap:11px;margin:12px 0 0}
.crow .sp{margin-left:auto}
.crow .btn[disabled]{opacity:.4;cursor:not-allowed}
/* What the pool can actually supply. A build with no eligible hook fails, and
   nothing else on the page says how many are left. */
.hooksup{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:18px 0 0;
  padding:12px 14px;background:var(--surface);border:1px solid var(--line);
  border-radius:11px}
.hooksup.none{border-color:rgba(251,146,60,.45)}
.hooksup.none b{color:var(--warn)}
.hooksup .hp{padding:4px 9px;border-radius:7px;background:var(--surface-2);
  border:1px solid var(--line-2);font:500 11.5px/1 "Fira Code",monospace;color:var(--muted)}
.hooksup .hp b{color:var(--text);font-weight:600}
.hooksup .sub{font-size:12px}
@media (max-width:900px){ .crow{flex-wrap:wrap} .crow .sp{display:none} }

/* ---------- the composer ----------
   One card per slide, laid out the way the carousel is: the photo on the
   left at 9:16, the words beside it. A wizard would hide the pool behind
   Next buttons; seeing the whole post at once is the point. */
.cx{max-width:920px}
.ptop{margin:0 0 10px!important}
.csub{font:600 11px/1 "Fira Code",monospace;text-transform:uppercase;
  letter-spacing:.07em;color:var(--dim);margin:18px 0 2px}
.csum{font-size:11.5px;color:var(--dim)}
.cwarn{margin:10px 0 0;padding:10px 12px;border-radius:10px;font-size:12px;line-height:1.55;
  background:rgba(245,158,11,.09);border:1px solid rgba(245,158,11,.38);color:#fde68a}
.cwarn b{color:var(--warn)}
.warnt{color:var(--warn)}
.segs.multi{flex-wrap:wrap;gap:6px;margin:10px 0 0;border:0;overflow:visible;
  align-items:flex-start}
.segs.multi .seg{border:1px solid var(--line-2);border-radius:8px;padding:7px 12px;
  white-space:nowrap}
.btn.sm{padding:7px 13px;font-size:12.5px}
.addsl{margin:10px 0 0}
/* ---------- motion ----------
   One orchestrated moment on load, and after that only motion that answers
   something you did. render() runs on every state change, so nothing here
   is attached to content — an entrance that re-fires on every repaint is
   a twitch, not polish. The boot class is set once and removed. */
@keyframes sweep{from{transform:translateY(-100%)}to{transform:translateY(100vh)}}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes wake{from{opacity:0}to{opacity:1}}
@keyframes livepulse{0%,100%{opacity:1}50%{opacity:.45}}

body.boot main::after{content:"";position:fixed;left:232px;right:0;top:0;height:120px;
  pointer-events:none;z-index:40;
  background:linear-gradient(rgba(var(--accent-rgb),0),rgba(var(--accent-rgb),.13),rgba(var(--accent-rgb),0));
  animation:sweep .85s cubic-bezier(.4,0,.2,1) forwards}
body.boot aside{animation:wake .5s ease both}
body.boot .brand{animation:rise .55s cubic-bezier(.2,.8,.2,1) both .05s}
body.boot .nav{animation:rise .4s cubic-bezier(.2,.8,.2,1) both}
body.boot .nav:nth-child(2){animation-delay:.05s}
body.boot .nav:nth-child(3){animation-delay:.09s}
body.boot .nav:nth-child(4){animation-delay:.13s}
body.boot .nav:nth-child(5){animation-delay:.17s}
body.boot main{animation:wake .6s ease both .15s}

/* Live, not decorative: the only thing that moves on its own is the post
   currently being handed to Instagram. */
.qrow.publishing .st,.wc.publishing .pill{animation:livepulse 1.4s ease-in-out infinite}

/* Turning to another page. The content carries the movement; the nav does
   not, because the bar sliding and the page sliding at once reads as drift. */
@keyframes turn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
#view.turned{animation:turn .26s cubic-bezier(.2,.8,.2,1)}

/* Every control says it was pressed. Depth, not colour: a HUD control is a
   switch you push, and the glow underneath confirms contact. */
.btn:active,.seg:active,.nav:active,.pil:active,.igcard:active,.wkarr:active,
.chk.acc:active,.lnk:active{transform:translateY(1px) scale(.985)}
.btn:active{box-shadow:0 0 22px -6px var(--glow)}
.btn,.seg,.nav,.pil,.igcard,.wkarr,.chk.acc,.lnk,.wc,.bt,.tl,.hk{
  transition:transform .09s cubic-bezier(.2,.8,.2,1),background .18s,
    color .18s,border-color .18s,box-shadow .22s,opacity .18s}

/* Motion that answers an action. */
.shwrap{animation:wake .16s ease}
.sh{animation:rise .22s cubic-bezier(.2,.8,.2,1)}
#modal[style*="flex"] .box{animation:rise .2s cubic-bezier(.2,.8,.2,1)}
.cardmenu{animation:rise .14s cubic-bezier(.2,.8,.2,1)}
.nav,.seg,.btn,.wc,.qrow{transition:background .18s,color .18s,border-color .18s,
  box-shadow .22s,opacity .18s}
.wc:hover{box-shadow:0 0 0 1px var(--line-2),0 0 22px -10px var(--glow)}

/* Inline links inside prose. Without this they fall through to the browser
   default — blue and underlined in the middle of a purple instrument. */
.why a,p a{color:var(--accent);text-decoration:none;
  border-bottom:1px solid rgba(var(--accent-rgb),.45);padding-bottom:1px}
.why a:hover,p a:hover{border-bottom-color:var(--accent);
  text-shadow:0 0 12px var(--glow)}

/* ---------- HUD ----------
   One bold device, used sparingly: corner brackets. They mark a panel as an
   instrument rather than a card, and because they only draw four corners
   they cost less visual weight than a full border would. Everything else
   here is restraint — hairlines, and glow reserved for what is active. */
.pcard, .ubox, .ukpi, .qrow, .slrow, .tkbar, .npbar, .cbar, .libbar + .grid,
#modal .box{position:relative}
.pcard::before, .ubox::before, .ukpi::before, .tkbar::before, .npbar::before,
.cbar::before, #modal .box::before{
  content:"";position:absolute;inset:-1px;pointer-events:none;
  background:
    linear-gradient(var(--line-2),var(--line-2)) 0 0/9px 1px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 0 0/1px 9px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 100% 0/9px 1px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 100% 0/1px 9px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 0 100%/9px 1px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 0 100%/1px 9px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 100% 100%/9px 1px no-repeat,
    linear-gradient(var(--line-2),var(--line-2)) 100% 100%/1px 9px no-repeat}

/* Glow marks the one thing that is live, never decoration. */
.nav[aria-current="true"]{box-shadow:inset 2px 0 0 var(--accent),
  0 0 22px -8px var(--glow)}
.btn{box-shadow:0 0 16px -8px var(--glow)}
.seg.on{box-shadow:inset 0 0 0 1px var(--line-2),0 0 14px -8px var(--glow)}
.wc.publishing{box-shadow:0 0 20px -8px var(--glow)}
.wh.today b,.wh.today i{text-shadow:0 0 12px var(--glow)}

/* Figures are the instrument reading; they get the mono face and the glow,
   prose stays quiet. */
.ukpi b,.kpi b,.astat b{font-family:"Fira Code",ui-monospace,monospace;
  letter-spacing:-.02em;text-shadow:0 0 18px rgba(var(--accent-rgb),.25)}

/* Thumbnails are the one place colour comes from the content, so the chrome
   around them gets out of the way. */
.thumb,.wc,.igcard img,.sth{border-radius:2px}
.card,.cardwrap,.igcard,.wc{border-radius:3px}

/* ---------- tiktok + library ---------- */
.tkbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:0 0 6px;
  padding:12px 14px;background:var(--surface);border:1px solid var(--line);border-radius:12px}
.tkbar .slots{display:flex;gap:8px;flex-wrap:wrap}
.tkbar .csum{flex:1;min-width:120px}
.slot{padding:5px 10px;border-radius:8px;background:var(--surface-2);
  border:1px solid var(--line-2);font:500 11.5px/1 "Fira Code",monospace;color:var(--muted)}
.slot b{color:var(--ok);font-weight:700;margin-right:3px}
.slot.none{opacity:.55}
.slot.none b{color:var(--dim)}
.libbar{display:flex;align-items:center;gap:10px;margin:0 0 6px;flex-wrap:wrap}
.libbar .lbl{width:52px;flex:none;font:500 10.5px/1 "Fira Code",monospace;
  text-transform:uppercase;letter-spacing:.07em;color:var(--dim)}
.libbar .segs{margin:0}
.libbar.sort{margin-bottom:14px}
.libbar.sort .seg{padding:5px 10px;font-size:10.5px}
@media (max-width:900px){ .libbar .lbl{width:auto} }
/* ---------- new post ----------
   One question, five answers, one button. */
.np{max-width:640px}
.np h3{font:600 17px/1.3 system-ui;margin:0 0 12px}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:8px}
.pil{padding:13px 14px;border:1px solid var(--line-2);border-radius:12px;
  background:var(--surface);color:var(--text);text-align:left}
.pil:hover{border-color:var(--muted)}
.pil.on{border-color:var(--accent);background:rgba(var(--accent-rgb),.1)}
.pil b{display:block;font:600 13.5px/1.3 system-ui}
.pil i{display:block;margin-top:3px;font-style:normal;font-size:11.5px;color:var(--dim)}
.pil.on i{color:var(--muted)}
.csub .opt{text-transform:none;letter-spacing:0;color:var(--dim);font-weight:500}
.npnote{width:100%;min-height:64px;resize:vertical;margin:8px 0 0;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:10px;
  color:var(--text);font:400 13px/1.6 system-ui;padding:10px 12px}
.npnote:focus{outline:none;border-color:var(--accent)}
.npnote::placeholder{color:var(--dim)}
.npbar{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin:18px 0 0;
  padding:12px 14px;background:var(--surface);border:1px solid var(--line-2);
  border-radius:13px}
.npbar .sum{flex:1;min-width:150px;font-size:12px;color:var(--dim)}
.npbar .btn[disabled]{opacity:.4;cursor:not-allowed}
.thumb .dots{position:absolute;top:8px;right:8px;width:32px;height:32px;
  border-radius:8px;background:rgba(var(--ink-rgb),.72);border:1px solid var(--line-2);
  color:var(--muted);font:600 16px/29px system-ui;text-align:center;cursor:pointer;
  opacity:.5;z-index:2;transition:opacity .18s,color .18s,border-color .18s}
.cardwrap:hover .thumb .dots{opacity:1}
.thumb .dots:hover{color:var(--text);border-color:var(--accent)}
.cardmenu{position:fixed;z-index:var(--z-modal);background:var(--surface);
  border:1px solid var(--line-2);border-radius:10px;padding:5px;
  box-shadow:0 12px 30px rgba(var(--ink-rgb),.65)}
.cardmenu button{display:block;width:100%;text-align:left;background:none;
  border:0;color:var(--text);font:500 13px/1 system-ui;padding:9px 13px;border-radius:7px}
.cardmenu button:hover{background:var(--surface-2);color:var(--accent)}
.cardmenu button.bad:hover{color:var(--bad)}
/* ---------- schedule ----------
   A day-grouped list, not a month grid: a month grid at 400px is unreadable
   and the question is always "what goes out next", never "what did June
   look like". */
.qrow{display:flex;align-items:center;gap:11px;padding:9px 12px;margin:0 0 7px;
  border:1px solid var(--line);border-radius:11px;background:var(--surface)}
.qrow .tm{width:44px;flex:none;font:600 12px/1 "Fira Code",monospace;color:var(--text)}
.qrow .sth{width:30px;height:53px;object-fit:cover;border-radius:5px;flex:none;
  border:1px solid var(--line-2)}
.qrow .sw{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.qrow .sw b{font:600 13px/1.3 system-ui}
.qrow .sw i{font-style:normal;font-size:11px;color:var(--dim)}
/* flex:none, or the label is the thing that gets squeezed off the row when
   a Cancel button is also present. */
.qrow .st{flex:none;min-width:86px;text-align:right;white-space:nowrap;
  font:500 10px/1 "Fira Code",monospace;color:var(--dim);
  text-transform:uppercase;letter-spacing:.06em}
.qrow.published{border-color:rgba(34,197,94,.35)}
.qrow.published .st{color:var(--ok)}
.qrow.failed{border-color:rgba(244,63,94,.45)}
.qrow.failed .st{color:var(--bad)}
.qrow.publishing .st{color:var(--accent)}
.iggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));
  gap:9px;margin:9px 0 0}
.igcard{padding:0;border:1px solid var(--line);border-radius:11px;overflow:hidden;
  background:var(--surface);text-align:left;color:var(--text);display:block}
.igcard:hover{border-color:var(--accent)}
.igcard img{width:100%;aspect-ratio:9/16;object-fit:cover;display:block;
  border-bottom:1px solid var(--line)}
.igcard .n{display:block;padding:8px 10px 0;font:600 12px/1.3 system-ui;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.igcard .s{display:block;padding:2px 10px 9px;font:500 10px/1.3 "Fira Code",monospace;
  color:var(--dim)}
.iggrid.pick{grid-template-columns:repeat(auto-fill,minmax(104px,1fr));
  max-height:42vh;overflow:auto;padding:2px}
.igpicked{display:flex;align-items:center;gap:11px;margin:8px 0 0;padding:9px 11px;
  border:1px solid var(--accent);border-radius:11px;background:rgba(var(--accent-rgb),.07)}
.igpicked img{width:34px;height:60px;object-fit:cover;border-radius:6px;flex:none}
.igpicked .n{flex:1;min-width:0;font:600 13px/1.35 system-ui;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.igpicked .n i{display:block;font-style:normal;font:500 10.5px/1.4 "Fira Code",monospace;
  color:var(--dim);margin-top:2px}
/* A quiet text action. "Change" and "Publish now" are not primary buttons and
   should not be shaped like the one thing you came here to press. */
.lnk{background:none;border:0;color:var(--muted);font:500 12px/1 system-ui;
  padding:7px 4px;text-decoration:underline;text-underline-offset:3px}
.lnk:hover{color:var(--accent)}
.lnk[disabled]{opacity:.4;text-decoration:none}
.igcap{width:100%;min-height:112px;resize:vertical;margin:8px 0 0;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:9px;
  color:var(--text);font:400 12.5px/1.6 system-ui;padding:9px 11px}
.igcap:focus{outline:none;border-color:var(--accent)}
.whenrow{display:grid;grid-template-columns:1.4fr 1fr;gap:8px;margin:8px 0 0}
.whenrow .cin{width:100%}
.shfoot{display:flex;align-items:center;gap:10px;justify-content:flex-end;
  padding:12px 16px;border-top:1px solid var(--line)}
.shfoot .btn[disabled]{opacity:.4;cursor:not-allowed}
.shfoot .spin{vertical-align:-2px;margin-right:5px}
.qrow .st.published{color:var(--ok)}
.qrow .st.publishing{color:var(--accent)}
/* A button stretches its content by default; without an explicit height an
   empty slot drew as tall as a filled one with a thumbnail in it. */
.qrow.empty{width:100%;height:46px;padding:0 12px;text-align:left;
  border-style:dashed;background:none;color:var(--dim)}
.qrow.empty .sw{flex-direction:row;align-items:center}
.qrow.empty:hover:not(:disabled){border-color:var(--accent);color:var(--text)}
.qrow.empty .sw i{font-style:normal;font-size:12px}
.qrow.empty.past{opacity:.4}
.qrow.empty.past:hover{border-color:var(--line)}
/* the week as a week */
.wknav{display:flex;align-items:center;justify-content:center;gap:6px;position:relative}
.wknav .lnk{position:absolute;right:0}
.wkr{min-width:132px;text-align:center;font:600 14px/1 system-ui;letter-spacing:.01em}
.wkarr{width:30px;height:30px;padding:0;border-radius:8px;border:1px solid var(--line-2);
  background:var(--surface);color:var(--muted);font:400 17px/26px system-ui}
.wkarr:hover:not(:disabled){color:var(--accent);border-color:var(--accent)}
.wkarr:disabled{opacity:.3;cursor:not-allowed}
.wknav .lnk{margin-left:4px}
.wgrid{display:grid;grid-template-columns:52px repeat(7,1fr);gap:6px;margin:6px 0 0}
.wh{padding:2px 4px 4px;text-align:center;font:600 11px/1.25 "Fira Code",monospace;
  color:var(--dim)}
.wh b{display:block;font-weight:600;color:var(--muted);text-transform:uppercase;
  letter-spacing:.06em}
.wh i{font-style:normal;font-size:14px;color:var(--text)}
.wh.today b,.wh.today i{color:var(--accent)}
.wt{display:flex;align-items:center;justify-content:flex-end;padding-right:8px;
  font:600 11px/1 "Fira Code",monospace;color:var(--dim)}
.wc{position:relative;aspect-ratio:4/5;border-radius:10px;overflow:hidden;padding:0;
  border:1px solid var(--line-2);background:var(--surface)}
.wc img{width:100%;height:100%;object-fit:cover;display:block;opacity:.85}
.wc .t{position:absolute;left:0;right:0;bottom:0;padding:14px 5px 4px;text-align:left;
  background:linear-gradient(transparent,rgba(var(--ink-rgb),.94));
  font:600 9px/1.25 system-ui;color:#e2e8f0;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wc .x{position:absolute;top:3px;right:3px;width:19px;height:19px;padding:0;
  border-radius:6px;border:0;background:rgba(var(--ink-rgb),.78);color:var(--muted);
  font:600 13px/17px system-ui;opacity:0;transition:opacity .15s}
.wc:hover .x{opacity:1}
.wc .x:hover{color:var(--bad)}
.wc.published{border-color:rgba(34,197,94,.4);cursor:pointer}
.wc.failed{border-color:rgba(244,63,94,.45)}
.wc .pill{position:absolute;top:4px;left:4px;padding:2px 6px;border-radius:6px;
  font:600 8px/1.5 "Fira Code",monospace;text-transform:uppercase;letter-spacing:.05em;
  background:rgba(var(--ink-rgb),.82)}
.wc .pill.ok{color:var(--ok)}
.wc .pill.bad{color:var(--bad)}
.wc .pill.go{color:var(--accent)}
.wstats{position:absolute;left:0;right:0;bottom:17px;display:flex;justify-content:center;
  gap:7px;padding:3px 4px;background:linear-gradient(transparent,rgba(var(--ink-rgb),.9));
  font:600 9px/1.4 "Fira Code",monospace;color:#cbd5e1}
.wstats i{font-style:normal;margin-right:2px;color:var(--dim)}

.wc.publishing{border-color:var(--accent)}
.wc.empty{border-style:dashed;background:none;color:var(--line-2);
  font:400 17px/1 system-ui}
.wc.empty:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.wc.empty.past{font:500 9px/1 "Fira Code",monospace;color:var(--dim);opacity:.45}
.weeklist{display:none}
@media (max-width:900px){ .wgrid{display:none} .weeklist{display:block} }
@media (max-width:900px){ .srow .sth{display:none} }

/* ---------- users ----------
   Distributions, not totals: "how many habits does a real user keep" is a
   shape, and a mean would hide it. */
.ukpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));
  gap:9px;margin:14px 0 0}
.ukpi{padding:13px 14px;border:1px solid var(--line);border-radius:12px;
  background:var(--surface)}
.ukpi b{display:block;font:600 25px/1.1 system-ui;letter-spacing:-.02em}
.ukpi span{display:block;margin-top:5px;font-size:12px;color:var(--muted)}
.ukpi i{display:block;margin-top:3px;font-style:normal;font-size:11px;color:var(--dim)}
.ugrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
  gap:10px;margin:14px 0 0}
.ubox{padding:13px 14px;border:1px solid var(--line);border-radius:12px;
  background:var(--surface)}
.ubox h4{margin:0 0 9px;font:600 13px/1.3 system-ui}
.ubar{display:flex;align-items:center;gap:9px;margin:0 0 5px}
.ubar .l{width:56px;flex:none;font:500 10.5px/1 "Fira Code",monospace;color:var(--dim)}
.ubar .l.bad{color:var(--bad)}
.ubar .fl{width:150px;flex:none;font-size:11.5px;color:var(--muted)}
.ubar .t i.bad{background:var(--bad)}
.ubox.wide{grid-column:1/-1;margin:14px 0 0}
.ubox .csum i{font-style:normal;color:var(--dim)}
.ubar .t{flex:1;height:8px;border-radius:4px;background:var(--surface-2);overflow:hidden}
.ubar .t i{display:block;height:100%;background:var(--accent);border-radius:4px}
.ubar .v{width:34px;flex:none;text-align:right;font:500 11px/1 "Fira Code",monospace;
  color:var(--muted)}

/* The fast path, first thing on the page: everything the rules can decide,
   decided, and then straight out. The cards below are for having a say. */
.fastrow{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
/* Status on the left, the week you are looking at dead centre. The centre
   column is sized by its content so the range stays centred on the page
   however long the status text runs. */
.ighead{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
  gap:12px;margin:2px 0 0}
@media(max-width:900px){.ighead{grid-template-columns:1fr;gap:8px}}
.btn.qd{font-weight:600}
.slbgwrap{position:relative;flex:none;width:84px;align-self:flex-start}
/* Without align-self the wrapper stretches to the card's height and the
   re-roll lands under the photo instead of on it. */
.reroll{position:absolute;right:4px;bottom:4px;width:24px;height:24px;padding:0;
  border-radius:7px;border:1px solid var(--line-2);background:rgba(var(--ink-rgb),.82);
  color:var(--muted);font-size:13px;line-height:22px}
.reroll:hover{color:var(--accent);border-color:var(--accent)}
@media (max-width:900px){ .slbgwrap{width:66px} }

.slrows{display:flex;flex-direction:column;gap:10px;margin:12px 0 0}
.slrow{display:flex;gap:13px;padding:12px;border:1px solid var(--line);
  border-radius:13px;background:var(--surface)}
.slbg{position:relative;width:84px;flex:none;aspect-ratio:9/16;border-radius:9px;
  overflow:hidden;padding:0;border:1px dashed var(--line-2);background:var(--surface-2)}
.slbg.has{border-style:solid;border-color:var(--line-2)}
.slbg img{width:100%;height:100%;object-fit:cover;display:block}
.slbg .lab{position:absolute;left:0;right:0;bottom:0;padding:10px 3px 3px;
  background:linear-gradient(transparent,rgba(var(--ink-rgb),.92));
  font:500 8px/1.2 "Fira Code",monospace;color:#cbd5e1}
.slbg .pick{display:block;padding:0 6px;color:var(--dim);font:500 10px/1.35 "Fira Code",monospace}
.slbg:hover{border-color:var(--accent)}
.slmain{flex:1;min-width:0;display:flex;flex-direction:column;gap:7px}
.slhead{display:flex;align-items:center;gap:8px}
.slhead .k{font:600 10px/1 "Fira Code",monospace;text-transform:uppercase;
  letter-spacing:.07em;color:var(--dim)}
.slhead .rm{margin-left:auto;background:none;border:0;color:var(--dim);
  font-size:17px;padding:0 4px;line-height:1}
.slhead .rm:hover{color:var(--bad)}
.slact{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.gbusy{font:500 11px/1 "Fira Code",monospace;color:var(--accent)}
.slrow.hook{border-color:var(--line-2)}
.slrow.k-cta{opacity:.92}

.cin{width:100%;background:var(--surface-2);border:1px solid var(--line-2);
  border-radius:9px;color:var(--text);font:400 13px/1.5 system-ui;padding:8px 11px}
.cin.big{font-size:14.5px}
.cin.wide{display:block;margin:8px 0 0}
.cin:focus{outline:none;border-color:var(--accent)}
.cin::placeholder{color:var(--dim)}
.cx textarea{width:100%;min-height:76px;resize:vertical;margin:8px 0 0;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:9px;
  color:var(--text);font:400 13px/1.6 system-ui;padding:9px 11px}
.cx textarea:focus{outline:none;border-color:var(--accent)}
.cx textarea::placeholder{color:var(--dim)}

/* hook cards read as the slide reads: two lines, lowercase, one size */
.hgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(206px,1fr));gap:8px;margin:8px 0 0}
.hk{border:1px solid var(--line-2);border-radius:10px;background:var(--surface-2);
  padding:12px 13px;text-align:left;color:var(--text);font:400 13px/1.45 system-ui}
.hk:hover{border-color:var(--muted)}
.hk.sug{border-style:dashed}
.hk.sug .p{color:var(--accent)}
.hk .p{display:block;margin-top:7px;font:500 9.5px/1 "Fira Code",monospace;
  color:var(--dim);text-transform:uppercase;letter-spacing:.07em}

/* the gallery, inside the sheet. 9:16 because that is the shape they become */
.bgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px;
  margin:11px 0 0;padding:2px}
.bt{position:relative;aspect-ratio:9/16;border-radius:9px;overflow:hidden;padding:0;
  border:1px solid var(--line-2);background:var(--surface-2)}
.bt img{width:100%;height:100%;object-fit:cover;display:block}
.bt.on{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent)}
/* Not hidden: a rule-breaking photo can still be the right call, it just has
   to be a decision rather than an accident. */
.bt.faded{opacity:.42}
.bt.faded:hover{opacity:1}
.bt .fl{position:absolute;top:5px;right:5px;display:flex;flex-direction:column;gap:3px;align-items:flex-end}
.bt .fl i{font-style:normal;font:600 8.5px/14px "Fira Code",monospace;padding:0 4px;
  border-radius:4px;background:rgba(var(--ink-rgb),.82);color:var(--muted)}
.bt .fl i.warn{color:var(--warn)}
.bt .vb{position:absolute;left:0;right:0;bottom:0;padding:14px 5px 4px;text-align:left;
  background:linear-gradient(transparent,rgba(var(--ink-rgb),.92));
  font:500 8.5px/1.25 "Fira Code",monospace;color:#cbd5e1}

/* tools: the icon is how you recognise one, so the icon leads */
.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:7px;margin:8px 0 0}
.tl{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:9px;
  border:1px solid var(--line-2);background:var(--surface-2);color:var(--text);
  font:500 12px/1.25 system-ui;text-align:left;width:100%}
.tl img,.tl .noico{width:22px;height:22px;border-radius:6px;flex:none}
.tl .noico{background:var(--line-2)}
.tl.on{border-color:var(--accent);background:rgba(var(--accent-rgb),.1)}
.tl.faded{opacity:.45}
.tl .tnum{margin-left:auto;font:700 10px/1 "Fira Code",monospace;color:var(--accent)}
.tl .tnum.warn{color:var(--warn);font-weight:600}
.slmain>.tl{width:auto;align-self:flex-start}

/* the sheet: a picker over the post, not a page you navigate to */
.shwrap{position:fixed;inset:0;z-index:var(--z-modal);background:rgba(var(--ink-rgb),.72);
  display:flex;align-items:flex-end;justify-content:center;padding:24px}
.sh.narrow{width:min(460px,100%)}
.sh{width:min(760px,100%);max-height:86vh;display:flex;flex-direction:column;
  background:var(--surface);border:1px solid var(--line-2);border-radius:15px;
  box-shadow:0 24px 60px rgba(var(--ink-rgb),.7)}
.shhead{display:flex;align-items:center;gap:10px;padding:14px 16px;
  border-bottom:1px solid var(--line);font:600 14px/1 system-ui}
.shhead .rm{margin-left:auto;background:none;border:0;color:var(--dim);font-size:21px;
  line-height:1;padding:0 4px}
.shhead .rm:hover{color:var(--text)}
.shbody{padding:4px 16px 18px;overflow:auto}

/* the bar follows you down the page: what you have, and the one button */
.cbar{position:sticky;bottom:8px;display:flex;align-items:center;gap:11px;flex-wrap:wrap;
  margin:16px 0 0;padding:12px 14px;background:var(--surface);
  border:1px solid var(--line-2);border-radius:13px;box-shadow:0 8px 24px rgba(var(--ink-rgb),.55)}
.cbar .sum{flex:1;min-width:170px;font-size:12px;color:var(--dim);line-height:1.45}
@media (max-width:900px){
  .slrow{padding:10px;gap:10px}
  .slbg{width:66px}
  .bgrid{grid-template-columns:repeat(auto-fill,minmax(76px,1fr))}
  .hgrid{grid-template-columns:1fr}
  .tgrid{grid-template-columns:repeat(auto-fill,minmax(116px,1fr))}
  .shwrap{padding:0}
  .sh{max-height:92vh;border-radius:15px 15px 0 0}
  .cbar{position:sticky;bottom:0;border-radius:13px 13px 0 0}
}
.runpill.bad{border-color:var(--bad);color:var(--bad)}
.toast .bad{color:var(--bad);font-weight:700}
.trow.fail{align-items:flex-start}
.trow.fail i{display:block;margin-top:3px;font-style:normal;font-size:11px;
  color:var(--dim);line-height:1.45}
.trow.fail .rt{margin-left:auto;align-self:flex-start;flex:none;
  padding:5px 11px;font-size:11.5px}
#stalebar{padding:11px 16px;background:rgba(251,146,60,.12);
  border-bottom:1px solid rgba(251,146,60,.4);color:var(--muted);
  font:400 12.5px/1.5 system-ui}
#stalebar b{color:var(--warn);font-weight:600}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.brand .v{font-size:11px;color:var(--dim)}
nav{display:flex;flex-direction:column;gap:2px}
.navlabel{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);
  padding:0 8px;margin:0 0 8px}
.nav{display:flex;align-items:center;gap:10px;width:100%;text-align:left;background:none;
  border:0;color:var(--muted);padding:9px 10px;border-radius:8px;min-height:40px;
  transition:background .18s,color .18s}
.nav:hover{background:var(--surface-2);color:var(--text)}
.nav[aria-current="true"]{background:rgba(var(--accent-rgb),.1);color:var(--accent);
  font-weight:500;border-radius:0 3px 3px 0}
.nav[aria-current="true"] svg{opacity:1}
.nav[aria-current="true"] .ct{color:var(--accent)}
.nav svg{width:17px;height:17px;flex:none;opacity:.9}
.nav .ct{margin-left:auto;font-size:11px;color:var(--dim);font-family:"Fira Code",monospace}

/* ---------- accounts ---------- */
.accounts{margin-top:auto;display:flex;flex-direction:column;gap:9px}
.acct{display:block;text-decoration:none;background:var(--surface-2);
  border:1px solid var(--line-2);border-radius:var(--r);padding:11px 12px;
  transition:border-color .15s}
.acct:hover{border-color:var(--accent)}
/* The card is a filter, so it has to look switched on when it is one. */
.acct.sel{border-color:var(--accent);
  box-shadow:0 0 0 1px var(--accent) inset,0 0 22px -12px var(--glow)}
.astat{display:flex;align-items:baseline;gap:6px;margin-top:7px}
.astat b{font:600 20px/1 "Fira Code",monospace;color:var(--text)}
.astat span{font-size:10.5px;color:var(--dim)}
.astat i{margin-left:auto;font:600 11px/1 "Fira Code",monospace;font-style:normal}
.astat i.up{color:var(--ok)} .astat i.down{color:var(--bad)}
.arow{display:flex;justify-content:space-between;margin-top:8px;
  font-size:10.5px;color:var(--dim)}
.acct .top{display:flex;align-items:center;gap:8px}
.acct svg{width:15px;height:15px;flex:none}
.acct .h{font-size:12px;font-weight:600;color:var(--text);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acct .num{margin-left:auto;font-size:11px;font-family:"Fira Code",monospace;color:var(--muted)}
.track{height:4px;background:#0b1120;border-radius:3px;margin-top:9px;overflow:hidden}
.track i{display:block;height:100%;background:var(--accent);transition:width .25s}
.track.full i{background:var(--bad)}
.acct button{margin-top:8px;width:100%;background:none;border:1px solid var(--line-2);
  color:var(--muted);border-radius:7px;padding:5px;font-size:11px;min-height:30px;
  transition:border-color .18s,color .18s}
.acct button:hover{border-color:var(--accent);color:var(--text)}

/* The cadence line. One post an hour is the target, so the only question the
   sidebar has to answer is "can I post to this account yet" — the colour is
   the answer and the elapsed time is the evidence. */
.cad{display:flex;align-items:center;gap:7px;margin-top:8px;
  font:600 10px/1 "Fira Code",monospace;letter-spacing:.06em;text-transform:uppercase}
.cad::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--cc);
  box-shadow:0 0 9px -1px var(--cc);flex:none}
.cad b{font-weight:700;color:var(--cc)}
.cad span{margin-left:auto;color:var(--dim);font-weight:500;letter-spacing:.04em;
  text-transform:none}
/* Both ends of the range are mistakes, so both pulse. The middle sits still. */
@keyframes cadpulse{0%,100%{opacity:1}50%{opacity:.45}}
.cad.soon::before,.cad.over::before{animation:cadpulse 1.8s ease-in-out infinite}
.cad.soon{--cc:#7DA2FF}
.cad.now{--cc:var(--ok)}
.cad.late{--cc:#F5B945}
.cad.over{--cc:var(--bad)}
.cad.never{--cc:var(--dim)}

/* ---------- main ---------- */
main{overflow:auto}
.bar{position:sticky;top:0;z-index:10;background:rgba(var(--ink-rgb),.92);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);padding:18px 28px;display:flex;align-items:center;gap:16px}
h1{font-size:17px;font-weight:600;margin:0;letter-spacing:.01em}
.sub{color:var(--dim);font-size:12px}
.wrap{padding:14px 28px 60px}

/* Accent picker. Every colour on the page derives from --accent-rgb, so
   the whole theme turns on one value. */
.cpick{position:relative;flex:none}
.cpdot{width:26px;height:26px;border-radius:50%;border:1px solid var(--line-2);
  background:var(--accent);cursor:pointer;padding:0;display:block;
  box-shadow:0 0 14px -3px var(--glow);transition:transform .16s ease}
.cpdot:hover{transform:scale(1.1)}
.cppop{position:absolute;right:0;top:34px;z-index:60;width:212px;padding:12px;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:var(--r);
  box-shadow:0 18px 44px -12px #000,0 0 26px -12px var(--glow)}
.cppop[hidden]{display:none}
.cppop .lbl{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--dim);margin:0 0 8px}
.cpsw{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:11px}
.cpsw button{width:100%;aspect-ratio:1;border-radius:50%;border:1px solid transparent;
  cursor:pointer;padding:0}
.cpsw button[aria-pressed="true"]{border-color:#fff;
  box-shadow:0 0 0 2px var(--surface-2),0 0 0 3px currentColor}
.cprow{display:flex;gap:8px;align-items:center}
.cprow input[type=color]{width:34px;height:30px;padding:0;border:1px solid var(--line-2);
  border-radius:var(--r);background:none;cursor:pointer}
.cprow .btn{flex:1;justify-content:center}

/* ---------- ideas: the map ----------
   A pannable surface with bubbles on it. Everything is positioned in map
   coordinates inside .mmin, which is the only thing that moves when you pan —
   so a bubble's stored x/y never has to know where the viewport is. */
.mmwrap{position:relative}
.mmbar{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin:0 0 11px}
.mmhint{flex:1;min-width:180px;font-size:11.5px;color:var(--dim)}
.kchips{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.kchip{background:none;border:1px solid var(--line);border-radius:7px;cursor:pointer;
  color:var(--muted);font:600 10.5px/1 "Fira Code",monospace;letter-spacing:.06em;
  text-transform:uppercase;padding:6px 8px;display:flex;align-items:center;gap:6px;
  transition:color .15s,border-color .15s}
.kchip::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--kc)}
.kchip.add::before{display:none}
.kchip:hover{color:var(--text);border-color:var(--line-2)}
.kchip.on{color:var(--text);border-color:var(--kc);
  box-shadow:0 0 0 1px var(--kc) inset,0 0 14px -6px var(--kc)}
.kin{width:104px;background:var(--surface-2);border:1px solid var(--accent);
  border-radius:7px;color:var(--text);font:600 10.5px/1 "Fira Code",monospace;
  padding:7px 8px;text-transform:uppercase}
.kin:focus{outline:none}

.mmap{position:relative;overflow:hidden;touch-action:none;cursor:grab;
  height:calc(100vh - 232px);min-height:440px;
  background:var(--surface);border:1px solid var(--line);border-radius:14px}
.mmap:active{cursor:grabbing}
.mmin{position:absolute;inset:0;will-change:transform;transform-origin:0 0}
.mmlines{position:absolute;left:-4000px;top:-4000px;width:8000px;height:8000px;
  overflow:visible;pointer-events:none}
/* the svg is offset, so the paths are too — cancel it on the group */
.mmlines path{transform:translate(4000px,4000px)}
.mmempty{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;text-align:center;line-height:1.7;
  color:var(--dim);font-size:13px;pointer-events:none}

.bub{position:absolute;width:186px;box-sizing:border-box;cursor:grab;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:11px;
  padding:9px 10px;display:flex;flex-direction:column;gap:6px;
  box-shadow:0 10px 26px -14px #000;transition:box-shadow .16s,border-color .16s}
.bub:hover{border-color:var(--kc)}
.bub.sel{border-color:var(--kc);box-shadow:0 0 0 1px var(--kc),0 0 26px -10px var(--kc)}
.bub.target{border-style:dashed}
.bub:active{cursor:grabbing}
.bkind{display:flex;align-items:center;gap:5px;
  font:700 8.5px/1 "Fira Code",monospace;letter-spacing:.14em;
  text-transform:uppercase;color:var(--kc);opacity:.85}
.bkind::before{content:"";width:6px;height:6px;border-radius:50%;
  background:var(--kc);flex:none}
/* In the inspector it keeps its box — there it is a heading, not a tag. */
.mmins .bkind{border:1px solid var(--kc);border-radius:5px;padding:4px 6px;opacity:1}
.bub .btx{font-size:12.5px;line-height:1.5;color:var(--text);word-break:break-word;
  display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
.bub .bpic{width:100%;max-height:132px;object-fit:cover;border-radius:7px;display:block}
.bub .btx.ph{color:var(--dim);font-style:italic}
/* Typing happens on the bubble. The box is invisible so the bubble does not
   change shape the moment you click into it. */
.bed{width:100%;box-sizing:border-box;background:none;border:0;padding:0;resize:none;
  color:var(--text);font:400 12.5px/1.5 system-ui;overflow:hidden;min-height:38px}
.bed:focus{outline:none}
.bub .bed::placeholder{color:var(--dim)}

.zoomer{display:flex;align-items:center;gap:2px;border:1px solid var(--line);
  border-radius:8px;padding:2px}
.zoomer button{width:26px;height:24px;background:none;border:0;cursor:pointer;
  color:var(--muted);font:500 15px/1 system-ui;border-radius:6px}
.zoomer button:hover{color:var(--accent);background:rgba(var(--accent-rgb),.08)}
.zoomer span{min-width:38px;text-align:center;font:600 10.5px/1 "Fira Code",monospace;
  color:var(--dim)}
/* A head title is the thing everything else hangs off, so it looks like one. */
.bub.k-title{width:214px;background:var(--surface);border-width:2px;
  align-items:center;text-align:center}
.bub.k-title .btx{font-size:15px;font-weight:600;line-height:1.35;text-align:center}
.bub.k-title .bed{text-align:center;font-size:15px;font-weight:600}

/* The four handles. They sit outside the bubble's box and only appear when
   the pointer is on it, so the board is quiet until you reach for a branch. */
.hnd{position:absolute;width:20px;height:20px;border-radius:50%;padding:0;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  background:var(--surface-2);border:1px solid var(--kc);color:var(--kc);
  font:600 13px/1 system-ui;opacity:0;transition:opacity .14s,transform .14s;
  z-index:3}
.bub:hover .hnd,.bub.sel .hnd{opacity:.75}
.hnd:hover{opacity:1;transform:scale(1.18);
  background:var(--kc);color:var(--bg)}
.hnd.n{top:-11px;left:50%;margin-left:-10px}
.hnd.s{bottom:-11px;left:50%;margin-left:-10px}
.hnd.e{right:-11px;top:50%;margin-top:-10px}
.hnd.w{left:-11px;top:50%;margin-top:-10px}

/* The inspector, not an inline editor: editing in place on a draggable thing
   fights the drag on every click. */
.mmins{position:absolute;right:14px;top:60px;width:264px;z-index:12;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:13px;
  padding:13px;display:flex;flex-direction:column;gap:9px;
  box-shadow:0 22px 50px -18px #000,0 0 24px -14px var(--glow)}
.mmins .ihead{display:flex;align-items:center;justify-content:space-between}
.mmins .rm{background:none;border:0;color:var(--dim);font-size:17px;cursor:pointer;
  line-height:1;padding:0 2px}
.mmins .rm:hover{color:var(--text)}
.mmins textarea{min-height:92px;resize:vertical;background:var(--surface);
  border:1px solid var(--line);border-radius:8px;color:var(--text);
  font:400 13px/1.55 system-ui;padding:9px 10px}
.mmins textarea:focus{outline:none;border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(var(--accent-rgb),.12)}
.mmins .iref{width:100%;border-radius:8px;display:block;cursor:zoom-in}
.mmins .ilab{margin:2px 0 0;font:700 9.5px/1 "Fira Code",monospace;
  letter-spacing:.13em;text-transform:uppercase;color:var(--dim)}
.mmins .iacts{display:flex;gap:6px;flex-wrap:wrap;margin-top:2px}
.mmins .iacts button{background:none;border:1px solid var(--line);border-radius:7px;
  color:var(--muted);font:600 10.5px/1 system-ui;padding:7px 9px;cursor:pointer;
  transition:color .15s,border-color .15s}
.mmins .iacts button:hover{color:var(--accent);border-color:var(--accent)}
.mmins .iacts button.warn:hover{color:var(--bad);border-color:var(--bad)}
.mmins .ifoot{margin:0;font-size:10.5px;color:var(--dim)}
@media(max-width:900px){.mmins{position:static;width:auto;margin-top:11px}}

/* ---------- cards ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(172px,1fr));gap:12px}
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
.sl .num{position:absolute;top:7px;left:7px;background:rgba(var(--ink-rgb),.82);color:var(--text);
  font:500 11px/1 "Fira Code",monospace;padding:4px 7px;border-radius:6px}
.sl[aria-pressed="true"] img{border-color:var(--accent);box-shadow:0 0 0 2px rgba(var(--accent-rgb),.35)}
.sl[aria-pressed="true"] .num{background:var(--accent);color:#04222f}
.del{position:absolute;top:8px;right:8px;width:32px;height:32px;border-radius:8px;
  background:rgba(var(--ink-rgb),.72);border:1px solid var(--line-2);color:var(--muted);
  display:flex;align-items:center;justify-content:center;opacity:.5;z-index:2;
  transition:opacity .18s,color .18s,border-color .18s}
.cardwrap:hover .del{opacity:1}
.del:hover{color:var(--bad);border-color:var(--bad)}
.del svg{width:15px;height:15px}
.cardwrap{position:relative}
/* Set by the sync from real view counts, never by hand. Solid, because a
   translucent badge takes its colour from whatever photograph is behind it,
   and the colour is the thing carrying the tier. */
.tier{position:absolute;top:8px;left:8px;z-index:2;padding:4px 9px;border-radius:7px;
  font:700 11px/1 "Fira Code",monospace;letter-spacing:.02em;
  color:#04121f;background:#38bdf8;border:0;
  box-shadow:0 2px 10px rgba(0,0,0,.45)}
/* Cool to hot as the number climbs, so a grid reads by colour before it is
   read by digits. */
.tier.t1{background:#38bdf8}                    /* 1k  */
.tier.t2{background:#22d3ee}                    /* 2k  */
.tier.t3{background:#34d399}                    /* 3k  */
.tier.t4{background:#facc15}                    /* 5k  */
.tier.t5{background:#fb923c}                    /* 10k */
.tier.t6{background:#f43f5e;color:#fff}         /* 25k */
/* In the footer, not beside the title: the numbers are the outcome of the
   post, not part of naming it. Values bold and light, units dim, so the row
   reads as three numbers rather than six words. */
/* Two actions of equal weight: they split the footer rather than one
   hugging the stats and the other the edge. */
/* A row named by its caption is one we could not tie to a post. Saying so
   beats leaving it to be inferred from the shape of the name. */
.idtag{margin-left:9px;padding:2px 7px;border-radius:5px;vertical-align:2px;
  font:600 9.5px/1.5 system-ui;letter-spacing:.05em;text-transform:uppercase;
  background:rgba(var(--accent-rgb),.13);border:1px solid var(--accent);color:var(--accent)}
.idtag.weak{background:rgba(251,146,60,.13);border-color:var(--warn);color:var(--warn)}
.unk{display:inline-flex;align-items:center;justify-content:center;
  width:15px;height:15px;margin-right:7px;border-radius:50%;vertical-align:-2px;
  font:700 10px/1 system-ui;background:var(--surface-2);
  border:1px solid var(--line-2);color:var(--dim);cursor:help}
.acts{display:flex;gap:7px;flex:1;margin-left:auto}
.acts .cta{flex:1;text-align:center}
.cstat{display:flex;align-items:baseline;gap:5px;margin-right:auto;
  font:500 11px/1 "Fira Code",monospace;color:var(--dim)}
.cstat b{font-weight:600;font-size:12.5px;color:var(--text)}
.cstat b + span{margin-right:6px}
.cstat b.r{color:var(--ok)}
.livestat{display:inline-flex;align-items:center;gap:11px;
  font:500 13px/1 "Fira Code",monospace;color:var(--text)}
.livestat .r{color:var(--dim)}
.tier.inline{position:static;backdrop-filter:none}
.chip{font:500 10.5px/1 "Fira Code",monospace;padding:5px 8px;border-radius:6px;
  border:1px solid var(--line-2);background:var(--surface-2);color:var(--dim);
  letter-spacing:.01em;transition:all .14s;white-space:nowrap}
.chip.drf{color:var(--accent);border-color:#14405a;background:rgba(var(--accent-rgb),.09);cursor:pointer}
.chip.drf:hover{background:rgba(var(--accent-rgb),.22)}
.chip.pub{color:var(--ok);border-color:#14532d;background:rgba(34,197,94,.10);cursor:pointer}
.chip.err{color:var(--bad);border-color:#5c1626}
.cfoot{display:flex;align-items:center;gap:7px;padding:9px 11px;border-top:1px solid var(--line);
  background:var(--surface);min-height:40px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:10px;margin:0 0 26px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;
  padding:14px 16px 15px;display:flex;flex-direction:column;min-height:104px}
.kpi .l{font:500 10px/1 system-ui;color:var(--dim);text-transform:uppercase;
  letter-spacing:.09em;margin-bottom:auto}
.kpi .n{font:600 30px/1 "Fira Code",monospace;color:var(--text);margin:14px 0 0;
  letter-spacing:-.02em}
.kpi .n.good{color:var(--ok)} .kpi .n.warn{color:var(--warn)}
.kpi .n small{font-size:15px;color:var(--dim);font-weight:500;margin-left:2px}
.kpi .s{font-size:10.5px;color:var(--dim);margin-top:6px;line-height:1.4}
.d{font:600 10.5px/1 "Fira Code",monospace;margin-right:5px}
.d.up{color:var(--ok)} .d.down{color:var(--bad)}
.d.flat,.d.none{color:var(--dim)}
.periods{display:flex;align-items:center;gap:8px;margin:0 0 12px;flex-wrap:wrap}
.pillp{background:var(--surface-2);border:1px solid var(--line-2);color:var(--muted);
  font:500 12px/1 system-ui;padding:9px 16px;border-radius:20px;cursor:pointer}
.pillp:hover{color:var(--text)}
.pillp.on{background:var(--text);color:var(--bg);border-color:var(--text)}
.range{font-size:11.5px;color:var(--dim);margin:0 0 16px}
.acctfilter{display:flex;gap:6px;margin-left:auto}
.pilla{display:inline-flex;align-items:center;gap:7px;background:var(--surface-2);
  border:1px solid var(--line-2);color:var(--text);font:500 11.5px/1 system-ui;
  padding:8px 12px;border-radius:20px;cursor:pointer;transition:opacity .15s,color .15s}
.pilla i{width:9px;height:9px;border-radius:50%;border:1.5px solid;display:inline-block}
/* Deselected reads as switched off: dimmed and hollow, not another colour. */
.pilla.off{background:transparent;color:var(--dim);opacity:.45}
.pilla.off:hover{opacity:.8}
@media(max-width:900px){.acctfilter{margin-left:0;width:100%}}
/* Six tiles in an auto-fit grid landed 5 + 1. Fixed column counts that divide
   six evenly keep every row full at any width. */
.mgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin:0 0 22px}
@media(min-width:1500px){.mgrid{grid-template-columns:repeat(6,1fr)}}
@media(max-width:1100px){.mgrid{grid-template-columns:repeat(2,1fr)}}
.mtile{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:16px 17px}
.ml{font-size:12px;color:var(--muted);margin-bottom:9px}
.mn{font:600 30px/1 "Fira Code",monospace;color:var(--text);letter-spacing:-.02em}
.md{font:500 12px/1 system-ui;margin-top:10px;display:flex;align-items:baseline;gap:5px}
.md span{color:var(--dim);font-size:11px}
.md.up{color:var(--ok)} .md.down{color:var(--bad)}
.md.flat,.md.none{color:var(--dim)}
/* This table is read at a glance to answer one question — which account is
   worth publishing to first — so its numbers are foreground, not chrome. */
.mx.cmp td{padding:13px 10px}
.mx.cmp td.n .sp{color:var(--text);font-size:12.5px}
.mx.cmp .t{font-weight:600;font-size:13.5px}
.mx.cmp th{font-size:10px;letter-spacing:.1em;padding-bottom:10px;white-space:nowrap}
.mx.cmp .hr{font:700 17px/1 "Fira Code",monospace;color:var(--text)}
/* Green down to red on the figure itself, so the column can be read at a
   glance without comparing rows to each other. */
.mx.cmp .hr.r4{color:var(--ok)}
.mx.cmp .hr.r3{color:#A3E635}
.mx.cmp .hr.r2{color:#F5B945}
.mx.cmp .hr.r1{color:var(--bad)}
.best{margin-left:9px;padding:3px 7px;border-radius:5px;vertical-align:2px;
  font:600 9px/1 system-ui;letter-spacing:.07em;text-transform:uppercase;
  white-space:nowrap;
  background:rgba(var(--accent-rgb),.15);border:1px solid var(--accent);color:var(--accent)}
.worst{margin-left:9px;font:500 10.5px/1 system-ui;color:var(--dim);white-space:nowrap}
.mx.cmp .t i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:9px}
.mx.cmp b{font:600 14px/1 "Fira Code",monospace;color:var(--text)}
.mx.cmp tr.lead td{background:rgba(var(--accent-rgb),.05)}
.mx.cmp tr.lead b{color:var(--accent)}
.sp.paid{color:var(--warn)}
.kpi .accs{display:flex;flex-direction:column;gap:3px;margin-top:12px}
.kpi .accs div{display:flex;justify-content:space-between;align-items:baseline;
  font:500 11px/1 system-ui;color:var(--muted)}
.kpi .accs b{font:600 14px/1 "Fira Code",monospace;color:var(--text)}
/* ---------- pillar bars: rates compared by length, not by slice ---------- */
.pcard.warn{border-color:rgba(251,146,60,.45)}
.pcard.warn h4{color:var(--warn)}
.tight .ir.bad{color:var(--warn)}
.tight .il.go{cursor:pointer;text-decoration:underline;text-decoration-style:dotted}
.tight li .cta{margin-left:10px;flex:none}
.pbar{display:flex;align-items:center;gap:12px;padding:7px 0}
.pbar .pn{flex:0 0 130px;font:500 12px/1 system-ui;color:var(--muted);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-transform:capitalize}
.pbar .pt{flex:1;height:9px;border-radius:5px;background:var(--surface-2);overflow:hidden}
.pbar .pt i{display:block;height:100%;background:var(--accent);border-radius:5px}
.pbar .pv{flex:0 0 44px;text-align:right;font:600 12px/1 "Fira Code",monospace;color:var(--text)}
.pbar .ps{flex:0 0 66px;text-align:right;font:400 11px/1 "Fira Code",monospace;color:var(--dim)}
.pbar.thin{opacity:.45}
@media (max-width:900px){ .pbar .pn{flex-basis:88px} .pbar .ps{display:none} }

/* ---------- published: the date-cohort browser ---------- */
.rlab{font:600 12px/1 system-ui;color:var(--dim);margin-right:4px;
  text-transform:uppercase;letter-spacing:.06em}
.cust{display:inline-flex;align-items:center;gap:7px;margin-left:6px;flex-wrap:wrap}
.cust .dash{font:400 11.5px/1 system-ui;color:var(--dim)}
.cust .btn{padding:7px 13px;font-size:12px}
.cust .btn[disabled]{opacity:.4;cursor:not-allowed}
.cust .sub{font-size:11px}
.cust input{background:var(--surface-2);border:1px solid var(--line-2);color:var(--text);
  border-radius:8px;padding:6px 8px;font:500 12px/1 system-ui;color-scheme:dark}
.plist{display:flex;flex-direction:column;gap:6px;margin-top:14px}
/* Mirrors .prow's flex layout exactly so the labels sit over their columns.
   The children are spans, so each one that carries a width needs an explicit
   display — inline spans ignore it and the whole header slides left. */
.phead{display:flex;align-items:center;gap:12px;padding:2px 12px 5px;
  border:1px solid transparent;
  font:500 10px/1 system-ui;letter-spacing:.09em;text-transform:uppercase;color:var(--dim)}
.phead .pth{display:block;background:none;height:auto}
.phead .pnm{display:block;flex:1;min-width:0}
.phead .pcells{display:flex;gap:6px;flex:none}
.phead .pc{display:inline-flex;background:none;border:0;
  padding:0 9px;color:var(--dim);font:500 10px/1 system-ui;
  letter-spacing:.06em;text-transform:uppercase;overflow:hidden;white-space:nowrap}
.phead .peng{display:flex;gap:9px;flex:none}
.phead .peng span{display:block;min-width:30px;text-align:right;color:var(--muted)}
.phead .prate{display:block;min-width:48px;text-align:right}
.prow{display:flex;align-items:center;gap:12px;padding:9px 12px;cursor:pointer;
  background:var(--surface);border:1px solid var(--line);border-radius:11px}
.prow:hover{border-color:var(--line-2);background:var(--surface-2)}
.pth{width:38px;height:52px;flex:none;border-radius:6px;overflow:hidden;background:#0b1120}
.pth img{width:100%;height:100%;object-fit:cover;display:block}
.pnm{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.pnm b{font:600 13px/1.2 system-ui;color:var(--text);overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.pnm span{font:400 11px/1 "Fira Code",monospace;color:var(--dim)}
.daypill{display:inline-block;padding:2px 7px;margin-right:6px;border-radius:6px;
  border:1px solid;font:600 10.5px/1.5 "Fira Code",monospace;letter-spacing:.01em;
  vertical-align:1px}
.paid{color:var(--warn);font-style:normal}
/* Per account, side by side. Summing them would hide the 30x spread, which
   is the only thing three accounts running one post can teach you. */
.pcells{display:flex;gap:6px;flex:none}
.pc{display:inline-flex;align-items:center;gap:5px;flex:0 0 78px;justify-content:flex-end;
  padding:6px 9px;border-radius:8px;background:var(--surface-2);border:1px solid var(--line);
  font:500 12px/1 "Fira Code",monospace;color:var(--muted);text-decoration:none}
.pc i{width:6px;height:6px;border-radius:50%;flex:none}
.pc.hot{color:var(--text);border-color:var(--accent);background:rgba(var(--accent-rgb),.12)}
.pc.none{color:var(--line-2);justify-content:center}
.peng{display:flex;gap:9px;flex:none;font:500 12px/1 "Fira Code",monospace;color:var(--dim)}
.peng span{min-width:30px;text-align:right}
.prate{flex:none;min-width:48px;text-align:right;font:500 12px/1 "Fira Code",monospace;
  color:var(--dim)}
.prate.good{color:var(--ok)}
@media (max-width:900px){
  /* The row keeps its meaning at 393px by dropping to two lines rather than
     shrinking every column until none of them can be read. */
  .phead{display:none}
  .prow{flex-wrap:wrap;gap:9px;padding:9px 10px}
  .pnm{flex:1 1 auto}
  .pcells{order:3;width:100%;justify-content:flex-start}
  .pc{flex:1;min-width:0;justify-content:center}
  .peng{order:2;margin-left:auto}
  .prate{order:2;min-width:0}
  .rlab{width:100%;margin:0 0 2px}
  .cust{margin-left:0;width:100%}
  .cust input{flex:1;min-width:0}
}
.tabsel{display:none;background:var(--surface-2);border:1px solid var(--line-2);
  color:var(--text);border-radius:9px;padding:9px 11px;font:600 13px/1 system-ui;
  cursor:pointer;appearance:none;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round'><path d='m6 9 6 6 6-6'/></svg>");
  background-repeat:no-repeat;background-position:right 9px center;background-size:15px;
  padding-right:30px}
.subtabs{display:flex;align-items:center;gap:4px;margin:0 0 4px;padding-bottom:14px;
  border-bottom:1px solid var(--line)}
.sub{background:none;border:0;color:var(--muted);font:500 13px/1 system-ui;
  padding:9px 14px;border-radius:8px;cursor:pointer}
.sub:hover{color:var(--text);background:var(--surface)}
.sub.on{background:var(--surface-2);color:var(--accent)}
.sub.ghost{margin-left:auto;font-size:11.5px;color:var(--dim);
  border:1px solid var(--line-2);display:inline-flex;align-items:center;gap:7px}
.sub.ghost:hover{color:var(--text)}
.sub.ghost:disabled{opacity:.85;cursor:default}
.sub.ghost .spin{width:11px;height:11px;border-width:2px}
.sub.ghost .ok{font-size:12px}
.sect{display:flex;align-items:baseline;gap:10px;margin:22px 0 12px}
.sect h3{margin:0;font-size:14px;font-weight:600;color:var(--text)}
.sect p{margin:0;font-size:11.5px;color:var(--dim)}
.mxbar{display:flex;align-items:center;gap:10px;margin:0 0 10px}
.mxbar .sp{margin-left:auto}
.segs{display:flex;gap:0;border:1px solid var(--line-2);border-radius:8px;overflow:hidden}
.seg{background:var(--surface-2);border:0;color:var(--muted);font:500 11px/1 system-ui;
  padding:7px 11px;cursor:pointer;border-right:1px solid var(--line-2)}
.segs .seg:last-child{border-right:0}
.seg:hover{color:var(--text)}
.seg.on{background:rgba(var(--accent-rgb),.14);color:var(--accent)}
.mxbar>.seg{border:1px solid var(--line-2);border-radius:8px}
.mx{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:8px}
.mx th{text-align:left;font:500 10.5px/1 "Fira Code",monospace;color:var(--dim);
  padding:0 8px 9px;text-transform:uppercase;letter-spacing:.05em}
.mx th.n,.mx td.n{text-align:right}
.mx td{padding:6px 8px;border-top:1px solid var(--line)}
.mx td.t{color:var(--text);max-width:340px}
.tline{display:flex;align-items:center;gap:0;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
/* The slug says which post it is only if you already know. The hook says it
   outright. */
/* The slug names the post; clicking it shows the post. */
.peek{background:none;border:0;padding:0;color:var(--text);font:inherit;
  cursor:pointer;text-align:left;max-width:250px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;vertical-align:middle}
.peek:hover{color:var(--accent)}
/* Slide viewer */
#peek{position:fixed;inset:0;z-index:80;background:rgba(var(--ink-rgb),.86);
  display:flex;align-items:center;justify-content:center;padding:28px}
/* An ID selector outranks the browser's [hidden]{display:none}, so without
   this the overlay never hides and its backdrop dims the whole page. */
#peek[hidden],#pagemenu[hidden]{display:none}
#peek .pk{background:var(--surface);border:1px solid var(--line-2);border-radius:15px;
  padding:18px;max-width:min(1180px,94vw);max-height:92vh;overflow:auto}
#peek h4{margin:0 0 3px;font-size:15px;font-weight:600;color:var(--text)}
#peek .cap{font-size:11.5px;color:var(--dim);line-height:1.5;margin:0 0 14px;
  max-width:760px}
#peek .shots{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px}
#peek .shots img{height:min(58vh,540px);border-radius:9px;border:1px solid var(--line);
  display:block}
#peek .x{position:absolute;top:20px;right:24px;background:none;border:0;
  color:var(--dim);font-size:26px;cursor:pointer;line-height:1}
#peek .cta{display:flex;gap:9px;margin-top:14px;flex-wrap:wrap}
.cell{display:block;font:500 12px/1 "Fira Code",monospace;text-align:right;
  padding:6px 8px;border-radius:6px;color:var(--text)}
.cell.win{box-shadow:inset 2px 0 0 var(--ok)}
.cell.dead{color:var(--bad)}
.cell.none{color:var(--dim)}
.sp{font:500 11px/1 "Fira Code",monospace;color:var(--dim)}
.sp.wide{color:var(--warn)}
.ad{width:19px;height:19px;border-radius:5px;border:1px solid var(--line-2);
  background:var(--surface-2);color:var(--dim);font:600 10px/1 "Fira Code",monospace;
  cursor:pointer;margin-right:7px;vertical-align:middle;opacity:.4;transition:all .15s}
tr:hover .ad{opacity:.9}
.ad.on{opacity:1;color:var(--warn);border-color:#5b420f;background:rgba(245,158,11,.12)}
.unt{color:var(--dim);font-style:italic}
/* Recent is the normal state, not an error — only "ready to run again" is
   worth colouring. Everything red made the column unreadable. */
.age{font:500 11px/1 "Fira Code",monospace;padding:4px 8px;border-radius:5px;
  border:1px solid transparent;white-space:nowrap;color:var(--dim)}
.age.no{color:var(--dim)}
.age.warn{color:var(--muted)}
.age.ok{color:var(--ok);background:rgba(34,197,94,.10);border-color:#14532d}
/* Two columns, and cards in a row match height — align-items:start was what
   left a short card floating above a gap. */
.panelrow{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:20px 0}
.pcard{display:flex;flex-direction:column}
.pcard ul.tight{flex:1}
.pcard .do{margin-top:auto}
@media(max-width:1000px){.panelrow{grid-template-columns:1fr}}
.pcard{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 16px}
.pcard h4{margin:0 0 3px;font-size:13px;font-weight:600;color:var(--text)}
.pcard .why{font-size:11px;color:var(--dim);margin:0 0 12px}
.pcard .do{font-size:11.5px;color:var(--accent);margin:12px 0 0;
  padding-top:11px;border-top:1px solid var(--line)}
.pcard ul.tight{list-style:none;margin:0;padding:0}
.pcard ul.tight li{display:flex;align-items:baseline;gap:8px;padding:7px 0;
  border-bottom:1px solid var(--line);font-size:12px}
.pcard ul.tight li:last-child{border-bottom:0}
.pcard ul.tight li.none{color:var(--dim);justify-content:center;padding:14px 0}
.pcard .il{color:var(--muted);flex:1;min-width:0;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.pcard .il a{color:var(--muted);text-decoration:none}
.pcard .il a:hover{color:var(--accent)}
.pcard .ir{font:600 13px/1 "Fira Code",monospace;color:var(--text)}
.pcard .is{font:500 10px/1 "Fira Code",monospace;color:var(--dim);min-width:62px;
  text-align:right}
.pcard .go.ghost{border-color:transparent;background:none;pointer-events:none;
  width:62px;padding:6px 0}
.pcard .dim{color:var(--dim);font-weight:400}
/* Always visible: a button you have to hover to discover is not a button. */
.pcard .go{margin-left:10px;font:500 10.5px/1 system-ui;padding:6px 10px;border-radius:6px;
  border:1px solid var(--line-2);background:var(--surface-2);color:var(--muted);
  cursor:pointer;white-space:nowrap;transition:color .15s,border-color .15s}
.pcard .go:hover{color:var(--accent);border-color:var(--accent)}
.chart{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 16px}
.chart h4{margin:0 0 3px;font-size:13px;font-weight:600;color:var(--text)}
.chart .why{font-size:11px;color:var(--dim);line-height:1.5;margin:0 0 12px}
.chart svg{width:100%;height:auto;display:block}
.chart.wide{margin:0 0 4px}
/* Two cards that answer the same question — which account is working —
   read better beside each other than one under the other, where you have to
   scroll to hold both in your head. Stacks again when neither would get
   enough width to be legible. */
.duo{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;
  align-items:stretch;margin:0 0 4px}
.duo>.chart{margin:0;min-width:0;display:flex;flex-direction:column}
.duo .mx.cmp{flex:1;margin-bottom:0}
/* flex:none — a flex item may shrink past its content, and an svg sized by
   aspect ratio has no floor to stop at. */
/* The base rule centres the plot with `margin: … auto`, and auto side
   margins in a flex container suppress the stretch and size the item to its
   content — which is why the chart came out 300px wide inside a 650px card. */
.duo .chartwrap{flex:none;max-width:none;margin:10px 0 0;width:100%}
/* Six columns in half a screen: the gutters go before the figures do. */
.duo .mx.cmp td{padding-left:6px;padding-right:6px}
.duo .mx.cmp th{padding-left:6px;padding-right:6px}
@media(max-width:1180px){.duo{grid-template-columns:1fr}}
/* Capped and centred. Five points stretched across the full width of a
   desktop is a flat line whatever the numbers do. */
.chartwrap{position:relative;max-width:720px;margin:6px auto 0}
.chartwrap svg{width:100%;height:auto;display:block}
.hitc{cursor:crosshair}
.ctip{position:absolute;pointer-events:none;z-index:5;transform:translate(-50%,-100%);
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:9px;
  padding:8px 11px;box-shadow:0 12px 28px rgba(0,0,0,.55);white-space:nowrap}
.ctip[hidden]{display:none}
.ctip>b{display:block;font:600 11px/1.4 "Fira Code",monospace;color:var(--text);
  margin-bottom:5px}
/* Name in one column, figure right-aligned in the other, so the numbers line
   up whatever the account is called. */
.ctip .tr{display:grid;grid-template-columns:auto auto;gap:2px 14px;
  font:500 11px/1.5 "Fira Code",monospace}
.ctip .tr i{font-style:normal;color:var(--c)}
.ctip .tr b{text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
.ctip .tr b.up{color:var(--ok)}
.ctip .tr b.dn{color:var(--bad)}
.ctip .tr b.z{color:var(--dim)}
.legend{display:flex;gap:16px;margin-top:12px;font-size:11px;color:var(--muted)}
.legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px}
#menubtn,#refreshbtn{display:none}
@keyframes spin360{to{transform:rotate(360deg)}}
#refreshbtn.spinning svg{animation:spin360 .7s linear infinite}
@media (max-width:900px){
  /* The strip could only ever show three of six pages. */
  aside nav{display:none}
  #menubtn{display:inline-flex;align-items:center;justify-content:center;
    width:34px;height:34px;background:var(--surface-2);
    border:1px solid var(--line-2);color:var(--text);border-radius:9px;
    padding:0;cursor:pointer;order:2}
  #menubtn svg{width:17px;height:17px}
  /* Sync sits alone in the corner; #runs carries the margin-left:auto. */
  #refreshbtn{display:inline-flex;align-items:center;justify-content:center;
    width:34px;height:34px;background:var(--surface-2);border:1px solid var(--line-2);
    color:var(--muted);border-radius:9px;cursor:pointer;order:9}
  #refreshbtn svg{width:16px;height:16px}
  #refreshbtn:active{color:var(--accent)}
  #runs{order:8}
  h1{display:block;font-size:16px;order:1;margin-right:2px}
  .bar .sub{order:3;font-size:11.5px}
  #pagemenu{position:fixed;inset:0;z-index:70;background:rgba(var(--ink-rgb),.6)}
  #pagemenu .sheet{position:absolute;left:12px;right:12px;top:64px;
    background:var(--surface);border:1px solid var(--line-2);border-radius:14px;
    padding:7px;box-shadow:0 22px 50px rgba(0,0,0,.6)}
  .pg{display:flex;align-items:center;gap:12px;width:100%;background:none;border:0;
    color:var(--muted);font:500 14px/1 system-ui;padding:14px 13px;border-radius:10px;
    cursor:pointer;text-align:left}
  .pg svg{width:17px;height:17px;flex:none}
  .pg b{margin-left:auto;font:500 12px/1 "Fira Code",monospace;color:var(--dim)}
  .pg.on{background:var(--surface-2);color:var(--accent)}
}
.pipe{display:flex;gap:9px;margin:0 0 20px;flex-wrap:wrap}
.pill2{display:inline-flex;align-items:baseline;gap:7px;padding:9px 14px;border-radius:9px;
  background:var(--surface);border:1px solid var(--line);color:var(--muted);
  font-size:12px;text-decoration:none}
.pill2 b{font:600 15px/1 "Fira Code",monospace;color:var(--text)}
.pill2:hover{border-color:var(--line-2)}
.pill2.warn{border-color:#5b420f;background:rgba(245,158,11,.07)}
.pill2.warn b{color:var(--warn)}
.pill2.off{opacity:.6}
.chartrow2{display:grid;grid-template-columns:1.55fr 1fr;gap:14px}
@media(max-width:960px){.chartrow2{grid-template-columns:1fr}}
.pcard ul.tight li .ir.hit,.chart ul.tight li .ir.hit{color:var(--ok)}
.chart ul.tight{list-style:none;margin:0;padding:0}
.chart ul.tight li{display:flex;align-items:baseline;gap:9px;padding:8px 0;
  border-bottom:1px solid var(--line);font-size:12px}
.chart ul.tight li:last-child{border-bottom:0}
.chart .il{color:var(--muted);flex:1;min-width:0;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.chart .ir{font:600 13px/1 "Fira Code",monospace;color:var(--text)}
.hint2{font-size:11px;color:var(--dim);margin:8px 0 0;line-height:1.55}
.tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
.tag{font:500 10px/1 "Fira Code",monospace;padding:4px 7px;border-radius:5px;
  border:1px solid var(--line-2);color:var(--dim);white-space:nowrap}
.tag.rep{color:#A78BFA;border-color:#3b2f63;background:rgba(167,139,250,.08)}
.tag.src{color:var(--muted)}
.cfoot .miss{flex:1 1 auto;min-width:0;font-size:11px;color:var(--warn);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cta{margin-left:auto;font-size:11.5px;font-weight:600;padding:7px 13px;border-radius:7px;
  white-space:nowrap;flex:0 0 auto;line-height:1.1;
  border:1px solid var(--accent);background:rgba(var(--accent-rgb),.13);color:var(--accent);cursor:pointer}
.cta.sec{border-color:var(--line-2);background:var(--surface-2);color:var(--muted)}
.cta:hover{background:rgba(var(--accent-rgb),.26)}
/* The grid stretches every card to the tallest in its row, and a block
   container leaves that slack as dead space under the footer — 28px on any
   card without a lineage tag. A column instead: the body takes the slack,
   the footer stays pinned to the bottom at its own height. */
.cardwrap{border:1px solid var(--line);border-radius:13px;overflow:hidden;
  background:var(--surface);display:flex;flex-direction:column}
.cardwrap > .card{flex:1 1 auto}
.cardwrap > .cfoot{flex:none}
.actbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:9px;flex-wrap:wrap;
  padding:12px 14px;margin:0 0 16px;background:var(--surface);border:1px solid var(--line);
  border-radius:12px;backdrop-filter:blur(9px)}
.actbar .who2{font:600 14px/1 system-ui;color:var(--text);margin-right:auto}
.pop{position:absolute;top:100%;left:0;margin-top:7px;z-index:40;width:310px;
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:11px;
  padding:6px;box-shadow:0 16px 40px rgba(0,0,0,.5)}
.pop.right{left:auto;right:0}
.pop button{display:block;width:100%;text-align:left;padding:9px 11px;border-radius:8px;
  border:0;background:none;color:var(--text);font-size:13px;cursor:pointer}
.pop button:hover{background:var(--surface)}
.pop button b{display:block;font-weight:600}
.pop button span{display:block;color:var(--dim);font-size:11px;margin-top:2px;line-height:1.45}
.strip{display:flex;gap:10px;margin:0 0 18px;overflow-x:auto;padding-bottom:4px}
.strip .sl{flex:0 0 auto;width:172px;position:relative;background:none;border:0;
  padding:0;cursor:pointer}
.strip .sl img{width:100%;border-radius:10px;border:2px solid transparent;display:block}
.strip .sl.picked img{border-color:var(--accent);box-shadow:0 0 0 3px rgba(var(--accent-rgb),.28)}
.redobar{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin:0 0 14px;padding:12px 14px;
  border:1px solid var(--accent);border-radius:11px;background:rgba(var(--accent-rgb),.06)}
.redobar input{flex:1;min-width:260px;background:var(--surface-2);border:1px solid var(--line-2);
  border-radius:8px;padding:9px 11px;color:var(--text);font-size:13px}
.copyrow{display:grid;grid-template-columns:1fr 2fr;gap:14px}
@media(max-width:820px){.copyrow{grid-template-columns:1fr}}
.runpill{display:inline-flex;align-items:center;gap:8px;background:var(--surface-2);
  border:1px solid var(--line-2);border-radius:20px;padding:7px 14px;font-size:12px;
  color:var(--muted);cursor:pointer}
.runpill:hover{color:var(--text)}
.runpill .q{color:var(--dim);font-size:11px}
.toast .x{position:absolute;top:11px;right:12px;background:none;border:0;
  color:var(--dim);font-size:16px;cursor:pointer;line-height:1}
.toast{position:relative}
.trow .dot{width:8px;height:8px;border-radius:50%;background:var(--line-2);
  display:inline-block}
#jobs .toast{position:fixed;right:22px;bottom:22px;z-index:55;width:310px}
@media(max-width:900px){#jobs .toast{right:12px;left:12px;bottom:12px;width:auto}}
.toast{position:fixed;right:22px;bottom:22px;z-index:60;width:330px;
  background:var(--surface);border:1px solid var(--line-2);border-radius:13px;
  padding:15px 17px;box-shadow:0 18px 44px rgba(0,0,0,.55);
  animation:rise .22s ease-out}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.toast h5{margin:0 0 3px;font-size:14px;font-weight:600;color:var(--text);
  display:flex;align-items:center;gap:9px}
.toast .trow{display:flex;align-items:center;gap:9px;margin-top:9px;font-size:12px;
  color:var(--muted)}
.toast .trow .mk{width:16px;text-align:center;flex:0 0 16px}
.toast .trow .dt{color:var(--dim);font-size:11px;margin-left:auto;text-align:right;
  max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.toast .ok{color:var(--ok)} .toast .bad{color:var(--bad)}
.spin{width:14px;height:14px;border-radius:50%;border:2px solid var(--line-2);
  border-top-color:var(--accent);animation:sp .7s linear infinite;display:inline-block}
@keyframes sp{to{transform:rotate(360deg)}}
.topbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 22px;
  padding:13px 15px;background:var(--surface);border:1px solid var(--line);border-radius:12px}
.topbar .sub{margin-left:auto}
.daygrp{margin-bottom:30px}
.dayhd{display:flex;align-items:baseline;gap:10px;margin:0 0 12px;
  font:600 13px/1 "Fira Code",monospace;color:var(--muted);
  border-bottom:1px solid var(--line);padding-bottom:9px}
.dayhd .ct{color:var(--dim);font-weight:400;font-size:11px}
.tms{color:var(--dim);font-size:11px;margin-top:3px}
/* Inside the card. It used to sit at -5,-5 — outside a container with
   overflow:hidden, so it was clipped and never once appeared. */
.new{position:absolute;top:9px;left:9px;width:11px;height:11px;border-radius:50%;
  background:var(--bad);box-shadow:0 0 0 2px rgba(var(--ink-rgb),.75),0 0 10px rgba(244,63,94,.7);
  z-index:4}
/* The badge shares that corner, so it steps right of the dot when a post is
   both unseen and performing. Not down: .tier is positioned against
   .cardwrap, which includes the footer, so bottom:9px landed it on top of
   the view count. */
.cardwrap:has(.new) .tier{left:28px}
.nav .badge{margin-left:6px;width:8px;height:8px;border-radius:50%;background:var(--bad);
  display:inline-block}
.hint{color:var(--dim);font-size:12px;margin:-14px 0 20px}
.run{display:inline-flex;align-items:center;gap:9px;background:var(--surface-2);
  border:1px solid var(--line-2);border-radius:20px;padding:7px 14px;font-size:12px;
  color:var(--muted);margin-left:8px}
.run b{color:var(--text);font-weight:500}
.run .el{font-family:"Fira Code",monospace;color:var(--accent)}
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
#modal{position:fixed;inset:0;background:rgba(var(--ink-rgb),.8);display:none;align-items:center;
  justify-content:center;z-index:60;padding:24px}
#modal .box{background:var(--surface);border:1px solid var(--line-2);border-radius:14px;
  padding:24px;max-width:460px;width:100%;box-shadow:0 24px 60px rgba(0,0,0,.55)}
#modal h3{margin:0 0 10px;font-size:16px;font-weight:600}
#modal p{margin:0 0 18px;color:var(--muted);font-size:13px;line-height:1.6}
#modal p b{color:var(--text);font-weight:600}
/* One row per account, the box beside its name, and the thing that decides
   whether you can even send — the slot count — on the same line. */
.accpick{display:grid;gap:8px}
.chk.acc{display:flex;align-items:center;gap:11px;width:100%;padding:11px 13px;
  border-radius:10px;background:var(--surface-2)}
.chk.acc:hover{border-color:var(--muted)}
.chk.acc:has(input:checked){border-color:var(--accent);background:rgba(var(--accent-rgb),.08)}
.chk.acc .nm{font-weight:600}
.chk.acc .sub{margin-left:auto;font:500 11px/1 "Fira Code",monospace;color:var(--dim)}
.chk.acc.full{opacity:.5;cursor:not-allowed}
.chk.acc.full .sub{color:var(--warn)}
#modal .foot{display:flex;gap:9px;justify-content:flex-end;margin-top:20px}
#modal .danger{background:var(--bad);color:#fff}
.sched{display:grid;gap:12px}
.sched .accts{display:flex;gap:8px;flex-wrap:wrap}
.chk{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line-2);
  border-radius:8px;padding:8px 12px;font-size:13px;cursor:pointer;min-height:40px}
.chk input{width:auto;margin:0}
/* Direct Post panel — the surface TikTok audits, so it is also the one screen
   here that gets filmed. Every size is stated outright rather than inherited:
   the panel sits inside the post detail view, where the ambient rules size
   images to their container and would blow the avatar and the preview up. */
.panel.dp{max-width:600px;padding:0;overflow:hidden}
.dp .sec{padding:22px 26px;border-bottom:1px solid var(--line)}
.dp .sec:last-of-type{border-bottom:0}
.dp .cap-l{display:block;font-size:11px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--dim);margin-bottom:14px}
/* Who is being posted to. */
.dp .who{display:flex;align-items:center;gap:13px}
.dp .who img.av{width:44px;height:44px;min-width:44px;max-width:44px;border-radius:50%;
  object-fit:cover;display:block;border:1px solid var(--line-2)}
.dp .who .nm{min-width:0}
.dp .who .nm b{display:block;font-size:15px;font-weight:600;line-height:1.35}
.dp .who .nm span{display:block;font-size:13px;color:var(--muted);margin-top:1px}
/* One control per line: name, then its constraint under it, then the switch. */
.dp .row{display:flex;align-items:flex-start;gap:18px;padding:17px 0;
  border-bottom:1px solid var(--line)}
.dp .row:first-of-type{padding-top:0}
.dp .row:last-child{padding-bottom:0;border-bottom:0}
.dp .row .txt{flex:1;min-width:0}
.dp .row .t{display:block;font-size:14px;font-weight:600;line-height:1.4}
.dp .row .d{display:block;font-size:12.5px;color:var(--dim);line-height:1.55;margin-top:4px}
.dp .row.muted .t{color:var(--muted)}
/* Switch. A checkbox underneath so it stays keyboard reachable and labelled. */
.dp .sw{position:relative;width:46px;height:27px;min-width:46px;margin-top:1px}
.dp .sw input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;
  z-index:2;cursor:pointer}
.dp .sw i{position:absolute;inset:0;border-radius:999px;background:var(--line-2);
  transition:background .2s ease;pointer-events:none}
.dp .sw i::after{content:"";position:absolute;top:3px;left:3px;width:21px;height:21px;
  border-radius:50%;background:#F8FAFC;transition:transform .2s ease;
  box-shadow:0 1px 3px rgba(0,0,0,.4)}
.dp .sw input:checked~i{background:var(--accent)}
.dp .sw input:checked~i::after{transform:translateX(19px)}
.dp .sw input:focus-visible~i{outline:2px solid var(--text);outline-offset:2px}
.dp .sw input:disabled{cursor:not-allowed}
.dp .sw input:disabled~i{opacity:.35}
.dp .req{color:var(--bad)}
.dp select{min-height:46px}
.dp .note{display:block;font-size:12.5px;color:var(--dim);line-height:1.55;margin-top:8px}
.dp .note.warn{color:var(--warn)}
.dp .sub.bad{color:var(--bad)}
/* Commercial disclosure, revealed under its switch. */
.dp .disc{margin-top:16px;padding:16px;border-radius:10px;background:#0b1120;
  border:1px solid var(--line)}
.dp .disc .opts{display:flex;gap:10px;flex-wrap:wrap}
.dp .disc .chk{background:var(--surface)}
/* Preview: required by the guidelines, so it stays — but as a filmstrip. */
.dp .prev{display:flex;gap:9px;overflow-x:auto;padding-bottom:4px}
.dp .prev img{width:56px;height:100px;min-width:56px;object-fit:cover;display:block;
  border-radius:7px;border:1px solid var(--line-2)}
.dp .cap-t{margin-top:15px;font-size:13px;font-weight:600;line-height:1.45}
.dp .cap-b{margin-top:6px;font-size:12.5px;color:var(--muted);line-height:1.6;
  max-height:78px;overflow:auto}
.dp .consent{padding:14px 26px;background:#0b1120;border-top:1px solid var(--line);
  font-size:12.5px;color:var(--muted);line-height:1.65}
.dp .consent a{color:var(--accent)}
.dp .foot{padding:20px 26px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.dp .foot .hint{flex-basis:100%;font-size:12px;color:var(--dim);line-height:1.55;margin:0}
/* The Post page: a list of what can be sent on the left, the composer beside
   it. One column on a narrow screen, picker first. */
.postwrap{display:grid;grid-template-columns:300px minmax(0,1fr);gap:22px;align-items:start}
.picker{display:flex;flex-direction:column;gap:8px;position:sticky;top:0}
.picker .cap-l{display:block;font-size:11px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--dim);margin-bottom:4px}
.pk{display:flex;align-items:center;gap:12px;width:100%;text-align:left;padding:10px;
  background:var(--surface);border:1px solid var(--line);border-radius:11px;
  color:inherit;transition:border-color .16s,background .16s}
.pk:hover{border-color:var(--line-2)}
.pk.on{border-color:var(--accent);background:var(--surface-2)}
.pk img{width:40px;height:71px;min-width:40px;object-fit:cover;border-radius:6px;
  display:block;border:1px solid var(--line-2)}
.pk .m{min-width:0;flex:1}
.pk .t{display:block;font-size:13px;font-weight:600;line-height:1.35;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pk .d{display:block;font-size:11.5px;color:var(--dim);margin-top:3px;line-height:1.45}
/* Which account, asked before any of the posting controls appear. */
.acctpick{display:flex;flex-direction:column;gap:9px;margin-bottom:4px}
.pa{display:flex;flex-direction:column;align-items:flex-start;gap:3px;width:100%;
  text-align:left;padding:14px 16px;background:#0b1120;border:1px solid var(--line-2);
  border-radius:10px;color:inherit;transition:border-color .16s}
.pa:hover{border-color:var(--accent)}
.pa .t{font-size:14px;font-weight:600}
.pa .d{font-size:12.5px;color:var(--dim)}
@media (max-width:900px){
  .postwrap{grid-template-columns:1fr}
  .picker{position:static;flex-direction:row;overflow-x:auto;padding-bottom:6px}
  .picker .cap-l{display:none}
  .pk{width:auto;min-width:210px;flex:none}
}
.schedbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px;
  padding:12px 15px;border-radius:10px;background:var(--surface);
  border:1px solid var(--line-2);border-left:3px solid #A78BFA}
.schedbar.direct{border-left-color:var(--warn)}
.schedbar b{font-size:13px;font-weight:600}
.schedbar .sub{color:var(--muted);font-size:12px}
.schedbar .btn{margin-left:auto;min-height:34px;padding:7px 13px}
.when{color:var(--accent);font-family:"Fira Code",monospace;font-size:12px}
#zoom{position:fixed;inset:0;background:rgba(var(--ink-rgb),.94);display:none;align-items:center;
  justify-content:center;z-index:var(--z-modal);padding:24px}
#zoom img{max-height:88vh;max-width:min(88vw,520px);border-radius:12px}
#zoom .nav{position:absolute;top:50%;transform:translateY(-50%);width:52px;height:52px;
  border-radius:50%;background:rgba(30,41,59,.9);border:1px solid var(--line-2);color:var(--text);
  display:flex;align-items:center;justify-content:center;transition:background .18s,border-color .18s}
#zoom .nav:hover{background:var(--surface-2);border-color:var(--accent)}
#zoom .nav svg{width:22px;height:22px}
#zoom .prev{left:24px}#zoom .next{right:24px}
#zoom .count{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);
  font:500 13px/1 "Fira Code",monospace;color:var(--muted);background:rgba(var(--ink-rgb),.8);
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
  /* On a phone these are reference, not action: shrink them so the actual
     content starts above the fold. */
  .acct{min-width:0;flex:1;padding:8px 10px}
  .acct .sub{display:none}
  .acct .top{gap:6px}
  .acct .h{font-size:11px}
  .accounts{gap:6px}
  .bar{padding:14px 16px}
  .wrap{padding:16px 16px 48px}
  /* A 9:16 thumb across a phone's full width makes one post fill the screen,
     and the max-height cap left it narrow with dead space beside it. Rows
     instead: small still, text alongside, several posts visible at once. */
  /* Two a row. At this width the slide is the only thing worth showing at
     size, so the chrome around it shrinks to a name, a time and one action. */
  /* minmax(0,…) not 1fr: a bare 1fr floors at the card's min-content and the
     second column runs off the screen. */
  .grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
  .cardwrap{display:flex;flex-direction:column;border-radius:11px;min-width:0}
  .card{display:flex;flex-direction:column;align-items:stretch;gap:0;text-align:left}
  .thumb{aspect-ratio:9/16;width:auto;flex:none;max-height:none;min-height:0;
    border-radius:0}
  .thumb img{height:100%}
  .meta{flex:1;min-width:0;padding:8px 9px 9px;display:flex;flex-direction:column;
    gap:2px}
  .meta .tt{font-size:12px}
  .meta .tms{font-size:10.5px}
  /* Lineage chips wrap to three lines in a half-width column and say little
     you cannot get by opening the post. */
  .meta .tags{display:none}
  .cfoot{border-top:1px solid var(--line);padding:0}
  .cfoot .cta{width:100%;border-radius:0;padding:9px 8px;font-size:11px;
    border-left:0;border-right:0;border-bottom:0}
  .cfoot .miss{padding:6px 9px;font-size:10px}
  /* Keep the row's own controls on the thumbnail, clear of the action button. */
  .fav,.del,.thumb .dots{opacity:.9;width:32px;height:32px}
  .tier{top:6px;left:6px;padding:3px 7px;font-size:10px}
  .del{top:6px;right:auto;left:auto;right:6px}
  .new{top:7px;left:7px}
  .cfoot{min-height:0}
  .slides{grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:9px}
  .srow{flex-wrap:wrap}
  .srow .nm{width:auto}
  .srow .sp{margin-left:0;width:100%}
  .srow .sp .btn{flex:1}
  #zoom .prev{left:8px}#zoom .next{right:8px}
  #zoom .nav{width:44px;height:44px}
  #zoom img{max-width:82vw}
  .toolbar{flex-wrap:wrap}

  /* --- everything built after the first mobile pass --- */
  /* Four rows, in the order the decisions get made: who and where you are,
     which accounts, the one action worth a full row, then the rest paired.
     The overflow menu is a corner square, not a full-width button of its own. */
  .actbar{position:sticky;top:0;gap:7px;padding:11px 12px;border-radius:11px}
  .actbar .back{order:1;flex:none}
  .actbar .who2{order:2;flex:1 1 auto;min-width:0;width:auto;margin:0;
    font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .actbar .btn.more{order:3;flex:none;width:38px;min-width:0;padding:0;
    min-height:38px;font-size:15px}
  /* The primary is the whole point of the screen, so it gets its own row. */
  .actbar .btn:not(.sec){order:5;flex:1 1 100%;min-height:44px;font-size:13.5px}
  .actbar .btn.sec:not(.more){order:6;flex:1 1 calc(50% - 4px);min-height:40px;
    min-width:0;padding-left:8px;padding-right:8px;font-size:12.5px}
  .pop{width:calc(100vw - 48px);left:0;right:auto}
  .strip{gap:8px;margin-bottom:14px;scroll-snap-type:x mandatory}
  .strip .sl{width:44vw;scroll-snap-align:start}
  .redobar{padding:11px 12px;gap:9px}
  .redobar input{min-width:0;width:100%}
  .subtabs{gap:8px;padding-bottom:12px;margin-bottom:2px;align-items:center;
    overflow:visible}
  .subtabs .sub:not(.ghost){display:none}
  .tabsel{display:block;flex:1;min-width:0}
  .sub{white-space:nowrap;padding:9px 12px;font-size:12.5px}
  .sub.ghost{margin-left:0;flex:none;padding:9px 13px}
  .mgrid{grid-template-columns:repeat(2,1fr);gap:9px}
  .mtile{padding:13px 13px}
  .mn{font-size:23px}
  .md{font-size:11px;margin-top:7px;flex-wrap:wrap}
  .md span{font-size:10px}
  .pillp{padding:8px 13px;font-size:11.5px}
  .kpis{grid-template-columns:1fr 1fr;gap:9px}
  .panelrow{grid-template-columns:1fr;gap:11px}
  .chartrow2{grid-template-columns:1fr}
  /* Tables keep their shape and scroll sideways rather than being crushed. */
  .chart,.pcard{padding:13px 14px}
  .chart .mx,.mx{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;
    white-space:nowrap}
  .mx td.t{max-width:150px}
  .mxbar{flex-wrap:wrap;gap:8px}
  .mxbar .sp{margin-left:0;order:3;width:100%}
  .segs{flex:1}
  .seg{flex:1;padding:8px 9px;font-size:11.5px}
  .toast{right:12px;left:12px;bottom:12px;width:auto}
  .cfoot{padding:9px 10px}
  .cta{padding:8px 12px;font-size:11px}
  /* Comfortable thumb targets. */
  .fav,.del,.thumb .dots{width:36px;height:36px;opacity:.85}
  .chip{padding:7px 10px}
  .age{padding:5px 8px}
}

/* --- narrow phones --- */
@media (max-width:430px){
  .mgrid{grid-template-columns:1fr 1fr}
  .kpis{grid-template-columns:1fr 1fr}
  .strip .sl{width:62vw}
  .wrap{padding:14px 12px 44px}
  .bar{padding:12px 12px}
  h1{font-size:15px}
}
.kfun{display:flex;flex-direction:column;gap:3px;margin-top:6px}
.kfun .row{display:grid;grid-template-columns:150px 1fr 62px;align-items:center;gap:10px;
  font-size:12.5px}
.kfun .nm{color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kfun .tr{background:rgba(255,255,255,.06);border-radius:4px;height:15px;overflow:hidden}
.kfun .fl{height:100%;border-radius:4px;background:linear-gradient(90deg,#E08968,#F0C08D)}
.kfun .vv{text-align:right;font-variant-numeric:tabular-nums}
.kfun .row.drop .fl{background:linear-gradient(90deg,#c2554a,#E08968)}
.kgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0 18px}
</style></head><body>
<script>
(function(){try{
  var h=localStorage.getItem('pf.accent'); if(!h) return;
  var n=parseInt(h.slice(1),16), r=document.documentElement;
  r.style.setProperty('--accent',h);
  r.style.setProperty('--accent-rgb',[n>>16&255,n>>8&255,n&255].join(','));
}catch(e){}})();
</script>
<div class="bgfx" aria-hidden="true">
  <i class="ring"></i><i class="ring"></i><i class="ring"></i>
  <div class="hud">
    <i class="m h1"></i><i class="m h2"></i><i class="m h3"></i><i class="m h4"></i>
    <i class="m h5"></i><i class="m h6"></i><i class="h7"></i>
  </div>
  <div class="sat a"><i class="s1"></i><i class="s2"></i><i class="s3"></i><i class="s4"></i></div>
  <div class="sat b"><i class="s1"></i><i class="s2"></i><i class="s3"></i><i class="s4"></i></div>
  <div class="sat c"><i class="s1"></i><i class="s2"></i><i class="s3"></i><i class="s4"></i></div>
  <i class="wire w1"></i><i class="wire w2"></i><i class="wire w3"></i>
  <i class="grain"></i>
  <i class="br tl"></i><i class="br tr"></i><i class="br bl"></i><i class="br br2"></i>
</div>
<div class="hudread" id="hudread" aria-hidden="true">
  <div class="clk" id="hudclk"></div>
  <div class="dt" id="huddt"></div>
  <div class="rows" id="hudrows"></div>
</div>
<div class="app">
<aside>
  <div class="brand">
    <span class="eye" aria-hidden="true"><i class="r1"></i><i class="r2"></i><i class="r3"></i>
      <i class="r4"></i><i class="r5"></i><i class="r7"></i><i class="r8"></i>
      <i class="tb"><b style="--a:0deg"></b><b style="--a:45deg"></b><b style="--a:90deg"></b><b style="--a:135deg"></b><b style="--a:180deg"></b><b style="--a:225deg"></b><b style="--a:270deg"></b><b style="--a:315deg"></b></i>
      <i class="tb2"><b style="--a:30deg"></b><b style="--a:120deg"></b><b style="--a:210deg"></b><b style="--a:300deg"></b></i>
      <i class="r6"></i>
      <img src="/icon/arco.png" alt="ARCO app icon"></span>
    <div><div class="n">ARCO</div>
      <div class="v">content pipeline</div></div>
  </div>
  <nav aria-label="Filter posts">
    <p class="navlabel">Pipeline</p>
    <div id="nav"></div>
  </nav>
  <div class="accounts" id="accounts"></div>
</aside>
<main>
  <div class="bar"><h1 id="ttl">Inbox</h1><span class="sub" id="cnt"></span>
  <button id="menubtn" onclick="togglePages()" aria-label="Pages"></button>
  <button id="refreshbtn" onclick="refreshNow(this)" aria-label="Refresh">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
      <path d="M3 2v6h6"/><path d="M3 13a9 9 0 1 0 3-7.7L3 8"/></svg></button>
  <div id="runs" style="margin-left:auto"></div>
  <div class="cpick">
    <button class="cpdot" id="cpdot" onclick="toggleAccent(event)"
      aria-label="Dashboard colour"></button>
    <div class="cppop" id="cppop" hidden>
      <p class="lbl">Dashboard colour</p>
      <div class="cpsw" id="cpsw"></div>
      <div class="cprow">
        <input type="color" id="cpin" aria-label="Custom colour"
          oninput="previewAccent(this.value)">
        <button class="btn" onclick="saveAccent()">Apply</button>
      </div>
    </div>
  </div></div>
<div id="jobs"></div>
  <div class="wrap" id="view"></div>
</main>
</div>
<div id="peek" hidden></div>
<div id="pagemenu" hidden></div>
<div id="toast"></div>
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
  all:'<path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>',
  new:'<path d="M12 5v14M5 12h14"/>',
  ig:'<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  tiktok:'<path d="M12 9v4m0 4h.01M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.4 0Z"/>',
  lib:'<path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>',
  ideas:'<path d="M9 18h6M10 22h4"/><path d="M8 14a6 6 0 1 1 8 0c-.7.6-1 1.2-1 2H9c0-.8-.3-1.4-1-2Z"/>',
  users:'<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'+'<circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
};
const ic = k => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[k]}</svg>`;
const tk = c => `<svg viewBox="0 0 24 24" fill="${c||'currentColor'}" aria-hidden="true"><path d="${TIKTOK}"/></svg>`;
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

let DATA=null, cur=null, filter='review', sel=0, redoMode=false, zi=-1;
let redoSel=new Set(), openMenu=null;
// Direct Post panel: which account's panel is open, that creator's settings as
// TikTok reports them, and what has been chosen. dpInfo is never reused across
// opens — the guidelines require the creator's settings to be re-read every
// time the posting page is rendered.
let dpAcct=null, dpInfo=null, dpBusy=false, dpTopic=null;
let dpSet={privacy:'', disable_comment:false, auto_add_music:false,
           disclose:false, brand_organic:false, branded_content:false};
const PILLARS=[['tools','Tools'],['screentime','Screen time'],['discipline','Discipline'],
               ['build','Building'],['learn','Studying']];
// Four tabs, one per thing he actually does: make posts, work the TikTok
// queue, fill the Instagram week, look at numbers. Ten tabs was ten places
// to check when the question is only ever "what is waiting on me".
const FILTERS=[['ideas','Ideas'],['new','New post'],['tiktok','TikTok'],
               ['ig','Instagram'],['lib','Library'],['stats','Analytics']];
// Library is one grid with a segmented control rather than four tabs that
// each held a slice of the same list.
const LIBS=[['liked','Performing'],['out','Published'],
            ['unsent','Unsent'],['all','All']];
let libTab = 'liked';
const isOut = p => ['drafted','published','failed'].includes(stateOf(p));
// Drafted but not published everywhere: this is the TikTok worklist.
const needsPublish = p => stateOf(p)==='drafted';

// 'out' is one tab because a post moves drafted -> published without any work
// here; splitting them made you check two lists for the same post.


const DAY=86400;
function stateOf(p){
  const rs = DATA.accounts.map(a => (p.delivery||{})[a.key]).filter(Boolean);
  if (rs.length && rs.every(r => r.published)) return 'published';
  if (rs.some(r => r.status==='SENT')) return 'drafted';
  if (rs.length && rs.every(r => r.status==='FAILED')) return 'failed';
  // Already out there, whatever the delivery log says: the sync found it on an
  // account, or it is flagged performing. Either way it is not waiting on a
  // review, and it can still be reposted, redone or reworded from Published.
  if (p.stats || p.liked) return 'published';
  // Never sent. Review is this week's work; older than that is history and
  // lives in Archive, where it is still one click away.
  if ((Date.now()/1000 - p.mtime) > 7*DAY) return 'archive';
  return 'review';
}
// ------------------------------------------------------------------ ideas
//
// Where a post starts. Four kinds of thing live on one board: ideas to make,
// hooks to open with, references to steal a look from, and promo codes to
// give away. They share a board because they are the same act — noticing
// something now that you will want at 9am on a Tuesday — and because a note
// often turns out to be a hook, which a four-page version would make you
// retype.
//
// The bar at the top never changes shape, and an idea goes straight from its
// card into the generator with the text as the brief.

let NOTES = null, noteSel = null, noteLink = null, noteKind = 'idea';
let noteEdit = null, panX = 0, panY = 0, mzoom = 1, notePic = null, newKind = false;
// True while a pointer is down on a bubble or the canvas. The dashboard polls
// in the background and re-renders when the pipeline changes; rebuilding the
// map out from under a pointer is what made dragging tear.
let mmDrag = false;
const ZMIN = 0.35, ZMAX = 2.2;

// The four the board ships with. A kind is only a label, so anything typed
// into the kind box is as real as these — the colour is derived from the
// string rather than looked up, which is what makes a custom kind free.
const NKINDS = [['title','Title'],['idea','Idea'],['hook','Hook'],
                ['ref','Reference'],['code','Code']];
const NCOL = {title:'#E8EDFA', idea:'#B46BFF', hook:'#3BA8FF',
              ref:'#26D0C4', code:'#E4C24A'};
const BUBW = 196, BUBH = 86, GAP = 66;
// Which way each handle grows, in the order they read around the bubble.
const DIRS = [['n','↑'],['e','→'],['s','↓'],['w','←']];

function kindColour(k){
  if(NCOL[k]) return NCOL[k];
  let h = 0;
  for(const c of k) h = (h*31 + c.charCodeAt(0)) % 360;
  return `hsl(${h} 68% 63%)`;
}

function allKinds(){
  const seen = new Set(NKINDS.map(k => k[0]));
  (NOTES||[]).forEach(r => seen.add(r.kind));
  return [...seen];
}

async function loadNotes(){
  try { NOTES = (await (await fetch('/api/ideas')).json()).rows || []; }
  catch(e){ NOTES = []; }
  try {
    panX = +(localStorage.getItem('pf.mm.x') || 0);
    panY = +(localStorage.getItem('pf.mm.y') || 0);
    mzoom = +(localStorage.getItem('pf.mm.z') || 1) || 1;
  } catch(e){}
  await seedPositions();
  paintIdeaCount();
  if(filter==='ideas') render();
}

// Notes written before the board became a map have no coordinates. Lay them
// out once, in a grid, and persist — so they never move on their own again.
async function seedPositions(){
  const loose = (NOTES||[]).filter(r => !r.x && !r.y);
  if(loose.length < 2 && (NOTES||[]).length === loose.length && loose.length < 2) {
    if(!loose.length) return;
  }
  if(!loose.length) return;
  for(let i = 0; i < loose.length; i++){
    loose[i].x = 60 + (i % 4) * (BUBW + 40);
    loose[i].y = 60 + Math.floor(i / 4) * 150;
    await noteWrite({op:'move', id:loose[i].id, x:loose[i].x, y:loose[i].y}, true);
  }
}

function paintIdeaCount(){
  const cell = document.querySelector('.nav[onclick*="ideas"] .ct');
  if(cell) cell.textContent = tabCount('ideas');
}

// ---------------------------------------------------------------- the map

function ideasView(){
  const rows = NOTES || [];
  document.getElementById('cnt').textContent =
    `${rows.length} bubble${rows.length===1?'':'s'}`;

  return `<div class="mmwrap">
    <div class="mmbar">
      <button class="btn" onclick="addHead()">+ Title</button>
      <div class="kchips">${allKinds().map(k =>
        `<button class="kchip ${noteKind===k?'on':''}" style="--kc:${kindColour(k)}"
           onclick="noteKind='${esc(k)}';render()">${esc(k)}</button>`).join('')}
        ${newKind
          ? `<input class="kin" id="kin" placeholder="new kind" maxlength="24"
               onkeydown="if(event.key==='Enter')takeKind();if(event.key==='Escape'){newKind=false;render()}"
               onblur="takeKind()">`
          : `<button class="kchip add" onclick="newKind=true;render()">+ kind</button>`}
      </div>
      <span class="mmhint">${noteLink
        ? 'Now click the bubble to connect it to — or press Esc.'
        : 'Hover a bubble and press + on the side you want the branch. New branches are '
          + `<b style="color:${kindColour(noteKind)}">${esc(noteKind)}</b>.`}</span>
      <div class="zoomer">
        <button onclick="zoomBy(1/1.2)" aria-label="Zoom out">−</button>
        <span>${Math.round(mzoom*100)}%</span>
        <button onclick="zoomBy(1.2)" aria-label="Zoom in">+</button>
      </div>
      <button class="btn sec sm" onclick="fitMap()">Fit</button>
    </div>

    <div class="mmap" id="mmap" onpointerdown="panStart(event)"
         ondblclick="addBubbleAt(event)" onwheel="wheelZoom(event)">
      <div class="mmin" id="mmin"
           style="transform:translate(${panX}px,${panY}px) scale(${mzoom})">
        <svg class="mmlines" id="mmlines"></svg>
        ${rows.map(bubble).join('')}
      </div>
      ${rows.length ? '' : `<div class="mmempty">Nothing on the board.<br>
        Start with a title, then branch off it with the + handles.</div>`}
    </div>

    <div id="mmins-host">${inspector()}</div>
  </div>`;
}

function bubble(r){
  const c = kindColour(r.kind);
  const sel = noteSel === r.id;
  const pic = r.img
    ? `<img class="bpic" src="/ideas_img/${esc(r.img)}" alt="" loading="lazy">` : '';
  const body = r.text || (r.img ? '' : 'Write it here');
  // The four handles are the whole interaction: a branch is one click on the
  // side you want it, and it arrives connected.
  const hands = DIRS.map(([d,gl]) =>
    `<button class="hnd ${d}" title="Add ${esc(NKINDS.find(k=>k[0]===noteKind)?'a '+noteKind:'a bubble')} ${d==='n'?'above':d==='s'?'below':d==='e'?'right':'left'}"
       onpointerdown="event.stopPropagation()"
       onclick="branch(event,'${r.id}','${d}')">+</button>`).join('');
  return `<div class="bub k-${esc(r.kind)} ${sel?'sel':''} ${noteLink&&noteLink!==r.id?'target':''}"
    id="b-${r.id}" style="left:${r.x||0}px;top:${r.y||0}px;--kc:${c}"
    onpointerdown="bubDown(event,'${r.id}')"
    ondblclick="editBubble(event,'${r.id}')">
    <span class="bkind">${esc(r.kind)}</span>
    ${pic}
    ${noteEdit===r.id
      ? `<textarea class="bed" id="bed" rows="2"
           onpointerdown="event.stopPropagation()" ondblclick="event.stopPropagation()"
           onblur="saveEdit('${r.id}',this.value)"
           onkeydown="edKey(event,'${r.id}')">${esc(r.text)}</textarea>`
      : `<div class="btx ${r.text?'':'ph'}">${esc(body)}</div>`}
    ${hands}
  </div>`;
}

function inspector(){
  const r = (NOTES||[]).find(x => x.id === noteSel);
  if(!r) return '';
  const linked = ((r.links)||[]).length +
    (NOTES||[]).filter(o => (o.links||[]).includes(r.id)).length;
  return `<aside class="mmins">
    <div class="ihead"><span class="bkind" style="--kc:${kindColour(r.kind)}">${esc(r.kind)}</span>
      <button class="rm" onclick="noteSel=null;render()">×</button></div>
    ${r.img?`<img class="iref" src="/ideas_img/${esc(r.img)}" alt=""
      onclick="zoomNote('${esc(r.img)}')">`:''}
    <p class="ilab">Picture</p>
    <div class="iacts">
      <button onclick="document.getElementById('ifile').click()">
        ${r.img?'Replace':'Add picture'}</button>
      ${r.img?`<button class="warn" onclick="noteWrite({op:'edit',id:'${r.id}',img:''})">Remove</button>`:''}
      <input type="file" id="ifile" accept="image/*" hidden
        onchange="attachPic('${r.id}', this)">
    </div>
    <p class="ilab">Kind</p>
    <div class="kchips">${allKinds().map(k =>
      `<button class="kchip ${r.kind===k?'on':''}" style="--kc:${kindColour(k)}"
         onclick="noteWrite({op:'edit',id:'${r.id}',kind:'${esc(k)}'})">${esc(k)}</button>`).join('')}</div>
    <div class="iacts">
      ${r.kind==='idea'?`<button onclick="buildFromNote('${r.id}')">Build this</button>`:''}
      <button onclick="startLink('${r.id}')">${noteLink===r.id?'Pick a bubble…':'Connect'}</button>
      <button onclick="copyNote('${esc(r.text).replace(/'/g,'&#39;')}',this)">Copy</button>
      <button class="warn" onclick="delNote('${r.id}')">Delete</button>
    </div>
    <p class="ifoot">${linked} connection${linked===1?'':'s'} ·
      ${new Date((r.at||0)*1000).toLocaleDateString('en-GB',{day:'2-digit',month:'short'})}</p>
  </aside>`;
}

// ---------------------------------------------------------------- edges
//
// Drawn from where the bubbles actually are rather than from the stored
// coordinates, so a line keeps up with a bubble mid-drag.

// Where the line from one bubble's centre towards another crosses the first
// bubble's border.
function edgePoint(from, to){
  const cx = from.offsetLeft + from.offsetWidth/2;
  const cy = from.offsetTop + from.offsetHeight/2;
  const dx = (to.offsetLeft + to.offsetWidth/2) - cx;
  const dy = (to.offsetTop + to.offsetHeight/2) - cy;
  if(!dx && !dy) return {x:cx, y:cy};
  const hw = from.offsetWidth/2 + 2, hh = from.offsetHeight/2 + 2;
  const t = Math.min(dx ? hw/Math.abs(dx) : Infinity,
                     dy ? hh/Math.abs(dy) : Infinity);
  return {x: Math.round(cx + dx*t), y: Math.round(cy + dy*t)};
}

function focusEditor(){
  const t = document.getElementById('bed');
  if(t && document.activeElement !== t){
    t.focus();
    t.setSelectionRange(t.value.length, t.value.length);
  }
}

function drawLinks(){
  const svg = document.getElementById('mmlines'); if(!svg) return;
  const seen = new Set(), out = [];
  (NOTES||[]).forEach(r => ((r.links)||[]).forEach(to => {
    const key = [r.id, to].sort().join('|');
    if(seen.has(key)) return;
    seen.add(key);
    const a = document.getElementById('b-'+r.id), b = document.getElementById('b-'+to);
    if(!a || !b) return;
    // Meet the boundary, not the centre: a line that runs under a bubble and
    // out the other side reads as one long line through it.
    const A = edgePoint(a, b), B = edgePoint(b, a);
    const d = Math.abs(B.x-A.x) >= Math.abs(B.y-A.y)
      ? `M${A.x},${A.y} C${(A.x+B.x)/2},${A.y} ${(A.x+B.x)/2},${B.y} ${B.x},${B.y}`
      : `M${A.x},${A.y} C${A.x},${(A.y+B.y)/2} ${B.x},${(A.y+B.y)/2} ${B.x},${B.y}`;
    out.push(`<path d="${d}" fill="none" stroke="${kindColour(r.kind)}"
      stroke-width="1.5" opacity=".5"/>`);
  }));
  svg.innerHTML = out.join('');
}

// ---------------------------------------------------------------- input

function bubDown(e, id){
  e.stopPropagation();
  const el = e.currentTarget;
  const r = (NOTES||[]).find(x => x.id === id); if(!r) return;

  if(noteLink && noteLink !== id){
    const from = noteLink; noteLink = null;
    return noteWrite({op:'link', id:from, to:id});
  }

  const sx = e.clientX, sy = e.clientY, ox = r.x||0, oy = r.y||0;
  let moved = false;
  mmDrag = true;
  try { el.setPointerCapture(e.pointerId); } catch(err){}
  const mv = ev => {
    const dx = ev.clientX - sx, dy = ev.clientY - sy;
    if(Math.abs(dx) + Math.abs(dy) > 3) moved = true;
    // Screen pixels are map pixels divided by the zoom.
    r.x = Math.round(ox + dx/mzoom); r.y = Math.round(oy + dy/mzoom);
    el.style.left = r.x + 'px'; el.style.top = r.y + 'px';
    drawLinks();
  };
  const up = () => {
    el.removeEventListener('pointermove', mv);
    el.removeEventListener('pointerup', up);
    try { el.releasePointerCapture(e.pointerId); } catch(err){}
    mmDrag = false;
    if(moved) noteWrite({op:'move', id, x:r.x, y:r.y}, true);
    else selectBubble(id);
  };
  el.addEventListener('pointermove', mv);
  el.addEventListener('pointerup', up);
}

function panStart(e){
  if(e.target.closest('.bub')) return;
  const el = document.getElementById('mmin');
  const sx = e.clientX, sy = e.clientY, ox = panX, oy = panY;
  let moved = false;
  mmDrag = true;
  const mv = ev => {
    panX = ox + ev.clientX - sx; panY = oy + ev.clientY - sy;
    if(Math.abs(panX-ox) + Math.abs(panY-oy) > 3) moved = true;
    el.style.transform = `translate(${panX}px,${panY}px)`;
  };
  const up = () => {
    document.removeEventListener('pointermove', mv);
    document.removeEventListener('pointerup', up);
    mmDrag = false;
    savePan();
    if(!moved && (noteSel || noteEdit)){
      noteSel = null; noteEdit = null; render();
    }
  };
  document.addEventListener('pointermove', mv);
  document.addEventListener('pointerup', up);
}

function addHead(){
  const map = document.getElementById('mmap');
  const w = map ? map.clientWidth : 800, h = map ? map.clientHeight : 500;
  newBubble(Math.round(w/2 - panX - BUBW/2), Math.round(h/2 - panY - 40), 'title');
}

function addBubbleAt(e){
  if(e.target.closest('.bub')) return;
  const p = toMap(e.clientX, e.clientY);
  newBubble(Math.round(p.x - BUBW/2), Math.round(p.y - 22));
}

// Screen point to map point, through the pan and the zoom.
function toMap(cx, cy){
  const box = document.getElementById('mmap').getBoundingClientRect();
  return {x: (cx - box.left - panX)/mzoom, y: (cy - box.top - panY)/mzoom};
}

function applyView(){
  const el = document.getElementById('mmin');
  if(el) el.style.transform = `translate(${panX}px,${panY}px) scale(${mzoom})`;
  const lab = document.querySelector('.zoomer span');
  if(lab) lab.textContent = Math.round(mzoom*100) + '%';
}

function setZoom(z, cx, cy){
  const next = Math.round(Math.max(ZMIN, Math.min(ZMAX, z)) * 1000) / 1000;
  if(next === mzoom) return;
  const box = document.getElementById('mmap').getBoundingClientRect();
  // Keep whatever is under the cursor (or the middle) where it is.
  const px = (cx == null ? box.width/2 : cx - box.left);
  const py = (cy == null ? box.height/2 : cy - box.top);
  panX = px - (px - panX) * (next/mzoom);
  panY = py - (py - panY) * (next/mzoom);
  mzoom = next;
  applyView();
  savePan();
}

const zoomBy = f => setZoom(mzoom * f);

function wheelZoom(e){
  // Only a deliberate pinch or ⌘/ctrl+wheel zooms. A plain two-finger scroll
  // belongs to the page, and nothing zooms while a drag is in progress.
  if(mmDrag || (!e.ctrlKey && !e.metaKey) || !e.deltaY) return;
  e.preventDefault();
  setZoom(mzoom * (e.deltaY > 0 ? 1/1.12 : 1.12), e.clientX, e.clientY);
}

function savePan(){
  try {
    localStorage.setItem('pf.mm.x', panX);
    localStorage.setItem('pf.mm.y', panY);
    localStorage.setItem('pf.mm.z', mzoom);
  } catch(e){}
}

// Grow a branch out of one side. The child lands clear of everything already
// on the board — a mind map that stacks its own branches on top of each other
// is worse than a list.
function branch(e, id, dir){
  e.stopPropagation();
  const r = (NOTES||[]).find(x => x.id === id); if(!r) return;
  const el = document.getElementById('b-'+id);
  const w = el ? el.offsetWidth : BUBW, h = el ? el.offsetHeight : BUBH;
  let x = r.x||0, y = r.y||0;
  if(dir==='e') x += w + GAP;
  if(dir==='w') x -= BUBW + GAP;
  if(dir==='s') y += h + GAP;
  if(dir==='n') y -= BUBH + GAP;
  // Slide perpendicular to the branch until the spot is empty.
  const step = (dir==='n'||dir==='s') ? [BUBW+GAP, 0] : [0, BUBH+GAP];
  for(let i = 0; i < 12 && occupied(x, y); i++){
    const k = Math.ceil((i+1)/2) * ((i % 2) ? -1 : 1);
    x = (dir==='n'||dir==='s' ? (r.x||0) + step[0]*k : x);
    y = (dir==='e'||dir==='w' ? (r.y||0) + step[1]*k : y);
  }
  newBubble(Math.round(x), Math.round(y), noteKind, id);
}

function occupied(x, y){
  return (NOTES||[]).some(o => {
    const el = document.getElementById('b-'+o.id);
    const w = el ? el.offsetWidth : BUBW, h = el ? el.offsetHeight : BUBH;
    return Math.abs((o.x||0) - x) < w - 8 && Math.abs((o.y||0) - y) < h - 8;
  });
}

async function newBubble(x, y, kind, from){
  const body = {op:'add', kind:kind || noteKind, text:'', x, y};
  if(from) body.from = from;
  await noteWrite(body);
  const first = (NOTES||[])[0];
  if(first){ noteSel = first.id; noteEdit = first.id; render(); }
}

// Selecting touches two classes and one panel — never the whole board.
function selectBubble(id){
  if(noteSel === id) return;
  noteSel = id;
  document.querySelectorAll('.bub.sel').forEach(b => b.classList.remove('sel'));
  const el = document.getElementById('b-'+id);
  if(el) el.classList.add('sel');
  const host = document.getElementById('mmins-host');
  if(host) host.innerHTML = inspector();
}

function editBubble(e, id){
  e.stopPropagation();
  noteSel = id; noteEdit = id;
  render();
}

function saveEdit(id, text){
  const r = (NOTES||[]).find(x => x.id === id);
  noteEdit = null;
  if(r && text.trim() === (r.text||'').trim()){ render(); return; }
  noteWrite({op:'edit', id, text});
}

function edKey(e, id){
  // Enter commits, because a bubble is a label rather than a paragraph;
  // shift+Enter is there when a line break is genuinely wanted.
  if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); e.target.blur(); }
  if(e.key === 'Escape'){ noteEdit = null; render(); }
  // Tab out of one bubble and straight into a new sibling below it.
  if(e.key === 'Tab'){ e.preventDefault(); e.target.blur();
    setTimeout(() => branch({stopPropagation(){}}, id, 's'), 60); }
}

function startLink(id){
  noteLink = noteLink === id ? null : id;
  render();
}

function takeKind(){
  const el = document.getElementById('kin');
  const v = el ? el.value.trim().toLowerCase().replace(/[^a-z0-9 _-]/g,'') : '';
  newKind = false;
  if(v) noteKind = v;
  render();
}

// Bring everything back on screen — the one thing you cannot do by dragging
// when you have panned away from all of it.
function fitMap(){
  const rows = NOTES || []; if(!rows.length) return;
  const minX = Math.min(...rows.map(r => r.x||0));
  const minY = Math.min(...rows.map(r => r.y||0));
  // Zoom out far enough that the whole map fits, then sit it in the corner.
  const map = document.getElementById('mmap');
  const maxX = Math.max(...rows.map(r => (r.x||0) + BUBW));
  const maxY = Math.max(...rows.map(r => (r.y||0) + BUBH*1.6));
  const fit = Math.min(1, (map.clientWidth - 80)/Math.max(1, maxX - minX),
                          (map.clientHeight - 80)/Math.max(1, maxY - minY));
  mzoom = Math.round(Math.max(ZMIN, Math.min(ZMAX, fit)) * 1000) / 1000;
  panX = 40 - minX*mzoom; panY = 40 - minY*mzoom;
  applyView();
  savePan();
}

// ---------------------------------------------------------------- writes

async function noteWrite(body, quiet){
  try {
    const r = await (await fetch('/api/ideas', {method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})).json();
    if(r.rows) NOTES = r.rows;
    paintIdeaCount();
    if(!quiet) render(); else drawLinks();
  } catch(e){ nsay('Could not save'); }
}

function delNote(id){
  const r = (NOTES||[]).find(x => x.id===id);
  showModal({
    title: 'Delete this bubble?',
    body: r && r.img
      ? 'The picture goes with it. There is no copy anywhere else.'
      : (r ? (r.text || 'It is empty.').slice(0, 160) : ''),
    ok: 'Delete', danger: true,
    action: () => { noteSel = null; return noteWrite({op:'del', id}); },
  });
}

function copyNote(text, el){
  navigator.clipboard.writeText(text).then(() => {
    if(el){ const was = el.textContent; el.textContent = 'Copied';
      setTimeout(() => { el.textContent = was; }, 900); }
  });
}

// The point of the board: an idea leaves it as a brief, not as a memory.
function buildFromNote(id){
  const r = (NOTES||[]).find(x => x.id===id); if(!r) return;
  buildNote = r.text;
  if(r.pillar) buildPillar = r.pillar;
  setFilter('new');
}

// One upload path, whether the bytes came from a file picker or the
// clipboard. Attaching to an existing bubble beats making a new one — a
// reference almost always belongs to something already on the board.
async function uploadPic(dataUrl){
  const up = await (await fetch('/api/ideas/img', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({data:dataUrl})})).json();
  return up.img || null;
}

function attachPic(id, input){
  const f = input.files && input.files[0]; if(!f) return;
  const rd = new FileReader();
  rd.onload = async () => {
    const img = await uploadPic(rd.result);
    if(!img) return nsay('That file is not an image');
    await noteWrite({op:'edit', id, img});
  };
  rd.readAsDataURL(f);
}

function zoomNote(img){
  const el = document.getElementById('zoomimg');
  el.src = '/ideas_img/' + img;
  el.alt = 'Reference';
  document.getElementById('zcount').textContent = '';
  document.getElementById('mzoom').style.display = 'flex';
}

function nsay(msg){
  const t = document.getElementById('toast'); if(!t) return;
  t.innerHTML = `<div class="toast"><h5>${esc(msg)}</h5></div>`;
  setTimeout(() => { if(t.firstChild) t.innerHTML = ''; }, 2600);
}

// Paste anywhere on the board to drop a screenshot in as its own bubble.
document.addEventListener('paste', e => {
  if(filter!=='ideas' || cur) return;
  const item = [...(e.clipboardData&&e.clipboardData.items||[])]
    .find(i => i.type.startsWith('image/'));
  if(!item) return;
  e.preventDefault();
  const rd = new FileReader();
  rd.onload = async () => {
    try {
      const img = await uploadPic(rd.result);
      if(!img) return nsay('That file is not an image');
      // Onto the selected bubble if there is one; otherwise it becomes its own.
      if(noteSel) return noteWrite({op:'edit', id:noteSel, img});
      const map = document.getElementById('mmap');
      await noteWrite({op:'add', kind:'ref', text:'', img,
        x: Math.round((map?map.clientWidth:800)/2 - panX - BUBW/2),
        y: Math.round((map?map.clientHeight:500)/2 - panY - 60)});
    } catch(err){ nsay('Upload failed'); }
  };
  rd.readAsDataURL(item.getAsFile());
});

document.addEventListener('keydown', e => {
  if(e.key !== 'Escape' || filter !== 'ideas') return;
  if(noteLink){ noteLink = null; render(); }
  else if(noteEdit){ noteEdit = null; render(); }
  else if(noteSel){ noteSel = null; render(); }
});

// ---------------------------------------------------------------- new post
//
// Pick what kind of post, press the button. That is the whole page.
//
// It used to be a slide-by-slide composer — a card per slide, its own photo,
// its own copy, a picker for each. It worked, and it was the wrong tool: the
// point of this dashboard is to keep posts going out, and every field on
// that page was a decision standing between him and a post. The agent
// already follows the same rules a person would, so it does the whole thing
// and the result lands in Review where it can be judged in one look.
let HOOKS = null, buildPillar = 'tools', buildCount = 1, buildNote = '';

async function loadHooks(){
  try { HOOKS = await (await fetch('/api/hooks')).json(); } catch(e){ HOOKS = {eligible:[]}; }
  if(filter==='new') render();
}

function composeView(){
  const running = (DATA.runs||[]).filter(r=>r.kind==='build').length;
  const free = ((HOOKS&&HOOKS.eligible)||[]).filter(h=>h.pillar===buildPillar).length;
  return `<div class="cx np">
    <h3>What kind of post?</h3>
    <div class="pillars">${PILLARS.map(([k,lab])=>
      `<button class="pil ${buildPillar===k?'on':''}" onclick="buildPillar='${k}';render()">
        <b>${lab}</b><i>${esc(PILLAR_IS[k]||'')}</i></button>`).join('')}</div>

    <h4 class="csub">Anything specific? <span class="opt">optional</span></h4>
    <textarea class="npnote" placeholder="e.g. lead with Raycast, keep it to four tools"
      oninput="buildNote=this.value">${esc(buildNote)}</textarea>

    <div class="npbar">
      <span class="sum">${free
        ? `${free} ${esc(buildPillar)} hook${free===1?'':'s'} free`
        : `<b class="warnt">no ${esc(buildPillar)} hook is free</b> — every one is inside its cooldown`}</span>
      <div class="segs">${[1,2,3].map(n=>
        `<button class="seg ${buildCount===n?'on':''}" onclick="buildCount=${n};render()">${n}</button>`).join('')}</div>
      <button class="btn" onclick="startBuild()" ${free?'':'disabled'}>
        ${buildCount===1?'Generate':'Generate '+buildCount}</button>
    </div>
    <p class="why">It writes the hook, picks the photos and the roster, writes
      every slide, the title and the caption, renders them and pushes them
      live. A few minutes, then it appears under
      <a href="#" onclick="setFilter('tiktok');return false">TikTok › Built, not
      drafted</a>.</p>
    ${running?`<p class="why">${running} already running. They go one at a
      time: two agents writing hooks.json at once lose each other's work.</p>`:''}
  </div>`;
}

// What each pillar is actually about, so the choice is not five slugs.
const PILLAR_IS = {
  tools: 'a stack of apps, ARCO first',
  screentime: 'hours lost to the phone',
  discipline: 'locking in without motivation',
  build: 'shipping things, running it solo',
  learn: 'studying and retaining',
};

async function startBuild(){
  const r = await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({count:buildCount, pillar:buildPillar, note:buildNote.trim()})});
  const j = await r.json().catch(()=>({}));
  if(j.error) return say(j.error);
  buildNote = '';
  say('Building. It appears under TikTok when the slides and caption are done.');
  await load();
  HOOKS = null; loadHooks();
}
// ---------------------------------------------------------------- users
//
// The app's own numbers, next to the numbers for the posts that sell it. They
// belong on one screen: a week of good reach that moves no installs and no
// blocking is a content problem, and the same week with installs that never
// turn blocking on is a product one. Two dashboards could never say that.
let USERS = null, usersDays = 30;

async function loadUsers(){
  try { USERS = await (await fetch('/api/users?days='+usersDays)).json(); }
  catch(e){ USERS = {error: String(e)}; }
  if(filter==='stats') render();
}

const PCT = (n,d) => d ? Math.round(100*n/d) : 0;

function bars(rows, key, label){
  const order = ['0','1-2','3-5','6-10','11+'];
  const mine = (rows||[]).filter(r=>r.k===key && r.b!=='?');
  const total = mine.reduce((a,r)=>a+r.n,0);
  if(!total) return '';
  const by = Object.fromEntries(mine.map(r=>[r.b,r.n]));
  return `<div class="ubox"><h4>${esc(label)}</h4>
    ${order.map(b=>{
      const n = by[b]||0, p = PCT(n,total);
      return `<div class="ubar"><span class="l">${b}</span>
        <span class="t"><i style="width:${p}%"></i></span>
        <span class="v">${p}%</span></div>`;}).join('')}
    <p class="csum">${total} install${total===1?'':'s'} seen</p></div>`;
}

// The funnel, in the order it happens. Percentages are of installs that
// finished onboarding, because an install that never got through onboarding
// has not had a chance to do any of the rest.
const FUNNEL = [['onboarded','Finished onboarding'],
                ['screenTimeGranted','Allowed Screen Time'],
                ['firstTask','Planned a task'],
                ['firstWindow','Created a block window'],
                ['firstWindowRan','A window actually ran']];

function funnelBox(){
  const rows = USERS.funnel || [];
  if(!rows.length) return '';
  const total = {};
  rows.forEach(r => { total[r.event] = (total[r.event]||0) + r.n; });
  const base = total.onboarded || Math.max(...Object.values(total), 1);
  const r = USERS.retention || {};
  return `<div class="ubox wide"><h4>Where installs stop</h4>
    ${FUNNEL.map(([k,label])=>{
      const n = total[k]||0, p = PCT(n, base);
      return `<div class="ubar"><span class="fl">${esc(label)}</span>
        <span class="t"><i style="width:${p}%"></i></span>
        <span class="v">${n}</span></div>`;}).join('')}
    ${r.cohort?`<p class="csum">Came back: ${PCT(r.d1,r.cohort)}% after a day ·
      ${PCT(r.d7,r.cohort)}% after a week · ${PCT(r.d30,r.cohort)}% after a month
      <i>(of ${r.cohort} installs)</i></p>`:''}</div>`;
}

// The two permissions the product rests on. A denied Screen Time
// authorisation means the blocker cannot work at all for that install, and
// no other number here would ever show it.
function permsBox(){
  const rows = USERS.perms || [];
  if(!rows.length) return '';
  const tally = (field) => {
    const out = {};
    rows.forEach(r => { out[r[field]] = (out[r[field]]||0) + r.n; });
    return out;
  };
  const box = (t, label, warn) => {
    const total = Object.values(t).reduce((a,b)=>a+b,0) || 1;
    return `<div class="ubox"><h4>${esc(label)}</h4>
      ${['granted','denied','unasked','?'].filter(k=>t[k]).map(k=>
        `<div class="ubar"><span class="l ${k==='denied'?'bad':''}">${k}</span>
          <span class="t"><i class="${k==='denied'?'bad':''}"
            style="width:${PCT(t[k],total)}%"></i></span>
          <span class="v">${PCT(t[k],total)}%</span></div>`).join('')}
      <p class="csum">${esc(warn)}</p></div>`;
  };
  return `<div class="ugrid">
    ${box(tally('screenTime'), 'Screen Time permission',
          'Denied means the blocker cannot run for them at all.')}
    ${box(tally('notifs'), 'Notification permission',
          'Denied means no reminders — for a planner that is most of it.')}
  </div>`;
}

function usersView(){
  if(!USERS) { loadUsers(); return '<div class="empty">Reading the app…</div>'; }
  // Zeroes here are not a bug: no build carrying the telemetry has shipped,
  // so nothing has reported yet. Saying so beats an empty chart that reads
  // like nobody uses the app.
  if(!USERS.off && !USERS.error && !((USERS.active||{}).installs))
    return `<div class="cwarn"><b>Nothing has reported yet.</b> The app only
      sends usage once a build carrying it is on someone's phone — 2.0.1 in
      review does not have it. Ship the next build and this fills in.</div>`;
  if(USERS.off) return `<div class="cwarn"><b>Not collecting yet.</b> ${esc(USERS.why)}</div>`;
  if(USERS.error) return `<div class="cwarn"><b>The metrics worker did not answer.</b>
    ${esc(USERS.error)}</div>`;
  const a = USERS.active || {}, n = a.installs || 0;
  const rate = (USERS.taskRate||{}).avg_rate;
  const kpi = (v, l, sub) => `<div class="ukpi"><b>${v}</b><span>${esc(l)}</span>
    ${sub?`<i>${esc(sub)}</i>`:''}</div>`;
  return `<div class="cx">
    <div class="segs multi">${[7,30,90].map(d=>
      `<button class="seg ${usersDays===d?'on':''}"
        onclick="usersDays=${d};USERS=null;loadUsers()">${d} days</button>`).join('')}</div>
    ${USERS.stale?`<div class="cwarn"><b>Saved copy.</b> The worker is not
      answering right now, so these are the last numbers it gave.</div>`:''}
    <div class="ukpis">
      ${kpi(n, 'installs seen', 'opened the app at least once')}
      ${kpi(a.today||0, 'opened today')}
      ${kpi(PCT(a.blocking_installs, n)+'%', 'turned blocking on',
            (a.blocking_installs||0)+' of '+n)}
      ${kpi(PCT(a.focus_installs, n)+'%', 'used focus',
            (a.focus_installs||0)+' of '+n)}
      ${kpi(PCT(a.premium_installs, n)+'%', 'on premium',
            (a.premium_installs||0)+' of '+n)}
      ${kpi(rate==null?'–':Math.round(rate)+'%', 'of planned tasks done',
            'averaged over days where anything was planned')}
    </div>
    ${funnelBox()}
    ${permsBox()}
    <div class="ugrid">
      ${bars(USERS.dist,'habits','Habits kept')}
      ${bars(USERS.dist,'tasks','Tasks planned in a day')}
      ${bars(USERS.dist,'blockWindows','Blocked Hours windows')}
      ${bars(USERS.dist,'focusSessions7d','Focus sessions a week')}
    </div>
    <p class="why">One snapshot per install per day, counts bucketed, nothing
      identifying. A user with an iPhone and a Mac counts once — the day is
      claimed in iCloud, not on the device.</p>
  </div>`;
}

// A card's overflow menu. One entry today — Instagram is the only thing a
// finished post can be sent to that is not already a button — but this is
// where Threads and the rest land when they arrive.
function cardMenu(topic, ev){
  closeCardMenu();
  const m = document.createElement('div');
  m.className = 'cardmenu';
  m.innerHTML = `<button onclick="closeCardMenu();igOpen('${topic}')">Post to Instagram</button>
    <button class="bad" onclick="closeCardMenu();del(event,'${topic}')">Delete</button>`;
  document.body.appendChild(m);
  const r = ev.currentTarget.getBoundingClientRect();
  // Flip above or left when the card sits near an edge, so the menu is never
  // drawn off screen on a phone.
  m.style.top = Math.min(r.bottom + 6, innerHeight - m.offsetHeight - 10) + 'px';
  m.style.left = Math.min(r.left, innerWidth - m.offsetWidth - 10) + 'px';
  setTimeout(()=>document.addEventListener('click', closeCardMenu, {once:true}), 0);
}
function closeCardMenu(){
  document.querySelectorAll('.cardmenu').forEach(el=>el.remove());
}

// ------------------------------------------------------------- schedule
//
// Instagram has no draft inbox — publishing is immediate — so scheduling
// means the Cloudflare worker holds the post and fires it on a cron. This
// page is the view of that queue; the laptop being shut changes nothing.
let IG = null, igSheet = null, igBusy = false;

async function loadIG(){
  try { IG = await (await fetch('/api/ig')).json(); } catch(e){ IG = {error:String(e)}; }
  hudStats();
  if(filter==='ig') render();
}

const igAcc = () => ((IG&&IG.accounts)||[{key:'getarco',label:'get.arco'}]);
const dayKey = ts => new Date(ts*1000).toLocaleDateString('en-GB',
  {weekday:'short', day:'2-digit', month:'short'});

// Three a day, at the same three times. Fixed rather than configurable:
// a posting rhythm you can change is a decision you make again every week.
const IG_SLOTS = ['07:00', '12:00', '19:00'];
let igWeekOff = 0, igFill = null, igProgress = '';

function igSlotAt(day, hhmm){
  const [h, m] = hhmm.split(':').map(Number);
  const d = new Date(day); d.setHours(h, m, 0, 0);
  return Math.floor(d.getTime() / 1000);
}
function igSlotCount(from, to){
  let n = 0;
  for(let i = 0; i < 14; i++){
    const day = new Date(); day.setDate(day.getDate() + i);
    IG_SLOTS.forEach(t => { const at = igSlotAt(day, t); if(at >= from && at < to) n++; });
  }
  return n;
}

// The seven days ahead, each showing all three slots — filled ones with the
// post, empty ones drawn as empty. A month grid cannot show times at phone
// width, and the question is always "what goes out today, where are the holes".
function igWeekDays(){
  const rows = ((IG && IG.queue) || []).filter(r => r.status !== 'cancelled');
  const taken = new Set();
  const out = [];
  // Monday to Sunday, not the next seven days. The columns are labelled
  // MON..SUN, so starting on whatever today happens to be put Thursday in
  // the Monday column and dropped everything earlier in the week.
  const monday = new Date();
  monday.setHours(0,0,0,0);
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7) + igWeekOff * 7);
  for(let i = 0; i < 7; i++){
    const day = new Date(monday);
    day.setDate(day.getDate() + i);
    const slots = IG_SLOTS.map(t => {
      const at = igSlotAt(day, t);
      // Anything within the half hour counts as filling that slot, so a post
      // scheduled by hand at 07:05 is not drawn as a hole at 07:00.
      const row = rows.find(r => !taken.has(r.id) && Math.abs(r.at - at) < 1800);
      if(row) taken.add(row.id);
      return { time: t, at, row, past: at < Date.now() / 1000 };
    });
    out.push({ day, slots });
  }
  return out;
}

function schedView(){
  if(!IG){ loadIG(); return '<div class="empty">Reading the queue…</div>'; }
  if(IG.error) return `<div class="cwarn"><b>The worker did not answer.</b> ${esc(IG.error)}</div>`;
  const days = igWeekDays();
  const holes = days.reduce((n, d) => n + d.slots.filter(s => !s.row && !s.past).length, 0);
  const filled = days.reduce((n, d) => n + d.slots.filter(s => s.row).length, 0);
  const done = ((IG.queue) || []).filter(r =>
    r.status !== 'queued' && r.status !== 'publishing').sort((a, b) => b.at - a.at);

  return `<div class="cx">
    <div class="ighead">
      <div class="fastrow">
        <button class="btn qd" onclick="igFillWeek()" ${holes ? '' : 'disabled'}>
          ${holes ? `Fill the week · ${holes} empty` : 'Week is full'}</button>
        <span class="csum">${igProgress ||
          `${filled}/${days.length * IG_SLOTS.length} filled · ${IG_SLOTS.join(', ')} daily`}</span>
      </div>
      ${igWeekNav(days)}
    </div>
    ${igGrid(days)}
    <div class="weeklist">${days.map(d => `<h4 class="csub">${d.day.toLocaleDateString('en-GB',
        {weekday:'long', day:'2-digit', month:'short'})}</h4>
      ${d.slots.map(s => igSlotRow(s)).join('')}`).join('')}</div>

    ${igFillView()}${igSheetView()}</div>`;
}

// Days across, times down — the shape of a week. Only on a wide screen:
// seven columns at phone width is seven columns of nothing, so below 900px
// the day-grouped list takes over.
// Which week you are looking at, and how to get to another one. The range
// matters more than the offset: "14 – 20 Sept" is a date you can check
// against your own calendar, "next week" is not.
function igWeekNav(days){
  const a = days[0].day, b = days[days.length-1].day;
  const mon = d => d.toLocaleDateString('en-GB', {month:'short'});
  const range = mon(a) === mon(b)
    ? `${a.getDate()} – ${b.getDate()} ${mon(b)}`
    : `${a.getDate()} ${mon(a)} – ${b.getDate()} ${mon(b)}`;
  return `<div class="wknav">
    <button class="wkarr" onclick="igWeekOff--;render()"
      ${igWeekOff <= 0 ? 'disabled title="This is the current week"' : ''}>‹</button>
    <span class="wkr">${esc(range)}</span>
    <button class="wkarr" onclick="igWeekOff++;render()">›</button>
    ${igWeekOff ? `<button class="lnk" onclick="igWeekOff=0;render()">today</button>` : ''}
  </div>`;
}

// One cell. Published carries a pill and opens the post; queued carries a
// cancel. Nothing else needs to be on it — the picture says which post.
function wcell(r){
  const pill = r.status === 'published' ? '<span class="pill ok">published</span>'
             : r.status === 'failed' ? '<span class="pill bad">failed</span>'
             : r.status === 'publishing' ? '<span class="pill go">publishing</span>' : '';
  const open = r.permalink
    ? `onclick="window.open('${esc(r.permalink)}','_blank','noopener')"` : '';
  // Instagram's own numbers, not TikTok's — the worker pulls them back for
  // anything live. Symbol and figure only; the labels would not fit and do
  // not need to.
  const n = v => v == null ? null : (v >= 1000 ? (v/1000).toFixed(1).replace('.0','')+'k' : v);
  const stats = r.status === 'published' && r.views != null
    ? `<span class="wstats">
         <i title="views">▶</i>${n(r.views)}
         <i title="accounts reached">◎</i>${n(r.reach)}
         <i title="likes">♥</i>${n(r.likes)}
         <i title="comments">💬</i>${n(r.comments)}</span>` : '';
  return `<div class="wc ${r.status}" title="${esc(r.topic)}${r.error? ' — '+esc(r.error):''}" ${open}>
      <img src="/slide/${esc(r.topic)}/01.jpg" alt="" loading="lazy">
      ${pill}${stats}<span class="t">${esc(r.topic)}</span>
      ${r.status === 'queued'
        ? `<button class="x" onclick="event.stopPropagation();igCancel('${r.id}')" title="Cancel">×</button>`
        : ''}</div>`;
}

function igGrid(days){
  const cell = s => {
    if(!s.row) return `<button class="wc empty ${s.past?'past':''}"
        ${s.past?'disabled':`onclick="igOpenAt(${s.at})"`}>
        ${s.past?'passed':'+'}</button>`;
    return wcell(s.row);
  };
  return `<div class="wgrid">
    <div class="wh"></div>
    ${days.map(d => `<div class="wh ${d.slots[0] && new Date().toDateString()===d.day.toDateString()?'today':''}">
        <b>${d.day.toLocaleDateString('en-GB',{weekday:'short'})}</b>
        <i>${d.day.getDate()}</i></div>`).join('')}
    ${IG_SLOTS.map((t,i) => `<div class="wt">${t}</div>
      ${days.map(d => cell(d.slots[i])).join('')}`).join('')}
  </div>`;
}

function igSlotRow(s){
  if(!s.row) return `<button class="qrow empty ${s.past?'past':''}"
      ${s.past?'disabled':`onclick="igOpenAt(${s.at})"`}>
      <span class="tm">${s.time}</span>
      <span class="sw"><i>${s.past ? 'passed' : 'empty — tap to fill'}</i></span></button>`;
  const r = s.row;
  return `<div class="qrow ${r.status}">
      <span class="tm">${s.time}</span>
      <img class="sth" src="/slide/${esc(r.topic)}/01.jpg" alt="" loading="lazy">
      <span class="sw"><b>${esc(r.topic)}</b><i>${esc(r.account)}</i></span>
      <button class="btn sec sm" onclick="igCancel('${r.id}')">Cancel</button>
      <span class="st ${r.status}">${r.status === 'publishing'
        ? '<span class="spin"></span> publishing' : 'queued'}</span></div>`;
}

function igDoneRow(r){
  return `<div class="qrow ${r.status}">
      <span class="tm">${hm(r.at)}</span>
      <img class="sth" src="/slide/${esc(r.topic)}/01.jpg" alt="" loading="lazy">
      <span class="sw"><b>${esc(r.topic)}</b>
        <i>${esc(r.account)}${r.error ? ' · ' + esc(r.error) : ''}</i></span>
      ${r.permalink ? `<a class="btn sec sm" href="${esc(r.permalink)}"
        target="_blank" rel="noopener">View</a>` : ''}
      <span class="st ${r.status}">${r.status === 'published'
        ? '✓ published' : esc(r.status)}</span></div>`;
}

// Every post that could go out, best first. Performing before merely
// published, because the whole point of Instagram here is to give a post
// that already worked a second audience.
function igPickable(){
  const queued = new Set(((IG && IG.queue) || [])
    .filter(r => r.status === 'queued' || r.status === 'publishing').map(r => r.topic));
  const cutoff = Date.now() / 1000 - 30 * 86400;
  const recent = new Set(((IG && IG.queue) || [])
    .filter(r => r.status === 'published' && r.at > cutoff).map(r => r.topic));
  const ok = p => p.slides && p.slides.length && p.registered
    && !queued.has(p.topic) && !recent.has(p.topic);
  const best = (a, b) => bestViews(b) - bestViews(a);
  return DATA.posts.filter(p => ok(p) && p.liked).sort(best)
    .concat(DATA.posts.filter(p => ok(p) && !p.liked && isOut(p)).sort(best));
}

function igFillWeek(){
  const pool = igPickable();
  const slots = [];
  igWeekDays().forEach(d => d.slots.forEach(s => {
    // Never within a quarter of an hour: Pages needs a moment to serve a
    // crop that was pushed seconds ago.
    if(!s.row && !s.past && s.at > Date.now()/1000 + 900) slots.push(s);
  }));
  igFill = { picks: slots.map((s, i) => ({ at: s.at, time: s.time,
             topic: pool[i] ? pool[i].topic : null })),
             pool: pool.map(p => p.topic), short: Math.max(0, slots.length - pool.length) };
  render();
}

function igFillView(){
  if(!igFill) return '';
  const used = new Set(igFill.picks.map(p => p.topic).filter(Boolean));
  const n = igFill.picks.filter(p => p.topic).length;
  return `<div class="shwrap" onclick="if(event.target===this){igFill=null;render()}">
    <div class="sh"><div class="shhead"><b>Fill the week</b>
      <button class="rm" onclick="igFill=null;render()">×</button></div>
      <div class="shbody">
        <p class="why">Best-performing first, then the rest of what has been
          published. Nothing that went to Instagram in the last 30 days.
          Swap or drop anything before it goes.</p>
        ${igFill.short ? `<div class="cwarn"><b>Pool ran out.</b>
          ${igFill.short} slot${igFill.short===1?'':'s'} left empty rather than
          repeating a post.</div>` : ''}
        ${igFill.picks.map((p, i) => `<div class="qrow ${p.topic?'':'empty'}">
            <span class="tm">${new Date(p.at*1000).toLocaleDateString('en-GB',
              {weekday:'short'})} ${p.time}</span>
            ${p.topic ? `<img class="sth" src="/slide/${esc(p.topic)}/01.jpg" alt="">
              <span class="sw"><b>${esc(p.topic)}</b></span>
              <button class="lnk" onclick="igSwap(${i})">swap</button>
              <button class="lnk" onclick="igDrop(${i})">×</button>`
            : '<span class="sw"><i>left empty</i></span>'}</div>`).join('')}
      </div>
      <div class="shfoot">
        <span class="csum">${igProgress || ''}</span>
        <button class="btn" onclick="igScheduleFill()" ${n?'':'disabled'}>
          Schedule ${n}</button>
      </div></div></div>`;
}

function igSwap(i){
  const used = new Set(igFill.picks.map(p => p.topic).filter(Boolean));
  const cur = igFill.picks[i].topic;
  const next = igFill.pool.find(t => t !== cur && !used.has(t));
  if(!next) return say('Nothing else in the pool.');
  igFill.picks[i].topic = next; render();
}
function igDrop(i){ igFill.picks[i].topic = null; render(); }

async function igScheduleFill(){
  const picks = igFill.picks.filter(p => p.topic);
  const ok = await igEnsurePrepared(picks.map(p => p.topic),
                                    m => { igProgress = m; render(); });
  if(!ok){ igProgress = ''; render(); return; }
  let done = 0, failed = [];
  for(const p of picks){
    igProgress = `scheduling ${done+1} of ${picks.length}…`; render();
    const r = await (await fetch('/api/ig/schedule', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:p.topic, account:igAcc()[0].key, at:p.at})})).json();
    if(r.error) failed.push(p.topic + ': ' + r.error); else done++;
  }
  igProgress = ''; igFill = null; IG = null;
  await loadIG();
  say(failed.length ? `${done} scheduled, ${failed.length} failed — ${failed[0]}`
                    : `${done} scheduled.`);
}
function igOpenAt(at){
  igOpen(null);
  const d = new Date(at * 1000);
  igSheet.date = new Date(at*1000 - d.getTimezoneOffset()*60000).toISOString().slice(0,10);
  igSheet.time = String(d.getHours()).padStart(2,'0') + ':'
               + String(d.getMinutes()).padStart(2,'0');
  render();
}

function igOpen(topic){
  if(filter !== 'ig'){ filter = 'ig'; saveHash(); }
  const d = new Date(Date.now()+3600e3);
  igSheet = {topic: topic||'', account: igAcc()[0].key,
             date: d.toISOString().slice(0,10),
             time: String(d.getHours()).padStart(2,'0')+':00',
             caption: null};
  if(topic) igLoadCaption(topic);
  render();
}

// Fetched when a post is picked rather than shipped with the whole list —
// ninety-eight captions is most of a megabyte nobody asked for.
async function igLoadCaption(topic){
  const r = await (await fetch('/api/ig/caption',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic})})).json();
  if(!igSheet || igSheet.topic !== topic) return;
  igSheet.caption = r.caption || '';
  render();
}

function igSheetView(){
  if(!igSheet) return '';
  const prepared = (IG&&IG.prepared)||{};
  const topics = Object.keys(prepared);
  return `<div class="shwrap" onclick="if(event.target===this){igSheet=null;render()}">
    <div class="sh ${igSheet.topic?'narrow':''}">
      <div class="shhead"><b>Post to Instagram</b>
      <button class="rm" onclick="igSheet=null;render()">×</button></div>
      <div class="shbody">
        <h4 class="csub">Which post</h4>
        ${igSheet.topic ? `<div class="igpicked">
            <img src="/slide/${esc(igSheet.topic)}/01.jpg" alt="">
            <span class="n">${esc(igSheet.topic)}
              <i>${prepared[igSheet.topic]
                ? prepared[igSheet.topic]+' slides, cropped to 4:5'
                : 'will be cropped to 4:5 first'}</i></span>
            <button class="lnk" onclick="igSheet.topic='';render()">Change</button>
          </div>

          <h4 class="csub">Caption</h4>
          ${igSheet.caption===null
            ? '<p class="csum">reading it…</p>'
            : `<textarea class="igcap" oninput="igSheet.caption=this.value"
                 placeholder="what goes under the post">${esc(igSheet.caption)}</textarea>
               <p class="csum">${(igSheet.caption||'').length} characters ·
                 Instagram allows 2,200. No music: the API cannot attach it.</p>`}`
        : `<p class="why">Pick one. You recognise these by the picture, not the slug.</p>
           <div class="iggrid pick">${igPickable().map(p=>`
             <button class="igcard" onclick="igPick('${esc(p.topic)}')">
               <img loading="lazy" src="/slide/${esc(p.topic)}/${p.slides[0]}" alt="">
               <span class="n">${esc(p.topic)}</span>
               <span class="s">${prepared[p.topic] ? prepared[p.topic]+' ready' : 'needs cropping'}</span>
             </button>`).join('')}</div>`}
        <h4 class="csub">Account</h4>
        <div class="segs multi">${igAcc().map(a=>
          `<button class="seg ${igSheet.account===a.key?'on':''}"
            onclick="igSheet.account='${a.key}';render()">${esc(a.label)}</button>`).join('')}</div>
        <h4 class="csub">When</h4>
        <div class="whenrow">
          <input class="cin" type="date" value="${igSheet.date}" oninput="igSheet.date=this.value">
          <input class="cin" type="time" value="${igSheet.time}" oninput="igSheet.time=this.value">
        </div>
        <p class="csum">Publishing is immediate and cannot be undone.</p>
      </div>
      <div class="shfoot">
        <button class="lnk" onclick="igSchedule(true)"
          ${igBusy||!igSheet.topic?'disabled':''}>Publish now</button>
        <button class="btn" onclick="igSchedule(false)"
          ${igBusy||!igSheet.topic?'disabled':''}>
          ${igBusy?`<span class="spin"></span> ${esc(igProgress||'working')}`:'Schedule'}</button>
      </div></div></div>`;
}

function igPick(topic){
  igSheet.topic = topic; igSheet.caption = null;
  igLoadCaption(topic); render();
}

// Crop, push, and wait for Pages to actually serve them — Instagram fetches
// the images over public HTTPS, so a post that only exists on this laptop
// cannot be published by anything. Polls rather than sleeping a fixed minute,
// because Pages is usually quicker than that and occasionally slower.
async function igEnsurePrepared(topics, onStep){
  const need = [...new Set(topics)].filter(t => !((IG&&IG.prepared)||{})[t]);
  if(!need.length) return true;
  onStep(`cropping ${need.length}…`);
  const r = await (await fetch('/api/ig/prepare_many',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topics:need})})).json();
  if(r.error){ say(r.error); return false; }
  for(let i = 0; i < 40; i++){
    onStep('waiting for Pages…');
    const c = await (await fetch('/api/ig/check',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:need[need.length-1]})})).json();
    if(c.total && c.live === c.total) break;
    await new Promise(r => setTimeout(r, 5000));
  }
  IG = null; await loadIG();
  return true;
}

async function igSchedule(now){
  const topic = igSheet.topic, account = igSheet.account;
  const at = now ? Math.floor(Date.now()/1000)
                 : Math.floor(new Date(igSheet.date+'T'+igSheet.time).getTime()/1000);
  if(!now && at < Date.now()/1000) return say('That time is in the past.');
  igBusy = true; igProgress = ''; render();
  const ok = await igEnsurePrepared([topic], m => { igProgress = m; render(); });
  igProgress = '';
  if(!ok){ igBusy = false; render(); return; }
  const r = await (await fetch('/api/ig/schedule',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, account, at, caption: igSheet.caption})})).json();
  igBusy = false;
  if(r.error){ render(); return say(r.error); }

  // Close, land on the queue, and show the row working — the same shape as
  // drafting, where you watch it finish rather than wondering whether it did.
  igSheet = null;
  if(filter !== 'ig'){ filter = 'ig'; saveHash(); }
  IG = null;
  await loadIG();
  if(now){
    // Nothing else will nudge it for up to a minute, so fire it immediately
    // and then watch the row until Instagram has actually taken it.
    fetch('/api/ig/run',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    igWatch(topic);
  }
  say(now ? 'Publishing…' : 'Scheduled.');
}

// Poll until the row stops moving. Cheap — it is one small GET, and only
// while something is actually in flight.
function igWatch(topic){
  let tries = 0;
  const tick = async () => {
    tries++;
    await loadIG();
    const r = ((IG&&IG.queue)||[]).find(x => x.topic === topic);
    if(r && r.status === 'published'){ say('Published to Instagram.'); return; }
    if(r && r.status === 'failed'){ say(r.error || 'That did not publish.'); return; }
    if(tries > 40) return;
    setTimeout(tick, 4000);
  };
  setTimeout(tick, 3500);
}

async function igCancel(id){
  await fetch('/api/ig/cancel',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id})});
  IG = null; await loadIG();
}
async function igRunNow(){
  const r = await (await fetch('/api/ig/run',{method:'POST',
    headers:{'Content-Type':'application/json'},body:'{}'})).json();
  say(r.error ? r.error : (r.ran ? 'Published '+r.topic : 'Nothing was due.'));
  IG = null; await loadIG();
}

const match = p => filter==='all' ? true
                 : filter==='liked' ? p.liked
                 : filter==='out' ? isOut(p)
                 : stateOf(p)===filter;

let lastRuns = 0, notifyOK = false, jobsOpen = true;

function elapsed(ts){
  const s = Math.max(0, Math.round(Date.now()/1000 - ts));
  return s < 60 ? s+'s' : Math.floor(s/60)+'m '+(s%60)+'s';
}

// Background work uses exactly the same card as drafting does: a header with
// a spinner, one row per item, and a tick when it lands. One visual language
// for "something is happening", whether it is a delivery or an agent.
let seenRuns = [], justDone = [], batchTotal = 0, batchDone = 0;

function paintRuns(){
  const all = DATA.runs||[];
  // A failure is not a job in progress. Keeping it out of the counts stops
  // "building 3 of 3" claiming work that already died.
  const bad  = all.filter(r => r.status === 'failed' || r.status === 'interrupted');
  const runs = all.filter(r => r.status === 'running' || r.status === 'queued');
  const running = runs.filter(r => r.status === 'running');
  const queued  = runs.filter(r => r.status !== 'running');

  // anything that was in the list last time and is gone now has finished
  const names = runs.map(r => r.what);
  seenRuns.filter(w => !names.includes(w)).forEach(w => {
    justDone.push(w); batchDone += 1;
    setTimeout(() => { justDone = justDone.filter(x => x !== w); paintRuns(); }, 6000);
  });
  seenRuns = names;

  // A queue drains one at a time, so "3 of 5" is the useful number. The total
  // is the high-water mark since the queue was last empty.
  if (!runs.length && !justDone.length) { batchTotal = 0; batchDone = 0; }
  else batchTotal = Math.max(batchTotal, runs.length + batchDone);

  document.getElementById('runs').innerHTML = runs.length
    ? `<button class="runpill" onclick="jobsOpen=!jobsOpen;paintRuns()">
         <span class="busy"></span>building ${Math.min(batchDone + 1, batchTotal)}/${batchTotal}${
           queued.length ? ` <span class="q">${queued.length} waiting</span>` : ''}</button>`
    : bad.length
    ? `<button class="runpill bad" onclick="jobsOpen=!jobsOpen;paintRuns()">
         ${bad.length} failed</button>`
    : '';

  const box = document.getElementById('jobs');
  if ((!runs.length && !justDone.length && !bad.length)
      || (!jobsOpen && (runs.length || bad.length))) {
    box.innerHTML = '';
  } else if (!runs.length && !justDone.length && bad.length) {
    // Nothing running, something broken: say what and why, and stay until
    // dismissed. This is the state a failed redo used to spend six seconds in
    // wearing a green tick.
    box.innerHTML = `<div class="toast">
      <button class="x" onclick="jobsOpen=false;paintRuns()">&times;</button>
      <h5><span class="bad">!</span>${bad.length} run${bad.length===1?'':'s'} failed</h5>
      ${bad.map(r => `<div class="trow fail">
        <span class="mk"><span class="bad">!</span></span>
        <span>${esc(r.what)}<br><i>${esc(whyPlain(r))}</i></span>
        <button class="btn sec rt" onclick="retryRun('${r.kind}',${r.at})">Retry</button>
      </div>`).join('')}
      <button class="btn sec" style="width:100%;margin-top:9px"
        onclick="dismissFails()">Clear</button>
    </div>`;
  } else {
    const head = runs.length
      ? `<h5><span class="spin"></span>Building ${
             Math.min(batchDone + 1, batchTotal)} of ${batchTotal}</h5>
         <div class="sub" style="font-size:11px">${
           running.length ? 'One at a time, so they cannot overwrite each other.'
                          : 'Waiting for the current run to finish.'}</div>`
      : `<h5><span class="ok">&#10003;</span>Done, ${batchTotal} built</h5>
         <div class="sub" style="font-size:11px">They are in Review.</div>`;
    box.innerHTML = `<div class="toast">
      ${runs.length ? `<button class="x" onclick="jobsOpen=false;paintRuns()">&times;</button>` : ''}
      ${head}
      ${justDone.map(w => `<div class="trow">
         <span class="mk"><span class="ok">&#10003;</span></span>
         <span>${esc(w)}</span></div>`).join('')}
      ${bad.map(r => `<div class="trow fail">
         <span class="mk"><span class="bad">!</span></span>
         <span>${esc(r.what)}<br><i>${esc(r.why || '')}</i></span></div>`).join('')}
      ${runs.map(r => r.status === 'running'
        ? `<div class="trow"><span class="mk"><span class="spin"></span></span>
             <span>${esc(r.what)}</span>
             <span class="dt el" data-t="${r.started}">${elapsed(r.started)}</span></div>`
        : `<div class="trow"><span class="mk"><span class="dot"></span></span>
             <span>${esc(r.what)}</span>
             <span class="dt">waiting</span></div>`).join('')}
    </div>`;
  }

  document.title = (running.length ? '● ' : '') +
    (runs.length ? runs.length + ' building — ' : '') + 'ARCO pipeline';
  if (runs.length < lastRuns && notifyOK) {
    new Notification('ARCO pipeline', {body: 'A background run finished.'});
  }
  lastRuns = runs.length;
  if (running.length && !window._tick) {
    window._tick = setInterval(() => {
      document.querySelectorAll('.trow .el[data-t]').forEach(e => {
        const t = parseFloat(e.dataset.t);
        e.textContent = isFinite(t) ? elapsed(t) : '';
      });
    }, 1000);
  }
  if (!running.length && window._tick) { clearInterval(window._tick); window._tick = null; }
}

// What the current view actually depends on. The poll runs every five
// seconds while a build is going; re-rendering on each one threw away scroll
// position and any half-typed redo note, which read as a random refresh.
function viewSig(){
  const runs = (DATA.runs||[]).map(r=>r.topic+':'+r.status+':'+(r.done||0)).join(',');
  const p = cur ? (DATA.posts||[]).find(x=>x.topic===cur) : null;
  return [runs, DATA.posts.length,
          p ? (p.slides||[]).join(',') + ':' + (p.redos||[]).length + ':' + !!p.queued : ''
         ].join('|');
}

async function load(quiet){
  // The laptop holds no data of its own, so when the machine that does goes
  // off the network there is nothing to draw. Say that, rather than showing
  // an empty dashboard that looks like everything was deleted.
  let fresh;
  try {
    fresh = await (await fetch('/api/posts')).json();
  } catch (err) {
    fresh = {error: String(err)};
  }
  // A stale snapshot is still worth showing: you can read the pipeline, you
  // just cannot act on it until the machine that owns it is back.
  STALE = !!(fresh && fresh.from_cache);
  if (fresh && fresh.from_cache) {
    DATA = fresh;
    paintStale();
    clearTimeout(window._runpoll);
    window._runpoll = setTimeout(() => load(quiet).then(() => render()), 15000);
    if (!quiet) render();
    return;
  }
  if (fresh && (fresh.upstream_down || fresh.error)) {
    const v = document.getElementById('view');
    if (v && !DATA) v.innerHTML = offlineNote(fresh);
    const hb = document.getElementById('host');
    if (hb) { hb.classList.add('down'); hb.title = 'Upstream is not answering'; }
    clearTimeout(window._runpoll);
    window._runpoll = setTimeout(() => {
      load(quiet).then(() => { if (filter === 'stats' && !AN) loadAnalytics(); else render(); });
    }, 15000);
    return;
  }
  paintStale();
  DATA = fresh;
  paintRuns();
  // poll whenever anything is running, from any page
  // Poll fast while work is running, slowly otherwise. Without the slow beat
  // the last paint sticks: nothing refetches, so a finished run keeps showing
  // its timer until you reload the page by hand.
  clearTimeout(window._runpoll);
  window._runpoll = setTimeout(async () => {
    const was = viewSig();
    await load(true);                    // refresh the data, hold the paint
    if(viewSig() !== was) render();      // progress alone repaints in paintRuns
  }, (DATA.runs||[]).length ? 5000 : 20000);
  const unseen = DATA.posts.some(p => !p.seen && stateOf(p)==='review');
  ICONS.liked = '<path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/>';
  const counts = Object.fromEntries(FILTERS.map(([k]) => [k, tabCount(k)]));
  ICONS.archive = ICONS.archive || '<path d="M21 8v13H3V8M1 3h22v5H1zM10 12h4"/>';
  ICONS.review = ICONS.review || '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>';
  ICONS.out = ICONS.out || ICONS.drafted;
  ICONS.stats = ICONS.stats || '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>';
  ICONS.post = ICONS.post || '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l6-3.5Z"/>';
  ICONS.ready = ICONS.ready || '<path d="M12 6v6l4 2"/><circle cx="12" cy="12" r="9"/>';
  document.getElementById('nav').innerHTML = FILTERS.map(([k,lab]) =>
    `<button class="nav" aria-current="${filter===k}" onclick="setFilter('${k}')">
       ${ic(ICONS[k]?k:'all')}<span>${lab}</span>
       ${k==='review'&&unseen?'<span class="badge"></span>':''}
       <span class="ct">${counts[k]}</span></button>`).join('');
  // Followers is the number that compounds, so it leads. Today's publishing
  // is the operational bit and sits under it.
  const AST = DATA.account_stats || {};
  document.getElementById('accounts').innerHTML =
    `<p class="navlabel">Accounts</p>` + DATA.accounts.map(a=>{
      const t = (DATA.published_today||{})[a.key]||0;
      const st = AST[a.key] || {};
      const d = st.delta;
      const only = anAccs && anAccs.size === 1 && anAccs.has(a.key);
      return `<a class="acct ${only?'sel':''}" data-k="${a.key}" href="#"
                onclick="pickAccount('${a.key}');return false"
                title="${only ? 'Show every account again'
                             : 'See only ' + esc(a.label) + ' in Analytics'}">
        <div class="top">${tk('#F8FAFC')}<span class="h">@${esc(a.label)}</span></div>
        <div class="astat">
          <b>${st.followers ?? '–'}</b><span>followers</span>
          ${d ? `<i class="${d>0?'up':'down'}">${d>0?'+':''}${d}</i>` : ''}
        </div>
        ${cadence(st.last_at)}
      </a>`;}).join('');
  if(!quiet) render();

}

// Cmd-R should reload the page you are looking at, not send you back to
// Review. The hash carries the whole view: tab, post, analytics sub-tab and
// period. `?` separates the post from the rest so old <topic>/<slide> links
// still work.

function closePages(){
  const m = document.getElementById('pagemenu');
  if(m){ m.hidden = true; m.innerHTML = ''; }
  document.removeEventListener('click', closeOnce);
}

function closeOnce(e){
  if(e.target.closest('#pagemenu') || e.target.closest('#menubtn')) return;
  closePages();
}

// The view slides in only when you actually moved. One class, removed as
// soon as it has played, so a repaint mid-animation cannot stack two.
let navMoved = false;
function playNav(){
  if(!navMoved) return;
  navMoved = false;
  const v = document.getElementById('view');
  if(!v) return;
  v.classList.remove('turned');
  void v.offsetWidth;            // restart the animation, not queue it
  v.classList.add('turned');
  v.addEventListener('animationend', () => v.classList.remove('turned'), {once:true});
}

/* Accent picker. One stored hex drives --accent and --accent-rgb; every
   other colour token is written against those, so nothing else changes. */
const DEFAULT_ACCENT = '#E8EDFA';
const ACCENTS = ['#E8EDFA','#B46BFF','#7C6BFF','#3BA8FF','#26D0C4','#3ED27A',
                 '#E4C24A','#FF9A3C','#FF5C7A','#F45CC8','#5AE0FF','#C9FF4A'];
let accent = localStorage.getItem('pf.accent') || DEFAULT_ACCENT;

function paintAccent(hex){
  const n = parseInt(hex.slice(1), 16), r = document.documentElement;
  r.style.setProperty('--accent', hex);
  r.style.setProperty('--accent-rgb', [n>>16&255, n>>8&255, n&255].join(','));
}
function previewAccent(hex){ paintAccent(hex); drawSwatches(hex); }

function drawSwatches(sel){
  const el = document.getElementById('cpsw'); if(!el) return;
  el.innerHTML = ACCENTS.map(h =>
    `<button style="background:${h};color:${h}" title="${h}"` +
    ` aria-pressed="${h.toLowerCase()===sel.toLowerCase()}"` +
    ` onclick="previewAccent('${h}');document.getElementById('cpin').value='${h}'"></button>`
  ).join('');
}

function toggleAccent(e){
  e && e.stopPropagation();
  const pop = document.getElementById('cppop');
  if(pop.hidden){
    // Open on the saved colour, not on whatever a cancelled preview left behind.
    accent = localStorage.getItem('pf.accent') || DEFAULT_ACCENT;
    paintAccent(accent);
    document.getElementById('cpin').value = accent;
    drawSwatches(accent);
    pop.hidden = false;
    setTimeout(() => document.addEventListener('click', closeAccentOnce), 0);
  } else { closeAccent(); }
}
function closeAccent(){
  document.getElementById('cppop').hidden = true;
  document.removeEventListener('click', closeAccentOnce);
  // Revert anything previewed but not applied.
  paintAccent(localStorage.getItem('pf.accent') || DEFAULT_ACCENT);
}
function closeAccentOnce(e){
  if(!e.target.closest('.cpick')) closeAccent();
}
function saveAccent(){
  accent = document.getElementById('cpin').value;
  localStorage.setItem('pf.accent', accent);
  paintAccent(accent);
  document.getElementById('cppop').hidden = true;
  document.removeEventListener('click', closeAccentOnce);
  nsay('Colour applied');
}

function setFilter(k){
  if(k !== filter) navMoved = true;
  // Leaving the Post page drops a half-made publish rather than keeping it
  // armed behind another tab, and forces a fresh creator read on return.
  if(filter==='post' && k!=='post'){ dpAcct=null; dpInfo=null; }
  filter=k; cur=null; closePages(); saveHash(); load();
}

function saveHash(){
  const q = ['v=' + filter];
  if(filter === 'lib'){
    q.push('lib=' + libTab);
    if(libTab === 'liked' && perfSort !== 'views') q.push('s=' + perfSort);
  }
  if(filter === 'stats'){
    q.push('t=' + anTab, 'p=' + anPeriod, 'r=' + anRange);
    // Custom carries its dates, or reloading the page lands on a range with
    // no bounds and nothing to show.
    if(anRange === 'custom' && anFrom){
      q.push('cf=' + Math.round(anFrom));
      if(anTo) q.push('ct=' + Math.round(anTo));
    }
    if(anAccs) q.push('a=' + [...anAccs].join(','));
  }
  location.replace('#' + (cur ? encodeURIComponent(cur) + (zi >= 0 ? '/' + (zi+1) : '') + '?' : '?') + q.join('&'));
}

function restoreHash(){
  const raw = decodeURIComponent(location.hash.slice(1));
  if(!raw) return;
  const [postPart, queryPart] = raw.split('?');
  new URLSearchParams(queryPart || '').forEach((val, key) => {
    if(key === 'v' && FILTERS.some(f => f[0] === val)) filter = val;
    if(key === 't') anTab = val;
    if(key === 'p') anPeriod = val;
    if(key === 'r') anRange = val;
    if(key === 's') perfSort = val;
    if(key === 'lib' && LIBS.some(l => l[0] === val)) libTab = val;
    if(key === 'cf') anFrom = +val || null;
    if(key === 'ct') anTo = +val || null;
    if(key === 'a') anAccs = new Set(val.split(',').filter(Boolean));
  });
  if(!postPart) return;
  const [t, n] = postPart.split('/');
  if(t && DATA.posts.some(p => p.topic === t)){
    cur = t;
    if(n) setTimeout(()=>zoomAt(parseInt(n,10)-1), 0);
  }
}

// On a phone the nav is a strip that scrolls the later pages off screen, so
// there it becomes a menu instead: current page on the button, full list on tap.
function togglePages(){
  const m = document.getElementById('pagemenu');
  if(!m.hidden) return closePages();
  const counts = Object.fromEntries(FILTERS.map(([k]) => [k, tabCount(k)]));
  m.innerHTML = `<div class="sheet">${FILTERS.map(([k,lab])=>
    `<button class="pg ${filter===k?'on':''}" onclick="setFilter('${k}')">
       ${ic(ICONS[k]?k:'all')}<span>${lab}</span>
       <b>${counts[k]}</b></button>`).join('')}</div>`;
  m.hidden = false;
  setTimeout(()=>document.addEventListener('click', closeOnce), 0);
}

// Pull-to-refresh does not exist here and a phone reload loses the page, so
// this refetches in place: posts always, and the TikTok numbers too when you
// are looking at Analytics.
async function refreshNow(btn){
  if(btn) btn.classList.add('spinning');
  try{
    if(filter === 'stats'){ await fetch('/api/sync'); AN = null; }
    await load();
    if(filter === 'stats') await loadAnalytics(); else render();
  } finally {
    if(btn) setTimeout(()=>btn.classList.remove('spinning'), 400);
  }
}

/* The background console. The clock ticks on its own; the figures are
   refreshed whenever a page draws, so they never contradict what is on it. */
function hudClock(){
  const d = new Date(), p = n => String(n).padStart(2, '0');
  const clk = document.getElementById('hudclk');
  if(clk) clk.innerHTML = `${p(d.getHours())}:${p(d.getMinutes())}<span>${p(d.getSeconds())}</span>`;
  const dt = document.getElementById('huddt');
  if(dt) dt.textContent = d.toLocaleDateString('en-GB',
    {weekday:'short', day:'2-digit', month:'short', year:'numeric'});
}

function hudStats(){
  const el = document.getElementById('hudrows'); if(!el) return;
  const AST = DATA.account_stats || {};
  const followers = (DATA.accounts || [])
    .reduce((n, a) => n + ((AST[a.key] || {}).followers || 0), 0);
  const igRows = (IG && IG.queue) || null;
  const queued = igRows ? igRows.filter(r => r.status === 'queued') : null;
  const next = queued && queued.map(r => r.at).sort((a, b) => a - b)[0];
  const hhmm = t => {
    const d = new Date(t * 1000), p = n => String(n).padStart(2, '0');
    return `${p(d.getHours())}:${p(d.getMinutes())}`;
  };
  const rows = [
    ['LIBRARY', (DATA.posts || []).length],
    ['FOLLOWERS', followers.toLocaleString('en-GB')],
    ['IG QUEUED', queued ? queued.length : '—'],
    ['IG LIVE', igRows ? igRows.filter(r => r.status === 'published').length : '—'],
    ['NEXT', next ? hhmm(next) : '—'],
  ];
  el.innerHTML = rows.map(([k, v]) => `<div><i>${k}</i><b>${v}</b></div>`).join('');
}

hudClock();
setInterval(hudClock, 1000);

function render(){ try{ render_(); playNav(); hudStats(); }catch(err){
  // A blank page tells you nothing. Surface the failure where the list goes.
  document.getElementById('view').innerHTML =
    '<div class="empty">Something broke while drawing this view.<br><br><code>'+
    (err && err.message ? err.message : err)+'</code></div>';
  console.error(err);
} }

function render_(){
  const view=document.getElementById('view');
  const pageName = cur ? cur : (FILTERS.find(f=>f[0]===filter)||[])[1];
  document.getElementById('ttl').textContent = pageName;
  const mb = document.getElementById('menubtn');
  // Three lines, not a caption: the page name lives in the h1 beside it.
  if(mb) mb.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="2" stroke-linecap="round"><path d="M3 6h18"/><path d="M3 12h18"/>
      <path d="M3 18h18"/></svg>`;
  if (cur) return detail();
  if(filter==='ideas'){
    // A poll landing mid-drag, or mid-sentence, must not replace the node the
    // pointer is holding or the box being typed into.
    if(mmDrag || (noteEdit && document.activeElement
                           && document.activeElement.id === 'bed')){
      drawLinks();
      return;
    }
    view.innerHTML = ideasView();
    // The edges are measured from the laid-out bubbles, so they can only be
    // drawn once the browser has placed them.
    if(NOTES) requestAnimationFrame(() => { drawLinks(); focusEditor(); });
    else loadNotes();
    return;
  }
  if(filter==='new'){
    document.getElementById('cnt').textContent = '';
    view.innerHTML = composeView();
    if(!HOOKS) loadHooks();
    return;
  }
  if(filter === 'ig'){
    document.getElementById('cnt').textContent = '';
    view.innerHTML = schedView();
    return;
  }
  if(filter === 'tiktok'){
    view.innerHTML = tiktokView();
    return;
  }
  if(filter === 'lib'){
    view.innerHTML = libraryView();
    return;
  }
  if(filter==='stats'){
    document.getElementById('cnt').textContent = '';
    view.innerHTML = analyticsView();
    return;
  }
  const list = DATA.posts.filter(match);
  document.getElementById('cnt').textContent = `${list.length} post${list.length===1?'':'s'}`;
  view.innerHTML = (list.length ? groups(list)
                   : `<div class="empty">Nothing here yet.</div>`);
  // poll while a build is running so finished posts appear without a refresh
  const running = (DATA.builds||[]).some(b=>['queued','running'].includes(b.status));
  clearTimeout(window._poll);
  if(running) window._poll = setTimeout(()=>load().then(render), 6000);
}

// One number per tab, and only where a number means "this is waiting on
// you". Library and Analytics are places you go to look, not queues.
// Posting rhythm. An hour between posts is the target and two is still
// healthy; under an hour reads as a burst, and a long gap is the thing that
// actually costs reach. Both ends are wrong, so both are coloured and both
// pulse — only the window in between is allowed to sit quiet.
const CADENCE = [
  [60,   'soon', 'too soon'],
  [150,  'now',  'post now'],
  [300,  'late', 'slipping'],
  [1e9,  'over', 'overdue'],
];

// The elapsed time is the whole point, so it cannot wait for the next stats
// sync to move. Only the .cad line is rewritten — repainting the sidebar would
// throw away the follower counts mid-animation.
function paintCadence(){
  const AST = (DATA && DATA.account_stats) || {};
  document.querySelectorAll('.acct[data-k] .cad').forEach(c => {
    const key = c.closest('.acct').dataset.k;
    c.outerHTML = cadence((AST[key] || {}).last_at);
  });
}

// Half a minute: the line is written in whole minutes, so anything faster
// redraws the same string.
setInterval(paintCadence, 30000);

function cadence(at){
  if(!at) return `<div class="cad never"><b>no posts yet</b></div>`;
  const mins = Math.max(0, Math.round(Date.now()/1000 - at) / 60);
  const [, cls, label] = CADENCE.find(([m]) => mins < m);
  return `<div class="cad ${cls}"><b>${label}</b><span>${sinceMins(mins)}</span></div>`;
}

function sinceMins(mins){
  if(mins < 1) return 'just now';
  if(mins < 60) return `${Math.round(mins)}m ago`;
  const h = Math.floor(mins/60), m = Math.round(mins % 60);
  if(h < 24) return m ? `${h}h ${m}m ago` : `${h}h ago`;
  const days = Math.floor(h/24);
  return days === 1 ? '1 day ago' : `${days} days ago`;
}

function tabCount(k){
  if(k === 'ideas'){
    // Unused codes are the only thing here with a deadline on it.
    const n = (NOTES||[]).filter(r => r.kind==='code' && !r.used).length;
    return n || '';
  }
  if(k === 'tiktok'){
    const n = DATA.posts.filter(p => needsPublish(p) || stateOf(p)==='review').length;
    return n || '';
  }
  if(k === 'ig'){
    // Empty slots in the next seven days: the "am I behind" number.
    if(!IG || !IG.queue) return '';
    const now = Date.now()/1000, end = now + 7*86400;
    const taken = IG.queue.filter(r =>
      (r.status==='queued'||r.status==='publishing') && r.at>=now && r.at<end).length;
    const holes = Math.max(0, igSlotCount(now, end) - taken);
    return holes || '';
  }
  return '';
}

// TikTok, in the order the work happens: what is sitting in your phone's
// inbox waiting to be published, then what is waiting to be drafted. The
// slot line is the constraint that decides how much you can do today.
function tiktokView(){
  const todo = DATA.posts.filter(p=>stateOf(p)==='review').sort((a,b)=>whenOf(b)-whenOf(a));
  document.getElementById('cnt').textContent = `${todo.length} to draft`;
  return `<h4 class="csub">Built, not drafted</h4>
    ${todo.length ? groups(todo)
      : '<div class="empty">Review is clear — build more.</div>'}`;
}

// Everything that exists, one grid, sliced by a segmented control. It was
// four tabs holding four views of the same list.
function libraryView(){
  const list = DATA.posts.filter(p =>
      libTab==='liked' ? p.liked
    : libTab==='out'   ? isOut(p)
    : libTab==='unsent'? (!isOut(p) && p.slides && p.slides.length)
    : true).sort((a,b)=>whenOf(b)-whenOf(a));
  document.getElementById('cnt').textContent = `${list.length} post${list.length===1?'':'s'}`;
  // Two rows of identical chips said nothing about which one filtered and
  // which one sorted. The labels do that; the second row is also smaller,
  // because sorting is the lesser decision.
  return `<div class="libbar">
      <span class="lbl">Show</span>
      <div class="segs multi">${LIBS.map(([k,lab])=>
        `<button class="seg ${libTab===k?'on':''}"
          onclick="libTab='${k}';saveHash();render()">${lab}</button>`).join('')}</div>
    </div>
    ${libTab==='liked' ? `<div class="libbar sort">
      <span class="lbl">Rank by</span>
      <div class="segs multi">${
        [['views','Best account'],['total','All accounts'],['new','Newest']].map(([v,l])=>
          `<button class="seg ${perfSort===v?'on':''}"
            onclick="perfSort='${v}';saveHash();render()">${l}</button>`).join('')}</div>
    </div>` : ''}
    ${list.length ? groups(list) : '<div class="empty">Nothing here yet.</div>'}`;
}

// The one timestamp that matters for a post: when it was published, else
// when it was drafted, else when it was built. Every tab groups on it.
function whenOf(p){
  const ds = DATA.accounts.map(a=>(p.delivery||{})[a.key]).filter(Boolean);
  // last_out beats published_at: a repost is the same post going out again,
  // and it is the going-out that this list is ordered by.
  const outs = ds.map(r=>r.last_out).filter(Boolean);
  if(outs.length) return Math.max(...outs);
  const pubs = ds.map(r=>r.published_at).filter(Boolean);
  if(pubs.length) return Math.max(...pubs);
  const sent = ds.map(r=>r.at).filter(Boolean);
  if(sent.length) return Math.max(...sent);
  return p.mtime;
}
const two = n => String(n).padStart(2,'0');
function dstamp(ts){ const d=new Date(ts*1000);
  return `${d.getDate()}.${d.getMonth()+1}.${d.getFullYear()}`; }
// A date and a time in one pill, coloured by the day. The time alone made
// every row look like the same afternoon; a colour per day means a batch
// posted together reads as a batch without anyone counting dates.
function dayHue(ts){
  const d = new Date(ts*1000);
  const key = d.getFullYear()*10000 + (d.getMonth()+1)*100 + d.getDate();
  // Golden-angle steps: consecutive days land far apart on the wheel rather
  // than shading into each other.
  return Math.round((key * 137.508) % 360);
}
// When a post went out. With one account selected that is exactly that
// account's time; otherwise it is the most recent, which is the same thing
// the sidebar means by "last published".
function postedAt(r){
  if(anAccs && anAccs.size === 1){
    const k = [...anAccs][0];
    if(r.at && r.at[k]) return r.at[k];
  }
  return r.last_at;
}

// A round number near the target spacing — the axis should read 5, 10, 20,
// never 7 or 13.
function niceStep(span, want = 16){
  if(span <= want) return 1;
  const raw = Math.max(1, span) / want;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  return [1, 2, 5, 10].map(m => m * mag).find(v => v >= raw) || 10 * mag;
}

// Hit rate is the share of uploads that cleared the performing threshold, so
// the bands are absolutes rather than a ranking — an account is not doing well
// because the others are worse.
function rateBand(hr){
  if(hr >= 40) return 'r4';
  if(hr >= 25) return 'r3';
  if(hr >= 12) return 'r2';
  return 'r1';
}

function dayPill(ts){
  if(!ts) return '';
  const d = new Date(ts*1000), h = dayHue(ts);
  const dd = String(d.getDate()).padStart(2,'0');
  const mm = String(d.getMonth()+1).padStart(2,'0');
  return `<span class="daypill" style="color:hsl(${h} 70% 72%);
    background:hsl(${h} 60% 72% / .13);border-color:hsl(${h} 60% 72% / .3)">${dd}.${mm}. ${hm(ts)}</span>`;
}

function hm(ts){ const d=new Date(ts*1000);
  return `${two(d.getHours())}:${two(d.getMinutes())}`; }
function ago(ts){
  const s = Math.max(0, Date.now()/1000 - ts);
  if(s < 3600){ const m=Math.round(s/60); return m<=1?'just now':m+' minutes ago'; }
  if(s < 86400){ const h=Math.round(s/3600); return h+' hour'+(h===1?'':'s')+' ago'; }
  const d=Math.round(s/86400); return d+' day'+(d===1?'':'s')+' ago';
}
// How long ago, and nothing else. The exact draft and publish clock times
// were on every card and answered a question nobody asks twice; the detail
// view still has them per account.
function times(p){
  return ago(whenOf(p));
}
function groups(list){
  // Drafted/Published splits into the worklist and the done pile. Everything
  // else is one list: day headers fragment a short list for no benefit.
  if(filter==='out'){
    const todo = list.filter(needsPublish).sort((a,b)=>whenOf(b)-whenOf(a));
    const done = list.filter(p=>!needsPublish(p)).sort((a,b)=>whenOf(b)-whenOf(a));
    return band('Publish next', todo, 'Newest first — these hold your 5 draft slots.')
         + band('Done', done, '');
  }
  if(filter==='review'){
    const by = new Map();
    list.slice().sort((a,b)=>whenOf(b)-whenOf(a)).forEach(p=>{
      const k = dstamp(whenOf(p));
      if(!by.has(k)) by.set(k, []);
      by.get(k).push(p);
    });
    return [...by].map(([d,ps]) => `<div class="daygrp">
      <div class="dayhd">${d}<span class="ct">${ps.length} post${ps.length===1?'':'s'}</span></div>
      <div class="grid">${ps.map(card).join('')}</div></div>`).join('');
  }
  // Performing is a ranking, not a feed: the question is which post did best,
  // so it opens on views and can fall back to recency.
  if(filter==='lib' && libTab==='liked'){
    const by = {
      views: (a,b) => bestViews(b) - bestViews(a),
      total: (a,b) => totals(b).v - totals(a).v,
      new:   (a,b) => whenOf(b) - whenOf(a),
    }[perfSort] || ((a,b) => bestViews(b) - bestViews(a));
    return `<div class="grid">${list.slice().sort(by).map(card).join('')}</div>`;
  }
  return `<div class="grid">${list.slice().sort((a,b)=>whenOf(b)-whenOf(a))
    .map(card).join('')}</div>`;
}

function band(title, ps, note){
  if(!ps.length) return '';
  return `<div class="daygrp"><div class="dayhd">${title}
    <span class="ct">${ps.length}</span>${note?`<span class="ct" style="margin-left:auto">${note}</span>`:''}</div>
    <div class="grid">${ps.map(card).join('')}</div></div>`;
}

// Reviewing ten posts is a keyboard job. J/K walk the current filter, D
// drafts, P marks published, F opens it on TikTok, 1-6 pick redo slides.
document.addEventListener('keydown', e=>{
  const t=e.target.tagName;
  if(t==='INPUT'||t==='TEXTAREA'||t==='SELECT') return;
  if(document.getElementById('modal').style.display==='flex') return;
  const list = (DATA&&DATA.posts||[]).filter(match);
  if(!cur){
    if(e.key==='Enter' && list.length){ open_(list[0].topic); e.preventDefault(); }
    return;
  }
  const p = DATA.posts.find(x=>x.topic===cur); if(!p) return;
  const i = list.findIndex(x=>x.topic===cur);
  const go = n => { const x=list[n]; if(x) open_(x.topic); };
  if(redoMode && /^[1-6]$/.test(e.key)){ pick(+e.key); e.preventDefault(); return; }
  switch(e.key){
    case 'j': go(i+1); break;
    case 'k': go(i-1); break;
    case 'd': draft(null); break;
    case 'p': break;   // publication is detected, not declared
    case 'f': {                       // was: flag performing, now set by sync
      const u = Object.values(p.stats || {}).map(c => c.url).filter(Boolean)[0];
      if(u) window.open(u, '_blank');
      break;
    }
    case 'r': toggleRedo(); break;
    case 'Escape': if(redoMode) toggleRedo(); else if(openMenu){ openMenu=null; render(); } else back(); break;
    default: return;
  }
  e.preventDefault();
});

let AN = null, anAll = false, anSort = 'best', anTab = 'published', anPeriod = '7';
// The cohort range. Deliberately separate state from anPeriod: one asks
// "published when", the other "gained when", and sharing a control is how
// those two get confused.
let anRange = '7', anFrom = null, anTo = null, pubSort = 'new', pubAll = false;
let anError = null, STALE = false, perfSort = 'views';

// One bar, above everything, when the data on screen is a saved copy. It says
// how old it is, because a number you cannot date is worse than no number.
function paintStale(){
  let el = document.getElementById('stalebar');
  if (!STALE) { if (el) el.remove(); return; }
  if (!el) {
    el = document.createElement('div');
    el.id = 'stalebar';
    document.querySelector('main').prepend(el);
  }
  const at = (DATA && DATA.cached_at) ? ago(DATA.cached_at) : 'earlier';
  el.innerHTML = `<b>Showing a saved copy from ${at}.</b>
    The machine that owns the data is not answering, so nothing here can be
    drafted, redone or replicated until it is back. Retrying every 15 seconds.`;
}

// One place that explains an unreachable upstream, so every view says the
// same thing rather than each going blank in its own way.
function offlineNote(e){
  return `<div class="empty">
    <b style="color:var(--warn)">The machine holding the data is not answering.</b><br><br>
    This dashboard is a window onto it and keeps nothing itself, so there is
    nothing to show until it is back. It retries on its own.<br><br>
    <code>${esc((e && e.error) || 'upstream unreachable')}</code></div>`;
}
let anAccs = null;   // null = all three; otherwise a Set of account keys
const AN_TOP = 20;
const ACOL = {vn:'#38BDF8', getarco:'#A78BFA', us:'#22C55E', max:'#F59E0B',
              prodgod:'#F472B6'};

// Three states so the button says what it is doing: idle, working, done.
// It used to relabel the element it was clicked on, which the re-render then
// replaced — so the label reverted the moment the numbers arrived.
let syncState = null;

async function resync(){
  if(syncState === 'busy') return;
  syncState = 'busy'; paintSync();
  try{
    await fetch('/api/sync');
    AN = null;
    await loadAnalytics();          // re-renders, so paintSync runs again
    syncState = 'done';
    setTimeout(()=>{ syncState = null; paintSync(); }, 2500);
  } catch(e) {
    syncState = null;
  }
  paintSync();
}

function paintSync(){
  const b = document.getElementById('syncbtn');
  if(!b) return;
  if(syncState === 'busy'){
    b.innerHTML = '<span class="spin"></span>Syncing…'; b.disabled = true;
  } else if(syncState === 'done'){
    b.innerHTML = '<span class="ok">&#10003;</span>Synced'; b.disabled = true;
  } else {
    b.textContent = 'Sync now'; b.disabled = false;
  }
}

// The panels used to tell you what to do and leave you to go and do it.
async function quickReshoot(topic){
  const r = await fetch('/api/replicate',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, mode:'reshoot'})});
  const j = await r.json();
  if(j.already) return showModal({title:'Already queued',
    body:topic + ' is already waiting to be replicated.', ok:'OK', action:null});
  await load(); render();
}

// Read the numbers, then look at the post that made them, without leaving
// the table.
function peek(topic){
  const p = DATA.posts.find(x => x.topic === topic);
  const box = document.getElementById('peek');
  const r = (AN.rows || []).find(x => x.topic === topic) || {};
  if(!p){
    // untracked: the slides were never in this repo, so show TikTok's cover
    box.innerHTML = `<button class="x" onclick="closePeek()">&times;</button>
      <div class="pk"><h4>Not built here</h4>
        <p class="cap">${esc(r.title||'')}</p>
        ${r.thumb?`<div class="shots"><img src="${esc(r.thumb)}" alt=""></div>`:''}
        <div class="cta">${Object.entries(r.urls||{}).filter(([,u])=>u).map(([k,u])=>
          `<a class="btn sec" href="${esc(u)}" target="_blank" rel="noreferrer">Open on ${esc(k)}</a>`).join('')}</div>
      </div>`;
  } else {
    box.innerHTML = `<button class="x" onclick="closePeek()">&times;</button>
      <div class="pk">
        <h4>${esc(p.topic)}</h4>
        <p class="cap">${esc(p.caption || p.title || '')}</p>
        <div class="shots">${p.slides.map((s,i)=>
          `<img loading="lazy" src="/slide/${p.topic}/${s}?v=${(p.slide_mtimes||{})[s]||0}"
                alt="Slide ${i+1}">`).join('')}</div>
        <div class="cta">
          <button class="btn sec" onclick="closePeek();cur='${topic}';filter='all';render()">Open post</button>
          ${Object.entries(r.urls||{}).filter(([,u])=>u).map(([k,u])=>
            `<a class="btn sec" href="${esc(u)}" target="_blank" rel="noreferrer">On ${esc(k)}</a>`).join('')}
        </div>
      </div>`;
  }
  box.hidden = false;
  box.onclick = e => { if(e.target.id === 'peek') closePeek(); };
  document.addEventListener('keydown', peekEsc);
}
function peekEsc(e){ if(e.key === 'Escape') closePeek(); }
function closePeek(){
  const b = document.getElementById('peek');
  b.hidden = true; b.innerHTML = '';
  document.removeEventListener('keydown', peekEsc);
}

async function promoted(topic){
  await fetch('/api/promoted?topic='+encodeURIComponent(topic));
  AN = null; await loadAnalytics();
}

function midnight(){ const d = new Date(); d.setHours(0,0,0,0); return d.getTime()/1000; }
function rangeBounds(){
  const m = midnight(), DAY = 86400;
  if(anRange === 'today')     return [m, null];
  if(anRange === 'yesterday') return [m - DAY, m];
  if(anRange === '7')         return [m - 6 * DAY, null];
  if(anRange === '30')        return [m - 29 * DAY, null];
  if(anRange === 'custom')    return [anFrom, anTo];   // only from an old link
  return [0, null];                       // all time
}
function setRange(r){
  // Custom opens on yesterday, one day, because that is the thing you
  // usually want a custom range for. It used to open on two empty inputs,
  // which resolved to no range at all and showed nothing.
  if(r === 'custom' && anFrom == null){
    anFrom = midnight() - 86400;
    anTo = null;
  }
  anRange = r; AN = null; pubAll = false; saveHash(); loadAnalytics();
}

// The two date fields only hold what you typed. Nothing reloads until Apply:
// picking a start date used to fire a query against a half-finished range,
// so you watched the numbers change into something you had not asked for.
let draftFrom = null, draftTo = null;
function setCustom(which, v){
  if(which === 'from') draftFrom = v || null;
  else draftTo = v || null;
  const b = document.getElementById('applyrange');
  if(b) b.disabled = !draftFrom;
}
function applyCustom(){
  if(!draftFrom) return;
  const day = t => new Date(t + 'T00:00:00').getTime() / 1000;
  anFrom = day(draftFrom);
  // One date means that one day, not everything since. A range needs both.
  anTo = draftTo ? day(draftTo) + 86400 : anFrom + 86400;
  if(anTo <= anFrom) anTo = anFrom + 86400;
  anRange = 'custom'; AN = null; pubAll = false; saveHash(); loadAnalytics();
}
async function loadAnalytics(){
  // Restored onto custom with no dates — from a bookmark or a reload — so
  // fall back to the day it opens on rather than querying nothing.
  if(anRange === 'custom' && anFrom == null){ anFrom = midnight() - 86400; anTo = null; }
  const [lo, hi] = rangeBounds();
  const q = 'period=' + anPeriod +
    (lo != null ? '&from=' + lo : '') + (hi != null ? '&to=' + hi : '') +
    (anAccs && anAccs.size ? '&accounts=' + [...anAccs].join(',') : '');
  // Same as load(): an unreachable upstream comes back as an error object,
  // and assigning it to AN made every figure on the page undefined.
  let got;
  try {
    got = await (await fetch('/api/analytics?' + q)).json();
  } catch (err) {
    got = {error: String(err), upstream_down: true};
  }
  const dead = got && (got.upstream_down || got.error) && !got.from_cache;
  AN = dead ? null : got;
  anError = dead ? got : null;
  if (got && got.from_cache) { STALE = true; paintStale(); }
  render();
}

// Click an account to see only that one; click it again to go back to all
// three. Comparing one against the others is the common question, and a
// multi-select made you click twice to ask it.
function toggleAcct(k){
  const solo = anAccs && anAccs.size === 1 && anAccs.has(k);
  anAccs = solo ? null : new Set([k]);
  AN = null; paintAccountSel(); saveHash(); loadAnalytics();
}

// The sidebar card is the same filter as the chip above the charts, so it
// toggles the same way. Arriving from another page always selects, though —
// a filter left over from an earlier visit should not make the first click
// read as a deselect.
function pickAccount(k){
  const arriving = filter !== 'stats' || anTab !== 'accounts';
  filter = 'stats'; anTab = 'accounts';
  if(arriving){
    anAccs = new Set([k]);
    AN = null; paintAccountSel(); saveHash(); loadAnalytics(); render();
  } else {
    toggleAcct(k);
  }
}

// Only the class changes. Repainting the sidebar would restart the cadence
// pulse and drop the follower numbers for a frame.
function paintAccountSel(){
  document.querySelectorAll('.acct[data-k]').forEach(el => {
    const only = anAccs && anAccs.size === 1 && anAccs.has(el.dataset.k);
    el.classList.toggle('sel', !!only);
    el.title = only ? 'Show every account again'
                    : 'See only @' + el.dataset.k + ' in Analytics';
  });
}

function setPeriod(p){ anPeriod = p; AN = null; saveHash(); loadAnalytics(); }

// A delta with no previous period to compare against is not zero, it is
// unknown — so it renders as a dash rather than a confident 0%.
function delta(now, was, opts){
  opts = opts || {};
  if(was == null) return '<span class="d none">–</span>';
  if(!was) return now ? '<span class="d up">new</span>' : '<span class="d none">–</span>';
  const pct = Math.round(((now - was) / was) * 100);
  if(!pct) return '<span class="d flat">no change</span>';
  const good = opts.invert ? pct < 0 : pct > 0;
  return `<span class="d ${good?'up':'down'}">${pct>0?'▲':'▼'} ${Math.abs(pct)}%</span>`;
}

// How long since this went out, and whether that is long enough to run it
// again. Red is too soon: the same slides a day apart reads as a repeat to
// anyone who saw the first one, and probably to TikTok too.
const REPOST_SAFE = 14, REPOST_SOON = 7;
function aged(ts){
  if(!ts) return '<span class="age">–</span>';
  const d = (Date.now()/1000 - ts) / 86400;
  const cls = d >= REPOST_SAFE ? 'ok' : d >= REPOST_SOON ? 'warn' : 'no';
  const txt = d < 1 ? 'today' : d < 2 ? 'yesterday'
            : d < 14 ? Math.round(d)+'d ago'
            : Math.round(d/7)+'w ago';
  return `<span class="age ${cls}" title="${cls==='ok'?'Old enough to run again'
    :cls==='warn'?'Nearly old enough to run again':'Recent'}">${txt}</span>`;
}

// log10 position on a 1..3000 axis, which is the only honest scale here: the
// data is bimodal, everything is either a few hundred or past a thousand.
const lg = v => Math.log10(Math.max(1, v)) / Math.log10(3000);

function analyticsView(){
  if(anError) return offlineNote(anError);
  if(!AN){ loadAnalytics(); return '<div class="empty">Reading the numbers…</div>'; }
  const k = AN.kpi, pa = AN.per_account, T = AN.threshold;
  const accs = AN.accounts;
  const fmt = n => (n||0).toLocaleString();

  const w = AN.window, cur = w.this, was = w.prev;
  const PERIODS = [['1','Today'],['7','7 days'],['28','28 days'],
                   ['60','60 days'],['365','365 days']];
  const dstr = ts => { const d=new Date(ts*1000);
    return d.toLocaleDateString([], {month:'short', day:'numeric'}); };

  const every = AN.all_accounts || AN.accounts;
  const on = k => !anAccs || anAccs.has(k);
  const periodBar = `<div class="periods">${PERIODS.map(([v,l])=>
    `<button class="pillp ${anPeriod===v?'on':''}" onclick="setPeriod('${v}')">${l}</button>`).join('')}
    <span class="acctfilter">${every.map(a=>
      `<button class="pilla ${on(a.key)?'on':'off'}" onclick="toggleAcct('${a.key}')"
         title="${on(a.key) && anAccs ? 'Show all three again' : 'Show only ' + esc(a.label)}">
         <i style="${on(a.key)?`background:${ACOL[a.key]};border-color:${ACOL[a.key]}`
                             :'background:transparent;border-color:var(--line-2)'}"></i>${esc(a.short)}</button>`).join('')}</span>
  </div>`;

  // Big metric tiles, absolute number with an arrow and a percentage, the way
  // TikTok's own Studio shows them.
  const tile = (label, now, before, opts) => {
    opts = opts || {};
    const d = (before == null) ? null : now - before;
    const pct = (before) ? Math.round((d / before) * 100) : null;
    const up = d != null && d > 0, down = d != null && d < 0;
    return `<div class="mtile">
      <div class="ml">${label}</div>
      <div class="mn">${opts.pct ? now + '%' : fmt(now)}</div>
      ${d == null ? '<div class="md none">no earlier data</div>'
        : `<div class="md ${up?'up':down?'down':'flat'}">
             ${up?'▲':down?'▼':'•'} ${d>0?'+':''}${opts.pct?d+'%':fmt(d)}
             ${pct!=null?`<span>(${pct>0?'+':''}${pct}%)</span>`:''}</div>`}
    </div>`;
  };

  // A cohort tile never carries an arrow. There is nothing to compare it
  // against: these are running totals of a set of posts, not a change.
  const ctile = (label, value, note) => `<div class="mtile">
    <div class="ml">${label}</div><div class="mn">${fmt(value)}</div>
    <div class="md none">${note || ''}</div></div>`;

  const hadPrev = was.posts > 0;
  // The tiles that earn their place are the ones TikTok cannot show, because
  // TikTok only ever sees one account at a time. Totals and medians ACROSS
  // the three are this dashboard's whole reason to exist.
  const totals = `<div class="mgrid">
    ${tile('Post views', cur.views, hadPrev?was.views:null)}
    ${tile('Posts published', cur.account_posts, was.account_posts)}
    ${tile('Likes', cur.likes, hadPrev?was.likes:null)}
    ${tile('Followers', w.followers, w.followers_delta==null?null:w.followers-w.followers_delta)}
    ${tile('Comments', cur.comments, hadPrev?was.comments:null)}
    ${tile('Shares', cur.shares, hadPrev?was.shares:null)}
  </div>`;

  const crossMetrics = `<div class="mgrid">
    ${tile('Median per upload', cur.median, hadPrev?was.median:null)}
    ${tile('Uploads over ' + fmt(T), cur.hit_rate, hadPrev?was.hit_rate:null, {pct:true})}
    ${tile('Posts that landed', cur.broke_out, hadPrev?was.broke_out:null)}
  </div>`;

  // The comparison itself: one row per account, same posts, different outcome.
  const bestKey = accs.slice().sort((a,b)=>pa[b.key].median-pa[a.key].median)[0].key;
  const compare = `<div class="chart wide"><h4>Same posts, three accounts</h4>
    <p class="why">Organic only, sorted by hit rate.</p>
    <table class="mx cmp"><thead><tr><th>account</th><th class="n">uploads</th>
      <th class="n">hit rate</th>
      <th class="n">median</th><th class="n">views</th>
      <th class="n">followers</th></tr></thead>
      <tbody>${accs.slice().sort((a,b)=>
          (pa[b.key].wins/Math.max(1,pa[b.key].posts)) -
          (pa[a.key].wins/Math.max(1,pa[a.key].posts))).map(a=>{
        const v = pa[a.key];
        const hr = Math.round(100*v.wins/Math.max(1,v.posts));
        const rank = accs.slice().sort((x, y) =>
          (pa[y.key].wins / Math.max(1, pa[y.key].posts)) -
          (pa[x.key].wins / Math.max(1, pa[x.key].posts)));
        const tag = a.key === rank[0].key
          ? ''
          : a.key === rank[rank.length - 1].key
            ? `<span class="worst">${Math.round(
                (pa[rank[0].key].wins / Math.max(1, pa[rank[0].key].posts)) /
                Math.max(0.01, pa[a.key].wins / Math.max(1, pa[a.key].posts)))}x behind</span>`
            : '';
        return `<tr class="${a.key===rank[0].key?'lead':''}">
          <td class="t"><i style="background:${ACOL[a.key]}"></i>${esc(a.label)}${tag}</td>
          <td class="n"><span class="sp">${v.posts}</span></td>
          <td class="n"><span class="hr ${rateBand(hr)}">${hr}%</span></td>
          <td class="n"><span class="sp">${fmt(v.median)}</span></td>
          <td class="n"><span class="sp">${fmt(v.total)}</span></td>
          <td class="n"><span class="sp">${v.followers??'–'}</span></td></tr>`;
      }).join('')}</tbody></table></div>`;

  // Views by publish day, area chart in the same spirit as TikTok's.
  const DW=1040, DH=210, DL=52, DR=20, DT=20, DB=32;
  const dl = w.daily || [];
  let dayChart;
  if(dl.length < 2){
    dayChart = '<p class="why">Not enough days in this range to draw a line.</p>';
  } else {
    const mx = Math.max(...dl.map(d=>d.views)) || 1;
    const px = i => DL + (i/(dl.length-1))*(DW-DL-DR);
    const py = v => (DH-DB) - (v/mx)*(DH-DT-DB);
    const line = dl.map((d,i)=>`${i?'L':'M'}${px(i).toFixed(1)},${py(d.views).toFixed(1)}`).join(' ');
    const area = `${line} L${px(dl.length-1).toFixed(1)},${DH-DB} L${px(0).toFixed(1)},${DH-DB} Z`;
    const grid = [1,.5,0].map(f=>{
      const y = py(mx*f);
      return `<line x1="${DL}" y1="${y.toFixed(1)}" x2="${DW-DR}" y2="${y.toFixed(1)}"
        stroke="var(--line)" stroke-dasharray="${f?'3 4':'0'}"/>
        <text x="${DW-DR+4}" y="${(y+3).toFixed(1)}" fill="var(--dim)" font-size="10">${
          f?fmt(Math.round(mx*f)):'0'}</text>`;
    }).join('');
    dayChart = `<svg viewBox="0 0 ${DW+46} ${DH}">
      ${grid}
      <path d="${area}" fill="url(#ag)" opacity=".35"/>
      <defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38BDF8" stop-opacity=".55"/>
        <stop offset="100%" stop-color="#38BDF8" stop-opacity="0"/></linearGradient></defs>
      <path d="${line}" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linejoin="round"/>
      ${dl.map((d,i)=>`<circle cx="${px(i).toFixed(1)}" cy="${py(d.views).toFixed(1)}" r="3.5"
        fill="var(--bg)" stroke="#38BDF8" stroke-width="2">
        <title>${d.day}: ${fmt(d.views)} views from ${d.posts} post${d.posts===1?'':'s'}</title></circle>`).join('')}
      <text x="${DL}" y="${DH-8}" fill="var(--dim)" font-size="10">${dl[0].day.slice(5)}</text>
      <text x="${DW-DR}" y="${DH-8}" fill="var(--dim)" font-size="10"
        text-anchor="end">${dl[dl.length-1].day.slice(5)}</text>
    </svg>`;
  }
  const viewsCard = `<div class="chart wide"><h4>Views by day posted</h4>
    <p class="why">What the posts published on each day have earned since.</p>
    ${dayChart}</div>`;

  const head = periodBar + `<div class="range">${dstr(w.from)} – ${dstr(w.to)}</div>`;

  // The list only grows. Twenty is what fits on a screen and covers everything
  // worth acting on; the rest is history, one click away.
  const sorted = AN.rows.slice().sort(
    anSort==='new' ? (a,b)=>(b.posted_at||0)-(a.posted_at||0)
    : anSort==='spread' ? (a,b)=>b.spread-a.spread
    : (a,b)=>b.best-a.best);
  const shown = anAll ? sorted : sorted.slice(0, AN_TOP);

  const controls = `<div class="mxbar">
    <div class="segs">${[['best','Most views'],['new','Newest'],['spread','Widest spread']]
      .map(([v,l])=>`<button class="seg ${anSort===v?'on':''}"
        onclick="anSort='${v}';render()">${l}</button>`).join('')}</div>
    <span class="sp">${shown.length} of ${sorted.length}</span>
    ${sorted.length>AN_TOP?`<button class="seg" onclick="anAll=${!anAll};render()">
      ${anAll?'Show top '+AN_TOP:'Show all '+sorted.length}</button>`:''}
  </div>`;

  const matrix = controls + `<table class="mx">
    <thead><tr><th>post</th>${accs.map(a=>`<th class="n">${esc(a.short)}</th>`).join('')}
      <th class="n">spread</th><th class="n">last posted</th></tr></thead>
    <tbody>${shown.map(r=>`<tr>
      <td class="t" title="${esc(r.title||r.topic)}">
        <button class="ad ${r.promoted?'on':''}" onclick="promoted('${r.topic}')"
          title="${r.promoted?'Promoted — excluded from organic figures':'Mark as promoted (paid)'}">$</button>
        <button class="peek" onclick="peek('${r.topic}')" title="See the slides">${
          r.untracked ? `<span class="unt">${esc((r.title||'').slice(0,40))}…</span>`
                      : esc(r.topic)}</button>${
        r.mode?` <span class="tag rep" style="padding:2px 5px">${esc(r.mode)}</span>`:''}${
        r.pillar?` <span class="sp">${esc(r.pillar)}</span>`:''}</td>
      ${accs.map(a=>{
        const v=r.cells[a.key];
        if(v==null) return '<td class="n"><span class="cell none">–</span></td>';
        const cls = v>=T?'win':(v<100 && r.best>=T)?'dead':'';
        const alpha = (lg(v)*0.42).toFixed(3);
        return `<td class="n"><a class="cell ${cls}" style="background:rgba(var(--accent-rgb),${alpha})"
          href="${r.urls[a.key]||'#'}" target="_blank" rel="noreferrer">${fmt(v)}</a></td>`;
      }).join('')}
      <td class="n"><span class="sp ${r.spread>10?'wide':''}">${r.spread}x</span></td>
      <td class="n">${aged(r.posted_at)}</td>
    </tr>`).join('')}</tbody>
    <tfoot><tr><td class="t" style="color:var(--dim)">wins / median</td>
      ${accs.map(a=>`<td class="n"><span class="sp">${pa[a.key].wins}/${pa[a.key].posts}
        &middot; ${fmt(pa[a.key].median)}</span></td>`).join('')}
      <td></td><td></td></tr></tfoot></table>
    <p class="hint2">Cell shade is log-scaled views. Green edge cleared ${fmt(T)}.
      Red means that account buried a post another account pushed. Click a number to open it on TikTok.</p>`;

  const best = accs.slice().sort((a,b)=>pa[b.key].median-pa[a.key].median)[0];
  const worst = accs.slice().sort((a,b)=>pa[a.key].median-pa[b.key].median)[0];

  const item = (label, right, sub, act) => `<li><span class="il">${label}</span>
    <span class="ir">${right}</span>${sub?`<span class="is">${sub}</span>`:''}${
    act?`<button class="go" onclick="quickReshoot('${act}')"
          title="Same words, new backgrounds">reshoot</button>`
      :'<span class="go ghost"></span>'}</li>`;

  const reshoot = `
    <div class="pcard"><h4>Reshoot these</h4>
      <p class="why">Cleared ${fmt(T)} on 2+ accounts.</p>
      <ul class="tight">${AN.suggest.length
        ? AN.suggest.map(t=>{
            const r = AN.rows.find(x=>x.topic===t) || {};
            return item(`<a href="#" onclick="cur='${t}';filter='all';render();return false">${esc(t)}</a>`,
                        fmt(r.best||0), '', t);
          }).join('')
        : '<li class="none">Nothing new qualifies</li>'}</ul>
      <p class="do">Reshoot keeps the copy and swaps the photographs.</p></div>`;

  const buried = `
    <div class="pcard"><h4>Liked, not shown</h4>
      <p class="why">Above ${AN.like_rate}% like rate, under ${fmt(T)} views.</p>
      <ul class="tight">${(AN.buried||[]).length
        ? AN.buried.map(b=>item(esc(b.untracked?b.title.slice(0,26)+'…':b.topic),
            b.rate+'%', fmt(b.views)+' views', b.untracked?'':b.topic)).join('')
        : '<li class="none">Nothing stands out</li>'}</ul>
      <p class="do">The copy already works; it needs another roll.</p></div>`;

  // Followers per day, not a cumulative line: "we gained 4 today" is the
  // number that tells you whether a post worked. The running total is on the
  // KPI row already.
  const W=720, H=380, L=54, R=26, TOP=30, BOT=44;
  const series = accs.map(a=>({key:a.key, label:a.short, pts:(pa[a.key].history||[])}))
                     .filter(sv=>sv.pts.length);

  // one bucket per calendar day, per account
  const dayKey = ts => { const d=new Date(ts*1000);
    return d.getFullYear()+'-'+two(d.getMonth()+1)+'-'+two(d.getDate()); };
  const days = new Map();
  series.forEach(sv=>{
    for(let i=1;i<sv.pts.length;i++){
      const gain = sv.pts[i].followers - sv.pts[i-1].followers;
      const k = dayKey(sv.pts[i].at);
      if(!days.has(k)) days.set(k, {});
      days.get(k)[sv.key] = (days.get(k)[sv.key]||0) + gain;
    }
  });
  const [rLo, rHi] = rangeBounds();
  const dayList = [...days.entries()].sort((a,b)=>a[0]<b[0]?-1:1)
    .filter(([d])=>{
      const t = new Date(d + 'T12:00:00').getTime()/1000;
      return (rLo == null || t >= rLo) && (rHi == null || t < rHi);
    }).slice(-30);
  // 2.9, the way he writes dates — not 09.02, which reads as February.
  const dmy = d => { const [,m,dd] = d.split('-'); return `${+dd}.${+m}`; };

  let trend;
  if(!dayList.length){
    const totals = series.map(sv=>`${esc(sv.label)} ${sv.pts[sv.pts.length-1].followers}`).join(' &middot; ');
    trend = `<p class="why">Only one snapshot exists so far, so there is no daily
      change to plot. The sync takes one a day — this fills in from tomorrow.</p>
      <p class="hint2">Currently ${totals}.</p>`;
  } else {
    // A line per account, one point per day: the shape of who is growing is
    // the question, and three bars per day made that a comparison of heights
    // rather than of trajectories.
    const gains = accs.map(a=>({a, pts: dayList.map(([d,v])=>({d, g: v[a.key]||0}))}));
    const all = gains.flatMap(sv=>sv.pts.map(p=>p.g));
    const hi = Math.max(1, ...all), lo = Math.min(0, ...all);
    const px = i => L + (dayList.length===1 ? (W-L-R)/2
                        : i * (W-L-R)/(dayList.length-1));
    const py = g => TOP + (hi-g)/Math.max(1,(hi-lo)) * (H-TOP-BOT);
    const zeroY = py(0);
    const step = niceStep(hi - lo);
    const ticks = [];
    for(let v = Math.ceil(lo/step)*step; v <= hi + 1e-9; v += step) ticks.push(Math.round(v));
    // Horizontal rules carry the value; zero is the one that means something,
    // so it is drawn solid while the rest stay hairlines.
    const yrules = ticks.map(v => `<line x1="${L}" y1="${py(v).toFixed(1)}"
        x2="${W-R}" y2="${py(v).toFixed(1)}" stroke="var(--line${v===0?'-2':''})"
        stroke-width="1" ${v===0?'':'stroke-dasharray="2 5"'}/>
      <text x="${L-9}" y="${(py(v)+4).toFixed(1)}" fill="var(--dim)" font-size="12"
        text-anchor="end">${v>0?'+':''}${v}</text>`).join('');

    const lines = gains.map(sv=>{
      const d = sv.pts.map((p,i)=>`${i?'L':'M'}${px(i).toFixed(1)},${py(p.g).toFixed(1)}`).join('');
      // The number sits on the point. Three accounts on one axis means the
      // shape alone cannot tell you whether a rise is +2 or +23.
      const dots = sv.pts.map((p,i)=>`<circle cx="${px(i).toFixed(1)}" cy="${py(p.g).toFixed(1)}"
        r="3.5" fill="${ACOL[sv.a.key]}" stroke="var(--bg)" stroke-width="1.5"/>`).join('');
      return `<path d="${d}" fill="none" stroke="${ACOL[sv.a.key]}" stroke-width="2.5"
        stroke-linejoin="round" stroke-linecap="round"/>${dots}`;
    }).join('');
    const labels = dayList.map(([d],i)=>`<text x="${px(i).toFixed(1)}" y="${H-12}"
      fill="var(--dim)" font-size="12" text-anchor="middle">${dmy(d)}</text>`).join('');
    // One hit area per day rather than per point: at this density the points
    // of three accounts overlap, and aiming at a 3.5px dot is not a thing
    // anyone should have to do.
    const cols = dayList.map(([d, v], i) => {
      const w = (W - L - R) / Math.max(1, dayList.length);
      const rows = accs.map(a => {
        const g = v[a.key] || 0;
        return `<i style="--c:${ACOL[a.key]}">${esc(a.short)}</i>`
             + `<b class="${g>0?'up':g<0?'dn':'z'}">${g>0?'+':''}${g}</b>`;
      }).join('');
      return `<rect class="hitc" x="${(px(i) - w/2).toFixed(1)}" y="${TOP}"
        width="${w.toFixed(1)}" height="${H-TOP-BOT}" fill="transparent"
        data-x="${px(i).toFixed(1)}" data-day="${dmy(d)}"
        data-rows="${esc(rows)}"/>`;
    }).join('');
    trend = `<div class="chartwrap"><svg viewBox="0 0 ${W} ${H}" id="trendsvg">
      <line class="guide" x1="0" y1="${TOP}" x2="0" y2="${H-BOT}"
        stroke="var(--line-2)" stroke-width="1" opacity="0"/>
      ${yrules}${lines}${labels}${cols}</svg><div class="ctip" hidden></div></div>`;
  }

  const trendCard = `<div class="chart wide"><h4>Followers gained per day</h4>
    <p class="why">One line per account. Views reset with every post; followers
      are the only thing that accumulates.</p>${trend}
    <div class="legend">${accs.map(a=>
      `<span><i style="background:${ACOL[a.key]}"></i>${esc(a.label)}
        <b style="color:var(--text)">${pa[a.key].followers??'–'}</b></span>`).join('')}</div></div>`;

  // The last handful of posts and how they did: the feedback loop, one line
  // each. Declared out here because more than one tab shows it — it used to
  // live inside the overview branch, which made the Accounts tab throw.
  const recent = AN.rows.slice()
    .filter(r=>!r.promoted)
    .sort((a,b)=>(b.posted_at||0)-(a.posted_at||0)).slice(0,6);
  const latest = `<div class="chart wide"><h4>Latest posts</h4>
    <p class="why">Best account per post, newest first.</p>
    <ul class="tight">${recent.map(r=>`<li>
      <span class="il">${r.untracked ? '<span class="unk">?</span>' : ''}${
        esc(r.name || r.topic)}</span>
      <span class="ir ${r.best>=T?'hit':''}">${fmt(r.best)}</span>
      <span class="is">${aged(r.posted_at)}</span></li>`).join('')}</ul></div>`;

  // Four screens rather than one long scroll. Each fits without scrolling,
  // which is the point: analytics you have to scroll through does not get read.
  const TABS = [['published','Posts'],['accounts','Accounts'],
                ['posts','Compare'],['todo','Act'],['app','App']];
  // Four tabs fit a desktop and do not fit a phone, where they became a
  // sideways scroll that hid the section you were not on. Same state, two
  // controls: the buttons on wide screens, one picker on narrow ones.
  const tabbar = `<div class="subtabs">
    <select class="tabsel" aria-label="Analytics section"
      onchange="anTab=this.value;saveHash();render()">${TABS.map(([v,l])=>
      `<option value="${v}" ${anTab===v?'selected':''}>${l}</option>`).join('')}</select>
    ${TABS.map(([v,l])=>
    `<button class="sub ${anTab===v?'on':''}" onclick="anTab='${v}';saveHash();render()">${l}</button>`).join('')}
    <button class="sub ghost" id="syncbtn" onclick="resync()"
      title="Pull fresh numbers from TikTok">Sync now</button></div>`;

  const sect = (h, p) => `<div class="sect"><h3>${h}</h3><p>${p}</p></div>`;

  // Posts published in a date range, with what each has earned SINCE
  // publishing. Every number here is a running total, never a change during
  // the window — the label says so, because the two are easy to confuse and
  // impossible to tell apart once mixed.
  // Heart, bubble, arrow — the three counters TikTok itself shows, so the
  // glyphs read faster than LIKES/COMM/SHARES and take a third of the width.
  const SVGI = d => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
    style="width:13px;height:13px;vertical-align:-2px">${d}</svg>`;
  const I_LIKE = SVGI('<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>');
  const I_COMM = SVGI('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>');
  const I_SHARE = SVGI('<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="m16 6-4-4-4 4"/><path d="M12 2v13"/>');

  const RANGES = [['today','Today'],['7','7 days'],
                  ['30','30 days'],['all','All']];
  const iso = ts => ts ? new Date(ts*1000).toISOString().slice(0,10) : '';
  const rangeChips = () => `<div class="periods">
      ${RANGES.map(([v,l])=>`<button class="pillp ${anRange===v?'on':''}"
        onclick="setRange('${v}')">${l}</button>`).join('')}
      <span class="acctfilter">${every.map(a=>
        `<button class="pilla ${on(a.key)?'on':'off'}" onclick="toggleAcct('${a.key}')">
           <i style="${on(a.key)?`background:${ACOL[a.key]};border-color:${ACOL[a.key]}`
                               :'background:transparent;border-color:var(--line-2)'}"></i>${esc(a.short)}</button>`).join('')}</span>
    </div>`;

  function publishedView(){
    const P = AN.published;
    // The bar comes first no matter what. Returning early on an empty range
    // took the chips with it and left a page that asked for a date range
    // while offering nothing to pick.
    if(!P) return rangeChips()
      + '<div class="empty">Pick a date range above.</div>';
    const t = P.totals, bar = rangeChips();

    const sameDay = P.to - P.from <= 86400;
    const span = anRange==='today' ? 'today'
               // dstr(0) is Jan 1 1970, which reads as a real date and is not one.
               : anRange==='all' ? 'all time'
               : sameDay ? `on ${dstr(P.from)}`
               : `${dstr(P.from)} – ${dstr(P.to)}`;
    const tiles = `<div class="mgrid">
      ${ctile('Views', t.views, 'earned since publishing')}
      ${ctile('Posts published', t.uploads,
              `${fmt(t.posts)} concept${t.posts===1?'':'s'}, one upload per account`)}
      ${ctile('Likes', t.likes, t.views?`${(100*t.likes/t.views).toFixed(1)}% of views`:'')}
      ${ctile('Comments', t.comments, 'since publishing')}
      ${ctile('Shares', t.shares, 'since publishing')}
      ${ctile('Median per upload', t.median, `${t.hits} of ${t.uploads} over ${fmt(T)}`)}
    </div>`;

    const sorts = [['new','Newest'],['views','Most views'],['rate','Best like rate']];
    const rowsAll = P.rows.slice().sort((a,b)=>
      pubSort==='views' ? b.views-a.views
      : pubSort==='rate' ? b.rate-a.rate
      : postedAt(b)-postedAt(a));
    const shown = pubAll ? rowsAll : rowsAll.slice(0,20);

    const cell = (r,a) => {
      const v = r.cells[a.key];
      if(v==null) return `<span class="pc none" title="not published to ${esc(a.label)}">–</span>`;
      const u = r.urls[a.key];
      const hot = v >= T;
      // The columns to the right are sums; this is the one account.
      const p = (r.per || {})[a.key] || {};
      const rate = v ? (100 * (p.likes||0) / v).toFixed(1) : '0.0';
      const tip = `${a.label}\n${fmt(v)} views · ${fmt(p.likes||0)} likes · `
        + `${fmt(p.comments||0)} comments · ${fmt(p.shares||0)} shares\n${rate}% like rate`;
      return `<a class="pc ${hot?'hot':''}" ${u?`href="${u}" target="_blank" rel="noopener"`:''}
        title="${esc(tip)}" onclick="event.stopPropagation()">
        <i style="background:${ACOL[a.key]}"></i>${fmt(v)}</a>`;
    };

    // Column headings. Without them the three view cells were three numbers
    // with no way to tell which account each belonged to except by colour.
    const phead = `<div class="phead">
      <span class="pth"></span>
      <span class="pnm">post</span>
      <span class="pcells">${accs.map(a=>
        `<span class="pc"><i style="background:${ACOL[a.key]}"></i>${esc(a.short)}</span>`).join('')}</span>
      <span class="peng"><span title="likes">${I_LIKE}</span>
        <span title="comments">${I_COMM}</span><span title="shares">${I_SHARE}</span></span>
      <span class="prate">rate</span>
    </div>`;

    const body = shown.length ? `<div class="plist">${phead}${shown.map(r=>`
      <div class="prow" onclick="open_('${r.topic}')">
        <div class="pth">${r.thumb?`<img loading="lazy" src="${r.thumb}" alt="">`:''}</div>
        <div class="pnm">
          <b>${r.untracked ? `<span class="unk"
              title="Live on the account but not one of our posts: published before the pipeline, or its caption was rewritten. Named from its opening words.">?</span>` : ''}${
            esc(r.name || r.topic)}</b>
          <span>${dayPill(postedAt(r))}${r.pillar?' '+esc(r.pillar):''}${r.promoted?' · <i class="paid">$</i>':''}</span>
        </div>
        <div class="pcells">${accs.map(a=>cell(r,a)).join('')}</div>
        <div class="peng" title="likes · comments · shares, all accounts">
          <span>${fmt(r.likes)}</span><span>${fmt(r.comments)}</span><span>${fmt(r.shares)}</span>
        </div>
        <div class="prate ${r.rate>=AN.like_rate?'good':''}">${r.rate}%</div>
      </div>`).join('')}</div>
      ${rowsAll.length>20&&!pubAll?`<button class="more" onclick="pubAll=true;render()">
        Show all ${rowsAll.length}</button>`:''}`
      : `<div class="empty">Nothing published ${span}.</div>`;

    return bar + sect(`Published ${span}`,
        'Totals are what each post has earned since it went up, not what changed during this window.')
      + tiles
      + `<div class="mxbar"><div class="segs">${sorts.map(([v,l])=>
          `<button class="seg ${pubSort===v?'on':''}" onclick="pubSort='${v}';render()">${l}</button>`).join('')}</div></div>`
      + body;
  }

  let body;
  if(anTab==='published'){
    body = publishedView();
  } else if(anTab==='accounts'){
    const topThree = `<div class="panelrow">${accs.map(a=>{
      const list = (AN.top_per_account||{})[a.key] || [];
      return `<div class="pcard"><h4>${esc(a.label)}</h4>
        <p class="why">Best three, organic.</p>
        <ul class="tight">${list.length ? list.map(x=>
          `<li class="${x.untracked?'':'go'}" ${x.untracked?'':`onclick="open_('${x.topic}')"`}>
             <span class="il">${esc(x.untracked ? (x.title||'untitled').slice(0,24)+'…' : x.topic)}</span>
             <span class="ir hit">${fmt(x.views)}</span>
             <span class="is">${x.rate}% liked</span></li>`).join('')
          : '<li class="none">Nothing yet</li>'}</ul></div>`;}).join('')}</div>`;
    body = rangeChips() + `<div class="duo">${compare}${trendCard}</div>`;
  } else if(anTab==='posts'){
    body = sect('Every post, every account',
           'Shade is log-scaled views. Click a number to open it on TikTok. '
           + '$ marks a promoted post so paid reach stays out of the medians. '
           + 'Last posted turns green once a post is old enough to run again.')
         + matrix;
  } else if(anTab==='app'){
    // The app's own numbers belong beside the posts that sell it: a week of
    // reach that moves no installs is a content problem, and installs that
    // never turn blocking on are a product one.
    if(!USERS) loadUsers();
    body = usersView();
  } else if(anTab==='todo'){
    const stale = AN.stale || [];
    const stalePanel = `<div class="pcard"><h4>Drafts holding a slot</h4>
      <p class="why">Sent, never published. Five pending per account per day, and
        only publishing frees one — deleting does not.</p>
      <ul class="tight">${stale.length ? stale.map(x=>
        `<li class="go" onclick="open_('${x.topic}')">
           <span class="il">${esc(x.topic)}</span>
           <span class="ir ${x.hours>48?'hit':''}">${x.hours}h</span>
           <span class="is">${esc(x.account)}</span></li>`).join('')
        : '<li class="none">Nothing waiting</li>'}</ul>
      <p class="do">Publish these in the TikTok app to free the slots</p></div>`;

    // AN.pillars is keyed by pillar name, not a list.
    const pl = Object.entries(AN.pillars || {})
      .map(([name, v]) => ({name, ...v,
            rate: Math.round(100 * v.broke_out / Math.max(1, v.posts))}))
      .sort((a, b) => b.rate - a.rate);
    const pmax = Math.max(1, ...pl.map(x=>x.rate));
    const pillarPanel = `<div class="chart"><h4>Which angle earns reach</h4>
      <p class="why">Share of posts clearing ${fmt(T)} on at least one account,
        by pillar. Bars rather than a pie: rates compared by length stay
        readable on a phone.</p>
      ${pl.length ? pl.map(x=>`<div class="pbar ${x.posts<5?'thin':''}"
        title="${x.posts<5?'Too few posts to trust this rate':''}">
        <span class="pn">${esc(x.name)}</span>
        <span class="pt"><i style="width:${Math.round(100*x.rate/pmax)}%"></i></span>
        <span class="pv">${x.rate}%</span>
        <span class="ps">${x.posts} post${x.posts===1?'':'s'}</span></div>`).join('')
        : '<p class="why">No pillars tagged yet.</p>'}
      ${pl.some(x=>x.posts<5) ? `<p class="why">Dimmed rows have fewer than five
        posts — one lucky upload reads as 100%.</p>` : ''}
      ${(AN.pillars||{}).unknown ? `<p class="why">${AN.pillars.unknown.posts} posts
        carry no pillar tag, so most of this chart is the "unknown" row. Tagging
        hooks in the pool is what makes this comparison mean anything.</p>` : ''}</div>`;

    const und = AN.undelivered || [];
    const nameOf = k => (accs.find(a=>a.key===k)||{}).short || k;
    const gapPanel = `<div class="pcard ${und.length?'warn':''}"><h4>Did not reach every account</h4>
      <p class="why">A failed send says so. An account with no record at all says
        nothing — the post just ran on two accounts instead of three.</p>
      <ul class="tight">${und.length ? und.map(x=>{
        const gaps = [...x.failed, ...x.missing];
        return `<li>
          <span class="il go" onclick="open_('${x.topic}')">${esc(x.topic)}</span>
          <span class="ir ${x.failed.length?'bad':''}">${
            x.failed.length ? 'failed' : 'missing'}</span>
          <span class="is">${gaps.map(k=>esc(nameOf(k))).join(', ')}</span>
          <button class="cta" onclick="draftGaps(event,'${x.topic}',
            ${JSON.stringify(gaps).replace(/"/g,'&quot;')})">Draft to ${gaps.length===1
              ? esc(nameOf(gaps[0])) : gaps.length + ' accounts'}</button>
        </li>`;}).join('')
        : '<li class="none">Every post reached every account</li>'}</ul>
      ${und.some(x=>x.detail) ? `<p class="why">${esc(und.find(x=>x.detail).detail)}</p>` : ''}
      <p class="do">Each send spends one of five pending slots on that account.</p></div>`;

    body = `<div class="panelrow">${gapPanel}${stalePanel}</div>`
         + `<div class="panelrow">${reshoot}${buried}</div>`;
  } else {
    body = publishedView();
  }
  // The button is re-created on every render, so its state has to be
  // re-applied rather than held on the element.
  setTimeout(paintSync, 0);
  return tabbar + body;
}

function poll(){
  clearTimeout(window._poll2);
  window._poll2 = setTimeout(()=>load().then(()=>{ render(); poll(); }), 8000);
}

const TRASH='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"'
  +' stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>'
  +'<path d="M10 11v6M14 11v6"/></svg>';

// The build strip duplicated the progress card. One place says what is
// happening: the toast bottom-right.
async function cancelBuild(){
  await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cancel:true})});
  await load();
}

const MODE_TAG = {reword:'reworded', reshoot:'new backgrounds', new:'new take'};

// Where a post came from, and what it has spawned. Both matter when deciding
// whether to replicate again: three copies of one concept is enough.
function lineage(p){
  const bits = [];
  if(p.from_replicate)
    bits.push(`<span class="tag rep" title="Replicated from ${esc(p.from_replicate)}">
      ${esc(MODE_TAG[p.replicate_mode]||'replicated')} &middot; ${esc(p.from_replicate)}</span>`);
  if(p.replicated)
    bits.push(`<span class="tag src">replicated ${p.replicated===1?'once':p.replicated+'x'}</span>`);
  return bits.length?`<div class="tags">${bits.join('')}</div>`:'';
}

const fmtn = n => (n || 0).toLocaleString();

// Reach, rounded down to the tier it cleared. The sync already sets the
// performing flag from real view counts, so a button to say so by hand was
// asking for an opinion the numbers had already given.
// The badge is read at a glance across a grid, so it carries one number and
// a colour. Rounding 1,240 down to "1k" threw away the part that separates a
// post that just cleared the bar from one that doubled it.
const TIERS = [[25000,6],[10000,5],[5000,4],[3000,3],[2000,2],[1000,1]];
function tierOf(views){
  const t = TIERS.find(([n]) => views >= n);
  if(!t) return null;
  const k = views / 1000;
  // One decimal below 10k, where the hundreds still say something; whole
  // thousands above it, where they do not.
  const label = k < 10 ? k.toFixed(1).replace('.', ',') + 'k'
                       : Math.round(k) + 'k';
  return {label, lvl: t[1]};
}
function bestViews(p){
  const cells = Object.values(p.stats || {});
  return cells.length ? Math.max(...cells.map(c => c.views || 0)) : 0;
}
function totals(p){
  const cells = Object.values(p.stats || {});
  return cells.reduce((a, c) => ({v: a.v + (c.views||0), l: a.l + (c.likes||0)}),
                      {v: 0, l: 0});
}

function card(p){
  const st = stateOf(p);
  // The same post goes to every account, so per-account chips were three
  // controls for one decision. Only a partial state is worth naming.
  const recs = DATA.accounts.map(a=>({a, r:(p.delivery||{})[a.key]}));
  const failed = recs.filter(x=>x.r && x.r.status==='FAILED');
  const missing = recs.filter(x=>!x.r);
  let note = '';
  if(failed.length)
    note = `<span class="miss" title="${esc(failed.map(x=>x.a.label+': '+(x.r.detail||'')).join(' · '))}">
      failed on ${failed.map(x=>esc(x.a.short)).join(', ')}</span>`;
  else if(missing.length && missing.length < recs.length)
    note = `<span class="miss">not sent to ${missing.map(x=>esc(x.a.short)).join(', ')}</span>`;

  // One action per card, chosen by where the post actually is.
  let act = '';
  if(st==='review' || st==='failed')
    act = `<span class="acts">${p.approved
      ? `<button class="cta sec" onclick="approve(event,'${p.topic}',false)"
           title="Take it back off the Post page">Approved</button>` : ''}
      <button class="cta sec" onclick="cardDraft(event,'${p.topic}')">Draft to all</button></span>`;
  // No Mark published button: the sync reads the account back and sets it.
  else if(st==='published' && p.days_since>=7)
    act = `<button class="cta sec" onclick="cardRepost(event,'${p.topic}')">Repost</button>`;

  const busy = p.queued || (p.redos||[]).length;
  return `<div class="cardwrap" data-topic="${p.topic}">
    ${p.seen?'':`<span class="new" title="${p.from_replicate?'From '+esc(p.from_replicate):'Not opened yet'}"></span>`}
    ${(() => { const t = tierOf(bestViews(p));
      return t ? `<span class="tier t${t.lvl}"
        title="Best account: ${fmtn(bestViews(p))} views">${t.label}</span>` : ''; })()}
    <button class="card" onclick="open_('${p.topic}')">
      <div class="thumb"><img loading="lazy" src="/slide/${p.topic}/${p.slides[0]}"
        alt="First slide of ${esc(p.topic)}">
        <span class="dots" role="button" tabindex="0" title="More"
          onclick="event.stopPropagation();cardMenu('${esc(p.topic)}',event)"
          onkeydown="if(event.key==='Enter'){event.stopPropagation();cardMenu('${esc(p.topic)}',event)}">⋯</span></div>
      <div class="meta">
        <div class="tt">${esc(p.topic)}${busy?' <span class="spin"></span>':''}</div>
        <div class="tms">${p.registered?'':'<span style="color:var(--warn)">no caption · </span>'}${times(p)}</div>
        ${lineage(p)}
      </div>
    </button>
    <div class="cfoot">${(() => { const t = totals(p);
      if(!t.v) return note;
      const rate = (100 * t.l / t.v).toFixed(1);
      return `<span class="cstat" title="All three accounts combined">
        <b>${fmtn(t.v)}</b><span>views</span>
        <b>${fmtn(t.l)}</b><span>likes</span>
        <b class="r">${rate}%</b></span>` + note; })()}${act}</div>
  </div>`;
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
  cur=t; sel=0; redoMode=false; saveHash(); render();
  const p=DATA.posts.find(x=>x.topic===t);
  if(p && !p.seen){
    fetch('/api/seen',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:t})}).then(()=>{ p.seen=true; });
  }
}
function back(){ cur=null; sel=0; redoMode=false; dpAcct=null; dpInfo=null; saveHash(); render(); }

function detail(){
  const p=DATA.posts.find(x=>x.topic===cur);
  if(!p) return back();
  document.getElementById('cnt').textContent='';
  const st = stateOf(p);
  const sent = DATA.accounts.filter(a=>(p.delivery||{})[a.key]);
  const unpub = sent.filter(a=>!((p.delivery||{})[a.key]||{}).published);

  // Exactly one primary, chosen by where the post is. The old three gated
  // sections offered draft and publish two or three times over.
  let primary;
  if(!sent.length || st==='failed')
    primary = `<button class="btn" onclick="draft(null)">Draft to all accounts</button>`;
  else if(unpub.length)
    primary = `<span class="sub">Drafted. The sync marks it published once it is live.</span>`;

  else {
    // Live everywhere. The numbers are the status, so show them rather than
    // a button asking whether this one did well.
    const t = totals(p), tier = tierOf(bestViews(p));
    primary = t.v
      ? `<span class="livestat">${tier ? `<b class="tier inline t${tier.lvl}">${tier.label}</b>` : ''}
           <span>${fmtn(t.v)} views</span><span>${fmtn(t.l)} likes</span>
           <span class="r">${(100*t.l/t.v).toFixed(1)}% liked</span></span>`
      : `<span class="sub">Live. The sync reads the numbers back every 30 minutes.</span>`;
  }


  document.getElementById('view').innerHTML = `
    <div class="actbar">
      <button class="back" onclick="back()">&larr;</button>
      <span class="who2">${esc(p.topic)}${(() => {
        // How this post stays findable. A copy known only by its caption is
        // the one that goes missing when a caption is edited, and that is
        // worth seeing before it happens rather than after.
        const id = p.ident || {};
        const live = Object.values(id).filter(Boolean);
        if(!live.length) return '';
        const weak = live.filter(x => x === 'caption').length;
        return weak
          ? `<span class="idtag weak" title="${weak} live cop${weak===1?'y is':'ies are'} matched only by caption — editing it would detach ${weak===1?'it':'them'}">by caption</span>`
          : `<span class="idtag" title="Every live copy is pinned to its TikTok video id, so a caption edit cannot detach it">pinned</span>`;
      })()}</span>
      ${primary}
      ${['review','failed','archive'].includes(st)?`<button
        class="btn ${p.approved?'sec':''}" onclick="approve(event,'${p.topic}',${!p.approved})">
        ${p.approved?'Approved ✓':'Approve'}</button>`:''}
      <button class="btn sec" onclick="toggleRedo()" aria-pressed="${redoMode}">
        ${redoMode?'Cancel redo':'Redo slides'}</button>
      <button class="btn sec" onclick="menu('rep')">Replicate &#9662;</button>
      ${sent.length?`<button class="btn sec" onclick="cardRepost(event,'${p.topic}')">Repost</button>`:''}
      <button class="btn sec more" onclick="menu('more')">&#8943;</button>
      ${openMenu==='rep'?`<div class="pop">
        <button onclick="replicate('reword')"><b>Reword it</b>
          <span>Same concept and roster, hook and copy rephrased.</span></button>
        <button onclick="replicate('reshoot')"><b>Same words, new backgrounds</b>
          <span>Copy stays identical, photographs swapped.</span></button>
        <button onclick="replicate('new')"><b>New take</b>
          <span>Different hook and a sibling roster.</span></button></div>`:''}
      ${openMenu==='more'?`<div class="pop right">
        ${p.approved?`<button onclick="sendTo('${p.topic}')"><b>Post directly</b>
          <span>Opens this post on the Post page.</span></button>`
         :`<button onclick="approve(event,'${p.topic}',true)"><b>Approve to post</b>
          <span>Only approved posts reach the Post page.</span></button>`}
        <button onclick="askSchedule()"><b>Schedule drafting</b><span>Send later.</span></button>
        <button onclick="del(event,'${p.topic}')"><b>Delete post</b><span>Moves to _deleted.</span></button>
      </div>`:''}
    </div>

    ${schedBar(p)}

    ${redoMode?`<div class="redobar">
      <input id="rnote" autofocus
        placeholder="What is wrong? e.g. the hook is too long, or slide 3 says the wrong thing"
        onkeydown="if(event.key==='Enter')redo()">
      <button class="btn" id="rgo" onclick="redo()">
        ${redoSel.size ? `Redo ${redoSel.size} slide${redoSel.size===1?'':'s'}` : 'Redo'}</button>
      <span class="sub">${redoSel.size
        ? 'Only the picked slides change; the rest come out byte-identical.'
        : 'Say what is wrong and it works out which slides. Click any to narrow it.'}</span>
    </div>`:''}

    <div class="strip">${p.slides.map((s,i)=>
      `<button class="sl ${redoMode&&redoSel.has(i+1)?'picked':''}"
         onclick="${redoMode?`pick(${i+1})`:`zoomAt(${i})`}"
         aria-pressed="${redoMode&&redoSel.has(i+1)}">
         <img loading="lazy" src="/slide/${p.topic}/${s}?v=${(p.slide_mtimes||{})[s]||0}"
              alt="Slide ${i+1}">
         <span class="num">${i+1}</span></button>`).join('')}</div>

    <div class="copyrow">
      <div class="field"><label for="ti">Title</label>
        <input id="ti" value="${esc(p.title)}" onblur="save()"></div>
      <div class="field"><label for="ca">Caption</label>
        <textarea id="ca" onblur="save()">${esc(p.caption)}</textarea></div>
    </div>
    ${(p.redos||[]).length?`<div class="log on">${
      (p.redos||[]).map(r=>'slides '+((r.slides||[r.slide]).join(', '))+': '+esc(r.note)).join('\n')}</div>`:''}
    <div class="log" id="log"></div>`;
}

// The two things you actually do to a post live at the top, so a drafted or
// published post never needs scrolling to reach them.




async function approve(e, topic, yes){
  if(e) e.stopPropagation();
  const p = DATA.posts.find(x=>x.topic===topic);
  if(p) p.approved = yes;          // paint before the fetch, like marking published
  render();
  await fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, approved:yes})});
  await load(); render();
}

async function publishAll(){
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur, published:true})});
  await load(); render();
}

// Direct Post settings, per account. TikTok's content-sharing guidelines make
// most of this mandatory: the privacy list must come from the creator, no
// default may be preselected, a control the creator disabled must be shown
// disabled, and the commercial disclosure must gate the publish button.
//
// This panel is also the audit deliverable. TikTok reviews a video of it, not
// the API calls, so every control below has to stay visible even when it is
// inapplicable — a missing disclosure toggle is a disqualification.

const PRIV_LABEL = {
  PUBLIC_TO_EVERYONE: 'Everyone',
  MUTUAL_FOLLOW_FRIENDS: 'Friends',
  FOLLOWER_OF_CREATOR: 'Followers',
  SELF_ONLY: 'Only me',
};

// Opening the panel re-reads the creator's settings. Never render the form
// from a cached copy: what the creator allows can change between posts.
async function openDirect(key){
  openMenu = null;
  if(dpAcct === key) return closeDirect();
  dpAcct = key; dpInfo = null; dpBusy = false;
  dpSet = {privacy:'', disable_comment:false, auto_add_music:false,
           disclose:false, brand_organic:false, branded_content:false};
  render();
  try{
    const res = await fetch('/api/creator_info?account='+encodeURIComponent(key));
    dpInfo = await res.json();
  }catch(err){
    dpInfo = {error: err.message};
  }
  if(dpAcct === key) render();
}
function closeDirect(){ dpAcct=null; dpInfo=null; render(); }

// From a post straight into the Post page with it already chosen.
function sendTo(topic){
  openMenu=null; cur=null; dpTopic=topic; dpAcct=null; dpInfo=null;
  filter='post'; saveHash(); render();
}

function dpSetVal(k, v){
  dpSet[k] = v;
  // Branded content cannot be private. The server refuses the pair too, but
  // the guidelines want the option gone from the UI, not rejected on submit.
  if(k === 'branded_content' && v && dpSet.privacy === 'SELF_ONLY') dpSet.privacy = '';
  if(k === 'disclose' && !v){ dpSet.brand_organic = false; dpSet.branded_content = false; }
  render();
}

// Nothing may publish until a privacy level is chosen, and if the post is
// declared commercial, until it is said which kind.
function dpReady(){
  if(!dpSet.privacy) return false;
  if(dpSet.disclose && !dpSet.brand_organic && !dpSet.branded_content) return false;
  return true;
}

// The Post page. Direct posting is the one flow here that publishes without a
// second pair of eyes, so it gets a destination of its own rather than a menu
// item: you go there deliberately, pick the post, then the account.
// Approving in Review is what puts a post here. Nothing reaches the account
// without that step, which is the only human gate left once posting is direct.
const postable = p => p.approved && (p.slides||[]).length > 0
                   && stateOf(p) !== 'published';

function postView(){
  const list = DATA.posts.filter(postable).sort((a,b)=>whenOf(b)-whenOf(a));
  document.getElementById('cnt').textContent =
    `${list.length} post${list.length===1?'':'s'}`;

  // Anything already queued to go out on its own belongs at the top: it is the
  // only state here that acts while you are not looking.
  const queued = DATA.posts.flatMap(p =>
    (p.schedules||[]).filter(s=>!s.done).map(s=>({p, s})));

  if(!list.length) return `<div class="empty">No finished posts to send yet.</div>`;

  const cards = list.map(p=>{
    const cover = (p.slides||[])[0];
    const done = DATA.accounts.filter(a=>((p.delivery||{})[a.key]||{}).published).length;
    const sent = DATA.accounts.filter(a=>(p.delivery||{})[a.key]).length;
    return `<button class="pk ${dpTopic===p.topic?'on':''}"
        onclick="pickPost('${p.topic}')">
      ${cover?`<img loading="lazy" src="/slide/${p.topic}/${cover}?v=${(p.slide_mtimes||{})[cover]||0}" alt="">`:''}
      <span class="m">
        <span class="t">${esc(p.topic)}</span>
        <span class="d">${(p.slides||[]).length} slides &middot;
          ${sent?`${done} of ${sent} live`:'not sent'} &middot; ${times(p)}</span>
      </span>
    </button>`;
  }).join('');

  return `
    ${queued.length?`<div class="panel" style="max-width:760px">
      <h2>Going out on its own</h2>
      ${queued.map(({p,s})=>{
        const who = (s.accounts||[]).map(label).join(', ') || 'all accounts';
        const priv = s.mode==='direct'
          ? (PRIV_LABEL[(s.settings||{}).privacy] || (s.settings||{}).privacy || '?') : '';
        return `<div class="schedbar ${s.mode==='direct'?'direct':''}">
          <b>${esc(p.topic)} &mdash; ${s.mode==='direct'?'posts directly':'drafts'} to ${esc(who)}</b>
          <span class="when">${fmt(s.at)}</span>
          ${priv?`<span class="sub">visible to "${esc(priv)}"</span>`:''}
          <button class="btn sec" onclick="cancelSched('${p.topic}')">Cancel</button>
        </div>`;}).join('')}
    </div>`:''}

    <div class="postwrap">
      <div class="picker">
        <span class="cap-l">Choose a post</span>
        ${cards}
      </div>
      <div class="composer">${composerPane()}</div>
    </div>`;
}

// Selecting a post on the Post page. Separate from `cur` on purpose: opening a
// post to review it should not arm a publish.
function pickPost(topic){
  dpTopic = topic;
  if(dpAcct) return openDirect(dpAcct);   // re-read for the newly chosen post
  render();
}

function composerPane(){
  if(!dpTopic) return `<div class="empty">Pick a post to send.</div>`;
  const p = DATA.posts.find(x=>x.topic===dpTopic);
  if(!p){ dpTopic=null; return `<div class="empty">That post is gone.</div>`; }
  if(!dpAcct){
    return `<div class="panel dp"><div class="sec">
      <span class="cap-l">Send ${esc(p.topic)} to</span>
      <div class="acctpick">${DATA.accounts.map(a=>{
        const r = (p.delivery||{})[a.key];
        const state = !r ? 'not sent yet'
                    : r.published ? 'already live there'
                    : r.status==='SENT' ? 'drafted, waiting in the inbox'
                    : 'last attempt failed';
        return `<button class="pa" onclick="openDirect('${a.key}')">
          <span class="t">@${esc(a.label)}</span><span class="d">${state}</span>
        </button>`;}).join('')}</div>
      <span class="note">Posting here publishes straight to the account. To send
        a draft to the inbox instead, use Draft on the post itself.</span>
    </div></div>`;
  }
  return directPanel(p);
}

function directPanel(p){
  const a = DATA.accounts.find(x=>x.key===dpAcct);
  if(!a) return '';
  const shell = inner => `<div class="panel dp"><div class="sec">${inner}</div></div>`;

  if(!dpInfo) return shell(
    `<span class="cap-l">Posting to TikTok</span>
     <span class="sub">Reading ${esc(a.label)}'s settings from TikTok…</span>`);
  if(dpInfo.error) return shell(
    `<span class="cap-l">Posting to TikTok</span>
     <span class="sub bad">Could not read this creator's settings: ${esc(dpInfo.error)}</span>
     <div class="actions" style="margin-top:16px">
       <button class="btn sec" onclick="closeDirect()">Close</button></div>`);

  const opts = dpInfo.privacy_level_options || [];
  const nick = dpInfo.creator_nickname || a.label;
  const uname = dpInfo.creator_username ? '@'+dpInfo.creator_username : '';
  const avatar = dpInfo.creator_avatar_url
    ? `<img class="av" src="${esc(dpInfo.creator_avatar_url)}" alt="">` : '';

  // A level the creator does not offer is never listed, and SELF_ONLY
  // disappears entirely once the post is declared branded content.
  const usable = opts.filter(o => !(o === 'SELF_ONLY' && dpSet.branded_content));
  const label = dpSet.branded_content ? 'Paid partnership'
              : dpSet.brand_organic  ? 'Promotional content' : '';

  // One switch, rendered the same way everywhere so the rows line up.
  const sw = (on, attrs) =>
    `<span class="sw"><input type="checkbox" ${on?'checked':''} ${attrs}><i></i></span>`;
  const row = (title, desc, control, cls='') =>
    `<div class="row ${cls}"><span class="txt"><span class="t">${title}</span>
       ${desc?`<span class="d">${desc}</span>`:''}</span>${control}</div>`;

  return `<div class="panel dp">
    <div class="sec">
      <span class="cap-l">Posting to TikTok</span>
      <div class="who">${avatar}<span class="nm">
        <b>${esc(nick)}</b><span>${esc(uname)}</span></span></div>
    </div>

    <div class="sec">
      <label for="dppriv">Who can view this post <span class="req">*</span></label>
      <select id="dppriv" onchange="dpSetVal('privacy', this.value)">
        <option value=""${dpSet.privacy?'':' selected'}>Select who can view…</option>
        ${usable.map(o=>`<option value="${o}"${dpSet.privacy===o?' selected':''}
          >${esc(PRIV_LABEL[o]||o)}</option>`).join('')}
      </select>
      ${dpSet.branded_content && opts.includes('SELF_ONLY')
        ? `<span class="note">Branded content cannot be private, so "Only me" is unavailable.</span>` : ''}
    </div>

    <div class="sec">
      <span class="cap-l">Interactions</span>
      ${row('Comment',
            dpInfo.comment_disabled ? 'Turned off by the creator on TikTok.' : '',
            sw(!dpSet.disable_comment,
               `${dpInfo.comment_disabled?'disabled':''} aria-label="Allow comments"
                onchange="dpSetVal('disable_comment', !this.checked)"`),
            dpInfo.comment_disabled?'muted':'')}
      ${row('Duet', 'Video posts only — not available for photo posts.',
            sw(false, 'disabled aria-label="Duet"'), 'muted')}
      ${row('Stitch', 'Video posts only — not available for photo posts.',
            sw(false, 'disabled aria-label="Stitch"'), 'muted')}
      ${row('Add recommended music', 'Lets TikTok pick a track for the slideshow.',
            sw(dpSet.auto_add_music,
               `aria-label="Add recommended music"
                onchange="dpSetVal('auto_add_music', this.checked)"`))}
    </div>

    <div class="sec">
      <span class="cap-l">Disclosure</span>
      ${row('Disclose post content',
            'Turn on to disclose that this post promotes yourself, a third party, or both.',
            sw(dpSet.disclose,
               `aria-label="Disclose post content"
                onchange="dpSetVal('disclose', this.checked)"`))}
      ${dpSet.disclose?`<div class="disc">
        <div class="opts">
          <label class="chk"><input type="checkbox" ${dpSet.brand_organic?'checked':''}
            onchange="dpSetVal('brand_organic', this.checked)"> Your Brand</label>
          <label class="chk"><input type="checkbox" ${dpSet.branded_content?'checked':''}
            onchange="dpSetVal('branded_content', this.checked)"> Branded Content</label>
        </div>
        ${label?`<span class="note warn">Your photo post will be labeled
          "${label}". This cannot be changed once posted.</span>`
         :`<span class="note">Pick at least one to continue.</span>`}
      </div>`:''}
    </div>

    <div class="sec">
      <span class="cap-l">Preview</span>
      <div class="prev">${p.slides.map((s,i)=>
        `<img loading="lazy" src="/slide/${p.topic}/${s}?v=${(p.slide_mtimes||{})[s]||0}"
           alt="Slide ${i+1}">`).join('')}</div>
      <div class="cap-t">${esc(p.title)}</div>
      <div class="cap-b">${esc(p.caption)}</div>
    </div>

    <div class="consent">By posting, you agree to TikTok's
      ${dpSet.branded_content
        ? `<a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank"
             rel="noopener">Branded Content Policy</a> and `:''}
      <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en"
         target="_blank" rel="noopener">Music Usage Confirmation</a>.</div>

    <div class="foot">
      <button class="btn" ${dpReady() && !dpBusy?'':'disabled'}
        onclick="publishDirect()">${dpBusy?'Posting…':'Post to '+esc(a.label)}</button>
      <button class="btn sec" ${dpReady() && !dpBusy?'':'disabled'}
        onclick="scheduleDirect()">Schedule instead</button>
      <button class="btn sec" onclick="closeDirect()">Cancel</button>
      <span class="hint">After posting it may take a few minutes to appear on the
        profile. A scheduled post goes out with exactly these settings, and only
        while the dashboard is running.</span>
    </div>
  </div>`;
}

// A pending schedule was invisible until now, which is survivable for a draft
// and not for a direct post: that one publishes unattended, so it has to be
// something you can see coming and call off.
function schedBar(p){
  const rows = (p.schedules||[]).filter(s=>!s.done);
  if(!rows.length) return '';
  return rows.map(s=>{
    const who = (s.accounts||[]).map(label).join(', ') || 'all accounts';
    const priv = s.mode==='direct'
      ? (PRIV_LABEL[(s.settings||{}).privacy] || (s.settings||{}).privacy || '?') : '';
    return `<div class="schedbar ${s.mode==='direct'?'direct':''}">
      <b>${s.mode==='direct'?'Posts directly':'Drafts'} to ${esc(who)}</b>
      <span class="when">${fmt(s.at)}</span>
      ${priv?`<span class="sub">visible to "${esc(priv)}"</span>`:''}
      <button class="btn sec" onclick="cancelSched('${p.topic}')">Cancel</button>
    </div>`;
  }).join('');
}

async function cancelSched(topic){
  await fetch('/api/schedule',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, cancel:true})});
  await load(); render();
  say('Schedule cancelled. Nothing will go out on its own.');
}

// The settings the panel has collected, in the shape the API takes. Shared by
// posting now and scheduling, so a scheduled post cannot drift from what the
// panel showed when the choices were made.
function dpPayload(){
  return {
    privacy: dpSet.privacy,
    disable_comment: dpSet.disable_comment,
    auto_add_music: dpSet.auto_add_music,
    brand_organic: dpSet.disclose && dpSet.brand_organic,
    branded_content: dpSet.disclose && dpSet.branded_content,
  };
}

function scheduleDirect(){
  if(!dpReady() || dpBusy) return;
  const key = dpAcct, a = DATA.accounts.find(x=>x.key===key);
  const d = new Date(Date.now()+3600e3); d.setSeconds(0,0);
  const iso = new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);
  const priv = PRIV_LABEL[dpSet.privacy] || dpSet.privacy;
  showModal({
    title:'Schedule this post',
    body:`It posts straight to ${a.label} at the time you pick, visible to `
        +`"${priv}". The dashboard has to be running when it comes due.`,
    ok:'Schedule',
    extra:`<div class="sched"><div><label for="dpwhen">When</label>
      <input type="datetime-local" id="dpwhen" value="${iso}"></div></div>`,
    action: async()=>{
      const at = new Date(document.getElementById('dpwhen').value).getTime()/1000;
      if(!at) return say('That date could not be read; nothing was scheduled.');
      const res = await fetch('/api/schedule',{method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({topic:dpTopic, at, accounts:[key], mode:'direct',
                             settings:dpPayload()})});
      const r = await res.json().catch(()=>({}));
      if(!res.ok) return say('Not scheduled: '+(r.error||('server returned '+res.status)));
      dpAcct=null; dpInfo=null;
      await load(); render();
      say('Scheduled. It posts to '+key+' at '
          +new Date(at*1000).toLocaleString()+'.');
    }});
}

async function publishDirect(){
  if(!dpReady() || dpBusy) return;
  if (blockedOffline()) return;
  const key = dpAcct;
  dpBusy = true; render();
  say('Posting directly. The publish is polled until TikTok reports it complete.');
  let txt;
  try{
    const res = await fetch('/api/publish_direct',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:dpTopic, account:key, settings:dpPayload()})});
    const r = await res.json();
    if(!res.ok) throw new Error(r.error || ('server returned '+res.status));
    txt = 'Posting to '+key+'. The delivery log records the result when TikTok finishes.';
    dpAcct = null; dpInfo = null;
  }catch(err){
    txt = 'Direct post failed: '+err.message;
  }
  dpBusy = false;
  await load();
  say(txt);
}

function menu(which){ openMenu = openMenu===which ? null : which; render(); }

// Marking is the highest-frequency action in the tool, so it patches local
// state and paints before the fetch lands. A full reload here used to throw
// away scroll position on every single click.
async function chip(e, topic, key){
  e.stopPropagation();
  const p=DATA.posts.find(x=>x.topic===topic);
  const r=(p.delivery||{})[key];
  if(!r || r.status!=='SENT') return;
  const now = !r.published;
  r.published = now; r.published_at = now ? Date.now()/1000 : null;
  render();
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, account:key, published:now})});
  await load(); render();
}

async function cardPublished(e, topic){
  e.stopPropagation();
  const p=DATA.posts.find(x=>x.topic===topic);
  DATA.accounts.forEach(a=>{ const r=(p.delivery||{})[a.key];
    if(r && r.status==='SENT' && !r.published){ r.published=true; r.published_at=Date.now()/1000; } });
  render();
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, published:true})});
  await load(); render();
}

function cardDraft(e, topic){ e.stopPropagation(); cur=topic; draft(null); }

// Only the accounts that never got it. Re-sending to all three would spend
// slots on accounts that already have the post.
async function draftGaps(e, topic, accts){
  e.stopPropagation();
  cur = topic;
  await draft(accts);
  AN = null;
  loadAnalytics();
}

// Reposting sends slides that are already on Pages, so there is no agent and
// no rebuild: it is the same delivery path a second time.
function cardRepost(e, topic){
  if(e) e.stopPropagation();
  openMenu=null;
  const p=DATA.posts.find(x=>x.topic===topic);
  const was = DATA.accounts.filter(a=>((p.delivery||{})[a.key]||{}).published).map(a=>a.key);
  const pick = was.length?was:DATA.accounts.map(a=>a.key);
  const pend = DATA.pending || {};
  showModal({
    title:'Repost', ok:'Re-draft now',
    body:`<b>${esc(topic)}</b> goes out again as fresh inbox drafts — the same
      slides, nothing rebuilt. You publish them from the TikTok app as usual.`,
    extra:`<div class="accpick">${DATA.accounts.map(a=>{
      const free = Math.max(0, (DATA.cap||5) - (pend[a.key]||0));
      const went = ((p.delivery||{})[a.key]||{}).published;
      return `<label class="chk acc ${free?'':'full'}">
         <input type="checkbox" class="rp" value="${a.key}"
           ${pick.includes(a.key)&&free?'checked':''} ${free?'':'disabled'}>
         <span class="nm">${esc(a.label)}</span>
         <span class="sub">${free ? free+' of '+(DATA.cap||5)+' slots free'
                                  : 'no slots left today'}${went?' · went out before':''}</span>
       </label>`}).join('')}</div>`,
    action: async()=>{
      const keys=[...document.querySelectorAll('.rp:checked')].map(x=>x.value);
      if(!keys.length) return;
      cur = topic; await draft(keys);
    }});
}

function label(k){ return (DATA.accounts.find(a=>a.key===k)||{}).label || k; }
function fmt(ts){ const d=new Date(ts*1000);
  return d.toLocaleString([], {weekday:'short', day:'numeric', month:'short',
                               hour:'2-digit', minute:'2-digit'}); }

let onOK=null;
function showModal({title, body='', extra='', ok='Confirm', danger=false, action}){
  document.getElementById('mt').textContent=title;
  document.getElementById('mb').innerHTML=body;
  document.getElementById('mx').innerHTML=extra;
  const b=document.getElementById('mok');
  b.textContent=ok; b.className='btn'+(danger?' danger':'');
  onOK=action; document.getElementById('modal').style.display='flex';
  const f=document.querySelector('#mx input,#mx select'); if(f) f.focus();
}
function closeModal(){ document.getElementById('modal').style.display='none'; onOK=null; }
document.getElementById('mok').onclick=async()=>{ const f=onOK; closeModal(); if(f) await f(); };
document.getElementById('modal').onclick=e=>{ if(e.target.id==='modal') closeModal(); };

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

function toggleRedo(){ redoMode=!redoMode; redoSel=new Set(); openMenu=null; render(); }

function zoomAt(i){
  const p=DATA.posts.find(x=>x.topic===cur); if(!p) return;
  saveHash();
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
  if(cur) saveHash(); }
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

function pick(n){
  if(redoSel.has(n)) redoSel.delete(n); else redoSel.add(n);
  render();
  const t=document.getElementById('rnote'); if(t) t.focus();
}
function zoomSel(){ if(sel) zoomAt(sel-1); }
async function redo(){
  if (blockedOffline()) return;
  const note=(document.getElementById('rnote')||{}).value||'';
  const slides=[...redoSel].sort((a,b)=>a-b);
  if(!note.trim()) return say('Say what is wrong first.');
  const topic = cur;
  redoMode=false; redoSel=new Set();
  await fetch('/api/redo',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, slides, note})});
  // Stay on the post. This used to jump back to the list so the run was
  // visible, but the job panel is on every page now, so the jump only ever
  // read as the page refreshing itself for no reason.
  await load(); render();
}

// The recorded reason plus what it means. "the dashboard restarted mid-run"
// is accurate and tells you nothing about whether to try again.
function whyPlain(r){
  const w = r.why || '';
  if(/restarted (mid-run|while)/i.test(w))
    return 'The run was gone when the dashboard came back — it had already died on its own. Nothing was written. Retry is safe.';
  if(/session limit|usage limit/i.test(w))
    return w + ' — retry after it resets.';
  if(/not logged in/i.test(w))
    return 'The claude CLI is not signed in on this machine. Run claude once in a terminal, then retry.';
  if(/no caption/i.test(w))
    return w + ' The slides exist; only the hooks.json entry is missing.';
  return w || 'No reason was recorded.';
}

async function retryRun(kind, at){
  await fetch('/api/retry', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({kind, at})});
  say('Queued again.');
  jobsOpen = true;
  await load();
}

async function dismissFails(){
  await fetch('/api/dismiss', {method:'POST',
    headers:{'Content-Type':'application/json'}, body:'{}'});
  jobsOpen = false;
  await load();
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
const REP_LABEL = {reword:'Rewording', reshoot:'Re-shooting', new:'New take from'};
const REP_SUB = {
  reword:'Same concept and roster, hook and copy rephrased.',
  reshoot:'Copy stays identical, backgrounds swapped.',
  new:'Different hook and a sibling roster.'};

async function replicate(mode){
  if (blockedOffline()) return;
  const topic = cur;
  openMenu=null;
  await fetch('/api/replicate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, mode})});
  filter='review'; back();
  await load(); render();
}
async function publish(key,v){
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur,account:key,published:v})}); await load();
}
async function publishedAll(key){
  await fetch('/api/published',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({account:key})}); await load();
}
// Drafting blocks for as long as three accounts take to reach
// SEND_TO_USER_INBOX. Without something on screen it reads as a dead click,
// so the toast names each account and settles into a result per row.
function toastStart(keys){
  const rows = keys.map(k=>`<div class="trow" id="tr-${k}">
      <span class="mk"><span class="spin"></span></span>
      <span>${esc(label(k))}</span></div>`).join('');
  document.getElementById('toast').innerHTML = `<div class="toast" id="tst">
    <h5><span class="spin"></span>Drafting to ${keys.length} account${keys.length===1?'':'s'}</h5>
    <div class="sub" style="font-size:11px">Each one polls until TikTok confirms the inbox draft.</div>
    ${rows}</div>`;
}

function toastDone(results){
  const el = document.getElementById('tst');
  if(!el) return;
  const rs = Object.entries(results||{});
  const good = rs.filter(([,v])=>v.status==='SENT').length;
  const all = good === rs.length && rs.length > 0;
  el.querySelector('h5').innerHTML = all
    ? `<span class="ok">&#10003;</span>Drafted to ${good} account${good===1?'':'s'}`
    : `<span class="bad">!</span>${good} of ${rs.length} drafted`;
  el.querySelector('.sub').textContent = all
    ? 'They are waiting in each TikTok inbox.'
    : 'Open the post for the failure detail.';
  rs.forEach(([k,v])=>{
    const row = document.getElementById('tr-'+k);
    if(!row) return;
    const ok = v.status==='SENT';
    row.querySelector('.mk').innerHTML = ok
      ? '<span class="ok">&#10003;</span>' : '<span class="bad">&#10007;</span>';
    if(v.detail) row.insertAdjacentHTML('beforeend',
      `<span class="dt">${esc(v.detail)}</span>`);
  });
  // A clean run needs no dismissing; a failure stays until it is read.
  if(all) setTimeout(()=>{ const t=document.getElementById('toast'); if(t) t.innerHTML=''; }, 4500);
  else setTimeout(()=>{ const t=document.getElementById('toast'); if(t) t.innerHTML=''; }, 12000);
}

// Redo and replicate hand work to a background agent, so unlike drafting
// there is no response to wait on. The toast is driven by DATA.runs instead:
// it stays up while a run mentioning this topic is alive, and resolves when
// the run disappears.



// Called from load(). A run has to be seen alive at least once before its
// absence counts as finished, otherwise the poll that fires before the agent
// registers would mark it done immediately.

function blockedOffline(){
  if (!STALE) return false;
  say('Not while the data is a saved copy — the machine that owns it decides '
      + 'what has already been sent, and acting on a stale copy is how a post '
      + 'goes out twice.');
  return true;
}

async function draft(accts){
  if (blockedOffline()) return;
  const keys = accts || DATA.accounts.map(a=>a.key);
  toastStart(keys);
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
    toastDone(r.results);
  }catch(err){
    txt = 'Draft failed: '+err.message+'\nNothing was recorded. The server log has the detail.';
    toastDone(Object.fromEntries(keys.map(k=>[k,{status:'FAILED',detail:err.message}])));
  }
  await load();            // always re-render so buttons come back enabled
  say(txt);
}

// The chart's hover. Delegated from the document because the SVG is redrawn
// on every render and a bound listener would not survive it.
document.addEventListener('mousemove', e => {
  const wrap = document.querySelector('.chartwrap');
  if(!wrap) return;
  const tip = wrap.querySelector('.ctip');
  const guide = wrap.querySelector('.guide');
  const col = e.target.closest && e.target.closest('.hitc');
  if(!col){ if(tip) tip.hidden = true; if(guide) guide.setAttribute('opacity','0'); return; }
  const svg = wrap.querySelector('svg');
  const box = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  const x = +col.dataset.x;
  guide.setAttribute('x1', x); guide.setAttribute('x2', x);
  guide.setAttribute('opacity', '.8');
  tip.innerHTML = `<b>${col.dataset.day}</b><div class="tr">${col.dataset.rows}</div>`;
  tip.hidden = false;
  tip.style.left = (x / vb.width * box.width) + 'px';
  tip.style.top  = (28 / vb.height * box.height) + 'px';
});

// One boot sequence, then never again: the class comes off as soon as it
// has played, so a re-render cannot replay it.
document.body.classList.add('boot');
setTimeout(() => document.body.classList.remove('boot'), 1100);

load().then(() => {
  restoreHash();
  // restoreHash only sets state; something has to draw it. This used to be
  // setApp(), which rendered as a side effect of picking the app — so
  // removing the app switcher left the page permanently blank.
  render();
});
</script></body></html>"""


# A device frame for designing the phone layout on a desktop screen. Held
# separate from PAGE so nothing here can leak into the real dashboard.
PHONE_FRAME = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><title>ARCO — phone preview</title>
<link rel="icon" href="/favicon.png">
<style>
:root{--bg:#020617;--surface:#0b1220;--line:#1e293b;--line2:#334155;
      --text:#e2e8f0;--dim:#64748b;--accent:#38bdf8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font:14px/1.4 ui-sans-serif,system-ui,-apple-system,"SF Pro Text",sans-serif;
  min-height:100vh;display:flex;flex-direction:column;align-items:center}
header{display:flex;align-items:center;gap:14px;flex-wrap:wrap;
  padding:14px 20px;width:100%;border-bottom:1px solid var(--line);
  background:var(--surface);position:sticky;top:0;z-index:10}
.ttl{font-weight:600;letter-spacing:-.01em}
.ttl span{color:var(--dim);font-weight:400;margin-left:8px;font-size:12.5px}
.seg{display:flex;gap:2px;background:#020617;border:1px solid var(--line);
  border-radius:9px;padding:2px}
.seg button{background:none;border:0;color:var(--dim);cursor:pointer;
  font:500 12px/1 inherit;padding:7px 11px;border-radius:7px;white-space:nowrap}
.seg button.on{background:var(--line);color:var(--text)}
.seg button:hover:not(.on){color:var(--text)}
.sp{margin-left:auto;display:flex;gap:8px;align-items:center}
.btn{background:#020617;border:1px solid var(--line);color:var(--dim);
  border-radius:9px;padding:8px 12px;font:500 12px/1 inherit;cursor:pointer}
.btn:hover{color:var(--text);border-color:var(--line2)}
.dims{font:400 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--dim)}
main{flex:1;display:flex;align-items:flex-start;justify-content:center;
  padding:26px 20px 40px;width:100%}
/* The bezel is cosmetic. The iframe inside is the real viewport, at exactly
   the device's CSS pixel size, so the media queries fire as they would. */
.device{background:#0f172a;border:1px solid var(--line2);border-radius:44px;
  padding:11px;box-shadow:0 30px 80px rgba(0,0,0,.6);transform-origin:top center}
.screen{position:relative;border-radius:34px;overflow:hidden;background:#000}
.notch{position:absolute;top:9px;left:50%;transform:translateX(-50%);
  width:106px;height:29px;background:#000;border-radius:16px;z-index:5;
  pointer-events:none}
iframe{display:block;border:0;background:var(--bg)}
</style></head><body>
<header>
  <div class="ttl">Phone preview<span id="note">dev instance · port 4501</span></div>
  <div class="seg" id="devs"></div>
  <div class="seg" id="zooms"></div>
  <div class="sp">
    <span class="dims" id="dims"></span>
    <button class="btn" id="rl">Reload</button>
    <button class="btn" id="open">Open full</button>
  </div>
</header>
<main><div class="device" id="dev">
  <div class="screen" id="scr"><div class="notch" id="notch"></div>
    <iframe id="f" src="/"></iframe></div>
</div></main>
<script>
const DEVICES = [
  {id:'se',  name:'SE',        w:375, h:667, notch:false},
  {id:'15',  name:'15/16',     w:393, h:852, notch:true},
  {id:'max', name:'Pro Max',   w:430, h:932, notch:true},
  {id:'mini',name:'13 mini',   w:375, h:812, notch:true},
];
const ZOOMS = [100, 90, 80, 70];
let dev = localStorage.getItem('pf.dev') || '15';
let zoom = +(localStorage.getItem('pf.zoom') || 100);

function paint(){
  const d = DEVICES.find(x=>x.id===dev) || DEVICES[1];
  const f = document.getElementById('f');
  f.style.width  = d.w + 'px';
  f.style.height = d.h + 'px';
  document.getElementById('scr').style.width  = d.w + 'px';
  document.getElementById('scr').style.height = d.h + 'px';
  document.getElementById('notch').style.display = d.notch ? 'block' : 'none';
  document.getElementById('dev').style.transform = 'scale(' + (zoom/100) + ')';
  document.getElementById('dims').textContent = d.w + ' x ' + d.h;
  document.getElementById('devs').innerHTML = DEVICES.map(x =>
    `<button data-d="${x.id}" class="${x.id===dev?'on':''}">${x.name}</button>`).join('');
  document.getElementById('zooms').innerHTML = ZOOMS.map(z =>
    `<button data-z="${z}" class="${z===zoom?'on':''}">${z}%</button>`).join('');
  localStorage.setItem('pf.dev', dev);
  localStorage.setItem('pf.zoom', zoom);
}
document.getElementById('devs').onclick = e => {
  const b = e.target.closest('[data-d]'); if(!b) return; dev = b.dataset.d; paint(); };
document.getElementById('zooms').onclick = e => {
  const b = e.target.closest('[data-z]'); if(!b) return; zoom = +b.dataset.z; paint(); };
document.getElementById('rl').onclick = () => {
  const f = document.getElementById('f'); f.src = f.src; };
document.getElementById('open').onclick = () => window.open('/', '_blank');
// R reloads the frame, not the harness, so a design pass is one keystroke.
addEventListener('keydown', e => {
  if((e.key==='r'||e.key==='R') && !e.metaKey && !e.ctrlKey){
    e.preventDefault(); const f=document.getElementById('f'); f.src=f.src; }
});
paint();
</script></body></html>"""


class Server(socketserver.ThreadingTCPServer):
    """Threaded, because a delivery takes minutes.

    On the single-threaded server one Draft call blocked every other request,
    so slides stopped loading and the whole dashboard looked broken until the
    send finished.
    """
    allow_reuse_address = True
    daemon_threads = True


def clean_history():
    """Rewrite stats_history.json, dropping points that cannot be true.

    Before video ids were pinned, two live videos sharing a caption were both
    appended to one series, so a topic's history ping-ponged between two
    posts' view counts. Views are cumulative, so the repair is to walk each
    series backwards from its final point — which agrees with post_stats and
    is therefore trustworthy — keeping only points no higher than the one
    after them. The interloper series falls out.
    """
    hist = load(STATS_HISTORY, {})
    bak = STATS_HISTORY + '.bak'
    with open(bak, 'w') as fh:
        json.dump(hist, fh, ensure_ascii=False)
    kept = dropped = 0
    for topic, per in hist.items():
        for key, arr in per.items():
            arr.sort(key=lambda x: x['at'])
            out, ceiling = [], None
            for pt in reversed(arr):
                if ceiling is None or pt['views'] <= ceiling:
                    out.append(pt)
                    ceiling = pt['views']
                else:
                    dropped += 1
            out.reverse()
            kept += len(out)
            per[key] = out
    with open(STATS_HISTORY, 'w') as fh:
        json.dump(hist, fh, ensure_ascii=False)
    print('kept %d points, dropped %d, backup at %s' % (kept, dropped, bak))


if __name__ == '__main__':
    if '--clean-history' in sys.argv:
        clean_history()
        raise SystemExit(0)
    # In-flight runs are detached, so a restart does not end them. Deciding
    # what happened to each one is reconcile_queues' job, below — this used
    # to mark them all interrupted first, which threw away live work.
    backfill_built_at()
    if UPSTREAM:
        print('[proxy] api -> %s' % UPSTREAM)
        # In the background: opening two connections to the far side of the
        # world took longer than the launcher waits, so the server looked as
        # though it had failed to start.
        threading.Thread(target=warm_upstream, daemon=True).start()
        print('[proxy] no scheduler here; that host owns sync and builds')
    elif DEV:
        print('[dev] no scheduler, no auto-sync, no scheduled builds')
    elif not UPSTREAM:
        reconcile_queues()
        threading.Thread(target=scheduler_loop, daemon=True).start()
    tok = access_token()
    with Server(('0.0.0.0', PORT), Handler) as srv:
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
