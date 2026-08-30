#!/usr/bin/env python3
"""run-it-all-at-19: tools pillar. The stack behind a one person business.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'run-it-all-at-19'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['everything i run my business on', 'at 19']
THEME = 'business'
TOOLS = ['ARCO', 'Perplexity', 'Stripe', 'RevenueCat', 'Framer']
BGS = ['bg-h40.jpg', 'bg-h22.jpg', 'bg-h24.jpg', 'bg-h34.jpg',
       'bg-h35.jpg', 'bg-n04.jpg']

BODY = {
 'Perplexity': [
    'Labs turns a question into a',
    'spreadsheet or a small dashboard.',
    '',
    'You get the comparison built for',
    'you, not another page of links.',
 ],
 'Stripe': [
    'The customer portal is a hosted',
    'page where people manage billing.',
    '',
    'They cancel or swap a card without',
    'you building a settings screen.',
 ],
 'RevenueCat': [
    'Experiments show two paywalls at',
    'once and split the new installs.',
    '',
    'You learn which price earns more',
    'before you commit to one.',
 ],
 'Framer': [
    'A CMS collection turns one page',
    'into a template for every entry.',
    '',
    'Fifty posts share one layout and',
    'you change it in a single place.',
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
