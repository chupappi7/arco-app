#!/usr/bin/env python3
"""type-less-4: tools pillar in the photo look (_tools_photo).

  hook      "i barely type anymore / these 5 tools do it for me", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    ChatGPT, Superwhisper, Granola, Loom. ChatGPT is the one LLM. Every
            point checked against every earlier generator: none taught before.
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-type-less-4.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='type-less-4',
    hook=['i barely type anymore', 'these 5 tools do it for me'],
    theme='focus',
    bgs=[
        'bg-h46.jpg',    # hook         desk-city-day
        'bg-h38.jpg',    # ARCO         supercars-dusk
        'bg-h19.jpg',    # ChatGPT      lounge-day
        'bg-n04.jpg',    # Superwhisper desk-empty-day villa-day
        'bg-h32.jpg',    # Granola      window-silhouette
        'bg-h35.jpg',    # Loom         supercars-dusk
    ],
    arco=['Focus mode blocks every app on my', 'list for the whole session.', '', 'The phone stops being a decision', 'while the timer runs.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['Tap the mic in the ChatGPT message box and it types out what you say with the punctuation in.',
          'A long prompt takes as long as it takes to say, not to type.']),
        ('Superwhisper',
         ['Superwhisper modes rewrite what you say as an email or a note before it lands in the app.',
          'You talk the way you think and the text comes out ready to send.']),
        ('Granola',
         ['Granola drafts the follow up email from the meeting it just took notes on.',
          'The recap goes out a minute after the call with nothing typed up.']),
        ('Loom',
         ['Loom writes the title, the summary and the chapters of a recording when you stop.',
          'The video goes out with its write up done and nothing typed under it.']),
    ],
)
