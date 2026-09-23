#!/usr/bin/env python3
"""run-it-all-at-19-3: third outing of the run-it-all hook, build pillar.

  hook      "everything i run my business on / at 19". One of the two hooks
            hook_rules.eligible(pillar='build') returned on 2026-09-23.
  roster    ARCO, ChatGPT, n8n, Canva, Cloudflare. ChatGPT is the LLM: after
            Gemini (business-at-19-3) the least recently used model
            (rest-of-my-life). 4x-productivity-10, built alongside, also
            carries ChatGPT and n8n with different points (editor reading,
            templates).
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: ChatGPT projects, branching, agent mode,
            canvas, custom instructions, memory, record mode, study mode,
            Drive, Codex, scheduled tasks; putting a product photo into a
            scene is Photoroom's point already. n8n agent node, self-hosting,
            pinned data; Canva brand kit, resize, bulk create, mockups,
            planner and the rest; Cloudflare tunnel, email routing, AI
            gateway. Fresh here: ChatGPT transparent PNGs, the n8n error
            workflow, Canva designs published as websites, Cloudflare R2
            with no bandwidth fees.
  ARCO      the hook is about running a business, so THEME is 'business';
            next_arco_angle('business') drew v8.
  photos    the gen-daily-batch walk: pick_hook_bg gave bg-h17, and the app
            slides come from frames under BAND_MAX_LUMA with no person (the
            hook has one), no adjacent vibe repeat, and nothing in the post
            recorded just before (BG_COOLDOWN = 1). Several builds ran
            alongside this one and kept rewriting bg_history, so frames
            were chosen to avoid their posts where the pool allowed and
            never to clash with the neighbouring post. Desk-city-day frames
            put the copy over monitors; they sit between darker scenes.

Usage:
    python3 tools/gen-run-it-all-at-19-3.py            # every slide
    python3 tools/gen-run-it-all-at-19-3.py --only 03  # one slide, for redos
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
TOPIC = 'run-it-all-at-19-3'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['everything i run my business on', 'at 19']
PILLAR = 'build'
THEME = 'business'

TOOLS = ['ARCO', 'ChatGPT', 'n8n', 'Canva', 'Cloudflare']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. n8n',
          '4. Canva', '5. Cloudflare']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# Drawn once with next_arco_angle(THEME) and written out, so a redo of one
# slide does not advance the rotation and change the copy.
ARCO_BODY = ['I manage all my tasks here and the', 'day is planned in half a minute.', '', 'Focus mode puts every distraction', 'away until I am done.', '', 'My holy grail.']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h17.jpg',   # 01 hook        desk-person-night  the one person
       'bg-h35.jpg',   # 02 ARCO        supercars-dusk     band luma 37.2
       'bg-h49.jpg',   # 03 ChatGPT     desk-city-day      band luma 54.8
       'bg-h31.jpg',   # 04 n8n         lounge-night       band luma 19.7
       'bg-h52.jpg',   # 05 Canva       desk-city-day      band luma 62.6
       'bg-h37.jpg']   # 06 Cloudflare  supercars-dusk     band luma 22.7

BODY = {
 'ChatGPT': [
    'Ask for a transparent background',
    'and it hands back a clean PNG.',
    '',
    'The logo drops straight onto the',
    'site with nothing to cut out.',
 ],
 'n8n': [
    'An error workflow runs whenever',
    'any other workflow fails.',
    '',
    'A broken automation messages you',
    'instead of failing quietly for days.',
 ],
 'Canva': [
    'Any design publishes as a website',
    'on a free Canva domain.',
    '',
    'The link in your bio is the same',
    'file you designed the post in.',
 ],
 'Cloudflare': [
    'R2 stores your files with no fee',
    'for the bandwidth they use.',
    '',
    'A video that blows up on your site',
    'does not come back as a bill.',
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

    c.assert_audience(TOOLS)
    # preflight only checks the LLM count for the tools pillar; build posts
    # carry exactly one model too.
    c.assert_one_llm(TOOLS)
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
        body = ARCO_BODY if tool == 'ARCO' else BODY[tool]
        if tool == 'ARCO':
            print('  ARCO angle:', ' / '.join(l for l in body if l))
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma '
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
