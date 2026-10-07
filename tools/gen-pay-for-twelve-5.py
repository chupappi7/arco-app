#!/usr/bin/env python3
"""pay-for-twelve-5: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-07: a tools post is a five-app listicle with every
            slide in the same visual language, icon, number and name, two
            lines, over a photo. ARCO is one of the five and gets the same
            app_slide as the rest, titled App Blocker & Focus: ARCO. No phone
            mockup anywhere.
  hook      "i pay for 12 apps / these 5 do all the work", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Gemini, Stripe, Supabase, RevenueCat. Gemini is the one LLM, rotated across the
            2026-10-07 photo batch.
  answers   the hook says five apps carry the work of twelve, so every point is one app standing in for another: a video without a camera or editor, a company without a lawyer, search without a second database, revenue numbers without a spreadsheet.
  ARCO      angle v9, drawn once with next_arco_angle('business') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame from those never used on a hook; app frames under
            BAND_MAX_LUMA, no desk frame (their monitors and chairs sit
            behind the copy), no hook-only vibe, at most one person, no adjacent
            vibe, nothing shared with the post before.

Usage: python3 tools/gen-pay-for-twelve-5.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='pay-for-twelve-5',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='business',
    bgs=[
         'bg-h10.jpg',    # hook
         'bg-h36.jpg',    # ARCO
         'bg-h24.jpg',    # Gemini
         'bg-h29.jpg',    # Stripe
         'bg-n04.jpg',    # Supabase
         'bg-h22.jpg',    # RevenueCat
    ],
    arco=['All of my tasks sit here and planning', 'the day takes 30 seconds.', '', 'Focus mode puts every distraction', 'away, and Blocked Hours repeats it', 'every weekday.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Upload a photo, describe the motion, and Veo turns it into an eight second video with sound.',
          'The product clip exists without a camera or an editing app.']),
        ('Stripe',
         ['Stripe Atlas forms a US company and gets its tax ID for you.',
          'You take payments as a real business without a lawyer or a filing service.']),
        ('Supabase',
         ['Supabase stores AI embeddings in the same Postgres database as your data.',
          'Search by meaning ships without paying for a second vector database.']),
        ('RevenueCat',
         ['RevenueCat Charts draw MRR, churn and trial conversion from the receipts it already handles.',
          'The subscription numbers need no spreadsheet and no extra analytics tool.']),
    ])
