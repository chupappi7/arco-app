#!/usr/bin/env python3
"""pay-for-twelve-3: "i pay for 12 apps / these 5 do all the work".

The hook promises apps that do the work themselves, so every slide teaches
a capability that hands a job off: Gemini Audio Overview turning a doc
into a two-host podcast, Zapier Copilot building a zap from a sentence, Descript cutting
retakes, the Notion agent building and filling a database. None of these
points appear in any caption in hooks.json. (The first draft's Gemini Canvas
report-to-web-page point was taken by business-at-19-3, built alongside.)

The hook is least recently used among hook_rules.eligible(pillar='tools').
ARCO_BODY is angle v5 (theme planning) drawn once with next_arco_angle and
written out literally so a rebuild renders the copy that shipped.

Backgrounds picked with the gen-daily-batch walk: hook from the unused
hook-only frames, app frames with no hook-only vibe, copy_band_luma under
BAND_MAX_LUMA, no monitor wall behind the copy (bg-h46/h48/h49/h50 and
bg-n05 put bright screens under the title), no adjacent vibe repeat, at most one person, none in the previous
post (run-it-all-at-19-3, built alongside). The hook frame is the unused desk-led-neon frame
with the plainest shelf zone (x100-980, y1105-1447): bg-h75 at 20.8 luma,
sd 22.6.

  01 hook         bg-h75  desk-led-neon
  02 ARCO         bg-h22  lounge-day
  03 Gemini       bg-h37  supercars-dusk
  04 Zapier       bg-n01  villa-day
  05 Descript     bg-h52  desk-city-day
  06 Notion       bg-h88  supercars-dusk

Usage:
    python3 tools/gen-pay-for-twelve-3.py            # every slide
    python3 tools/gen-pay-for-twelve-3.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'pay-for-twelve-3'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Gemini', 'Zapier', 'Descript', 'Notion']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Gemini', '3. Zapier',
          '4. Descript', '5. Notion']

BGS = ['bg-h75.jpg',   # 01 hook        desk-led-neon
       'bg-h22.jpg',   # 02 ARCO        lounge-day
       'bg-h37.jpg',   # 03 Gemini      supercars-dusk
       'bg-n01.jpg',   # 04 Zapier      villa-day
       'bg-h52.jpg',   # 05 Descript    desk-city-day
       'bg-h88.jpg']   # 06 Notion      supercars-dusk

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
DARK_FRAMES = {'bg-h37.jpg', 'bg-h88.jpg'}

ARCO_BODY = [
    'I keep every task in here and plan',
    'tomorrow in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away the moment it starts.',
    '',
    'The one I would not delete.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Gemini': [
    'Audio Overview turns an uploaded doc',
    'into a two host podcast about it.',
    '',
    'You get through 40 pages of notes',
    'on a walk, with the screen off.',
 ],
 'Zapier': [
    'Describe the automation in a line',
    'and Copilot builds every step.',
    '',
    'You check the apps it picked and',
    'switch it on, nothing wired by hand.',
 ],
 'Descript': [
    'Remove retakes finds every line you',
    'restarted and keeps a single take.',
    '',
    'A recording full of false starts',
    'comes back as one clean read.',
 ],
 'Notion': [
    'The Notion agent builds a database',
    'and fills it from your own pages.',
    '',
    'Ask for a content calendar and the',
    'table arrives with the posts in it.',
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
