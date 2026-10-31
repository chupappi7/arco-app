#!/usr/bin/env python3
"""work-by-noon-14: the tools i use to do / a full day of work by noon.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    the hours it compresses before noon.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle a1 [planning,build,business], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _tools_photo import main

main(
    topic='work-by-noon-14',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=['bg-h56.jpg',   # hook         desk-led-warm      luma 22
         'bg-h51.jpg',   # ARCO         desk-city-day      luma 60
         'bg-n06.jpg',   # Gemini       desk-empty-day     luma 55
         'bg-h49.jpg',   # Notion       desk-city-day      luma 58
         'bg-h39.jpg',   # Zapier       supercars-dusk     luma 32
         'bg-h46.jpg'],  # Sentry       desk-city-day      luma 62
    arco=['I plan the whole day before I start',
          'it, so nothing waits on a decision.', '',
          'I get more done by noon than I used', 'to manage by six.', '',
          'The plan does the deciding.'],
    tools=[
        ('Gemini',
         ['Gemini scheduled actions run a prompt at a time you set and send you the result.',
          'The summary of your inbox is written by 7am, before you have opened it.']),
        ('Notion',
         ['A Notion database template opens the page with its fields already filled in.',
          'The morning admin that used to take an hour is three clicks before coffee.']),
        ('Zapier',
         ['Zapier moves a record between two apps the moment it changes in either one.',
          'The handover you used to do at 9am already happened while you were asleep.']),
        ('Sentry',
         ['Sentry cron monitors alert you when a scheduled job did not run on time.',
          'A broken overnight backup is an alert at 8am, not a discovery after lunch.']),
    ])
