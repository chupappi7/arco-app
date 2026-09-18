#!/usr/bin/env python3
"""wish-i-knew-at-17-5: fifth outing of the at-17 hook, icon shelf, fresh roster.

"5 apps i wish someone / showed me at 17" (tools pillar). Second least
recently used of the three hooks hook_rules.eligible(pillar='tools')
returned on 2026-09-18: wish-i-knew-at-17-4, six posts back.

  roster    ARCO, Antigravity, GitHub, Canva, Figma. Antigravity is the
            LLM: second least recently used model (4x-productivity-8,
            seven posts back) and this hook has never carried it. At 17
            the things nobody shows you are that the tools that build
            real products are free to open: an agent that learns your
            project, any repo readable in an editor, cuts on the beat,
            a demo that runs inside the pitch.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Antigravity agent manager in parallel,
            browser click-through, plan doc; GitHub actions, schedules,
            pages, codespaces, branch protection, student pack, release
            notes, dependabot, auto merge; Canva resize, brand kit,
            whiteboard, doc to slides, presentation recording, bulk
            create, mockups, magic expand, content planner, locked brand
            templates; Figma components, auto layout, variables, dev mode,
            prototype links, community files. Fresh here: the Antigravity
            knowledge base, github.dev on the full stop key, Canva beat
            sync, live prototypes inside Figma Slides. Each verified by
            search on 2026-09-18 before it went on a slide.
  ARCO      at 17 the problem is the phone, so THEME is 'focus'.
  photos    hook bg-h63 (desk-led-neon), next hook-only frame without a
            person the hook log has not used after h58 went to
            4x-productivity-9. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, no person, nothing
            from the previous post (4x-productivity-9) and disjoint from
            keep-five-6 built in the same batch.

Usage:
    python3 tools/gen-wish-i-knew-at-17-5.py            # every slide
    python3 tools/gen-wish-i-knew-at-17-5.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)
from PIL import Image, ImageDraw

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'wish-i-knew-at-17-5'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i wish someone', 'showed me at 17']
PILLAR = 'tools'
THEME = 'focus'

TOOLS = ['ARCO', 'Antigravity', 'GitHub', 'Canva', 'Figma']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Antigravity', '3. GitHub',
          '4. Canva', '5. Figma']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h63.jpg',   # 01 hook         desk-led-neon
       'bg-h29.jpg',   # 02 ARCO         supercars-dusk    band luma 18.7
       'bg-h20.jpg',   # 03 Antigravity  lounge-day        band luma 67.0
       'bg-h39.jpg',   # 04 GitHub       supercars-dusk    band luma 35.8
       'bg-n03.jpg',   # 05 Canva        villa-day         band luma 63.6
       'bg-h31.jpg']   # 06 Figma        lounge-night      band luma 19.7

BODY = {
 'Antigravity': [
    'Antigravity saves what it learned',
    'about the project as knowledge.',
    '',
    'The second task starts knowing the',
    'setup the first one worked out.',
 ],
 'GitHub': [
    'Press the full stop key on any repo',
    'and it opens in vs code, in the tab.',
    '',
    'You read a real app the way its',
    'authors wrote it, file by file.',
 ],
 'Canva': [
    'Beat sync cuts the clips to the',
    'beats of the track you drop in.',
    '',
    'A montage lands on the music with',
    'no scrubbing to find the hits.',
 ],
 'Figma': [
    'Drop a prototype into a Figma Slides',
    'deck and it runs live on the slide.',
    '',
    'The demo gets tapped through in',
    'the pitch, not shown as a still.',
 ],
}

BODY_MAX_W = 800


def assert_body_fits(body):
    f = c.font(50, 'Semibold')
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    for tool, lines in body.items():
        for ln in lines:
            if not ln:
                continue
            w = d.textbbox((0, 0), ln, font=f)[2]
            if w > BODY_MAX_W:
                raise SystemExit(f'{tool}: "{ln}" is {w}px wide, over {BODY_MAX_W}')


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    assert_body_fits(BODY)
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
        if tool == 'ARCO':
            print('  ARCO angle:', ' / '.join(l for l in body if l))
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
