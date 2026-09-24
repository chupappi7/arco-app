#!/usr/bin/env python3
"""three-hours-screens: screentime pillar, real ARCO screens on veiled photos.

The screens concept (_veiled_screens) under the three-hours hook, the least
recently used eligible screentime hook. The hook promises hours back without
deleting anything, so every reason keeps the apps installed. Three mechanisms,
each checked in the iOS source on pivot-timer and shipped since June 2026:
the Bad Habits page ranks apps by minutes (BadHabitsPageReport, sorted desc);
a timer habit with Auto-start Focus starts a focus session of its own target
length when played (HabitTimerEngine, habit.focusEnabled); a focus session
runs a Live Activity counting down on the lock screen and Dynamic Island
(FocusLiveActivity, Text(timerInterval:)). None repeats a hooks.json caption
or the other screens posts. Suggested blocks was considered and dropped: not
certain it is in the build on the store.

The closer is ARCO angle drawn once by next_arco_angle('screentime') and
frozen here. Backgrounds by _veiled_screens.pick_bgs, then frozen.
"""
import sys
from _veiled_screens import (build, CONTROL, BAD_HABITS, TODAY,
                             KICKER, CARD_OUTLINE)

build(
    topic='three-hours-screens',
    hook=['i cut 3 hours of screen time', 'without deleting a single app'],
    bgs=['bg-h78.jpg',   # hook   desk-led-neon
         'bg-h20.jpg',   # 1      lounge-day
         'bg-h21.jpg',   # 2      lounge-night
         'bg-h34.jpg',   # 3      desk-empty-day
         'bg-h35.jpg'],  # card   supercars-dusk
    slides=[
        (BAD_HABITS, '1', 'Lock the app at the top.',
         'Insights rank every app by its hours this week. Lock the one at '
         'the top and the rest stay open.'),
        (TODAY, '2', 'A habit can lock the phone.',
         'Turn on Auto-start Focus for a timer habit. Tap play on Read '
         'before bed and the apps lock for its 30 minutes.'),
        (CONTROL, '3', 'Time left is on the lock screen.',
         'A focus session counts down on the lock screen and Dynamic '
         'Island. You check it without unlocking.'),
    ],
    closer=['Blocked Hours closes the apps on a schedule I set once.',
            '9am arrives and the feeds simply do not open.'],
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    only={int(a) for a in sys.argv[1:]} or None)
