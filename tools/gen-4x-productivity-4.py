#!/usr/bin/env python3
"""4x-productivity-4: tools pillar. A replication of lock-in-anyway, which the
sync marked performing -- same shape kept (an approved two-line hook, five
tools, ARCO leading), everything that would read as the same post changed.

lock-in-anyway's own hook is a discipline hook, and assert_roster_allowed now
refuses a roster under a discipline pillar, so the replication moves to the
tools pillar and takes the longest-rested roster hook in the pool, "the tools
i used to / 4x my productivity" -- the reference render at 1359 views. Roster
is the one suggested for this build; the four teaching points are new and
none of them appears in any caption in hooks.json:

  Codex     headless run from one terminal command   (captions have parallel
            attempts, agents.md, cloud tasks, screenshots, pr review)
  Notion    a database template that repeats itself  (captions have button
            blocks, property automations, synced blocks, forms, rollups)
  Obsidian  today's note opens from your template    (captions have backlinks,
            unlinked mentions, markdown files, canvas, bases)
  CapCut    style one caption, apply to all of them  (captions have text to
            speech, motion tracking, auto reframe)

Backgrounds picked with the gen-daily-batch guards (hook-only vibes at index 0
only, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, no person) and
frozen here so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = '4x-productivity-4'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the tools i used to', '4x my productivity']
PILLAR = 'tools'
TOOLS = ['ARCO', 'Codex', 'Notion', 'Obsidian', 'CapCut']

# 01 hook      bg-h77  desk-led-neon    first hook outing
# 02 ARCO      bg-h29  supercars-dusk   band luma 18.7
# 03 Codex     bg-h24  lounge-night     band luma 49.8
# 04 Notion    bg-h50  desk-city-day    band luma 64.7, first outing anywhere
# 05 Obsidian  bg-h37  supercars-dusk   band luma 22.7
# 06 CapCut    bg-n04  villa-day        band luma 57.8
# Order set by reading the first render, not by the gate alone: the two frames
# whose copy band is brightest (h50, a daylight office, and n04, a pale villa
# facade) both hold white text but hold it worst, so they sit at 4 and 6 and
# the two darkest frames carry slides 2 and 3, which are the ones actually
# read. h48/h52 are the other clean desk-city-day frames and were left out
# rather than stacking a second near-identical daylight office into the same
# carousel, which is what the all-of-it-at-19 render showed going wrong.
BGS = ['bg-h77.jpg', 'bg-h29.jpg', 'bg-h24.jpg',
       'bg-h50.jpg', 'bg-h37.jpg', 'bg-n04.jpg']

# The twelve frames the two lock-in shoots used, plus the six from the last
# post, excluded from the walk.
SOURCE_BGS = ['bg-h36.jpg', 'bg-h49.jpg', 'bg-n03.jpg', 'bg-n06.jpg',
              'bg-h20.jpg', 'bg-h39.jpg',
              'bg-h65.jpg', 'bg-h22.jpg', 'bg-h35.jpg', 'bg-h46.jpg',
              'bg-n01.jpg', 'bg-n05.jpg']

# next_arco_angle('planning') has spent every v* angle, so it would reset the
# rotation and hand back v1 -- the single most repeated block of copy in the
# feed. v11 is a new angle in the approved register instead, rotating the
# feature to the timeline and Blocked Hours; it is pinned here and already
# marked used in arco_angles.json.
BODY = {
 'ARCO': [
    'Every task I have gets a time on',
    "the day's timeline, not a list.",
    '',
    'Blocked Hours shuts the feeds for',
    'those windows without me asking.',
    '',
    'My holy grail.',
 ],
 'Codex': [
    'It runs a whole task from one',
    'terminal command, with no chat.',
    '',
    'That line goes in a script, so the',
    'work is done before you sit down.',
 ],
 'Notion': [
    'A database template can repeat on',
    'its own and create the page for you.',
    '',
    'Monday opens with the review already',
    'there, checklist inside it.',
 ],
 'Obsidian': [
    "It opens today's note by itself,",
    'built from a template you wrote once.',
    '',
    'The day starts on the same three',
    'questions instead of a blank page.',
 ],
 'CapCut': [
    'Style one caption and apply it to',
    'every caption in the project.',
    '',
    'Every video keeps the same look',
    'without restyling a single word.',
 ],
}

assert set(BGS).isdisjoint(SOURCE_BGS), 'a lock-in frame leaked back in'
preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)

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
