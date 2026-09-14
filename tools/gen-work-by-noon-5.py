#!/usr/bin/env python3
"""work-by-noon-5: the fifth outing of the "full day of work by noon" hook.

hook_rules.eligible(pillar='tools') returns five hooks; this is the second
least recently used (work-by-noon-4, ten posts back) and the least recent one
went to ten-x-5 in the same batch. It goes out verbatim. The build follows
gen-ten-x-4.py: icon shelf under the headline, ARCO leading the roster, one
teaching point per app, mechanism then consequence.

What is deliberately different from the four earlier work-by-noon posts:

  roster ARCO, ChatGPT, Vercel, Descript, Supabase. Exactly one LLM (ChatGPT,
         nine posts back on ten-x-4; Gemini carried work-by-noon-4, so the
         same hook gets a different model). Nothing tagged 'seller'.
  copy   every point is a capability no caption in tools/hooks.json has
         taught. ChatGPT has carried the Drive connector, Canvas, study mode,
         scheduled Tasks and Projects; memory that picks facts up on its own
         is new. Vercel's preview URLs went out on ship-with, so this slide
         teaches instant rollback. Descript's transcript editing went out on
         posting-daily and its filler-word pass on keep-five-3; the typed
         words spoken in your own trained voice are new. Supabase's instant
         APIs went out on app-in-a-weekend and its row security on
         weekend-not-month; Realtime is new.
  ARCO   work-by-noon and work-by-noon-3 both shipped "planned in 30 seconds"
         under this exact hook and work-by-noon-4 shipped the timeline angle
         (v11), so the remaining planning angles would be a third outing of
         the same mechanism. THEME is 'focus' instead: the way a day's work
         fits before noon is sessions nothing interrupts, which is f1's copy.
         next_arco_angle('focus') -> f1, drawn at compose time and frozen
         here so a rebuild cannot hand this post different copy.
  photos hook bg-h49 is unused as a hook and has the calmest shelf zone of
         the desk-city-day frames (73.6, sd 54.2); bg-n04 went to ten-x-5.
         App frames walked with the gen-daily-batch gates: no hook-only vibe
         past slide 1, every copy band under BAND_MAX_LUMA on the gradient it
         renders with, no adjacent vibe repeat, one person (bg-h32), and
         nothing that appeared in ten-x-5 (BG_COOLDOWN = 1).

  01 hook      bg-h49  desk-city-day      shelf zone luma 73.6, sd 54.2
  02 ARCO      bg-h88  supercars-dusk     band luma 28.2, p97 44
  03 ChatGPT   bg-h21  lounge-night       band luma 41.5 on GRAD_DARK
  04 Vercel    bg-h37  supercars-dusk     band luma 22.7
  05 Descript  bg-h22  lounge-day         band luma 34.3 on GRAD_DARK
  06 Supabase  bg-h32  window-silhouette  band luma 24.3 on GRAD_DARK, person

Usage:
    python3 tools/gen-work-by-noon-5.py            # every slide
    python3 tools/gen-work-by-noon-5.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'work-by-noon-5'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to do', 'a full day of work by noon']
PILLAR = 'tools'
# The planning angles are spent under this hook (30 seconds twice, the
# timeline on work-by-noon-4), so ARCO answers on focus: a day compresses
# into a morning when the sessions run uninterrupted.
THEME = 'focus'

TOOLS = ['ARCO', 'ChatGPT', 'Vercel', 'Descript', 'Supabase']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. Vercel',
          '4. Descript', '5. Supabase']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-chatgpt.png', 'icon-vercel.png',
         'icon-descript.png', 'icon-supabase.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h49.jpg',   # 01 hook      desk-city-day      calmest unused shelf
       'bg-h88.jpg',   # 02 ARCO      supercars-dusk     band luma 28.2
       'bg-h21.jpg',   # 03 ChatGPT   lounge-night       band luma 41.5 dark
       'bg-h37.jpg',   # 04 Vercel    supercars-dusk     band luma 22.7
       'bg-h22.jpg',   # 05 Descript  lounge-day         band luma 34.3 dark
       'bg-h32.jpg']   # 06 Supabase  window-silhouette  band luma 24.3 dark

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {'bg-h88.jpg': GRAD, 'bg-h37.jpg': GRAD}

# Angle f1 from arco_angles.json, drawn via next_arco_angle('focus') at
# compose time and written out literally: the rotating call moves the
# pointer, so a rebuild would come back with different copy and `--only 02`
# could not redo the slide that shipped.
ARCO_BODY = [
    'Focus mode blocks every app on my',
    'list for the whole session.',
    '',
    'The phone stops being a decision',
    'while the timer runs.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'ChatGPT': [
    'Memory picks up facts from your',
    'chats without being told to.',
    '',
    'Mention a deadline once and it',
    'plans around it weeks later.',
 ],
 'Vercel': [
    'Rollback puts an earlier deploy',
    'back live in one click.',
    '',
    'A broken ship costs a minute,',
    'not the rest of the morning.',
 ],
 'Descript': [
    'Train it on your voice once and',
    'typed words come out spoken.',
    '',
    'A flubbed line is fixed by typing',
    'it, not by re-recording the take.',
 ],
 'Supabase': [
    'Realtime pushes database changes',
    'to every open screen as they land.',
    '',
    'Two phones stay in sync with no',
    'refresh button and no sync code.',
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
