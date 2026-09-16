#!/usr/bin/env python3
"""4x-productivity-7: seventh outing of the 4x hook, fresh roster.

"the tools i used to / 4x my productivity" (tools pillar, eligible, least
recently used of the six eligible hooks).

  roster    ARCO, Antigravity, Notion, ClickUp, Descript. Antigravity is the
            LLM: it last appeared 9 posts ago (4x-productivity-6), the
            least recently used of the pool.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Antigravity's agent manager (4x-productivity-6);
            every prior Notion point (automations, rollups, synced blocks,
            templates, web clipper, calendar, forms, AI Q&A); ClickUp views,
            dependencies, multi-list, automations; Descript transcript
            editing, filler removal, voice typing. Fresh here: Antigravity's
            browser verification recording, Notion chart view, ClickUp doc
            line -> task, Descript Studio Sound.
  photos    hook from the unused pool (bg-n06, desk-empty-day), app slides
            from non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeats, no person, nothing from the previous post
            (ship-weekend-4).

Usage:
    python3 tools/gen-4x-productivity-7.py            # every slide
    python3 tools/gen-4x-productivity-7.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = '4x-productivity-7'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i used to', '4x my productivity']
PILLAR = 'tools'
# The hook promises output multiplied, so ARCO answers on planning the day,
# not on study or screen time.
THEME = 'planning'

TOOLS = ['ARCO', 'Antigravity', 'Notion', 'ClickUp', 'Descript']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Antigravity', '3. Notion',
          '4. ClickUp', '5. Descript']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-n06.jpg',   # 01 hook        desk-empty-day
       'bg-h21.jpg',   # 02 ARCO        lounge-night      band luma 64.6
       'bg-h49.jpg',   # 03 Antigravity desk-city-day     band luma 54.8
       'bg-h29.jpg',   # 04 Notion      supercars-dusk    band luma 18.7
       'bg-h20.jpg',   # 05 ClickUp     lounge-day        band luma 67.0
       'bg-h36.jpg']   # 06 Descript    supercars-dusk    band luma 20.3

BODY = {
 'Antigravity': [
    'It opens a real browser and',
    'clicks through what it built.',
    '',
    'You review a recording of the',
    'test instead of running it.',
 ],
 'Notion': [
    'A database can open as a chart',
    'that redraws as rows change.',
    '',
    'Progress becomes a live graph',
    'with nothing exported by hand.',
 ],
 'ClickUp': [
    'Highlight a line in a doc and',
    'it becomes a task on the board.',
    '',
    'Meeting notes turn into the',
    'work list as you write them.',
 ],
 'Descript': [
    'Studio sound removes the room',
    'from a laptop mic recording.',
    '',
    'A take from your kitchen sounds',
    'recorded in a booth.',
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
