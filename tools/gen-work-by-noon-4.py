#!/usr/bin/env python3
"""work-by-noon-4: the noon hook, new roster, icon-shelf opening.

The hook is the least recently used eligible tools hook in hook_pool.json --
hook_rules.eligible(pillar='tools') returns it first, its last outing was
work-by-noon-3 well past HOOK_COOLDOWN -- and it goes out verbatim. The build
follows gen-ten-x-4.py: the shelf of five icons under the headline so the
viewer sees the roster before reading a word, ARCO leading, one teaching
point per app, mechanism then consequence.

What is different from the two earlier work-by-noon posts, which shared one
set of words and differed only in photography:

  roster ARCO, Gemini, Superwhisper, Make, Linear. Exactly one LLM (Gemini,
         the least recently used of them: ChatGPT, Claude, Perplexity and
         Codex have carried the last four posts). Nothing tagged 'seller',
         and none of the five is a repeat of the previous post's set.
  copy   every point is a capability no caption in tools/hooks.json has
         taught. That ruled out most of the obvious ones: Gemini's Deep
         Research went out on pay-double, its Gems on selling-online, whole
         file uploads on showed-me-at-17 and the Live screen share on
         ten-x-3; Superwhisper's dictate-anywhere hotkey has carried six
         captions and its rewrite Modes went out on best-for-last; Linear's
         branch-name automation went out on month-in-a-weekend and Cycles on
         ship-with; Make's scenario inspector went out on saved-hours, and
         "an automation can run on a schedule" is Zapier's point from
         twelve-apps. So this post teaches the Workspace connection, the
         local model, the error handler and Triage.
  ARCO   the hook asks what gets a day's work done before noon, so THEME is
         'planning'. next_arco_angle('planning') would hand back v2, which
         opens on "the day gets planned in 30 seconds" -- the same line
         work-by-noon and work-by-noon-3 both already shipped under this
         exact hook, so a third outing teaches a returning viewer nothing.
         v11 is used instead: tasks taking a time on the timeline is the
         mechanism that answers "by noon", and it has not shipped.
  photos six frames, none of them in ten-x-4, walked with the
         gen-daily-batch guards: hook unused as a hook, app frames free of
         hook-only vibes, every copy band under BAND_MAX_LUMA, no adjacent
         vibe repeat, one person at most.

The hook frame is picked for the shelf, not just for the hook text. The icons
land at y1105-1447, so the lower half of slide 1 has to be plain and dark or
they stop reading as a set. Measured over the shelf box on the real render,
bg-h39 is the emptiest lower half left in the pool: luma 15.7 at sd 8.5, a
dark forecourt with nothing in it. Every other unused hook frame fails that
test -- the six desk-city-day frames put lit monitors behind the icons
(72-86 luma, sd 49-58), the villa-day frames put a lit house and a pool
there (59-103), bg-h44 is a bright window (84.1) and bg-h34/n05/n06 are desks
whose edges cut through the shelf. bg-h35 averages 36.3 but at sd 40.5: the
mean is low only because half the frame is black while a headlight sits
directly under the second icon row.

As in gen-ten-x-4.py, the daylight and lit-interior frames carry GRAD_DARK
(f_bot 0.42) rather than app_slide's default 0.68; BAND_MAX_LUMA is a mean
and the default ramp leaves highlights sitting right behind the grey
paragraph dashes.

  01 hook          bg-h39  supercars-dusk     shelf zone luma 15.7, sd 8.5
  02 ARCO          bg-h24  lounge-night       band luma 31.8
  03 Gemini        bg-h37  supercars-dusk     band luma 14.8
  04 Superwhisper  bg-h34  desk-empty-day     band luma 62.4 -> 43.5 dark
  05 Make          bg-h45  window-silhouette  band luma 45.6, the one person
  06 Linear        bg-n04  villa-day          band luma 57.8 -> 38.7 dark

Usage:
    python3 tools/gen-work-by-noon-4.py            # every slide
    python3 tools/gen-work-by-noon-4.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/arco-app'
TOPIC = 'work-by-noon-4'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to do', 'a full day of work by noon']
PILLAR = 'tools'
# "a full day of work by noon" is a question about how the day is set up, so
# ARCO answers on a planning angle rather than a focus or study one.
THEME = 'planning'

TOOLS = ['ARCO', 'Gemini', 'Superwhisper', 'Make', 'Linear']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Gemini', '3. Superwhisper',
          '4. Make', '5. Linear']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-gemini.png', 'icon-superwhisper.jpg',
         'icon-make.png', 'icon-linear.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h39.jpg',   # 01 hook          supercars-dusk     plain dark shelf
       'bg-h24.jpg',   # 02 ARCO          lounge-night       band luma 31.8
       'bg-h37.jpg',   # 03 Gemini        supercars-dusk     band luma 14.8
       'bg-h34.jpg',   # 04 Superwhisper  desk-empty-day     band luma 43.5
       'bg-h45.jpg',   # 05 Make          window-silhouette  band luma 45.6
       'bg-n04.jpg']   # 06 Linear        villa-day          band luma 38.7

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h24.jpg': GRAD, 'bg-h37.jpg': GRAD}

# Angle v11 from arco_angles.json, written out literally rather than drawn
# from next_arco_angle(THEME) at render time: the rotating call moves the
# pointer, so a rebuild would come back with different copy and `--only 02`
# could not redo the slide that shipped.
ARCO_BODY = [
    'Every task I have gets a time on',
    "the day's timeline, not a list.",
    '',
    'Blocked Hours shuts the feeds for',
    'those windows without me asking.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Gemini': [
    'Connect Gmail and Drive and it',
    'answers from your own mail and files.',
    '',
    'The invoice or the thread comes',
    'back without you opening the inbox.',
 ],
 'Superwhisper': [
    'The model runs on the machine, so',
    'dictation works with no connection.',
    '',
    'You talk a draft out on a plane and',
    'the audio never leaves the laptop.',
 ],
 'Make': [
    'An error handler retries the step',
    'that failed and carries on.',
    '',
    'The overnight batch is finished by',
    'morning, not stopped at item nine.',
 ],
 'Linear': [
    'Every bug and request lands in',
    'Triage, not straight in the backlog.',
    '',
    'You sort it once and the list you',
    'work from stays the real one.',
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
