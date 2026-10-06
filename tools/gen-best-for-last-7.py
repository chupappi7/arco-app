#!/usr/bin/env python3
"""best-for-last-7: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-07: ship-weekend-screens format, six tools posts
            with varied hooks; the app is named by its current store name,
            App Blocker & Focus: ARCO, on its slide and in the card's search
            line.
  hook      "5 tools to stay productive / i saved the best for last",
            from hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Codex, Raycast, Linear, Canva.
            One LLM, rotated across the 2026-10-07 batch. The hook counts five apps, so the post carries five and runs to 7 slides.
  ARCO      "Mark in progress" moves a task into an In progress group above
            Inbox and every project; ticking it done clears the flag
            (TasksPrototypeView inProgressGroup, setInProgress; TaskSheets).
  teaching  every tool point checked against the captions in tools/hooks.json.
  card      angle drawn once with next_arco_angle('focus') and frozen.
  photos    hook frame chosen so the batch's six hooks sit on six different
            scenes; app frames from the pick_bgs pool (band luma gate, no
            hook-only vibe, one person, no adjacent vibe, no frame shared
            with the post before).

Usage: python3 tools/gen-best-for-last-7.py [slide numbers to redo]
"""
import sys
from _veiled_screens import TODAY
from _tools_screens import build, PROMO_STORE_NAME

build(
    topic='best-for-last-7',
    hook=['5 tools to stay productive', 'i saved the best for last'],
    theme='focus',
    bgs=[
         'bg-h38.jpg',   # hook
         'bg-h32.jpg',   # ARCO
         'bg-h34.jpg',   # Codex
         'bg-h35.jpg',   # Raycast
         'bg-h46.jpg',   # Linear
         'bg-h88.jpg',   # Canva
         'bg-n01.jpg',   # card
    ],
    arco=(TODAY, "What you're on sits on top.",
          'Tap Mark in progress on a task and it moves above every project in Tasks. Tick it done and the flag clears itself.'),
    tools=[
        ('Codex', 'It codes with the wifi off.',
         ['Run codex --oss and the Codex CLI works with an open model running on your laptop.',
          'A flight or a dead cafe connection stops being a day off from the build.']),
        ('Raycast', 'Typos get fixed in place.',
         ['Select a paragraph and run Fix Spelling and Grammar from the Raycast bar.',
          'The corrected text replaces your selection in whatever app you are typing in.']),
        ('Linear', 'The backlog clears itself.',
         ['Turn on auto-close in your team settings and issues nobody touched for months close on their own.',
          'The list you open each morning only holds work someone still cares about.']),
        ('Canva', 'Erase anything in a photo.',
         ['In Canva, brush Magic Eraser over a cable or a stranger in the shot.',
          'It disappears and the background fills in, so the photo you have is the one you post.']),
    ],
    closer=['I start a session and every app on the list', 'locks itself. Four hours later the phone has', 'not been picked up once. My holy grail.'],
    promo=PROMO_STORE_NAME,
    only={int(a) for a in sys.argv[1:]} or None)
