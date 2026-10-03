#!/usr/bin/env python3
"""boring-phone-screens-2: screentime pillar, real ARCO screens on veiled photos.

Thinh's request of 2026-10-03: same format as the recent screentime screens
posts, with the "arco focus" search CTA on the card. Second outing of the
boring-phone hook on screens, four new reasons the phone went quiet, each
checked in the committed iOS source on pivot-timer: Take a break opens a
1-30 minute ruler with the break left after it (BreakRuler,
breakBudgetNote); each Blocked Hours window picks Gentle, 2 breaks an hour,
or Focused, 1 (BlockedHoursDifficulty, breaksSection); the streak-on-the-line
notification for streaks of 7+ days, with Mark done on it
(NotificationManager); "Focus done · <time> banked. Shield lifted."
(FocusManager.scheduleFocusCompleteNotification). None repeats a hooks.json
caption or the other screens posts.

The closer is ARCO angle f1, drawn by next_arco_angle('screentime') and
frozen here. Backgrounds from the leftover app-slide pool with
hundred-hours-screens-2's set excluded (hook bg-h04 from pick_hook_bg),
vibes alternating, no person, then frozen.
"""
import sys
from _veiled_screens import (build, SHIELD, CONTROL, TODAY, GOOD_HABITS,
                             KICKER, CARD_OUTLINE)

build(
    topic='boring-phone-screens-2',
    hook=['my phone is boring now', 'and it changed everything'],
    bgs=['bg-h04.jpg',   # hook   lounge-day
         'bg-h38.jpg',   # 1      supercars-dusk
         'bg-h48.jpg',   # 2      desk-city-day
         'bg-n03.jpg',   # 3      villa-day
         'bg-n06.jpg',   # 4      desk-empty-day
         'bg-h39.jpg'],  # card   supercars-dusk
    slides=[
        (CONTROL, '1', 'A break is a number you pick.',
         'Take a break opens a ruler from 1 to 30 minutes. It shows how '
         'much break is left after this one.'),
        (SHIELD, '2', 'Each block has its own rules.',
         'Set a window to Gentle for 2 breaks an hour or Focused for 1. '
         'Evenings stay loose while work hours stay tight.'),
        (GOOD_HABITS, '3', 'The streak sends the reminder.',
         'A streak of 7 days or more gets one afternoon reminder if the '
         'habit is still open. Mark done sits on the notification.'),
        (TODAY, '4', 'It tells you when it opens.',
         'When a session ends you get one note: Focus done, 1h 30m banked, '
         'shield lifted. No checking the phone to find out.'),
    ],
    closer=['Focus mode blocks every app on my list for the whole session.',
            'The phone stops being a decision while the timer runs.'],
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    promo=['Search “arco focus” on the App Store.'],
    only={int(a) for a in sys.argv[1:]} or None)
