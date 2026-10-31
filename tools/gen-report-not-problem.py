#!/usr/bin/env python3
"""report-not-problem: the screen time report shows the damage and changes nothing.

  hook    "your screen time report / is not the problem", new to hook_pool
          2026-10-31 (pillar screentime, theme screentime).
  lens    every step is something the report never did: it ACTS. Reading a
          number on Sunday is the behaviour the hook is arguing against, so
          no step here is "check your usage" -- that is the problem restated.
  ARCO    angle a2 (Blocked Hours, set once, number halves): the one angle in
          the screentime set that answers a report with an action rather than
          better reporting. a6/i1 are Insights angles and would have agreed
          with the thing the hook calls useless.
  rules   none repeat boring-phone-2 (Raise to Wake, Hide app, one page,
          badges), the only other post in this look.
"""
from _screentime_common import build

build(
    topic='report-not-problem',
    hook=['your screen time report', 'is not the problem'],
    bgs=['bg-h54.jpg',   # hook         desk-led-warm      luma 38
         'bg-h52.jpg',   # ARCO         desk-city-day      luma 64
         'bg-n05.jpg',   # 2            desk-empty-day     luma 51
         'bg-h51.jpg',   # 3            desk-city-day      luma 60
         'bg-n06.jpg',   # 4            desk-empty-day     luma 55
         'bg-h48.jpg'],  # 5            desk-city-day      luma 65
    arco_lines=['Blocked Hours shuts my apps from',
                'six to eight, every evening.', '',
                'I set it once and my screen time is', 'down by half.', '',
                'I never argue with it.'],
    rules=[
        ('Downtime picks the hours', [
            'Set Downtime in Screen Time and',
            'name the hours apps stay shut.', '',
            'The report says where the evening',
            'went. Downtime spends it for you.']),
        ('App Limits cap the category', [
            'One limit covers Social, instead',
            'of one app at a time.', '',
            'The number stops being a surprise',
            'you read about on Sunday.']),
        ('Alerts arrive on your clock', [
            'Scheduled Summary holds alerts and',
            'delivers them at times you pick.', '',
            'You open the phone because you',
            'decided to, not because it buzzed.']),
        ('The charger moves out', [
            'Leave the charger in the kitchen',
            'and let the phone sleep there.', '',
            'The first hour of the day happens',
            'before you have read anything.']),
    ])
