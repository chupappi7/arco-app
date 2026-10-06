#!/usr/bin/env python3
"""keep-five-9: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-07: ship-weekend-screens format, six tools posts
            with varied hooks; the app is named by its current store name,
            App Blocker & Focus: ARCO, on its slide and in the card's search
            line.
  hook      "the 5 apps i would keep / if i deleted everything else",
            from hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Claude, Obsidian, Figma, OpusClip.
            One LLM, rotated across the 2026-10-07 batch. The hook counts five apps, so the post carries five and runs to 7 slides.
  ARCO      Plan your day "Events · just time" chips: + New saves a reusable
            event, a tap places it on the timeline as an Event card
            (PlanDayPrototypeView). Pitched as the chip, not the burned
            remembered-time point.
  teaching  every tool point checked against the captions in tools/hooks.json.
  card      angle drawn once with next_arco_angle('planning') and frozen.
  photos    hook frame chosen so the batch's six hooks sit on six different
            scenes; app frames from the pick_bgs pool (band luma gate, no
            hook-only vibe, one person, no adjacent vibe, no frame shared
            with the post before).

Usage: python3 tools/gen-keep-five-9.py [slide numbers to redo]
"""
import sys
from _veiled_screens import PLAN_DAY
from _tools_screens import build, PROMO_STORE_NAME

build(
    topic='keep-five-9',
    hook=['the 5 apps i would keep', 'if i deleted everything else'],
    theme='planning',
    bgs=[
         'bg-n04.jpg',   # hook
         'bg-h32.jpg',   # ARCO
         'bg-h34.jpg',   # Claude
         'bg-h35.jpg',   # Obsidian
         'bg-h46.jpg',   # Figma
         'bg-h88.jpg',   # OpusClip
         'bg-n06.jpg',   # card
    ],
    arco=(PLAN_DAY, 'One tap books lunch.',
          'Save Lunch or Commute once as an event in Plan your day. Every day after, one tap blocks that time on the timeline.'),
    tools=[
        ('Claude', 'Your tool gets a link.',
         ['Hit Publish on an artifact Claude built and it gets a public link.',
          'The tracker or calculator runs for anyone who opens it, with nothing to host.']),
        ('Obsidian', 'Memos live in the note.',
         ['Turn on the Audio recorder core plugin and record from inside the note you are writing.',
          'The file saves in your vault and sits embedded right there, so the memo app can go.']),
        ('Figma', 'A frame becomes an app.',
         ['Paste a frame into Figma Make and describe how it should behave.',
          'It builds a working prototype from it, so you test the flow before any code.']),
        ('OpusClip', 'Ask for the clip you want.',
         ['Type what you are looking for into ClipAnything, like every time I talk about pricing.',
          'OpusClip cuts those moments out of the long video as clips ready to post.']),
    ],
    closer=['I manage all my tasks here and the day takes', '30 seconds to plan. Focus mode puts every', 'distraction away, and Blocked Hours does it on', 'a schedule.'],
    promo=PROMO_STORE_NAME,
    only={int(a) for a in sys.argv[1:]} or None)
