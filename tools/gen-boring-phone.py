#!/usr/bin/env python3
"""boring-phone: tools pillar. What is left on the phone once the feeds are gone.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'boring-phone'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['my phone is boring now', 'and it changed everything']
THEME = 'focus'
TOOLS = ['ARCO', 'Claude', 'CapCut', 'Higgsfield', 'Descript']
BGS = ['bg-h59.jpg', 'bg-h37.jpg', 'bg-h45.jpg', 'bg-h29.jpg',
       'bg-h24.jpg', 'bg-h34.jpg']

BODY = {
 'Claude': [
    'It builds a working page in the',
    'chat and you can share the link.',
    '',
    'The small tool you needed exists',
    'without installing anything.',
 ],
 'CapCut': [
    'Auto cutout removes the background',
    'with no green screen.',
    '',
    'You film against a bare wall and',
    'still land on any backdrop.',
 ],
 'Higgsfield': [
    'A preset locks the look so a whole',
    'batch comes out in one style.',
    '',
    'Every image in a set matches with',
    'no prompt written twice.',
 ],
 'Descript': [
    'Type over a word you fluffed and',
    'it speaks it in your voice.',
    '',
    'One bad sentence gets fixed',
    'without recording the take again.',
 ],
}

preflight(TOPIC, TOOLS, BGS, hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

# ARCO carries its full App Store name on its own slide, so a viewer who
# goes looking finds the listing under the name they just read.
TITLES = {'ARCO': 'ARCO: Day Planner & Focus'}

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
    title = f'{n}. {TITLES.get(tool, tool)}'
    app_slide(bg, icons[tool], title, body, f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
