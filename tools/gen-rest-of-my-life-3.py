#!/usr/bin/env python3
"""rest-of-my-life-3: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-07: ship-weekend-screens format, six tools posts
            with varied hooks; the app is named by its current store name,
            App Blocker & Focus: ARCO, on its slide and in the card's search
            line.
  hook      "5 apps i will use / for the rest of my life",
            from hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Gemini, GitHub, Framer, Cloudflare.
            One LLM, rotated across the 2026-10-07 batch. The hook counts five apps, so the post carries five and runs to 7 slides.
  ARCO      Insights "Best streak" tile: top three current runs as rings, each
            closing at that habit's own best (InsightsPrototypeView
            streakTile, on by default).
  teaching  every tool point checked against the captions in tools/hooks.json.
  card      angle drawn once with next_arco_angle('planning') and frozen.
  photos    hook frame chosen so the batch's six hooks sit on six different
            scenes; app frames from the pick_bgs pool (band luma gate, no
            hook-only vibe, one person, no adjacent vibe, no frame shared
            with the post before).

Usage: python3 tools/gen-rest-of-my-life-3.py [slide numbers to redo]
"""
import sys
from _veiled_screens import GOOD_HABITS
from _tools_screens import build, PROMO_STORE_NAME

build(
    topic='rest-of-my-life-3',
    hook=['5 apps i will use', 'for the rest of my life'],
    theme='planning',
    bgs=[
         'bg-h19.jpg',   # hook
         'bg-h32.jpg',   # ARCO
         'bg-h34.jpg',   # Gemini
         'bg-h35.jpg',   # GitHub
         'bg-h46.jpg',   # Framer
         'bg-h88.jpg',   # Cloudflare
         'bg-n01.jpg',   # card
    ],
    arco=(GOOD_HABITS, 'Streaks chase records.',
          'Best streak on Insights rings your top three habits. Each ring closes at that habit’s own best, so you see how close a run is.'),
    tools=[
        ('Gemini', 'Edit a photo in words.',
         ['Upload a photo to Gemini and type the change, like a new jacket or a beach behind you.',
          'The face stays the same person, so one good photo covers every version you want.']),
        ('GitHub', 'Issues file themselves.',
         ['Turn on the Auto-add workflow in a GitHub Project with a filter like label:bug.',
          'Every matching issue lands on the board, so nothing waits for you to sort it.']),
        ('Framer', 'A layout from a sentence.',
         ['Describe the page to Wireframer in Framer and it lays out the sections.',
          'You start from a real responsive page you can edit, not a blank canvas.']),
        ('Cloudflare', 'Bots out, no puzzles.',
         ['Put Cloudflare Turnstile on your signup form instead of a CAPTCHA.',
          'Real people sign up without clicking traffic lights, and the bots stay out.']),
    ],
    closer=['All my tasks live here and I plan the whole', 'day in 30 seconds. Focus mode puts every', 'distraction away. My holy grail.'],
    promo=PROMO_STORE_NAME,
    only={int(a) for a in sys.argv[1:]} or None)
