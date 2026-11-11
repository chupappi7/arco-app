#!/usr/bin/env python3
"""ten-x-15: tools pillar in the photo look (_tools_photo).

  hook      "how i 10x'd / my productivity", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    Gemini, Raycast, Zapier, Higgsfield. Gemini is the one LLM.
  re-shoot of ten-x-3, a top performer, on new frames.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-ten-x-15.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ten-x-15',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=[
        'bg-h12.jpg',    # hook         desk-person-night
        'bg-h39.jpg',    # ARCO         supercars-dusk
        'bg-h02.jpg',    # Gemini       lounge-day
        'bg-h48.jpg',    # Raycast      desk-city-day
        'bg-h21.jpg',    # Zapier       lounge-night
        'bg-h19.jpg',    # Higgsfield   lounge-day
    ],
    arco=['One button starts the block and', 'locks every app on the list.', '', 'No settings and no deciding, I am', 'in and the phone is out.', '', 'One tap and I am working.'],
    tools=[
        ('Gemini',
         ['A Live session can see your screen while you share it.',
          'You ask about the error in front of you instead of retyping it.']),
        ('Raycast',
         ['Drop your own shell script in and it becomes a command with its own keyword.',
          'The thing you opened the terminal for now runs from the search bar.']),
        ('Zapier',
         ['A Digest step collects items and releases them as one message on a schedule.',
          'Ten alerts through the week arrive as one summary on friday.']),
        ('Higgsfield',
         ['One prompt runs as a batch and comes back as several finished frames.',
          'You pick the shot instead of rewriting the prompt ten times.']),
    ],
)
