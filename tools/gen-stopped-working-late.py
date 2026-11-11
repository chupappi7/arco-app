#!/usr/bin/env python3
"""stopped-working-late: tools pillar in the photo look (_tools_photo).

  hook      "i stopped working late / these 5 apps are why", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Claude, n8n, Sentry, CapCut. Claude is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-stopped-working-late.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='stopped-working-late',
    hook=['i stopped working late', 'these 5 apps are why'],
    theme='planning',
    bgs=[
        'bg-h71.jpg',    # hook         desk-led-neon
        'bg-h34.jpg',    # ARCO         desk-empty-day
        'bg-h38.jpg',    # Claude       supercars-dusk
        'bg-h22.jpg',    # n8n          lounge-day
        'bg-h46.jpg',    # Sentry       desk-city-day
        'bg-h39.jpg',    # CapCut       supercars-dusk
    ],
    arco=['One app holds the plan and the', 'block that protects it.', '', 'Tasks get a time on the timeline and', 'Focus mode shuts the apps for it.', '', 'My holy grail.'],
    tools=[
        ('Claude',
         ['Claude Code checkpoints let you rewind its edits to any earlier point.',
          'A wrong turn at five is undone, not debugged until nine.']),
        ('n8n',
         ['An n8n workflow can hand one step to an AI model, like sorting replies by intent.',
          'The inbox triage runs while you finish the real work.']),
        ('Sentry',
         ['Sentry Session Replay shows what the user clicked right before the error.',
          'A bug gets reproduced in minutes instead of all evening.']),
        ('CapCut',
         ['CapCut reads your script aloud in an AI voice and lays it on the timeline.',
          'The voiceover is done without a mic session at night.']),
    ],
)
