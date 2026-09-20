#!/usr/bin/env python3
"""ten-x-8: eighth outing of the 10x hook, tools pillar.

  hook      "how i 10x'd / my productivity". The least recently used tools
            hook hook_rules.eligible(pillar='tools') returned on 2026-09-20
            (ten-x-7, eight posts back).
  roster    ARCO, Cursor, Airtable, Superwhisper, Make. Cursor is the LLM:
            third least recently used model (pay-for-twelve-2); this hook
            last carried it on ten-x-5 with tab predictions.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Cursor tab predictions (twice), rules files,
            docs indexing, the slack cloud agent, bugbot; Airtable form to
            automation, interfaces (twice); Superwhisper any-app dictation,
            modes, on-device model, vocabulary, the iPhone keyboard; Make
            scenario view, error handler. Claude Code checkpoints are burned
            too, so Cursor's checkpoints were not used. Fresh here: Cmd K in
            Cursor's terminal writing the shell command, Airtable lookup
            fields across a link, Superwhisper folding selected text into a
            dictation, the Make data store.
  ARCO      the hook is about output, so THEME is 'planning'.
  photos    hook bg-h67 (desk-led-neon), the next hook-only frame after
            rest-of-my-life. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, no person, nothing from
            the previous post (rest-of-my-life).

Usage:
    python3 tools/gen-ten-x-8.py            # every slide
    python3 tools/gen-ten-x-8.py --only 03  # one slide, for redos
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
TOPIC = 'ten-x-8'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ["how i 10x'd", 'my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Cursor', 'Airtable', 'Superwhisper', 'Make']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Cursor', '3. Airtable',
          '4. Superwhisper', '5. Make']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h67.jpg',   # 01 hook          desk-led-neon
       'bg-h37.jpg',   # 02 ARCO          supercars-dusk   band luma 22.7
       'bg-n01.jpg',   # 03 Cursor        villa-day        band luma 66.3
       'bg-h24.jpg',   # 04 Airtable      lounge-night     band luma 49.8
       'bg-h34.jpg',   # 05 Superwhisper  desk-empty-day   band luma 62.4
       'bg-h88.jpg']   # 06 Make          supercars-dusk   band luma 28.2

BODY = {
 'Cursor': [
    'Cmd K in the terminal writes the',
    'shell command from a sentence.',
    '',
    'Find every file over 100mb runs',
    'without remembering a single flag.',
 ],
 'Airtable': [
    'Link two tables and a lookup field',
    'pulls any column across the link.',
    '',
    "The client's email sits on every",
    'invoice and is never typed twice.',
 ],
 'Superwhisper': [
    'A mode can read the text you have',
    'selected before you speak.',
    '',
    'Highlight an email, say the answer,',
    'and the reply comes out written.',
 ],
 'Make': [
    'A data store is a small database',
    'that lives inside your scenario.',
    '',
    'It remembers what it already sent,',
    'so no row goes out twice.',
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
