#!/usr/bin/env python3
"""rest-of-my-life-4: 5 apps i will use / for the rest of my life.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    why it outlasts a trend.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle a4 [planning,build,business], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _tools_photo import main
from _veiled_screens import TASKS

main(
    topic='rest-of-my-life-4',
    hook=['5 apps i will use', 'for the rest of my life'],
    theme='planning',
    bgs=['bg-h60.jpg',   # hook         desk-led-neon      luma 27
         'bg-h32.jpg',   # ARCO         window-silhouette  luma 36 (the one person)
         'bg-h88.jpg',   # Codex        supercars-dusk     luma 29
         'bg-h21.jpg',   # Obsidian     lounge-night       luma 64
         'bg-h35.jpg',   # GitHub       supercars-dusk     luma 33
         'bg-h22.jpg'],  # Figma        lounge-day         luma 53
    arco=['Every task I have sits on one page', 'with a time next to it.',
          '', 'I stopped keeping half the list in',
          'my head and losing the other half.', '',
          'One page, the whole day.'],
    tools=[
        ('Codex',
         ['Codex works a task in its own sandbox and opens a pull request when it is done.',
          'You review a diff, which is a skill that outlives whichever model wrote it.']),
        ('Obsidian',
         ['Obsidian stores every note as a plain markdown file in a folder you own.',
          'The notes open in anything, so the company going away costs you nothing.']),
        ('GitHub',
         ['GitHub keeps the full history of a project and who changed what, permanently.',
          'Work from ten years ago still opens, which almost nothing else on a laptop does.']),
        ('Figma',
         ['Figma auto layout resizes a frame to fit whatever ends up inside it.',
          'The file still works after the brand, the copy and the team have all changed.']),
    ],
    cta=(TASKS,
         'Search \u201carco focus\u201d.',
         'The planner and the blocker are one app. '
         'This screen is where you start.'))
