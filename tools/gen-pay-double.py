#!/usr/bin/env python3
"""pay-double: tools pillar, stacked uppercase hook.

Hook style replicated from the two posts that performed (tools-nobody-posts,
ship-alone): Compressed Black headline over a Condensed Bold second line.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, assert_varied, assert_fresh_tools,
                     assert_one_llm, next_arco_angle, record_post_tools)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/pay-double'
os.makedirs(OUT, exist_ok=True)

# Exactly one LLM, rotated to Gemini (Claude carried keep-five, Perplexity
# the draft before this).
TOOLS = ['Gemini', 'ARCO', 'Loom', 'Airtable', 'Framer']

BGS = ['bg-h03.jpg',     # hook, taken from the rotation on first build
       'bg-h50.jpg',     # gemini    desk-city-day
       'bg-h24.jpg',     # arco      lounge-night
       'bg-h45.jpg',     # loom      window-silhouette (the one person)
       'bg-h35.jpg',     # airtable  supercars-dusk
       'bg-h34.jpg']     # framer    desk-empty-day

assert_one_llm(TOOLS)
assert_fresh_tools(TOOLS)
assert_varied(BGS)

hook_slide(BGS[0], ['5 tools', 'i would pay double for'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-gemini.png', '1. Gemini', [
    'Deep Research reads dozens of',
    'sources and cites every claim.',
    '',
    'You get the sources, not an answer',
    'you have to take on trust.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-loom.png', '3. Loom', [
    'It writes the title, summary and',
    'chapters from what you said.',
    '',
    'Record once and the description',
    'is already done.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-airtable.png', '4. Airtable', [
    'A form writes straight into the',
    'base and fires an automation.',
    '',
    'Someone submits and the row, the',
    'email and the status all happen.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-framer.png', '5. Framer', [
    'The design file is the site. You',
    'publish from the canvas itself.',
    '',
    'No handoff, no rebuilding it in',
    'code afterwards.',
], f'{OUT}/06.jpg')

record_post_tools('pay-double', TOOLS)
print('\nbackgrounds:', ', '.join(BGS))
