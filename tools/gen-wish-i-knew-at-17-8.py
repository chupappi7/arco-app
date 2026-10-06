#!/usr/bin/env python3
"""wish-i-knew-at-17-8: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-07: ship-weekend-screens format, six tools posts
            with varied hooks; the app is named by its current store name,
            App Blocker & Focus: ARCO, on its slide and in the card's search
            line.
  hook      "5 apps i wish someone / showed me at 17",
            from hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Cursor, ElevenLabs, CapCut, Notion.
            One LLM, rotated across the 2026-10-07 batch. The hook counts five apps, so the post carries five and runs to 7 slides.
  ARCO      habit page sentence: best and worst weekday once ten planned days
            exist, "Tuesday is your day for this. Friday is the weak one."
            (HabitPage sentence).
  teaching  every tool point checked against the captions in tools/hooks.json.
  card      angle drawn once with next_arco_angle('study') and frozen.
  photos    hook frame chosen so the batch's six hooks sit on six different
            scenes; app frames from the pick_bgs pool (band luma gate, no
            hook-only vibe, one person, no adjacent vibe, no frame shared
            with the post before).

Usage: python3 tools/gen-wish-i-knew-at-17-8.py [slide numbers to redo]
"""
import sys
from _veiled_screens import TODAY
from _tools_screens import build, PROMO_STORE_NAME

build(
    topic='wish-i-knew-at-17-8',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
         'bg-n05.jpg',   # hook
         'bg-h24.jpg',   # ARCO
         'bg-h29.jpg',   # Cursor
         'bg-h31.jpg',   # ElevenLabs
         'bg-h50.jpg',   # CapCut
         'bg-h37.jpg',   # Notion
         'bg-h45.jpg',   # card
    ],
    arco=(TODAY, 'It finds the day you slip.',
          'Open a habit from Today and after two weeks of data it writes one line, like Tuesday is your day for this, Friday is the weak one.'),
    tools=[
        ('Cursor', 'Read real code without breaking it.',
         ['Open any open source project in Cursor and switch the chat to Ask mode.',
          'It explains how the app works file by file and never edits a single line.']),
        ('ElevenLabs', 'Music you can post.',
         ['Describe a track to Eleven Music and it writes the song, with vocals or without.',
          'Paid plans clear it for commercial use, so the video is not muted for copyright.']),
        ('CapCut', 'Read the script, look at the lens.',
         ['Turn on Teleprompter in the CapCut camera and your script scrolls over the shot.',
          'You read every line while looking into the lens, so the first take is usable.']),
        ('Notion', 'Maths notes look printed.',
         ['Type /math in a Notion page and write the formula in LaTeX syntax.',
          'It renders as a clean equation, so your notes read like the textbook does.']),
    ],
    closer=['Focus mode blocks every app on my list for the', 'whole session. The phone stops being a', 'decision while the timer runs. My holy grail.'],
    promo=PROMO_STORE_NAME,
    only={int(a) for a in sys.argv[1:]} or None)
