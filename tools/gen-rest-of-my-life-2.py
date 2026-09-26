#!/usr/bin/env python3
"""rest-of-my-life-2: "5 apps i will use / for the rest of my life".

  hook      second least recently used of hook_rules.eligible(pillar='tools')
            on 2026-09-26 (keep-five-8, built alongside, took the first).
  roster    ARCO, Codex, Obsidian, Canva, n8n. Codex is the LLM (last seen
            in launch-weekend-2). The hook promises apps that last, so every
            slide teaches a capability that keeps paying back: Codex handing
            a task to the cloud from the editor, Obsidian file recovery
            snapshots, Canva translating a finished design, an n8n webhook
            that gives a workflow its own link. None of these points appear
            in any caption in hooks.json.
  ARCO      title carries the current store name, App Blocker & Focus: ARCO.
            THEME 'planning'; next_arco_angle drew v11, written out below.
  photos    gen-daily-batch walk: hook bg-h33, an unused bright daylight
            frame with no screens. App frames under BAND_MAX_LUMA, no
            hook-only vibe, no monitor wall behind the copy, no adjacent vibe
            repeat, one person (h45), nothing from keep-five-8.

  01 hook      bg-h33  desk-empty-day
  02 ARCO      bg-h21  lounge-night
  03 Codex     bg-h38  supercars-dusk
  04 Obsidian  bg-n03  villa-day
  05 Canva     bg-h45  window-silhouette (the one person)
  06 n8n       bg-h20  lounge-day

Usage:
    python3 tools/gen-rest-of-my-life-2.py            # every slide
    python3 tools/gen-rest-of-my-life-2.py --only 03  # one slide, for redos
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
TOPIC = 'rest-of-my-life-2'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i will use', 'for the rest of my life']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Codex', 'Obsidian', 'Canva', 'n8n']
TITLES = ['1. App Blocker & Focus: ARCO', '2. Codex', '3. Obsidian',
          '4. Canva', '5. n8n']

BGS = ['bg-h33.jpg',   # 01 hook        desk-empty-day
       'bg-h21.jpg',   # 02 ARCO        lounge-night
       'bg-h38.jpg',   # 03 Codex       supercars-dusk
       'bg-n03.jpg',   # 04 Obsidian    villa-day
       'bg-h45.jpg',   # 05 Canva       window-silhouette
       'bg-h20.jpg']   # 06 n8n         lounge-day

ARCO_BODY = [
    'Every task I have gets a time on',
    "the day's timeline, not a list.",
    '',
    'Blocked Hours shuts the feeds for',
    'those windows without me asking.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Codex': [
    'Codex in VS Code sends a task to',
    'the cloud and pulls the diff back.',
    '',
    'The laptop stays free while it runs',
    'and the change lands in your editor.',
 ],
 'Obsidian': [
    'File recovery snapshots every note',
    'every few minutes while you write.',
    '',
    'A paragraph you cut yesterday',
    'comes back with no backup set up.',
 ],
 'Canva': [
    'Canva translates a finished design',
    'into another language in one click.',
    '',
    'The same post goes out in Spanish',
    'with the layout left as it was.',
 ],
 'n8n': [
    'A webhook node gives a workflow its',
    'own link that anything can call.',
    '',
    'A form, a button or another app',
    'starts the job by opening that link.',
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
