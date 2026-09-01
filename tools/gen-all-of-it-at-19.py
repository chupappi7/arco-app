#!/usr/bin/env python3
"""all-of-it-at-19: build pillar. A replication of lock-in-anyway, which the
sync marked performing — same shape (approved two-line hook, five tools, ARCO
leading), everything else new.

Changed so it does not read as the same post twice: a different approved hook
("everything i run my business on / at 19", rested 22 posts, the longest of
any eligible tools/build hook), a different roster, six backgrounds none of
which the two lock-in shoots used, and five teaching points that appear in no
caption in hooks.json.

Backgrounds picked with the gen-daily-batch guards (hook-only vibes at index 0
only, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, no person) and
then frozen here so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, assert_one_llm,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'all-of-it-at-19'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['everything i run my business on', 'at 19']
PILLAR = 'build'
TOOLS = ['ARCO', 'Codex', 'Notion', 'Obsidian', 'CapCut']

# 01 hook      bg-h74  desk-led-neon    first hook outing
# 02 ARCO      bg-h31  lounge-night     band luma 19.7
# 03 Codex     bg-h34  desk-empty-day   band luma 62.4
# 04 Notion    bg-h38  supercars-dusk   band luma 21.2
# 05 Obsidian  bg-h51  desk-city-day    band luma 61.7
# 06 CapCut    bg-h21  lounge-night     band luma 64.6
# h50 and h52 are the other clean desk-city-day frames and were both dropped
# after reading the first render: h50/51/52 are near-identical daylight
# offices, and on h52 the copy lands straight across three white monitors,
# which swallows the leading dashes even though the band clears the luma gate.
# The pool has no other dark app frame outside the cooldown, so the two
# lounge-night photographs carry slides 2 and 6 -- h31 is a warm interior and
# h21 faces the city, so they do not read as the same room. h51 is the one
# daylight frame left in the set and sits at slide 5, where the copy is doing
# the least work, rather than at 3 behind the ARCO card.
BGS = ['bg-h74.jpg', 'bg-h31.jpg', 'bg-h34.jpg',
       'bg-h38.jpg', 'bg-h51.jpg', 'bg-h21.jpg']

# The twelve frames the two lock-in shoots used, excluded from the walk.
SOURCE_BGS = ['bg-h36.jpg', 'bg-h49.jpg', 'bg-n03.jpg', 'bg-n06.jpg',
              'bg-h20.jpg', 'bg-h39.jpg',
              'bg-h65.jpg', 'bg-h22.jpg', 'bg-h35.jpg', 'bg-h46.jpg',
              'bg-n01.jpg', 'bg-n05.jpg']

# next_arco_angle('business') returns v9 on this state, which is the angle
# both lock-in shoots rendered -- replicating a post is not repeating its ARCO
# card. v10 is the one slot the rotation had never spent, so it is pinned here
# and marked used in arco_angles.json.
BODY = {
 'ARCO': [
    'I manage all my tasks here and plan',
    'the day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'The one I actually open every day.',
 ],
 'Codex': [
    'Ask for several attempts and it runs',
    'the same task in parallel.',
    '',
    'You compare finished diffs and pick',
    'one, instead of prompting again.',
 ],
 'Notion': [
    'A button block creates a page from a',
    'template with the fields filled in.',
    '',
    'Logging a client or a bug is one tap,',
    'not a blank page every time.',
 ],
 'Obsidian': [
    'Every note lists the pages that',
    'mention it without linking to it.',
    '',
    'Old notes reconnect as you write,',
    'instead of sinking into a folder.',
 ],
 'CapCut': [
    'Auto reframe recuts a wide video to',
    'vertical and follows the subject.',
    '',
    'One edit becomes the youtube and the',
    'tiktok version, not two exports.',
 ],
}

assert set(BGS).isdisjoint(SOURCE_BGS), 'a lock-in frame leaked back in'
preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
# preflight only runs the LLM guard on the tools pillar, and this is a build
# post, so ask for it by name.
assert_one_llm(TOOLS)

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
