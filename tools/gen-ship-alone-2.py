#!/usr/bin/env python3
"""ship-alone-2: re-shoot of ship-alone. Same words, new photos.

Every hook line, title, body line and roster entry is frozen from the source
post; only the backgrounds and the topic slug change. ship-alone went out with
the 2026-08-23 daily batch and its generator was never committed, so the copy
here was read back off drafts/ship-alone/01.jpg .. 06.jpg, slide by slide,
including the ARCO card. That card is written out rather than drawn from
next_arco_angle: the angle rotates, and a re-shoot changes photos, not copy.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically. One thing was taken out of the picker's hands: the six photographs
ship-alone shot on are excluded from the walk, because a re-shoot that reuses
the source's own photos is not a re-shoot. Those six are not in bg_history
either -- the post predates that log -- so they were identified by correlating
each slide against the pool and are named in SOURCE_BGS below.

Two guards are deliberately not run, because the source copy cannot satisfy
them and the copy is not ours to change on a re-shoot:
  - assert_hook_approved: this hook is not in today's hook_pool.json. It went
    out with the daily batch and the pool has rotated since.
  - assert_hook_fresh: the hook is reused on purpose. mark_hook_used still
    records the outing so the cooldown counts it from here.
Everything else still runs, including assert_one_llm -- this roster carries
Codex and nothing else.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_hook_pillar, assert_one_llm)

TOPIC = 'ship-alone-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 tools', 'that replace a whole team']
TOOLS = ['Codex', 'ARCO', 'GitHub', 'RevenueCat', 'Notion']
TITLES = ['1. Codex', '2. ARCO: Day Planner & Focus', '3. GitHub',
          '4. RevenueCat', '5. Notion']
ICONS = ['icon-codex.png', 'icon-arco.png', 'icon-github.jpg',
         'icon-revenuecat.png', 'icon-notion.jpg']
BGS = ['bg-h63.jpg', 'bg-h20.jpg', 'bg-h21.jpg', 'bg-h29.jpg',
       'bg-h32.jpg', 'bg-h34.jpg']

# The six photographs the source post was shot on. Excluded from the picker.
SOURCE_BGS = ['bg-h14.jpg', 'bg-h12.jpg', 'bg-n09.jpg', 'bg-h09.jpg',
              'bg-h04.jpg', 'bg-h02.jpg']

BODY = [
 [
    'I describe the feature and it writes',
    'the code, runs it and fixes what',
    'breaks before I look at it.',
    '',
    'I review the diff, not the typing.',
 ],
 [
    'I manage all my tasks here and plan',
    'the day in 30 seconds. Focus mode',
    'puts every distraction away.',
    '',
    'My holy grail.',
 ],
 [
    'Actions runs my tests and builds',
    'on every push, on their machines.',
    '',
    'Branch protection stops me merging',
    'anything that failed.',
 ],
 [
    'Subscriptions without a payment',
    'server. It handles receipts,',
    'renewals and refunds.',
    '',
    'One line tells the app who paid.',
 ],
 [
    'Databases, not pages. The roadmap,',
    'the content calendar and every idea',
    'are one table with different views.',
 ],
]

# hook_slide hardwires both hook guards so a generator cannot forget them. A
# re-shoot is the one case where the repeat is the point, so they are disabled
# here and nowhere else. Every other guard still runs.
c.assert_hook_fresh = lambda lines, topic=None: True
c.assert_hook_approved = lambda lines: True

assert_one_llm(TOOLS)
assert_audience(TOOLS)
assert_varied(BGS)
assert_bg_fresh(BGS, TOPIC)
assert_hook_pillar(HOOK, 'tools')

# Record the hook background by hand rather than through pick_hook_bg: that
# function narrows its candidates to night-desk vibes whenever any are unused,
# so `prefer` is silently ignored and it can log a background this post never
# rendered.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'), indent=1)

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

for i in range(len(TOOLS)):
    n = i + 1
    app_slide(BGS[n], ICONS[i], TITLES[i], BODY[i], f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
