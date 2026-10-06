#!/usr/bin/env python3
"""4x-productivity-11: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-07: ship-weekend-screens format, six tools posts
            with varied hooks; the app is named by its current store name,
            App Blocker & Focus: ARCO, on its slide and in the card's search
            line.
  hook      "the tools i used to / 4x my productivity",
            from hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Manus, Vercel, CleanShot X.
            One LLM, rotated across the 2026-10-07 batch.
  ARCO      habit page ON TIME: four weeks as on time / late (15+ min) / missed,
            and onTimeFix: "Usually starts 25 min after 07:00. Moving the slot
            to 07:25 turns most of the late ones green." (HabitPage).
  teaching  every tool point checked against the captions in tools/hooks.json.
  card      angle drawn once with next_arco_angle('planning') and frozen.
  photos    hook frame chosen so the batch's six hooks sit on six different
            scenes; app frames from the pick_bgs pool (band luma gate, no
            hook-only vibe, one person, no adjacent vibe, no frame shared
            with the post before).

Usage: python3 tools/gen-4x-productivity-11.py [slide numbers to redo]
"""
import sys
from _veiled_screens import TODAY
from _tools_screens import build, PROMO_STORE_NAME

build(
    topic='4x-productivity-11',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
         'bg-h49.jpg',   # hook
         'bg-h24.jpg',   # ARCO
         'bg-h29.jpg',   # Manus
         'bg-h31.jpg',   # Vercel
         'bg-h37.jpg',   # CleanShot X
         'bg-h45.jpg',   # card
    ],
    arco=(TODAY, 'It tells you when to move a habit.',
          'Open a habit from Today to see four weeks split into on time, late and missed. If you keep starting late, it names the slot that fixes it.'),
    tools=[
        ('Manus', 'Email it the work.',
         ['Manus gives you its own email address. Forward a thread and it starts on the task inside.',
          'The research a client asked for comes back to your inbox as a finished file.']),
        ('Vercel', 'Your keys come down in one line.',
         ['Run vercel env pull and every environment variable from the dashboard lands in .env.local.',
          'A new laptop runs the project in a minute, with no keys pasted by hand.']),
        ('CleanShot X', 'Screenshots come out post ready.',
         ['Open a capture in the Background tool and it sits on a padded backdrop with a shadow.',
          'The product shot for the launch post is done without opening a design app.']),
    ],
    closer=['Every task I have is in here and the day gets', 'planned in 30 seconds. Focus mode puts every', 'distraction away while I work. My holy grail.'],
    promo=PROMO_STORE_NAME,
    only={int(a) for a in sys.argv[1:]} or None)
