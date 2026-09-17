#!/usr/bin/env python3
"""study-four-hours-2: learn pillar, method post. Second outing of the hook.

The hook is a learn hook, so the post answers it with numbered steps through
rule_slide, never a roster: app_slide refuses under this pillar
(assert_roster_allowed) and it is right to. The first outing
(study-four-hours) went out as a five-app listicle before that rule existed.

Every step is a thing that keeps the phone out of a four hour session. ARCO
leads at 1 and its copy comes from the study-tagged angles so the slide
answers this hook: the block that closes the apps, not planning the day in
30 seconds. The other four are what the phone usually gets picked up FOR
(the clock, the kitchen, a reply, the break) and what replaces each one.

Rule slides follow Thinh's screentime-100h note: no numbered squares, the
number lives in the title and the title carries the highlight. No icon shelf
on the hook: there is no roster, and a lone ARCO icon would mark the post as
the advert.

Backgrounds picked with the gen-daily-batch walk (hook-only vibes skipped
on rule slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at
most one person, nothing from the previous post) and frozen so the post
rebuilds identically. bg-h51 was the only hook background left unused in
the rotation. ARCO's card is the longest block in the post, so it takes the
darkest frame.

The ARCO angle (f1) was drawn once with next_arco_angle('study') and is
written out literally here so a rebuild does not rotate it.

rebuild: python3 tools/gen-study-four-hours-2.py
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (rule_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'study-four-hours-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['how i study 4 hours', 'without touching my phone']
BGS = ['bg-h51.jpg',   # hook   desk-city-day
       'bg-h31.jpg',   # 1 ARCO lounge-night, band luma 19.7
       'bg-h37.jpg',   # 2      supercars-dusk
       'bg-n04.jpg',   # 3      villa-day
       'bg-h45.jpg',   # 4      window-silhouette (the one person)
       'bg-h22.jpg']   # 5      lounge-day

# next_arco_angle('study') -> f1
ARCO = [
    'Focus mode blocks every app on my',
    'list for the whole session.',
    '',
    'The phone stops being a decision',
    'while the timer runs.',
    '',
    'My holy grail.',
]

STEPS = [
    ('1. ARCO', ARCO),
    ('2. Everything on the desk first', [
        'Water, charger, calculator and the',
        'textbook are out before you sit.',
        '',
        'Every trip to the kitchen is where',
        'the phone gets picked up.',
    ]),
    ('3. A sheet for stray thoughts', [
        'A reply to send or a thing to look',
        'up goes on paper, not on the phone.',
        '',
        'The thought is parked, and the list',
        'gets dealt with at the break.',
    ]),
    ('4. The block ends on a result', [
        'Four hours is the container, a',
        'finished past paper is the finish.',
        '',
        'You stop checking how long is left,',
        'and the clock lives on the phone.',
    ]),
    ('5. Break away from the desk', [
        'Ten minutes every fifty, and the',
        'break is a walk, water, a window.',
        '',
        'A feed break resets attention to',
        'zero. A walk keeps the thread.',
    ]),
]

preflight(TOPIC, ['ARCO'], BGS, pillar='learn', hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
# A rebuild must not append a second history entry for the same outing.
if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
    mark_hook_used(HOOK, TOPIC)

for i, (title, body) in enumerate(STEPS):
    rule_slide(BGS[i + 1], i + 1, title, body, f'{OUT}/{i + 2:02d}.jpg',
               badge=False, title_fill=c.YELLOW)

record_post_tools(TOPIC, ['ARCO'])
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
