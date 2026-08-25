#!/usr/bin/env python3
"""open-every-day: tools pillar, everyday productivity, big apps only.

Supporting tools are names the audience already has installed. Naming a small
app promotes it for free and costs a slot, because the viewer stops to work
out what it is. ARCO is the only app in the post anyone is meant to discover.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     assert_same_niche, assert_big_apps, next_arco_angle,
                     record_post_tools)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/open-every-day'
os.makedirs(OUT, exist_ok=True)

TOOLS = ['Apple Shortcuts', 'ARCO', 'Wispr Flow', 'Google Sheets', 'Apple Notes']

# App slides carry five lines of body copy, so their backgrounds have to be
# dark enough for the scrim to hold white text. Daylight scenes wash the copy
# out no matter how hard the scrim pushes; only the hook is short enough.
BGS = ['bg-h01.jpg',   # hook        lounge-day
       'bg-h59.jpg',   # shortcuts   desk-led-neon
       'bg-h53.jpg',   # arco        desk-led-warm
       'bg-h44.jpg',   # wispr flow  window-silhouette
       'bg-h29.jpg',   # sheets      supercars-dusk
       'bg-h21.jpg']   # notes       lounge-night

assert_big_apps(TOOLS)
assert_same_niche(TOOLS)
assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['the apps i actually open every day',
                    'not the ones i pretend to use'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-shortcuts.png', '1. Shortcuts', [
    'Automations can fire on arrival,',
    'not just at a time.',
    '',
    'You walk into the library and the',
    'phone goes silent on its own.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-wisprflow.png', '3. Wispr Flow', [
    'It types into any app and strips',
    'the ums while you talk.',
    '',
    'A long message takes about a',
    'quarter of the time.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-gsheets.png', '4. Google Sheets', [
    'IMPORTHTML pulls a table straight',
    'off a web page.',
    '',
    'The sheet updates itself when the',
    'page changes, no copy paste.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-applenotes.png', '5. Notes', [
    'Search reads the words inside your',
    'photos and scanned pages.',
    '',
    'A whiteboard you shot in march is',
    'findable by what it said.',
], f'{OUT}/06.jpg')

record_post_tools('open-every-day', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
