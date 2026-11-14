#!/usr/bin/env python3
"""screen-time-under-3: screentime pillar, ARCO's own screens as the whole post.

  hook      "8 hours of screen time to under 3 / this is my phone now", written 2026-11-14 at Thinh's request
            ("post more posts where its showing arco ui ... with new hooks"),
            added to hook_pool.json with origin 'claude'.
  why       Thinh, 2026-11-14: more eyes on the UI, which turns into
            downloads. Added on top of frequency test week 1 (2026-11-20),
            not swapped for a tools post.
  screens   the 7 Oct captures in design/control-center; every line was
            checked against pivot-timer (shield copy in ShieldConfiguration-
            Extension, Today timeline, widget Start intent, Insights groups).
  design    big-screen: no photograph behind the handset, the screenshot is
            the argument.

Usage: python3 tools/gen-screen-time-under-3.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, INSIGHTS_NOW, SHIELD_NOW, TIMELINE, TODAY_NOW)
from _tools_screens import PROMO_COMMENT

build(
    topic='screen-time-under-3',
    hook=['8 hours of screen time to under 3', 'this is my phone now'],
    kicker='here is why',
    bgs=['bg-h34.jpg', 'bg-h39.jpg', 'bg-h46.jpg', 'bg-h29.jpg', 'bg-h24.jpg', 'bg-h88.jpg'],
    slides=[
        (INSIGHTS_NOW, '1', 'First, see where it goes.',
         'Insights splits the week into distracting, entertainment and everyday, with the hours for each app.'),
        (SHIELD_NOW, '2', 'The feed opens to a question.',
         'During focus, a blocked app asks what it adds to your day. Lock back in is the big button.'),
        (TIMELINE, '3', 'The plan gets the first look.',
         'The timeline widget puts today’s blocks on the home screen, ticked off as they get done.'),
        (TODAY_NOW, '4', 'Every hour has a job.',
         'Today lays tasks and habits on one timeline, so free time is planned before the phone fills it.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='screentime',
    promo=PROMO_COMMENT,
    design='big-screen',
    only=[int(a) for a in sys.argv[1:]] or None,
)
