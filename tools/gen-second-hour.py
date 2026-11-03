#!/usr/bin/env python3
"""second-hour: starting is easy, staying is the part nobody builds for.

  hook    "the hard part is not starting / it is the second hour", new to
          hook_pool 2026-10-31 (pillar discipline, theme discipline).
  lens    what it does when the first hour's momentum is gone. Nothing here
          is a motivation trick, because motivation is the thing that has
          already run out by the time this hook applies.
  ARCO    angle a10: an hour of work is an hour, not forty minutes and a
          scroll. Erosion inside a session is the second hour's actual
          failure mode.
  pillar  discipline. The screens builder takes the pillar as an argument,
          so a discipline hook uses the same look as the screentime ones.

Rebuilt 2026-11-02 on Thinh's note -- "i think all should have screens at
least, text by itself is boring". The first build carried one screen and
four text steps over photographs; it was the best of that set at a 2.3% like
rate, and the screens posts in this pillar sit above it.
"""
from _veiled_screens import (build, TODAY_NOW, CONTROL, TIMELINE, GOOD_HABITS,
                             CTA_COMMENT, KICKER, CARD_OUTLINE)

build(
    topic='second-hour',
    hook=['the hard part is not starting', 'it is the second hour'],
    pillar='discipline',
    bgs=['bg-n07.jpg',   # hook         desk-led-neon      luma 34
         'bg-h32.jpg',   # 1            window-silhouette  luma 36 (the one person)
         'bg-h88.jpg',   # 2            supercars-dusk     luma 29
         'bg-h21.jpg',   # 3            lounge-night       luma 64
         'bg-h35.jpg',   # 4            supercars-dusk     luma 33
         'bg-h22.jpg'],  # card         lounge-day         luma 53
    kicker=KICKER,
    slides=[
        (TODAY_NOW, '1', 'Hour two is already placed.',
         'Both blocks go on the timeline while you plan. '
         'Hour two starts without a decision.'),
        (CONTROL, '2', 'The session holds the apps.',
         'Start the timer and the feeds stay shut until it ends. '
         'An hour of work is an hour.'),
        (TIMELINE, '3', 'Coming back is one line.',
         'The widget shows the block that is running. '
         'The walk back to the desk misses the feed.'),
        (GOOD_HABITS, '4', 'A lost hour is visible.',
         'Focus time is counted by the week. '
         'The second hour stops being a mood.'),
    ],
    closer=['Anyone can start.',
            'Build the day so hour two runs itself.'],
    promo=CTA_COMMENT,
    card_style=CARD_OUTLINE,
    design='wide-band')
