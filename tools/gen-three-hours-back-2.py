#!/usr/bin/env python3
"""three-hours-back-2: screentime pillar, told on real screens.

Rebuilt (2026-09-23) in the under-an-hour concept on Thinh's note: "redo all
with the new concept of screentime we did so use the screenshots". The hook
slide is unchanged: that concept's hook is the same hook_slide over a photo.
Every slide after it is an ARCO screen in a handset on the dark fade, with the
step beside it, and the post closes on the icon card with the store badge.

The hook promises hours back WITHOUT deleting anything, so every step keeps
the apps installed: they lock on a schedule, a focus session shuts them, the
day is placed before it starts, and Insights show where the hours went
instead. Two of the four screens (Plan your day, Insights good habits) are
not in under-an-hour, and none of its copy is reused.

The first version (ARCO plus four stock iOS steps on photographs) is in git
history at 0ece2e7.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (hook_slide, phone_slide, cta_slide, linear_ground,
                     preflight, assert_teaches, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'three-hours-back-2'
OUT = f'{c.REPO}/drafts/{TOPIC}'
SHOTS = '/Users/thinh/Desktop/appstore screens'
SIM = 'Simulator Screenshot - iPhone 17 Pro - 2026-09-21 at'
os.makedirs(OUT, exist_ok=True)

HOOK = ['i cut 3 hours of screen time', 'without deleting a single app']
HOOK_BG = 'bg-h71.jpg'   # desk-led-neon: night-desk, hook only

if not any(h['lines'] == HOOK for h in hook_rules.eligible(TOPIC, 'screentime')):
    raise SystemExit(f'hook not eligible: {HOOK}')
preflight(TOPIC, ['ARCO'], [HOOK_BG], pillar='screentime', hook=HOOK)

# crop_top clears the status bar without eating the page title.
SLIDES = [
    ('Screenshot 2026-09-21 at 2.37.56.png', 40, '1',
     'The apps stay. They just lock.',
     'Blocked hours shut the feeds on a schedule set once. Nothing is '
     'deleted, it just will not open.'),
    ('IMG_4283.PNG', 120, '2',
     'A focus session shuts the rest.',
     'Start the timer and TikTok and Instagram stay locked until it ends.'),
    (f'{SIM} 02.48.07.png', 150, '3',
     'Every hour gets a job first.',
     'Plan your day puts tasks and habits on the timeline, so no hour is '
     'left empty for the feed.'),
    (f'{SIM} 02.52.56.png', 150, '4',
     'The hours show up as work.',
     'Insights count focus time by the week, so you see where the '
     'hours went instead.'),
]
for _, _, _, title, body in SLIDES:
    assert_teaches(title, [body])

GROUND = linear_ground((26, 28, 33), (9, 9, 11))
# The copy sits on the fade, not a photo; hold it to the same band ceiling.
if c.band_luma(GROUND, 600, 1300) > c.BAND_MAX_LUMA:
    raise SystemExit('ground too bright for the copy band')
STYLE = {'side': 'right', 'col_x': 72, 'col_w': 392, 'col_y': 665,
         'title_face': 'Semi Condensed Heavy', 'body_face': 'Semi Condensed Medium',
         'app_face': 'Semi Condensed Bold',
         'title_size': 62, 'body_size': 35, 'app_size': 28, 'lead': 1.05,
         'ink': (248, 248, 250), 'sub': (166, 166, 174),
         'eyebrow': (248, 248, 250)}

hook_slide(HOOK_BG, HOOK, f'{OUT}/01.jpg')
if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
    mark_hook_used(HOOK, TOPIC)

for i, (src, crop, num, title, body) in enumerate(SLIDES, 2):
    phone_slide(GROUND, f'{SHOTS}/{src}', crop, num, title, body,
                f'{OUT}/{i:02d}.jpg', style=STYLE)

# Flat card on the same fade: the hook's night desk is hook-only, and the
# closer belongs to the set of screens rather than to a new photograph.
cta_slide(None, f'{OUT}/06.jpg',
          subtitle=['Lock the apps without deleting them.',
                    'Plan the day so there is nothing to scroll into.'],
          badge=True, card=GROUND,
          style={'icon': 240, 'box': (96, 984, 520, 1400), 'name_size': 62,
                 'ink': (248, 248, 250), 'sub': (166, 166, 174)})

if not any(e.get('topic') == TOPIC for e in c.tool_history()):
    record_post_tools(TOPIC, ['ARCO'])
record_post_bgs(TOPIC, [HOOK_BG])
print('done')
