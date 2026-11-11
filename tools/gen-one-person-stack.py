#!/usr/bin/env python3
"""one-person-stack: build pillar in the photo look (_tools_photo).

  hook      "the whole stack / for a one person app", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Cursor, Supabase, Firebase, Vercel. Cursor is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-one-person-stack.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='one-person-stack',
    hook=['the whole stack', 'for a one person app'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h65.jpg',    # hook         desk-led-neon
        'bg-h50.jpg',    # ARCO         desk-city-day
        'bg-h02.jpg',    # Cursor       lounge-day
        'bg-h35.jpg',    # Supabase     supercars-dusk
        'bg-h51.jpg',    # Firebase     desk-city-day
        'bg-n06.jpg',    # Vercel       desk-empty-day
    ],
    arco=['I plan the whole day before I start', 'it, so nothing waits on a decision.', '', 'I get more done by noon than I used', 'to manage by six.', '', 'The plan does the deciding.'],
    tools=[
        ('Cursor',
         ['A Cursor rules file tells the agent your conventions for every chat in the project.',
          'The code it writes already looks like the code you write.']),
        ('Supabase',
         ['Supabase Realtime pushes database changes to every open screen as they happen.',
          'Live updates work without building a socket server.']),
        ('Firebase',
         ['Firebase Remote Config changes a value in the live app without a new release.',
          'A wrong price or label gets fixed in a minute, not a review cycle.']),
        ('Vercel',
         ['Vercel keeps every deploy, and Instant Rollback puts the last good one back live.',
          'A broken release is undone in one click.']),
    ],
)
