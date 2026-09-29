#!/usr/bin/env python3
"""launch-weekend-screens: build pillar, real ARCO screens on veiled photos.

Thinh's request of 2026-09-29: same concept as the screentime screens posts,
with their screenshots and backgrounds, second build outing after
ship-weekend-screens. Hook is the least recently used eligible build hook,
"launch an app in one weekend", so every reason is about getting two days
of building done and carried from Saturday into Sunday. Each checked in the
iOS source on pivot-timer: a Blocked Hours window can drop "Use my Focus
apps" and pick its own list (BlockedHoursSheet appsSection); holding a timer
habit offers Log time (TodayPrototypeView contextMenu, LogTimeSheet);
yesterday's unfinished timed tasks open Plan your day with the time they had
(PlanDayPrototypeView reload, "Unfinished · yesterday", "was 14:00"); the
Insights hero names the week's BEST DAY. None repeats a hooks.json caption
or the other screens posts.

The closer is ARCO angle drawn once by next_arco_angle('build') and frozen
here. Backgrounds by _veiled_screens.pick_bgs with ship-weekend-screens' set
excluded, so two screens posts in a row do not share frames, then frozen.
"""
import sys
from _veiled_screens import (build, TODAY, PLAN_DAY, CONTROL, GOOD_HABITS,
                             KICKER, CARD_OUTLINE)

build(
    topic='launch-weekend-screens',
    hook=['launch an app', 'in one weekend'],
    bgs=['bg-n08.jpg',   # hook   desk-led-neon
         'bg-h31.jpg',   # 1      lounge-night
         'bg-h34.jpg',   # 2      desk-empty-day
         'bg-h35.jpg',   # 3      supercars-dusk
         'bg-h45.jpg',   # 4      window-silhouette (the one person)
         'bg-h48.jpg'],  # card   desk-city-day
    slides=[
        (CONTROL, '1', 'The build days get their own lock.',
         'Turn off Use my Focus apps on a Blocked Hours window and pick its '
         'own list. YouTube and Discord shut for the weekend only.'),
        (TODAY, '2', 'Forgot the timer? Log it.',
         'Hold a timer habit like Deep work and tap Log time. The two hours '
         'you built without it still count.'),
        (PLAN_DAY, '3', 'Saturday’s leftovers open Sunday.',
         'Tasks you did not finish yesterday sit at the top of Plan your '
         'day, with the time they had. Place puts them back on today.'),
        (GOOD_HABITS, '4', 'Sunday has a number to beat.',
         'Insights name your best focus day of the week. Sunday '
         'opens with Saturday\u2019s hours to beat.'),
    ],
    closer=['One app holds the plan and the block that protects it.',
            'Tasks get a time, and Focus mode shuts the apps for it.'],
    pillar='build',
    kicker=KICKER,
    card_style=CARD_OUTLINE,
    only={int(a) for a in sys.argv[1:]} or None)
