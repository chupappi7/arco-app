#!/usr/bin/env python3
"""keep-five-7: re-shoot of keep-five. Same words, new photos.

Copied from gen-keep-five-2.py (itself the frozen-copy form of gen-keep-five);
only TOPIC and BGS differ.

Every hook line, title, body line, roster entry and caption is frozen from
the source post; only the backgrounds and the topic slug change. gen-keep-five
draws its ARCO slide from next_arco_angle, and that angle rotates, so the
lines are written out here instead -- read back off drafts/keep-five/03.jpg,
which is angle "v1" in arco_angles.json. Rotating again would put different
words on the slide, and a re-shoot changes photos, not copy.

Backgrounds picked with the gen-daily-batch walk on 2026-09-21 (hook-only
vibes skipped on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe
repeat, at most one person, nothing assert_bg_fresh rejects) and frozen so
the post rebuilds identically. The six photographs keep-five was shot on are
excluded from the walk, because a re-shoot that reuses the source's own
photos is not a re-shoot; they are listed in SOURCE_BGS.

The hook background is the first hook-only frame without a person that the
hook log has not used and that sits outside the cooldown: bg-h69. pick_hook_bg
is not called because it would return bg-h14, a desk-person-night frame, and
spend the one-person budget on the hook.

  01 hook    bg-h69  desk-led-neon
  02 Claude  bg-h20  lounge-day         copy_band_luma 67.0
  03 ARCO    bg-h24  lounge-night       copy_band_luma 49.8
  04 Notion  bg-h32  window-silhouette  copy_band_luma 38.8, the one person
  05 GitHub  bg-h34  desk-empty-day     copy_band_luma 62.4
  06 CapCut  bg-h35  supercars-dusk     copy_band_luma 37.2

Both hook guards run: the hook is in hook_pool.json and hook_rules.status
says it is past its cooldown (keep-five-6, seven posts back). mark_hook_used
records the seventh outing so the cooldown counts it from here.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, record_post_tools,
                     record_post_bgs, assert_audience, assert_varied,
                     assert_bg_fresh, assert_hook_pillar, assert_one_llm,
                     assert_fresh_tools)

TOPIC = 'keep-five-7'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
TOOLS = ['Claude', 'ARCO', 'Notion', 'GitHub', 'CapCut']
TITLES = ['1. Claude', '2. ARCO', '3. Notion', '4. GitHub', '5. CapCut']
ICONS = ['icon-claude.jpg', 'icon-arco.png', 'icon-notion.jpg',
         'icon-github.jpg', 'icon-capcut.png']

BGS = ['bg-h69.jpg',   # 01 hook    desk-led-neon
       'bg-h20.jpg',   # 02 claude  lounge-day         band luma 67.0
       'bg-h24.jpg',   # 03 arco    lounge-night       band luma 49.8
       'bg-h32.jpg',   # 04 notion  window-silhouette  band luma 38.8, person
       'bg-h34.jpg',   # 05 github  desk-empty-day     band luma 62.4
       'bg-h35.jpg']   # 06 capcut  supercars-dusk     band luma 37.2

# The six photographs the source post was shot on. Excluded from the walk.
SOURCE_BGS = ['bg-h01.jpg', 'bg-h59.jpg', 'bg-h53.jpg',
              'bg-h44.jpg', 'bg-h29.jpg', 'bg-h21.jpg']

BODY = [
 [
    'You can define your own agents and',
    'run them at the same time.',
    '',
    'One builds, one reviews, each with',
    'its own clean context window.',
 ],
 [
    'I manage all my tasks here and plan',
    'the day in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'My holy grail.',
 ],
 [
    'A database automation fires when a',
    'property changes, not on a timer.',
    '',
    'Flip status to done and it stamps',
    'the date and files the page itself.',
 ],
 [
    'Actions can run on a schedule, not',
    'only when you push.',
    '',
    'A nightly scraper or weekly report',
    'runs on their machines, not yours.',
 ],
 [
    'Auto captions can be read out loud',
    'with text to speech in one tap.',
    '',
    'A faceless video gets a voiceover',
    'without recording anything.',
 ],
]

assert_one_llm(TOOLS)
assert_fresh_tools(TOOLS)
assert_audience(TOOLS)
assert_varied(BGS)
assert_bg_fresh(BGS, TOPIC)
assert_hook_pillar(HOOK, 'tools')
assert not set(BGS) & set(SOURCE_BGS), 'a re-shoot must not reuse the source photos'
for bg in BGS[1:]:
    luma = c.copy_band_luma(bg)
    if luma > c.BAND_MAX_LUMA:
        raise SystemExit(f'{bg} copy band is {luma:.1f}, over {c.BAND_MAX_LUMA}')

# Record the hook background by hand rather than through pick_hook_bg: that
# function narrows its candidates to night-desk vibes whenever any are unused,
# so `prefer` is silently ignored and it can log a background this post never
# rendered.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'), indent=1)

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

for i in range(len(TOOLS)):
    n = i + 1
    app_slide(BGS[n], ICONS[i], TITLES[i], BODY[i], f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
