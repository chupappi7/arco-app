#!/usr/bin/env python3
"""work-by-noon-15: tools pillar in the photo look (_tools_photo).

  hook      "the tools i use to do / a full day of work by noon", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    ChatGPT, ClickUp, Obsidian, Make. ChatGPT is the one LLM. Points were
            checked against the newer generators only; about half repeat
            Sep-Oct lessons, all 3+ weeks old (allowed by Thinh, 2026-11-11).
  ARCO      angle drawn once with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled per post,
            outside a 3-post cooldown, at most 2 shared with any of the last 10. Picked 2026-11-11.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov (AIOS/Analyses/2026-11-11 ARCO
            frequency test.md).

Usage: python3 tools/gen-work-by-noon-15.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='work-by-noon-15',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=[
        'bg-n01.jpg',    # hook         villa-day
        'bg-h49.jpg',    # ARCO         desk-city-day
        'bg-h35.jpg',    # ChatGPT      supercars-dusk
        'bg-h20.jpg',    # ClickUp      lounge-day
        'bg-h51.jpg',    # Obsidian     desk-city-day
        'bg-h38.jpg',    # Make         supercars-dusk
    ],
    arco=['The block I am in sits on the Lock', 'Screen with the time left running.', '', 'I pick the phone up and it tells me', 'to get back to work.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['A ChatGPT task runs a prompt at the time you set and sends you the answer.',
          'The morning brief is waiting before you open a single app.']),
        ('ClickUp',
         ['Drag a ClickUp task onto the calendar view and it takes that hour of the day.',
          'Every task has a start time, so noon arrives with them done.']),
        ('Obsidian',
         ['The Daily notes plugin opens today’s note from your own template.',
          'The morning starts on a page that already lists what to do.']),
        ('Make',
         ['A Make scenario reads new email and files every attachment into the right folder.',
          'The inbox chores are finished before you sit down.']),
    ],
)
