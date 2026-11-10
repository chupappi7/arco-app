#!/usr/bin/env python3
"""ship-weekend-6: build pillar in the photo look (_tools_photo, pillar='build').

  hook      "how i ship in a weekend / what used to take a month", from the
            approved pool, word for word. Best median of the eligible hooks
            (842 over 21 outings) and 50 posts since it last ran.
  theme     build -- hook_pool.json binds it.
  lens      every tool point answers: the stage of shipping it collapses.
            Plan (Claude), sign-in (Firebase), paywall (Superwall), beta
            (TestFlight), in build order.
  roster    Claude is the one LLM. Every point checked against every caption
            in tools/hooks.json: Claude plan mode, Firebase Authentication,
            Superwall placements and TestFlight's What to Test note have not
            been taught before.
  ARCO      angle drawn once with next_arco_angle('build') and frozen below.
  photos    pick_bgs from gen-daily-batch on 2026-11-10.
  cta       none. Tools and build posts end on the fifth app: ARCO reads as
            one recommendation among peers, and the ask drew 2 comments on
            ~10.6k views (27 Oct - 9 Nov). Thinh, 2026-11-10.

Usage: python3 tools/gen-ship-weekend-6.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ship-weekend-6',
    hook=['how i ship in a weekend', 'what used to take a month'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h37.jpg',    # hook        supercars-dusk
        'bg-h01.jpg',    # ARCO        lounge-day
        'bg-h21.jpg',    # Claude      lounge-night
        'bg-h22.jpg',    # Firebase    lounge-day
        'bg-h24.jpg',    # Superwall   lounge-night
        'bg-h29.jpg',    # TestFlight  supercars-dusk
    ],
    arco=['One button starts the block and', 'locks every app on the list.', '', 'No settings and no deciding, I am', 'in and the phone is out.', '', 'One tap and I am working.'],
    tools=[
        ('Claude',
         ['Claude Code plan mode reads the project and writes the plan before it touches a file.',
          'You fix the approach in one message instead of undoing a day of edits.']),
        ('Firebase',
         ['Firebase Authentication gives you Apple, Google and email sign in from one SDK.',
          'The login screen takes an afternoon instead of the first week.']),
        ('Superwall',
         ['Superwall decides which paywall shows at which moment in the app from its dashboard.',
          'You test the paywall while you build the next feature, with no new release.']),
        ('TestFlight',
         ['Every TestFlight build carries a What to Test note that testers read first.',
          'Feedback comes back about the change you made, not the whole app.']),
    ],
)
