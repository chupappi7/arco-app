#!/usr/bin/env python3
"""business-at-19: tools pillar. Running the business, not building the code.

Backgrounds were chosen with the gen-daily-batch algorithm (hook unused in
hook_usage.json, app slides non-hook-only, copy band under BAND_MAX_LUMA, no
adjacent vibe repeat, at most one person) and frozen here so the post rebuilds
the same way.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'business-at-19'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the tools i use to run my business', 'at 19 years old']
TOOLS = ['ARCO', 'Claude', 'Notion', 'Canva', 'RevenueCat']
# Slide 2 was on bg-h83, one of the bg-h81..h88 frames a build generated
# itself when the pool ran short. Thinh retired all eight to bg/_unapproved/:
# the pool is his to curate, so a build picks from what is already in it.
BGS = ['bg-h12.jpg', 'bg-h21.jpg', 'bg-h22.jpg', 'bg-h24.jpg',
       'bg-h50.jpg', 'bg-h29.jpg']

BODY = {
 'Claude': [
    'Claude connects to your other apps',
    'through MCP servers.',
    '',
    'It reads and edits inside them from',
    'the same chat, with no exporting.',
 ],
 'Notion': [
    'A synced block shows the same',
    'content on several pages.',
    '',
    'You change the price once and it',
    'updates everywhere it appears.',
 ],
 'Canva': [
    'A brand kit applies your fonts and',
    'colours to any template at once.',
    '',
    'Everything you make matches, with',
    'no design work each time.',
 ],
 'RevenueCat': [
    'Paywalls are configured in the',
    'dashboard, not in the build.',
    '',
    'You change a price or a layout',
    'without shipping an app update.',
 ],
}

preflight(TOPIC, TOOLS, BGS)

# hook_usage.json only gets the entry the first time this runs; a rebuild
# must not consume a second background from the rotation.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK)

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    body = next_arco_angle() if tool == 'ARCO' else BODY[tool]
    app_slide(bg, icons[tool], f'{n}. {tool}', body, f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
