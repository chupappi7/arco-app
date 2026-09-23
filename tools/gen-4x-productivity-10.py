#!/usr/bin/env python3
"""4x-productivity-10: "the tools i used to / 4x my productivity".

The hook promises a multiplier on output, so every slide teaches a way to
skip a step you would otherwise do by hand: ChatGPT on the Mac writing the
fix into the open file, a GitHub keyword closing the issue on merge, an
Obsidian embed keeping one checklist in every note, an n8n template that
starts the automation nearly built. None of these points appear in any
caption in hooks.json.

The hook is among the least recently used in hook_rules.eligible(pillar='tools').
ARCO_BODY is angle v6 (theme planning) drawn once with next_arco_angle
and written out literally so a rebuild renders the copy that shipped.

Backgrounds picked with the gen-daily-batch walk: hook from the unused
hook-only frames, app frames with no hook-only vibe, copy_band_luma under
BAND_MAX_LUMA, no monitor wall behind the copy (bg-h46/h48/h49/h50 and
bg-n05 put bright screens under the title), no adjacent vibe repeat, at most one person, none in the
previous post (pay-for-twelve-3). The hook frame is the unused desk-led-neon frame
with the plainest remaining shelf zone (x100-980, y1105-1447): bg-h77 at 22.0 luma, sd 30.2 (bg-h75 went to pay-for-twelve-3).

  01 hook         bg-h77  desk-led-neon
  02 ARCO         bg-h20  lounge-day
  03 ChatGPT      bg-h38  supercars-dusk
  04 GitHub       bg-n03  villa-day
  05 Obsidian     bg-h39  supercars-dusk
  06 n8n          bg-h51  desk-city-day

Usage:
    python3 tools/gen-4x-productivity-10.py            # every slide
    python3 tools/gen-4x-productivity-10.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = '4x-productivity-10'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i used to', '4x my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'ChatGPT', 'GitHub', 'Obsidian', 'n8n']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. GitHub', '4. Obsidian', '5. n8n']

BGS = ['bg-h77.jpg',   # 01 hook        desk-led-neon
       'bg-h20.jpg',   # 02 ARCO        lounge-day
       'bg-h38.jpg',   # 03 ChatGPT     supercars-dusk
       'bg-n03.jpg',   # 04 GitHub      villa-day
       'bg-h39.jpg',   # 05 Obsidian    supercars-dusk
       'bg-h51.jpg']   # 06 n8n         desk-city-day

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
DARK_FRAMES = set()   # h38/h39 take GRAD_DARK: a white car sits under the body copy

ARCO_BODY = [
    'I manage all my tasks here and plan',
    'the day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away, Blocked Hours keeps them',
    'away on its own.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'ChatGPT': [
    'On a Mac it reads the code editor',
    'or terminal window you have open.',
    '',
    'It writes the fix into the file',
    'instead of a block you paste.',
 ],
 'GitHub': [
    'Write fixes #12 in a pull request',
    'and merging it closes issue 12.',
    '',
    'The to do list updates itself as',
    'the code lands, nothing ticked off.',
 ],
 'Obsidian': [
    'Put ! before a link and the whole',
    'note shows inside the one you are in.',
    '',
    'Change the checklist once and every',
    'note that embeds it shows the edit.',
 ],
 'n8n': [
    'The template library holds community',
    'workflows you import in one click.',
    '',
    'The automation you would build all',
    'afternoon starts nearly finished.',
 ],
}


def grad(bg):
    return GRAD if bg in DARK_FRAMES else GRAD_DARK


def band_luma(bg):
    """copy_band_luma, measured with the gradient this slide will use."""
    im = c.base_photo(bg, grad(bg))
    im = c.frame_for_band(im, 600, 1300)
    c.adaptive_scrim(im, 600, 1300)
    g = im.convert('L').crop((85, 980, 1000, 1310))
    px = list(g.getdata())
    return sum(px) / len(px)


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    # Other builds append to bg_history while this one runs, so "the last
    # post" drifts. Judge freshness against the post just before this one:
    # bg_history is cut at this topic for the length of preflight only, so
    # record_post_bgs below still sees the whole file.
    full = c.bg_history
    def upto_here():
        h = full()
        idx = [i for i, e in enumerate(h) if e['topic'] == TOPIC]
        return h[:idx[0] + 1] if idx else h
    c.bg_history = upto_here
    try:
        preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    finally:
        c.bg_history = full
    for bg in BGS[1:]:
        luma = band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        path = f'{c.SP}/hook_usage.json'
        log = json.load(open(path))
        if BGS[0] not in log:
            log.append(BGS[0])
            json.dump(log, open(path, 'w'), indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', icons=shelf)
        import hook_rules
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        app_slide(bg, icons[tool], TITLES[i], BODY[tool],
                  f'{OUT}/{n+1:02d}.jpg', grad=grad(bg))
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma {band_luma(bg):.1f}')

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
