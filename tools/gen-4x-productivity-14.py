#!/usr/bin/env python3
"""4x-productivity-14: tools pillar in the photo look (_tools_photo).

  hook      "the tools i used to / 4x my productivity", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: the time it gives back inside a working day
  roster    Claude, Raycast, Linear, Descript. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-4x-productivity-14.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='4x-productivity-14',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
        'bg-h12.jpg',    # hook
        'bg-h01.jpg',    # ARCO
        'bg-h21.jpg',    # Claude
        'bg-h22.jpg',    # Raycast
        'bg-h24.jpg',    # Linear
        'bg-h29.jpg',    # Descript
    ],
    arco=['Every task I have gets a time on', "the day's timeline, not a list.", '', 'Blocked Hours shuts the feeds for', 'those windows without me asking.', '', 'My holy grail.'],
    tools=[
        ('Claude',
         ['A Claude project keeps your files and your standing instructions attached to the chat.',
          'You stop spending the first ten minutes of every session re-explaining your own work.']),
        ('Raycast',
         ['Raycast keeps everything you have copied in a searchable history behind one hotkey.',
          'The link you copied before lunch is still there instead of gone.']),
        ('Linear',
         ['Linear files an issue from the keyboard without opening a form or picking a project.',
          'The bug you spotted gets written down in the ten seconds you actually have.']),
        ('Descript',
         ['Descript edits the audio when you edit the transcript, so cutting a line deletes the sound.',
          'An hour of recording becomes a usable cut without opening a timeline.']),
    ])
