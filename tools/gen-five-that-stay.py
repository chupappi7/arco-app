#!/usr/bin/env python3
"""five-that-stay: a tools post Thinh composed in the dashboard.

Everything he decided is followed verbatim: the hook ("the 5 apps i would
keep / if i deleted everything else", eligible per hook_rules at build time),
his six backgrounds in his order, his titles and body copy word for word
(only wrapped to the slide's line width), and a cta_slide closing card.
Exactly six slides.

The dashboard slot metadata carried stale tool ids (Codex, Obsidian,
Superwall) that do not match the titles and copy he wrote (Manus, Endel,
Firebase). The slides follow his words: every claim is a real feature of the
product actually named, so the rendered roster is ARCO, Manus, Endel,
Firebase and that is what gets registered.

ARCO's body is angle v6 verbatim, so v6 is frozen here and counted in
arco_angles.json `used` instead of drawing next_arco_angle(), which would
have handed back a different angle than the copy he wrote.

Backgrounds are Thinh's picks, verified against the same gates
gen-daily-batch runs: no hook-only vibe past slide 1, every app band under
BAND_MAX_LUMA (h22 53.5, h37 22.7, h34 62.4, h35 37.2), no adjacent vibe
repeat (desk-empty-day / lounge-day / supercars-dusk / desk-empty-day /
supercars-dusk / desk-city-day), no person in any frame.

Usage:
    python3 tools/gen-five-that-stay.py            # every slide
    python3 tools/gen-five-that-stay.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, cta_slide, hook_slide, mark_hook_used,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'five-that-stay'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'

TOOLS = ['ARCO', 'Manus', 'Endel', 'Firebase']
# Thinh wrote the titles without numbers; keep them that way.
TITLES = ['ARCO', 'Manus', 'Endel', 'Firebase']

# index 0 is the hook, 1..4 the app slides, 5 the closing card.
BGS = ['bg-n05.jpg',   # 01 hook      desk-empty-day     Thinh's pick
       'bg-h22.jpg',   # 02 ARCO      lounge-day         band luma 53.5
       'bg-h37.jpg',   # 03 Manus     supercars-dusk     band luma 22.7
       'bg-h34.jpg',   # 04 Endel     desk-empty-day     band luma 62.4
       'bg-h35.jpg',   # 05 Firebase  supercars-dusk     band luma 37.2
       'bg-h50.jpg']   # 06 closing   desk-city-day      Thinh's pick

BODY = {
 # Thinh's copy == arco_angles v6 verbatim; frozen, and v6 is counted below.
 'ARCO': [
    'I manage all my tasks here and plan',
    'the day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away, Blocked Hours keeps them',
    'away on its own.',
 ],
 'Manus': [
    'Manus opens a real browser and does',
    'the clicking and typing itself.',
    '',
    'A fifty-page research job finishes',
    'without you opening a tab.',
 ],
 'Endel': [
    'Endel writes the sound from the',
    'weather and daylight where I am.',
    '',
    "I haven't picked focus music in",
    'over a year.',
 ],
 'Firebase': [
    'Remote Config changes a value in',
    'the live app from a dashboard.',
    '',
    'A feature turns on for every user',
    'with no update and no review wait.',
 ],
}

CTA_SUB = ['The planner and app blocker in one.',
           'The one I would not delete.']


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:5]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        # pick_hook_bg narrows to unused hook-only vibes and ignores `prefer`
        # while any exist, so claim Thinh's background by hand.
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'),
                      indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        app_slide(bg, icons[tool], TITLES[i], BODY[tool], f'{OUT}/{n+1:02d}.jpg')

    if only in (None, 6):
        cta_slide(BGS[5], f'{OUT}/06.jpg', subtitle=CTA_SUB)

    if only is None:
        d = json.load(open(c.ARCO_ANGLES))
        if 'v6' not in d['used']:
            d['used'].append('v6')
            json.dump(d, open(c.ARCO_ANGLES, 'w'), indent=1)
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
