#!/usr/bin/env python3
"""ten-x-5: the fifth outing of the "how i 10x'd my productivity" hook.

hook_rules.eligible(pillar='tools') returns five hooks and this is the least
recently used of them (ten-x-4, eleven posts back), so it goes out verbatim.
The build follows gen-ten-x-4.py: icon shelf under the headline, ARCO leading
the roster, one teaching point per app, mechanism then consequence.

What is deliberately different from the four earlier ten-x posts:

  roster ARCO, Cursor, CleanShot X, Airtable, Photoroom. Exactly one LLM
         (Cursor, six posts back on keep-five-3; Manus carried three of the
         last four). Nothing tagged 'seller'.
  copy   every point is a capability no caption in tools/hooks.json has
         taught. Cursor's rules files went out on four-x-tools and its docs
         indexing on keep-five-3, so this post teaches Tab's next-edit
         prediction. CleanShot has taught scrolling capture, OCR, the corner
         overlay and GIF export; the self-uploading capture with the link on
         the clipboard is new. Airtable's form-to-row went out on pay-double,
         so Interfaces carry this slide. Photoroom's batch background removal
         went out on saved-hours; the generated scene behind a product shot
         is new.
  ARCO   ten-x and ten-x-2 both shipped "plans the day in 30 seconds" under
         this exact hook and ten-x-4 shipped the habits angle, so THEME is
         'insights': knowing where the hours go is a fresh mechanism for
         "10x" and i1 has never carried a post.
         next_arco_angle('insights') -> i1, drawn at compose time and frozen
         here so a rebuild cannot hand this post different copy.
  photos hook bg-n04 has never been used on a hook slide and has the calmest
         shelf zone of the twelve frames still unused (mean 55.3, sd 36.1;
         everything else sits 67-102 with sd 44-62). App frames walked with
         the gen-daily-batch gates: no hook-only vibe past slide 1, every
         copy band under BAND_MAX_LUMA on the gradient it renders with, no
         adjacent vibe repeat, no person at all, and nothing that appeared
         in five-that-stay (BG_COOLDOWN = 1).

  01 hook       bg-n04  villa-day       shelf zone luma 55.3, sd 36.1
  02 ARCO       bg-h31  lounge-night    band luma 19.7
  03 Cursor     bg-h29  supercars-dusk  band luma 18.7
  04 CleanShot  bg-h20  lounge-day      band luma 43.3 on GRAD_DARK
  05 Airtable   bg-h38  supercars-dusk  band luma 21.2
  06 Photoroom  bg-h24  lounge-night    band luma 31.8 on GRAD_DARK

Usage:
    python3 tools/gen-ten-x-5.py            # every slide
    python3 tools/gen-ten-x-5.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'ten-x-5'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ["how i 10x'd", 'my productivity']
PILLAR = 'tools'
# The 30-seconds planning line has carried this hook twice and the habits
# angle once, so ARCO answers on insights: you cannot multiply output while
# guessing where the hours go.
THEME = 'insights'

TOOLS = ['ARCO', 'Cursor', 'CleanShot X', 'Airtable', 'Photoroom']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Cursor', '3. CleanShot X',
          '4. Airtable', '5. Photoroom']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-cursor.png', 'icon-cleanshot.png',
         'icon-airtable.png', 'icon-photoroom.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-n04.jpg',   # 01 hook       villa-day       plainest unused shelf
       'bg-h31.jpg',   # 02 ARCO       lounge-night    band luma 19.7
       'bg-h29.jpg',   # 03 Cursor     supercars-dusk  band luma 18.7
       'bg-h20.jpg',   # 04 CleanShot  lounge-day      band luma 43.3 dark
       'bg-h38.jpg',   # 05 Airtable   supercars-dusk  band luma 21.2
       'bg-h24.jpg']   # 06 Photoroom  lounge-night    band luma 31.8 dark

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h31.jpg': GRAD, 'bg-h29.jpg': GRAD, 'bg-h38.jpg': GRAD}

# Angle i1 from arco_angles.json, drawn via next_arco_angle('insights') at
# compose time and written out literally: the rotating call moves the
# pointer, so a rebuild would come back with different copy and `--only 02`
# could not redo the slide that shipped.
ARCO_BODY = [
    'Insights show where the hours went,',
    'by app and by day.',
    '',
    'You stop guessing which one took',
    'the evening.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Cursor': [
    'Tab predicts your next edit and',
    'jumps the cursor to it.',
    '',
    'A rename ripples through the file',
    'on tab presses, not retyping.',
 ],
 'CleanShot X': [
    'Every capture uploads itself and',
    'puts the link on your clipboard.',
    '',
    'The screenshot is shared before a',
    'save dialog would have opened.',
 ],
 'Airtable': [
    'An Interface turns the base into',
    'a small app you hand to someone.',
    '',
    'The status gets updated by them,',
    'not by emails to you.',
 ],
 'Photoroom': [
    'Type the scene and it builds a',
    'background behind your product,',
    'shadows included.',
    '',
    'A phone photo on a desk becomes',
    'the studio shot without a studio.',
 ],
}


def band_luma(bg):
    """copy_band_luma, but measured with the gradient this slide will use.

    compose.copy_band_luma hardcodes the default gradient, so it would gate
    these frames on a render that never happens.
    """
    im = c.base_photo(bg, GRADS.get(bg, GRAD_DARK))
    im = c.frame_for_band(im, 600, 1300)
    c.adaptive_scrim(im, 600, 1300)
    g = im.convert('L').crop((85, 980, 1000, 1310))
    px = list(g.getdata())
    return sum(px) / len(px)


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:]:
        luma = band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        # Log the frame this post actually renders. pick_hook_bg gives unused
        # hook-only vibes priority over `prefer` and would hand back a
        # different background, burning one frame unused.
        path = f'{c.SP}/hook_usage.json'
        log = json.load(open(path))
        if BGS[0] not in log:
            log.append(BGS[0])
            json.dump(log, open(path, 'w'), indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', icons=SHELF)
        import hook_rules
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        app_slide(bg, icons[tool], TITLES[i], BODY[tool],
                  f'{OUT}/{n+1:02d}.jpg', grad=GRADS.get(bg, GRAD_DARK))
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma {band_luma(bg):.1f}')

    if only is None:
        # record_post_bgs de-dupes on topic; record_post_tools and
        # hook_rules.record append blindly, so a rebuild would log this post
        # twice and push an unrelated hook further down its cooldown.
        if not any(e.get('topic') == TOPIC for e in c.tool_history()):
            record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
