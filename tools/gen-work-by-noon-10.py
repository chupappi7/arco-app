#!/usr/bin/env python3
"""work-by-noon-10: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-07: a tools post is a five-app listicle with every
            slide in the same visual language, icon, number and name, two
            lines, over a photo. ARCO is one of the five and gets the same
            app_slide as the rest, titled App Blocker & Focus: ARCO. No phone
            mockup anywhere.
  hook      "the tools i use to do / a full day of work by noon", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, ChatGPT, Descript, Notion, PostHog. ChatGPT is the one LLM, rotated across the
            2026-10-07 photo batch.
  answers   the hook promises a day finished by noon, so every point removes a morning job: prep that was researched overnight, an edit given in words, a meeting booked in one reply, a question about the numbers answered without writing a query.
  ARCO      angle v8, drawn once with next_arco_angle('planning') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame from those never used on a hook; app frames under
            BAND_MAX_LUMA, no desk frame (their monitors and chairs sit
            behind the copy), no hook-only vibe, at most one person, no adjacent
            vibe, nothing shared with the post before.

Usage: python3 tools/gen-work-by-noon-10.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='work-by-noon-10',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=[
         'bg-h09.jpg',    # hook
         'bg-h29.jpg',    # ARCO
         'bg-h22.jpg',    # ChatGPT
         'bg-h36.jpg',    # Descript
         'bg-h24.jpg',    # Notion
         'bg-n04.jpg',    # PostHog
    ],
    arco=['I manage all my tasks here and the', 'day is planned in half a minute.', '', 'Focus mode puts every distraction', 'away until I am done.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['Pulse researches overnight from your past chats and your calendar.',
          'You wake up to cards with the prep for today’s meeting already done.']),
        ('Descript',
         ['Underlord takes an edit in plain words, like cut this into a 60 second clip.',
          'The cut lands on the timeline ready to check, not built by hand.']),
        ('Notion',
         ['Notion Calendar copies your free slots as text you paste into any message.',
          'The meeting gets booked in one reply instead of five emails.']),
        ('PostHog',
         ['PostHog AI builds the chart from a question you type in plain words.',
          'Why signups dropped on tuesday is answered before lunch, with no query written.']),
    ])
