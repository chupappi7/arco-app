#!/usr/bin/env python3
"""ship-weekend-8: build pillar in the photo look (_tools_photo).

  hook      "how i ship in a weekend / what used to take a month", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Codex, Supabase, Figma, TestFlight. Codex is the one LLM.
  re-shoot of weekend-not-month, a top performer, on new frames; TestFlight slide swapped for a point not run in 21 days.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-ship-weekend-8.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ship-weekend-8',
    hook=['how i ship in a weekend', 'what used to take a month'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-n10.jpg',    # hook         desk-person-night
        'bg-n01.jpg',    # ARCO         villa-day
        'bg-h29.jpg',    # Codex        supercars-dusk
        'bg-h02.jpg',    # Supabase     lounge-day
        'bg-h49.jpg',    # Figma        desk-city-day
        'bg-h04.jpg',    # TestFlight   lounge-day
    ],
    arco=['Every task has a time and the block', 'that protects it is the same app.', '', 'I stopped running a planner and a', 'blocker that knew nothing about', 'each other.', '', 'One app, one day.'],
    tools=[
        ('Codex',
         ['An AGENTS.md file in the repo tells it how to build and test.',
          'It runs your commands instead of guessing on every new task.']),
        ('Supabase',
         ['Access rules live in the database itself, not in your app code.',
          'A user only ever sees their own rows, whatever calls the api.']),
        ('Figma',
         ['Variables hold your colours and a mode swaps the whole set.',
          'Every screen switches to dark mode without redrawing anything.']),
        ('TestFlight',
         ['A TestFlight build reaches internal testers minutes after upload, with no review.',
          'The first test on a friend’s phone happens the same evening.']),
    ],
)
