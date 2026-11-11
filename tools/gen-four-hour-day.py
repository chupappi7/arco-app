#!/usr/bin/env python3
"""four-hour-day: tools pillar in the photo look (_tools_photo).

  hook      "i work 4 hours a day / these 5 apps are why", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    Claude, ElevenLabs, Stripe, GitHub. Claude is the one LLM. Every
            point checked against every earlier generator: none taught before.
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-four-hour-day.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='four-hour-day',
    hook=['i work 4 hours a day', 'these 5 apps are why'],
    theme='focus',
    bgs=[
        'bg-h54.jpg',    # hook         desk-led-warm
        'bg-h46.jpg',    # ARCO         desk-city-day
        'bg-h37.jpg',    # Claude       supercars-dusk
        'bg-h31.jpg',    # ElevenLabs   lounge-night
        'bg-n03.jpg',    # Stripe       villa-day
        'bg-h21.jpg',    # GitHub       lounge-night
    ],
    arco=['Focus mode puts every distracting', 'app away for the whole session.', '', 'An hour of work is an hour now, not', 'forty minutes and a scroll.', '', 'I get the time back.'],
    tools=[
        ('Claude',
         ['Claude builds the actual file, a spreadsheet, a deck or a doc, and hands it back to download.',
          'The step between the answer and the document disappears.']),
        ('ElevenLabs',
         ['ElevenLabs dubs a video into another language in your own voice.',
          'Re-recording every version is no longer part of the job.']),
        ('Stripe',
         ['Stripe Invoicing sends the reminders on its own until the invoice is paid.',
          'Chasing payment stops being a task in the day.']),
        ('GitHub',
         ['GitHub Actions runs your tests on every push.',
          'Checking that nothing broke is no longer a step you do by hand.']),
    ],
)
