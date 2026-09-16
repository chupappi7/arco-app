#!/usr/bin/env python3
"""keep-five-4: fourth outing of the "5 apps i would keep" hook, icon shelf.

"the 5 apps i would keep / if i deleted everything else" (tools pillar). Of
the four hooks hook_rules.eligible(pillar='tools') returned it was the least
recently used: five-that-stay, seven posts back.

  roster    ARCO, ChatGPT, Notion, Canva, Captions. ChatGPT is the LLM: with
            Cursor and Claude it is one of the three least recently used
            models (work-by-noon-5, eight posts back) and this hook has only
            carried it once, on keep-if-deleted. Captions is the niche pick;
            it has never been on a slide. Five jobs, one app each: the day,
            the thinking, the site, the design, the video.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: ChatGPT tasks, canvas, drive connector,
            custom instructions, study mode, projects, memory; Notion
            automations, rollups, synced blocks, templates, clipper,
            calendar, forms, charts, AI Q&A; Canva resize, brand kit, bulk
            create, doc to slides, whiteboard, presentation recording.
            Fresh here: ChatGPT record mode, Notion Sites, Canva Mockups,
            Captions eye contact.
  ARCO      the cull asks what runs the day, so THEME is 'planning'.
  photos    hook from the four frames never yet used on a hook (bg-n01,
            villa-day; the pool over the shelf zone is the plainest of
            them). Hook gradient floor lowered to 0.40 so the icons sit on a
            dark plate instead of daylight. App slides from non-hook-only
            vibes under BAND_MAX_LUMA, no adjacent vibe repeat, no person,
            nothing from the previous post (five-of-twelve). bg-n05 was
            rendered for the Notion slide first and replaced: it clears the
            luma gate at 57 but the mean hides three lit monitors sitting
            behind the first paragraph. bg-h20 is a window and a sofa.

Usage:
    python3 tools/gen-keep-five-4.py            # every slide
    python3 tools/gen-keep-five-4.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'keep-five-4'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'ChatGPT', 'Notion', 'Canva', 'Captions']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. Notion',
          '4. Canva', '5. Captions']

# Daylight frame: the default floor of 0.72 leaves the shelf on bright
# floor and chair. 0.40 measured the shelf zone at luma 48, sd 24.
HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-n01.jpg',   # 01 hook      villa-day
       'bg-h31.jpg',   # 02 ARCO      lounge-night      band luma 19.7
       'bg-h29.jpg',   # 03 ChatGPT   supercars-dusk    band luma 18.7
       'bg-h20.jpg',   # 04 Notion    lounge-day        band luma 67.0
       'bg-h35.jpg',   # 05 Canva     supercars-dusk    band luma 37.2
       'bg-h22.jpg']   # 06 Captions  lounge-day        band luma 53.5

BODY = {
 'ChatGPT': [
    'Record mode in the desktop app',
    'listens to a meeting as it runs.',
    '',
    'The notes and the action items',
    'are written when the call ends.',
 ],
 'Notion': [
    'Any page publishes as a live site',
    'on your own domain.',
    '',
    'The landing page is a doc you',
    'wrote, with nothing built in code.',
 ],
 'Canva': [
    'Mockups wraps a design onto a',
    'phone, a mug or a t-shirt.',
    '',
    'The product shot exists before',
    'the product does.',
 ],
 'Captions': [
    'Eye contact moves your gaze to',
    'the lens while you read a script.',
    '',
    'A take read off the screen looks',
    'like it was said from memory.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            c.pick_hook_bg(prefer=BGS[0])
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', grad=HOOK_GRAD, icons=shelf)
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):16s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

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
