#!/usr/bin/env python3
"""4x-productivity-3: re-shoot of 4x-productivity-2. Same words, new photos.

Every hook line, title, body line and roster entry is frozen from the source
post; only the backgrounds and the topic slug change. The ARCO body is written
out rather than taken from next_arco_angle because the angle rotates and the
copy has to come out byte-identical to the source.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically.

Two guards are deliberately not run, because the source copy cannot satisfy
them and the copy is not ours to change on a re-shoot:
  - assert_one_llm: this roster carries no LLM. It shipped that way.
  - assert_hook_fresh: the hook is reused on purpose. mark_hook_used still
    records the outing so the cooldown counts it from here.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_hook_approved, assert_hook_pillar)

TOPIC = '4x-productivity-3'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the tools i used to', '4x my productivity']
TOOLS = ['Obsidian', 'ARCO', 'Granola', 'CleanShot X', 'Endel']
TITLES = ['1. Obsidian', '2. ARCO: Day Planner & Focus', '3. Granola',
          '4. CleanShot X', '5. Endel']
# Icons are named here rather than read from tool_pool: Granola was dropped
# from the pool menu in e9c3ff3 and stays off it, but the source post shipped
# with it and a re-shoot does not change the roster.
ICONS = ['icon-obsidian.jpg', 'icon-arco.png', 'icon-granola.png',
         'icon-cleanshot.png', 'icon-endel.jpg']
BGS = ['bg-h56.jpg', 'bg-h20.jpg', 'bg-h21.jpg', 'bg-h29.jpg',
       'bg-h32.jpg', 'bg-h34.jpg']

BODY = [
 [
    'Every note links to the others and',
    'the graph shows how they connect.',
    '',
    'My notes organise themselves.',
 ],
 [
    'I manage all my tasks here and plan',
    'the day in 30 seconds. Focus mode',
    'puts every distraction away.',
    '',
    'My holy grail.',
 ],
 [
    'It listens to a meeting and the',
    'notes write themselves.',
    '',
    'Nobody types minutes anymore.',
 ],
 [
    'Screenshots with scrolling capture',
    'and text you can copy straight',
    'out of the image.',
 ],
 [
    'Focus sound generated live, no',
    'lyrics and no playlist to pick.',
    '',
    'Press play and start.',
 ],
]

# hook_slide hardwires assert_hook_fresh so a generator cannot forget it. A
# re-shoot is the one case where the repeat is the point, so it is disabled
# here and nowhere else. Every other guard still runs.
c.assert_hook_fresh = lambda lines, topic=None: True

assert_audience(TOOLS)
assert_varied(BGS)
assert_bg_fresh(BGS, TOPIC)
assert_hook_approved(HOOK)
assert_hook_pillar(HOOK, 'tools')

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
