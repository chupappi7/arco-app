#!/usr/bin/env python3
"""best-for-last-2: the "5 tools to stay productive" hook, icon-shelf opening.

hook_rules.eligible(pillar='tools') returns three hooks and this is the least
recently used of them, ten posts back on best-for-last, so it goes out
verbatim. The build follows gen-work-by-noon-4.py: a shelf of the five roster
icons under the headline so the viewer sees the post before reading a word,
ARCO leading, one teaching point per app, mechanism then consequence.

Nothing of the first best-for-last carries over except the hook:

  roster ARCO, Manus, Endel, Loom, Raycast. Exactly one LLM (Manus, thirteen
         posts back; Gemini, ChatGPT, Claude, Perplexity and Codex have
         carried the last five). Nothing tagged 'seller'. No overlap with the
         previous post's set, and only Raycast is shared with the original
         best-for-last, on a different capability.
  copy   every point is a capability no caption in tools/hooks.json has
         taught. That ruled out the obvious ones: Manus's cloud machine that
         keeps running after you close the tab has carried three captions
         (work-by-noon 1-3); Endel has always been "focus sound with no
         decisions"; Loom's auto title, summary and chapters went out on
         pay-double and its timestamped comments on killed-busywork; and
         Raycast has already taught clipboard history, quicklinks, snippets,
         floating notes, extensions, script commands, window snapping and
         Search Menu Items. So this post teaches the editable plan, the
         soundscape that tracks time of day and heart rate, the share link
         that works before the upload finishes, and app hotkeys.
  ARCO   "5 tools to stay productive" asks how the day is run, so THEME is
         'planning'. next_arco_angle('planning') would hand back v2, which is
         v1 with two words moved and whose every phrase is already in a
         caption. v9 is used instead: it has never shipped, and "Blocked
         Hours repeats it every weekday" is the one planning angle that names
         the recurrence rather than the schedule in the abstract.
  photos six frames, none of them in work-by-noon-4 or ten-x-4, walked with
         the gen-daily-batch guards: hook unused as a hook, app frames free
         of hook-only vibes, every copy band under BAND_MAX_LUMA, no adjacent
         vibe repeat, no person at all. bg-h35, h36, h38, h39 and h88 are one
         shoot, so the post takes exactly one of them (bg-h38).

The hook frame is picked for the shelf before it is picked for the text. The
icons land at y1105-1447, so the lower half of slide 1 has to be plain and
dark or they stop reading as a set. Measured over the shelf box on the real
render, no frame still unused as a hook passes: the six desk-city-day frames
put lit monitors behind the icons (73-86 luma, sd 50-59), the villa-day set
puts a lit house and a pool there (58-102), bg-h44 is a bright window (84.1),
bg-h34/n05/n06 are desks whose edges cut through the shelf, and bg-h35 is 35.0
at sd 39.5, low on average only because half the frame is black while a
headlight sits under the second row. bg-h59 is used instead: 10.4 luma at sd
7.4, the second plainest lower half in the whole pool, and although
hook_usage.json has it logged it has never appeared in a post, so no viewer
has seen it.

As in gen-work-by-noon-4.py the brighter frames carry GRAD_DARK (f_bot 0.42)
rather than app_slide's default 0.68; BAND_MAX_LUMA is a mean and the default
ramp leaves highlights sitting behind the grey paragraph dashes.

  01 hook     bg-h59  desk-led-neon    shelf zone luma 10.4, sd 7.4
  02 ARCO     bg-h38  supercars-dusk   band luma 21.2
  03 Manus    bg-h21  lounge-night     band luma 41.5 dark
  04 Endel    bg-n05  desk-empty-day   band luma 37.5 dark
  05 Loom     bg-h11  lounge-day       band luma 53.9 dark, never shipped
  06 Raycast  bg-n03  villa-day        band luma 48.7 dark

Usage:
    python3 tools/gen-best-for-last-2.py            # every slide
    python3 tools/gen-best-for-last-2.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/arco-app'
TOPIC = 'best-for-last-2'
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
BGS = ['bg-h59.jpg',   # 01 hook     desk-led-neon   plain dark shelf zone
       'bg-h38.jpg',   # 02 ARCO     supercars-dusk  band luma 21.2
       'bg-h21.jpg',   # 03 Manus    lounge-night    band luma 41.5
       'bg-n05.jpg',   # 04 Endel    desk-empty-day  band luma 37.5
       'bg-h11.jpg',   # 05 Loom     lounge-day      band luma 53.9
       'bg-n03.jpg']   # 06 Raycast  villa-day       band luma 48.7

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h38.jpg': GRAD}

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
