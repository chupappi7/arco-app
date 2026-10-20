#!/usr/bin/env python3
"""ten-x-13: tools pillar in the photo look (_tools_photo).

  hook      "how i 10x'd / my productivity", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: the step it removes, not the feature it ships
  roster    Cursor, Superwhisper, Airtable, Photoroom. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-ten-x-13.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ten-x-13',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=[
        'bg-h17.jpg',    # hook
        'bg-h05.jpg',    # ARCO
        'bg-h37.jpg',    # Cursor
        'bg-h49.jpg',    # Superwhisper
        'bg-n03.jpg',    # Airtable
        'bg-n05.jpg',    # Photoroom
    ],
    arco=['One button starts the block and', 'locks every app on the list.', '', 'No settings and no deciding, I am', 'in and the phone is out.', '', 'One tap and I am working.'],
    tools=[
        ('Cursor',
         ['Cursor edits across every file the change touches from a single instruction.',
          'The find-and-replace pass you used to do by hand stops existing.']),
        ('Superwhisper',
         ['Superwhisper types what you say into whatever window is in front of you.',
          'The blank-page stage of a first draft is gone; you talk and edit after.']),
        ('Airtable',
         ['An Airtable base gives you the table, the form and the views without a schema.',
          'You skip building a CRUD screen nobody outside the team will ever see.']),
        ('Photoroom',
         ['Photoroom cuts the background out on the phone in the second you take the shot.',
          'The round trip to a desktop editor disappears from the job.']),
    ])
