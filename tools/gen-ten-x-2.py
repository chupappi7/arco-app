#!/usr/bin/env python3
"""ten-x-2: tools pillar. A reword of do-all-the-work.

Same concept (a stack that writes and captures for you), the same roster and
the same five teaching points; new hook and new copy so it does not read as
the same post.

The source's own hook ("i pay for 12 apps / these 5 do all the work") was one
post old when this was built, and hook_rules keys the cooldown on the parent
hook, so a rewording of it was blocked too. "how i 10x'd my productivity" is the
eligible tools hook that asks the same question: a small stack that multiplies
what one person gets done. Every slide answers it with a mechanism, not a claim.

It also renders properly. The stacked hook style wants a two or three word first
line; a six word one shrinks to less than half the ceiling, which is how the
weakest hook slides in this feed happened.

Backgrounds are frozen so the post rebuilds identically. The hook takes a fresh
night-desk frame (hook-only vibe, the strongest images in the pool); the app
slides alternate supercars-dusk with two night interiors and one silhouette so
no two adjacent cards share a scene.

The first pass shot slides 3, 5 and 6 on the daylight desks and the pool villa.
All three passed the luma gate and all three failed the read: the copy crossed a
monitor bezel, a glass mullion and a white villa wall. The frames here were each
rendered with this post's own copy and read back before being frozen. grad_for
still pushes the gradient down on the brighter ones before adaptive_scrim runs.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'ten-x-2'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ["how i 10x'd", 'my productivity']
THEME = 'planning'
TOOLS = ['ARCO', 'Superwhisper', 'Granola', 'Claude', 'CleanShot X']
BGS = ['bg-h60.jpg', 'bg-h36.jpg', 'bg-h31.jpg', 'bg-h38.jpg',
       'bg-h22.jpg', 'bg-h45.jpg']

BODY = {
 'Superwhisper': [
    'Hold one key and talk. Clean text',
    'lands in whatever app is open.',
    '',
    'A two minute reply is done in',
    'fifteen seconds of talking.',
 ],
 'Granola': [
    'It listens to the call and turns',
    'the three words you typed into',
    'full notes.',
    '',
    'Nobody writes up the meeting',
    'afterwards. It is already written.',
 ],
 'Claude': [
    'Talk through the messy version and',
    'ask for the clean draft back.',
    '',
    'You spend the morning editing',
    'something instead of staring at',
    'an empty page.',
 ],
 'CleanShot X': [
    'It reads the words inside an image',
    'and copies them to the clipboard.',
    '',
    'Text you could only look at is',
    'now text you can paste and search.',
 ],
}


def grad_for(bg):
    """Gradient for an app slide, chosen from how bright its copy band is.

    adaptive_scrim aims for a band luma of 96 and caps its own strength, so on
    a daylight frame it runs out of room and the copy ends up on a lit window.
    Pushing the gradient first gives it something to work with.
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
