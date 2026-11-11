#!/usr/bin/env python3
"""feel-like-cheating: tools pillar in the photo look (_tools_photo).

  hook      "5 tools / that feel like cheating", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    Perplexity, Photoroom, Zapier, Descript. Perplexity is the one LLM. Points were
            checked against the newer generators only; about half repeat
            Sep-Oct lessons, all 3+ weeks old (allowed by Thinh, 2026-11-11).
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-feel-like-cheating.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='feel-like-cheating',
    hook=['5 tools', 'that feel like cheating'],
    theme='focus',
    bgs=[
        'bg-n03.jpg',    # hook         villa-day
        'bg-h21.jpg',    # ARCO         lounge-night
        'bg-h22.jpg',    # Perplexity   lounge-day
        'bg-h32.jpg',    # Photoroom    window-silhouette
        'bg-h46.jpg',    # Zapier       desk-city-day
        'bg-n04.jpg',    # Descript     villa-day
    ],
    arco=['Every time I open TikTok the shield', 'comes up instead of the feed.', '', 'The reflex still happens, it just', 'turns into a reminder to lock in.', '', 'That is the whole app.'],
    tools=[
        ('Perplexity',
         ['Perplexity Labs answers one question with a report, the charts and a spreadsheet.',
          'An afternoon of research and formatting comes back in minutes.']),
        ('Photoroom',
         ['Photoroom batch mode edits fifty photos at once with the same background.',
          'A whole set of shots is done in the time one used to take.']),
        ('Zapier',
         ['Describe an automation in one sentence and Zapier Copilot builds the zap.',
          'An hour of setup turns into a line of plain words.']),
        ('Descript',
         ['Descript Studio Sound strips the echo and the noise out of a recording in one click.',
          'A laptop mic in a bedroom sounds like a booth.']),
    ],
)
