#!/usr/bin/env python3
"""ship-weekend-screens: build pillar, real ARCO screens on veiled photos.

The screentime screens concept (_veiled_screens: hook photo, one ARCO screen
per reason in a handset, the icon card) on Thinh's request of 2026-09-29:
same concept as the latest screentime posts, aimed at a build hook. The hook
promises a month of work in a weekend, so every reason is about getting the
weekend booked and kept, checked in the iOS source on pivot-timer: quick
capture lifts "sat", "10am" and "#Work" out of the text (TaskCapture.parse);
Plan your day offers each task the time it was last given
(rememberedMinute); a Blocked Hours window can run on Weekends only
(BlockedHoursEditor daysSection); Insights at D split the day into twelve
two-hour blocks (bucketCount). None repeats a hooks.json caption or the
other screens posts.

The closer is ARCO angle v13, drawn once by next_arco_angle('build') and
frozen here. Backgrounds by _veiled_screens.pick_bgs with three-hours-screens'
set excluded, so two screens posts in a row do not share frames, then frozen.
"""
import sys
from _veiled_screens import (build, TODAY, PLAN_DAY, CONTROL, GOOD_HABITS,
                             KICKER, CARD_OUTLINE)

build(
    topic='ship-weekend-screens',
    hook=['how i ship in a weekend', 'what used to take a month'],
    bgs=['bg-n07.jpg',   # hook   desk-led-neon
         'bg-h32.jpg',   # 1      window-silhouette (the one person)
         'bg-h37.jpg',   # 2      supercars-dusk
         'bg-h46.jpg',   # 3      desk-city-day
         'bg-h88.jpg',   # 4      supercars-dusk
         'bg-n01.jpg'],  # card   villa-day
    slides=[
        (TODAY, '1', 'Saturday is booked by Tuesday.',
         'Type \u201clanding page sat 10am #Work\u201d as a task. It lands on '
         'Saturday at 10:00, filed under Work.'),
        (PLAN_DAY, '2', 'The time is already picked.',
         'Plan your day offers each task the time you gave it last. The '
         'build block goes back to 10:00 in one tap.'),
        (CONTROL, '3', 'The lock runs on weekends only.',
         'Set Blocked Hours to Weekends. Saturday and Sunday lock your '
         'focus apps. Weekdays stay open.'),
        (GOOD_HABITS, '4', 'You see which hours shipped.',
         'Switch Insights to D and the day splits into two hour blocks. '
         'An afternoon lost to the phone shows up as empty bars.'),
    ],
    closer=['The block I’m in sits on the Lock Screen with the time left on it.',
            'Picking up the phone shows the plan before it shows a feed.'],
    pillar='build',
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    only={int(a) for a in sys.argv[1:]} or None)
