#!/usr/bin/env python3
"""open-every-day: tools pillar, everyday productivity niche.

Replaces ship-alone. That post was one niche but far too deep: Proxyman and
Fastlane only land with iOS engineers, and this audience is not that. Same
rule, wider job: the apps you actually reach for daily.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     assert_same_niche, next_arco_angle, record_post_tools)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/open-every-day'
os.makedirs(OUT, exist_ok=True)

TOOLS = ['Obsidian', 'ARCO', 'Raindrop.io', 'Readwise Reader', 'Excalidraw']

# App slides carry five lines of body copy, so their backgrounds have to be
# dark enough for the scrim to hold white text. Daylight scenes wash the copy
# out no matter how hard the scrim pushes; only the hook is short enough.
BGS = ['bg-h01.jpg',   # hook        lounge-day
       'bg-h59.jpg',   # obsidian    desk-led-neon
       'bg-h53.jpg',   # arco        desk-led-warm
       'bg-h44.jpg',   # raindrop    window-silhouette
       'bg-h29.jpg',   # readwise    supercars-dusk
       'bg-h21.jpg']   # excalidraw  lounge-night

assert_same_niche(TOOLS)
assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['the apps i actually open every day',
                    'not the ones i pretend to use'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-obsidian.jpg', '1. Obsidian', [
    'Dataview turns your notes into a',
    'live query.',
    '',
    'Every unfinished task tagged uni,',
    'sorted by date, writes itself.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-raindrop.png', '3. Raindrop.io', [
    'It saves a copy of the page, not',
    'just the link.',
    '',
    'The article still opens years later,',
    'after the site has gone down.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-readwise.jpg', '4. Readwise Reader', [
    'Highlights come back on a spaced',
    'schedule, not in a dead archive.',
    '',
    'You see the line again right before',
    'you would have forgotten it.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-excalidraw.png', '5. Excalidraw', [
    'The Obsidian plugin keeps the',
    'drawing inside the note itself.',
    '',
    'The diagram lives with the notes',
    'it explains, not in another app.',
], f'{OUT}/06.jpg')

record_post_tools('open-every-day', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
