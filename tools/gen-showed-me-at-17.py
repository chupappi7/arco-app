#!/usr/bin/env python3
"""showed-me-at-17: tools pillar. Things a 17 year old could start using today.

Backgrounds picked with the gen-daily-batch algorithm and frozen so the post
rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'showed-me-at-17'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 apps i wish someone', 'showed me at 17']
TOOLS = ['ARCO', 'Gemini', 'Obsidian', 'Raycast', 'Endel']
BGS = ['bg-h53.jpg', 'bg-h35.jpg', 'bg-h31.jpg', 'bg-h37.jpg',
       'bg-h45.jpg', 'bg-h52.jpg']

BODY = {
 'Gemini': [
    'Gemini takes a whole textbook as',
    'an upload, not pasted chunks.',
    '',
    'You ask about one chapter and it',
    'answers from those pages.',
 ],
 'Obsidian': [
    'Your notes are plain markdown',
    'files sitting in a folder.',
    '',
    'They open on any device and keep',
    'working with no internet.',
 ],
 'Raycast': [
    'A snippet expands a keyword into',
    'a whole block of text anywhere.',
    '',
    'Your email intro types itself out',
    'from two letters.',
 ],
 'Endel': [
    'With an Apple Watch the sound',
    'follows your heart rate.',
    '',
    'It settles as you settle, instead',
    'of looping the same track.',
 ],
}

preflight(TOPIC, TOOLS, BGS)

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
