#!/usr/bin/env python3
"""pay-for-twelve-4: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-07: ship-weekend-screens format, six tools posts
            with varied hooks; the app is named by its current store name,
            App Blocker & Focus: ARCO, on its slide and in the card's search
            line.
  hook      "i pay for 12 apps / these 5 do all the work",
            from hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, ChatGPT, Notion, Supabase, PostHog.
            One LLM, rotated across the 2026-10-07 batch. The hook counts five apps, so the post carries five and runs to 7 slides.
  ARCO      Plan your day: the "Your day" bar sums every block as "Xh Ym booked",
            and with nothing left waiting the sheet reads "Your day is planned
            · N blocks · first up at 09:00" (PlanDayPrototypeView dayShape,
            allDone).
  teaching  every tool point checked against the captions in tools/hooks.json.
  card      angle drawn once with next_arco_angle('planning') and frozen.
  photos    hook frame chosen so the batch's six hooks sit on six different
            scenes; app frames from the pick_bgs pool (band luma gate, no
            hook-only vibe, one person, no adjacent vibe, no frame shared
            with the post before).

Usage: python3 tools/gen-pay-for-twelve-4.py [slide numbers to redo]
"""
import sys
from _veiled_screens import PLAN_DAY
from _tools_screens import build, PROMO_STORE_NAME

build(
    topic='pay-for-twelve-4',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='planning',
    bgs=[
         'bg-h08.jpg',   # hook
         'bg-h24.jpg',   # ARCO
         'bg-h29.jpg',   # ChatGPT
         'bg-h31.jpg',   # Notion
         'bg-h50.jpg',   # Supabase
         'bg-h37.jpg',   # PostHog
         'bg-h45.jpg',   # card
    ],
    arco=(PLAN_DAY, 'Your day, added up.',
          'Plan your day draws every block on one 24 hour bar and adds up the hours booked. Once nothing is waiting, it tells you what is first up.'),
    tools=[
        ('ChatGPT', 'Canva runs in the chat.',
         ['Start a message with Canva and ChatGPT runs the Canva app right in the conversation.',
          'The drafts show up in the chat and one tap opens your pick in Canva to edit.']),
        ('Notion', 'Plans open offline.',
         ['Mark a page Available offline and Notion keeps a copy on the device.',
          'You edit it on the train and the changes sync once you are back online.']),
        ('Supabase', 'A sheet becomes a table.',
         ['Import a CSV in the Supabase table editor and every row lands in a real table.',
          'The list you kept in a sheet is live data for the app, with nothing typed twice.']),
        ('PostHog', 'See where people click.',
         ['Open the PostHog toolbar on your live site and switch on the heatmap.',
          'Every click shows up over the page itself, so you see which button gets ignored.']),
    ],
    closer=['I manage all my tasks here and plan the day in', '30 seconds. Focus mode puts every distraction', 'away. My holy grail.'],
    promo=PROMO_STORE_NAME,
    only={int(a) for a in sys.argv[1:]} or None)
