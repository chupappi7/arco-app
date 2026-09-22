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
from compose import hook_slide, phone_slide, cta_slide

REPO = '/Users/thinh/SIXSIX/arco-app'
SHOTS = '/Users/thinh/Desktop/appstore screens'
OUT = f'{REPO}/drafts/under-an-hour'
os.makedirs(OUT, exist_ok=True)

SIM = 'Simulator Screenshot - iPhone 17 Pro - 2026-09-21 at'

hook_slide('bg-h35.jpg',
           ['i cut 3 hours of screen time', 'without deleting a single app'],
           f'{OUT}/01.jpg')

# crop_top clears the status bar without eating the page title.
SLIDES = [
    ('Screenshot 2026-09-21 at 2.35.22.png', 60, None,
     'This was the week that started it.',
     '57 hours. 24 of them on TikTok alone.'),
    (f'{SIM} 02.48.07.png', 150, '1',
     'Plan tomorrow the night before.',
     'A day with no gaps has nowhere to scroll.'),
    (f'{SIM} 03.09.49.png', 150, '2',
     'Every hour already has a job.',
     'You do not reach for it when you know what is next.'),
    ('IMG_4283.PNG', 120, '3',
     'The apps lock while you work.',
     'Thirty minutes at a time. TikTok and Instagram, gone.'),
    ('Screenshot 2026-09-21 at 2.37.56.png', 40, '4',
     'Try anyway and it asks why.',
     'That one question ends most of the attempts.'),
    (f'{SIM} 02.52.56.png', 150, '5',
     'Chase the other number instead.',
     '14 hours focused this week. 20 days straight reading.'),
]

# Bright frames only — black type needs a light picture under it.
BGS = ['bg-n02.jpg', 'bg-h48.jpg', 'bg-h52.jpg',
       'bg-n03.jpg', 'bg-h50.jpg', 'bg-h51.jpg']

for i, ((src, crop, num, title, body), bg) in enumerate(zip(SLIDES, BGS), 2):
    phone_slide(bg, f'{SHOTS}/{src}', crop, num, title, body, f'{OUT}/{i:02d}.jpg')

cta_slide('bg-h34.jpg', f'{OUT}/08.jpg',
          subtitle=['plan the day, block the rest.',
                    'the plan does the work — the block holds the line.'],
          badge=True)
