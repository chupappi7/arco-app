#!/usr/bin/env python3
"""best-for-last-5: fifth outing of the best-for-last hook, icon shelf.

"5 tools to stay productive / i saved the best for last" (tools pillar).
Third least recently used of the three hooks hook_rules.eligible(
pillar='tools') returned on 2026-09-18: best-for-last-4, six posts back.

  roster    ARCO, Codex, Linear, Canva, Superwhisper. Codex is the LLM:
            third least recently used model (pay-for-twelve, eight posts
            back) and this hook last carried Gemini. Every slide removes a
            pass you would otherwise do yourself: the UI check, the
            retyping, the fix-up, the typing.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Codex parallel attempts, screenshot input,
            resume, one-command runs, PR review, sandbox, phone start,
            AGENTS.md; Linear triage, cycles, branch-name auto close,
            sentry filing; Canva resize, brand kit, whiteboard, doc to
            slides, recording, bulk create, mockups, magic expand,
            content planner; Superwhisper vocabulary, modes, on-device,
            hotkey dictation. Fresh here: Codex browser check with
            screenshots on the PR, Linear Asks from slack, Canva brand
            template locked elements, Superwhisper iPhone keyboard.
  ARCO      staying productive is a question about the plan, THEME
            'planning'.
  photos    hook bg-h57 (desk-led-warm), next hook-only frame without a
            person the hook log has not used after h55 and h61 went to
            the other two posts of this batch. App slides from
            non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeat, one person (bg-h45, window-silhouette, slide 3),
            nothing from the previous post (pay-for-twelve-2). h21 last
            ran on ten-x-7, three posts back, outside the cooldown.

Usage:
    python3 tools/gen-best-for-last-5.py            # every slide
    python3 tools/gen-best-for-last-5.py --only 03  # one slide, for redos
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
TOPIC = 'best-for-last-5'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 tools to stay productive', 'i saved the best for last']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Codex', 'Linear', 'Canva', 'Superwhisper']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Codex', '3. Linear',
          '4. Canva', '5. Superwhisper']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h57.jpg',   # 01 hook          desk-led-warm
       'bg-h37.jpg',   # 02 ARCO          supercars-dusk     band luma 22.7
       'bg-h45.jpg',   # 03 Codex         window-silhouette  band luma 54.3, person
       'bg-h35.jpg',   # 04 Linear        supercars-dusk     band luma 37.2
       'bg-n01.jpg',   # 05 Canva         villa-day          band luma 66.3
       'bg-h21.jpg']   # 06 Superwhisper  lounge-night       band luma 64.6

BODY = {
 'Codex': [
    'Codex opens the screen it built',
    'in a browser and screenshots it.',
    '',
    'The pull request shows the UI',
    'before you read a line of code.',
 ],
 'Linear': [
    'Linear Asks turns a slack message',
    'into an issue with a thread link.',
    '',
    'The bug someone posted at lunch',
    'is on the board with no retyping.',
 ],
 'Canva': [
    'Lock the logo and layout on a',
    'brand template, leave the text.',
    '',
    'Whoever edits it changes the words',
    'and the layout stays on brand.',
 ],
 'Superwhisper': [
    'The iPhone version is a keyboard,',
    'so it dictates into any app.',
    '',
    'A message on the walk is typed',
    'before you reach the desk.',
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
