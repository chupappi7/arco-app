#!/usr/bin/env python3
"""three-hours-screens-2: screentime pillar, real ARCO screens on veiled photos.

Thinh's request of 2026-10-04: same format as no-willpower-screens-2 and
hundred-hours-screens-2, a different hook from each, with the "arco focus"
search CTA on the card. The only eligible screentime hook that is neither of
theirs is the three-hours one, so every reason keeps the apps installed and
only changes when they open. Four new reasons, each checked in the committed
iOS source on pivot-timer: Focus mode's duration defaults to "Until turned
off · stop when you're done" (FocusSheet, duration == 0); a Blocked Hours
window ended early shows "Skipped for today" with Resume, which clears the
early-end marker so the shield returns for the rest of the window
(BlockedHoursSheet, BlockedHoursManager.resumeAfterEarlyEnd); Bad Habits
group cards show four apps and "Every app in this group" opens the full list
from Screen Time (BadHabitsScene prefix(4), InsightsPrototypeView appsPage);
a new Blocked Hours window has "Use my Focus apps" on by default, so it
shields the Focus list (BlockedHoursSheet useFocusApps = true). None repeats
a hooks.json caption or the other screens posts.

The closer is ARCO angle drawn by next_arco_angle('screentime') and frozen
here. Backgrounds: hook from _veiled_screens.pick_bgs, app frames by the same
guards with both reference posts' sets excluded, then frozen.
"""
import sys
from _veiled_screens import (build, SHIELD, CONTROL, BAD_HABITS, TODAY,
                             KICKER, CARD_OUTLINE)

build(
    topic='three-hours-screens-2',
    hook=['i cut 3 hours of screen time', 'without deleting a single app'],
    bgs=['bg-h07.jpg',   # hook   lounge-day
         'bg-h21.jpg',   # 1      lounge-night
         'bg-h22.jpg',   # 2      lounge-day
         'bg-h36.jpg',   # 3      supercars-dusk
         'bg-h48.jpg',   # 4      desk-city-day
         'bg-n03.jpg'],  # card   villa-day
    slides=[
        (SHIELD, '1', 'The lock has no end time.',
         'Focus mode starts on Until turned off. The apps stay shut until '
         'you stop it, not when a timer runs out.'),
        (CONTROL, '2', 'Ending early can be undone.',
         'End a Blocked Hours window early and it reads Skipped for today. '
         'Tap Resume and the apps lock for the rest of it.'),
        (BAD_HABITS, '3', 'The small apps add up.',
         'Each group card shows its top four apps. Every app in this group '
         'lists the rest with their hours, down to the 5 minute ones.'),
        (TODAY, '4', 'One list covers every block.',
         'A new Blocked Hours window uses your Focus apps by default. Add '
         'an app once and every window locks it too.'),
    ],
    closer=['Blocked Hours closes the apps on a schedule I set once.',
            '9am arrives and the feeds simply do not open.'],
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    promo=['Search “arco focus” on the App Store.'],
    only={int(a) for a in sys.argv[1:]} or None)
