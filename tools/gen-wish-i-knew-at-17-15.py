#!/usr/bin/env python3
"""wish-i-knew-at-17-15: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i wish someone / showed me at 17", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it.
  roster    Perplexity, Obsidian, CapCut, Higgsfield. Perplexity is the one LLM.
  re-shoot of wish-i-knew-at-17-4, a top performer, on new frames.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('study') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-wish-i-knew-at-17-15.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-15',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
        'bg-h76.jpg',    # hook         desk-led-neon
        'bg-h36.jpg',    # ARCO         supercars-dusk
        'bg-h48.jpg',    # Perplexity   desk-city-day
        'bg-n03.jpg',    # Obsidian     villa-day
        'bg-n05.jpg',    # CapCut       desk-empty-day
        'bg-h37.jpg',    # Higgsfield   supercars-dusk
    ],
    arco=['Focus mode blocks every app on my', 'list for the whole session.', '', 'The phone stops being a decision', 'while the timer runs.', '', 'My holy grail.'],
    tools=[
        ('Perplexity',
         ['Deep research runs dozens of searches and writes the report.',
          'A topic that took an evening comes back sourced in minutes.']),
        ('Obsidian',
         ['The web clipper saves a page as a note with the title and url on it.',
          'An article stops living in a tab and links like any other note.']),
        ('CapCut',
         ['Long video to shorts cuts a full recording into captioned clips.',
          'One 20 minute video becomes a week of posts without scrubbing.']),
        ('Higgsfield',
         ['Speak takes a still character and a script and it says the lines.',
          'A presenter for the video exists with nobody on camera.']),
    ],
)
