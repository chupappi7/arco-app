#!/usr/bin/env python3
"""4x-productivity-9: ninth outing of the 4x hook, icon shelf, fresh roster.

"the tools i used to / 4x my productivity" (tools pillar). Least recently
used of the three hooks hook_rules.eligible(pillar='tools') returned on
2026-09-18: 4x-productivity-8, seven posts back.

  roster    ARCO, Gemini, Raycast, Loom, Zapier. Gemini is the LLM: least
            recently used model (best-for-last-4, eight posts back) and
            this hook has never carried it at the shelf size. Every slide
            removes a step between deciding and done: the tab hop, the
            shortcut hunt, the re-record, the copy and paste into an app.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Gemini deep research, gems, textbook
            upload, live screen share, gmail and drive, youtube link;
            Raycast clipboard history, quicklinks, snippets, floating
            notes, extensions, script commands, menu search, app hotkeys,
            meeting countdown, window snap; Loom title and chapters,
            timestamp comments, filler removal, instant link, viewer
            analytics, walkthrough to doc; Zapier schedule, filter, paths,
            digest, formatter. Fresh here: Gemini in Chrome across open
            tabs, the Raycast hyper key, Loom live rewind, Zapier MCP.
            Each verified by search on 2026-09-18 before it went on a
            slide.
  ARCO      4x productivity is a how-the-day-runs question, THEME
            'planning'.
  photos    hook bg-h58 (desk-led-warm), next hook-only frame without a
            person the hook log has not used. App slides from non-hook-only
            vibes under BAND_MAX_LUMA, no adjacent vibe repeat, no person,
            nothing from the previous post (best-for-last-5) and disjoint
            from the other two posts built in the same batch. No
            desk-city-day frame: every one previewed so far puts the
            monitors in the copy band.

Usage:
    python3 tools/gen-4x-productivity-9.py            # every slide
    python3 tools/gen-4x-productivity-9.py --only 03  # one slide, for redos
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
TOPIC = '4x-productivity-9'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i used to', '4x my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Gemini', 'Raycast', 'Loom', 'Zapier']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Gemini', '3. Raycast',
          '4. Loom', '5. Zapier']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h58.jpg',   # 01 hook     desk-led-warm
       'bg-h38.jpg',   # 02 ARCO     supercars-dusk    band luma 21.2
       'bg-h22.jpg',   # 03 Gemini   lounge-day        band luma 53.5
       'bg-h36.jpg',   # 04 Raycast  supercars-dusk    band luma 20.3
       'bg-n04.jpg',   # 05 Loom     villa-day         band luma 57.8
       'bg-h24.jpg']   # 06 Zapier   lounge-night      band luma 49.8

BODY = {
 'Gemini': [
    'Gemini in Chrome reads the tab you',
    'are on and the ones open beside it.',
    '',
    'Two pricing pages get compared in',
    'the sidebar with nothing pasted.',
 ],
 'Raycast': [
    'Raycast turns caps lock into a',
    'hyper key, four modifiers in one.',
    '',
    'Every app gets a hotkey nothing',
    'else on the mac already uses.',
 ],
 'Loom': [
    'Live rewind backs the recording up',
    'and carries on from that spot.',
    '',
    'A stumble at minute four does not',
    'mean starting the take from zero.',
 ],
 'Zapier': [
    'Zapier MCP hands an AI agent your',
    'apps as tools it can call itself.',
    '',
    'The agent drafts the reply and',
    'sends it from gmail in the chat.',
 ],
}

# The body column runs from x=125; anything past ~800px wide starts crowding
# the right edge on a phone. Measured, not eyeballed.
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
