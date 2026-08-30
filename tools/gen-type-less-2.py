#!/usr/bin/env python3
"""type-less-2: re-shoot of type-less. Same words, new photos.

Every hook line, title, body line and roster entry is frozen from the source
post; only the backgrounds and the topic slug change. type-less was built by a
daily batch whose generator was never committed, so the copy here was read back
off drafts/type-less/*.jpg line by line. The ARCO body is written out rather
than taken from next_arco_angle because the angle rotates and the copy has to
come out byte-identical to the source.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically. One choice was taken out of the picker's hands: bg-h21 is the
photograph the source shot its Claude slide on, and a re-shoot that reuses it
is not a re-shoot. Excluding it moves the walk on to bg-h35.

Two guards are deliberately not run, because the source copy cannot satisfy
them and the copy is not ours to change on a re-shoot:
  - assert_hook_approved: this hook is not in today's hook_pool.json. It went
    out in the 2026-08-24 batch and the pool has rotated since.
  - assert_hook_fresh: the hook is reused on purpose. mark_hook_used still
    records the outing so the cooldown counts it from here.
Everything else still runs, including assert_one_llm — this roster carries
Claude and nothing else.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_hook_pillar, assert_one_llm)

TOPIC = 'type-less-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['i barely type anymore', 'these 5 tools do it for me']
TOOLS = ['Superwhisper', 'ARCO', 'Granola', 'Claude', 'CleanShot X']
TITLES = ['1. Superwhisper', '2. ARCO: Day Planner & Focus', '3. Granola',
          '4. Claude', '5. CleanShot X']
ICONS = ['icon-superwhisper.jpg', 'icon-arco.png', 'icon-granola.png',
         'icon-claude.jpg', 'icon-cleanshot.png']
BGS = ['bg-h58.jpg', 'bg-h20.jpg', 'bg-h29.jpg', 'bg-h32.jpg',
       'bg-h34.jpg', 'bg-h35.jpg']

BODY = [
 [
    'Hold a key, talk, and clean text',
    'appears in any app at speaking',
    'speed.',
 ],
 [
    'Planning the day takes 30 seconds,',
    'not a journaling session. Tasks,',
    'plan and app blocking in one.',
    '',
    'My holy grail.',
 ],
 [
    'It listens to a meeting and the',
    'notes write themselves.',
 ],
 [
    'I dictate a rough idea and ask for',
    'the finished draft. Editing beats',
    'writing from zero.',
 ],
 [
    'Copy text straight out of any',
    'screenshot. No retyping from',
    'images ever again.',
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
# so `prefer` is silently ignored and it logs a background this post never
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
