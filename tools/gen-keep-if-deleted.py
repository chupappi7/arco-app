#!/usr/bin/env python3
"""keep-if-deleted: tools pillar. The five that would survive a clean phone.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'keep-if-deleted'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
THEME = 'planning'
TOOLS = ['ARCO', 'ChatGPT', 'Obsidian', 'Canva', 'Notion']
BGS = ['bg-h55.jpg', 'bg-h31.jpg', 'bg-h35.jpg', 'bg-h22.jpg',
       'bg-h37.jpg', 'bg-n04.jpg']

BODY = {
 'ChatGPT': [
    'Canvas opens the draft beside the',
    'chat and edits happen in place.',
    '',
    'You rewrite one paragraph instead',
    'of regenerating the whole thing.',
 ],
 'Obsidian': [
    'Bases turns a folder of notes into',
    'a table you can filter.',
    '',
    'The reading list is a view of what',
    'you wrote, not a second list.',
 ],
 'Canva': [
    'A doc converts into slides in one',
    'click, headings and all.',
    '',
    'The deck gets built from the notes',
    'you already wrote.',
 ],
 'Notion': [
    'Notion AI answers a question from',
    'the pages in your workspace.',
    '',
    'You search what you wrote instead',
    'of trying to remember where.',
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
