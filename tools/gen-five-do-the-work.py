#!/usr/bin/env python3
"""five-do-the-work: the five apps that carry the work when you pay for twelve.

A replica of wish-i-knew-at-17's build, not of its content. What is kept is the
shape that made it work: a number-forward first-person hook, the icon shelf
under it so the viewer sees five apps before reading a word, ARCO leading the
roster, and one teaching point per app -- what the feature does, then what it
lets the viewer go and do.

What changes is everything that would make it a repeat:

  hook   "i pay for 12 apps / these 5 do all the work", the least recently
         used eligible tools hook in hook_pool.json (the 17-year-old hook is
         four posts from returning). Same shape, different promise.
  roster ARCO, Claude, ClickUp, Raycast, CapCut. Exactly one LLM (Claude), and
         every name is tagged 'any', 'focus' or 'content' in tool_pool.json so
         assert_audience passes -- nothing from the 'seller' lane.
  copy   the hook asks which apps survive a cull, so THEME is 'planning' and
         ARCO answers on angle v14, added for this build: one app holding both
         the plan and the block, which is the consolidation the hook promised.
         The four other points -- Claude artifacts, ClickUp automations, a
         Raycast app hotkey, CapCut auto cutout -- appear in no caption in
         tools/hooks.json.
  photos six frames none of which were in the previous post, walked with the
         gen-daily-batch guards: hook unused as a hook and outside the
         cross-post cooldown, app frames free of hook-only vibes, every copy
         band under BAND_MAX_LUMA, no adjacent vibe repeat, one person at most.

Two things the guards do not catch had to be done by eye. First, the pool holds
near-duplicate frames: bg-h35 through bg-h39 and bg-h88 are all the same house
with the same two cars, and bg-h46 through bg-h52 are all the same chair, desk
and city window. The vibe rule only blocks ADJACENT repeats, so a first draft
of this post put bg-h35 on the hook and bg-h36 on slide 3 and the two read as
one photograph used twice. At most one frame from each cluster is used here.

Second, BAND_MAX_LUMA is a mean, and a mean passes a daylight frame whose copy
band averages 55 while carrying a blown-out sky right behind the text: the grey
paragraph dashes disappear into it. The previous post spent all three
lounge-night frames, so four of these five app slides are daylight, and they
carry GRAD_DARK instead of the default gradient -- f_bot 0.42 rather than 0.68,
which pulls the 97th-percentile luma behind the copy from about 140-160 down to
around 100, level with what the dark frames give for free.

  01 hook     bg-h45  window-silhouette   first hook outing, the one person
  02 ARCO     bg-h36  supercars-dusk      band luma 20.3, darkest, seven lines
  03 Claude   bg-h49  desk-city-day       band luma 54.8 -> 40.9 on GRAD_DARK
  04 ClickUp  bg-n04  villa-day           band luma 57.8 -> 38.7 on GRAD_DARK
  05 Raycast  bg-n06  desk-empty-day      band luma 53.6 -> 36.0 on GRAD_DARK
  06 CapCut   bg-h20  lounge-day          band luma 67.0 -> 43.3 on GRAD_DARK

Usage:
    python3 tools/gen-five-do-the-work.py            # every slide
    python3 tools/gen-five-do-the-work.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/arco-app'
TOPIC = 'five-do-the-work'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
PILLAR = 'tools'
# Paying for twelve and keeping five is a question about the day's setup, so
# ARCO answers on a planning angle (v14 below), not on a study block.

TOOLS = ['ARCO', 'Claude', 'ClickUp', 'Raycast', 'CapCut']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Claude', '3. ClickUp',
          '4. Raycast', '5. CapCut']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-claude.jpg', 'icon-clickup.jpg',
         'icon-raycast.png', 'icon-capcut.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h45.jpg',   # 01 hook     window-silhouette  (first hook outing)
       'bg-h36.jpg',   # 02 ARCO     supercars-dusk     band luma 20.3
       'bg-h49.jpg',   # 03 Claude   desk-city-day      band luma 40.9 dark
       'bg-n04.jpg',   # 04 ClickUp  villa-day          band luma 38.7 dark
       'bg-n06.jpg',   # 05 Raycast  desk-empty-day     band luma 36.0 dark
       'bg-h20.jpg']   # 06 CapCut   lounge-day         band luma 43.3 dark

# app_slide's default gradient. GRAD_DARK is the same ramp with a much lower
# floor, for the daylight frames whose highlights would otherwise sit right
# behind the copy. Keyed by background so the luma gate below measures each
# slide with the gradient it is actually rendered with, not the default.
GRAD = (0.85, 0.68, 300, 1250)
GRAD_DARK = (0.85, 0.42, 300, 1250)
GRADS = {'bg-h36.jpg': GRAD}

# Angle v14 from arco_angles.json, written out literally rather than drawn
# from next_arco_angle(THEME) at render time. The rotating call is right for a
# first build and it is what chose v14 here, but it makes the generator
# non-reproducible: re-running it moves the pointer and slide 02 comes back
# with different copy, so `--only 02` cannot redo the slide that shipped.
ARCO_BODY = [
    'One app holds the plan and the',
    'block that protects it.',
    '',
    'Tasks get a time on the timeline and',
    'Focus mode shuts the apps for it.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Claude': [
    'Ask for a tool and Claude builds a',
    'working one inside the chat.',
    '',
    'The tracker you were going to pay',
    'for exists in a minute.',
 ],
 'ClickUp': [
    'Automations run a rule on the board:',
    'status changes, the next task opens.',
    '',
    'The handoff you kept doing by hand',
    'happens without you.',
 ],
 'Raycast': [
    'Give an app a global hotkey and one',
    'key brings it forward or hides it.',
    '',
    'Switching stops being a hunt',
    'through windows.',
 ],
 'CapCut': [
    'Auto cutout lifts the subject out of',
    'a clip with no green screen.',
    '',
    'You can sit over your own screen',
    'recording in one project.',
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
        # Record the frame this post actually renders, rather than asking
        # pick_hook_bg to confirm it. pick_hook_bg gives unused hook-only
        # vibes priority over `prefer` and silently returns a different
        # background, so the version of this line copied from
        # gen-wish-i-knew-at-17.py credited bg-n09 for a hook drawn on
        # bg-h45: one frame burned unused, another left free to come back.
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
