#!/usr/bin/env python3
"""ten-x-7: seventh outing of the 10x hook, icon shelf, fresh roster.

"how i 10x'd / my productivity" (tools pillar). Third least recently used
of the four hooks hook_rules.eligible(pillar='tools') returned on
2026-09-17: ten-x-6, six posts back.

  roster    ARCO, ChatGPT, n8n, Loom, Descript. ChatGPT is the LLM: third
            least recently used model (keep-five-4, six posts back) and
            this hook last carried it on ten-x-4 with the projects point.
            n8n is the automation pick, Loom and Descript the content lane.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: ChatGPT tasks, custom instructions, canvas,
            study mode, codex from the phone, drive connector, projects,
            memory, record mode; n8n self hosting, pinned steps; Loom
            auto chapters, timestamp comments, filler cut, instant link,
            drop-off; Descript transcript editing, filler removal, voice
            overdub, studio sound. Fresh here: ChatGPT agent mode, the
            n8n agent node calling workflows as tools, Loom turning a
            recording into a written doc, Descript Rooms local recording.
  ARCO      output multiplied is a question about the day, THEME 'planning'.
  photos    hook bg-h56 (desk-led-warm), next hook-only frame without a
            person the reset hook log has not used after h54 and h60 went
            to the other two posts of this batch. App slides from
            non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeat, one person (bg-h32, window-silhouette, slide 6),
            nothing from the previous post (keep-five-5). bg-h51 was
            rendered for the Loom slide first and replaced: the copy
            landed across three lit monitors. bg-n06 is an empty desk
            with the screens off; it last ran on 4x-productivity-8, three
            posts back, outside the cooldown.

Usage:
    python3 tools/gen-ten-x-7.py            # every slide
    python3 tools/gen-ten-x-7.py --only 03  # one slide, for redos
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
TOPIC = 'ten-x-7'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ["how i 10x'd", 'my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'ChatGPT', 'n8n', 'Loom', 'Descript']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. n8n',
          '4. Loom', '5. Descript']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h56.jpg',   # 01 hook      desk-led-warm
       'bg-h38.jpg',   # 02 ARCO      supercars-dusk     band luma 21.2
       'bg-h34.jpg',   # 03 ChatGPT   desk-empty-day     band luma 62.4
       'bg-h21.jpg',   # 04 n8n       lounge-night       band luma 64.6
       'bg-n06.jpg',   # 05 Loom      desk-empty-day     band luma 53.6
       'bg-h32.jpg']   # 06 Descript  window-silhouette  band luma 38.8, person

BODY = {
 'ChatGPT': [
    'Agent mode opens its own browser',
    'and fills the forms itself.',
    '',
    'You hand it the errand and come',
    'back to the confirmation page.',
 ],
 'n8n': [
    'An agent node picks which of your',
    'workflows to run from a message.',
    '',
    'One chat trigger routes an email,',
    'a lookup or a report, no branches.',
 ],
 'Loom': [
    'Record a walkthrough once and it',
    'writes the steps up as a doc.',
    '',
    'The how-to guide has screenshots',
    'in it and nobody typed it.',
 ],
 'Descript': [
    'Rooms records each guest on their',
    'own machine at full quality.',
    '',
    'A bad connection on the call',
    'never shows in the episode.',
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
