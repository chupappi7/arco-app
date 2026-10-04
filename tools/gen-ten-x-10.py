#!/usr/bin/env python3
"""ten-x-10: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-04: ship-weekend-screens format for tools posts,
            "arco focus" search CTA on the card.
  hook      "how i 10x'd / my productivity", second strongest eligible tools
            hook by median views (1358 over eight outings) in
            hook_rules.eligible(pillar='tools').
  roster    ARCO, ChatGPT, Obsidian, Raycast. ChatGPT is the LLM, rotated
            away from Gemini on the sibling work-by-noon-9.
  teaching  each checked against every caption in tools/hooks.json:
            ARCO     a timer habit restarted the same day counts down only
                     what is left (HabitTimerEngine.start, alreadyDoneToday:
                     target minus minutes done today). The Today screen shows
                     "52m done" on Gym.
            ChatGPT  Option + Space opens the companion bar over any Mac app
                     (burned: editor reading, tasks, files, record, canvas,
                     custom instructions, branch, projects, agent, memory).
            Obsidian Workspaces core plugin saves and restores a pane layout
                     (burned: daily note, bases, canvas, sync, recovery,
                     backlinks, embeds, slides, clipper).
            Raycast  Quit All Applications from the System commands (burned:
                     clipboard, snippets, quicklinks, hyper key, floating
                     notes, menu items, calendar, calculator, extensions).
  ARCO card angle drawn once with next_arco_angle('focus') and frozen.
  photos    _veiled_screens.pick_bgs excluding work-by-noon-9's set, frozen.

Usage: python3 tools/gen-ten-x-10.py [slide numbers to redo]
"""
import sys
from _veiled_screens import TODAY
from _tools_screens import build

build(
    topic='ten-x-10',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=['bg-h06.jpg',   # hook      lounge-day
         'bg-h32.jpg',   # ARCO      window-silhouette (the one person)
         'bg-h34.jpg',   # ChatGPT   desk-empty-day
         'bg-h35.jpg',   # Obsidian  supercars-dusk
         'bg-h46.jpg',   # Raycast   desk-city-day
         'bg-h88.jpg'],  # card      supercars-dusk
    arco=(TODAY, 'The timer picks up where you left.',
          'Stop a 2 hour Deep work timer at 50 minutes. After lunch, '
          'play counts down only the 70 still left.'),
    tools=[
        ('ChatGPT', 'Ask from inside any app.',
         ['On a Mac, Option + Space opens a ChatGPT bar over whatever app '
          'is in front.',
          'You ask, read the answer and keep typing in your doc.']),
        ('Obsidian', 'Your layout comes back.',
         ['Turn on Workspaces and save the panes you have open for a project.',
          'Loading it reopens every note in its place, so the next session '
          'starts where the last one stopped.']),
        ('Raycast', 'Every other app closes.',
         ['Run Quit All Applications from the Raycast bar before you start.',
          'The screen holds nothing but the app you open next.']),
    ],
    closer=['Focus mode blocks every app on my list',
            'for the whole session. The phone stops being',
            'a decision while the timer runs. My holy grail.'],
    only={int(a) for a in sys.argv[1:]} or None)
