#!/usr/bin/env python3
"""three-hours-back: screentime pillar, method post.

The hook promises hours back WITHOUT deleting anything, so every slide is a
change you make to a phone that still has all its apps on it. app_slide is
barred under a screentime hook (assert_roster_allowed): a roster of products
does not answer "how did you cut three hours", numbered steps do.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on rule slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at
most one person) and frozen so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (rule_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'three-hours-back'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['i cut 3 hours of screen time', 'without deleting a single app']
THEME = 'screentime'
BGS = ['bg-h34.jpg',   # hook   desk-empty-day
       'bg-h20.jpg',   # ARCO   lounge-day
       'bg-h21.jpg',   # rule 2 lounge-night
       'bg-h29.jpg',   # rule 3 supercars-dusk
       'bg-h32.jpg',   # rule 4 window-silhouette (the one person)
       'bg-h36.jpg']   # rule 5 supercars-dusk

preflight(TOPIC, ['ARCO'], BGS, pillar='screentime', hook=HOOK)

log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

# In a method pillar the app takes a numbered badge like every other slide,
# and it leads: the measurement is what the other four steps are aimed by.
# Its copy comes from the screentime-tagged angles so it answers this hook.
rule_slide(BGS[1], 1, 'ARCO: Day Planner & Focus',
           next_arco_angle(THEME), f'{OUT}/02.jpg')

rule_slide(BGS[2], 2, 'Sign out, do not delete', [
    'Log out of every feed app and',
    'remove it from autofill.',
    '',
    'The app is still on the phone and',
    'opening it now costs a password.',
], f'{OUT}/03.jpg')

rule_slide(BGS[3], 3, 'Off the home screen', [
    'Delete the icons and leave the',
    'apps in the App Library.',
    '',
    'Opening one means typing the name',
    'of what takes your evening.',
], f'{OUT}/04.jpg')

rule_slide(BGS[4], 4, 'Turn the notifications off', [
    'Switch off badges and banners for',
    'every feed app, not just sounds.',
    '',
    'Nothing pulls at you, so the app',
    'opens when you decide it does.',
], f'{OUT}/05.jpg')

rule_slide(BGS[5], 5, 'Give the scroll one slot', [
    'Keep one fixed window for it,',
    'thirty minutes after dinner.',
    '',
    'The scrolling has a place to go,',
    'so the other hours stop leaking.',
], f'{OUT}/06.jpg')

record_post_tools(TOPIC, ['ARCO'])
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
