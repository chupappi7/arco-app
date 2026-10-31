#!/usr/bin/env python3
"""sixty-one-days: price the habit in days, then say where the days hide.

  hook    "4 hours a day on your phone / is 61 days a year", new to hook_pool
          2026-10-31 (pillar screentime, theme insights). 4 x 365 = 1,460h,
          which is 60.8 days -- the hook rounds, the slides do not contradict
          it.
  lens    the stretch of life it gives back. One step does the arithmetic,
          two say where in the day the hours actually sit, and the last one
          answers the question the arithmetic creates.
  ARCO    angle a6. It is the Insights angle that names four hours on one app,
          the hook's own number, so the slide lands on the hook instead of
          near it.
"""
from _screentime_common import build

build(
    topic='sixty-one-days',
    hook=['4 hours a day on your phone', 'is 61 days a year'],
    bgs=['bg-h79.jpg',   # hook         desk-led-neon      luma 41
         'bg-n04.jpg',   # ARCO         villa-day          luma 54
         'bg-h45.jpg',   # 2            window-silhouette  luma 50 (the one person)
         'bg-h37.jpg',   # 3            supercars-dusk     luma 23
         'bg-h34.jpg',   # 4            desk-empty-day     luma 61
         'bg-h36.jpg'],  # 5            supercars-dusk     luma 24
    arco_lines=['Insights shows the week by app and', 'by day, in hours.',
                '', 'Seeing four hours on one app is what',
                'made me finally cut it.', '',
                'The number did the convincing.'],
    rules=[
        ('One hour back is 15 days', [
            'Cut a single hour a day and the',
            'year hands you two weeks.', '',
            'You do not have to win all four',
            'to get a holiday back.']),
        ('Most of it is after nine', [
            'Read Insights by hour instead of',
            'by app, for one week.', '',
            'The four hours are rarely spread',
            'out. They sit in the evening.']),
        ('Pickups cost more than minutes', [
            'Every pickup restarts whatever you',
            'were in the middle of.', '',
            'Fifty a day is why four hours',
            'feels like the entire evening.']),
        ('Name what the days are for', [
            'Decide what the 61 days buy before',
            'you go and take them back.', '',
            'Hours with nowhere to go come',
            'straight back to the phone.']),
    ])
