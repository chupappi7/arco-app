#!/usr/bin/env python3
"""wish-at-17: a tools post replicating the shape of what-actually-worked.

The source post is gone from this repo -- no draft folder, no hooks.json
entry, no generator, and post_stats has never seen it; the only trace is a
`{"seen": true}` in post_status.json. So what carries over is the shape every
post of that pillar shares, not its words: an approved hook, ARCO first, one
LLM, five tools, six slides.

Everything that would read as a repeat is new. The hook is the coldest
eligible one in the pool (16 posts since its last outing). The roster puts
ARCO at #1 and pairs it with four names none of the last six posts used.
Every teaching point was checked against the full hooks.json caption corpus
before it was written: ChatGPT has been taught through Tasks, custom
instructions and Canvas but never study mode; Canva through magic resize,
brand kits, whiteboards and doc-to-slides but never present-and-record;
Notion through automations, synced blocks, template buttons and AI but never
forms; CapCut only ever through text-to-speech captions.

Backgrounds follow the gen-daily-batch walk (hook-only vibes on slide 1 only,
copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most one person)
with one thing tightened: the walk excluded every background from the last
THREE posts rather than the one BG_COOLDOWN requires. launch-weekend was
being built in this repo at the same time, so a one-post window would have
been read off a history that was about to change under it. Stricter than the
guard, never looser. The hook background was claimed through pick_hook_bg
before the roster was written, for the same reason.

The ARCO card comes from next_arco_angle('planning'), which returned v5 on
the render that shipped; the angle is written out literally so a rebuild
cannot hand this post different copy than the caption describes.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'wish-at-17'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 apps i wish someone', 'showed me at 17']
TOOLS = ['ARCO', 'ChatGPT', 'Notion', 'Canva', 'CapCut']
BGS = ['bg-h67.jpg',   # 01 hook     desk-led-neon    first outing, hook-only vibe
       'bg-h20.jpg',   # 02 ARCO     lounge-day       band luma 67.0
       'bg-h34.jpg',   # 03 ChatGPT  desk-empty-day   band luma 62.4
       'bg-h36.jpg',   # 04 Notion   supercars-dusk   band luma 20.3
       'bg-h48.jpg',   # 05 Canva    desk-city-day    band luma 60.8
       'bg-n03.jpg']   # 06 CapCut   villa-day        band luma 63.6

BODY = {
 # next_arco_angle('planning') -> v5, frozen so a rebuild matches the caption.
 'ARCO': [
    'I keep every task in here and plan',
    'tomorrow in 30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away the moment it starts.',
    '',
    'The one I would not delete.',
 ],
 'ChatGPT': [
    'Study mode answers a question with',
    'questions, one step at a time.',
    '',
    'You come out of the homework able',
    'to redo it without the chat open.',
 ],
 'Notion': [
    'A database can be opened as a form,',
    'and every answer lands as a row.',
    '',
    'You collect signups or feedback',
    'without paying for a second tool.',
 ],
 'Canva': [
    'A presentation records your camera',
    'and the slides together, with your',
    'script scrolling over them.',
    '',
    'You send a narrated walkthrough',
    'without opening an editor.',
 ],
 'CapCut': [
    'Motion tracking pins text to an',
    'object while the shot moves.',
    '',
    'The label stays on the thing you',
    'are pointing at, with no keyframes.',
 ],
}

preflight(TOPIC, TOOLS, BGS, pillar='tools', hook=HOOK)

# pick_hook_bg already claimed bg-h67 while the roster was being written, so
# it is logged; re-claim only if this is being rebuilt on a reset log.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    c.pick_hook_bg(prefer=BGS[0])

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    app_slide(bg, icons[tool], f'{n}. {tool}', BODY[tool], f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
