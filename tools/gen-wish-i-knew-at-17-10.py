#!/usr/bin/env python3
"""wish-i-knew-at-17-10: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "5 apps i wish someone / showed me at 17", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Antigravity, Notion, Cloudflare, Canva. Antigravity is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook is what a 17 year old should have been shown, so every point lands on that age: a first app agreed on before any code, the student plan nobody mentions, a first site that survives its traffic, a class presentation with a real Q&A.
  ARCO      angle f2, drawn once with next_arco_angle('study') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-wish-i-knew-at-17-10.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-10',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
         'bg-h59.jpg',    # hook
         'bg-h39.jpg',    # ARCO
         'bg-h24.jpg',    # Antigravity
         'bg-h35.jpg',    # Notion
         'bg-h31.jpg',    # Cloudflare
         'bg-h37.jpg',    # Canva
    ],
    arco=['I start a session and every app on', 'the list locks itself.', '', 'Four hours later the phone has not', 'been picked up once.', '', 'My holy grail.'],
    tools=[
        ('Antigravity',
         ['The Antigravity agent can draw a mockup of a screen before it writes the code.',
          'You agree on how the app looks before a single file changes.']),
        ('Notion',
         ['Sign up for Notion with a school email and the Plus plan is free.',
          'Unlimited uploads and 30 days of page history cost nothing while you are a student.']),
        ('Cloudflare',
         ['Cloudflare Pages hosts a static site for free with no bandwidth limit.',
          'The first project you share stays up even on the day it gets traffic.']),
        ('Canva',
         ['Canva Live lets the room send questions from their phones while you present.',
          'The Q&A after your class presentation is a list on screen, not silence.']),
    ])
