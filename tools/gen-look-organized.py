#!/usr/bin/env python3
"""look-organized: tools pillar in the photo look (_tools_photo).

  hook      "5 apps / that make me look organized", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    ChatGPT, Granola, Notion, Linear. ChatGPT is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-look-organized.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='look-organized',
    hook=['5 apps', 'that make me look organized'],
    theme='planning',
    bgs=[
        'bg-h75.jpg',    # hook         desk-led-neon
        'bg-h51.jpg',    # ARCO         desk-city-day
        'bg-h19.jpg',    # ChatGPT      lounge-day
        'bg-h37.jpg',    # Granola      supercars-dusk
        'bg-h21.jpg',    # Notion       lounge-night
        'bg-h52.jpg',    # Linear       desk-city-day
    ],
    arco=['I manage all my tasks here and plan', 'the day in 30 seconds.', '', 'Focus mode puts every distraction', 'away.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['ChatGPT memory keeps your preferences and projects from one chat to the next.',
          'You stop explaining your situation every time you ask.']),
        ('Granola',
         ['Ask Granola what was agreed and it answers across every meeting in a folder.',
          'Nobody has to remember who promised what.']),
        ('Notion',
         ['A Notion chart turns a database into a live chart on the page.',
          'Progress stays visible without anyone updating a slide.']),
        ('Linear',
         ['Linear project updates post a weekly status with a health flag.',
          'People know where things stand without asking you.']),
    ],
)
