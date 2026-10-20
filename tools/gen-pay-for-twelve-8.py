#!/usr/bin/env python3
"""pay-for-twelve-8: tools pillar in the photo look (_tools_photo).

  hook      "i pay for 12 apps / these 5 do all the work", from the approved pool, word for word.
  theme     business -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: the work it absorbs that another subscription was doing
  roster    ChatGPT, Notion, Buffer, PostHog. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('business') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-pay-for-twelve-8.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='pay-for-twelve-8',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='business',
    bgs=[
        'bg-h30.jpg',    # hook
        'bg-h11.jpg',    # ARCO
        'bg-h38.jpg',    # ChatGPT
        'bg-h50.jpg',    # Notion
        'bg-n04.jpg',    # Buffer
        'bg-n06.jpg',    # PostHog
    ],
    arco=['The block I’m in sits on the Lock', 'Screen with the time left on it.', '', 'Picking up the phone shows the plan', 'before it shows a feed.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['ChatGPT drafts, rewrites and proofreads in one window with your files attached.',
          'It quietly replaced three writing tools I was paying for separately.']),
        ('Notion',
         ['A Notion database is the wiki and the task tracker looking at the same rows.',
          'One subscription covers what a docs tool and a project tool were splitting.']),
        ('Buffer',
         ['Buffer queues a post per channel and publishes on the schedule you set.',
          'It does the job the dedicated scheduler was charging monthly for.']),
        ('PostHog',
         ['PostHog puts analytics, session replay and feature flags on the same events.',
          'Three separate bills became one line, reading from one source.']),
    ])
