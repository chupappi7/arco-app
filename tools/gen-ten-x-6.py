#!/usr/bin/env python3
"""ten-x-6: sixth outing of the 10x hook, icon shelf, fresh roster.

"how i 10x'd / my productivity" (tools pillar). Second least recently used
of the hooks hook_rules.eligible(pillar='tools') returned: ten-x-5, six
posts back.

  roster    ARCO, Claude, Supabase, Runway, Superwhisper. Claude is the
            LLM: with Cursor and ChatGPT it is one of the three least
            recently used (best-for-last-3, six posts back), and this hook
            has not carried it since ten-x-2. Runway is the niche pick; it
            has never been on a slide.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Claude agents in parallel, MCP, styles,
            projects, artifacts, quizzes, checkpoints, dictation cleanup,
            folder passes, skills; Supabase auth, RLS, table endpoints,
            realtime; Superwhisper modes, on-device, hotkey. Fresh here:
            Claude Code plan mode, Supabase Cron, Runway Aleph, Superwhisper
            vocabulary.
  ARCO      output multiplied is a question about the day, THEME 'planning'.
  photos    hook from the frames never yet used on a hook (bg-h50,
            desk-city-day), gradient floor 0.40 so the shelf sits on a
            dark chair rather than daylight. App slides from non-hook-only
            vibes under BAND_MAX_LUMA, no adjacent vibe repeat, no person,
            nothing from the previous post (keep-five-4). bg-h49 was
            rendered for the Superwhisper slide first and replaced: the
            copy landed across two lit monitors full of thumbnails. bg-n04
            is a villa and sky; it last ran two posts back, outside the
            cooldown.

Usage:
    python3 tools/gen-ten-x-6.py            # every slide
    python3 tools/gen-ten-x-6.py --only 03  # one slide, for redos
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
TOPIC = 'ten-x-6'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ["how i 10x'd", 'my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Claude', 'Supabase', 'Runway', 'Superwhisper']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Claude', '3. Supabase',
          '4. Runway', '5. Superwhisper']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h50.jpg',   # 01 hook          desk-city-day
       'bg-h36.jpg',   # 02 ARCO          supercars-dusk    band luma 20.3
       'bg-h34.jpg',   # 03 Claude        desk-empty-day    band luma 62.4
       'bg-h38.jpg',   # 04 Supabase      supercars-dusk    band luma 21.2
       'bg-h21.jpg',   # 05 Runway        lounge-night      band luma 64.6
       'bg-n04.jpg']   # 06 Superwhisper  villa-day         band luma 57.8

BODY = {
 'Claude': [
    'In Claude Code, plan mode reads',
    'the repo and proposes the change.',
    '',
    'You say yes once and it works',
    'through every file without asking.',
 ],
 'Supabase': [
    'Cron runs a query on a schedule',
    'from inside the database itself.',
    '',
    'The nightly cleanup or the weekly',
    'digest needs no server at all.',
 ],
 'Runway': [
    'Describe a change to a finished',
    'clip and Aleph re-renders it.',
    '',
    'The shot becomes night, or loses',
    'the crowd, with no reshoot.',
 ],
 'Superwhisper': [
    'A vocabulary list teaches it the',
    'names and terms you actually use.',
    '',
    'Dictated text comes back spelled',
    'right with no correction pass.',
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
