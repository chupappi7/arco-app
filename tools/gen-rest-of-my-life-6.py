#!/usr/bin/env python3
"""rest-of-my-life-6: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i will use / for the rest of my life", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Gemini, GitHub, Figma, Raycast. Gemini is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-rest-of-my-life-6.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='rest-of-my-life-6',
    hook=['5 apps i will use', 'for the rest of my life'],
    theme='planning',
    bgs=[
        'bg-h70.jpg',    # hook         desk-led-neon
        'bg-h11.jpg',    # ARCO         lounge-day
        'bg-h31.jpg',    # Gemini       lounge-night
        'bg-h45.jpg',    # GitHub       window-silhouette
        'bg-n05.jpg',    # Figma        desk-empty-day
        'bg-h36.jpg',    # Raycast      supercars-dusk
    ],
    arco=['The block I am in sits on the Lock', 'Screen with the time left running.', '', 'I pick the phone up and it tells me', 'to get back to work.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Gemini in Google Sheets writes a formula from a sentence.',
          'Spreadsheets stay useful long after you forget the syntax.']),
        ('GitHub',
         ['A GitHub Project turns your issues into a board with your own fields and views.',
          'The roadmap lives next to the code for as long as the repo does.']),
        ('Figma',
         ['Figma variables switch a whole design between light and dark with one setting.',
          'Design decisions live in one place and outlast every redesign.']),
        ('Raycast',
         ['Raycast Quicklinks search any site straight from the launcher.',
          'Looking something up skips the browser tab and the feed beside it.']),
    ],
)
