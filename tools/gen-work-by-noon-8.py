#!/usr/bin/env python3
"""work-by-noon-8: eighth outing of the by-noon hook, tools pillar.

  hook      "the tools i use to do / a full day of work by noon". Second
            least recently used tools hook hook_rules.eligible(pillar='tools')
            returned on 2026-09-20 (work-by-noon-7, seven posts back).
  roster    ARCO, Manus, Sentry, Cloudflare, Higgsfield. Manus is the LLM:
            the least recently used model (keep-five-5); this hook carried
            it once before on the first work-by-noon with the cloud machine
            point, which is not repeated.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Manus cloud machine, checklist plan with
            mid-run instructions, scheduled tasks, browser clicking, slide
            decks, wide research; Sentry session replay, suspect commit,
            crashes filed into Linear; Cloudflare tunnel, email routing;
            Higgsfield batch frames, face training, motion presets, speak.
            Running on a cron is burned across Supabase, GitHub and Zapier,
            so Cloudflare's cron triggers were not used either. Fresh here:
            Manus reading a data file into charts, Sentry Seer writing the
            root cause and the fix, the Cloudflare AI gateway caching model
            calls, Higgsfield Marketing Studio building ads from one product
            photo (confirmed against the Higgsfield model catalogue).
  ARCO      the hook is about getting the day's work done, so THEME is
            'planning'.
  photos    hook bg-h68 (desk-led-neon), the next hook-only frame after
            ten-x-8. App slides from non-hook-only vibes under BAND_MAX_LUMA,
            no adjacent vibe repeat, no person, nothing from the previous
            post (ten-x-8). bg-h22 also sits in rest-of-my-life, two posts
            back, which BG_COOLDOWN = 1 allows.

Usage:
    python3 tools/gen-work-by-noon-8.py            # every slide
    python3 tools/gen-work-by-noon-8.py --only 03  # one slide, for redos
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
TOPIC = 'work-by-noon-8'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to do', 'a full day of work by noon']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Manus', 'Sentry', 'Cloudflare', 'Higgsfield']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Manus', '3. Sentry',
          '4. Cloudflare', '5. Higgsfield']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h68.jpg',   # 01 hook        desk-led-neon
       'bg-h38.jpg',   # 02 ARCO        supercars-dusk   band luma 21.2
       'bg-n03.jpg',   # 03 Manus       villa-day        band luma 63.6
       'bg-h21.jpg',   # 04 Sentry      lounge-night     band luma 64.6
       'bg-h22.jpg',   # 05 Cloudflare  lounge-day       band luma 53.5
       'bg-h35.jpg']   # 06 Higgsfield  supercars-dusk   band luma 37.2

BODY = {
 'Manus': [
    'Give it the csv and it writes the',
    'analysis with the charts drawn.',
    '',
    'The weekly numbers come back as',
    'a page to read, not a file to open.',
 ],
 'Sentry': [
    'Seer reads the stack trace and the',
    'code and writes the root cause.',
    '',
    'The fix arrives as a pull request,',
    "so last night's crash is a diff",
    'waiting at 9.',
 ],
 'Cloudflare': [
    'AI gateway sits in front of your',
    'model calls and caches answers.',
    '',
    'The same prompt asked twice is',
    'billed once and answered at once.',
 ],
 'Higgsfield': [
    'Marketing Studio takes one product',
    'photo and builds the ad around it.',
    '',
    'A tiktok ready ad exists before',
    'anything has been filmed.',
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
