#!/usr/bin/env python3
"""four-x-tools: tools pillar. The five that multiplied the output.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'four-x-tools'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the tools i used to', '4x my productivity']
THEME = 'planning'
TOOLS = ['ARCO', 'Cursor', 'Raycast', 'Zapier', 'Loom']
BGS = ['bg-n10.jpg', 'bg-h88.jpg', 'bg-h20.jpg', 'bg-h36.jpg',
       'bg-h21.jpg', 'bg-h39.jpg']

BODY = {
 'Cursor': [
    'Rules files in the repo apply your',
    'conventions to every edit.',
    '',
    'You stop repeating the same',
    'correction in each new chat.',
 ],
 'Raycast': [
    'Extensions search inside the apps',
    'you already use, from one bar.',
    '',
    'You land on the page or the issue',
    'without opening the app first.',
 ],
 'Zapier': [
    'A path splits the zap and runs a',
    'different branch per case.',
    '',
    'One automation covers the',
    'exceptions instead of five.',
 ],
 'Loom': [
    'It cuts the ums and the long',
    'silences out of the recording.',
    '',
    'One take is usable, so nothing',
    'has to be recorded twice.',
 ],
}

preflight(TOPIC, TOOLS, BGS, hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
    app_slide(bg, icons[tool], f'{n}. {tool}', body, f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
