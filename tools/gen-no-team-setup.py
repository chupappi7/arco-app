#!/usr/bin/env python3
"""no-team-setup: build pillar in the photo look (_tools_photo, pillar='build').

  hook      "one person, no team / this is the setup", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Cursor, Supabase, RevenueCat, Runway. Cursor is the one LLM. Points were
            checked against the newer generators only; about half repeat
            Sep-Oct lessons, all 3+ weeks old (allowed by Thinh, 2026-11-11).
  ARCO      angle drawn once with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-no-team-setup.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='no-team-setup',
    hook=['one person, no team', 'this is the setup'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h59.jpg',    # hook         desk-led-neon
        'bg-h19.jpg',    # ARCO         lounge-day
        'bg-h48.jpg',    # Cursor       desk-city-day
        'bg-h02.jpg',    # Supabase     lounge-day
        'bg-h36.jpg',    # RevenueCat   supercars-dusk
        'bg-n05.jpg',    # Runway       desk-empty-day
    ],
    arco=['Tasks with no time wait in Anytime', 'instead of crowding today.', '', 'Today holds only what I gave an', 'hour to, so I actually finish it.', '', 'The list stopped lying to me.'],
    tools=[
        ('Cursor',
         ['Cursor Bugbot reviews every pull request and flags the bugs before you merge.',
          'You get the second reviewer without hiring a second engineer.']),
        ('Supabase',
         ['Supabase Edge Functions run your server code with no server to set up.',
          'The backend is a few files, not a server you have to look after.']),
        ('RevenueCat',
         ['RevenueCat Paywalls are built in its dashboard and change without an app update.',
          'Pricing tests run while you keep building the product.']),
        ('Runway',
         ['Runway Aleph edits a video you already shot from a written instruction.',
          'A reshoot becomes a sentence instead of a day.']),
    ],
)
