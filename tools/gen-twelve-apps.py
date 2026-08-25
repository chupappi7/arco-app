#!/usr/bin/env python3
"""twelve-apps: tools pillar. Hook from the approved set in examples.md.

Paid-tools angle, so every slide teaches something you only get once you are
actually paying attention to the app, not a feature list.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     assert_one_llm, next_arco_angle, record_post_tools,
                     pick_hook_bg)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/twelve-apps'
os.makedirs(OUT, exist_ok=True)

TOOLS = ['Canva', 'ARCO', 'Figma', 'Zapier', 'ElevenLabs']

# App slides carry five lines of white body copy, so their backgrounds have to
# be dark enough for the scrim to hold them. Adjacent vibes must differ.
HOOK_BG = pick_hook_bg()          # bg-h02, lounge-day, never used on a hook
BGS = [HOOK_BG,
       'bg-h60.jpg',   # canva       desk-led-neon
       'bg-h54.jpg',   # arco        desk-led-warm
       'bg-h45.jpg',   # figma       window-silhouette
       'bg-h35.jpg',   # zapier      supercars-dusk
       'bg-h24.jpg']   # elevenlabs  lounge-night

assert_one_llm(TOOLS)
assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['i pay for 12 apps',
                    'these 5 do all the work'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-canva.png', '1. Canva', [
    'Magic Resize rebuilds one design',
    'into every other size you need.',
    '',
    'A post becomes a story and a',
    'thumbnail without redrawing it.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-figma.png', '3. Figma', [
    'Make one element a component and',
    'every copy of it stays linked.',
    '',
    'Change the master once and it',
    'updates across every page.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-zapier.png', '4. Zapier', [
    'A zap can run on a schedule, not',
    'only when something triggers it.',
    '',
    'Every monday it pulls your numbers',
    'into a sheet while you sleep.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-elevenlabs.png', '5. ElevenLabs', [
    'It clones a voice from about a',
    'minute of clean audio.',
    '',
    'After that it reads anything you',
    'write in the same voice.',
], f'{OUT}/06.jpg')

record_post_tools('twelve-apps', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
