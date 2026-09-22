#!/usr/bin/env python3
"""screentime post: 8 hours a day down to under one, told on real screens.

Other posts put words over a stock photo. This one uses the app itself — the
number that started it, then one screen per reason, each in a handset with the
argument beside it. On a screen-time account the proof and the pitch are the
same picture, which is the whole reason to shoot it this way.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (hook_slide, phone_slide, cta_slide, linear_ground,
                     base_photo, adaptive_scrim)

REPO = '/Users/thinh/SIXSIX/arco-app'
SHOTS = '/Users/thinh/Desktop/appstore screens'
OUT = f'{REPO}/drafts/under-an-hour'
os.makedirs(OUT, exist_ok=True)

SIM = 'Simulator Screenshot - iPhone 17 Pro - 2026-09-21 at'

hook_slide('bg-h35.jpg',
           ['4 things that cut my screen time', 'not one of them is willpower'],
           f'{OUT}/01.jpg')

# crop_top clears the status bar without eating the page title.
SLIDES = [
    ('Screenshot 2026-09-21 at 2.37.56.png', 40, '1',
     'The apps lock on a schedule.',
     'Blocked hours run themselves. The feed does not open during them.'),
    (f'{SIM} 03.09.49.png', 150, '2',
     'A planned day keeps me on the work.',
     'Without a plan I scroll all day. With one, every hour already has a job.'),
    ('Screenshot 2026-09-21 at 2.35.22.png', 60, '3',
     'I can see where the hours went.',
     '57 in a week. 24 of them on TikTok. Seeing it is what made me change it.'),
    ('IMG_4283.PNG', 120, '4',
     'Focus mode and the distractions are gone.',
     'When I need to lock in, one session takes TikTok and Instagram away.'),
]

# A dark fade, not a photograph: a picture behind a product shot is two
# subjects competing, and the handset's metal edge has nothing to catch
# against on a light ground.
GROUND = linear_ground((26, 28, 33), (9, 9, 11))
BGS = [GROUND] * len(SLIDES)

# Copy on the left, handset on the right, on a flat ground. Semi Condensed
# Heavy cuts harder at thumbnail size than SF Bold does, and the column sits
# above the phone's midline rather than on it.
STYLE = {'side': 'right', 'col_x': 72, 'col_w': 392, 'col_y': 665,
         'title_face': 'Semi Condensed Heavy', 'body_face': 'Semi Condensed Medium',
         'app_face': 'Semi Condensed Bold',
         'title_size': 62, 'body_size': 35, 'app_size': 28, 'lead': 1.05,
         'ink': (248, 248, 250), 'sub': (166, 166, 174),
         'eyebrow': (248, 248, 250)}

for i, ((src, crop, num, title, body), bg) in enumerate(zip(SLIDES, BGS), 2):
    phone_slide(bg, f'{SHOTS}/{src}', crop, num, title, body,
                f'{OUT}/{i:02d}.jpg', style=STYLE)

# The closing card goes back to the hook's photograph: the villa and the two
# cars. The card sits in the sky, where the hook copy sat, with the sky
# scrimmed from the top edge down so there is no seam, and the cars are
# left clear beneath the badge. The post closes on the picture it opened on.
CTA_BG = base_photo('bg-h35.jpg', (1.0, 1.0, 0, 1))
adaptive_scrim(CTA_BG, 0, 940, target=60, strength_cap=0.62)

cta_slide(None, f'{OUT}/06.jpg',
          subtitle=['Plan the day, block the rest.',
                    'The plan does the work. The block holds the line.'],
          badge=True, card=CTA_BG,
          style={'icon': 240, 'box': (96, 984, 130, 960), 'name_size': 62,
                 'ink': (248, 248, 250), 'sub': (166, 166, 174),
                 'badge_gap': 40})
