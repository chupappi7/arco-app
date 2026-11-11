#!/usr/bin/env python3
"""4x-productivity-16: tools pillar in the photo look (_tools_photo).

  hook      "the tools i used to / 4x my productivity", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Gemini, Notion, Canva, Linear. Gemini is the one LLM. Every
            point checked against every earlier generator: none taught before.
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-4x-productivity-16.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='4x-productivity-16',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
        'bg-h62.jpg',    # hook         desk-led-neon
        'bg-h34.jpg',    # ARCO         desk-empty-day
        'bg-h52.jpg',    # Gemini       desk-city-day
        'bg-h45.jpg',    # Notion       window-silhouette
        'bg-h04.jpg',    # Canva        lounge-day
        'bg-h88.jpg',    # Linear       supercars-dusk
    ],
    arco=['I manage all my tasks here and plan', 'the day in 30 seconds.', '', 'Focus mode puts every distraction', 'away.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Gemini in Gmail summarises a long thread in a card at the top of it.',
          'Catching up on a thread takes a glance instead of ten minutes.']),
        ('Notion',
         ['Notion AI autofill fills a database column from what each page says.',
          'Tagging fifty rows by hand is no longer part of the week.']),
        ('Canva',
         ['Canva Bulk Create fills one template from a spreadsheet, a design per row.',
          'Fifty graphics take the time of making one.']),
        ('Linear',
         ['Linear Asks turns a request in a Slack thread into an issue.',
          'Requests stop getting lost in chat and land in the queue.']),
    ],
)
