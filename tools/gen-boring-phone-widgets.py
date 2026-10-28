#!/usr/bin/env python3
"""boring-phone-widgets: screentime pillar in the screens look.

  request   Thinh, 2026-10-26: show the UI, the features, the widgets, and
            put the strongest thing early -- most people never reach the end
            of a slideshow, so the best screen goes on slide 2 rather than
            being saved for a finish nobody sees.
  screens   the CURRENT app, captured 4-7 Oct against 2.1.2. The screens
            format had been reading a desktop folder whose newest capture was
            21 September, which is how a post went out showing a plan screen
            dated 22 August and was rejected.
  order     widgets first. A home screen of habit streaks instead of app
            icons is literally what the hook describes, and it is the one
            screen that reads without being explained.
  hook      "my phone is boring now / and it changed everything", from the
            approved pool, word for word.

Usage: python3 tools/gen-boring-phone-widgets.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, pick_bgs, WIDGETS, SHIELD_NOW,
                             TODAY_NOW, INSIGHTS_NOW)
from _tools_screens import PROMO_COMMENT

TOPIC = 'boring-phone-widgets'

build(
    topic=TOPIC,
    hook=['my phone is boring now', 'and it changed everything'],
    kicker='here is why',
    bgs=pick_bgs(TOPIC, 5),   # hook + 4 screens + card
    slides=[
        (WIDGETS, 1, 'The home screen keeps the score.',
         'Every habit gets a widget that fills in as you keep it, so the run is on '
         'the home screen instead of inside an app you have to remember to open.'),
        (SHIELD_NOW, 2, 'The app you reach for is gone.',
         'A blocked app opens onto a shield instead of its feed. The reach is still '
         'a reflex, it just ends at a wall now.'),
        (TODAY_NOW, 3, 'The day is drawn, not listed.',
         'Tasks and habits sit on one timeline with a line for now, so the hour that '
         'was never going to fit shows up before you start it.'),
        (INSIGHTS_NOW, 4, 'The hours are counted for you.',
         'Insights breaks the week down by app and by day, so you argue with a number '
         'instead of a feeling about where the evening went.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='screentime',
    promo=PROMO_COMMENT,
    only=[int(a) for a in sys.argv[1:]] or None,
)
