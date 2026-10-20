#!/usr/bin/env python3
"""use-for-life-2: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i will use / for the rest of my life", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: why it outlasts a trend
  roster    Manus, Vercel, ElevenLabs, Stripe. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-use-for-life-2.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='use-for-life-2',
    hook=['5 apps i will use', 'for the rest of my life'],
    theme='planning',
    bgs=[
        'bg-h41.jpg',    # hook
        'bg-h20.jpg',    # ARCO
        'bg-h52.jpg',    # Manus
        'bg-h02.jpg',    # Vercel
        'bg-h24.jpg',    # ElevenLabs
        'bg-h29.jpg',    # Stripe
    ],
    arco=['Every task has a time and the block', 'that protects it is the same app.', '', 'I stopped running a planner and a', 'blocker that knew nothing about', 'each other.', '', 'One app, one day.'],
    tools=[
        ('Manus',
         ['Manus takes a goal and runs the steps itself, reporting what it did.',
          'What it automates is your process, which outlives whichever model is underneath.']),
        ('Vercel',
         ['Vercel builds and deploys from the branch every time you push to it.',
          'Shipping stays one command no matter which framework you move to next.']),
        ('ElevenLabs',
         ['ElevenLabs reads a script in a voice that holds up for a whole video.',
          'The voice is yours to reuse long after the tool you made it in changes.']),
        ('Stripe',
         ['Stripe handles the card, the tax and the failed payment retry for you.',
          'Taking money is the part of a business that never goes out of fashion.']),
    ])
