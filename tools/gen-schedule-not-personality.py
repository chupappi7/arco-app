#!/usr/bin/env python3
"""schedule-not-personality: discipline pillar, real ARCO screens on veiled photos.

The screentime screens concept (_veiled_screens: hook photo, one ARCO screen
per reason in a handset, the icon card) on Thinh's 2026-09-23 note: same way,
but the hook and the copy aimed at discipline, listing reasons. Each title is
a reason discipline is a schedule; the screen beside it is the mechanism,
checked in the iOS source: Wake up carries an AlarmKit alarm that follows the
block, the Plan your day card counts untimed tasks down to "Nothing waiting
for a time", Insights puts the average day beside the best one, and ending
Blocked Hours early is a 30 second wait that resets if you leave. None repeats
a hooks.json caption, no-willpower-screens or hundred-hours-screens.

The closer is ARCO angle s1, drawn once by next_arco_angle('discipline') and
frozen here. Backgrounds picked by the gen-daily-batch rules with today's
screens posts excluded, then frozen.

Thinh's fix the same day: "here is why" under the hook, and a thin white
outline on the card's icon and App Store badge. Only 01 and 06 changed;
`python3 gen-schedule-not-personality.py 1 6` re-renders just those.
"""
import sys
from _veiled_screens import (build, PLAN_DAY, TODAY, GOOD_HABITS, CONTROL,
                             KICKER, CARD_OUTLINE)

build(
    topic='schedule-not-personality',
    hook=['discipline', 'is a schedule, not a personality'],
    bgs=['bg-h42.jpg',   # hook   jet-mountain (the one person)
         'bg-h37.jpg',   # 1      supercars-dusk
         'bg-h49.jpg',   # 2      desk-city-day
         'bg-n04.jpg',   # 3      villa-day
         'bg-n06.jpg',   # 4      desk-empty-day
         'bg-h38.jpg'],  # card   supercars-dusk
    slides=[
        (PLAN_DAY, '1', 'The day starts at a set time.',
         'Put Wake up on the plan and it sets a real alarm. Move the block '
         'and the alarm moves with it.'),
        (TODAY, '2', 'Every task gets a slot.',
         'The Plan your day card counts tasks with no time yet. It stays up '
         'until it reads nothing waiting.'),
        (GOOD_HABITS, '3', 'The bar is your own best day.',
         'Insights show your average day next to your best one, 2h 3m '
         'against 2h 58m. That gap is the target.'),
        (CONTROL, '4', 'Quitting early costs you.',
         'Ending blocked hours early means a 30 second wait on screen. '
         'Leave it and the count starts over.'),
    ],
    closer=['Blocked Hours closes the apps on a schedule I set once.',
            '9am arrives and the feeds simply do not open.'],
    pillar='discipline',
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    only={int(a) for a in sys.argv[1:]} or None)
