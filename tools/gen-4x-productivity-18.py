#!/usr/bin/env python3
"""4x-productivity-18: tools pillar in the photo look (_tools_photo).

  hook      "the tools i used to / 4x my productivity", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Antigravity, ElevenLabs, Linear, Cloudflare. Antigravity is the one LLM.
  re-shoot of 4x-productivity-8, a top performer, on new frames; Cloudflare, ElevenLabs slide swapped for a point not run in 21 days.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-4x-productivity-18.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='4x-productivity-18',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
        'bg-h17.jpg',    # hook         desk-person-night
        'bg-h05.jpg',    # ARCO         lounge-day
        'bg-h21.jpg',    # Antigravity  lounge-night
        'bg-h51.jpg',    # ElevenLabs   desk-city-day
        'bg-h31.jpg',    # Linear       lounge-night
        'bg-h48.jpg',    # Cloudflare   desk-city-day
    ],
    arco=['The block I’m in sits on the Lock', 'Screen with the time left on it.', '', 'Picking up the phone shows the plan', 'before it shows a feed.', '', 'My holy grail.'],
    tools=[
        ('Antigravity',
         ['The agent writes its plan as a doc you comment on before it codes.',
          'A wrong assumption is fixed in a note, not in a finished diff.']),
        ('ElevenLabs',
         ['ElevenLabs Voice Changer keeps your delivery and swaps in another voice.',
          'A take recorded tired still sounds like the brand.']),
        ('Linear',
         ['Sentry crashes file themselves in Linear with the stack trace on.',
          'Bugs are in the backlog before anyone has reported them.']),
        ('Cloudflare',
         ['Cloudflare Web Analytics counts visitors without cookies or a heavy script.',
          'You see the traffic without slowing the page down.']),
    ],
)
