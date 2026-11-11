#!/usr/bin/env python3
"""boring-part: tools pillar in the photo look (_tools_photo).

  hook      "5 apps / that do the boring part", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    ChatGPT, Descript, GitHub, Zapier. ChatGPT is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-boring-part.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='boring-part',
    hook=['5 apps', 'that do the boring part'],
    theme='focus',
    bgs=[
        'bg-h63.jpg',    # hook         desk-led-neon
        'bg-h04.jpg',    # ARCO         lounge-day
        'bg-n04.jpg',    # ChatGPT      villa-day
        'bg-h20.jpg',    # Descript     lounge-day
        'bg-h24.jpg',    # GitHub       lounge-night
        'bg-h29.jpg',    # Zapier       supercars-dusk
    ],
    arco=['Focus mode blocks every app on my', 'list for the whole session.', '', 'The phone stops being a decision', 'while the timer runs.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['ChatGPT agent works through a website in its own browser and asks before it submits anything.',
          'The form filling and the copy and paste happen while you do something else.']),
        ('Descript',
         ['Descript removes every um and uh from a recording in one click.',
          'The cleanup pass on a voiceover is gone.']),
        ('GitHub',
         ['Dependabot opens a pull request whenever a package you use has an update.',
          'Keeping dependencies current stops being a chore you schedule.']),
        ('Zapier',
         ['Zapier Tables hold the rows your zaps read and write, with no spreadsheet in between.',
          'The tracking sheet keeps itself up to date.']),
    ],
)
