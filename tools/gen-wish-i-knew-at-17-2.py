#!/usr/bin/env python3
"""wish-i-knew-at-17-2: the wish-i-knew-at-17 post re-shot on new photographs.

A mechanical re-shoot: every hook line, title, body line, roster entry and
caption is byte-identical to gen-wish-i-knew-at-17.py; only the topic slug and
the backgrounds change. The hook slide keeps its icon shelf (compose.hook_slide
icons=, roster order with ARCO first) and every guard still runs.

Hook is "5 apps i wish someone / showed me at 17", reused verbatim from the
source post, so mark_hook_used counts this outing against the cooldown. It is
a school-age hook, so THEME is 'study' and the ARCO card comes back as angle
l1, the study block that closes the distracting apps with it, rather than the
plan-the-day-in-30-seconds copy that answers a build hook.

Backgrounds picked with the gen-daily-batch walk: hook from the frames that are
unused as hooks and outside the cross-post cooldown, app frames with no
hook-only vibe, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, and none of the source post's six photos — the whole point of the
re-shoot is different photographs. ARCO gets the darkest desk band because
slide 02 is the longest block in the post; supercars-dusk cannot sit at 02
because the hook already carries that vibe.

  01 hook        bg-h35  supercars-dusk     first hook outing
  02 ARCO        bg-n06  desk-empty-day     band luma 53.6, seven lines
  03 Perplexity  bg-h36  supercars-dusk     band luma 20.3, darkest
  04 Notion      bg-h49  desk-city-day      band luma 54.8
  05 Obsidian    bg-n04  villa-day          band luma 57.8
  06 Canva       bg-h45  window-silhouette  band luma 54.3, the one person

Usage:
    python3 tools/gen-wish-i-knew-at-17-2.py            # every slide
    python3 tools/gen-wish-i-knew-at-17-2.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'wish-i-knew-at-17-2'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i wish someone', 'showed me at 17']
PILLAR = 'tools'
# 17 means school, so ARCO answers on the study block and the apps that close
# with it, not on planning a work day.
THEME = 'study'

TOOLS = ['ARCO', 'Perplexity', 'Notion', 'Obsidian', 'Canva']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Perplexity', '3. Notion',
          '4. Obsidian', '5. Canva']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-perplexity.png', 'icon-notion.jpg',
         'icon-obsidian.jpg', 'icon-canva.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h35.jpg',   # 01 hook        supercars-dusk     (first hook outing)
       'bg-n06.jpg',   # 02 ARCO        desk-empty-day     band luma 53.6
       'bg-h36.jpg',   # 03 Perplexity  supercars-dusk     band luma 20.3
       'bg-h49.jpg',   # 04 Notion      desk-city-day      band luma 54.8
       'bg-n04.jpg',   # 05 Obsidian    villa-day          band luma 57.8
       'bg-h45.jpg']   # 06 Canva       window-silhouette  band luma 54.3

BODY = {
 'Perplexity': [
    'A finished thread turns into a Page,',
    'written up with its sources.',
    '',
    'A night of research on one topic',
    'ends as a link you can send.',
 ],
 'Notion': [
    'The web clipper drops any page',
    'into a database with your fields.',
    '',
    'Every source for the essay lands in',
    'one table instead of thirty tabs.',
 ],
 'Obsidian': [
    'Put a caret and an id after a line',
    'and you can link to that line.',
    '',
    'The essay points at the exact',
    'sentence, not the whole note.',
 ],
 'Canva': [
    'Bulk create builds one design per',
    'row of a spreadsheet.',
    '',
    'A list of forty terms comes back',
    'as forty finished cards.',
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
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', icons=SHELF)
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
