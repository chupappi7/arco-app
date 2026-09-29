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

Fix pass (2026-09-29), Thinh's note on the first render: "remove the numbers
and the squares, look at how screentime does it". Slides 02-05 drop the
numbered badge and take the screentime-100h treatment, the title itself in
yellow. The titles never carried an "N." so no number is left anywhere.
Slides 01 and 06 had neither and are untouched.

Second fix pass (2026-09-29), Thinh: "do it like screentime posts use
screenshots, same style of text". Slides 02-05 move from rule_slide to the
screens treatment (_veiled_screens): a real ARCO screen in a handset on the
veiled photo, the number and title and one paragraph beside it in STYLE. Each
rule is tied to the screen it touches — Control Center for Blocked Hours,
Today's play button, the shield's "what does this add to your day?", Plan your
day for tomorrow's first block. The ARCO verdict line ("the one I would not
delete") is dropped. Same backgrounds, so no vibe changes. Rendered with
`--only 2 3 4 5`; 01 and 06 were not re-rendered.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (hook_slide, cta_slide, phone_slide, preflight,
                     assert_teaches, mark_hook_used, record_post_tools,
                     record_post_bgs)
from _veiled_screens import (KICKER, CARD_OUTLINE, STYLE, SHOTS, veiled,
                             CONTROL, TODAY, SHIELD, PLAN_DAY)

# `--only 2 3` re-renders just those slides and leaves the rest, and the hook
# and background histories, untouched.
ONLY = {int(a) for a in sys.argv[sys.argv.index('--only') + 1:]} if '--only' in sys.argv else None
want = (lambda n: ONLY is None or n in ONLY)

TOPIC = 'lock-in-anyway-4'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['this is how you lock in', "when you don't feel like it"]
TOOLS = ['ARCO']
BGS = ['bg-n09.jpg', 'bg-h36.jpg', 'bg-h32.jpg', 'bg-h88.jpg',
       'bg-n04.jpg', 'bg-h37.jpg']

SLIDES = [
 (CONTROL, '1', 'Set the block once.',
  'Blocked Hours closes the apps on a schedule you set once. At 9am the '
  'feeds simply do not open.'),
 (TODAY, '2', 'Open it, nothing else.',
  'The only job of the first minute is to tap play on the block. Once the '
  'timer runs, carrying on is easier than stopping it.'),
 (SHIELD, '3', 'Phone in another room.',
  'Leave it there before the block starts. Walk back for it anyway and the '
  'blocked app opens on a screen asking what it adds to your day.'),
 (PLAN_DAY, '4', 'Stop mid-sentence.',
  'End halfway through a sentence you know how to finish, and place '
  'finishing it as tomorrow\'s first block. No blank page to face.'),
]

CTA = 'Planner and app blocker in one.'
# The search line is the call to action, so it goes in the bold ink `promo`
# slot rather than the grey subtitle.
SEARCH = ['Search “arco focus” on the App Store.']

preflight(TOPIC, TOOLS, BGS, pillar='discipline', hook=HOOK)
for b in BGS[1:]:
    if c.copy_band_luma(b) > c.BAND_MAX_LUMA:
        raise SystemExit(f'{b}: copy band too bright')
for (_, _, title, body) in SLIDES:
    assert_teaches(title, [body])

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

if want(1):
    hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', kicker=KICKER)
if ONLY is None and not any(e.get('topic') == TOPIC for e in hook_rules.history()):
    mark_hook_used(HOOK, TOPIC)

for i, ((src, crop), num, title, body) in enumerate(SLIDES, 2):
    if want(i):
        phone_slide(veiled(BGS[i - 1]), f'{SHOTS}/{src}', crop, num, title, body,
                    f'{OUT}/{i:02d}.jpg', style=STYLE)

if want(6):
    cta_slide(None, f'{OUT}/06.jpg', subtitle=CTA, promo=SEARCH, badge=True, card=veiled(BGS[5]),
              style={'icon': 240, 'box': (96, 984, 520, 1400), 'name_size': 62,
                     'ink': (248, 248, 250), 'sub': (176, 176, 184), **CARD_OUTLINE})

if ONLY is not None:
    sys.exit()
if not any(e.get('topic') == TOPIC for e in c.tool_history()):
    record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
