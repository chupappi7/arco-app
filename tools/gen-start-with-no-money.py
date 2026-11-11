#!/usr/bin/env python3
"""start-with-no-money: build pillar in the photo look (_tools_photo).

  hook      "how i'd start at 19 / with no money", from the approved pool, word for word.
  theme     business -- hook_pool.json binds it.
  roster    Manus, Cloudflare, Firebase, Stripe. Manus is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('business') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-start-with-no-money.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='start-with-no-money',
    hook=["how i'd start at 19", 'with no money'],
    theme='business',
    pillar='build',
    bgs=[
        'bg-h78.jpg',    # hook         desk-led-neon
        'bg-h88.jpg',    # ARCO         supercars-dusk
        'bg-h46.jpg',    # Manus        desk-city-day
        'bg-h21.jpg',    # Cloudflare   lounge-night
        'bg-h32.jpg',    # Firebase     window-silhouette
        'bg-h51.jpg',    # Stripe       desk-city-day
    ],
    arco=['Every task I have sits on one page', 'with a time next to it.', '', 'I stopped keeping half the list in', 'my head and losing the other half.', '', 'One page, the whole day.'],
    tools=[
        ('Manus',
         ['Manus Wide Research runs many agents at once, one per item on your list.',
          'Market research a consultant would charge for comes back in an hour.']),
        ('Cloudflare',
         ['Cloudflare Workers runs your backend free up to 100,000 requests a day.',
          'The first thousand users cost nothing to serve.']),
        ('Firebase',
         ['Firebase Hosting serves your site with SSL on a free subdomain.',
          'Putting the site live costs nothing.']),
        ('Stripe',
         ['Stripe charges no monthly fee, only a cut of each payment.',
          'Selling costs nothing until the first sale.']),
    ],
)
