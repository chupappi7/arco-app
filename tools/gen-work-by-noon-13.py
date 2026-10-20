#!/usr/bin/env python3
"""work-by-noon-13: tools pillar in the photo look (_tools_photo).

  hook      "the tools i use to do / a full day of work by noon", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: the hours it compresses before noon
  roster    Codex, Granola, Zapier, Canva. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-work-by-noon-13.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='work-by-noon-13',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=[
        'bg-h14.jpg',    # hook
        'bg-h02.jpg',    # ARCO
        'bg-h31.jpg',    # Codex
        'bg-h34.jpg',    # Granola
        'bg-h35.jpg',    # Zapier
        'bg-h46.jpg',    # Canva
    ],
    arco=['Tasks without a time wait in Anytime', 'until the day has room for them.', '', 'Focus mode blocks the apps I chose', 'for exactly that block.', '', 'My holy grail.'],
    tools=[
        ('Codex',
         ['Codex applies one instruction across every file in the repo that needs it.',
          'The rename that used to eat a morning lands before the coffee goes cold.']),
        ('Granola',
         ['Granola listens to the call and writes the notes against your own agenda.',
          'You leave the meeting with the actions already written instead of a blank page.']),
        ('Zapier',
         ['Zapier moves the record between two apps the moment it changes in the first.',
          'Nobody opens a spreadsheet at nine to copy yesterday into today.']),
        ('Canva',
         ['A Canva brand kit locks the fonts and colours so a new graphic starts filled in.',
          'The post that needed a designer is done in the gap before your first call.']),
    ])
