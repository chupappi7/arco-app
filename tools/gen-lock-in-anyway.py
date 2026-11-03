#!/usr/bin/env python3
"""lock-in-anyway: learn pillar. Studying on the days motivation does not turn
up, by making the first move a click instead of a decision.

Backgrounds picked with the gen-daily-batch guards (hook-only vibes skipped,
copy band under BAND_MAX_LUMA, no adjacent vibe repeat, one person at most)
and frozen here so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'lock-in-anyway'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['this is how you lock in', "when you don't feel like it"]
TOOLS = ['ARCO', 'Claude', 'Raycast', 'CleanShot X', 'Canva']
BGS = ['bg-h36.jpg', 'bg-h49.jpg', 'bg-n03.jpg', 'bg-n06.jpg',
       'bg-h20.jpg', 'bg-h39.jpg']

BODY = {
 'Claude': [
    'Ask for a quiz on what you just',
    'read and it builds a working one.',
    '',
    'You click through questions in the',
    'chat instead of rereading a page.',
 ],
 'Raycast': [
    'Floating Notes keeps a note above',
    'every window on one hotkey.',
    '',
    'The next step stays on screen',
    'while you work somewhere else.',
 ],
 'CleanShot X': [
    'Captures park in a corner overlay',
    'instead of piling on the desktop.',
    '',
    'You drag the diagram into your',
    'notes without saving a file.',
 ],
 'Canva': [
    'Any design opens out into an',
    'infinite whiteboard.',
    '',
    'The whole topic gets mapped in one',
    'place before you write a word.',
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
