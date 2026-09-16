#!/usr/bin/env python3
"""wish-i-knew-at-17-3: third outing of the at-17 hook, fresh roster.

"5 apps i wish someone / showed me at 17" (tools pillar, eligible).

  roster    ARCO, Manus, GitHub, Figma, Loom. Manus is the LLM: after
            Antigravity in 4x-productivity-7, it is the least recently used
            (last seen in five-that-stay, 6 posts back at build time).
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Manus cloud machine, mid-run corrections,
            scheduled tasks, browser clicking; GitHub actions/pages/
            codespaces/branch protection; Figma components, auto layout,
            variables, dev mode, prototype links; Loom auto chapters,
            timestamp comments, filler cut, instant link. Fresh here: Manus
            slide decks, the GitHub student developer pack, Figma community
            files duplicating editable, Loom viewer drop-off insights.
  photos    hook from the unused pool (bg-h48, desk-city-day), app slides
            from non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeats, one person (bg-h45, window-silhouette, slide 6),
            nothing from the previous post (4x-productivity-7).

Usage:
    python3 tools/gen-wish-i-knew-at-17-3.py            # every slide
    python3 tools/gen-wish-i-knew-at-17-3.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'wish-i-knew-at-17-3'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i wish someone', 'showed me at 17']
PILLAR = 'tools'
# The hook speaks to a younger self drowning in distraction, so ARCO answers
# on focus mode locking the apps, not on planning speed.
THEME = 'focus'

TOOLS = ['ARCO', 'Manus', 'GitHub', 'Figma', 'Loom']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Manus', '3. GitHub',
          '4. Figma', '5. Loom']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h48.jpg',   # 01 hook   desk-city-day
       'bg-h31.jpg',   # 02 ARCO   lounge-night        band luma 19.7
       'bg-h50.jpg',   # 03 Manus  desk-city-day       band luma 64.7
       'bg-h35.jpg',   # 04 GitHub supercars-dusk      band luma 37.2
       'bg-h22.jpg',   # 05 Figma  lounge-day          band luma 53.5
       'bg-h45.jpg']   # 06 Loom   window-silhouette   band luma 54.3 (person)

BODY = {
 'Manus': [
    'Give it a topic and it comes',
    'back with a full slide deck.',
    '',
    'The presentation is done before',
    'you open a slides app.',
 ],
 'GitHub': [
    'A school email unlocks the',
    'student pack of paid dev tools.',
    '',
    'Copilot, cloud credits and a',
    'domain cost you nothing.',
 ],
 'Figma': [
    'Any community file duplicates',
    'into your drafts, fully editable.',
    '',
    'You learn design by opening how',
    'real apps were actually built.',
 ],
 'Loom': [
    'It shows who watched your video',
    'and where they dropped off.',
    '',
    'You see the exact minute a',
    'pitch starts losing people.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            c.pick_hook_bg(prefer=BGS[0])
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
        mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):16s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

    if only is None:
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
