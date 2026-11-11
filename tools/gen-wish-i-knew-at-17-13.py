#!/usr/bin/env python3
"""wish-i-knew-at-17-13: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i wish someone / showed me at 17", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it.
  roster    Gemini, Obsidian, Notion, GitHub. Gemini is the one LLM. Every
            point checked against every earlier generator: none taught before.
  ARCO      angle drawn once with next_arco_angle('study') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-wish-i-knew-at-17-13.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-13',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
        'bg-h88.jpg',    # hook         supercars-dusk
        'bg-n05.jpg',    # ARCO         desk-empty-day
        'bg-h20.jpg',    # Gemini       lounge-day
        'bg-h49.jpg',    # Obsidian     desk-city-day
        'bg-n03.jpg',    # Notion       villa-day
        'bg-h02.jpg',    # GitHub       lounge-day
    ],
    arco=['I start a session and every app on', 'the list locks itself.', '', 'Four hours later the phone has not', 'been picked up once.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Upload your notes to Gemini and Audio Overview turns them into a podcast with two hosts.',
          'Revision happens on the bus with headphones in, not only at a desk.']),
        ('Obsidian',
         ['Obsidian Canvas lays your notes out as cards you connect on one board.',
          'A whole topic fits on one screen and the gaps between ideas show.']),
        ('Notion',
         ['Any Notion page goes live as a website from the Publish tab.',
          'Your projects are online as a portfolio years before anyone asks for one.']),
        ('GitHub',
         ['The GitHub Student Developer Pack unlocks paid developer tools free with a school email.',
          'You learn on the same tools working developers pay for.']),
    ],
)
