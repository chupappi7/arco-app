#!/usr/bin/env python3
"""weekend-not-month: tools pillar. The stack that compresses a build.

Backgrounds picked with the gen-daily-batch algorithm and frozen so the post
rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'weekend-not-month'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['how i ship in a weekend', 'what used to take a month']
TOOLS = ['ARCO', 'Codex', 'Supabase', 'Figma', 'TestFlight']
BGS = ['bg-h29.jpg', 'bg-h31.jpg', 'bg-h37.jpg', 'bg-h81.jpg',
       'bg-h84.jpg', 'bg-h21.jpg']

BODY = {
 'Codex': [
    'An AGENTS.md file in the repo tells',
    'it how to build and test.',
    '',
    'It runs your commands instead of',
    'guessing on every new task.',
 ],
 'Supabase': [
    'Access rules live in the database',
    'itself, not in your app code.',
    '',
    'A user only ever sees their own',
    'rows, whatever calls the api.',
 ],
 'Figma': [
    'Variables hold your colours and a',
    'mode swaps the whole set.',
    '',
    'Every screen switches to dark mode',
    'without redrawing anything.',
 ],
 'TestFlight': [
    'A public link puts up to 10,000',
    'testers on your beta.',
    '',
    'You post one url instead of',
    'collecting emails to invite.',
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
