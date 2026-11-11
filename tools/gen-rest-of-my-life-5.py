#!/usr/bin/env python3
"""rest-of-my-life-5: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i will use / for the rest of my life", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Claude, Notion, Raycast, CleanShot X. Claude is the one LLM. Every
            point checked against every earlier generator: none taught before.
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-rest-of-my-life-5.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='rest-of-my-life-5',
    hook=['5 apps i will use', 'for the rest of my life'],
    theme='planning',
    bgs=[
        'bg-h53.jpg',    # hook         desk-led-warm
        'bg-n06.jpg',    # ARCO         desk-empty-day
        'bg-h31.jpg',    # Claude       lounge-night
        'bg-h29.jpg',    # Notion       supercars-dusk
        'bg-h34.jpg',    # Raycast      desk-empty-day
        'bg-h45.jpg',    # CleanShot X  window-silhouette
    ],
    arco=['Habits take a real slot on the day,', 'the same as any task.', '', 'Mine lasted past the first month', 'because the day made room for it.', '', 'That is why they finally stuck.'],
    tools=[
        ('Claude',
         ['Connect Google Calendar and Claude plans the week around the meetings already in it.',
          'The plan you get fits the real week, not an empty one.']),
        ('Notion',
         ['Notion Mail sorts the inbox into views by rules you write in plain words.',
          'The mail that needs you is the first thing you see.']),
        ('Raycast',
         ['The Raycast calculator converts currencies and time zones as you type the question.',
          'Scheduling a call across countries stops being a search.']),
        ('CleanShot X',
         ['CleanShot X scrolling capture saves a whole long page as one image.',
          'A full thread or a receipt is one shot instead of six.']),
    ],
)
