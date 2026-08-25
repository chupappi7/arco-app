#!/usr/bin/env python3
"""schedule-not-personality: discipline pillar, tools-post structure.

Method-led, so slides 1, 3, 4 and 5 carry a numbered badge instead of an app
icon. Same badge box, same title position, same dashed body as a tools post,
because earlier discipline posts dropped all three and read as prose.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, rule_slide, hook_slide, assert_varied,
                     next_arco_angle, record_post_tools, pick_hook_bg)

OUT = '/Users/thinh/SIXSIX/arco-app/drafts/schedule-not-personality'
os.makedirs(OUT, exist_ok=True)

BGS = [pick_hook_bg(),
       'bg-h21.jpg',   # rule 1   lounge-night
       'bg-h35.jpg',   # arco     supercars-dusk
       'bg-h45.jpg',   # rule 3   window-silhouette (the one person)
       'bg-h34.jpg',   # rule 4   desk-empty-day
       'bg-h24.jpg']   # rule 5   lounge-night

assert_varied(BGS)

hook_slide(BGS[0], ['discipline', 'is a schedule, not a personality'],
           f'{OUT}/01.jpg')

rule_slide(BGS[1], 1, 'Decide the night before', [
    'Write tomorrow’s first task before',
    'you go to sleep.',
    '',
    'You wake into an instruction, not a',
    'decision you have to win.',
], f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-arco.png', '2. ARCO', next_arco_angle(), f'{OUT}/03.jpg')

rule_slide(BGS[3], 3, 'Shrink the start', [
    'Set ten minutes and give yourself',
    'permission to stop after.',
    '',
    'The resistance is to starting. Past',
    'that the timer stops mattering.',
], f'{OUT}/04.jpg')

rule_slide(BGS[4], 4, 'Same two hours, daily', [
    'Keep the slot even on the days you',
    'sit there and do almost nothing.',
    '',
    'A slot you always keep costs no',
    'willpower to walk into.',
], f'{OUT}/05.jpg')

rule_slide(BGS[5], 5, 'Another room, not face down', [
    'Face down is one reach away. The',
    'next room is a decision.',
    '',
    'Put distance in the way and you',
    'stop needing to resist it.',
], f'{OUT}/06.jpg')

record_post_tools('schedule-not-personality', ['ARCO'])
print('\nbackgrounds:', ', '.join(BGS))
