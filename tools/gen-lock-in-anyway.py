#!/usr/bin/env python3
"""lock-in-anyway: this is how you lock in / when you don't feel like it.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    what it does when the motivation is simply absent.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle s2 [screentime,discipline], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _screentime_common import build

build(
    topic='lock-in-anyway',
    hook=['this is how you lock in', "when you don't feel like it"],
    bgs=['bg-h65.jpg',   # hook         desk-led-neon      luma 38
         'bg-h46.jpg',   # ARCO         desk-city-day      luma 62
         'bg-h32.jpg',   # 2            window-silhouette  luma 36 (the one person)
         'bg-h36.jpg',   # 3            supercars-dusk     luma 24
         'bg-h34.jpg',   # 4            desk-empty-day     luma 61
         'bg-h88.jpg'],  # 5            supercars-dusk     luma 29
    arco_lines=['The block runs on a timetable, not', 'on willpower.', '',
                'There is no decision left to make', 'when the hour starts.',
                '', 'My holy grail.'],
    rules=[
        ('Start at five minutes', [
            'Set the block to five minutes when',
            'you cannot face a full hour.',
            '',
            'Starting was the only part that',
            'needed motivation.',
        ]),
        ('The desk is already set', [
            'Leave the file open and the tab',
            'ready from the night before.',
            '',
            'There is nothing to set up on the',
            'morning you feel like nothing.',
        ]),
        ('Lower the bar, not the block', [
            'Keep the hour, change what counts',
            'as finishing it.',
            '',
            'You end the day having done the',
            'block, so tomorrow is not a restart.',
        ]),
        ('Do it badly on purpose', [
            'Decide the first pass is allowed',
            'to be rough before you start.',
            '',
            'Most days the work does not need',
            'you to feel like doing it.',
        ]),
    ])
