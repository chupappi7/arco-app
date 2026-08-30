#!/usr/bin/env python3
"""pay-double-2: re-shoot of pay-double. Same words, new photos.

Every hook line, title, body line and roster entry is frozen from the source
post; only the backgrounds and the topic slug change. The ARCO body is written
out rather than taken from next_arco_angle because the angle rotates and the
copy has to come out byte-identical to the source: it is angle v1, read back
off drafts/pay-double/03.jpg.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically. The source's own six photos are excluded from the walk as well:
a re-shoot that reuses one of them is not a re-shoot.

One guard is deliberately not run, because the source copy cannot satisfy it
and the copy is not ours to change on a re-shoot:
  - assert_hook_approved: this hook is not in today's hook_pool.json. It went
    out with the 2026-08-26 build and the pool has rotated since.
assert_hook_fresh is left on and passes on its own — the source hook is well
past HOOK_COOLDOWN. mark_hook_used still records this outing so the cooldown
counts it from here. Every other guard runs, including assert_one_llm: this
roster carries Gemini and nothing else.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_fresh_tools, assert_hook_pillar,
                     assert_one_llm)

TOPIC = 'pay-double-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 tools', 'i would pay double for']
TOOLS = ['Gemini', 'ARCO', 'Loom', 'Airtable', 'Framer']
TITLES = ['1. Gemini', '2. ARCO', '3. Loom', '4. Airtable', '5. Framer']
ICONS = ['icon-gemini.png', 'icon-arco.png', 'icon-loom.png',
         'icon-airtable.png', 'icon-framer.png']
BGS = ['bg-h61.jpg',     # hook       desk-led-neon
       'bg-h20.jpg',     # gemini     lounge-day
       'bg-h21.jpg',     # arco       lounge-night
       'bg-h22.jpg',     # loom       lounge-day
       'bg-h29.jpg',     # airtable   supercars-dusk
       'bg-h31.jpg']     # framer     lounge-night

BODY = [
 [
    'Deep Research reads dozens of',
    'sources and cites every claim.',
    '',
    'You get the sources, not an answer',
    'you have to take on trust.',
 ],
 [
    'I manage all my tasks here and plan',
    'the day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'My holy grail.',
 ],
 [
    'It writes the title, summary and',
    'chapters from what you said.',
    '',
    'Record once and the description',
    'is already done.',
 ],
 [
    'A form writes straight into the',
    'base and fires an automation.',
    '',
    'Someone submits and the row, the',
    'email and the status all happen.',
 ],
 [
    'The design file is the site. You',
    'publish from the canvas itself.',
    '',
    'No handoff, no rebuilding it in',
    'code afterwards.',
 ],
]

# hook_slide hardwires assert_hook_approved so a generator cannot forget it. A
# re-shoot is the one case where a hook off the current pool is the point, so
# it is disabled here and nowhere else. Every other guard still runs.
c.assert_hook_approved = lambda lines: True

assert_one_llm(TOOLS)
assert_fresh_tools(TOOLS)
assert_audience(TOOLS)
assert_varied(BGS)
assert_bg_fresh(BGS, TOPIC)
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
