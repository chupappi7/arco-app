#!/usr/bin/env python3
"""business-at-19-4: build pillar in the photo look (_tools_photo, pillar='build').

  hook      "the tools i use to run my business / at 19 years old", from the approved pool, word for word.
  theme     business -- hook_pool.json binds it.
  roster    Manus, Cloudflare, PostHog, Buffer. Manus is the one LLM. Points were
            checked against the newer generators only; about half repeat
            Sep-Oct lessons, all 3+ weeks old (allowed by Thinh, 2026-11-11).
  ARCO      angle drawn once with next_arco_angle('business') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-business-at-19-4.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='business-at-19-4',
    hook=['the tools i use to run my business', 'at 19 years old'],
    theme='business',
    pillar='build',
    bgs=[
        'bg-h60.jpg',    # hook         desk-led-neon
        'bg-h38.jpg',    # ARCO         supercars-dusk
        'bg-h50.jpg',    # Manus        desk-city-day
        'bg-h20.jpg',    # Cloudflare   lounge-day
        'bg-n01.jpg',    # PostHog      villa-day
        'bg-h24.jpg',    # Buffer       lounge-night
    ],
    arco=['Every task I have is in here and the', 'day gets planned in 30 seconds.', '', 'Focus mode puts every distraction', 'away while I work.', '', 'My holy grail.'],
    tools=[
        ('Manus',
         ['Manus builds a full slide deck from one prompt, with the research done for it.',
          'The pitch deck is a draft in minutes instead of a weekend.']),
        ('Cloudflare',
         ['Cloudflare Email Routing forwards hello at your domain to your own inbox for free.',
          'You write from a company address on day one without paying for mail.']),
        ('PostHog',
         ['The PostHog free tier covers a million events every month.',
          'You see what customers do from launch day without a bill.']),
        ('Buffer',
         ['The Buffer free plan schedules posts across three channels.',
          'A week of marketing goes out while you work on the product.']),
    ],
)
