#!/usr/bin/env python3
"""keep-five-3: the "5 apps i would keep" hook, icon-shelf opening.

hook_rules.eligible(pillar='tools') returns three hooks and this is the least
recently used of them: "the 5 apps i would keep / if i deleted everything
else" last went out on delete-the-rest, eleven posts back, against five for
wish-i-knew-at-17 and nine for 4x-productivity. It ships verbatim. The build
follows gen-best-for-last-2.py: a shelf of the five roster icons under the
headline so the viewer sees the post before reading a word, ARCO leading, one
teaching point per app, mechanism then consequence.

Nothing carries over from the three earlier posts on this hook except the
hook itself:

  roster ARCO, Cursor, Figma, Descript, Buffer. Exactly one LLM, and Cursor
         is the longest unused of them: thirty-five posts back on
         four-x-tools, while Manus, Gemini, ChatGPT, Claude, Perplexity and
         Codex have carried the last six. Nothing tagged 'seller'. No overlap
         with the previous post's set, and none of the five appeared in
         keep-five, keep-five-2 or delete-the-rest.
         The five answer the hook as a cull rather than a category sweep: the
         day, the code, the design, the video, the posting. One app per job
         and nothing left over, which is the shape "if i deleted everything
         else" asks for.
  copy   every point is a capability no caption in tools/hooks.json has
         taught, and each one is the reason that app survives the cull rather
         than a description of what it is. That ruled out the obvious ones:
         Cursor has already taught Tab predicting the next edit and rules
         files; Figma has had components, auto layout, variables and dev
         mode; Descript's edit-the-transcript-to-cut-the-footage went out on
         posting-daily. So this post teaches indexed docs by URL, a shared
         prototype link, filler-word and gap removal, and one composer that
         rewrites per channel.
         Obsidian was the first pick for slide 5 and was dropped: fourteen
         captions have mined it down to block ids and unlinked mentions, and
         nothing real was left to teach.
  ARCO   "the 5 apps i would keep" asks what runs the day once the phone is
         stripped, so THEME is 'planning'. next_arco_angle('planning') would
         hand back v2, which is v1 with two words moved. v5 is used instead:
         it has never shipped, and its closer "The one I would not delete."
         is the hook's own sentence answered, which no other angle does.
  photos six frames, none of them in the last three posts, walked with the
         gen-daily-batch guards: hook plain and dark where the shelf lands,
         app frames free of hook-only vibes, every copy band under
         BAND_MAX_LUMA, no adjacent vibe repeat, no person at all.
         bg-h46 was rendered for slide 3 first and replaced: it passes the
         luma gate at 43.7 as a mean, but the mean hides three lit monitors
         sitting directly behind the second paragraph, and it put a second
         desk-city-day frame in a six-slide post. bg-h31 is 12.8 and clean.

The hook frame is picked for the shelf before it is picked for the text. The
icons land at y1105-1447, so the lower half of slide 1 has to be plain and
dark or they stop reading as a set. Measured over the shelf box on the real
render, bg-h68 is the plainest lower half in the entire pool: 5.4 luma at sd
8.5, an unlit floor behind a dark chair. The three frames never yet shipped
as a hook all fail it and were rendered to check: bg-h41 puts the icons on a
man's suited back so his shoulders cut through the second row, bg-h57 puts
them on lit monitors, bg-h16 on a person. bg-h68 last carried a hook twenty
posts ago on month-in-a-weekend, under the old flat-text style with no shelf.

As in gen-best-for-last-2.py the brighter frames carry GRAD_DARK (f_bot 0.42)
rather than app_slide's default 0.68; BAND_MAX_LUMA is a mean and the default
ramp leaves highlights sitting behind the grey paragraph dashes.

  01 hook      bg-h68  desk-led-neon      shelf zone luma 5.4, sd 8.5
  02 ARCO      bg-h35  supercars-dusk     band luma 24.0
  03 Cursor    bg-h31  lounge-night       band luma 12.8
  04 Figma     bg-h05  lounge-day         band luma 52.0
  05 Descript  bg-n02  villa-day          band luma 56.3
  06 Buffer    bg-h48  desk-city-day      band luma 50.4

Usage:
    python3 tools/gen-keep-five-3.py            # every slide
    python3 tools/gen-keep-five-3.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/arco-app'
TOPIC = 'keep-five-3'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'
# What survives a cull is a question about how the day is run, not about
# screen time or a study session, so ARCO answers on a planning angle.
THEME = 'planning'

TOOLS = ['ARCO', 'Cursor', 'Figma', 'Descript', 'Buffer']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Cursor', '3. Figma',
          '4. Descript', '5. Buffer']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-cursor.png', 'icon-figma.png',
         'icon-descript.png', 'icon-buffer.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h68.jpg',   # 01 hook      desk-led-neon   plain dark shelf zone
       'bg-h35.jpg',   # 02 ARCO      supercars-dusk  band luma 24.0
       'bg-h31.jpg',   # 03 Cursor    lounge-night    band luma 12.8
       'bg-h05.jpg',   # 04 Figma     lounge-day      band luma 52.0
       'bg-n02.jpg',   # 05 Descript  villa-day       band luma 56.3
       'bg-h48.jpg']   # 06 Buffer    desk-city-day   band luma 50.4

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h35.jpg': GRAD}

# Angle v5 from arco_angles.json, written out literally rather than drawn from
# next_arco_angle(THEME) at render time: the rotating call moves the pointer,
# so a rebuild would come back with different copy and `--only 02` could not
# redo the slide that shipped.
ARCO_BODY = [
    'I keep every task in here and plan',
    'tomorrow in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away the moment it starts.',
    '',
    'The one I would not delete.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Cursor': [
    'Give it a docs URL and it indexes',
    'that whole site for you.',
    '',
    'You @ the docs in a prompt and the',
    'code comes back on the current',
    'version, not a two year old one.',
 ],
 'Figma': [
    'Wire the frames to each other and',
    'share the prototype as a link.',
    '',
    'The flow gets tapped through on a',
    'phone before any of it is built.',
 ],
 'Descript': [
    'One pass strips every um and pulls',
    'the pauses between words shorter.',
    '',
    'A rambling first take comes back',
    'tight before you open the timeline.',
 ],
 'Buffer': [
    'One box writes the post, then each',
    'channel keeps its own edit of it.',
    '',
    'The same idea goes out short here',
    'and long there without retyping.',
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
