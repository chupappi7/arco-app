#!/usr/bin/env python3
"""pay-for-twelve-9: tools pillar in the photo look (_tools_photo).

  hook      "i pay for 12 apps / these 5 do all the work", from the approved pool, word for word.
  theme     business -- hook_pool.json binds it.
  roster    Gemini, Canva, Photoroom, Cloudflare. Gemini is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('business') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-pay-for-twelve-9.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='pay-for-twelve-9',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='business',
    bgs=[
        'bg-h16.jpg',    # hook         desk-person-night
        'bg-n06.jpg',    # ARCO         desk-empty-day
        'bg-h02.jpg',    # Gemini       lounge-day
        'bg-n05.jpg',    # Canva        desk-empty-day
        'bg-h49.jpg',    # Photoroom    desk-city-day
        'bg-n04.jpg',    # Cloudflare   villa-day
    ],
    arco=['Tasks without a time wait in Anytime', 'until the day has room for them.', '', 'Focus mode blocks the apps I chose', 'for exactly that block.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Paste a YouTube link into Gemini and it summarises the video with timestamps.',
          'A paid tool for video notes is no longer needed.']),
        ('Canva',
         ['Canva translates a whole design into another language in one click.',
          'Paying a translator for every flyer stops.']),
        ('Photoroom',
         ['Photoroom puts your product into a generated scene from one sentence.',
          'Paying for a product shoot or stock photos stops.']),
        ('Cloudflare',
         ['Cloudflare Tunnel puts a server on your laptop on the internet with no ports opened.',
          'The paid tunnel service for demos goes.']),
    ],
)
