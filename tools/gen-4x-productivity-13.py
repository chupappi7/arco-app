#!/usr/bin/env python3
"""4x-productivity-13: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "the tools i used to / 4x my productivity", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Cursor, Granola, Figma, Buffer. Cursor is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook promises four times the output, so every point cuts the time a routine job eats: a wrong step fixed in the plan not the diff, notes with no laptop, a design found from a screenshot, the bio link built where the posts already are.
  ARCO      angle v14, drawn once with next_arco_angle('planning') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-4x-productivity-13.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='4x-productivity-13',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
         'bg-h44.jpg',    # hook
         'bg-h31.jpg',    # ARCO
         'bg-h35.jpg',    # Cursor
         'bg-h22.jpg',    # Granola
         'bg-h37.jpg',    # Figma
         'bg-h24.jpg',    # Buffer
    ],
    arco=['One app holds the plan and the', 'block that protects it.', '', 'Tasks get a time on the timeline and', 'Focus mode shuts the apps for it.', '', 'My holy grail.'],
    tools=[
        ('Cursor',
         ['Cursor plan mode writes the plan as a file you edit before any code changes.',
          'A wrong step is fixed in one line instead of undone across twenty files.']),
        ('Granola',
         ['The Granola iPhone app takes notes on a meeting with no laptop open.',
          'A coffee chat ends as written notes and next steps on your phone.']),
        ('Figma',
         ['Figma visual search finds every frame that looks like an image you drop in.',
          'A button you drew months ago is found from a screenshot, not by digging.']),
        ('Buffer',
         ['Buffer Start Page is a link in bio page you edit from the same dashboard.',
          'Your bio link gets built without paying for a separate link in bio app.']),
    ])
