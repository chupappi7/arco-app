#!/usr/bin/env python3
"""hundred-hours-screens-2: screentime pillar, real ARCO screens on veiled photos.

Thinh's request of 2026-10-03: same format as the recent screentime screens
posts, with the "arco focus" search CTA on the card. Second outing of the
100+ hours hook on screens, five new reasons, each checked in the committed
iOS source on pivot-timer: "or add my N most distracting apps" picks from
Social, Entertainment and Games over 14 days (SuggestedBlocks,
SuggestedBlocksReport); the Blocked Hours sheet's "Your day · Nh protected"
bar (CoverageBar); a focus session's break bank, 5 minutes for 30 or 60
minutes, kept in the App Group so a force quit does not refill it
(FocusManager.breakBudgetSeconds); the green dot on the Control tab and
"NOT BLOCKING · SCREEN TIME OFF" with its one-tap fix (MainTabView
blockingNow, notBlockingLabel); the Follow-through tile, last 14 focus
sessions, turned on in Customise (followThroughTile). None repeats a
hooks.json caption or the other screens posts.

The closer is ARCO angle i1, drawn by next_arco_angle('screentime') and
frozen here. Backgrounds from _veiled_screens.pick_bgs with
no-willpower-screens-2's set excluded, then frozen.
"""
import sys
from _veiled_screens import (build, SHIELD, CONTROL, BAD_HABITS, TODAY,
                             GOOD_HABITS, KICKER, CARD_OUTLINE)

build(
    topic='hundred-hours-screens-2',
    hook=['5 reasons your screen time', 'is still 100+ hours'],
    bgs=['bg-h03.jpg',   # hook   lounge-day
         'bg-h34.jpg',   # 1      desk-empty-day
         'bg-h35.jpg',   # 2      supercars-dusk
         'bg-h45.jpg',   # 3      window-silhouette (the one person)
         'bg-h46.jpg',   # 4      desk-city-day
         'bg-n01.jpg',   # 5      villa-day
         'bg-n05.jpg'],  # card   desk-empty-day
    slides=[
        (BAD_HABITS, '1', 'You blocked the wrong apps.',
         'With no apps picked, tap add my most distracting apps. It takes '
         'them from your last 14 days of social, entertainment and games.'),
        (CONTROL, '2', 'Your blocks cover two hours.',
         'Blocked Hours draws every window on one 24 hour bar and adds '
         'them up. 4h protected means 20 hours are not.'),
        (SHIELD, '3', 'Your breaks never run out.',
         'A one hour focus session gets 5 minutes of breaks. Force '
         'quitting the app does not refill them.'),
        (TODAY, '4', 'The block is not even on.',
         'A green dot sits on the Control tab while apps are locked. If '
         'Screen Time access is off, Control says Not blocking and fixes '
         'it in one tap.'),
        (GOOD_HABITS, '5', 'You quit halfway and forget.',
         'Turn on Follow-through in Customise. It shows how many of your '
         'last 14 focus sessions you finished.'),
    ],
    closer=['Insights show where the hours went, by app and by day.',
            'You stop guessing which one took the evening.'],
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    promo=['Search “arco focus” on the App Store.'],
    only={int(a) for a in sys.argv[1:]} or None)
