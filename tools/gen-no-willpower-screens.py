#!/usr/bin/env python3
"""no-willpower-screens: screentime pillar, real ARCO screens on veiled photos.

The under-an-hour concept (hook photo, a screen in a handset per step, the
icon card) on Thinh's 2026-09-23 note: normal backgrounds with the opacity
down so only a little of each shows. Same hook as under-an-hour, four new
answers to it: none repeats that post's or three-hours-back-2's points
(schedule locks, focus session, planned day, where the hours went). Each is a
mechanism that works without willpower, checked in the iOS source: the shield
copy, the difficulty break rates, the Bad Habits categories, the play button
on a timeline block.

Backgrounds picked with _veiled_screens.pick_bgs (the gen-daily-batch walk)
on the first build and frozen.
"""
from _veiled_screens import build, SHIELD, CONTROL, BAD_HABITS, TODAY

build(
    topic='no-willpower-screens',
    hook=['4 things that cut my screen time', 'not one of them is willpower'],
    bgs=['bg-h40.jpg',   # hook   jet-mountain (the one person)
         'bg-h20.jpg',   # 1      lounge-day
         'bg-h21.jpg',   # 2      lounge-night
         'bg-h22.jpg',   # 3      lounge-day
         'bg-h24.jpg',   # 4      lounge-night
         'bg-h29.jpg'],  # card   supercars-dusk
    slides=[
        (SHIELD, '1', 'The blocked app asks first.',
         'Open Instagram in a block and it asks what this adds to your day. '
         'The feed never loads.'),
        (CONTROL, '2', 'Breaks are rationed.',
         'Every break is 5 minutes. On Strict you get one every 2 hours, '
         'then the apps stay shut.'),
        (BAD_HABITS, '3', 'Only the distracting part counts.',
         'Insights split the hours into distracting, entertainment and '
         'everyday, so you know which 60% to cut.'),
        (TODAY, '4', 'The block you are in is a timer.',
         'Tap play on it and the timeline counts it down, so the phone shows '
         'the task, not a feed.'),
    ],
    closer=['A lock that asks before it opens.',
            'Breaks that run out on their own.'])
