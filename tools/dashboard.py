#!/usr/bin/env python3
"""Local review dashboard for the TikTok pipeline.

  python3 tools/dashboard.py        # http://localhost:4500

Shows every built post, what has been delivered where, and how many pending
slots each account has left. Drafting runs the same autopost.js path the cron
job uses, so nothing here is a second implementation that can drift.

Stdlib only, no install. Binds to localhost.
"""
import gzip
import http.client
import http.server
import json
import secrets
import socket
import mimetypes
import os
import re
import socketserver
import subprocess
import threading
import time
import urllib.parse
import urllib.request

import hook_rules

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFTS = os.path.join(REPO, 'drafts')
HOOKS = os.path.join(REPO, 'tools', 'hooks.json')
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


def published_today():
    """Drafts marked published since local midnight, per account."""
    midnight = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
    out = {a['key']: 0 for a in ACCOUNTS}
    for _t, accts in delivery_log().items():
        for key, rec in accts.items():
            if rec.get('published') and (rec.get('published_at') or 0) >= midnight:
                out[key] = out.get(key, 0) + 1
    return out


def account_summary():
    """Followers now and the change since the oldest sample we hold.

    The sidebar used to say nothing but "published today", which is the least
    interesting fact about an account.
    """
    stats = load(ACCT_STATS, {})
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
        }
    return out


def active_runs():
    """Every background job still going, so the header can show all of them."""
    runs = []
    for label, items in (('build', build_queue()), ('redo', redo_queue()),
                         ('replicate', replicate_queue())):
        for x in items:
            if x.get('status') in ('queued', 'running'):
                if label == 'build':
                    what = '%d post%s' % (x['count'], '' if x['count'] == 1 else 's')
                elif label == 'redo':
                    ns = x.get('slides') or [x.get('slide')]
                    what = '%s slide%s %s' % (x['topic'], '' if len(ns) == 1 else 's',
                                              ', '.join(str(n) for n in ns))
                else:
                    what = 'replicating %s' % x['from']
                runs.append({'kind': label, 'what': what,
                             'topic': x.get('topic') or x.get('from'),
                             'mode': x.get('mode'),
                             'status': x.get('status', 'queued'),
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
SYNC_EVERY = 1800             # seconds between automatic syncs
RAW_KEEP = 72 * 3600          # how long raw snapshots live, for trajectories


def _norm(t):
    """Captions round-trip through TikTok with whitespace changes."""
    return ' '.join((t or '').lower().split())


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

    idx, _ = hooks_index()
    # A caption can belong to more than one topic: a reshoot keeps the copy
    # byte-identical on purpose, so `ship-alone` and `ship-alone-2` look the
    # same here. One entry per caption meant the second silently overwrote the
    # first and a dozen uploads vanished from the numbers.
    by_caption = {}
    for topic, post in idx.items():
        cap = _norm(post.get('caption'))
        if cap:
            by_caption.setdefault(cap, []).append(topic)
    log_now = delivery_log()

    def pick_topic(cap, key, posted_at, taken):
        """Of the topics sharing this caption, the one this upload came from.

        Decided by delivery time: whichever topic was sent to this account
        closest before the post appeared. Falls back to any unclaimed topic.
        """
        cands = [t for t in by_caption.get(cap, []) if (t, key) not in taken]
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
        for t, per_ in stats.items():
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

        for v in data['videos']:
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
            stats.setdefault(topic, {})[key] = dict(
                point,
                id=str(v.get('id') or '') or None,
                url=v.get('share_url'),
                cover=v.get('cover_image_url'),
                posted_at=v.get('create_time'), synced=time.time(),
            )
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
            'cells': cells,
            'likes': {k: (per.get(k) or {}).get('likes') for k in keys},
            'comments': {k: (per.get(k) or {}).get('comments') for k in keys},
            'shares': {k: (per.get(k) or {}).get('shares') for k in keys},
            'at': {k: (per.get(k) or {}).get('posted_at') for k in keys},
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

    def at_of(r):
        ats = [t for t in r['at'].values() if t]
        return min(ats) if ats else (r.get('posted_at') or 0)

    out = []
    for r in rows:
        ats = {k: t for k, t in r['at'].items() if t and lo <= t < hi}
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
            'at': ats, 'first_at': min(ats.values()),
            'views': tot['cells'], 'likes': tot['likes'],
            'comments': tot['comments'], 'shares': tot['shares'],
            'best': max(vs) if vs else 0,
            'rate': round(100 * tot['likes'] / max(1, tot['cells']), 1),
        })
    out.sort(key=lambda x: -x['first_at'])

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
        results[key] = {'status': status, 'detail': detail, 'at': time.time()}
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
Slides to fix: {slides}
What Thinh says is wrong:
{note}

1. Find tools/gen-*.py referencing '{topic}'. That file is the spec.
2. Fix EVERY slide listed above in this one run. Change nothing else: the
   slides not listed must come out byte-identical.
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
    if not (rec.get('caption') or '').strip():
        return 'registered with an empty caption'
    return ''


def _agent(prompt, mark, ok_token, topic=None):
    """Run a headless Claude in the repo and record the outcome."""
    mark(status='queued')
    with _agent_gate:
        mark(status='running', started=time.time())
        try:
            p = subprocess.run(['claude', '-p', prompt], cwd=REPO,
                               capture_output=True, text=True, timeout=3600)
            out = ((p.stdout or '') + (p.stderr or '')).strip()
            good = ok_token in out
            # A build that rendered slides and skipped the caption is not done.
            # It used to report success and sit in Review looking finished.
            if good and ok_token == 'BUILT':
                built = re.search(r'BUILT\s+([a-z0-9][a-z0-9-]*)', out)
                name = built.group(1) if built else topic
                why = (unregistered(name) if name else '') or unpushed()
                if why:
                    return mark(status='failed', done=False,
                                log='Slides built, but %s: %s.\n\n%s'
                                    % (name or 'the run', why, out[-900:]),
                                finished=time.time())
        except Exception as exc:
            return mark(status='failed', log=str(exc))
        mark(status='done' if good else 'failed', done=good,
             log=out[-1200:] or 'no output', finished=time.time())


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
        slides=', '.join('%02d.jpg (number %d)' % (n, n) for n in slides)),
        mark, 'FIXED')


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
    _agent(prompt, mark, 'BUILT', topic=job.get('topic'))


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

    mark(status='queued')
    with _agent_gate:                  # same shared-state reason as _agent
        mark(status='running', started=time.time())
        try:
            p = subprocess.run(['claude', '-p', prompt], cwd=REPO,
                               capture_output=True, text=True, timeout=3600)
            out = ((p.stdout or '') + (p.stderr or '')).strip()
            ok = 'BUILT' in out
            # A batch can build several; any one of them missing its caption
            # means the run is not finished, whatever it printed.
            broken = [t for t in set(re.findall(r'BUILT\s+([a-z0-9][a-z0-9-]*)', out))
                      if unregistered(t)]
            push = unpushed() if ok else ''
            if ok and (broken or push):
                ok = False
                why = []
                if broken:
                    why.append('No caption on: ' + ', '.join(sorted(broken))
                               + '. They cannot be delivered until hooks.json has one.')
                if push:
                    why.append(push.capitalize() + '.')
                out = ' '.join(why) + '\n\n' + out[-900:]
            mark(status='done' if ok else 'failed', done=ok,
                 log=out[-1200:] or 'no output', finished=time.time())
        except subprocess.TimeoutExpired:
            mark(status='failed', log='timed out after an hour')
        except FileNotFoundError:
            mark(status='failed', log='claude CLI not found on PATH')
        except Exception as exc:
            mark(status='failed', log=str(exc))


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
            (BUILD, build_queue, run_build, save_builds)):
        q = load()
        pending = []
        for x in q:
            if x.get('status') == 'running':
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
                d['stale'] = True
                d['stale_at'] = os.path.getmtime(snap)
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
        if path == '/api/host':
            # Two dashboards look identical on purpose — same data, same page.
            # This is the one thing that differs, so the UI can say which one
            # you are typing into before you draft from it.
            return self._send(200, {
                'name': socket.gethostname().split('.')[0].replace('s-Mac-mini', ' mini'),
                'kind': 'local' if UPSTREAM else 'host',
                'upstream': UPSTREAM or None,
                'dev': DEV,
            })
        # Answered here, never forwarded: the question is which server you are
        # talking to, and the proxy would hand back the other one's answer.
        if UPSTREAM and path.startswith('/api/'):
            return self._proxy()
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
        if path == '/icon/arco.png':
            f = os.path.join(REPO, 'tools', 'slides', 'icons', 'icon-arco.png')
            with open(f, 'rb') as fh:
                return self._send(200, fh.read(), 'image/png')
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
.brand .v{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
/* A property of the subtitle, not a third thing in the stack: a dot in the
   host's colour and the name beside it, on the same line. */
.hostb{display:inline-flex;align-items:center;gap:5px;
  font:500 11px/1 "Fira Code",monospace;color:var(--accent)}
.hostb::before{content:"";width:6px;height:6px;border-radius:50%;
  background:currentColor;box-shadow:0 0 7px currentColor}
/* The laptop is the one that can be closed mid-task, so it gets the warmer
   colour. */
.hostb.local{color:var(--warn)}
/* Upstream gone: the dot stops glowing and goes red, so a stale page is
   visibly stale rather than quietly wrong. */
#stalebar{padding:11px 16px;background:rgba(251,146,60,.12);
  border-bottom:1px solid rgba(251,146,60,.4);color:var(--muted);
  font:400 12.5px/1.5 system-ui}
#stalebar b{color:var(--warn);font-weight:600}
.hostb.down{color:var(--bad)}
.hostb.down::before{box-shadow:none;animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
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
.acct{display:block;text-decoration:none;background:var(--surface-2);
  border:1px solid var(--line-2);border-radius:var(--r);padding:11px 12px;
  transition:border-color .15s}
.acct:hover{border-color:var(--accent)}
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
/* Set by the sync from real view counts, never by hand. */
.tier{position:absolute;top:8px;left:8px;z-index:2;padding:4px 8px;border-radius:7px;
  font:600 10.5px/1 "Fira Code",monospace;letter-spacing:.02em;
  background:rgba(56,189,248,.16);border:1px solid var(--accent);color:var(--accent);
  backdrop-filter:blur(6px)}
/* In the footer, not beside the title: the numbers are the outcome of the
   post, not part of naming it. Values bold and light, units dim, so the row
   reads as three numbers rather than six words. */
.cstat{display:flex;align-items:baseline;gap:5px;margin-right:auto;
  font:500 11px/1 "Fira Code",monospace;color:var(--dim)}
.cstat b{font-weight:600;font-size:12.5px;color:var(--text)}
.cstat b + span{margin-right:6px}
.cstat b.r{color:var(--ok)}
.livestat{display:inline-flex;align-items:center;gap:11px;
  font:500 13px/1 "Fira Code",monospace;color:var(--text)}
.livestat .r{color:var(--dim)}
.tier.inline{position:static;backdrop-filter:none}
.chips{display:flex;gap:5px}
.chip{font:500 10.5px/1 "Fira Code",monospace;padding:5px 8px;border-radius:6px;
  border:1px solid var(--line-2);background:var(--surface-2);color:var(--dim);
  letter-spacing:.01em;transition:all .14s;white-space:nowrap}
.chip.drf{color:var(--accent);border-color:#14405a;background:rgba(56,189,248,.09);cursor:pointer}
.chip.drf:hover{background:rgba(56,189,248,.22)}
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
.mx.cmp th{font-size:10px;letter-spacing:.1em;padding-bottom:10px}
.mx.cmp .hr{font:700 17px/1 "Fira Code",monospace;color:var(--text)}
.mx.cmp tr.lead .hr{color:var(--accent)}
.best{margin-left:9px;padding:3px 7px;border-radius:5px;vertical-align:2px;
  font:600 9px/1 system-ui;letter-spacing:.07em;text-transform:uppercase;
  background:rgba(56,189,248,.15);border:1px solid var(--accent);color:var(--accent)}
.worst{margin-left:9px;font:500 10.5px/1 system-ui;color:var(--dim)}
.mx.cmp .t i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:9px}
.mx.cmp b{font:600 14px/1 "Fira Code",monospace;color:var(--text)}
.mx.cmp tr.lead td{background:rgba(56,189,248,.05)}
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
.cust{display:inline-flex;gap:6px;margin-left:6px}
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
.paid{color:var(--warn);font-style:normal}
/* Per account, side by side. Summing them would hide the 30x spread, which
   is the only thing three accounts running one post can teach you. */
.pcells{display:flex;gap:6px;flex:none}
.pc{display:inline-flex;align-items:center;gap:5px;flex:0 0 78px;justify-content:flex-end;
  padding:6px 9px;border-radius:8px;background:var(--surface-2);border:1px solid var(--line);
  font:500 12px/1 "Fira Code",monospace;color:var(--muted);text-decoration:none}
.pc i{width:6px;height:6px;border-radius:50%;flex:none}
.pc.hot{color:var(--text);border-color:var(--accent);background:rgba(56,189,248,.12)}
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
.seg.on{background:rgba(56,189,248,.14);color:var(--accent)}
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
#peek{position:fixed;inset:0;z-index:80;background:rgba(2,6,23,.86);
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
/* Capped and centred. Five points stretched across the full width of a
   desktop is a flat line whatever the numbers do. */
.chartwrap{position:relative;max-width:720px;margin:6px auto 0}
.chartwrap svg{width:100%;height:auto;display:block}
.hitc{cursor:crosshair}
.ctip{position:absolute;pointer-events:none;z-index:5;transform:translate(-50%,-100%);
  background:var(--surface-2);border:1px solid var(--line-2);border-radius:9px;
  padding:8px 11px;box-shadow:0 12px 28px rgba(0,0,0,.55);white-space:nowrap}
.ctip[hidden]{display:none}
.ctip b{display:block;font:600 11px/1.4 "Fira Code",monospace;color:var(--text)}
.ctip span{font:500 11px/1.5 "Fira Code",monospace;color:var(--muted)}
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
  #pagemenu{position:fixed;inset:0;z-index:70;background:rgba(2,6,23,.6)}
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
  border:1px solid var(--accent);background:rgba(56,189,248,.13);color:var(--accent);cursor:pointer}
.cta.sec{border-color:var(--line-2);background:var(--surface-2);color:var(--muted)}
.cta:hover{background:rgba(56,189,248,.26)}
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
.strip .sl.picked img{border-color:var(--accent);box-shadow:0 0 0 3px rgba(56,189,248,.28)}
.redobar{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin:0 0 14px;padding:12px 14px;
  border:1px solid var(--accent);border-radius:11px;background:rgba(56,189,248,.06)}
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
  background:var(--bad);box-shadow:0 0 0 2px rgba(2,6,23,.75),0 0 10px rgba(244,63,94,.7);
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
  .fav,.del{opacity:.9;width:32px;height:32px}
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
  .actbar .chips{order:4;width:100%;margin:1px 0 0}
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
  .fav,.del{width:36px;height:36px;opacity:.85}
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
</style></head><body>
<div class="app">
<aside>
  <div class="brand">
    <img src="/icon/arco.png" alt="ARCO app icon">
    <div><div class="n">ARCO</div>
      <div class="v">content pipeline<span id="host"></span></div></div>
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
  <div id="runs" style="margin-left:auto"></div></div>
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
  all:'<path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>'
};
const ic = k => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[k]}</svg>`;
const tk = c => `<svg viewBox="0 0 24 24" fill="${c||'currentColor'}" aria-hidden="true"><path d="${TIKTOK}"/></svg>`;
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

let DATA=null, cur=null, filter='review', sel=0, redoMode=false, zi=-1;
let redoSel=new Set(), openMenu=null;
const PILLARS=[['tools','Tools'],['screentime','Screen time'],['discipline','Discipline'],
               ['build','Building'],['learn','Studying']];
const FILTERS=[['review','Review'],['out','Published'],
               ['liked','Performing'],['stats','Analytics'],
               ['all','All posts'],['archive','Archive']];
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
  const runs = DATA.runs||[];
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
    : '';

  const box = document.getElementById('jobs');
  if ((!runs.length && !justDone.length) || (!jobsOpen && runs.length)) {
    box.innerHTML = '';
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
  STALE = !!(fresh && fresh.stale);
  if (fresh && fresh.stale) {
    DATA = fresh;
    paintStale();
    const hb1 = document.getElementById('host');
    if (hb1) { hb1.classList.add('down'); hb1.title = 'Upstream is not answering — showing the last copy'; }
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
  const hb0 = document.getElementById('host');
  if (hb0) hb0.classList.remove('down');
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
  const counts = Object.fromEntries(FILTERS.map(([k]) => [k,
    k==='stats' ? '' :
    DATA.posts.filter(p => k==='all'?true:k==='liked'?p.liked
                         :k==='out'?isOut(p):stateOf(p)===k).length]));
  ICONS.archive = ICONS.archive || '<path d="M21 8v13H3V8M1 3h22v5H1zM10 12h4"/>';
  ICONS.review = ICONS.review || '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>';
  ICONS.out = ICONS.out || ICONS.drafted;
  ICONS.stats = ICONS.stats || '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>';
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
      return `<a class="acct" href="#" onclick="filter='stats';anTab='accounts';
                anAccs=new Set(['${a.key}']);AN=null;saveHash();loadAnalytics();return false"
                title="See only ${esc(a.label)} in Analytics">
        <div class="top">${tk('#F8FAFC')}<span class="h">@${esc(a.label)}</span></div>
        <div class="astat">
          <b>${st.followers ?? '–'}</b><span>followers</span>
          ${d ? `<i class="${d>0?'up':'down'}">${d>0?'+':''}${d}</i>` : ''}
        </div>
      </a>`;}).join('');
  if(!quiet) render();

}

// Cmd-R should reload the page you are looking at, not send you back to
// Review. The hash carries the whole view: tab, post, analytics sub-tab and
// period. `?` separates the post from the rest so old <topic>/<slide> links
// still work.
function saveHash(){
  const q = ['v=' + filter];
  if(filter === 'stats'){
    q.push('t=' + anTab, 'p=' + anPeriod, 'r=' + anRange);
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
    if(key === 'a') anAccs = new Set(val.split(',').filter(Boolean));
  });
  if(!postPart) return;
  const [t, n] = postPart.split('/');
  if(t && DATA.posts.some(p => p.topic === t)){
    cur = t;
    if(n) setTimeout(()=>zoomAt(parseInt(n,10)-1), 0);
  }
}

function setFilter(k){ filter=k; cur=null; closePages(); saveHash(); load(); }

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

// On a phone the nav is a strip that scrolls the later pages off screen, so
// there it becomes a menu instead: current page on the button, full list on tap.
function togglePages(){
  const m = document.getElementById('pagemenu');
  if(!m.hidden) return closePages();
  const counts = Object.fromEntries(FILTERS.map(([k]) => [k,
    k==='stats' ? '' :
    DATA.posts.filter(p => k==='all'?true:k==='liked'?p.liked
                         :k==='out'?isOut(p):stateOf(p)===k).length]));
  m.innerHTML = `<div class="sheet">${FILTERS.map(([k,lab])=>
    `<button class="pg ${filter===k?'on':''}" onclick="setFilter('${k}')">
       ${ic(ICONS[k]?k:'all')}<span>${lab}</span>
       <b>${counts[k]}</b></button>`).join('')}</div>`;
  m.hidden = false;
  setTimeout(()=>document.addEventListener('click', closeOnce), 0);
}
function closeOnce(e){
  if(e.target.closest('#pagemenu') || e.target.closest('#menubtn')) return;
  closePages();
}
function closePages(){
  const m = document.getElementById('pagemenu');
  if(m){ m.hidden = true; m.innerHTML = ''; }
  document.removeEventListener('click', closeOnce);
}

function render(){ try{ render_(); }catch(err){
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

// The one timestamp that matters for a post: when it was published, else
// when it was drafted, else when it was built. Every tab groups on it.
function whenOf(p){
  const ds = DATA.accounts.map(a=>(p.delivery||{})[a.key]).filter(Boolean);
  const pubs = ds.map(r=>r.published_at).filter(Boolean);
  if(pubs.length) return Math.max(...pubs);
  const sent = ds.map(r=>r.at).filter(Boolean);
  if(sent.length) return Math.max(...sent);
  return p.mtime;
}
const two = n => String(n).padStart(2,'0');
function dstamp(ts){ const d=new Date(ts*1000);
  return `${d.getDate()}.${d.getMonth()+1}.${d.getFullYear()}`; }
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
let anError = null, STALE = false;

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
  const at = (DATA && DATA.stale_at) ? ago(DATA.stale_at) : 'earlier';
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
const ACOL = {vn:'#38BDF8', getarco:'#A78BFA', us:'#22C55E'};

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
  if(anRange === 'custom')    return [anFrom, anTo];
  return [0, null];                       // all time
}
function setRange(r){
  // Custom used to open on two empty inputs, which resolved to no range at
  // all and showed nothing. It starts on today and is narrowed from there.
  if(r === 'custom' && anFrom == null){ anFrom = midnight(); anTo = null; }
  anRange = r; AN = null; pubAll = false; saveHash(); loadAnalytics();
}
function setCustom(which, v){
  const t = v ? new Date(v + 'T00:00:00').getTime() / 1000 : null;
  if(which === 'from') anFrom = t;
  else anTo = t === null ? null : t + 86400;   // inclusive of the chosen day
  if(anFrom == null) anFrom = 0;
  if(anTo != null && anFrom > anTo) anFrom = anTo - 86400;
  anRange = 'custom'; AN = null; pubAll = false; saveHash(); loadAnalytics();
}
async function loadAnalytics(){
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
  const dead = got && (got.upstream_down || got.error) && !got.stale;
  AN = dead ? null : got;
  anError = dead ? got : null;
  if (got && got.stale) { STALE = true; paintStale(); }
  render();
}

// Click an account to see only that one; click it again to go back to all
// three. Comparing one against the others is the common question, and a
// multi-select made you click twice to ask it.
function toggleAcct(k){
  const solo = anAccs && anAccs.size === 1 && anAccs.has(k);
  anAccs = solo ? null : new Set([k]);
  AN = null; saveHash(); loadAnalytics();
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
          ? '<span class="best">publish here first</span>'
          : a.key === rank[rank.length - 1].key
            ? `<span class="worst">${Math.round(
                (pa[rank[0].key].wins / Math.max(1, pa[rank[0].key].posts)) /
                Math.max(0.01, pa[a.key].wins / Math.max(1, pa[a.key].posts)))}x behind</span>`
            : '';
        return `<tr class="${a.key===rank[0].key?'lead':''}">
          <td class="t"><i style="background:${ACOL[a.key]}"></i>${esc(a.label)}${tag}</td>
          <td class="n"><span class="sp">${v.posts}</span></td>
          <td class="n"><span class="hr">${hr}%</span></td>
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
        return `<td class="n"><a class="cell ${cls}" style="background:rgba(56,189,248,${alpha})"
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
    const lines = gains.map(sv=>{
      const d = sv.pts.map((p,i)=>`${i?'L':'M'}${px(i).toFixed(1)},${py(p.g).toFixed(1)}`).join('');
      // The number sits on the point. Three accounts on one axis means the
      // shape alone cannot tell you whether a rise is +2 or +23.
      const dots = sv.pts.map((p,i)=>`<circle cx="${px(i).toFixed(1)}" cy="${py(p.g).toFixed(1)}"
        r="4.5" fill="${ACOL[sv.a.key]}" stroke="var(--bg)" stroke-width="2"/>
        <text x="${px(i).toFixed(1)}" y="${(py(p.g)-12).toFixed(1)}" text-anchor="middle"
          font-size="13" font-weight="700" fill="${ACOL[sv.a.key]}">${p.g>0?'+':''}${p.g}</text>`).join('');
      return `<path d="${d}" fill="none" stroke="${ACOL[sv.a.key]}" stroke-width="2.5"
        stroke-linejoin="round" stroke-linecap="round"/>${dots}`;
    }).join('');
    const labels = dayList.map(([d],i)=>`<text x="${px(i).toFixed(1)}" y="${H-12}"
      fill="var(--dim)" font-size="10" text-anchor="middle">${dmy(d)}</text>`).join('');
    // One hit area per day rather than per point: at this density the points
    // of three accounts overlap, and aiming at a 3.5px dot is not a thing
    // anyone should have to do.
    const cols = dayList.map(([d, v], i) => {
      const w = (W - L - R) / Math.max(1, dayList.length);
      const rows = accs.map(a => `${esc(a.short)} ${(v[a.key]||0) > 0 ? '+' : ''}${v[a.key]||0}`);
      return `<rect class="hitc" x="${(px(i) - w/2).toFixed(1)}" y="${TOP}"
        width="${w.toFixed(1)}" height="${H-TOP-BOT}" fill="transparent"
        data-x="${px(i).toFixed(1)}" data-day="${dmy(d)}"
        data-rows="${esc(rows.join(' · '))}"/>`;
    }).join('');
    trend = `<div class="chartwrap"><svg viewBox="0 0 ${W} ${H}" id="trendsvg">
      <line class="guide" x1="0" y1="${TOP}" x2="0" y2="${H-BOT}"
        stroke="var(--line-2)" stroke-width="1" opacity="0"/>
      <line x1="${L}" y1="${zeroY.toFixed(1)}" x2="${W-R}" y2="${zeroY.toFixed(1)}"
        stroke="var(--line-2)" stroke-dasharray="3 4"/>
      <text x="${L-10}" y="${(zeroY+4).toFixed(1)}" fill="var(--dim)" font-size="12" text-anchor="end">0</text>
      <text x="${L-10}" y="${(py(hi)+4).toFixed(1)}" fill="var(--dim)" font-size="12" text-anchor="end">+${hi}</text>
      ${lines}${labels}${cols}</svg><div class="ctip" hidden></div></div>`;
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
      <span class="il">${esc(r.untracked?r.title.slice(0,34)+'…':r.topic)}</span>
      <span class="ir ${r.best>=T?'hit':''}">${fmt(r.best)}</span>
      <span class="is">${aged(r.posted_at)}</span></li>`).join('')}</ul></div>`;

  // Four screens rather than one long scroll. Each fits without scrolling,
  // which is the point: analytics you have to scroll through does not get read.
  const TABS = [['published','Posts'],['accounts','Accounts'],
                ['posts','Compare'],['todo','Act']];
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
                  ['30','30 days'],['all','All'],['custom','Custom']];
  const iso = ts => ts ? new Date(ts*1000).toISOString().slice(0,10) : '';
  const rangeChips = () => `<div class="periods">
      ${RANGES.map(([v,l])=>`<button class="pillp ${anRange===v?'on':''}"
        onclick="setRange('${v}')">${l}</button>`).join('')}
      ${anRange==='custom'?`<span class="cust">
        <input type="date" value="${iso(anFrom)}" onchange="setCustom('from',this.value)">
        <input type="date" value="${iso(anTo?anTo-86400:null)}" onchange="setCustom('to',this.value)">
      </span>`:''}
      <span class="acctfilter">${every.map(a=>
        `<button class="pilla ${on(a.key)?'on':'off'}" onclick="toggleAcct('${a.key}')">
           <i style="${on(a.key)?`background:${ACOL[a.key]};border-color:${ACOL[a.key]}`
                               :'background:transparent;border-color:var(--line-2)'}"></i>${esc(a.short)}</button>`).join('')}</span>
    </div>`;

  function publishedView(){
    const P = AN.published;
    if(!P) return '<div class="empty">Pick a date range.</div>';
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
      : b.first_at-a.first_at);
    const shown = pubAll ? rowsAll : rowsAll.slice(0,20);

    const cell = (r,a) => {
      const v = r.cells[a.key];
      if(v==null) return `<span class="pc none" title="not published to ${esc(a.label)}">–</span>`;
      const u = r.urls[a.key];
      const hot = v >= T;
      return `<a class="pc ${hot?'hot':''}" ${u?`href="${u}" target="_blank" rel="noopener"`:''}
        title="${esc(a.label)} · ${fmt(v)} views" onclick="event.stopPropagation()">
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
          <b>${esc(r.untracked ? (r.title||r.topic).slice(0,40) : r.topic)}</b>
          <span>${hm(r.first_at)}${r.pillar?' · '+esc(r.pillar):''}${r.promoted?' · <i class="paid">$</i>':''}</span>
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
    body = rangeChips() + compare + trendCard;
  } else if(anTab==='posts'){
    body = sect('Every post, every account',
           'Shade is log-scaled views. Click a number to open it on TikTok. '
           + '$ marks a promoted post so paid reach stays out of the medians. '
           + 'Last posted turns green once a post is old enough to run again.')
         + matrix;
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
function tierOf(views){
  if(views >= 100000) return '100k+';
  if(views >= 10000) return Math.floor(views/10000)*10 + 'k+';
  if(views >= 1000) return Math.floor(views/1000) + 'k+';
  return null;
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
    act = `<button class="cta" onclick="cardDraft(event,'${p.topic}')">Draft to all</button>`;
  // No Mark published button: the sync reads the account back and sets it.
  else if(st==='published' && p.days_since>=7)
    act = `<button class="cta sec" onclick="cardRepost(event,'${p.topic}')">Repost</button>`;

  const busy = p.queued || (p.redos||[]).length;
  return `<div class="cardwrap" data-topic="${p.topic}">
    ${p.seen?'':`<span class="new" title="${p.from_replicate?'From '+esc(p.from_replicate):'Not opened yet'}"></span>`}
    ${(() => { const t = tierOf(bestViews(p));
      return t ? `<span class="tier" title="Best account: ${fmtn(bestViews(p))} views">${t}</span>` : ''; })()}
    <button class="del" onclick="del(event,'${p.topic}')"
      aria-label="Delete ${esc(p.topic)}">${TRASH}</button>
    <button class="card" onclick="open_('${p.topic}')">
      <div class="thumb"><img loading="lazy" src="/slide/${p.topic}/${p.slides[0]}"
        alt="First slide of ${esc(p.topic)}"></div>
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
function back(){ cur=null; sel=0; redoMode=false; saveHash(); render(); }

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
      ? `<span class="livestat">${tier ? `<b class="tier inline">${tier}</b>` : ''}
           <span>${fmtn(t.v)} views</span><span>${fmtn(t.l)} likes</span>
           <span class="r">${(100*t.l/t.v).toFixed(1)}% liked</span></span>`
      : `<span class="sub">Live. The sync reads the numbers back every 30 minutes.</span>`;
  }

  const chips = DATA.accounts.map(a=>{
    const r=(p.delivery||{})[a.key];
    const k = !r ? 'none' : r.published ? 'pub' : r.status==='SENT' ? 'drf'
            : r.status==='FAILED' ? 'err' : 'none';
    return `<button class="chip ${k}" title="${esc(a.label)}"
      onclick="chip(event,'${p.topic}','${a.key}')">${esc(a.short||a.key)}</button>`;
  }).join('');

  document.getElementById('view').innerHTML = `
    <div class="actbar">
      <button class="back" onclick="back()">&larr;</button>
      <span class="who2">${esc(p.topic)}</span>
      <div class="chips">${chips}</div>
      ${primary}
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
        <button onclick="askSchedule()"><b>Schedule drafting</b><span>Send later.</span></button>
        <button onclick="del(event,'${p.topic}')"><b>Delete post</b><span>Moves to _deleted.</span></button>
      </div>`:''}
    </div>

    ${redoMode?`<div class="redobar">
      <span class="sub">Pick every slide that is wrong — click them, or press 1 to 6.</span>
      <input id="rnote" placeholder="What is wrong? Mention slide numbers if they differ.">
      <button class="btn" id="rgo" onclick="redo()" ${redoSel.size?'':'disabled'}>
        Redo ${redoSel.size||''} slide${redoSel.size===1?'':'s'}</button>
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




async function publishAll(){
  await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic:cur, published:true})});
  await load(); render();
}

// Direct Post settings, per account. TikTok's content-sharing guidelines make
// most of this mandatory: the privacy list must come from the creator, no
// default may be preselected, a control the creator disabled must be shown
// disabled, and the commercial disclosure must gate the publish button.














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
  showModal({
    title:'Repost '+topic, ok:'Re-draft now',
    body:'The same slides go out again as fresh inbox drafts. Nothing is rebuilt.',
    extra:'<div class="sched">'+DATA.accounts.map(a=>
      `<label style="display:flex;gap:9px;align-items:center;margin:7px 0">
         <input type="checkbox" class="rp" value="${a.key}" ${pick.includes(a.key)?'checked':''}>
         <span>${esc(a.label)}</span></label>`).join('')+'</div>',
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
  if(!slides.length) return;
  const topic = cur;
  redoMode=false; redoSel=new Set();
  await fetch('/api/redo',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic, slides, note})});
  // Stay on the post. This used to jump back to the list so the run was
  // visible, but the job panel is on every page now, so the jump only ever
  // read as the page refreshing itself for no reason.
  await load(); render();
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
  tip.innerHTML = `<b>${col.dataset.day}</b><span>${col.dataset.rows}</span>`;
  tip.hidden = false;
  tip.style.left = (x / vb.width * box.width) + 'px';
  tip.style.top  = (28 / vb.height * box.height) + 'px';
});

// Which machine is serving this page. Both dashboards are deliberately
// identical, so without this there is no way to tell whether an action is
// about to run on the laptop or on the mini.
fetch('/api/host').then(r=>r.json()).then(h=>{
  const el = document.getElementById('host');
  if(!el) return;
  const local = h.kind === 'local';
  el.className = local ? 'hostb local' : 'hostb';
  el.textContent = local ? 'macbook' : 'mini';
  el.insertAdjacentHTML('beforebegin', '<span style="color:var(--line-2)">·</span>');
  el.title = local
    ? 'Served by this MacBook. Data and every action go to ' + h.upstream
    : 'Served by the mini, which owns the data and runs the schedule';
}).catch(()=>{});

load().then(()=>{
  restoreHash();
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
    import sys
    if '--clean-history' in sys.argv:
        clean_history()
        raise SystemExit(0)
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
