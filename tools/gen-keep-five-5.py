#!/usr/bin/env python3
"""keep-five-5: fifth outing of the "5 apps i would keep" hook, icon shelf.

"the 5 apps i would keep / if i deleted everything else" (tools pillar).
Second least recently used of the four hooks hook_rules.eligible(
pillar='tools') returned on 2026-09-17: keep-five-4, seven posts back.

  roster    ARCO, Manus, GitHub, Canva, CleanShot X. Manus is the LLM:
            least recently used model (wish-i-knew-at-17-3, eight posts
            back) and this hook has never carried it. Five jobs, one app
            each: the day, the research, the code, the design, the screen.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Manus cloud machine, mid-run corrections,
            scheduled tasks, browser clicking, slide decks; GitHub actions,
            schedules, pages, codespaces, branch protection, student pack,
            release notes; Canva resize, brand kit, whiteboard, doc to
            slides, presentation recording, bulk create, mockups, magic
            expand; CleanShot scrolling capture, OCR, pin, overlay, gif,
            upload links. Fresh here: Manus wide research, Dependabot
            security PRs, the Canva content planner, CleanShot keystroke
            overlay on recordings.
  ARCO      the cull asks what runs the day, so THEME is 'planning'.
  photos    hook bg-h60 (desk-led-neon), next hook-only frame without a
            person the reset hook log has not used after h54 went to
            wish-i-knew-at-17-4. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, no person, nothing
            from the previous post (wish-i-knew-at-17-4) and disjoint from
            ten-x-7 built in the same batch.

Usage:
    python3 tools/gen-keep-five-5.py            # every slide
    python3 tools/gen-keep-five-5.py --only 03  # one slide, for redos
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
TOPIC = 'keep-five-5'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Manus', 'GitHub', 'Canva', 'CleanShot X']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Manus', '3. GitHub',
          '4. Canva', '5. CleanShot X']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h60.jpg',   # 01 hook         desk-led-neon
       'bg-h36.jpg',   # 02 ARCO         supercars-dusk    band luma 20.3
       'bg-h20.jpg',   # 03 Manus        lounge-day        band luma 67.0
       'bg-h37.jpg',   # 04 GitHub       supercars-dusk    band luma 22.7
       'bg-n04.jpg',   # 05 Canva        villa-day         band luma 57.8
       'bg-h24.jpg']   # 06 CleanShot X  lounge-night      band luma 49.8

BODY = {
 'Manus': [
    'Wide research runs one agent per',
    'item, a hundred at a time.',
    '',
    'Comparing 100 laptops comes back',
    'as one table, not one by one.',
 ],
 'GitHub': [
    'Dependabot opens a pull request',
    'the day a dependency gets a fix.',
    '',
    'A security patch is a merge button',
    'and not a morning of reading.',
 ],
 'Canva': [
    'The content planner schedules a',
    'design to tiktok or instagram.',
    '',
    'The week goes out from the same',
    'file it was designed in.',
 ],
 'CleanShot X': [
    'A recording shows every key you',
    'press on screen as you press it.',
    '',
    'A shortcut you demo gets read off',
    'the video, not explained twice.',
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
