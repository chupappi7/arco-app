#!/usr/bin/env python3
"""lock-in-screens: discipline pillar, real ARCO screens on veiled photos.

The screentime screens concept (_veiled_screens) on Thinh's 2026-09-23 note:
same way, hook and copy aimed at discipline, listing reasons. The hook is
about the days you do not feel like it, so every step lowers the bar to
start without letting the day go, checked in the iOS source: a stopwatch
habit counts as done with any time on it, a placed block nudges 15 minutes
at a time, ending a break early refunds its unused minutes, and each habit
card draws a bar per day. None repeats a hooks.json caption, lock-in-anyway,
no-willpower-screens, hundred-hours-screens or schedule-not-personality.

The closer is ARCO angle s2, drawn once by next_arco_angle('discipline') and
frozen here. Backgrounds picked by the gen-daily-batch rules with today's
screens posts excluded, then frozen.
"""
from _veiled_screens import build, TODAY, PLAN_DAY, CONTROL, GOOD_HABITS

build(
    topic='lock-in-screens',
    hook=['this is how you lock in', "when you don't feel like it"],
    bgs=['bg-h73.jpg',   # hook   desk-led-neon
         'bg-h39.jpg',   # 1      supercars-dusk
         'bg-h50.jpg',   # 2      desk-city-day
         'bg-n03.jpg',   # 3      villa-day
         'bg-n05.jpg',   # 4      desk-empty-day
         'bg-h51.jpg'],  # card   desk-city-day
    slides=[
        (TODAY, '1', 'Five minutes still counts.',
         'A stopwatch habit has no target. Any time on it marks the day '
         'done, so a short session keeps the run.'),
        (PLAN_DAY, '2', 'Push it, do not skip it.',
         'Plus and minus move a block 15 minutes at a time. The habit '
         'slides later today instead of dropping off.'),
        (CONTROL, '3', 'Come back early, keep the minutes.',
         'Take a break, then tap Back to it early. The unused minutes go '
         'back in the bank for later.'),
        (GOOD_HABITS, '4', 'The empty day shows up.',
         'Each habit card draws a bar for every day of the week, so the '
         'day you skipped is a gap you can see.'),
    ],
    closer=['The block runs on a timetable, not on willpower.',
            'No decision is left when the hour starts.'],
    pillar='discipline')
