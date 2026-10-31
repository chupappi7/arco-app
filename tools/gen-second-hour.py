#!/usr/bin/env python3
"""second-hour: starting is easy, staying is the part nobody builds for.

  hook    "the hard part is not starting / it is the second hour", new to
          hook_pool 2026-10-31 (pillar discipline, theme discipline).
  lens    what it does when the first hour's momentum is gone. Nothing here
          is a motivation trick, because motivation is the thing that has
          already run out by the time this hook applies.
  ARCO    angle a10: an hour of work is an hour, not forty minutes and a
          scroll. It is about erosion inside a session, which is the second
          hour's actual failure mode.
  pillar  discipline, carried by _screentime_common -- rule_slide serves both
          method-led pillars and the builder now takes the pillar from the
          hook rather than hardcoding screentime.
"""
from _screentime_common import build

build(
    topic='second-hour',
    hook=['the hard part is not starting', 'it is the second hour'],
    bgs=['bg-n07.jpg',   # hook         desk-led-neon      luma 34
         'bg-h32.jpg',   # ARCO         window-silhouette  luma 36 (the one person)
         'bg-h88.jpg',   # 2            supercars-dusk     luma 29
         'bg-h21.jpg',   # 3            lounge-night       luma 64
         'bg-h35.jpg',   # 4            supercars-dusk     luma 33
         'bg-h22.jpg'],  # 5            lounge-day         luma 53
    arco_lines=['Focus mode puts every distracting',
                'app away for the whole session.', '',
                'An hour of work is an hour now, not',
                'forty minutes and a scroll.', '', 'I get the time back.'],
    rules=[
        ('Set hour two before hour one', [
            'Put both blocks on the day while',
            'you are still planning it.', '',
            'Hour two starts without needing a',
            'decision you no longer have.']),
        ('Give the break an ending', [
            'Run the break on a timer instead',
            'of on how you feel.', '',
            'Ten minutes stops by itself.',
            'Open ended rest does not.']),
        ('Stop mid sentence', [
            'Leave the file open and the line',
            'unfinished when you break.', '',
            'Coming back is continuing, which',
            'is far cheaper than starting.']),
        ('The phone does not get a break', [
            'Walk away from the desk and leave',
            'the phone sitting on it.', '',
            'A scroll at minute three is how',
            'the second hour never happens.']),
    ])
