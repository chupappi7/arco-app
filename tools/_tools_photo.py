"""Tools posts in the photo look: one visual language on every slide.

Thinh's request of 2026-10-07: a tools post is a five-app listicle and all
five slides read the same, app icon, number and name, two short lines, over a
photo. The screens batch before this gave ARCO a phone mockup and the other
four icons, and the post read as two posts. Here ARCO goes through app_slide
like everything else; the phone mockup stays with the screentime format.

Slides: 01 hook with the icon shelf and kicker, 02-06 the roster with ARCO at
#1. No closing card: tools posts stay a recommendation among peers.

Backgrounds are chosen in the generator and only read from tools/slides/bg;
nothing here writes into that folder (hook_usage.json included).
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from PIL import Image, ImageDraw
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

KICKER = 'here is why'
ARCO_TITLE = '1. App Blocker & Focus: ARCO'
BODY_SIZE = 50
BODY_MAX_W = 820
BODY_FLOOR = 1600      # last body baseline stays clear of TikTok's caption


def _wrap(text, width):
    f = c.font(BODY_SIZE, 'Semibold')
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines, cur = [], ''
    for w in text.split():
        trial = f'{cur} {w}'.strip()
        if cur and d.textbbox((0, 0), trial, font=f)[2] > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    lines.append(cur)
    return lines


def wrap(text, width=BODY_MAX_W):
    """Wrap to the measure, narrowing it until the last line is not a lone
    word: a widow reads as a mistake."""
    for w in range(width, 600, -10):
        lines = _wrap(text, w)
        if len(lines) == 1 or len(lines[-1].split()) > 1:
            if len(lines) > 3:
                break
            return lines
    raise SystemExit(f'cannot wrap in three lines without a widow: {text}')


def body_lines(paras):
    out = []
    for p in paras:
        if out:
            out.append('')
        out.extend(wrap(p))
    return out


def assert_fits(name, lines):
    f = c.font(BODY_SIZE, 'Semibold')
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    for ln in lines:
        if ln and d.textbbox((0, 0), ln, font=f)[2] > BODY_MAX_W:
            raise SystemExit(f'{name}: "{ln}" is over {BODY_MAX_W}px')
    y = 995 + 72 * sum(1 for l in lines if l) + 26 * lines.count('')
    if y > BODY_FLOOR:
        raise SystemExit(f'{name}: copy runs to y={y}')


def build(topic, hook, theme, bgs, arco, tools, only=None):
    """arco: ARCO's body lines, drawn once with next_arco_angle(theme) and
    frozen in the generator. tools: [(name, [mechanism, consequence])] after
    ARCO. bgs: hook then one per roster slide."""
    out = f'{c.REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    roster = ['ARCO'] + [t[0] for t in tools]
    if len(roster) != 5 or len(bgs) != 6:
        raise SystemExit('a tools post is five apps on six slides')
    if not any(h['lines'] == hook for h in hook_rules.eligible(topic, 'tools')):
        raise SystemExit(f'hook not eligible: {hook}')
    for name in roster:
        c.assert_audience([name])

    # Judge background freshness against the post just before this one, so a
    # rebuild after later posts still passes.
    full = c.bg_history
    def upto_here():
        h = full()
        idx = [i for i, e in enumerate(h) if e['topic'] == topic]
        return h[:idx[0]] if idx else h
    c.bg_history = upto_here
    try:
        preflight(topic, roster, bgs, pillar='tools', hook=hook)
    finally:
        c.bg_history = full
    for bg in bgs[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over {c.BAND_MAX_LUMA}')

    bodies = [arco] + [body_lines(p) for _, p in tools]
    for name, lines in zip(roster, bodies):
        assert_fits(name, lines)
    titles = [ARCO_TITLE] + [f'{i}. {n}' for i, n in enumerate(roster[1:], 2)]
    icons = json.load(open(c.TOOL_POOL))['icons']

    want = (lambda n: only is None or n in only)
    if want(1):
        hook_slide(bgs[0], hook, f'{out}/01.jpg', kicker=KICKER,
                   icons=[icons[t] for t in roster])
    if not any(e.get('topic') == topic for e in hook_rules.history()):
        mark_hook_used(hook, topic)
    for i, (name, title, lines) in enumerate(zip(roster, titles, bodies)):
        n = i + 2
        if want(n):
            app_slide(bgs[i + 1], icons[name], title, lines, f'{out}/{n:02d}.jpg')
            print(f'  {bgs[i+1]}  {c.VIBES.get(bgs[i+1]):18s} band luma '
                  f'{c.copy_band_luma(bgs[i+1]):.1f}')

    if not any(e.get('topic') == topic for e in c.tool_history()):
        record_post_tools(topic, roster)
    # record_post_bgs moves the entry to the end; a rebuild with a swapped
    # frame updates it where it stands so the post order is kept.
    h = c.bg_history()
    mine = [e for e in h if e['topic'] == topic]
    if not mine:
        record_post_bgs(topic, bgs)
    elif mine[0]['bgs'] != list(bgs):
        mine[0]['bgs'] = list(bgs)
        json.dump(h, open(c.BG_HISTORY, 'w'), indent=1)


def main(**kw):
    only = {int(a) for a in sys.argv[1:]} or None
    build(only=only, **kw)
