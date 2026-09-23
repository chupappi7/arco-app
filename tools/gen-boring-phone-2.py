#!/usr/bin/env python3
"""boring-phone-2: screentime pillar, method post.

The hook promises a phone that stopped being interesting, so every step is a
setting that takes something off the screen: nothing lights up when lifted,
the feeds are hidden, the home screen is one page of tools, no badges. All
four are stock iOS settings, none of them deletes an app.

ARCO copy drawn by next_arco_angle('screentime') on the first build (s2) and
frozen here so a rebuild does not rotate it. Backgrounds picked with the
gen-daily-batch walk (hook-only vibe on the hook only, copy_band_luma under
70, no adjacent vibe repeat, one person at most: the hook's) and frozen.
"""
from _screentime_common import build

build(
    topic='boring-phone-2',
    hook=['my phone is boring now', 'and it changed everything'],
    bgs=['bg-h30.jpg',   # hook   jet-mountain (the one person)
         'bg-h20.jpg',   # ARCO   lounge-day
         'bg-h21.jpg',   # 2      lounge-night
         'bg-h22.jpg',   # 3      lounge-day
         'bg-h24.jpg',   # 4      lounge-night
         'bg-h29.jpg'],  # 5      supercars-dusk
    arco_lines=['The block runs on a timetable, not', 'on willpower.', '',
                'There is no decision left to make', 'when the hour starts.', '',
                'My holy grail.'],
    rules=[
        ('Raise to Wake is off', [
            'Switch off Raise to Wake in Display',
            '& Brightness settings.', '',
            'Lifting the phone shows a black',
            'screen, not a pile of alerts.']),
        ('The feeds are hidden', [
            'Hold a feed app and pick Hide and',
            'Require Face ID.', '',
            'It drops off the home screen and',
            'search, and its alerts go quiet.']),
        ('One home screen page', [
            'A Focus can show only the pages you',
            'pick. Give it one page of tools.', '',
            'While it is on, the page with the',
            'feeds is not there to swipe to.']),
        ('No red badges', [
            'Turn badges off for every app in',
            'Settings, then Notifications.', '',
            'The icons stop showing a count,',
            'so none of them asks to be opened.']),
    ])
