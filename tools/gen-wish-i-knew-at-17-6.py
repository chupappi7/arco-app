#!/usr/bin/env python3
"""wish-i-knew-at-17-6: "5 apps i wish someone / showed me at 17".

The hook speaks to someone at 17, so ARCO answers on the focus angle
(the phone locked through a study session) and every other slide teaches a
thing a teenager can use now: Antigravity asking before it runs a command,
Canva Magic Grab lifting a person onto a layer, CapCut templates keeping
the cuts of a trending edit, Figma selecting every matching layer for one edit.
None of these points appear in any caption in hooks.json.

The hook is among the least recently used in hook_rules.eligible(pillar='tools').
ARCO_BODY is angle f2 (theme focus) drawn once with next_arco_angle
and written out literally so a rebuild renders the copy that shipped.

Backgrounds picked with the gen-daily-batch walk: hook from the unused
hook-only frames, app frames with no hook-only vibe, copy_band_luma under
BAND_MAX_LUMA, no monitor wall behind the copy (bg-h46/h48/h49/h50 and
bg-n05 put bright screens under the title), no adjacent vibe repeat, at most one person, none in the
previous post (4x-productivity-10). The hook frame is the unused desk-led-neon frame
with the plainest remaining shelf zone (x100-980, y1105-1447): bg-h74 at 26.1 luma, sd 25.8 (h75 and h77 went to the two posts before).

  01 hook         bg-h74  desk-led-neon
  02 ARCO         bg-n06  desk-empty-day
  03 Antigravity  bg-h88  supercars-dusk
  04 Canva        bg-h31  lounge-night
  05 CapCut       bg-n04  villa-day
  06 Figma        bg-h32  window-silhouette, the one person

Usage:
    python3 tools/gen-wish-i-knew-at-17-6.py            # every slide
    python3 tools/gen-wish-i-knew-at-17-6.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'wish-i-knew-at-17-6'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i wish someone', 'showed me at 17']
PILLAR = 'tools'
THEME = 'focus'

TOOLS = ['ARCO', 'Antigravity', 'Canva', 'CapCut', 'Figma']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Antigravity', '3. Canva', '4. CapCut', '5. Figma']

BGS = ['bg-h74.jpg',   # 01 hook        desk-led-neon
       'bg-n06.jpg',   # 02 ARCO        desk-empty-day
       'bg-h88.jpg',   # 03 Antigravity supercars-dusk
       'bg-h31.jpg',   # 04 Canva       lounge-night
       'bg-n04.jpg',   # 05 CapCut      villa-day
       'bg-h32.jpg']   # 06 Figma       window-silhouette

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
DARK_FRAMES = {'bg-h31.jpg', 'bg-h32.jpg', 'bg-h88.jpg'}

ARCO_BODY = [
    'I start a session and every app on',
    'the list locks itself.',
    '',
    'Four hours later the phone has not',
    'been picked up once.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Antigravity': [
    'You choose whether it may run',
    'terminal commands without asking.',
    '',
    'Set it to ask and nothing installs',
    'or deletes until you say yes.',
 ],
 'Canva': [
    'Magic Grab lifts the person out of',
    'a photo onto a layer of their own.',
    '',
    'Move them, resize them or put the',
    'title behind them in the same shot.',
 ],
 'CapCut': [
    'A template keeps the cuts and the',
    'effects, and you drop in your clips.',
    '',
    'A trending edit is yours in a minute',
    'with none of the timing work.',
 ],
 'Figma': [
    'Select matching layers grabs every',
    'copy of the same style at once.',
    '',
    'One edit restyles forty buttons',
    'instead of forty clicks.',
 ],
}


def grad(bg):
    return GRAD if bg in DARK_FRAMES else GRAD_DARK


def band_luma(bg):
    """copy_band_luma, measured with the gradient this slide will use."""
    im = c.base_photo(bg, grad(bg))
    im = c.frame_for_band(im, 600, 1300)
    c.adaptive_scrim(im, 600, 1300)
    g = im.convert('L').crop((85, 980, 1000, 1310))
    px = list(g.getdata())
    return sum(px) / len(px)


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    # Other builds append to bg_history while this one runs, so "the last
    # post" drifts. Judge freshness against the post just before this one:
    # bg_history is cut at this topic for the length of preflight only, so
    # record_post_bgs below still sees the whole file.
    full = c.bg_history
    def upto_here():
        h = full()
        idx = [i for i, e in enumerate(h) if e['topic'] == TOPIC]
        return h[:idx[0] + 1] if idx else h
    c.bg_history = upto_here
    try:
        preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    finally:
        c.bg_history = full
    for bg in BGS[1:]:
        luma = band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        path = f'{c.SP}/hook_usage.json'
        log = json.load(open(path))
        if BGS[0] not in log:
            log.append(BGS[0])
            json.dump(log, open(path, 'w'), indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', icons=shelf)
        import hook_rules
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        app_slide(bg, icons[tool], TITLES[i], BODY[tool],
                  f'{OUT}/{n+1:02d}.jpg', grad=grad(bg))
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma {band_luma(bg):.1f}')

    if only is None:
        if not any(e.get('topic') == TOPIC for e in c.tool_history()):
            record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
