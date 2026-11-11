#!/usr/bin/env python3
"""report-not-problem-2: re-shoot of report-not-problem on new backgrounds, 2026-11-11.

Copy, screens and card unchanged from report-not-problem; frames picked by the
frequency-test picker. Frequency test week 1, 14-20 Nov.
"""
"""report-not-problem: the screen time report shows the damage and changes nothing.

  hook    "your screen time report / is not the problem", new to hook_pool
          2026-10-31 (pillar screentime, theme screentime).
  lens    every step is something the report never did: it ACTS. Reading a
          number on Sunday is the behaviour the hook is arguing against, so
          no step here is "check your usage" -- that is the problem restated.
  ARCO    angle a2 (Blocked Hours, set once, number halves): the one angle in
          the screentime set that answers a report with an action rather than
          better reporting.

Rebuilt 2026-11-02 on Thinh's note -- "i think all should have screens at
least, text by itself is boring". The first build was ARCO on one screen and
four stock iOS steps as text over photographs; it went out at a 0.8% like
rate against 2.0% for all posts. Every step is now a real ARCO screen in the
under-an-hour look, and the post closes on the card with the comment CTA.
The text-steps version is in git history.
"""
from _veiled_screens import (build, WIDGETS, SHIELD_NOW, TODAY_NOW, TIMELINE,
                             CTA_COMMENT, KICKER, CARD_OUTLINE)

build(
    topic='report-not-problem-2',
    hook=['your screen time report', 'is not the problem'],
    bgs=['bg-h58.jpg',
         'bg-h19.jpg',
         'bg-h31.jpg',
         'bg-h38.jpg',
         'bg-h49.jpg',
         'bg-h11.jpg'],  # card         desk-city-day      luma 65
    kicker=KICKER,
    slides=[
        (SHIELD_NOW, '1', 'The app opens into a wall.',
         'Blocked Hours shut the feeds on a schedule you set once. '
         'The report only tells you afterwards.'),
        (WIDGETS, '2', 'Blocking starts now.',
         'The timer widget on the home screen starts a session that locks '
         'the feeds until it ends. Nothing waits for Sunday.'),
        (TODAY_NOW, '3', 'Every hour gets a job.',
         'The day goes on the timeline as blocks. '
         'No empty hour is left for the feed.'),
        (TIMELINE, '4', 'A glance stays a glance.',
         'The widget shows the running block on the home screen. '
         'You never unlock to check.'),
    ],
    closer=['The report counts the hours.',
            'This one spends them.'],
    promo=CTA_COMMENT,
    card_style=CARD_OUTLINE,
    design='wide-band')
