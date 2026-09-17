#!/usr/bin/env python3
"""best-for-last-4: fourth outing of the stay-productive hook, icon shelf.

"5 tools to stay productive / i saved the best for last" (tools pillar).
Second least recently used of the four hooks hook_rules.eligible(pillar=
'tools') returned on 2026-09-17: best-for-last-3, eight posts back.

  roster    ARCO, Gemini, ClickUp, Raycast, Granola. Gemini is the LLM:
            second least recently used model (ship-weekend-4, deleted in
            the dashboard, so its last surviving outing is work-by-noon-4).
            ClickUp, Raycast and Granola are all focus lane, which is what
            "stay productive" asks for; Granola is the niche pick.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Gemini deep research, gems, textbook
            upload, live screen share, gmail/drive; ClickUp views,
            dependencies, one task in many lists, automations, doc line to
            task; Raycast clipboard, quicklinks, snippets, floating notes,
            extensions, script commands, menu search, app hotkeys; Granola
            notes from audio, ask across calls, templates (five-of-twelve,
            deleted but built). Fresh here: Gemini answering from a
            youtube link, ClickUp email-to-task addresses, Raycast's next
            meeting in the menu bar with one-key join, Granola listening
            through the mac with no bot on the call.
  ARCO      "stay productive" asks how the day is run, THEME 'planning'.
  photos    hook bg-h59 (desk-led-neon), next least recently used hook-only
            frame without a person after h53 went to pay-for-twelve. App
            slides from non-hook-only vibes under BAND_MAX_LUMA, no
            adjacent vibe repeat, no person, nothing from pay-for-twelve
            or study-four-hours-2.

Usage:
    python3 tools/gen-best-for-last-4.py            # every slide
    python3 tools/gen-best-for-last-4.py --only 03  # one slide, for redos
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
TOPIC = 'best-for-last-4'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 tools to stay productive', 'i saved the best for last']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Gemini', 'ClickUp', 'Raycast', 'Granola']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Gemini', '3. ClickUp',
          '4. Raycast', '5. Granola']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h59.jpg',   # 01 hook     desk-led-neon
       'bg-h36.jpg',   # 02 ARCO     supercars-dusk    band luma 20.3
       'bg-n05.jpg',   # 03 Gemini   desk-empty-day    band luma 57.1
       'bg-h38.jpg',   # 04 ClickUp  supercars-dusk    band luma 21.2
       'bg-h50.jpg',   # 05 Raycast  desk-city-day     band luma 64.7
       'bg-h21.jpg']   # 06 Granola  lounge-night      band luma 64.6

BODY = {
 'Gemini': [
    'Paste a youtube link and Gemini',
    'answers from the video itself.',
    '',
    'A 40 minute lecture gets asked',
    'three questions instead of watched.',
 ],
 'ClickUp': [
    'Every ClickUp list has its own',
    'email address.',
    '',
    "Forward the client's mail and it",
    'is a task with the files attached.',
 ],
 'Raycast': [
    'Raycast puts the next meeting in',
    'the menu bar with a countdown.',
    '',
    'The call joins on one key, no',
    'hunt for the link in the invite.',
 ],
 'Granola': [
    'Granola listens through the mac,',
    'so no bot joins the call.',
    '',
    'It works on any meeting app and',
    'in person with the laptop open.',
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
