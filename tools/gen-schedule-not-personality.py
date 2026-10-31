#!/usr/bin/env python3
"""schedule-not-personality: discipline / is a schedule, not a personality.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    the rule it enforces, so willpower is not the mechanism.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle s1 [screentime,discipline,schedule], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _screentime_common import build

build(
    topic='schedule-not-personality',
    hook=['discipline', 'is a schedule, not a personality'],
    bgs=['bg-h64.jpg',   # hook         desk-led-neon      luma 23
         'bg-h49.jpg',   # ARCO         desk-city-day      luma 58
         'bg-h39.jpg',   # 2            supercars-dusk     luma 32
         'bg-h50.jpg',   # 3            desk-city-day      luma 64
         'bg-h45.jpg',   # 4            window-silhouette  luma 50 (the one person)
         'bg-h37.jpg'],  # 5            supercars-dusk     luma 23
    arco_lines=['Blocked Hours closes the apps on a', 'schedule I set once.',
                '', '9am arrives and the feeds simply', 'do not open.', '',
                'The one I would not delete.'],
    rules=[
        ('The hours are set on sunday', [
            "Write the week's blocked hours once,",
            'at a time you are not in them.',
            '',
            'Monday morning has no decision in',
            'it, only a timetable.',
        ]),
        ('The rule names the apps', [
            'Pick the exact list of apps, not a',
            'vague intention to use less.',
            '',
            'A rule you can check is a rule.',
            'A mood is not one.',
        ]),
        ('Same hours every day', [
            'Keep the window identical rather',
            'than tuning it each morning.',
            '',
            'A schedule you negotiate with is',
            'back to being a personality.',
        ]),
        ('Someone else can see it', [
            'Share the week with one person who',
            'will ask you about it.',
            '',
            'The rule stops depending on who',
            'you are at 9pm.',
        ]),
    ])
