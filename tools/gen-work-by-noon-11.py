#!/usr/bin/env python3
"""work-by-noon-11: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "the tools i use to do / a full day of work by noon", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Claude, Notion, Raycast, Zapier. Claude is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook promises a day finished by noon, so every point takes a morning job off the list: an inbox cleared by the browser agent, meeting notes written into the doc during the call, the repeat reply on three keys, a lead followed up on its own.
  ARCO      angle v12, drawn once with next_arco_angle('planning') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-work-by-noon-11.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='work-by-noon-11',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=[
         'bg-h01.jpg',    # hook
         'bg-h38.jpg',    # ARCO
         'bg-n04.jpg',    # Claude
         'bg-h39.jpg',    # Notion
         'bg-h20.jpg',    # Raycast
         'bg-h21.jpg',    # Zapier
    ],
    arco=['Tasks without a time wait in Anytime', 'until the day has room for them.', '', 'Focus mode blocks the apps I chose', 'for exactly that block.', '', 'My holy grail.'],
    tools=[
        ('Claude',
         ['Claude in Chrome reads the tab you are on and clicks through the page for you.',
          'A full inbox gets archived and labelled while you make coffee.']),
        ('Notion',
         ['Notion AI meeting notes transcribe a call straight into the page you have open.',
          'The summary and action items are in the project doc the minute the call ends.']),
        ('Raycast',
         ['A Raycast snippet expands a few letters into a full reply you saved once.',
          'The answer you type ten times a morning takes three keystrokes each time.']),
        ('Zapier',
         ['A Zapier delay step holds the next action until the day and time you set.',
          'Every new lead gets the follow-up two days later with nothing on your calendar.']),
    ])
