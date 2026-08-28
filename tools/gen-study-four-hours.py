#!/usr/bin/env python3
"""study-four-hours: learn pillar. What makes a four hour session possible when
the phone is out of the loop: the plan, a tutor that makes you do the work, and
notes that revise you back.

Backgrounds picked with the gen-daily-batch guards (hook-only vibes skipped,
copy band under BAND_MAX_LUMA, no adjacent vibe repeat, one person at most)
and frozen here so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'study-four-hours'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['how i study 4 hours', 'without touching my phone']
TOOLS = ['ARCO', 'ChatGPT', 'Obsidian', 'Notion', 'ElevenLabs']
BGS = ['bg-h38.jpg', 'bg-h46.jpg', 'bg-h34.jpg', 'bg-n01.jpg',
       'bg-h48.jpg', 'bg-n05.jpg']

BODY = {
 'ChatGPT': [
    'Study mode replies with questions',
    'and steps, not the answer.',
    '',
    'You get walked through one problem',
    'and can do the next one alone.',
 ],
 'Obsidian': [
    'Canvas puts your notes on one',
    'infinite board, joined by arrows.',
    '',
    'A whole topic sits on one screen',
    'the week before the exam.',
 ],
 'Notion': [
    'A toggle block hides whatever is',
    'inside it until you click it.',
    '',
    'Put the answer under the question',
    'and your notes become flashcards.',
 ],
 'ElevenLabs': [
    'The Reader app reads any PDF or',
    'article out loud in a real voice.',
    '',
    'The chapter you never got to goes',
    'in on the walk home.',
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
