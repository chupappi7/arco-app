#!/usr/bin/env python3
"""hundred-hours-screens: screentime pillar, real ARCO screens on veiled photos.

The under-an-hour concept on Thinh's 2026-09-23 note: normal backgrounds with
the opacity down so only a little of each shows. Same hook as screentime-100h
and -2, five new reasons, none repeating theirs (no plan, not blocked, no end,
first unlock, weekly number, pickups, autoplay, bed via Sleep Focus, checking
the time) or no-willpower-screens'. Each reason is answered by the ARCO screen
beside it, checked in the iOS source: Lock back in closes the app and keeps
the block, windows can wrap midnight, Bad Habits shows the change vs the
previous period, Plan your day places untimed habits, Best streak.

Backgrounds picked with _veiled_screens.pick_bgs (the gen-daily-batch walk)
on the first build, excluding no-willpower-screens' set, and frozen.
"""
from _veiled_screens import (build, SHIELD, CONTROL, BAD_HABITS, PLAN_DAY,
                             GOOD_HABITS)

build(
    topic='hundred-hours-screens',
    hook=['5 reasons your screen time', 'is still 100+ hours'],
    bgs=['bg-h41.jpg',   # hook   jet-mountain (the one person)
         'bg-h31.jpg',   # 1      lounge-night
         'bg-h34.jpg',   # 2      desk-empty-day
         'bg-h35.jpg',   # 3      supercars-dusk
         'bg-h46.jpg',   # 4      desk-city-day
         'bg-h88.jpg',   # 5      supercars-dusk
         'bg-n01.jpg'],  # card   villa-day
    slides=[
        (SHIELD, '1', 'You open it on reflex.',
         'A locked app opens on this screen, not the feed. Lock back in '
         'closes it and the lock stays on.'),
        (CONTROL, '2', 'Your block ends at bedtime.',
         'Blocked hours can run past midnight, 23:00 to 07:00. The feeds '
         'stay locked until morning.'),
        (BAD_HABITS, '3', 'You never see it move.',
         'Insights put this week next to the last one as a percent, so a '
         '33% drop shows up while you make it.'),
        (PLAN_DAY, '4', 'Your habits have no time.',
         'Plan your day lists every habit without a slot. Place at 09:00 '
         'puts it on today, once or every day.'),
        (GOOD_HABITS, '5', 'Nothing counts the good days.',
         'Best streak counts days in a row across every habit, so a 20 day '
         'run is on the screen next to the feed.'),
    ],
    closer=['Locks that hold through the night.',
            'A week you can watch go down.'])
