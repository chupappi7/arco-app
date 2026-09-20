#!/usr/bin/env python3
"""best-for-last-6: the best-for-last-2 post re-shot on new photographs.

A mechanical re-shoot: every hook line, title, body line, roster entry and
caption is byte-identical to gen-best-for-last-2.py; only the topic slug, the
repo path and the backgrounds change. The hook slide keeps its icon shelf and
every guard still runs. ARCO_BODY stays angle v9 written out literally, so no
angle pointer moves.

The hook is reused verbatim from the source, so mark_hook_used counts this
outing against the cooldown (best-for-last-5 was seven posts back, so the
hook is eligible).

Backgrounds picked with the gen-daily-batch walk: hook from the frames unused
as a hook and outside the cross-post cooldown, app frames with no hook-only
vibe, compose.copy_band_luma under BAND_MAX_LUMA, no adjacent vibe repeat, at
most one person, none in the last post (assert_bg_fresh) and none of the
source post's six photos (bg-h59/h38/h21/n05/h11/n03).

The hook frame is the one unused desk-led-neon frame whose lower half is
plain enough for the shelf: measured over the shelf box (x100-980,
y1105-1447) on the hook gradient, bg-h72 is 15.9 luma at sd 22.3, darker and
flatter than the source's bg-h59 (20.9 / 24.4 by the same measure); the next
candidates in walk order, bg-h69/h70/h71, all sit at 33 luma with a lit desk
edge crossing the second row.

As in the source the brighter frames carry GRAD_DARK (f_bot 0.42); the two
frames as dark as the source's bg-h38 (bg-h29, bg-h31) keep app_slide's
default ramp.

  01 hook     bg-h72  desk-led-neon      shelf zone luma 15.9, sd 22.3
  02 ARCO     bg-h20  lounge-day         copy_band_luma 67.0
  03 Manus    bg-h24  lounge-night       copy_band_luma 49.8
  04 Endel    bg-h29  supercars-dusk     copy_band_luma 18.7
  05 Loom     bg-h31  lounge-night       copy_band_luma 19.7
  06 Raycast  bg-h32  window-silhouette  copy_band_luma 38.8, the one person

Usage:
    python3 tools/gen-best-for-last-6.py            # every slide
    python3 tools/gen-best-for-last-6.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'best-for-last-6'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 tools to stay productive', 'i saved the best for last']
PILLAR = 'tools'
# "stay productive" is a question about how the whole day is run, so ARCO
# answers on a planning angle rather than a study or screentime one.
THEME = 'planning'

TOOLS = ['ARCO', 'Manus', 'Endel', 'Loom', 'Raycast']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Manus', '3. Endel',
          '4. Loom', '5. Raycast']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-manus.png', 'icon-endel.jpg',
         'icon-loom.png', 'icon-raycast.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h72.jpg',   # 01 hook     desk-led-neon      plain dark shelf zone
       'bg-h20.jpg',   # 02 ARCO     lounge-day         copy_band_luma 67.0
       'bg-h24.jpg',   # 03 Manus    lounge-night       copy_band_luma 49.8
       'bg-h29.jpg',   # 04 Endel    supercars-dusk     copy_band_luma 18.7
       'bg-h31.jpg',   # 05 Loom     lounge-night       copy_band_luma 19.7
       'bg-h32.jpg']   # 06 Raycast  window-silhouette  copy_band_luma 38.8

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h29.jpg': GRAD, 'bg-h31.jpg': GRAD}

# Angle v9 from arco_angles.json, written out literally rather than drawn from
# next_arco_angle(THEME) at render time: the rotating call moves the pointer,
# so a rebuild would come back with different copy and `--only 02` could not
# redo the slide that shipped.
ARCO_BODY = [
    'All of my tasks sit here and',
    'planning the day takes 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away, and Blocked Hours repeats it',
    'every weekday.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Manus': [
    'It writes the plan as a checklist',
    'and takes new instructions mid run.',
    '',
    'You correct step two while it works',
    'instead of rerunning the whole job.',
 ],
 'Endel': [
    'The sound is generated against the',
    'time of day and your heart rate.',
    '',
    'Hour three is not hour one looping,',
    'so it still works late in a session.',
 ],
 'Loom': [
    'The share link is live the second',
    'you stop recording, mid upload.',
    '',
    'You send the walkthrough as you',
    'finish it, with nothing to wait for.',
 ],
 'Raycast': [
    'Give an app a hotkey and the same',
    'keys put it away again.',
    '',
    'Your inbox opens and closes on two',
    'keys, so you never pass the dock.',
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
