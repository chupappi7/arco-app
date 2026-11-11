#!/usr/bin/env python3
"""ten-x-16: tools pillar in the photo look (_tools_photo).

  hook      "how i 10x'd / my productivity", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    Claude, Supabase, Runway, Superwhisper. Claude is the one LLM.
  re-shoot of ten-x-6, a top performer, on new frames; Claude slide swapped for a point not run in 21 days.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-ten-x-16.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ten-x-16',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=[
        'bg-h42.jpg',    # hook         jet-mountain
        'bg-n04.jpg',    # ARCO         villa-day
        'bg-h51.jpg',    # Claude       desk-city-day
        'bg-h38.jpg',    # Supabase     supercars-dusk
        'bg-h11.jpg',    # Runway       lounge-day
        'bg-h46.jpg',    # Superwhisper desk-city-day
    ],
    arco=['The block I am in sits on the Lock', 'Screen with the time left running.', '', 'I pick the phone up and it tells me', 'to get back to work.', '', 'My holy grail.'],
    tools=[
        ('Claude',
         ['Claude Research searches the web and your Google Drive together and cites both.',
          'The answer comes from your own docs and the web in one pass.']),
        ('Supabase',
         ['Cron runs a query on a schedule from inside the database itself.',
          'The nightly cleanup or the weekly digest needs no server at all.']),
        ('Runway',
         ['Describe a change to a finished clip and Aleph re-renders it.',
          'The shot becomes night, or loses the crowd, with no reshoot.']),
        ('Superwhisper',
         ['A vocabulary list teaches it the names and terms you actually use.',
          'Dictated text comes back spelled right with no correction pass.']),
    ],
)
