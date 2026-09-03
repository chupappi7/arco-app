#!/usr/bin/env python3
"""ten-x-4: the fourth outing of the "how i 10x'd my productivity" hook.

The hook is the least recently used eligible tools hook in hook_pool.json --
it last went out on ten-x-3, thirteen posts ago -- and it goes out verbatim.
The build follows gen-five-do-the-work.py: number-forward hook, the icon shelf
under it so the viewer sees five apps before reading a word, ARCO leading the
roster, one teaching point per app, mechanism then consequence.

What is deliberately different from the three earlier ten-x posts:

  roster ARCO, ChatGPT, Granola, CleanShot X, Zapier. Exactly one LLM
         (ChatGPT, which last appeared five posts ago), and every name is
         tagged 'any', 'focus' or 'build' in tool_pool.json, nothing from the
         'seller' lane.
  copy   every point is a capability no caption in tools/hooks.json has taught
         yet, which took real pruning: ChatGPT scheduled Tasks went out on
         "before-nine", CleanShot's scrolling capture on "before-nine" and
         both 4x-productivity posts, its OCR on "ten-x-2", its corner overlay
         on the lock-in-anyway posts, and Granola has carried "it writes the
         notes for you" six times. So this post teaches ChatGPT Projects,
         Granola's ask-across-every-call search, CleanShot's GIF recording,
         and the inbox address every Zap can be given.
  ARCO   the hook asks what multiplied the output, so THEME is 'planning'.
         The rotation's next unused planning angle is v2, which opens on
         "the day gets planned in 30 seconds" -- the exact line ten-x and
         ten-x-2 both already used under this same hook, so a third would
         teach a returning viewer nothing. v15 was written for this build
         instead: habits repeating into the timeline is the mechanism that
         answers "10x", and it is ARCO copy that has not shipped.
  photos six frames, none of them in the previous post, walked with the
         gen-daily-batch guards: hook unused as a hook, app frames free of
         hook-only vibes, every copy band under BAND_MAX_LUMA, no adjacent
         vibe repeat, one person at most.

The hook frame is picked for the shelf, not just for the hook text. The icons
land at y1105-1447, so the lower half of slide 1 has to be plain and dark or
they stop reading as a set. bg-h88 is a car on a flat sheet of water: the
shelf zone measures luma 35.0 at sd 6.5, the emptiest lower half in the pool.
Every other unused hook frame fails that test -- the desk-city-day cluster
puts monitors behind the icons, villa-day puts a lit house and a pool there,
and bg-h35/h39 are the same two cars as bg-h36, which shipped yesterday.

As in the previous build, three of the five app frames are daylight or lit
interiors, so they carry GRAD_DARK (f_bot 0.42) rather than app_slide's
default 0.68; BAND_MAX_LUMA is a mean and the default ramp leaves highlights
sitting right behind the grey paragraph dashes. The mean is also why slide 5
is bg-h32 and not bg-n05: n05 passes at a band mean of 37.5 while its lit
monitors sit at a 97th-percentile luma of 120, right under the first body
line. bg-h32 measures 24.3 and 58.

  01 hook       bg-h88  supercars-dusk  shelf zone luma 35.0, sd 6.5
  02 ARCO       bg-h31  lounge-night    band luma 19.7, darkest, seven lines
  03 ChatGPT    bg-h29  supercars-dusk  band luma 18.7
  04 Granola    bg-h22  lounge-day      band luma 53.5 -> 34.3 on GRAD_DARK
  05 CleanShot  bg-h32  window-silhou.  band luma 38.8 -> 24.3 on GRAD_DARK
  06 Zapier     bg-n01  villa-day       band luma 66.3 -> 42.5 on GRAD_DARK

Usage:
    python3 tools/gen-ten-x-4.py            # every slide
    python3 tools/gen-ten-x-4.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/arco-app'
TOPIC = 'ten-x-4'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ["how i 10x'd", 'my productivity']
PILLAR = 'tools'
# "10x" is a question about the day's setup, not about a study block, so ARCO
# answers on a planning angle.
THEME = 'planning'

TOOLS = ['ARCO', 'ChatGPT', 'Granola', 'CleanShot X', 'Zapier']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. Granola',
          '4. CleanShot X', '5. Zapier']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-chatgpt.png', 'icon-granola.png',
         'icon-cleanshot.png', 'icon-zapier.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h88.jpg',   # 01 hook       supercars-dusk  plain dark shelf zone
       'bg-h31.jpg',   # 02 ARCO       lounge-night    band luma 19.7
       'bg-h29.jpg',   # 03 ChatGPT    supercars-dusk  band luma 18.7
       'bg-h22.jpg',   # 04 Granola    lounge-day      band luma 34.3 dark
       'bg-h32.jpg',   # 05 CleanShot  window-silhouette  band luma 24.3 dark
       'bg-n01.jpg']   # 06 Zapier     villa-day       band luma 42.5 dark

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h31.jpg': GRAD, 'bg-h29.jpg': GRAD}

# Angle v15 from arco_angles.json, written out literally rather than drawn
# from next_arco_angle(THEME) at render time: the rotating call moves the
# pointer, so a rebuild would come back with different copy and `--only 02`
# could not redo the slide that shipped.
ARCO_BODY = [
    'Habits repeat into the day and take',
    'their own slot on the timeline.',
    '',
    'The plan is half built before I open',
    'it, and Focus mode guards each block.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'ChatGPT': [
    'A project keeps its own files and',
    'instructions, and every chat inside',
    'it starts with them loaded.',
    '',
    'You stop pasting the same context in',
    'at the top of every new chat.',
 ],
 'Granola': [
    'Ask one question across every call',
    'it has ever recorded.',
    '',
    'What someone promised three meetings',
    'ago comes back with the date on it.',
 ],
 'CleanShot X': [
    'Record a window and export it as a',
    'GIF that plays anywhere you paste it.',
    '',
    'The bug report shows the click that',
    'caused it instead of describing it.',
 ],
 'Zapier': [
    'Every zap can be given its own email',
    'address that starts it.',
    '',
    'Forwarding a message kicks off the',
    'work with nothing new to connect.',
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
