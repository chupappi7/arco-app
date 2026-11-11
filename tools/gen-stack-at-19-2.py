#!/usr/bin/env python3
"""stack-at-19-2: build pillar in the photo look (_tools_photo).

  hook      "everything i run my business on / at 19", from the approved pool, word for word.
  theme     business -- hook_pool.json binds it.
  roster    Perplexity, Stripe, Airtable, Canva. Perplexity is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('business') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-stack-at-19-2.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='stack-at-19-2',
    hook=['everything i run my business on', 'at 19'],
    theme='business',
    pillar='build',
    bgs=[
        'bg-h66.jpg',    # hook         desk-led-neon
        'bg-h45.jpg',    # ARCO         window-silhouette
        'bg-h21.jpg',    # Perplexity   lounge-night
        'bg-h11.jpg',    # Stripe       lounge-day
        'bg-h49.jpg',    # Airtable     desk-city-day
        'bg-h05.jpg',    # Canva        lounge-day
    ],
    arco=['Every task I have sits on one page', 'with a time next to it.', '', 'I stopped keeping half the list in', 'my head and losing the other half.', '', 'One page, the whole day.'],
    tools=[
        ('Perplexity',
         ['A Perplexity Space keeps the files and searches for one project together, shared with your team.',
          'Research for the business lives in one place, not in scattered chats.']),
        ('Stripe',
         ['The Stripe customer portal lets customers change or cancel their own plan.',
          'Billing emails stop landing in your inbox.']),
        ('Airtable',
         ['An Airtable Interface puts a simple app on top of a base for the people who use it.',
          'A partner works in the orders view without touching the tables.']),
        ('Canva',
         ['Canva Docs to Decks turns a written doc into a presentation.',
          'The pitch gets written once and becomes the deck.']),
    ],
)
