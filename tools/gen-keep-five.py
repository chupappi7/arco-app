#!/usr/bin/env python3
"""keep-five: tools pillar, rebuilt after the Higgsfield resync.

bg-h27 (the ARCO slide's background) was deleted in Higgsfield and retired by
sync_bg.py, and the user dropped Soulver. Excalidraw takes the #3 slot.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     next_arco_angle, record_post_tools)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/keep-five'
os.makedirs(OUT, exist_ok=True)

TOOLS = ['Obsidian', 'ARCO', 'Excalidraw', 'GitHub', 'Readwise Reader']
# App slides carry five lines of body copy, so their backgrounds have to be
# dark enough for the scrim to hold white text. Daylight scenes (desk-city-day,
# villa-day) wash the copy out no matter how hard the scrim pushes; the hook is
# the only slide bright enough to work, because it carries two short lines.
BGS = ['bg-h01.jpg',   # hook        lounge-day
       'bg-h59.jpg',   # obsidian    desk-led-neon
       'bg-h53.jpg',   # arco        desk-led-warm
       'bg-h44.jpg',   # excalidraw  window-silhouette
       'bg-h29.jpg',   # github      supercars-dusk
       'bg-h21.jpg']   # readwise    lounge-night

assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['the 5 apps i would keep',
                    'if i had to delete everything else'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-obsidian.jpg', '1. Obsidian', [
    'Dataview turns your notes into a',
    'live query.',
    '',
    'Every unfinished task tagged uni,',
    'sorted by date, writes itself.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-excalidraw.png', '3. Excalidraw', [
    'The Obsidian plugin keeps the',
    'drawing inside the note itself.',
    '',
    'Diagrams version in git next to',
    'the text they explain.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-github.jpg', '4. GitHub', [
    'Actions runs on a cron, not just',
    'on push.',
    '',
    'A weekly scraper or report runs',
    'on their machines, no server.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-readwise.jpg', '5. Readwise Reader', [
    'Highlights come back on a spaced',
    'schedule, not in a dead archive.',
    '',
    'You see the line again right before',
    'you would have forgotten it.',
], f'{OUT}/06.jpg')

record_post_tools('keep-five', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
