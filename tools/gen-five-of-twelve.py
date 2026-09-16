#!/usr/bin/env python3
"""five-of-twelve: another outing of the 12-apps hook, fresh roster.

"i pay for 12 apps / these 5 do all the work" (tools pillar, eligible; prior
outings were twelve-apps, do-all-the-work, five-do-the-work,
twelve-down-to-five and five-carry-twelve).

  roster    ARCO, Perplexity, Granola, Higgsfield, Airtable. Perplexity is
            the LLM: after Antigravity and Manus in the two posts before
            this one, it is the least recently used. five-carry-twelve ran
            Manus under this same hook, so Perplexity also keeps the hook's
            outings on different models.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Perplexity spaces, source-aimed search,
            labs dashboards, thread pages; Granola listens/notes write
            themselves, rewrite from audio, ask across calls; Higgsfield
            batch frames, face consistency, motion presets; Airtable forms,
            interfaces. Fresh here: Perplexity scheduled tasks, Granola
            meeting templates, Higgsfield Soul presets, Airtable Sync.
  photos    hook from the unused pool (bg-n03, villa-day), app slides from
            non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeats, no person, nothing from the previous post
            (wish-i-knew-at-17-3) and no app slide shared with
            4x-productivity-7 either.

Usage:
    python3 tools/gen-five-of-twelve.py            # every slide
    python3 tools/gen-five-of-twelve.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'five-of-twelve'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
PILLAR = 'tools'
# The hook promises the five that carry the workload, so ARCO answers on
# planning the day, the job it is paid to do.
THEME = 'planning'

TOOLS = ['ARCO', 'Perplexity', 'Granola', 'Higgsfield', 'Airtable']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Perplexity', '3. Granola',
          '4. Higgsfield', '5. Airtable']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-n03.jpg',   # 01 hook       villa-day
       'bg-h24.jpg',   # 02 ARCO       lounge-night      band luma 49.8
       'bg-h51.jpg',   # 03 Perplexity desk-city-day     band luma 61.7
       'bg-h88.jpg',   # 04 Granola    supercars-dusk    band luma 28.2
       'bg-n04.jpg',   # 05 Higgsfield villa-day         band luma 57.8
       'bg-h37.jpg']   # 06 Airtable   supercars-dusk    band luma 22.7

BODY = {
 'Perplexity': [
    'A task re-runs your search on',
    'a schedule you set once.',
    '',
    'The price drop or the news',
    'lands as a morning message.',
 ],
 'Granola': [
    'A template shapes the notes to',
    'the meeting type you pick.',
    '',
    'A sales call and a standup come',
    'back as different documents.',
 ],
 'Higgsfield': [
    'A Soul preset holds one',
    'photographic look by name.',
    '',
    'Every image I generate lands',
    'in the same aesthetic.',
 ],
 'Airtable': [
    "Sync mirrors another app's data",
    'into your base on its own.',
    '',
    'The report reads live numbers',
    'nobody pasted in by hand.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

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
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
        mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):16s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

    if only is None:
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
