#!/usr/bin/env python3
"""day-on-one-screen: discipline pillar, ARCO's own screens as the whole post.

  hook      "my whole day fits on one screen / this is how i run it", written 2026-11-14 at Thinh's request
            ("post more posts where its showing arco ui ... with new hooks"),
            added to hook_pool.json with origin 'claude'.
  why       Thinh, 2026-11-14: more eyes on the UI, which turns into
            downloads. Added on top of frequency test week 1 (2026-11-17),
            not swapped for a tools post.
  screens   the 7 Oct captures in design/control-center; every line was
            checked against pivot-timer (shield copy in ShieldConfiguration-
            Extension, Today timeline, widget Start intent, Insights groups).
  design    big-screen: no photograph behind the handset, the screenshot is
            the argument.

Usage: python3 tools/gen-day-on-one-screen.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, SHIELD_NOW, TASKS, TIMELINE, TODAY_NOW)
from _tools_screens import PROMO_COMMENT

build(
    topic='day-on-one-screen',
    hook=['my whole day fits on one screen', 'this is how i run it'],
    kicker='here is why',
    bgs=['bg-h52.jpg', 'bg-h19.jpg', 'bg-n06.jpg', 'bg-h01.jpg', 'bg-h50.jpg', 'bg-h45.jpg'],
    slides=[
        (TODAY_NOW, '1', 'The day is drawn to scale.',
         'Each block takes the space its hours take, with a red line for now, so a gap in the plan shows at a glance.'),
        (TIMELINE, '2', 'The plan sits on the home screen.',
         'The timeline widget lists today’s blocks and ticks off the done ones, without opening the app.'),
        (TASKS, '3', 'Late tasks say so.',
         'The tasks widget colours each one by project and flags what is overdue, like 1D LATE in red.'),
        (SHIELD_NOW, '4', 'A block you can’t scroll through.',
         'Inside a focus block, Instagram and TikTok open to a shield instead of the feed.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='discipline',
    promo=PROMO_COMMENT,
    design='big-screen',
    only=[int(a) for a in sys.argv[1:]] or None,
)
