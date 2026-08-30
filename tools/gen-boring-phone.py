#!/usr/bin/env python3
"""boring-phone: screentime pillar, method post.

The hook promises a phone that stopped being interesting, so every slide is
one thing that was done to it. app_slide is barred under a screentime hook
(assert_roster_allowed): five products do not explain why the phone got
boring, five changes do.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on rule slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at
most one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (rule_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'boring-phone'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['my phone is boring now', 'and it changed everything']
THEME = 'screentime'
BGS = ['bg-h31.jpg',   # hook   lounge-night
       'bg-h22.jpg',   # ARCO   lounge-day
       'bg-h24.jpg',   # rule 2 lounge-night
       'bg-h35.jpg',   # rule 3 supercars-dusk
       'bg-h45.jpg',   # rule 4 window-silhouette (the one person)
       'bg-h37.jpg']   # rule 5 supercars-dusk (bg-h49 rendered washed:
                       #        the copy landed on a bright sky and the
                       #        monitor bezels and the dashes disappeared)

preflight(TOPIC, ['ARCO'], BGS, pillar='screentime', hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

# The app leads on a numbered badge like every other slide: in a method post
# an app icon here would be the only icon in the carousel and would mark that
# slide as the advert. Copy comes from the screentime-tagged angles.
rule_slide(BGS[1], 1, 'ARCO: Day Planner & Focus',
           next_arco_angle(THEME), f'{OUT}/02.jpg')

rule_slide(BGS[2], 2, 'Empty the lock screen', [
    'Put every app in the scheduled',
    'summary and hide the previews.',
    '',
    'You pick the phone up, see a clock,',
    'and put it back down.',
], f'{OUT}/03.jpg')

rule_slide(BGS[3], 3, 'Unfollow until it runs out', [
    'Unfollow and mute everything you',
    'would not go looking for by name.',
    '',
    'The feed reaches the end in a',
    'minute instead of never.',
], f'{OUT}/04.jpg')

rule_slide(BGS[4], 4, 'Turn autoplay off', [
    'Switch off autoplay so the next',
    'video does not start itself.',
    '',
    'Every extra one needs a tap, and',
    'most nights you stop at the first.',
], f'{OUT}/05.jpg')

rule_slide(BGS[5], 5, 'Move the watching to a laptop', [
    'Keep the long stuff on a laptop',
    'and off the phone entirely.',
    '',
    'Sitting down to watch gives the',
    'session a start and an end.',
], f'{OUT}/06.jpg')

record_post_tools(TOPIC, ['ARCO'])
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
