#!/usr/bin/env python3
"""discipline-timetable: discipline pillar, numbered rules under the schedule hook.

The hook says discipline is a SCHEDULE, so every rule is a scheduling
mechanic, as on schedule-rules. None repeats that post's rules (night before,
two fixed hours, end time, recurring slot), schedule-not-personality's
screens (wake alarm, Plan your day, best day, early-end wait) or a hooks.json
caption.

A discipline hook is answered by rule_slide steps, not a roster, so there is
no icon shelf: the only product in the post is ARCO, which takes rule 1 with
a numbered badge like every other slide. Its copy is ARCO angle s2, drawn
once by next_arco_angle('discipline') and frozen here so a rebuild does not
rotate it. "here is why" kicker per Thinh's 2026-09-23 note.

Backgrounds picked with the gen-daily-batch walk (pick_hook_bg for the hook,
which prefers an unused night desk frame; hook-only vibes off app slides, copy
band under BAND_MAX_LUMA, no adjacent vibe, at most one person, clear of the
last post) and ordered by copy band luma, darkest first, so the ARCO card, the
longest block at seven lines, gets the darkest band:

  01 hook      bg-h80  desk-led-neon
  02 ARCO      bg-h29  supercars-dusk  band luma 18.7
  03 rule 2    bg-h24  lounge-night    band luma 49.8
  04 rule 3    bg-h22  lounge-day      band luma 53.5
  05 rule 4    bg-h21  lounge-night    band luma 64.6
  06 rule 5    bg-h20  lounge-day      band luma 67.0
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (rule_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)
from _veiled_screens import KICKER

TOPIC = 'discipline-timetable'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['discipline', 'is a schedule, not a personality']
TOOLS = ['ARCO']
BGS = ['bg-h80.jpg', 'bg-h29.jpg', 'bg-h24.jpg', 'bg-h22.jpg',
       'bg-h21.jpg', 'bg-h20.jpg']

RULES = [
 ('ARCO', [
    'The block runs on a timetable, not',
    'on willpower.',
    '',
    'There is no decision left to make',
    'when the hour starts.',
    '',
    'My holy grail.',
 ]),
 ('Hardest task, first slot', [
    'Put the task you would avoid in the',
    'first block of the day.',
    '',
    'It is done before the excuses have',
    'had a chance to show up.',
 ]),
 ('Plan six hours, not eight', [
    'Leave a quarter of the day with',
    'nothing booked in it.',
    '',
    'A task that runs long eats the gap,',
    'not the block that comes after it.',
 ]),
 ('Move a missed slot', [
    'When a block slips, drag the task',
    'to the next open slot that day.',
    '',
    'One bad hour costs one hour, not',
    'the rest of the plan.',
 ]),
 ('Bedtime is the first block', [
    'Put the time you go to sleep on the',
    'plan before any task.',
    '',
    'A fixed bedtime is what makes a',
    'fixed start the next day possible.',
 ]),
]

preflight(TOPIC, TOOLS, BGS, pillar='discipline', hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', kicker=KICKER)
mark_hook_used(HOOK, TOPIC)

for i, (title, body) in enumerate(RULES):
    rule_slide(BGS[i + 1], i + 1, title, body, f'{OUT}/{i + 2:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
