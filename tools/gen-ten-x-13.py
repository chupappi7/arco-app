#!/usr/bin/env python3
"""ten-x-13: how i 10x'd / my productivity.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    the step it removes, not the feature it ships.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle a5 [focus,study,build], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _tools_photo import main

main(
    topic='ten-x-13',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=['bg-h61.jpg',   # hook         desk-led-neon      luma 31
         'bg-h31.jpg',   # ARCO         lounge-night       luma 20
         'bg-h29.jpg',   # Cursor       supercars-dusk     luma 21
         'bg-h24.jpg',   # Make         lounge-night       luma 48
         'bg-h52.jpg',   # Descript     desk-city-day      luma 64
         'bg-n05.jpg'],  # Framer       desk-empty-day     luma 51
    arco=['One button starts the block and', 'locks every app on the list.',
          '', 'No settings and no deciding, I am',
          'in and the phone is out.', '', 'One tap and I am working.'],
    tools=[
        ('Cursor',
         ['Cursor Tab predicts your next edit across the file instead of the next word.',
          'The step it removes is explaining what you were already about to do.']),
        ('Make',
         ['A Make scenario shows the data moving through every step while it runs.',
          'Reading a log to find out where it broke stops being part of the job.']),
        ('Descript',
         ['Descript edits the video by deleting words out of the transcript.',
          'Scrubbing a timeline to find the cut is a step that stops existing.']),
        ('Framer',
         ['Framer publishes the live site from the same canvas you designed it on.',
          'The handoff from design to build is not faster, it is simply gone.']),
    ])
