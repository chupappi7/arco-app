#!/usr/bin/env python3
"""plan-in-60-seconds: discipline pillar, ARCO's own screens as the whole post.

  hook      "i plan my whole day in 60 seconds / every morning, like this", written 2026-11-14 at Thinh's request
            ("post more posts where its showing arco ui ... with new hooks"),
            added to hook_pool.json with origin 'claude'.
  why       Thinh, 2026-11-14: more eyes on the UI, which turns into
            downloads. Added on top of frequency test week 1 (2026-11-18),
            not swapped for a tools post.
  screens   the 7 Oct captures in design/control-center; every line was
            checked against pivot-timer (shield copy in ShieldConfiguration-
            Extension, Today timeline, widget Start intent, Insights groups).
  design    big-screen: no photograph behind the handset, the screenshot is
            the argument.

Usage: python3 tools/gen-plan-in-60-seconds.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, SHIELD_NOW, TASKS, TODAY_NOW, WIDGETS)
from _tools_screens import PROMO_COMMENT

build(
    topic='plan-in-60-seconds',
    hook=['i plan my whole day in 60 seconds', 'every morning, like this'],
    kicker='here is why',
    bgs=['bg-h33.jpg', 'bg-h48.jpg', 'bg-h37.jpg', 'bg-n01.jpg', 'bg-h04.jpg', 'bg-h31.jpg'],
    slides=[
        (TODAY_NOW, '1', 'Start with what’s waiting.',
         'Plan your day sits at the top of Today with a count of tasks that have no time yet. Give each one a slot.'),
        (TASKS, '2', 'Priorities are flags.',
         'Red, orange or blue: the flag on each task decides what gets the morning slot and what waits.'),
        (WIDGETS, '3', 'Every kept day fills a square.',
         'Habit widgets fill a day for each one you kept, so a missed morning shows on the home screen.'),
        (SHIELD_NOW, '4', 'Then the apps close.',
         'Once a focus block starts, distracting apps open to a shield and one button: Lock back in.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='discipline',
    promo=PROMO_COMMENT,
    design='big-screen',
    only=[int(a) for a in sys.argv[1:]] or None,
)
