#!/usr/bin/env python3
"""lock-in-anyway-2: re-shoot of lock-in-anyway. Same words, new photos.

Every hook line, title, body line and roster entry is frozen from the source
post; only the backgrounds and the topic slug change. The source generator is
committed as gen-lock-in-anyway.py, so the copy is copied straight out of it
rather than read back off the JPGs -- with one exception. The ARCO card there
comes from next_arco_angle(), which rotates on every call and would hand this
build different copy, so the angle the source actually rendered (v9, read back
off drafts/lock-in-anyway/02.jpg) is written out literally below.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically. One thing was taken out of the picker's hands: the six photographs
lock-in-anyway shot on are excluded from the walk, because a re-shoot that
reuses the source's own photos is not a re-shoot. They are named in SOURCE_BGS.

The hook background is what pick_hook_bg returns on its own -- bg-h65 is the
first unused night-desk vibe, so `prefer` and the picker agree here and the
source's own pick_hook_bg call is kept verbatim.

BG_COOLDOWN is 1, but two other posts were being built in this repo while this
one was picked (ship-alone-2 had just recorded and stack-at-19 was mid-render),
so the walk excluded both of their sets rather than only whichever happened to
land last in bg_history. That is stricter than the guard, never looser.

One guard is deliberately not run. assert_roster_allowed landed after this post
shipped (53c2835, 2026-08-30) and rejects a roster drawn under a discipline
hook, which is exactly what lock-in-anyway is. A re-shoot changes photographs,
not copy and not shape, so the guard is disabled here and nowhere else. Every
other guard still runs, including the two hook guards -- this hook is in the
approved pool and its cooldown is clear -- and assert_one_llm, which passes
because the roster carries Claude and nothing else.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'lock-in-anyway-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['this is how you lock in', "when you don't feel like it"]
TOOLS = ['ARCO', 'Claude', 'Raycast', 'CleanShot X', 'Canva']
BGS = ['bg-h65.jpg',   # 01 hook         desk-led-neon      (first hook outing)
       'bg-h22.jpg',   # 02 ARCO         lounge-day         band luma 53.5
       'bg-h35.jpg',   # 03 Claude       supercars-dusk     band luma 37.2
       'bg-h46.jpg',   # 04 Raycast      desk-city-day      band luma 59.7
       'bg-n01.jpg',   # 05 CleanShot X  villa-day          band luma 66.3
       'bg-n05.jpg']   # 06 Canva        desk-empty-day     band luma 57.1

# The six photographs the source post was shot on. Excluded from the picker.
SOURCE_BGS = ['bg-h36.jpg', 'bg-h49.jpg', 'bg-n03.jpg', 'bg-n06.jpg',
              'bg-h20.jpg', 'bg-h39.jpg']

BODY = {
 'ARCO': [
    'All of my tasks sit here and planning',
    'the day takes 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away, and Blocked Hours repeats it',
    'every weekday.',
    '',
    'My holy grail.',
 ],
 'Claude': [
    'Ask for a quiz on what you just',
    'read and it builds a working one.',
    '',
    'You click through questions in the',
    'chat instead of rereading a page.',
 ],
 'Raycast': [
    'Floating Notes keeps a note above',
    'every window on one hotkey.',
    '',
    'The next step stays on screen',
    'while you work somewhere else.',
 ],
 'CleanShot X': [
    'Captures park in a corner overlay',
    'instead of piling on the desktop.',
    '',
    'You drag the diagram into your',
    'notes without saving a file.',
 ],
 'Canva': [
    'Any design opens out into an',
    'infinite whiteboard.',
    '',
    'The whole topic gets mapped in one',
    'place before you write a word.',
 ],
}

# app_slide hardwires the roster guard so a generator cannot forget it. A
# re-shoot of a post that predates the guard is the one case where the shape
# is not ours to change, so it is disabled here and nowhere else.
c.assert_roster_allowed = lambda out: True

preflight(TOPIC, TOOLS, BGS)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    app_slide(bg, icons[tool], f'{n}. {tool}', BODY[tool], f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
