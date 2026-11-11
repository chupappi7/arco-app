#!/usr/bin/env python3
"""pay-double-3: tools pillar in the photo look (_tools_photo).

  hook      "5 tools / i would pay double for", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Claude, Notion, Captions, Cloudflare. Claude is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-pay-double-3.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='pay-double-3',
    hook=['5 tools', 'i would pay double for'],
    theme='planning',
    bgs=[
        'bg-h61.jpg',    # hook         desk-led-neon
        'bg-h34.jpg',    # ARCO         desk-empty-day
        'bg-h22.jpg',    # Claude       lounge-day
        'bg-h39.jpg',    # Notion       supercars-dusk
        'bg-h51.jpg',    # Captions     desk-city-day
        'bg-h21.jpg',    # Cloudflare   lounge-night
    ],
    arco=['The block I’m in sits on the Lock', 'Screen with the time left on it.', '', 'Picking up the phone shows the plan', 'before it shows a feed.', '', 'My holy grail.'],
    tools=[
        ('Claude',
         ['A Claude Code hook runs a command you choose every time it edits a file, like your formatter.',
          'Formatting and tests happen on their own instead of being a step you remember.']),
        ('Notion',
         ['A Notion button runs several steps in one click, like adding a page and filling its fields.',
          'A weekly review that took ten clicks now starts with one.']),
        ('Captions',
         ['Captions has a teleprompter that scrolls your script while you record.',
          'A take works the first time instead of the fifth.']),
        ('Cloudflare',
         ['Cloudflare R2 stores your files with no fee when people download them.',
          'A file that goes popular stops turning into a surprise bill.']),
    ],
)
