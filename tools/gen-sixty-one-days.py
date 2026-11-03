#!/usr/bin/env python3
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
from _veiled_screens import (build, INSIGHTS_NOW, SHIELD_NOW, GOOD_HABITS,
                             PLAN_DAY, CTA_STORE, KICKER, CARD_OUTLINE)

build(
    topic='sixty-one-days',
    hook=['4 hours a day on your phone', 'is 61 days a year'],
    bgs=['bg-h79.jpg',   # hook         desk-led-neon      luma 41
         'bg-n04.jpg',   # 1            villa-day          luma 54
         'bg-h45.jpg',   # 2            window-silhouette  luma 50 (the one person)
         'bg-h37.jpg',   # 3            supercars-dusk     luma 23
         'bg-h34.jpg',   # 4            desk-empty-day     luma 61
         'bg-h36.jpg'],  # card         supercars-dusk     luma 24
    kicker=KICKER,
    slides=[
        (INSIGHTS_NOW, '1', 'The week, by app.',
         'Insights counts the hours per app and per day. '
         'Twenty four on one app is where the days hide.'),
        (SHIELD_NOW, '2', 'One hour back is 15 days.',
         'Blocked Hours shut the evening window. '
         'You do not have to win all four.'),
        (PLAN_DAY, '3', 'Give the hours a job.',
         'Plan the day and the time you cut lands on a block. '
         'Empty hours go back to the phone.'),
        (GOOD_HABITS, '4', 'The days show up as work.',
         'Focus time is counted by the week. '
         'The hour you took back is one you can point at.'),
    ],
    closer=['Four hours a day is 61 days a year.',
            'Take one of them back this week.'],
    promo=CTA_STORE,
    card_style=CARD_OUTLINE,
    design='wide-band')
