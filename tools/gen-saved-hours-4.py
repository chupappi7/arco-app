#!/usr/bin/env python3
"""saved-hours-4: tools pillar in the photo look (_tools_photo).

  hook      "5 tools / that saved me hours this week", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Perplexity, Airtable, Figma, CapCut. Perplexity is the one LLM. Points were
            checked against the newer generators only; about half repeat
            Sep-Oct lessons, all 3+ weeks old (allowed by Thinh, 2026-11-11).
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-saved-hours-4.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='saved-hours-4',
    hook=['5 tools', 'that saved me hours this week'],
    theme='planning',
    bgs=[
        'bg-h56.jpg',    # hook         desk-led-warm
        'bg-h49.jpg',    # ARCO         desk-city-day
        'bg-h36.jpg',    # Perplexity   supercars-dusk
        'bg-h19.jpg',    # Airtable     lounge-day
        'bg-h35.jpg',    # Figma        supercars-dusk
        'bg-n06.jpg',    # CapCut       desk-empty-day
    ],
    arco=['Every task I have gets a time on', "the day's timeline, not a list.", '', 'Blocked Hours shuts the feeds for', 'those windows without me asking.', '', 'My holy grail.'],
    tools=[
        ('Perplexity',
         ['Comet, the Perplexity browser, compares open tabs and fills in forms when you ask.',
          'The hour of tab hopping comes back finished.']),
        ('Airtable',
         ['An Airtable AI field writes a summary of every record in the table.',
          'Reading every row turns into reading one column.']),
        ('Figma',
         ['Figma Dev Mode shows the exact spacing and code for any layer you click.',
          'Handoff questions stop eating the week.']),
        ('CapCut',
         ['CapCut removes the background of a video with no green screen.',
          'The shot works anywhere, without a studio.']),
    ],
)
