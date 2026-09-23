#!/usr/bin/env python3
"""boring-phone-screens: screentime pillar, real ARCO screens on veiled photos.

The screens concept (_veiled_screens: hook photo, one ARCO screen per reason
in a handset, the icon card) under the boring-phone hook, the least recently
used eligible screentime hook. Four reasons the phone went boring, each a
mechanism checked in the iOS source on pivot-timer: the shield carries a
single button, Lock back in, with no secondary to get past it; the Focus
list shields whole categories (.specific(categories)); 25 minutes in one app
posts "Still what you opened it for?" with a Block for today action that
shields that app until 23:59; the Timeline widget starts, pauses and checks
habits from the home screen. None repeats a hooks.json caption or the other
screens posts. The Always allowed list was considered and dropped: its
picker has no button that opens it.

The closer is ARCO angle f1, drawn once by next_arco_angle('screentime') and
frozen here. Backgrounds by the gen-daily-batch rules with today's screens
posts excluded, then frozen. Kicker and card outline per Thinh's 2026-09-23
note.
"""
import sys
from _veiled_screens import (build, SHIELD, CONTROL, BAD_HABITS, TODAY,
                             KICKER, CARD_OUTLINE)

build(
    topic='boring-phone-screens',
    hook=['my phone is boring now', 'and it changed everything'],
    bgs=['bg-h43.jpg',   # hook   jet-mountain (the one person)
         'bg-h36.jpg',   # 1      supercars-dusk
         'bg-h48.jpg',   # 2      desk-city-day
         'bg-n04.jpg',   # 3      villa-day
         'bg-n06.jpg',   # 4      desk-empty-day
         'bg-h31.jpg'],  # card   lounge-night
    slides=[
        (SHIELD, '1', 'There is no ignore button.',
         'Screen Time limits come with Ignore Limit. This screen has one '
         'button, and it keeps the app shut.'),
        (CONTROL, '2', 'Block the category, not the app.',
         'Pick Social as a whole category. Every app in it locks, not only '
         'the ones you remembered to list.'),
        (BAD_HABITS, '3', '25 minutes gets a question.',
         'After 25 minutes in one app it asks if that is still why you '
         'opened it. Block for today shuts it till midnight.'),
        (TODAY, '4', 'The home screen is the day.',
         'The Timeline widget lists today\'s habits in order. Start, pause '
         'or check one off without opening an app.'),
    ],
    closer=['Focus mode blocks every app on my list for the whole session.',
            'The phone stops being a decision while the timer runs.'],
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    only={int(a) for a in sys.argv[1:]} or None)
