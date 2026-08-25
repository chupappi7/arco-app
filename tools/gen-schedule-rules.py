#!/usr/bin/env python3
"""schedule-rules: discipline pillar. Every slide argues the hook's claim.

The hook says discipline is a SCHEDULE, so all five slides are scheduling
mechanics. Nothing about motivation, environment or willpower, however good
the tip: those belong to a different hook.
"""
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, rule_slide, hook_slide, preflight,
                     record_post_tools, record_post_bgs, pick_hook_bg)

TOPIC = 'schedule-rules'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

BGS = ['bg-h05.jpg',
       'bg-h37.jpg',   # rule 1  supercars-dusk
       'bg-h31.jpg',   # arco    lounge-night
       'bg-h44.jpg',   # rule 3  window-silhouette (the one person)
       'bg-h38.jpg',   # rule 4  supercars-dusk (the white badge needs a
                       #         darker frame; on bg-h28 it vanished into
                       #         the white villa)
       'bg-h48.jpg']   # rule 5  desk-city-day

preflight(TOPIC, ['ARCO'], BGS, pillar='discipline')

hook_slide(BGS[0], ['discipline', 'is a schedule, not a personality'],
           f'{OUT}/01.jpg')

rule_slide(BGS[1], 1, 'Decide the night before', [
    'Write tomorrow’s first task before',
    'you go to sleep.',
    '',
    'You wake into an instruction, not a',
    'decision you have to win.',
], f'{OUT}/02.jpg')

# The app's own slide keeps its logo instead of a numbered badge; the badge
# and the icon sit in the same box, so the format stays uniform and no slide
# carries the number twice.
app_slide(BGS[2], 'icon-arco.png', 'ARCO', [
    'I manage all my tasks here and the',
    'day takes 30 seconds to plan.',
    '',
    'Blocked Hours closes the apps on a',
    'schedule, so 9am needs no decision.',
], f'{OUT}/03.jpg')

rule_slide(BGS[3], 3, 'Two fixed hours, daily', [
    'Keep the same slot even on the days',
    'you sit there and do almost nothing.',
    '',
    'A slot you never move stops being a',
    'thing you have to talk yourself into.',
], f'{OUT}/04.jpg')

rule_slide(BGS[4], 4, 'Give the task an end time', [
    'Put a finish on it, not just a start,',
    'and hold it.',
    '',
    'Work stops expanding once the clock',
    'decides how much fits.',
], f'{OUT}/05.jpg')

rule_slide(BGS[5], 5, 'Repeat it, do not re-decide it', [
    'Anything you do weekly goes on a',
    'recurring slot, never on a list.',
    '',
    'A list asks you to choose again',
    'every week. A repeat never asks.',
], f'{OUT}/06.jpg')

record_post_tools(TOPIC, ['ARCO'])
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
