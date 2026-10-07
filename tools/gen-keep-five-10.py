#!/usr/bin/env python3
"""keep-five-10: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-07: a tools post is a five-app listicle with every
            slide in the same visual language, icon, number and name, two
            lines, over a photo. ARCO is one of the five and gets the same
            app_slide as the rest, titled App Blocker & Focus: ARCO. No phone
            mockup anywhere.
  hook      "the 5 apps i would keep / if i deleted everything else", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Gemini, Canva, Cloudflare, Vercel. Gemini is the one LLM, rotated across the
            2026-10-07 photo batch.
  answers   the hook asks what survives deleting everything else, so every point is one app absorbing another: a design app, a form builder, a domain registrar that raises prices, an analytics script.
  ARCO      angle v11, drawn once with next_arco_angle('planning') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame from those never used on a hook; app frames under
            BAND_MAX_LUMA, no desk frame (their monitors and chairs sit
            behind the copy), no hook-only vibe, at most one person, no adjacent
            vibe, nothing shared with the post before.

Usage: python3 tools/gen-keep-five-10.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='keep-five-10',
    hook=['the 5 apps i would keep', 'if i deleted everything else'],
    theme='planning',
    bgs=[
         'bg-h46.jpg',    # hook
         'bg-n04.jpg',    # ARCO
         'bg-h36.jpg',    # Gemini
         'bg-h24.jpg',    # Canva
         'bg-h29.jpg',    # Cloudflare
         'bg-h22.jpg',    # Vercel
    ],
    arco=['Every task I have gets a time on', 'the day’s timeline, not a list.', '', 'Blocked Hours shuts the feeds for', 'those windows without me asking.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Write the notes in Gemini Canvas and pick Infographic from the Create menu.',
          'It designs a one page visual from them, so there is no design app to open.']),
        ('Canva',
         ['Canva Code builds a working calculator or quiz from one sentence.',
          'It sits in the design or on your Canva site with no form tool and no developer.']),
        ('Cloudflare',
         ['Cloudflare sells domains at the price the registry charges, with no markup on renewal.',
          'Year two costs what year one did, so there is no registrar to move away from.']),
        ('Vercel',
         ['Vercel Web Analytics counts visitors without using cookies.',
          'The site gets its numbers with no cookie banner and no Google Analytics script.']),
    ])
