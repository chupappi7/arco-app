#!/usr/bin/env python3
"""open-first: tools pillar in the photo look (_tools_photo).

  hook      "5 apps / i open before anything else", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  roster    Gemini, Obsidian, Raycast, Linear. Gemini is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('focus') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-open-first.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='open-first',
    hook=['5 apps', 'i open before anything else'],
    theme='focus',
    bgs=[
        'bg-h72.jpg',    # hook         desk-led-neon
        'bg-h88.jpg',    # ARCO         supercars-dusk
        'bg-h01.jpg',    # Gemini       lounge-day
        'bg-h51.jpg',    # Obsidian     desk-city-day
        'bg-h38.jpg',    # Raycast      supercars-dusk
        'bg-h34.jpg',    # Linear       desk-empty-day
    ],
    arco=['Every time I open TikTok the shield', 'comes up instead of the feed.', '', 'The reflex still happens, it just', 'turns into a reminder to lock in.', '', 'That is the whole app.'],
    tools=[
        ('Gemini',
         ['A Gem is a saved Gemini with your own instructions, like a planner that knows your week.',
          'The day comes back laid out the way you set it, every morning.']),
        ('Obsidian',
         ['Obsidian Bases turns notes with properties into a table you sort and filter.',
          'Every open item sits in one view before the day starts.']),
        ('Raycast',
         ['Raycast Floating Notes stay above every window on the screen.',
          'The day’s three priorities stay in sight while you work.']),
        ('Linear',
         ['My Issues in Linear collects everything assigned to you across every team.',
          'The first look of the day is one list, not five projects.']),
    ],
)
