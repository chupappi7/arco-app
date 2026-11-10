#!/usr/bin/env python3
"""boring-phone-home: screentime pillar in the screens look.

  hook      "my phone is boring now / and it changed everything", from the
            approved pool, word for word.
  lens      what it strips out of the phone pull. Each screen is one thing
            the pull no longer finds: the feed (shield), a blank home screen
            (timeline widget), an open app to check the list in (tasks
            widget), a vague sense of the hours (Insights).
  screens   the current 2.1.2 captures in design/control-center. Every line
            describes what the screenshot shows: the shield's question and
            its Lock back in button, the timeline's ticks, the tasks widget's
            red late flag, Insights' three categories by app.
  order     shield first: the strongest screen goes early because most
            viewers never reach the end. boring-phone-widgets opened on
            widgets; this one opens on the wall.

Usage: python3 tools/gen-boring-phone-home.py [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, pick_bgs, SHIELD_NOW, TIMELINE, TASKS,
                             INSIGHTS_NOW)
from _tools_screens import PROMO_COMMENT

TOPIC = 'boring-phone-home'

build(
    topic=TOPIC,
    hook=['my phone is boring now', 'and it changed everything'],
    kicker='here is why',
    bgs=pick_bgs(TOPIC, 5),   # hook + 4 screens + card
    slides=[
        (SHIELD_NOW, 1, 'The feed opens onto a question.',
         'A blocked app shows a shield asking what it adds to your day, with one '
         'button that locks you back in.'),
        (TIMELINE, 2, 'The home screen shows the day.',
         'A timeline widget lists the blocks in order and ticks each one off, so '
         'unlocking the phone shows what is next before anything new.'),
        (TASKS, 3, 'What is left sits on the home screen.',
         'The tasks widget shows today’s list with anything late flagged in red, '
         'so checking it never means opening an app.'),
        (INSIGHTS_NOW, 4, 'The scroll gets a number.',
         'Insights splits screen time into distracting, entertainment and everyday, '
         'app by app, so you see exactly where the hours went.'),
    ],
    closer='Plan the day, block the rest.',
    pillar='screentime',
    promo=PROMO_COMMENT,
    only=[int(a) for a in sys.argv[1:]] or None,
)
