#!/usr/bin/env python3
"""ten-x-12: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "how i 10x'd / my productivity", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Codex, Make, Airtable, Vercel. Codex is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook promises ten times the output, so every point multiplies one unit of effort: one prompt run as four attempts, one email split into forty filed attachments, one sentence turned into a whole base, one function run every day on its own.
  ARCO      angle f1, drawn once with next_arco_angle('focus') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-ten-x-12.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ten-x-12',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=[
         'bg-h75.jpg',    # hook
         'bg-h20.jpg',    # ARCO
         'bg-h21.jpg',    # Codex
         'bg-h38.jpg',    # Make
         'bg-n04.jpg',    # Airtable
         'bg-h39.jpg',    # Vercel
    ],
    arco=['Focus mode blocks every app on my', 'list for the whole session.', '', 'The phone stops being a decision', 'while the timer runs.', '', 'My holy grail.'],
    tools=[
        ('Codex',
         ['A Codex cloud task can run as up to four attempts at the same time.',
          'You read four takes on one feature and keep the best, from one prompt.']),
        ('Make',
         ['A Make iterator splits one list into items and runs each through the scenario.',
          'Forty attachments in one email get saved, renamed and filed with no clicks.']),
        ('Airtable',
         ['Airtable Omni builds a whole base from a sentence, tables and fields included.',
          'The tracker for your side project exists before you would have named a column.']),
        ('Vercel',
         ['A cron entry in vercel.json runs one of your functions on a schedule.',
          'The daily email or cleanup job runs with no server of your own.']),
    ])
