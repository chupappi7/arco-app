#!/usr/bin/env python3
"""pay-for-twelve-6: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "i pay for 12 apps / these 5 do all the work", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Perplexity, Canva, Stripe, Framer. Perplexity is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook says five apps do the work of twelve, so every point is a tool doing the job of another subscription: three chat apps in one, a spreadsheet inside the design tool, a pay what you want checkout with no storefront, a landing page drafted with nobody hired.
  ARCO      angle v13, drawn once with next_arco_angle('business') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-pay-for-twelve-6.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='pay-for-twelve-6',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='business',
    bgs=[
         'bg-h79.jpg',    # hook
         'bg-h37.jpg',    # ARCO
         'bg-h31.jpg',    # Perplexity
         'bg-h35.jpg',    # Canva
         'bg-h45.jpg',    # Stripe
         'bg-h88.jpg',    # Framer
    ],
    arco=['The block I’m in sits on the Lock', 'Screen with the time left on it.', '', 'Picking up the phone shows the plan', 'before it shows a feed.', '', 'My holy grail.'],
    tools=[
        ('Perplexity',
         ['Perplexity Pro lets you pick which model answers, Claude, GPT or Gemini.',
          'One subscription covers what used to be three chat apps.']),
        ('Canva',
         ['Canva Sheets turns a table into charts that drop straight into a design.',
          'The monthly numbers and the deck come from one file, with no spreadsheet app.']),
        ('Stripe',
         ['A Stripe payment link can let the buyer choose how much to pay.',
          'A pay what you want launch needs no storefront app on top of it.']),
        ('Framer',
         ['Framer Wireframer lays out a full responsive page from one sentence.',
          'You start by editing a landing page instead of paying someone to draft it.']),
    ])
