#!/usr/bin/env python3
"""keep-five: tools pillar, mainstream roster, one LLM.

Duplicates across posts are fine now; the freshness that matters is the
teaching point, not the logo.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     assert_one_llm, next_arco_angle, record_post_tools)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/keep-five'
os.makedirs(OUT, exist_ok=True)

TOOLS = ['Claude', 'ARCO', 'Notion', 'GitHub', 'CapCut']

# App slides carry five lines of body copy, so their backgrounds have to be
# dark enough for the scrim to hold white text. Daylight scenes wash the copy
# out no matter how hard the scrim pushes; only the hook is short enough.
BGS = ['bg-h01.jpg',   # hook      lounge-day
       'bg-h59.jpg',   # claude    desk-led-neon
       'bg-h53.jpg',   # arco      desk-led-warm
       'bg-h44.jpg',   # notion    window-silhouette
       'bg-h29.jpg',   # github    supercars-dusk
       'bg-h21.jpg']   # capcut    lounge-night

assert_one_llm(TOOLS)
assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['the 5 apps i would keep',
                    'if i had to delete everything else'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-claude.jpg', '1. Claude', [
    'Claude Code edits the project files',
    'in the terminal, not in a chat.',
    '',
    'Everything else hands me text to',
    'paste. This one does the work.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-notion.jpg', '3. Notion', [
    'One synced block can sit in many',
    'pages and stay the same block.',
    '',
    'I keep it for that alone. Nothing',
    'quietly goes out of date.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-github.jpg', '4. GitHub', [
    'Actions runs on a schedule, not',
    'only when you push.',
    '',
    'It is my backup and my server at',
    'once, so it counts as one app.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-capcut.png', '5. CapCut', [
    'Auto captions stay editable text,',
    'so one fix keeps the timing.',
    '',
    'Everything i post goes through it.',
    'It survives any cull.',
], f'{OUT}/06.jpg')

record_post_tools('keep-five', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
