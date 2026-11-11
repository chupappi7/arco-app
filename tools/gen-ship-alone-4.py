#!/usr/bin/env python3
"""ship-alone-4: build pillar in the photo look (_tools_photo, pillar='build').

  hook      "5 tools / that replace a whole team", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Codex, Sentry, Figma, OpusClip. Codex is the one LLM. Every
            point checked against every earlier generator: none taught before.
  ARCO      angle drawn once with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-ship-alone-4.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ship-alone-4',
    hook=['5 tools', 'that replace a whole team'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-n02.jpg',    # hook         villa-day
        'bg-h39.jpg',    # ARCO         supercars-dusk
        'bg-h52.jpg',    # Codex        desk-city-day
        'bg-n01.jpg',    # Sentry       villa-day
        'bg-h48.jpg',    # Figma        desk-city-day
        'bg-h05.jpg',    # OpusClip     lounge-day
    ],
    arco=['One button starts the block and', 'locks every app on the list.', '', 'No settings and no deciding, I am', 'in and the phone is out.', '', 'One tap and I am working.'],
    tools=[
        ('Codex',
         ['Tag @Codex in a Slack thread and it takes the task and replies with a pull request.',
          'The backlog gets worked while you are on something else.']),
        ('Sentry',
         ['Sentry Seer reads the stack trace of an error and proposes the fix.',
          'A crash arrives with its likely cause, so being on call takes ten minutes.']),
        ('Figma',
         ['Figma Make turns a prompt into a prototype you can click through on your phone.',
          'You test the idea in your hand before anyone draws a final screen.']),
        ('OpusClip',
         ['OpusClip cuts one long video into short clips and scores each by how well it holds attention.',
          'One recording becomes a week of posts without an editor.']),
    ],
)
