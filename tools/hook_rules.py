"""Hook eligibility: which approved hooks may be used on the next post.

Hooks used to be burn-once — `used: true` and gone forever. That threw away
the best asset in a photo carousel: the hook is most of what decides whether
slide 2 is ever seen, so retiring a proven one after a single post is the
most expensive thing this pipeline can do. Reuse is normal on TikTok; what
matters is spacing.

So a hook now sits out a cooldown instead of dying:

  - a hook cannot return within HOOK_COOLDOWN posts
  - if its last post was marked performing (1000+ views) it only sits out
    HOOK_COOLDOWN_PERFORMING, because it earned the repeat
  - a hook marked `retired: true` never comes back, which is the manual
    escape hatch for one that flopped

Stdlib only, no PIL: compose.py enforces it at render time and dashboard.py
counts with it, and neither should own a private copy of the arithmetic.
"""

import difflib as _difflib
import json as _json
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
HOOK_POOL = _os.path.join(_HERE, 'hook_pool.json')
HOOK_HISTORY = _os.path.join(_HERE, 'hook_history.json')
POST_FEEDBACK = _os.path.join(_HERE, 'post_feedback.json')

HOOK_COOLDOWN = 4            # posts a hook sits out before it can return
HOOK_COOLDOWN_PERFORMING = 2  # ...if its last outing did 1000+ views

# A hook may be reworded rather than repeated word for word. Measured on
# this pool: two genuinely different hooks never score above 0.70, while a
# one-word edit scores 0.91 and up, so 0.82 separates them with room.
# The cooldown keys on the parent hook, not the exact wording: rewording is
# a variation on one idea, and the feed reads it that way too.
VARIANT_MIN = 0.82


def _load(path, default):
    try:
        with open(path) as fh:
            return _json.load(fh)
    except (IOError, ValueError):
        return default


def key(lines):
    """Compare hooks on text alone: case, spacing and curly quotes vary."""
    return tuple(l.strip().lower().replace('’', "'") for l in lines)


def pool():
    return _load(HOOK_POOL, {}).get('hooks', [])


def _flat(lines):
    return ' / '.join(l.strip().lower().replace(chr(8217), "'") for l in lines)


def parent(lines):
    """The approved hook this one is, or is a rewording of. None if neither."""
    k = key(lines)
    for h in pool():
        if key(h['lines']) == k:
            return h
    flat, best, score = _flat(lines), None, VARIANT_MIN
    for h in pool():
        r = _difflib.SequenceMatcher(None, flat, _flat(h['lines'])).ratio()
        if r >= score:
            best, score = h, r
    return best


def history():
    """Hooks in the order they went out, oldest first."""
    return _load(HOOK_HISTORY, [])


def record(lines, topic=None):
    h = history()
    src = parent(lines)
    entry = {'topic': topic, 'hook': list(src['lines']) if src else list(lines)}
    if src and key(src['lines']) != key(lines):
        entry['as'] = list(lines)     # the wording that actually went out
    h.append(entry)
    with open(HOOK_HISTORY, 'w') as fh:
        _json.dump(h, fh, indent=1, ensure_ascii=False)
    return h


def forget(topic):
    """Drop a topic's entries: a deleted post should not hold its hook down."""
    h = [e for e in history() if e.get('topic') != topic]
    with open(HOOK_HISTORY, 'w') as fh:
        _json.dump(h, fh, indent=1, ensure_ascii=False)
    return h


def performing(topic):
    if not topic:
        return False
    return bool(_load(POST_FEEDBACK, {}).get(topic, {}).get('liked'))


def status(lines, topic=None):
    """(ok, reason). reason is None when the hook may be used now."""
    src = parent(lines) or {}
    if src.get('retired'):
        return False, 'retired: it did not work and was pulled from rotation'
    if HOOK_COOLDOWN <= 0:
        return True, None
    hist = [e for e in history() if e.get('topic') != topic]
    # Rewording does not reset the clock: the parent hook is what is counted.
    k, last = key(src.get('lines', lines)), None
    for i, e in enumerate(hist):
        if key(e['hook']) == k:
            last = i
    if last is None:
        return True, None
    gap = len(hist) - 1 - last
    need = HOOK_COOLDOWN_PERFORMING if performing(hist[last].get('topic')) else HOOK_COOLDOWN
    if gap < need:
        where = hist[last].get('topic') or 'an earlier post'
        return False, (f'used in "{where}", {gap} post(s) ago; it sits out '
                       f'{need} before it can return')
    return True, None


def pillar_of(lines):
    """The pillar this hook belongs to, or None if it was never tagged."""
    src = parent(lines)
    return (src or {}).get('pillar')


def eligible(topic=None, pillar=None):
    """Approved hooks usable right now, least recently used first."""
    hist = [e for e in history() if e.get('topic') != topic]
    order = {}
    for i, e in enumerate(hist):
        order[key(e['hook'])] = i
    ok = [h for h in pool() if status(h['lines'], topic)[0]
          and (not pillar or h.get('pillar') == pillar)]
    return sorted(ok, key=lambda h: order.get(key(h['lines']), -1))


def blocked(topic=None):
    out = []
    for h in pool():
        good, why = status(h['lines'], topic)
        if not good:
            out.append((h['lines'], why))
    return out
