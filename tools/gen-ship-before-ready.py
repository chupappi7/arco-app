#!/usr/bin/env python3
"""ship-before-ready: build pillar in the photo look (_tools_photo, pillar='build').

  hook      "5 tools to ship / before you feel ready", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Antigravity, TestFlight, Firebase, Framer. Antigravity is the one LLM. Points were
            checked against the newer generators only; about half repeat
            Sep-Oct lessons, all 3+ weeks old (allowed by Thinh, 2026-11-11).
  ARCO      angle drawn once with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-ship-before-ready.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ship-before-ready',
    hook=['5 tools to ship', 'before you feel ready'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h55.jpg',    # hook         desk-led-warm
        'bg-n05.jpg',    # ARCO         desk-empty-day
        'bg-h88.jpg',    # Antigravity  supercars-dusk
        'bg-h04.jpg',    # TestFlight   lounge-day
        'bg-h48.jpg',    # Firebase     desk-city-day
        'bg-h29.jpg',    # Framer       supercars-dusk
    ],
    arco=['Tasks without a time wait in Anytime', 'until the day has room for them.', '', 'Focus mode blocks the apps I chose', 'for exactly that block.', '', 'My holy grail.'],
    tools=[
        ('Antigravity',
         ['The Antigravity agent manager runs several agents on separate tasks at once.',
          'Three features move while you review the first.']),
        ('TestFlight',
         ['A TestFlight public link lets anyone join the beta without you adding their email.',
          'Your first testers come from one post, not a list of addresses.']),
        ('Firebase',
         ['Firebase Crashlytics reports each crash with the line of code it happened on.',
          'You ship the rough version knowing a crash will say where.']),
        ('Framer',
         ['A Framer site goes live on a free framer.website address.',
          'The landing page exists before the app does.']),
    ],
)
