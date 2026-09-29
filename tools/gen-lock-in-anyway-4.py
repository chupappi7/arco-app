#!/usr/bin/env python3
"""lock-in-anyway-4: discipline pillar, numbered rules under the lock-in hook.

The hook is the only one hook_rules.eligible(pillar='discipline') returned.
A discipline hook is answered by rule_slide steps, not a roster, so there is
no icon shelf. ARCO takes rule 1 on angle s1, drawn once by
next_arco_angle('discipline') and frozen here so a rebuild does not rotate
it. Rules 2-4 are ways to start when you do not feel like it; none repeats
lock-in-screens (five minutes counts, push not skip, break minutes back, the
week's bars), schedule-rules, discipline-timetable or any hooks.json caption.

Slide 6 is the closing card with Thinh's new CTA (2026-09-29): search
"arco focus" on the App Store, where it ranks #2. "here is why" kicker and the
outlined icon and badge per his 2026-09-23 note.

Backgrounds from the gen-daily-batch walk (_veiled_screens.pick_bgs), with
discipline-timetable's frames excluded so two discipline posts in a row do not
share a set. ARCO, the longest block, gets the darkest band. The walk gave
bg-h46 for rule 4; read back, its monitor wall sat under the copy, and every
other desk frame left did the same, so rule 4 moved to a villa and the card
to a dusk frame:

  01 hook     bg-n09  desk-led-neon
  02 ARCO     bg-h36  supercars-dusk     band luma 20.3
  03 rule 2   bg-h32  window-silhouette  band luma 38.8, the one person
  04 rule 3   bg-h88  supercars-dusk     band luma 28.2
  05 rule 4   bg-n04  villa-day          band luma 57.8
  06 card     bg-h37  supercars-dusk     veiled under the card
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (rule_slide, hook_slide, cta_slide, preflight,
                     mark_hook_used, record_post_tools, record_post_bgs)
from _veiled_screens import KICKER, CARD_OUTLINE, veiled

TOPIC = 'lock-in-anyway-4'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['this is how you lock in', "when you don't feel like it"]
TOOLS = ['ARCO']
BGS = ['bg-n09.jpg', 'bg-h36.jpg', 'bg-h32.jpg', 'bg-h88.jpg',
       'bg-n04.jpg', 'bg-h37.jpg']

RULES = [
 ('App Blocker & Focus: ARCO', [
    'Blocked Hours closes the apps on a',
    'schedule I set once.',
    '',
    '9am arrives and the feeds simply',
    'do not open.',
    '',
    'The one I would not delete.',
 ]),
 ('Open it, nothing else', [
    'The only job of the first minute is',
    'to open the file or the book.',
    '',
    'Once it is on the screen, carrying',
    'on is easier than closing it.',
 ]),
 ('Phone in another room', [
    'Leave the phone in a different room',
    'before the block starts.',
    '',
    'Checking it now takes a walk, and',
    'the walk is long enough to say no.',
 ]),
 ('Stop mid-sentence', [
    'End the session halfway through a',
    'sentence you know how to finish.',
    '',
    'Tomorrow starts by finishing it, so',
    'there is no blank page to face.',
 ]),
]

CTA = 'Planner and app blocker in one.'
# The search line is the call to action, so it goes in the bold ink `promo`
# slot rather than the grey subtitle.
SEARCH = ['Search “arco focus” on the App Store.']

preflight(TOPIC, TOOLS, BGS, pillar='discipline', hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', kicker=KICKER)
if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
    mark_hook_used(HOOK, TOPIC)

for i, (title, body) in enumerate(RULES):
    rule_slide(BGS[i + 1], i + 1, title, body, f'{OUT}/{i + 2:02d}.jpg')

cta_slide(None, f'{OUT}/06.jpg', subtitle=CTA, promo=SEARCH, badge=True, card=veiled(BGS[5]),
          style={'icon': 240, 'box': (96, 984, 520, 1400), 'name_size': 62,
                 'ink': (248, 248, 250), 'sub': (176, 176, 184), **CARD_OUTLINE})

if not any(e.get('topic') == TOPIC for e in c.tool_history()):
    record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
