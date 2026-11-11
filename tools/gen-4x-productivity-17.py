#!/usr/bin/env python3
"""4x-productivity-17: tools pillar in the photo look (_tools_photo).

  hook      "the tools i used to / 4x my productivity", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Gemini, Raycast, Loom, Zapier. Gemini is the one LLM.
  re-shoot of 4x-productivity-9, a top performer, on new frames.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-4x-productivity-17.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='4x-productivity-17',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
        'bg-h57.jpg',    # hook         desk-led-warm
        'bg-h52.jpg',    # ARCO         desk-city-day
        'bg-h05.jpg',    # Gemini       lounge-day
        'bg-n03.jpg',    # Raycast      villa-day
        'bg-h46.jpg',    # Loom         desk-city-day
        'bg-h02.jpg',    # Zapier       lounge-day
    ],
    arco=['One app holds the plan and the', 'block that protects it.', '', 'Tasks get a time on the timeline and', 'Focus mode shuts the apps for it.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Gemini in Chrome reads the tab you are on and the ones open beside it.',
          'Two pricing pages get compared in the sidebar with nothing pasted.']),
        ('Raycast',
         ['Raycast turns caps lock into a hyper key, four modifiers in one.',
          'Every app gets a hotkey nothing else on the mac already uses.']),
        ('Loom',
         ['Live rewind backs the recording up and carries on from that spot.',
          'A stumble at minute four does not mean starting the take from zero.']),
        ('Zapier',
         ['Zapier MCP hands an AI agent your apps as tools it can call itself.',
          'The agent drafts the reply and sends it from gmail in the chat.']),
    ],
)
