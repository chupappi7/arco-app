#!/usr/bin/env python3
"""use-for-life: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-19: arco.app had three posts left for a seven day
            week. Build/ship is the angle that breaks out (29.7% against the
            screen-time angle's 0%), so new volume goes here.
  hook      "5 apps i will use / for the rest of my life", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Claude, Obsidian, Raycast, Endel. Claude is the one LLM. The
            hook promises permanence, so the roster is the staples rather
            than whatever shipped this month.
  answers   the hook promises tools that outlast a trend, so every point is a
            reason the tool keeps working: context that persists, files you
            own, a clipboard that remembers, sound with nothing to pick.
  ARCO      angle v2, drawn once with next_arco_angle('planning') and frozen
            below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA, no
            adjacent vibe repeat, nothing shared with the post before.

Usage: python3 tools/gen-use-for-life.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='use-for-life',
    hook=['5 apps i will use', 'for the rest of my life'],
    theme='planning',
    bgs=[
         'bg-h11.jpg',    # hook
         'bg-h21.jpg',    # ARCO
         'bg-h22.jpg',    # Claude
         'bg-h24.jpg',    # Obsidian
         'bg-h29.jpg',    # Raycast
         'bg-h31.jpg',    # Endel
    ],
    arco=['Every task I have is in here and the', 'day gets planned in 30 seconds.', '',
          'Focus mode puts every distraction', 'away while I work.', '',
          'My holy grail.'],
    tools=[
        ('Claude',
         ['A Claude project keeps your files and your instructions attached to the chat itself.',
          'You stop re-explaining your own work at the top of every conversation.']),
        ('Obsidian',
         ['Obsidian keeps every note as a plain markdown file in a folder on your own disk.',
          'Nothing you wrote is locked inside a company that might shut the app down.']),
        ('Raycast',
         ['Raycast keeps a searchable history of everything you have copied, on one hotkey.',
          'The link you copied an hour ago is still there instead of overwritten.']),
        ('Endel',
         ['Endel generates focus sound as you listen instead of playing a fixed playlist.',
          'There is no track to choose and nothing runs out halfway through the session.']),
    ])
