#!/usr/bin/env python3
"""students-sleeping-on: tools pillar in the photo look (_tools_photo).

  hook      "5 apps students / are sleeping on", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it.
  roster    Claude, GitHub, Figma, Make. Claude is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('study') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-students-sleeping-on.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='students-sleeping-on',
    hook=['5 apps students', 'are sleeping on'],
    theme='study',
    bgs=[
        'bg-h43.jpg',    # hook         jet-mountain
        'bg-h52.jpg',    # ARCO         desk-city-day
        'bg-h31.jpg',    # Claude       lounge-night
        'bg-h19.jpg',    # GitHub       lounge-day
        'bg-h50.jpg',    # Figma        desk-city-day
        'bg-h04.jpg',    # Make         lounge-day
    ],
    arco=['Focus mode puts every distracting', 'app away for the whole session.', '', 'An hour of work is an hour now, not', 'forty minutes and a scroll.', '', 'I get the time back.'],
    tools=[
        ('Claude',
         ['A Claude artifact turns one prompt into a small working app, like a quiz you can share by link.',
          'The study group gets an interactive quiz from one message.']),
        ('GitHub',
         ['GitHub Codespaces opens a full coding setup in the browser, with free hours every month.',
          'A school laptop can run real projects.']),
        ('Figma',
         ['Figma Sites publishes a design as a live website.',
          'Your portfolio is online before applications open.']),
        ('Make',
         ['The Make free plan runs 1,000 operations a month.',
          'Learning automation costs nothing while you are still learning it.']),
    ],
)
