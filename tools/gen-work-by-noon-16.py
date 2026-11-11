#!/usr/bin/env python3
"""work-by-noon-16: tools pillar in the photo look (_tools_photo).

  hook      "the tools i use to do / a full day of work by noon", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    Manus, Sentry, Cloudflare, Higgsfield. Manus is the one LLM.
  re-shoot of work-by-noon-8, a top performer, on new frames; Sentry slide swapped for a point not run in 21 days.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-work-by-noon-16.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='work-by-noon-16',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=[
        'bg-h14.jpg',    # hook         desk-person-night
        'bg-h20.jpg',    # ARCO         lounge-day
        'bg-h46.jpg',    # Manus        desk-city-day
        'bg-n06.jpg',    # Sentry       desk-empty-day
        'bg-h05.jpg',    # Cloudflare   lounge-day
        'bg-n03.jpg',    # Higgsfield   villa-day
    ],
    arco=['Tasks with no time wait in Anytime', 'instead of crowding today.', '', 'Today holds only what I gave an', 'hour to, so I actually finish it.', '', 'The list stopped lying to me.'],
    tools=[
        ('Manus',
         ['Give it the csv and it writes the analysis with the charts drawn.',
          'The weekly numbers come back as a page to read, not a file to open.']),
        ('Sentry',
         ['Sentry alerts post in Slack with the error and how many users hit it.',
          'You know before noon whether the morning release broke something.']),
        ('Cloudflare',
         ['AI gateway sits in front of your model calls and caches answers.',
          'The same prompt asked twice is billed once and answered at once.']),
        ('Higgsfield',
         ['Marketing Studio takes one product photo and builds the ad around it.',
          'A tiktok ready ad exists before anything has been filmed.']),
    ],
)
