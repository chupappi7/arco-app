#!/usr/bin/env python3
"""keep-five-8: "the 5 apps i would keep / if i deleted everything else".

  hook      least recently used of hook_rules.eligible(pillar='tools') on
            2026-09-26.
  roster    ARCO, Claude, Notion, CapCut, Figma. Claude is the LLM (last seen
            in keep-five-7 and run-it-all-at-19-2). The hook asks what
            survives a cull, so every slide teaches a capability that makes
            another app unnecessary: Claude writing real Office files, Notion
            Mail labelling the inbox from a plain-words rule, CapCut fixing
            the audio in the editor, Figma Sites publishing the design. None
            of these points appear in any caption in hooks.json.
  ARCO      title carries the current store name, App Blocker & Focus: ARCO.
            THEME 'planning'; next_arco_angle drew v10, written out below so
            a rebuild renders the copy that shipped.
  photos    gen-daily-batch walk: hook from the unused frames, and bright,
            per the 2026-09-26 hook redos: bg-h34, a white room with the
            monitors off. App frames under BAND_MAX_LUMA, no hook-only vibe,
            no monitor wall behind the copy, no adjacent vibe repeat, no
            person, nothing from wish-i-knew-at-17-7.

  01 hook      bg-h34  desk-empty-day
  02 ARCO      bg-h22  lounge-day
  03 Claude    bg-h37  supercars-dusk
  04 Notion    bg-n04  villa-day
  05 CapCut    bg-h24  lounge-night
  06 Figma     bg-h35  supercars-dusk

Usage:
    python3 tools/gen-keep-five-8.py            # every slide
    python3 tools/gen-keep-five-8.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)
from PIL import Image, ImageDraw

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'keep-five-8'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Claude', 'Notion', 'CapCut', 'Figma']
TITLES = ['1. App Blocker & Focus: ARCO', '2. Claude', '3. Notion',
          '4. CapCut', '5. Figma']

BGS = ['bg-h34.jpg',   # 01 hook        desk-empty-day
       'bg-h22.jpg',   # 02 ARCO        lounge-day
       'bg-h37.jpg',   # 03 Claude      supercars-dusk
       'bg-n04.jpg',   # 04 Notion      villa-day
       'bg-h24.jpg',   # 05 CapCut      lounge-night
       'bg-h35.jpg']   # 06 Figma       supercars-dusk

ARCO_BODY = [
    'I manage all my tasks here and plan',
    'the day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'The one I actually open every day.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Claude': [
    'Claude makes real Excel, Word and',
    'PowerPoint files you download.',
    '',
    'The budget and the deck come back',
    'as files, not text to paste in.',
 ],
 'Notion': [
    'Notion Mail labels incoming email',
    'from a rule you write in plain words.',
    '',
    'Receipts and newsletters are sorted',
    'before you ever open the inbox.',
 ],
 'CapCut': [
    'Enhance voice turns a phone',
    'recording into clean studio audio.',
    '',
    'The edit and the sound fix happen',
    'in one app, with no mic to buy.',
 ],
 'Figma': [
    'Figma Sites publishes a design as a',
    'live website from the same file.',
    '',
    'The landing page goes up with no',
    'site builder and no code.',
 ],
}

BODY_MAX_W = 820


def assert_body_fits(body):
    f = c.font(50, 'Semibold')
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    for tool, lines in body.items():
        for ln in lines:
            if ln and d.textbbox((0, 0), ln, font=f)[2] > BODY_MAX_W:
                raise SystemExit(f'{tool}: "{ln}" is over {BODY_MAX_W}px')


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    # Judge background freshness against the post just before this one, so
    # a rebuild after later posts still passes.
    full = c.bg_history
    def upto_here():
        h = full()
        idx = [i for i, e in enumerate(h) if e['topic'] == TOPIC]
        return h[:idx[0] + 1] if idx else h
    c.bg_history = upto_here
    try:
        preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    finally:
        c.bg_history = full
    assert_body_fits(BODY)
    for bg in BGS[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        # pick_hook_bg ignores prefer while night-desk frames are unused,
        # so the chosen frame is logged directly.
        path = f'{c.SP}/hook_usage.json'
        log = json.load(open(path))
        if BGS[0] not in log:
            log.append(BGS[0])
            json.dump(log, open(path, 'w'), indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', icons=shelf)
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        app_slide(bg, icons[tool], TITLES[i], BODY[tool],
                  f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

    if only is None:
        if not any(e.get('topic') == TOPIC for e in c.tool_history()):
            record_post_tools(TOPIC, TOOLS)
        # record_post_bgs moves the entry to the end, which would reorder
        # the history on every rebuild; leave an unchanged entry in place.
        if not any(e['topic'] == TOPIC and e['bgs'] == BGS
                   for e in c.bg_history()):
            record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
