#!/usr/bin/env python3
"""sixty-one-days-2: re-shoot of sixty-one-days on new backgrounds, 2026-11-11.

Copy, screens and card unchanged from sixty-one-days; frames picked by the
frequency-test picker. Frequency test week 1, 14-20 Nov.
"""
"""sixty-one-days: price the habit in days, then say where the days hide.

  hook    "4 hours a day on your phone / is 61 days a year", new to hook_pool
          2026-10-31 (pillar screentime, theme insights). 4 x 365 = 1,460h,
          which is 60.8 days -- the hook rounds, the slides do not contradict
          it.
  lens    the stretch of life it gives back. One step does the arithmetic,
          two say where in the day the hours sit, and the last one answers
          the question the arithmetic creates.
  ARCO    angle a6, the Insights angle that names four hours on one app --
          the hook's own number -- so the opening screen lands on the hook.

Rebuilt 2026-11-02 on Thinh's note -- "i think all should have screens at
least, text by itself is boring". The first build carried one screen and
four text steps over photographs. Every step is a real ARCO screen now, and
the post closes on the card with the store CTA.
"""
from _veiled_screens import (WIDGETS, TODAY_NOW, build, INSIGHTS_NOW, SHIELD_NOW, GOOD_HABITS,
                             PLAN_DAY, CTA_STORE, KICKER, CARD_OUTLINE)

build(
    topic='sixty-one-days-2',
    hook=['4 hours a day on your phone', 'is 61 days a year'],
    bgs=['bg-h68.jpg',
         'bg-h24.jpg',
         'bg-h04.jpg',
         'bg-n03.jpg',
         'bg-n05.jpg',
         'bg-h22.jpg'],  # card         supercars-dusk     luma 24
    kicker=KICKER,
    slides=[
        (INSIGHTS_NOW, '1', 'The week, by app.',
         'Insights counts the hours per app and per day. '
         'Twenty four on one app is where the days hide.'),
        (SHIELD_NOW, '2', 'One hour back is 15 days.',
         'Blocked Hours shut the evening window. '
         'You do not have to win all four.'),
        (TODAY_NOW, '3', 'Give the hours a job.',
         'The day goes on a timeline and the time you cut lands on a block. '
         'Empty hours go back to the phone.'),
        (WIDGETS, '4', 'The days show up as work.',
         'Habit widgets fill in on the home screen as you keep them. '
         'The hour you took back is one you can point at.'),
    ],
    closer=['Four hours a day is 61 days a year.',
            'Take one of them back this week.'],
    promo=CTA_STORE,
    card_style=CARD_OUTLINE,
    design='wide-band')
