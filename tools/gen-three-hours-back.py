#!/usr/bin/env python3
"""three-hours-back: tools pillar. Five apps that took the hours back.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'three-hours-back'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['i cut 3 hours of screen time', 'without deleting a single app']
THEME = 'screentime'
TOOLS = ['ARCO', 'Gemini', 'Notion', 'Endel', 'Buffer']
BGS = ['bg-h54.jpg', 'bg-h31.jpg', 'bg-h32.jpg', 'bg-h36.jpg',
       'bg-h20.jpg', 'bg-h88.jpg']

BODY = {
 'Gemini': [
    'Paste a video link and it answers',
    'from the transcript.',
    '',
    'You take the one part you needed',
    'and never open the app.',
 ],
 'Notion': [
    'The web clipper saves a page into',
    'a database in one tap.',
    '',
    'Reading gets a slot later instead',
    'of eating the next hour now.',
 ],
 'Endel': [
    'Scenes download and keep playing',
    'with no connection at all.',
    '',
    'The phone goes on airplane mode',
    'and the session still has sound.',
 ],
 'Buffer': [
    'One draft gets rewritten for every',
    'platform before it goes out.',
    '',
    'You post from a laptop instead of',
    'opening the feed to do it.',
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
