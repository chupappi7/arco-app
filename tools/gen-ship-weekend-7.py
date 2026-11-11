#!/usr/bin/env python3
"""ship-weekend-7: build pillar in the photo look (_tools_photo).

  hook      "how i ship in a weekend / what used to take a month", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Codex, GitHub, Linear, Stripe. Codex is the one LLM.
  re-shoot of month-in-a-weekend, a top performer, on new frames.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-ship-weekend-7.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ship-weekend-7',
    hook=['how i ship in a weekend', 'what used to take a month'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h64.jpg',    # hook         desk-led-neon
        'bg-h48.jpg',    # ARCO         desk-city-day
        'bg-h36.jpg',    # Codex        supercars-dusk
        'bg-h22.jpg',    # GitHub       lounge-day
        'bg-h32.jpg',    # Linear       window-silhouette
        'bg-h37.jpg',    # Stripe       supercars-dusk
    ],
    arco=['Every task has a time and the block', 'that protects it is the same app.', '', 'I stopped running a planner and a', 'blocker that knew nothing about', 'each other.', '', 'One app, one day.'],
    tools=[
        ('Codex',
         ['You can start a task from the ChatGPT app on your phone.',
          'It runs in the cloud, so a task is still going while you are out.']),
        ('GitHub',
         ['Pages serves a folder in the repo as a live site, on push, for free.',
          'The landing page ships the same weekend as the app, with no host.']),
        ('Linear',
         ['Put the issue ID in the branch name and Linear picks it up.',
          'The issue moves itself to done the moment the pull request merges.']),
        ('Stripe',
         ["Stripe Tax works out the sales tax for the buyer's country at checkout.",
          'It also flags where you have crossed a registration threshold.']),
    ],
)
