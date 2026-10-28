#!/usr/bin/env python3
"""Three more screens posts, continuing boring-phone-widgets.

  request   Thinh, 2026-10-26: "do more posts actually letting people see the
            ui, the features the widgets, prioritize order bcs most poeple
            dont get to the end of the slideshow". So slide 2 of each post is
            the screen that proves that post's hook on its own, and nothing
            is saved for a finish nobody sees.
  screens   six of the seven current captures. Four of them are HOME screens
            carrying ARCO widgets, not pages inside the app -- scr-timeline
            and scr-tasks are the timeline and task widgets, screen-widgets
            is the habit and timer set. Only scr-today, screen-shield and
            screen-insights are the app itself. The copy has to say which it
            is looking at, and an in-app screen leads every post so the first
            thing a viewer sees is the product and not a home screen.
            scr-habits is a second capture of screen-widgets and is unused.
  hooks     the last three eligible screentime hooks, word for word from the
            pool. That empties the pillar until the cooldown turns over, so
            this is the whole batch.
  bgs       allocated across all three posts at once, then frozen here. Per-
            post picking with BG_COOLDOWN=1 collapses to alphabetical order
            once every frame counts as recent, and it has already produced
            two posts with identical six-frame sets. Frozen also means a
            rebuild of one slide cannot quietly reshuffle the rest.

Usage: python3 tools/gen-ui-tour.py            # all three
       python3 tools/gen-ui-tour.py <topic> [slide numbers to redo]
"""
import sys

from _veiled_screens import (build, WIDGETS, SHIELD_NOW, TODAY_NOW,
                             TIMELINE, TASKS, INSIGHTS_NOW)
from _tools_screens import PROMO_COMMENT

POSTS = [
    dict(
        topic='three-hours-no-deleting',
        # lens: the hours it removes without deleting anything
        hook=['i cut 3 hours of screen time', 'without deleting a single app'],
        bgs=['bg-h20.jpg', 'bg-h24.jpg', 'bg-h29.jpg', 'bg-h31.jpg',
             'bg-h36.jpg', 'bg-h45.jpg'],
        closer='Block the hours, keep the apps.',
        slides=[
            (SHIELD_NOW, 1, 'The app opens onto a wall.',
             'A blocked app keeps its place on the home screen and still takes the tap. '
             'What loads is a shield, so the reach costs a second instead of an hour.'),
            (INSIGHTS_NOW, 2, 'Three hours is a number now.',
             'Insights totals the week by app and by day, so you can see which hours came '
             'back and which ones you handed over anyway.'),
            (TODAY_NOW, 3, 'The evening is spoken for.',
             'Blocked windows run on the same timeline as the tasks, so 18:00 to 20:00 is '
             'already claimed before the evening you usually lose starts.'),
            (WIDGETS, 4, 'The hours land somewhere else.',
             'A timer widget totals the week on the home screen, 20h on the side project '
             'and up a quarter, so the time you stopped giving away is visible.'),
        ],
    ),
    dict(
        topic='still-100-hours',
        # lens: the reason it exposes, with a number on it
        hook=['5 reasons your screen time', 'is still 100+ hours'],
        bgs=['bg-h28.jpg', 'bg-h01.jpg', 'bg-h37.jpg', 'bg-h48.jpg',
             'bg-h88.jpg', 'bg-n01.jpg', 'bg-n05.jpg'],
        closer='See the hours, then take them back.',
        slides=[
            (INSIGHTS_NOW, 1, 'You never saw the breakdown.',
             'Insights splits the week by app and by day instead of handing you one total, '
             'so the hour you blamed on work turns out to have a name on it.'),
            (SHIELD_NOW, 2, 'Nothing stands in the way.',
             'A blocked app opens onto a shield for the hours you chose, not a reminder you '
             'can swipe past, so the tap that always worked stops working.'),
            (TODAY_NOW, 3, 'The day was never planned.',
             'Tasks and habits go on one timeline with a line for now, so an eight-hour list '
             'in a five-hour afternoon shows as overflow before you start.'),
            (TIMELINE, 4, 'The plan is somewhere you never look.',
             'A widget puts the day on the home screen with the next block already marked. '
             'A plan you have to go and open is a plan you stop opening.'),
            (WIDGETS, 5, 'The home screen still invites it.',
             'Habit widgets take the slots the feed apps had and fill in as you keep them, '
             'so the unlock starts on your own run and not on a feed.'),
        ],
    ),
    dict(
        topic='not-one-is-willpower',
        # lens: the mechanism that works without willpower
        hook=['4 things that cut my screen time', 'not one of them is willpower'],
        bgs=['bg-h39.jpg', 'bg-h02.jpg', 'bg-h38.jpg', 'bg-h49.jpg',
             'bg-n03.jpg', 'bg-n06.jpg'],
        closer='Set it once and let it run.',
        slides=[
            (TODAY_NOW, 1, 'Tomorrow is decided tonight.',
             'You draw the next day once, as blocks with times on them, so at 14:00 there is '
             'nothing to decide and something already written to do.'),
            (SHIELD_NOW, 2, 'The block does not ask first.',
             'Blocked hours start and end on a schedule you set once, with no prompt and no '
             'snooze, so there is nothing left to resist at 21:00.'),
            (TASKS, 3, 'The list waits on the home screen.',
             'A tasks widget shows the next six with the project and the flag on each, so '
             'nothing is held in your head and starting needs no decision.'),
            (WIDGETS, 4, 'The streak does the pushing.',
             'Each habit widget draws the run you are on where a feed app used to sit, and '
             'keeping a run going takes less from you than starting one over.'),
        ],
    ),
]


def main(argv):
    want = argv[0] if argv else None
    only = [int(a) for a in argv[1:]] or None
    for p in POSTS:
        if want and p['topic'] != want:
            continue
        build(topic=p['topic'], hook=p['hook'], kicker='here is why',
              bgs=p['bgs'], slides=p['slides'], closer=p['closer'],
              pillar='screentime', promo=PROMO_COMMENT, only=only)
        print('built', p['topic'])


if __name__ == '__main__':
    main(sys.argv[1:])
