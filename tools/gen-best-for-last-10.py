#!/usr/bin/env python3
"""best-for-last-10: 5 tools to stay productive / i saved the best for last.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    what it keeps you on task through.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle f1 [focus,study,screentime], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _tools_photo import main

main(
    topic='best-for-last-10',
    hook=['5 tools to stay productive', 'i saved the best for last'],
    theme='focus',
    bgs=['bg-h62.jpg',   # hook         desk-led-neon      luma 21
         'bg-h51.jpg',   # ARCO         desk-city-day      luma 60
         'bg-n06.jpg',   # Antigravity  desk-empty-day     luma 55
         'bg-h48.jpg',   # ClickUp      desk-city-day      luma 65
         'bg-h38.jpg',   # Loom         supercars-dusk     luma 20
         'bg-n04.jpg'],  # PostHog      villa-day          luma 54
    arco=['Focus mode blocks every app on my', 'list for the whole session.',
          '', 'The phone stops being a decision', 'while the timer runs.',
          '', 'My holy grail.'],
    tools=[
        ('Antigravity',
         ['Antigravity drives your editor and a browser in the same agent run.',
          'The work continues through the stretch where you would go looking elsewhere.']),
        ('ClickUp',
         ['ClickUp shows one list filtered down to only what is actually due today.',
          'It holds you through the hour when everything else starts looking urgent.']),
        ('Loom',
         ['Loom viewers comment at a timestamp rather than underneath the video.',
          'It carries the feedback round without a meeting cutting the day in half.']),
        ('PostHog',
         ['PostHog puts feature flags and session replay inside the same tool.',
          'It keeps you on the build through the week you would have spent guessing.']),
    ])
