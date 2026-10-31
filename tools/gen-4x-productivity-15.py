#!/usr/bin/env python3
"""4x-productivity-15: the tools i used to / 4x my productivity.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    the time it gives back inside a working day.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle v1 [planning,build,business], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _tools_photo import main

main(
    topic='4x-productivity-15',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=['bg-h55.jpg',   # hook         desk-led-warm      luma 14
         'bg-h52.jpg',   # ARCO         desk-city-day      luma 64
         'bg-n05.jpg',   # Claude       desk-empty-day     luma 51
         'bg-h48.jpg',   # Raycast      desk-city-day      luma 65
         'bg-h38.jpg',   # Linear       supercars-dusk     luma 20
         'bg-h50.jpg'],  # CleanShot X  desk-city-day      luma 64
    arco=['I manage all my tasks here and plan', 'the day in 30 seconds.',
          '', 'Focus mode puts every distraction', 'away.', '',
          'My holy grail.'],
    tools=[
        ('Claude',
         ['Claude Projects keep your files and instructions attached to every chat inside them.',
          'You stop losing the first ten minutes of a session re-explaining the project.']),
        ('Raycast',
         ['Raycast clipboard history searches everything you copied, weeks back.',
          'The link you lost on tuesday costs two keystrokes instead of twenty minutes.']),
        ('Linear',
         ['Linear cycles carry unfinished issues into the next one on their own.',
          'Nobody spends friday afternoon working out what did and did not get done.']),
        ('CleanShot X',
         ['CleanShot X pins a screenshot so it floats above every other window.',
          'You copy from it without the window switching that eats half an afternoon.']),
    ])
