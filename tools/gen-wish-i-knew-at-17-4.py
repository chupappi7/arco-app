#!/usr/bin/env python3
"""wish-i-knew-at-17-4: fourth outing of the at-17 hook, icon shelf, fresh roster.

"5 apps i wish someone / showed me at 17" (tools pillar). Least recently
used of the four hooks hook_rules.eligible(pillar='tools') returned on
2026-09-17: wish-i-knew-at-17-3, eight posts back.

  roster    ARCO, Perplexity, Obsidian, CapCut, Higgsfield. Perplexity is
            the LLM: second least recently used model (five-of-twelve,
            seven posts back) and this hook has never carried it at the
            shelf size. Obsidian and CapCut are what a 17 year old
            actually installs; Higgsfield is the content lane pick.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Perplexity spaces, source focus, labs,
            pages; Obsidian links, backlinks, bases, canvas, daily note
            template, block links, unlinked mentions, plain markdown;
            CapCut caption TTS, motion tracking, auto reframe, caption
            style apply-all, caption translation, auto cutout; Higgsfield
            batch prompts, face consistency, motion presets. Fresh here:
            Perplexity deep research, the Obsidian web clipper, CapCut
            long video to shorts, Higgsfield Speak.
  ARCO      at 17 the problem is the phone, so THEME is 'focus'.
  photos    hook bg-h54 (desk-led-warm), first hook-only frame without a
            person that the reset hook log has not used. App slides from
            non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeat, no person, nothing from the previous post
            (4x-productivity-8) and disjoint from keep-five-5 and ten-x-7
            built in the same batch. bg-h48 was rendered for the CapCut
            slide first and replaced: it clears the luma gate at 61 but
            the first paragraph landed across three monitors full of
            thumbnails. bg-n01 is a villa and a pool.

Usage:
    python3 tools/gen-wish-i-knew-at-17-4.py            # every slide
    python3 tools/gen-wish-i-knew-at-17-4.py --only 03  # one slide, for redos
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
TOPIC = 'wish-i-knew-at-17-4'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i wish someone', 'showed me at 17']
PILLAR = 'tools'
THEME = 'focus'

TOOLS = ['ARCO', 'Perplexity', 'Obsidian', 'CapCut', 'Higgsfield']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Perplexity', '3. Obsidian',
          '4. CapCut', '5. Higgsfield']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h54.jpg',   # 01 hook        desk-led-warm
       'bg-h29.jpg',   # 02 ARCO        supercars-dusk    band luma 18.7
       'bg-h22.jpg',   # 03 Perplexity  lounge-day        band luma 53.5
       'bg-h35.jpg',   # 04 Obsidian    supercars-dusk    band luma 37.2
       'bg-n01.jpg',   # 05 CapCut      villa-day         band luma 66.3
       'bg-h31.jpg']   # 06 Higgsfield  lounge-night      band luma 19.7

BODY = {
 'Perplexity': [
    'Deep research runs dozens of',
    'searches and writes the report.',
    '',
    'A topic that took an evening',
    'comes back sourced in minutes.',
 ],
 'Obsidian': [
    'The web clipper saves a page as a',
    'note with the title and url on it.',
    '',
    'An article stops living in a tab',
    'and links like any other note.',
 ],
 'CapCut': [
    'Long video to shorts cuts a full',
    'recording into captioned clips.',
    '',
    'One 20 minute video becomes a',
    'week of posts without scrubbing.',
 ],
 'Higgsfield': [
    'Speak takes a still character and',
    'a script and it says the lines.',
    '',
    'A presenter for the video exists',
    'with nobody on camera.',
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
