#!/usr/bin/env python3
"""study-apps: tools pillar in the photo look (_tools_photo).

  hook      "5 study apps / that actually did something", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it.
  roster    ChatGPT, ElevenLabs, Notion, Loom. ChatGPT is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('study') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-study-apps.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='study-apps',
    hook=['5 study apps', 'that actually did something'],
    theme='study',
    bgs=[
        'bg-h40.jpg',    # hook         jet-mountain
        'bg-n06.jpg',    # ARCO         desk-empty-day
        'bg-h52.jpg',    # ChatGPT      desk-city-day
        'bg-h36.jpg',    # ElevenLabs   supercars-dusk
        'bg-h31.jpg',    # Notion       lounge-night
        'bg-h37.jpg',    # Loom         supercars-dusk
    ],
    arco=['I put the study block in and the', 'distracting apps close with it.', '', 'The session ends when the timer', 'does, not when I give in.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['ChatGPT study mode asks you questions instead of giving you the answer.',
          'You find out what you don’t know before the exam does.']),
        ('ElevenLabs',
         ['ElevenReader reads any PDF or article aloud on your phone.',
          'The reading for class gets done on the walk there.']),
        ('Notion',
         ['Mark a Notion page available offline and it opens with no signal.',
          'Your notes still open on the train or in the library basement.']),
        ('Loom',
         ['Loom lets you draw on the screen while you record.',
          'Explaining a problem to the study group takes one short video.']),
    ],
)
