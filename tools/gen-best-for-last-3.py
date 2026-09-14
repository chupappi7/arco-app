#!/usr/bin/env python3
"""best-for-last-3: the third outing of the "5 tools to stay productive" hook.

hook_rules.eligible(pillar='tools') returns five hooks; the two ahead of this
one went to ten-x-5 and work-by-noon-5 in the same batch, so this is the next
in line (best-for-last-2, nine posts back). It goes out verbatim. The build
follows gen-best-for-last-2.py: icon shelf under the headline, ARCO leading,
one teaching point per app, mechanism then consequence.

Nothing of the earlier best-for-last posts carries over except the hook:

  roster ARCO, Claude, Notion, Canva, Higgsfield. Exactly one LLM (Claude,
         five posts back on app-in-a-weekend). Nothing tagged 'seller'. No
         overlap with either earlier best-for-last roster.
  copy   every point is a capability no caption in tools/hooks.json has
         taught. Claude has carried the agents-in-parallel line (keep-five
         1-3), MCP, Styles, draft-tightening and the built-in-chat tool, so
         this slide teaches Claude Code's checkpoints and rewind. Notion has
         carried the repeating template, button blocks, synced blocks,
         rollups, forms, the clipper and Notion AI; Notion Calendar laying
         database dates over the real calendar is new. Canva has carried the
         brand kit, doc-to-slides, the whiteboard, recorded presentations
         and bulk create; the one-click resize into every format is new.
         Higgsfield has only ever taught batch frames from one prompt
         (ten-x-3); the consistent character from your own photos is new.
  ARCO   "stay productive" asks how the day is run, so THEME is 'planning'.
         next_arco_angle('planning') -> v4, drawn at compose time and frozen
         here so a rebuild cannot hand this post different copy. The
         30-seconds line last carried this hook on best-for-last-2 as v9;
         v4 is its second outing here, in different words, which is what
         the rotation is for.
  photos hook bg-h34 is unused as a hook (desk-empty-day, shelf 77.2 sd
         53.5; bg-n04 and bg-h49 went to the other two posts of this batch).
         App frames walked with the gen-daily-batch gates: no hook-only vibe
         past slide 1, every copy band under BAND_MAX_LUMA on the gradient
         it renders with, no adjacent vibe repeat, no person at all, and
         nothing that appeared in work-by-noon-5 (BG_COOLDOWN = 1).

  01 hook        bg-h34  desk-empty-day  shelf zone luma 77.2, sd 53.5
  02 ARCO        bg-h36  supercars-dusk  band luma 20.3
  03 Claude      bg-h24  lounge-night    band luma 31.8 on GRAD_DARK
  04 Notion      bg-h39  supercars-dusk  band luma 22.3 on GRAD_DARK
  05 Canva       bg-h20  lounge-day      band luma 43.3 on GRAD_DARK
  06 Higgsfield  bg-n01  villa-day       band luma 42.5 on GRAD_DARK

Usage:
    python3 tools/gen-best-for-last-3.py            # every slide
    python3 tools/gen-best-for-last-3.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'best-for-last-3'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 tools to stay productive', 'i saved the best for last']
PILLAR = 'tools'
# "stay productive" is a question about how the whole day is run, so ARCO
# answers on a planning angle rather than a study or screentime one.
THEME = 'planning'

TOOLS = ['ARCO', 'Claude', 'Notion', 'Canva', 'Higgsfield']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Claude', '3. Notion',
          '4. Canva', '5. Higgsfield']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-claude.jpg', 'icon-notion.jpg',
         'icon-canva.png', 'icon-higgsfield.jpg']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h34.jpg',   # 01 hook        desk-empty-day  unused as a hook
       'bg-h36.jpg',   # 02 ARCO        supercars-dusk  band luma 20.3
       'bg-h24.jpg',   # 03 Claude      lounge-night    band luma 31.8 dark
       'bg-h39.jpg',   # 04 Notion      supercars-dusk  band luma 22.3 dark
       'bg-h20.jpg',   # 05 Canva       lounge-day      band luma 43.3 dark
       'bg-n01.jpg']   # 06 Higgsfield  villa-day       band luma 42.5 dark

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h36.jpg': GRAD}

# Angle v4 from arco_angles.json, drawn via next_arco_angle('planning') at
# compose time and written out literally: the rotating call moves the
# pointer, so a rebuild would come back with different copy and `--only 02`
# could not redo the slide that shipped.
ARCO_BODY = [
    'All my tasks live here and I plan the',
    'whole day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Claude': [
    'Claude Code checkpoints the code',
    'before every change it makes.',
    '',
    'You let it attempt the big rewrite',
    'because undo is one command.',
 ],
 'Notion': [
    'Notion Calendar lays database',
    'dates over your real calendar.',
    '',
    'Deadlines and meetings share one',
    'week view, nothing entered twice.',
 ],
 'Canva': [
    'Resize remakes one design into',
    'every format in a single pass.',
    '',
    'The post, the story and the',
    'banner come from one file.',
 ],
 'Higgsfield': [
    'Train it once on your face and',
    'every image keeps the same person.',
    '',
    'A week of visuals carries you in',
    'them with no shoot involved.',
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
