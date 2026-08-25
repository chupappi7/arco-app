#!/usr/bin/env python3
"""ship-alone: tools pillar, one niche (building and shipping an app).

Replaces the keep-five draft. That post mixed a reading app and a notes app
into a builder's list; a post is a set of tools for one job.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     assert_same_niche, next_arco_angle, record_post_tools)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/ship-alone'
os.makedirs(OUT, exist_ok=True)

TOOLS = ['GitHub', 'ARCO', 'Proxyman', 'Fastlane', 'Excalidraw']

# App slides carry five lines of body copy, so their backgrounds have to be
# dark enough for the scrim to hold white text. Daylight scenes wash the copy
# out no matter how hard the scrim pushes; only the hook is short enough.
BGS = ['bg-h01.jpg',   # hook        lounge-day
       'bg-h59.jpg',   # github      desk-led-neon
       'bg-h53.jpg',   # arco        desk-led-warm
       'bg-h44.jpg',   # proxyman    window-silhouette
       'bg-h29.jpg',   # fastlane    supercars-dusk
       'bg-h21.jpg']   # excalidraw  lounge-night

assert_same_niche(TOOLS)
assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['the tools i use to ship an ios app',
                    'without a team'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-github.jpg', '1. GitHub', [
    'Actions runs on a cron, not just',
    'on push.',
    '',
    'A nightly build or a weekly report',
    'runs on their machines, no server.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-proxyman.png', '3. Proxyman', [
    'Map Local swaps a live API response',
    'for a file on your Mac.',
    '',
    'You can test every paywall error',
    'state without touching the server.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-fastlane.png', '4. Fastlane', [
    'snapshot drives your UI tests to',
    'shoot the App Store screenshots.',
    '',
    'Every device and every language,',
    'from one command.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-excalidraw.png', '5. Excalidraw', [
    'The Obsidian plugin keeps the',
    'drawing inside the note itself.',
    '',
    'Screen flows version in git next',
    'to the code they describe.',
], f'{OUT}/06.jpg')

record_post_tools('ship-alone', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
