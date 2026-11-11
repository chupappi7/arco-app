#!/usr/bin/env python3
"""nobody-talks-2: tools pillar in the photo look (_tools_photo).

  hook      "nobody talks about these 5 apps / and they run my whole day", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Gemini, Zapier, Buffer, Notion. Gemini is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-nobody-talks-2.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='nobody-talks-2',
    hook=['nobody talks about these 5 apps', 'and they run my whole day'],
    theme='planning',
    bgs=[
        'bg-h41.jpg',    # hook         jet-mountain
        'bg-n03.jpg',    # ARCO         villa-day
        'bg-h88.jpg',    # Gemini       supercars-dusk
        'bg-h20.jpg',    # Zapier       lounge-day
        'bg-h24.jpg',    # Buffer       lounge-night
        'bg-n05.jpg',    # Notion       desk-empty-day
    ],
    arco=['I plan the whole day before I start', 'it, so nothing waits on a decision.', '', 'I get more done by noon than I used', 'to manage by six.', '', 'The plan does the deciding.'],
    tools=[
        ('Gemini',
         ['Gemini Deep Research reads hundreds of sites and writes a report with the sources cited.',
          'The research runs while you do the first block of the day.']),
        ('Zapier',
         ['The Zapier Chrome extension runs a zap on the page you are looking at.',
          'Saving a lead from a profile is one click, not a copy and paste.']),
        ('Buffer',
         ['The Buffer AI assistant rewrites one post for each network.',
          'Posting runs in the background of the day.']),
        ('Notion',
         ['Notion Calendar shows your Notion tasks next to your meetings.',
          'The plan and the meetings sit on one screen.']),
    ],
)
