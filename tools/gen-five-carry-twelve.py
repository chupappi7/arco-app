#!/usr/bin/env python3
"""five-carry-twelve: a tools post Thinh composed in the dashboard.

Everything he decided is followed verbatim: the hook ("i pay for 12 apps /
these 5 do all the work", eligible per hook_rules at build time), the six
backgrounds in his order, the roster (ARCO, Manus, Endel, Firebase), the
unnumbered titles he wrote, and a cta_slide closing card. Exactly six slides.

The copy was left open, so each slide answers what the hook promised — apps
that do the work on their own — with a teaching point checked against every
caption in hooks.json before it was written:
  ARCO      next_arco_angle('planning') -> v3, frozen here so a rebuild
            cannot hand this post copy the caption does not describe.
  Manus     scheduled tasks. Both prior Manus points (the cloud machine that
            outlives the tab, the mid-run checklist) are burnt; a task that
            repeats on a schedule is new to the corpus.
  Endel     weather and motion as inputs. Prior Endel points covered no
            playlist, time of day, and heart rate; weather/motion never.
  Firebase  Remote Config. Firebase appears nowhere in the corpus.

Backgrounds are Thinh's picks, verified against the same gates
gen-daily-batch runs: no hook-only vibe past slide 1, every app band under
BAND_MAX_LUMA (h20 67.0, h32 38.8, n01 66.3, h29 18.7), no adjacent vibe
repeat (villa-day / lounge-day / window-silhouette / villa-day /
supercars-dusk / villa-day), one person (bg-h32).

Usage:
    python3 tools/gen-five-carry-twelve.py            # every slide
    python3 tools/gen-five-carry-twelve.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, cta_slide, hook_slide, mark_hook_used,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'five-carry-twelve'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
PILLAR = 'tools'

TOOLS = ['ARCO', 'Manus', 'Endel', 'Firebase']
# Thinh wrote the titles without numbers; keep them that way.
TITLES = ['ARCO', 'Manus', 'Endel', 'Firebase']

# index 0 is the hook, 1..4 the app slides, 5 the closing card.
BGS = ['bg-n02.jpg',   # 01 hook      villa-day          Thinh's pick
       'bg-h20.jpg',   # 02 ARCO      lounge-day         band luma 67.0
       'bg-h32.jpg',   # 03 Manus     window-silhouette  band luma 38.8, the one person
       'bg-n01.jpg',   # 04 Endel     villa-day          band luma 66.3
       'bg-h29.jpg',   # 05 Firebase  supercars-dusk     band luma 18.7
       'bg-n03.jpg']   # 06 closing   villa-day          band luma 63.6

BODY = {
 # next_arco_angle('planning') -> v3, frozen; the rotation already counted it.
 'ARCO': [
    'I manage all my tasks here and the',
    'day takes 30 seconds to plan.',
    '',
    'Focus mode puts every distraction',
    'away, and Blocked Hours does it on',
    'a schedule.',
 ],
 'Manus': [
    'Set a task to repeat on a schedule',
    'and it runs without being asked.',
    '',
    'The morning report is already done',
    'when you sit down to read it.',
 ],
 'Endel': [
    'It reads the weather and your',
    'motion as inputs to the sound.',
    '',
    'A rainy still morning and a busy',
    'afternoon do not sound the same.',
 ],
 'Firebase': [
    'Remote Config changes values in',
    'the live app from a dashboard.',
    '',
    'You flip a feature on for everyone',
    'without shipping an update.',
 ],
}

CTA_SUB = ['The planner and the app blocker',
           'in one subscription.']


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
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
