#!/usr/bin/env python3
"""home-screen-five-2: tools pillar in the photo look (_tools_photo).

  hook      "the 5 apps on my home screen / everything else is in a folder",
            from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  lens      every tool point answers: why it earns a place on the home
            screen. A slot is paid for in taps per day, so each payoff is
            about the moment of reaching for the phone.
  roster    phone apps only, as in home-screen-five. Perplexity is the one
            LLM. Points not taught before: Perplexity on the Action button,
            Endel following heart rate, merging a pull request in the GitHub
            app, Loom recording the screen with the camera on.
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below.
  photos    hook chosen by hand from the unused hook frames so it is not a
            third window silhouette in a row; app frames by the gen-daily-batch
            rules with the cooldown raised to 3 posts.
  cta       none. Tools and build posts end on the fifth app: ARCO reads as
            one recommendation among peers, and the ask drew 2 comments on
            ~10.6k views (27 Oct - 9 Nov). Thinh, 2026-11-10.

Usage: python3 tools/gen-home-screen-five-2.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='home-screen-five-2',
    hook=['the 5 apps on my home screen', 'everything else is in a folder'],
    theme='focus',
    bgs=[
        'bg-h36.jpg',    # hook        supercars-dusk
        'bg-h05.jpg',    # ARCO        lounge-day
        'bg-h39.jpg',    # Perplexity  supercars-dusk
        'bg-h45.jpg',    # Endel       window-silhouette (the one person)
        'bg-h49.jpg',    # GitHub      desk-city-day
        'bg-h88.jpg',    # Loom        supercars-dusk
    ],
    arco=['I start a session and every app on', 'the list locks itself.', '', 'Four hours later the phone has not', 'been picked up once.', '', 'My holy grail.'],
    tools=[
        ('Perplexity',
         ['Perplexity can sit on the iPhone Action button and answer with sources from one press.',
          'The question gets asked the second you think of it, before a feed gets the tap.']),
        ('Endel',
         ['Endel reads my heart rate from the Apple Watch and shifts the sound with it.',
          'Starting to focus is one tap and the sound does the settling in.']),
        ('GitHub',
         ['The GitHub app shows the whole diff of a pull request and merges it from the phone.',
          'A one line fix ships from the queue at the coffee shop, not later at a desk.']),
        ('Loom',
         ['Loom on the iPhone records the screen with your camera in the corner.',
          'A walkthrough of the bug goes out in the time a message about it would take.']),
    ],
)
