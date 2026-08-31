#!/usr/bin/env python3
"""stack-at-19: the design-to-shipped stack, replicating launch-weekend.

launch-weekend worked as a build-pillar roster: a hook that promises a
concrete shipped outcome, then one LLM, ARCO, and three tools that carry the
thing the rest of the way. That shape is kept. Everything that would make
this read as the same post again is changed:

  * hook      "the tools i use to run my business / at 19 years old"
              (hook_pool, build pillar, last out 13 posts ago) instead of
              "launch an app / in one weekend".
  * roster    ARCO, Codex, GitHub, Figma, Framer. ARCO leads, which is what
              every post since ten-x does. Codex is the one LLM.
              "how i ship in a weekend" was the closer shape match but
              weekend-not-month already ran it over ARCO + Codex + Figma, so
              taking it here would have rebuilt that post, not this one.
  * photos    six backgrounds none of which launch-weekend used, and none
              used in the last 10 posts either: bg-h64/49/39/n06/52/n03.
  * copy      five teaching points that appear on no other slide and in no
              caption in hooks.json. Codex has been AGENTS.md, a sandbox PR
              and "writes the feature"; here it is review. GitHub has been
              Actions twice; here it is Dependabot. Figma has been auto
              layout, components and variables; here it is Dev Mode. Framer
              has been CMS collections and publish-from-canvas; here it is
              the built-in analytics.

Usage:
    python3 tools/gen-stack-at-19.py            # every slide
    python3 tools/gen-stack-at-19.py --only 04  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'stack-at-19'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to run my business', 'at 19 years old']
PILLAR = 'build'
# The hook asks what a business runs on, so ARCO answers on planning, not on
# a study block or a screen time number.
THEME = 'business'

TOOLS = ['ARCO', 'Codex', 'GitHub', 'Figma', 'Framer']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Codex', '3. GitHub',
          '4. Figma', '5. Framer']

# index 0 is the hook, 1..5 are the app slides in order.
# The luma gate is necessary and not sufficient: the first pass ran the app
# slides on the freshest photos in the pool, which were daylight offices at
# 54-64. They cleared BAND_MAX_LUMA and still failed the read, white copy
# dissolving into glass and sky, the same way ten-x-2's first pass did. Only
# dusk and night scenes hold five lines, so freshness is chosen inside that
# set rather than across the whole pool.
BGS = ['bg-h64.jpg',   # 01 hook    desk-led-neon      (first hook outing)
       'bg-h24.jpg',   # 02 ARCO    lounge-night       band luma 49.8
       'bg-h39.jpg',   # 03 Codex   supercars-dusk     band luma 35.8
       'bg-h31.jpg',   # 04 GitHub  lounge-night       band luma 19.7
       'bg-h88.jpg',   # 05 Figma   supercars-dusk     band luma 28.2
       'bg-h45.jpg']   # 06 Framer  window-silhouette  band luma 54.3

# The six photographs launch-weekend was shot on. Never reused here.
SOURCE_BGS = ['bg-h17.jpg', 'bg-h21.jpg', 'bg-h16.jpg', 'bg-h09.jpg',
              'bg-h02.jpg', 'bg-h04.jpg']

BODY = {
 'Codex': [
    'Tag it on a pull request and it',
    'reviews the diff line by line.',
    '',
    'Bugs get caught before the merge,',
    'with no one else on the team.',
 ],
 'GitHub': [
    'Dependabot watches your packages',
    'and opens the upgrade for you.',
    '',
    'A security fix arrives as something',
    'to merge, not something to find.',
 ],
 'Figma': [
    'Dev Mode hands you the spacing,',
    'colour and radius of any layer.',
    '',
    'You build the screen from numbers,',
    'not a screenshot and a guess.',
 ],
 'Framer': [
    'Analytics are built into the site,',
    'with no script to install.',
    '',
    'You see which page they land on and',
    'where they leave, from the editor.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    clash = sorted(set(BGS) & set(SOURCE_BGS))
    if clash:
        raise SystemExit(f'reuses launch-weekend photos: {", ".join(clash)}')

    # preflight only runs the LLM and cooldown guards on the tools pillar, and
    # this post is build, so those two are asked for by name.
    c.assert_one_llm(TOOLS)
    c.assert_fresh_tools(TOOLS)
    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for i, bg in enumerate(BGS[1:], start=1):
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            c.pick_hook_bg(prefer=BGS[0])
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
        mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):16s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

    if only is None:
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
