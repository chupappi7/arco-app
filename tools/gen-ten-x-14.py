#!/usr/bin/env python3
"""ten-x-14: tools pillar in the photo look (_tools_photo).

  hook      "how i 10x'd / my productivity", from the approved pool, word for word.
  theme     focus -- hook_pool.json binds it.
  lens      every tool point answers: the step it removes, not the feature it ships
  roster    ChatGPT, Raycast, Linear, CleanShot X. ChatGPT is the one LLM.
            Points not taught before: a table rebuilt from a screenshot,
            Raycast window snapping, Linear's command menu, CleanShot X text
            capture.
  ARCO      angle drawn once with next_arco_angle('focus') and frozen below.
  photos    hook chosen from the unused hook frames; app frames ordered by
            hand so none repeats the frames of the last three posts except
            bg-h29, last used four posts back in ship-weekend-6.
  cta       none. Tools and build posts end on the fifth app: ARCO reads as
            one recommendation among peers, and the ask drew 2 comments on
            ~10.6k views (27 Oct - 9 Nov). Thinh, 2026-11-10.

Usage: python3 tools/gen-ten-x-14.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='ten-x-14',
    hook=["how i 10x'd", 'my productivity'],
    theme='focus',
    bgs=[
        'bg-h50.jpg',    # hook         desk-city-day
        'bg-h29.jpg',    # ARCO         supercars-dusk
        'bg-h11.jpg',    # ChatGPT      lounge-day
        'bg-h51.jpg',    # Raycast      desk-city-day
        'bg-h24.jpg',    # Linear       lounge-night (n03's bright sky washed the copy out)
        'bg-n06.jpg',    # CleanShot X  desk-empty-day
    ],
    arco=['Focus mode puts every distracting', 'app away for the whole session.', '', 'An hour of work is an hour now, not', 'forty minutes and a scroll.', '', 'I get the time back.'],
    tools=[
        ('ChatGPT',
         ['ChatGPT reads a screenshot of a table and hands it back as a spreadsheet file.',
          'The retyping between a photo of numbers and a working sheet is gone.']),
        ('Raycast',
         ['Raycast snaps the front window to half or a third of the screen on one hotkey.',
          'Dragging windows into place before every task stops being a step.']),
        ('Linear',
         ['Cmd K in Linear runs any action on the issue you are on from the keyboard.',
          'The click path through three menus to change a status disappears.']),
        ('CleanShot X',
         ['CleanShot X copies the text out of any part of the screen you drag over.',
          'Retyping a line from a video or a locked PDF is no longer part of the job.']),
    ],
)
