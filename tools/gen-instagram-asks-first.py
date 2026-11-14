#!/usr/bin/env python3
"""instagram-asks-first: screentime pillar, ARCO's own screens as the whole post.

  hook      "instagram opens to this now / and i close it every time", written 2026-11-14 at Thinh's request
            ("post more posts where its showing arco ui ... with new hooks"),
            added to hook_pool.json with origin 'claude'.
  why       Thinh, 2026-11-14: more eyes on the UI, which turns into
            downloads. Added on top of frequency test week 1 (2026-11-16),
            not swapped for a tools post.
  screens   the 7 Oct captures in design/control-center; every line was
            checked against pivot-timer (shield copy in ShieldConfiguration-
            Extension, Today timeline, widget Start intent, Insights groups).
  design    big-screen: no photograph behind the handset, the screenshot is
            the argument.

Usage: python3 tools/gen-instagram-asks-first.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, HABITS, INSIGHTS_NOW, SHIELD_NOW, TODAY_NOW)
from _tools_screens import PROMO_COMMENT

build(
    topic='instagram-asks-first',
    hook=['instagram opens to this now', 'and i close it every time'],
    kicker='here is why',
    bgs=['bg-h79.jpg', 'bg-h24.jpg', 'bg-h02.jpg', 'bg-h49.jpg', 'bg-h34.jpg', 'bg-h11.jpg'],
    slides=[
        (SHIELD_NOW, '1', 'Instagram asks one question first.',
         'During a focus block it opens to a shield: what does this add to your day? One tap locks it again.'),
        (TODAY_NOW, '2', 'There is always a next block.',
         'Today puts every block on a timeline with a red line for now, so the next thing to start is right there.'),
        (HABITS, '3', 'Start is one tap from home.',
         'The habit chart widget shows this week’s hours and a Start button that runs the timer without opening anything.'),
        (INSIGHTS_NOW, '4', 'The week gets a number.',
         'Insights splits screen time into distracting, entertainment and everyday, against the week before.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='screentime',
    promo=PROMO_COMMENT,
    design='big-screen',
    only=[int(a) for a in sys.argv[1:]] or None,
)
