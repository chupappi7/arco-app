#!/usr/bin/env python3
"""screentime-100h: screentime pillar, seven slides.

Thinh asked for this one directly: the hook, three of the five reasons, the
CTA copy and a modern luxury penthouse behind the hook.

The hook is new to the pool. It is his wording, which is the approval — hooks
are added by hand on purpose — filed under screentime, which is what decides
the shape: numbered reasons through rule_slide, never a roster. app_slide
refuses on this pillar and it is right to.

He gave three reasons; a "5 reasons" hook owes five. Numbers 4 and 5 are
written to be the same kind of claim as his three: a thing that is true of the
phone, not a verdict about an app.

  1  the day has no plan          his
  2  the apps are not blocked     his
  3  a few minutes has no end     his
  4  the first unlock sets the day
  5  the number arrives weekly, the decision is hourly

Slide 7 is the closer he asked for: the icon, the full name, and what the app
does. It is the only slide in the post making a claim rather than teaching,
which is why it is cta_slide and not a sixth reason.

Backgrounds: the hook takes bg-h31, the darkest of the three lounge-night
frames at band luma 19.7, which is the penthouse-at-night look and the one
that holds a headline best. The rest avoid adjacent vibe repeats.
"""
import os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import hook_slide, rule_slide, cta_slide, mark_hook_used, record_post_bgs

TOPIC = 'screentime-100h'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 reasons your screen time', 'is still 100+ hours']
BGS = ['bg-h31.jpg', 'bg-h29.jpg', 'bg-h20.jpg',
       'bg-h88.jpg', 'bg-h34.jpg', 'bg-h32.jpg', 'bg-h22.jpg']

REASONS = [
    ('1. The day has no plan', [
        '- Nothing is written down, so the phone',
        '  becomes the plan by default.',
        '',
        '- A day with times on it leaves no gap for',
        '  the feed to fill.']),
    ('2. The apps are not blocked', [
        '- Deciding at the moment you reach for it is',
        '  the weakest point of the whole day.',
        '',
        '- A block set the night before never has to',
        '  be argued with.']),
    ('3. A few minutes has no end', [
        '- Nothing tells you the session is over, so',
        '  it ends when something interrupts it.',
        '',
        '- A block with an end time is the thing that',
        '  interrupts it.']),
    ('4. The first unlock sets the day', [
        '- Opening a feed before anything else trains',
        '  the next twelve hours to do the same.',
        '',
        '- What you open first is worth choosing while',
        '  you are not holding the phone.']),
    ('5. The number arrives weekly', [
        '- A Sunday report is a verdict on a week you',
        '  can no longer change.',
        '',
        '- The decision happens hourly, so the thing',
        '  that stops it has to be there hourly.']),
]

CTA = ['Day planner, app blocker and task',
       'manager in one app.',
       'The only productivity app you need.']

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
for i, (title, body) in enumerate(REASONS):
    rule_slide(BGS[i + 1], i + 1, title, body, f'{OUT}/0{i + 2}.jpg')
cta_slide(BGS[6], f'{OUT}/07.jpg', CTA)

mark_hook_used(HOOK, TOPIC)
record_post_bgs(TOPIC, BGS)
print('done')
