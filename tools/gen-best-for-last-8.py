#!/usr/bin/env python3
"""best-for-last-8: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-07: a tools post is a five-app listicle with every
            slide in the same visual language, icon, number and name, two
            lines, over a photo. ARCO is one of the five and gets the same
            app_slide as the rest, titled App Blocker & Focus: ARCO. No phone
            mockup anywhere.
  hook      "5 tools to stay productive / i saved the best for last", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Raycast, ClickUp, Obsidian, Manus. Manus is the one LLM, rotated across the
            2026-10-07 photo batch.
  answers   the hook is about staying productive and ends on the best, so the points cut the small daily drags (rewording, the stand-up, scattered to-dos) and the last slide carries the biggest hand-off: an agent working in your own logged-in browser.
  ARCO      angle f2, drawn once with next_arco_angle('focus') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame from those never used on a hook; app frames under
            BAND_MAX_LUMA, no desk frame (their monitors and chairs sit
            behind the copy), no hook-only vibe, at most one person, no adjacent
            vibe, nothing shared with the post before.

Usage: python3 tools/gen-best-for-last-8.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='best-for-last-8',
    hook=['5 tools to stay productive', 'i saved the best for last'],
    theme='focus',
    bgs=[
         'bg-n02.jpg',    # hook
         'bg-h32.jpg',    # ARCO
         'bg-n03.jpg',    # Raycast
         'bg-h37.jpg',    # ClickUp
         'bg-h21.jpg',    # Obsidian
         'bg-h20.jpg',    # Manus
    ],
    arco=['I start a session and every app on', 'the list locks itself.', '', 'Four hours later the phone has not', 'been picked up once.', '', 'My holy grail.'],
    tools=[
        ('Raycast',
         ['Write your own AI command once, like make this a bullet list, and give it a hotkey.',
          'It then runs on the text you select in whatever app is open.']),
        ('ClickUp',
         ['ClickUp Brain writes your stand-up from the tasks you actually moved yesterday.',
          'The update is ready in seconds, with nothing to remember.']),
        ('Obsidian',
         ['The Tasks community plugin pulls every unchecked box in your vault into one list.',
          'To-dos buried in meeting notes end up on one page, sorted by due date.']),
        ('Manus',
         ['The Browser Operator extension lets Manus work inside your own Chrome, already logged in.',
          'It pulls the numbers from your dashboards without you handing over a password.']),
    ])
