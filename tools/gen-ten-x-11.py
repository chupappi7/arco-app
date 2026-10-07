#!/usr/bin/env python3
"""ten-x-11: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-07: a tools post is a five-app listicle with every
            slide in the same visual language, icon, number and name, two
            lines, over a photo. ARCO is one of the five and gets the same
            app_slide as the rest, titled App Blocker & Focus: ARCO. No phone
            mockup anywhere.
  hook      "how i 10x'd / my productivity", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Claude, Captions, Higgsfield, Canva. Claude is the one LLM, rotated across the
            2026-10-07 photo batch.
  answers   the hook promises a multiplier, so every point is one person doing work that used to take a hand-off or an hour: an issue fixed by an agent, an edit done in one pass, a shot directed by drawing, a design reworded without a rebuild.
  ARCO      angle f1, drawn once with next_arco_angle('focus') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame from those never used on a hook; app frames under
            BAND_MAX_LUMA, no desk frame (their monitors and chairs sit
            behind the copy), no hook-only vibe, at most one person, no adjacent
            vibe, nothing shared with the post before.

Usage: python3 tools/gen-ten-x-11.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ten-x-11',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=[
         'bg-h28.jpg',    # hook
         'bg-h37.jpg',    # ARCO
         'bg-h20.jpg',    # Claude
         'bg-h88.jpg',    # Captions
         'bg-h21.jpg',    # Higgsfield
         'bg-n03.jpg',    # Canva
    ],
    arco=['Focus mode blocks every app on my', 'list for the whole session.', '', 'The phone stops being a decision', 'while the timer runs.', '', 'My holy grail.'],
    tools=[
        ('Claude',
         ['Install the Claude GitHub app and tag @claude on any issue.',
          'It writes the fix and opens the pull request while you work on the next thing.']),
        ('Captions',
         ['AI Edit adds the zooms, b-roll and captions to a talking video in one pass.',
          'An hour of editing becomes a draft you only have to check.']),
        ('Higgsfield',
         ['Draw-to-Video lets you sketch an arrow on a still image and the shot moves along it.',
          'You direct the camera with a pen instead of rewriting the prompt ten times.']),
        ('Canva',
         ['Grab Text turns words baked into an image into text you can edit.',
          'An old flyer gets new copy without rebuilding the design.']),
    ])
