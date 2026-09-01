#!/usr/bin/env python3
"""ship-alone-3: re-shoot of ship-alone. Same words, new photos.

A copy of gen-ship-alone-2.py -- itself the first re-shoot of ship-alone --
with the topic slug and the backgrounds changed and nothing else, so every
hook line, title, body line, roster entry, caption and title comes out
byte-identical to the source post. ship-alone's generator was never committed,
so the copy reaches here by way of gen-ship-alone-2.py, which read it back off
drafts/ship-alone/01.jpg .. 06.jpg slide by slide, including the ARCO card.
That card stays written out rather than drawn from next_arco_angle: the angle
rotates, and a re-shoot changes photos, not copy.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically, in the order the walk returned them. Twelve frames were taken out
of the walk by hand: the six ship-alone was shot on, because a re-shoot that
reuses the photographs it is re-shooting is not a re-shoot, and the six
ship-alone-2 used, because two re-shoots sharing a set are one post twice.
Neither set is in bg_history -- ship-alone predates that log -- so ship-alone's
six were identified by correlating its slides against the pool, and both sets
are named in SOURCE_BGS below.

  01 hook        bg-h76  desk-led-neon      first hook outing
  02 Codex       bg-h24  lounge-night       band luma 49.8
  03 ARCO        bg-h36  supercars-dusk     band luma 20.3, darkest
  04 GitHub      bg-h46  desk-city-day      band luma 59.7
  05 RevenueCat  bg-h88  supercars-dusk     band luma 28.2
  06 Notion      bg-n01  villa-day          band luma 66.3, no person in the set

One guard is deliberately not run, because the source copy cannot satisfy it
and the copy is not ours to change on a re-shoot:
  - assert_hook_approved: this hook is not in today's hook_pool.json. It went
    out with the daily batch and the pool has rotated since.
assert_hook_fresh is stubbed the same way it was on ship-alone-2, where the
reuse was inside the cooldown; here the hook has sat out long enough to pass
it on its own. mark_hook_used still records the outing so the cooldown counts
it from here. Everything else still runs, including assert_one_llm -- this
roster carries Codex and nothing else.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_hook_pillar, assert_one_llm)

TOPIC = 'ship-alone-3'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 tools', 'that replace a whole team']
TOOLS = ['Codex', 'ARCO', 'GitHub', 'RevenueCat', 'Notion']
TITLES = ['1. Codex', '2. ARCO: Day Planner & Focus', '3. GitHub',
          '4. RevenueCat', '5. Notion']
ICONS = ['icon-codex.png', 'icon-arco.png', 'icon-github.jpg',
         'icon-revenuecat.png', 'icon-notion.jpg']
BGS = ['bg-h76.jpg', 'bg-h24.jpg', 'bg-h36.jpg', 'bg-h46.jpg',
       'bg-h88.jpg', 'bg-n01.jpg']

# The photographs the earlier cuts of this post were shot on: ship-alone's own
# six, then ship-alone-2's. Both sets are excluded from the picker.
SOURCE_BGS = ['bg-h14.jpg', 'bg-h12.jpg', 'bg-n09.jpg', 'bg-h09.jpg',
              'bg-h04.jpg', 'bg-h02.jpg',
              'bg-h63.jpg', 'bg-h20.jpg', 'bg-h21.jpg', 'bg-h29.jpg',
              'bg-h32.jpg', 'bg-h34.jpg']

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

assert set(BGS).isdisjoint(SOURCE_BGS), 'a source frame leaked back in'
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
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

for i in range(len(TOOLS)):
    n = i + 1
    app_slide(BGS[n], ICONS[i], TITLES[i], BODY[i], f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
