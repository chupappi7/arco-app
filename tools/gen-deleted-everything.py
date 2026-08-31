#!/usr/bin/env python3
"""deleted-everything: tools pillar. A reword of do-all-the-work.

Same concept (a stack that writes and captures for you), the same roster and
the same five teaching points; a different hook and all new copy so it does not
read as the same post.

Hook. do-all-the-work's own hook ("i pay for 12 apps / these 5 do all the work")
is off cooldown again, and hook_rules.parent would accept a light rewording of
it -- but assert_hook_approved matches the pool exactly, on purpose, so a
reworded line cannot render without weakening the one guard that keeps hooks in
the user's voice. "the 5 apps i would keep / if i deleted everything else" is
the eligible tools hook that asks the same question the source asked: you pay
for a pile of apps, these are the ones carrying it. The 4x and 10x hooks were
the other same-idea candidates and both were skipped -- ten-x-2 already shot
this exact roster on the productivity-multiplier framing, so a third one would
read as the same post twice.

Copy. Every teaching point is the third phrasing of itself (do-all-the-work,
then ten-x-2, now this), so the mechanism is identical and no sentence is.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person, nothing assert_bg_fresh rejects) and frozen so the post rebuilds
identically. The walk was steered on three points the numbers do not see. The
daylight desk-city frames and the villa walls are excluded outright -- ten-x-2
measured them fine and read badly, the copy landing on a monitor bezel or a
white wall. bg-n06 was the picker's slide 6 at a passing luma of 54 and was cut
after reading the render for the same reason: a bright glass office, and the
card came back washed out beside the other five. And the vibe tags are coarser
than the eye -- bg-h36 and bg-h37 are the same house and the same two cars from
two metres apart, so a post carrying both reads as one photo used twice even
with a slide between them. bg-h29 is the supercars frame that is actually a
different picture. grad_for pushes the gradient down on the brighter frames
before adaptive_scrim runs, which is what keeps the leading dashes on bg-h21.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'deleted-everything'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
THEME = 'planning'
TOOLS = ['ARCO', 'Superwhisper', 'Granola', 'Claude', 'CleanShot X']
BGS = ['bg-h66.jpg', 'bg-h37.jpg', 'bg-h21.jpg', 'bg-h29.jpg',
       'bg-h32.jpg', 'bg-h31.jpg']

BODY = {
 'Superwhisper': [
    'A hotkey anywhere on the machine',
    'turns what you say into typed text.',
    '',
    'The long email you kept putting off',
    'gets said out loud once and sent.',
 ],
 'Granola': [
    'It sits on the call and fills in the',
    'notes you half typed, from the audio.',
    '',
    'The write up you would do at 6pm',
    'is already there when you hang up.',
 ],
 'Claude': [
    'Paste the rambling version and ask',
    'for the tight one back.',
    '',
    'Every piece of writing starts at the',
    'second draft instead of the first.',
 ],
 'CleanShot X': [
    'Screenshot anything and it lifts the',
    'text straight out of the picture.',
    '',
    'An error code in a video or a photo',
    'goes into search without retyping.',
 ],
}


def grad_for(bg):
    """Gradient for an app slide, chosen from how bright its copy band is.

    adaptive_scrim aims for a band luma of 96 and caps its own strength, so on
    a brighter frame it runs out of room and the copy ends up sitting on the
    photo. Pushing the gradient first gives it something to work with.
    """
    luma = c.copy_band_luma(bg)
    if luma >= 55:
        return (0.58, 0.40, 300, 1250)
    if luma >= 35:
        return (0.72, 0.55, 300, 1250)
    return (0.85, 0.68, 300, 1250)


preflight(TOPIC, TOOLS, BGS, 'tools', hook=HOOK)

# Record the hook background by hand rather than through pick_hook_bg: that
# function narrows its candidates to night-desk vibes whenever any are unused,
# so `prefer` is silently ignored for anything else and it logs a background
# this post never rendered.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'), indent=1)

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
    app_slide(bg, icons[tool], f'{n}. {tool}', body, f'{OUT}/{n+1:02d}.jpg',
              grad=grad_for(bg))

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
