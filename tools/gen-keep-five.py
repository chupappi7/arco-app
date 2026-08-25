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
                    'if i deleted everything else'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-claude.jpg', '1. Claude', [
    'You can define your own agents and',
    'run them at the same time.',
    '',
    'One builds, one reviews, each with',
    'its own clean context window.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-notion.jpg', '3. Notion', [
    'A database automation fires when a',
    'property changes, not on a timer.',
    '',
    'Flip status to done and it stamps',
    'the date and files the page itself.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-github.jpg', '4. GitHub', [
    'Actions can run on a schedule, not',
    'only when you push.',
    '',
    'A nightly scraper or weekly report',
    'runs on their machines, not yours.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-capcut.png', '5. CapCut', [
    'Auto captions can be read out loud',
    'with text to speech in one tap.',
    '',
    'A faceless video gets a voiceover',
    'without recording anything.',
], f'{OUT}/06.jpg')

record_post_tools('keep-five', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
