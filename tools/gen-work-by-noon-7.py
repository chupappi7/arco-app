#!/usr/bin/env python3
"""work-by-noon-7: seventh outing of the by-noon hook, icon shelf, fresh roster.

"the tools i use to do / a full day of work by noon" (tools pillar). Least
recently used of the three hooks hook_rules.eligible(pillar='tools')
returned on 2026-09-18: work-by-noon-6, eight posts back.

  roster    ARCO, Claude, GitHub, Granola, ElevenLabs. Claude is the LLM:
            least recently used model (ten-x-6, nine posts back) and this
            hook last carried Cursor. Every slide is something that got
            done before you sat down or without a second pass.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Claude styles, quizzes, artifacts, code
            checkpoints, terminal/files, skills, MCP, projects, subagents,
            plan mode, mockup to screen, folder cleanup, dictated drafts;
            GitHub actions, schedules, pages, codespaces, branch
            protection, student pack, release notes, dependabot; Granola
            no-bot listening, notes from audio, ask across calls;
            ElevenLabs voice clone, dubbing, reader app. Fresh here:
            Claude Code routines on a schedule, GitHub auto merge, Granola
            note templates, ElevenLabs voice isolator.
  ARCO      a day done by noon is a question about the plan, THEME
            'planning'.
  photos    hook bg-h55 (desk-led-warm), next hook-only frame without a
            person the hook log has not used. App slides from non-hook-only
            vibes under BAND_MAX_LUMA, no adjacent vibe repeat, no person,
            nothing from the previous post (ten-x-7) and disjoint from the
            other two posts built in the same batch.

Usage:
    python3 tools/gen-work-by-noon-7.py            # every slide
    python3 tools/gen-work-by-noon-7.py --only 03  # one slide, for redos
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
TOPIC = 'work-by-noon-7'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to do', 'a full day of work by noon']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Claude', 'GitHub', 'Granola', 'ElevenLabs']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Claude', '3. GitHub',
          '4. Granola', '5. ElevenLabs']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h55.jpg',   # 01 hook        desk-led-warm
       'bg-h39.jpg',   # 02 ARCO        supercars-dusk    band luma 35.8
       'bg-h20.jpg',   # 03 Claude      lounge-day        band luma 67.0
       'bg-h24.jpg',   # 04 GitHub      lounge-night      band luma 49.8
       'bg-n03.jpg',   # 05 Granola     villa-day         band luma 63.6
       'bg-h88.jpg']   # 06 ElevenLabs  supercars-dusk    band luma 28.2

BODY = {
 'Claude': [
    'A routine runs a Claude Code task',
    'on a schedule in the cloud.',
    '',
    'The nightly test run is a summary',
    'waiting when you sit down.',
 ],
 'GitHub': [
    'Turn on auto merge and the pull',
    'request merges when checks pass.',
    '',
    'A fix opened at 9 is on main by',
    '9:15 with nobody watching it.',
 ],
 'Granola': [
    'Pick a template before the call',
    'and the notes take that shape.',
    '',
    'A customer call ends as pains,',
    'quotes and next steps, no rewrite.',
 ],
 'ElevenLabs': [
    'Voice isolator strips the room',
    'noise off any recording.',
    '',
    'The take from the kitchen ships',
    'instead of being recorded again.',
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
