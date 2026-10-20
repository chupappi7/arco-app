#!/usr/bin/env python3
"""best-for-last-9: tools pillar in the photo look (_tools_photo).

  hook      "5 tools to stay productive / i saved the best for last", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: what it keeps you on task through
  roster    Claude, Endel, Obsidian, Make. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-best-for-last-9.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='best-for-last-9',
    hook=['5 tools to stay productive', 'i saved the best for last'],
    theme='focus',
    bgs=[
        'bg-h16.jpg',    # hook
        'bg-h04.jpg',    # ARCO
        'bg-h36.jpg',    # Claude
        'bg-h48.jpg',    # Endel
        'bg-h88.jpg',    # Obsidian
        'bg-n01.jpg',    # Make
    ],
    arco=['Every time I open TikTok the shield', 'comes up instead of the feed.', '', 'The reflex still happens, it just', 'turns into a reminder to lock in.', '', 'That is the whole app.'],
    tools=[
        ('Claude',
         ['Claude keeps the whole thread, so picking a task back up costs you a sentence.',
          'An interruption takes a minute out of the session instead of the rest of it.']),
        ('Endel',
         ['Endel generates the focus sound as you listen instead of playing a fixed playlist.',
          'Nothing ends halfway through, so there is no track change to break the session.']),
        ('Obsidian',
         ['Obsidian keeps every note as a plain markdown file in one folder on your disk.',
          'You find the note without leaving the app and losing the thread you were on.']),
        ('Make',
         ['Make runs the handoff between your tools on a schedule you set once.',
          'The job still happens on the afternoon you forget it exists.']),
    ])
