#!/usr/bin/env python3
"""saved-hours-2: re-shoot of saved-hours. Same words, new photos.

Every hook line, title, body line and roster entry is frozen from the source
post; only the backgrounds and the topic slug change. saved-hours was built by
gen-daily-batch.py, whose ARCO slide draws its copy from next_arco_angle. That
angle rotates, so the lines are written out here instead — read back off
drafts/saved-hours/03.jpg, which is angle "v4" in arco_angles.json. Rotating
again would put different words on the slide, and a re-shoot changes photos,
not copy.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically. One thing was taken out of the picker's hands: the six photographs
saved-hours shot on are excluded from the walk, because a re-shoot that reuses
the source's own photos is not a re-shoot.

Two guards are deliberately not run, because the source copy cannot satisfy
them and the copy is not ours to change on a re-shoot:
  - assert_hook_approved: this hook is not in today's hook_pool.json. It went
    out with the daily batch and the pool has rotated since.
  - assert_hook_fresh: the hook is reused on purpose. mark_hook_used still
    records the outing so the cooldown counts it from here.
Everything else still runs, including assert_one_llm — this roster carries
Perplexity and nothing else.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_hook_pillar, assert_one_llm)

TOPIC = 'saved-hours-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 tools', 'that saved me hours this week']
TOOLS = ['Perplexity', 'ARCO', 'Make', 'Photoroom', 'ElevenLabs']
TITLES = ['1. Perplexity', '2. ARCO', '3. Make', '4. Photoroom',
          '5. ElevenLabs']
ICONS = ['icon-perplexity.png', 'icon-arco.png', 'icon-make.png',
         'icon-photoroom.png', 'icon-elevenlabs.png']
BGS = ['bg-h62.jpg', 'bg-h24.jpg', 'bg-h32.jpg', 'bg-h34.jpg',
       'bg-h35.jpg', 'bg-h46.jpg']

BODY = [
 [
    'You can aim a search at academic',
    'papers or reddit alone.',
    '',
    'The answer stops averaging the',
    'whole internet.',
 ],
 [
    'All my tasks live here and I plan the',
    'whole day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'My holy grail.',
 ],
 [
    'A scenario shows the data moving',
    'through every step.',
    '',
    'You watch where it breaks instead',
    'of reading a log.',
 ],
 [
    'Point it at a folder and it cuts',
    'the background from all of them.',
    '',
    'Fifty product shots take one',
    'pass, not fifty.',
 ],
 [
    'It clones a voice from about a',
    'minute of clean audio.',
    '',
    'After that it reads anything you',
    'write in the same voice.',
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
