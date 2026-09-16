#!/usr/bin/env python3
"""work-by-noon-6: sixth outing of the by-noon hook, icon shelf, fresh roster.

"the tools i use to do / a full day of work by noon" (tools pillar). Third
least recently used of the hooks hook_rules.eligible(pillar='tools')
returned: work-by-noon-5, five posts back.

  roster    ARCO, Cursor, GitHub, PostHog, RevenueCat. Cursor is the LLM:
            the least recently used model of all (ten-x-5, seven posts
            back) and never before under this hook. PostHog and RevenueCat
            are the niche picks. Every tool is builder-lane: a morning that
            is the whole workday is the morning where the machines do the
            afternoon.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Cursor tab, rules files, docs indexing;
            GitHub actions on schedule, codespaces, dependabot, pages,
            student pack, branch protection; PostHog flags plus replay,
            autocapture; RevenueCat paywalls from the dashboard,
            experiments. Fresh here: Cursor background agents from Slack,
            GitHub generated release notes, PostHog targeted surveys,
            RevenueCat Customer Center.
  ARCO      a full day by noon is a planning question, THEME 'planning'.
  photos    hook from the frames never yet used on a hook (bg-h52,
            desk-city-day), gradient floor 0.40 for the shelf. App slides
            from non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeat, no person, nothing from the previous post (ten-x-6).
            The three posts built together (keep-five-4, ten-x-6, this)
            share no frame at all, so any of them rebuilds in any order
            without tripping assert_bg_fresh against the others.

Usage:
    python3 tools/gen-work-by-noon-6.py            # every slide
    python3 tools/gen-work-by-noon-6.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'work-by-noon-6'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to do', 'a full day of work by noon']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Cursor', 'GitHub', 'PostHog', 'RevenueCat']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Cursor', '3. GitHub',
          '4. PostHog', '5. RevenueCat']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h52.jpg',   # 01 hook        desk-city-day
       'bg-h24.jpg',   # 02 ARCO        lounge-night      band luma 49.8
       'bg-h88.jpg',   # 03 Cursor      supercars-dusk    band luma 28.2
       'bg-n06.jpg',   # 04 GitHub      desk-empty-day    band luma 53.6
       'bg-h39.jpg',   # 05 PostHog     supercars-dusk    band luma 35.8
       'bg-n03.jpg']   # 06 RevenueCat  villa-day         band luma 63.6

BODY = {
 'Cursor': [
    'Tag it in Slack and a cloud agent',
    'picks the task up from the thread.',
    '',
    'The bug reported in the channel is',
    'a pull request before the standup.',
 ],
 'GitHub': [
    'Tag a release and the notes write',
    'themselves from the merged PRs.',
    '',
    'The changelog is done the second',
    'the version goes out.',
 ],
 'PostHog': [
    'A survey shows only to users who',
    'just did the thing you care about.',
    '',
    'You ask why they cancelled at the',
    'moment it happens, not by email.',
 ],
 'RevenueCat': [
    'Customer Center lets users cancel,',
    'refund or restore inside the app.',
    '',
    'The support inbox stops filling',
    'with billing questions.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            c.pick_hook_bg(prefer=BGS[0])
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', grad=HOOK_GRAD, icons=shelf)
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):16s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

    if only is None:
        if not any(e.get('topic') == TOPIC for e in c.tool_history()):
            record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
