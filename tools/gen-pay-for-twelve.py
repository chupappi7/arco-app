#!/usr/bin/env python3
"""pay-for-twelve: seventh outing of the 12-apps hook, icon shelf, fresh roster.

"i pay for 12 apps / these 5 do all the work" (tools pillar). Least recently
used of the four hooks hook_rules.eligible(pillar='tools') returned on
2026-09-17 (five-of-twelve was deleted in the dashboard, so its outing was
forgotten and the hook came straight back).

  roster    ARCO, Codex, Zapier, Canva, Supabase. Codex is the LLM: least
            recently used model (business-at-19-2, eight posts back).
            Every tool is builder or content lane; nothing tagged seller.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Codex write/run/fix, sandbox+PR, AGENTS.md,
            PR review, phone start, screenshot input, parallel attempts,
            exec from one command, resume; Zapier schedule, filter, paths,
            digest; Canva resize, brand kit, whiteboard, doc-to-slides,
            recorded presentation, bulk create, mockups; Supabase auth,
            RLS, auto API, realtime, cron. Fresh here: the Codex sandbox
            (folder-scoped, network off), Zapier formatter steps, Canva
            Magic Expand, Supabase storage image transforms from the url.
  ARCO      "these 5 do all the work" is a how-the-day-runs question,
            THEME 'planning'.
  photos    hook bg-h53 (desk-led-warm): the hook rotation had gone through
            all 83 frames, so pick_hook_bg resets and h53 is the least
            recently used hook-only frame without a person. App slides from
            non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeat, no person, nothing from the previous post
            (study-four-hours-2). The three posts built together
            (pay-for-twelve, best-for-last-4, 4x-productivity-8) share no
            frame, so any of them rebuilds in any order.

Usage:
    python3 tools/gen-pay-for-twelve.py            # every slide
    python3 tools/gen-pay-for-twelve.py --only 03  # one slide, for redos
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
TOPIC = 'pay-for-twelve'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Codex', 'Zapier', 'Canva', 'Supabase']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Codex', '3. Zapier',
          '4. Canva', '5. Supabase']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h53.jpg',   # 01 hook      desk-led-warm
       'bg-h29.jpg',   # 02 ARCO      supercars-dusk    band luma 18.7
       'bg-h34.jpg',   # 03 Codex     desk-empty-day    band luma 62.4
       'bg-h35.jpg',   # 04 Zapier    supercars-dusk    band luma 37.2
       'bg-h49.jpg',   # 05 Canva     desk-city-day     band luma 54.8
       'bg-h24.jpg']   # 06 Supabase  lounge-night      band luma 49.8

BODY = {
 'Codex': [
    'The Codex sandbox reaches only the',
    'folder you opened, network off.',
    '',
    'Leave it on a task all afternoon',
    'and it cannot touch anything else.',
 ],
 'Zapier': [
    'A formatter step reshapes data on',
    'its way between two apps.',
    '',
    'The date a form collects lands in',
    'the invoice format, nothing typed.',
 ],
 'Canva': [
    'Magic Expand paints past the edge',
    'of a photo in any direction.',
    '',
    'A landscape shot becomes a full',
    '9:16 story with nothing cropped.',
 ],
 'Supabase': [
    'Storage resizes an image straight',
    'from the url, width in the link.',
    '',
    'One original goes up and every',
    'thumbnail is a link, not a file.',
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
