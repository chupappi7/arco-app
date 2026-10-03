#!/usr/bin/env python3
"""no-willpower-screens-2: screentime pillar, real ARCO screens on veiled photos.

Thinh's request of 2026-10-03: same format as three-hours-screens,
boring-phone-screens and lock-in-screens, with the "arco focus" search CTA
on the card. Hook is the least recently used eligible screentime hook, so
every reason is a mechanism that works without willpower. Each checked in
the committed iOS source on pivot-timer: the Focus mode sheet reads "Apps
unlock at HH:mm" before the session starts (FocusPrototypeView); the
DeviceActivity monitor re-applies the shield when a break ends, even inside
the app (intervalDidStart, sixsix.breakEnd / sixsix.bhbreak); one "45 minutes
today" notification a day across the distraction list (heavyDayMin = 45);
the Wind-down preset, 21-23 every day, from Today's lock icon
(BlockedHours.presets). None repeats a hooks.json caption or the other
screens posts.

The closer is ARCO angle s2, drawn by next_arco_angle('screentime') and
frozen here. Backgrounds from _veiled_screens.pick_bgs (hook bg-h02), app
frames re-ordered by hand so the set differs from no-willpower-screens.
"""
import sys
from _veiled_screens import (build, SHIELD, CONTROL, BAD_HABITS, TODAY,
                             KICKER, CARD_OUTLINE)

build(
    topic='no-willpower-screens-2',
    hook=['4 things that cut my screen time', 'not one of them is willpower'],
    bgs=['bg-h02.jpg',   # hook   lounge-day
         'bg-h31.jpg',   # 1      lounge-night
         'bg-h49.jpg',   # 2      desk-city-day
         'bg-h24.jpg',   # 3      lounge-night
         'bg-h50.jpg',   # 4      desk-city-day
         'bg-h29.jpg'],  # card   supercars-dusk
    slides=[
        (CONTROL, '1', 'The end time is set first.',
         'Pick One hour in Focus mode and it reads Apps unlock at 15:30 '
         'before you start. The finish line is fixed before minute one.'),
        (SHIELD, '2', 'The lock comes back on its own.',
         'When a break ends, the shield returns even if you are still in '
         'the app. Nobody has to remember to close it.'),
        (BAD_HABITS, '3', '45 minutes gets one message.',
         'Pass 45 minutes in your distracting apps and it sends one note: '
         'that is a workout, a chapter. Once a day, never more.'),
        (TODAY, '4', 'One tap locks every evening.',
         'Tap the lock on Today and pick Wind-down. The apps shut from '
         '21:00 to 23:00 every night after that.'),
    ],
    closer=['The block runs on a timetable, not on willpower.',
            'There is no decision left to make when the hour starts.'],
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    promo=['Search “arco focus” on the App Store.'],
    only={int(a) for a in sys.argv[1:]} or None)
