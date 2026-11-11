#!/usr/bin/env python3
"""seven-day-build: build pillar in the photo look (_tools_photo).

  hook      "give me seven days / and i'd build it like this", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Cursor, Supabase, Stripe, TestFlight. Cursor is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-seven-day-build.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='seven-day-build',
    hook=['give me seven days', "and i'd build it like this"],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h74.jpg',    # hook         desk-led-neon
        'bg-h20.jpg',    # ARCO         lounge-day
        'bg-h36.jpg',    # Cursor       supercars-dusk
        'bg-h45.jpg',    # Supabase     window-silhouette
        'bg-h35.jpg',    # Stripe       supercars-dusk
        'bg-h01.jpg',    # TestFlight   lounge-day
    ],
    arco=['Every task I have gets a time on', "the day's timeline, not a list.", '', 'Blocked Hours shuts the feeds for', 'those windows without me asking.', '', 'My holy grail.'],
    tools=[
        ('Cursor',
         ['Cursor background agents work on a branch in the cloud while you keep editing.',
          'The side features get built while you do the main one.']),
        ('Supabase',
         ['Supabase branching gives each pull request its own copy of the database.',
          'A schema change gets tested without touching real data.']),
        ('Stripe',
         ['Every Stripe Payment Link comes with a QR code you can print or share.',
          'You take a payment before a checkout page exists.']),
        ('TestFlight',
         ['TestFlight testers send feedback by taking a screenshot inside the beta.',
          'Bug reports arrive with the screen attached.']),
    ],
)
