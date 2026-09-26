#!/usr/bin/env python3
"""ten-x-9: "how i 10x'd / my productivity".

  hook      third least recently used of hook_rules.eligible(pillar='tools')
            on 2026-09-26 (keep-five-8 and rest-of-my-life-2, built
            alongside, took the first two).
  roster    ARCO, Manus, Zapier, ClickUp, Descript. Manus is the LLM (last
            seen in best-for-last-6). The hook promises output multiplied,
            so every slide teaches a job that stops needing you: Manus
            building and hosting a site from one request, the Zapier Email
            Parser turning mail into rows, a ClickUp recurring task that
            recreates itself on close, Descript Eye Contact letting a script
            be read in one take. None of these points appear in any caption
            in hooks.json.
  ARCO      title carries the current store name, App Blocker & Focus: ARCO.
            THEME 'planning'; next_arco_angle drew v12, written out below.
  photos    gen-daily-batch walk: hook bg-h51, an unused daylight city desk.
            App frames under BAND_MAX_LUMA, no hook-only vibe, no monitor
            wall behind the copy, no adjacent vibe repeat, no person,
            nothing from rest-of-my-life-2. 04 first drew bg-n06 and put
            the copy over its monitors; swapped to h24.

  01 hook      bg-h51  desk-city-day
  02 ARCO      bg-h31  lounge-night
  03 Manus     bg-h29  supercars-dusk
  04 Zapier    bg-h24  lounge-night
  05 ClickUp   bg-h22  lounge-day
  06 Descript  bg-h36  supercars-dusk

Usage:
    python3 tools/gen-ten-x-9.py            # every slide
    python3 tools/gen-ten-x-9.py --only 03  # one slide, for redos
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
TOPIC = 'ten-x-9'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ["how i 10x'd", 'my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Manus', 'Zapier', 'ClickUp', 'Descript']
TITLES = ['1. App Blocker & Focus: ARCO', '2. Manus', '3. Zapier',
          '4. ClickUp', '5. Descript']

BGS = ['bg-h51.jpg',   # 01 hook        desk-city-day
       'bg-h31.jpg',   # 02 ARCO        lounge-night
       'bg-h29.jpg',   # 03 Manus       supercars-dusk
       'bg-h24.jpg',   # 04 Zapier      lounge-night
       'bg-h22.jpg',   # 05 ClickUp     lounge-day
       'bg-h36.jpg']   # 06 Descript    supercars-dusk

ARCO_BODY = [
    'Tasks without a time wait in Anytime',
    'until the day has room for them.',
    '',
    'Focus mode blocks the apps I chose',
    'for exactly that block.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Manus': [
    'Ask Manus for a website and it',
    'builds it, hosts it and sends a link.',
    '',
    'The landing page is live before you',
    'have opened a code editor.',
 ],
 'Zapier': [
    'Email Parser gives you an address',
    'that pulls fields out of any email.',
    '',
    'An order email becomes a row in',
    'your sheet with nothing copied over.',
 ],
 'ClickUp': [
    'Close a recurring task and ClickUp',
    'makes the next one, date and all.',
    '',
    'The weekly invoice run never has',
    'to be written down again.',
 ],
 'Descript': [
    'Eye Contact moves your gaze to the',
    'lens while you read off the screen.',
    '',
    'You read the script in one take and',
    'still look straight at the viewer.',
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
