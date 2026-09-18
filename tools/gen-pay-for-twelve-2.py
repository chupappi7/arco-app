#!/usr/bin/env python3
"""pay-for-twelve-2: second outing of the 12-apps hook, icon shelf, fresh roster.

"i pay for 12 apps / these 5 do all the work" (tools pillar). Second least
recently used of the three hooks hook_rules.eligible(pillar='tools')
returned on 2026-09-18: pay-for-twelve, seven posts back.

  roster    ARCO, Cursor, Notion, Firebase, Runway. Cursor is the LLM:
            second least recently used model (work-by-noon-6, nine posts
            back) and this hook last carried Codex. Each slide is a job
            the app takes over: the review, the reschedule, the send, the
            animation.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Cursor rules, tab, docs indexing, slack
            cloud agent; Notion button block, property automation, forms,
            charts, repeating templates, rollups, synced blocks, publish
            to web, AI Q&A, calendar, web clipper, database views;
            Firebase remote config (twice); Runway Aleph. Fresh here:
            Cursor BugBot, Notion timeline dependencies shifting dates,
            Firebase scheduled push campaigns, Runway Act-Two.
  ARCO      five apps that carry the day is a question about the plan,
            THEME 'planning'.
  photos    hook bg-h61 (desk-led-neon), next hook-only frame without a
            person the hook log has not used after h55 went to
            work-by-noon-7. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, no person, nothing
            from the previous post (work-by-noon-7) and disjoint from
            best-for-last-5 built in the same batch. desk-city-day frames
            were previewed and dropped: every one puts the monitors behind
            the copy.

Usage:
    python3 tools/gen-pay-for-twelve-2.py            # every slide
    python3 tools/gen-pay-for-twelve-2.py --only 03  # one slide, for redos
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
TOPIC = 'pay-for-twelve-2'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Cursor', 'Notion', 'Firebase', 'Runway']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Cursor', '3. Notion',
          '4. Firebase', '5. Runway']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h61.jpg',   # 01 hook      desk-led-neon
       'bg-h36.jpg',   # 02 ARCO      supercars-dusk    band luma 20.3
       'bg-h31.jpg',   # 03 Cursor    lounge-night      band luma 19.7
       'bg-n04.jpg',   # 04 Notion    villa-day         band luma 57.8
       'bg-h29.jpg',   # 05 Firebase  supercars-dusk    band luma 18.7
       'bg-h22.jpg']   # 06 Runway    lounge-day        band luma 53.5

BODY = {
 'Cursor': [
    'BugBot reads every pull request',
    'and comments where the bug is.',
    '',
    'The review is done before you',
    'have asked anyone to look.',
 ],
 'Notion': [
    'Mark one task as blocked by',
    'another on the timeline view.',
    '',
    'Push the first date back and',
    'every task after it shifts too.',
 ],
 'Firebase': [
    'Schedule a push notification in',
    'the console for a day and hour.',
    '',
    'The launch message goes out at',
    '9am tuesday with you offline.',
 ],
 'Runway': [
    'Act-Two maps a phone video of you',
    'onto any character you generate.',
    '',
    'The character acts the scene',
    'and nobody animated a frame.',
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
        if tool == 'ARCO':
            print('  ARCO angle:', ' / '.join(l for l in body if l))
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
