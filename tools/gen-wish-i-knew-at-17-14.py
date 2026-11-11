#!/usr/bin/env python3
"""wish-i-knew-at-17-14: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i wish someone / showed me at 17", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it.
  roster    Perplexity, Notion, Obsidian, Canva. Perplexity is the one LLM.
  re-shoot of wish-i-knew-at-17, a top performer, on new frames; Canva, Notion slide swapped for a point not run in 21 days.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('study') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-wish-i-knew-at-17-14.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-14',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
        'bg-h67.jpg',    # hook         desk-led-neon
        'bg-h31.jpg',    # ARCO         lounge-night
        'bg-n01.jpg',    # Perplexity   villa-day
        'bg-h46.jpg',    # Notion       desk-city-day
        'bg-h29.jpg',    # Obsidian     supercars-dusk
        'bg-n04.jpg',    # Canva        villa-day
    ],
    arco=['I start a session and every app on', 'the list locks itself.', '', 'Four hours later the phone has not', 'been picked up once.', '', 'My holy grail.'],
    tools=[
        ('Perplexity',
         ['A finished thread turns into a Page, written up with its sources.',
          'A night of research on one topic ends as a link you can send.']),
        ('Notion',
         ['A Notion synced block shows the same content on several pages at once.',
          'Your timetable updates everywhere when you edit it once.']),
        ('Obsidian',
         ['Put a caret and an id after a line and you can link to that line.',
          'The essay points at the exact sentence, not the whole note.']),
        ('Canva',
         ['Canva Magic Media turns one sentence into an image for a slide.',
          'Every slide in a school project gets its own picture in seconds.']),
    ],
)
