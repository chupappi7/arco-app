#!/usr/bin/env python3
"""five-hours-deep-work: build pillar, ARCO's own screens as the whole post.

  hook      "5 hours of deep work a day / this is the whole setup", written 2026-11-14 at Thinh's request
            ("post more posts where its showing arco ui ... with new hooks"),
            added to hook_pool.json with origin 'claude'.
  why       Thinh, 2026-11-14: more eyes on the UI, which turns into
            downloads. Added on top of frequency test week 1 (2026-11-19),
            not swapped for a tools post.
  screens   the 7 Oct captures in design/control-center; every line was
            checked against pivot-timer (shield copy in ShieldConfiguration-
            Extension, Today timeline, widget Start intent, Insights groups).
  design    big-screen: no photograph behind the handset, the screenshot is
            the argument.

Usage: python3 tools/gen-five-hours-deep-work.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, HABITS, SHIELD_NOW, TIMELINE, TODAY_NOW)
from _tools_screens import PROMO_COMMENT

build(
    topic='five-hours-deep-work',
    hook=['5 hours of deep work a day', 'this is the whole setup'],
    kicker='here is why',
    bgs=['bg-h51.jpg', 'bg-n03.jpg', 'bg-h32.jpg', 'bg-h35.jpg', 'bg-h21.jpg', 'bg-h05.jpg'],
    slides=[
        (TODAY_NOW, '1', 'Deep work gets a play button.',
         'Tap play on a timed block and its timer runs. The minutes go to that habit’s total for the day.'),
        (HABITS, '2', 'Hours, not checkmarks.',
         'The chart widget shows hours per day for the week and the change on last week, like 20h 15m, up 25%.'),
        (TIMELINE, '3', 'The next block is on the home screen.',
         'The timeline widget shows what is done and what starts next, so the phone opens on the plan.'),
        (SHIELD_NOW, '4', 'The apps close with it.',
         'During the block, TikTok and Instagram open to a shield instead of the feed.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='build',
    promo=PROMO_COMMENT,
    design='big-screen',
    only=[int(a) for a in sys.argv[1:]] or None,
)
