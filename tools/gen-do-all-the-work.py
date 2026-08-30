#!/usr/bin/env python3
"""do-all-the-work: tools pillar. A reword of type-less.

Same concept (a stack that writes and captures for you), same roster and the
same five teaching points; new hook from the pool and new copy so it does not
read as the same post. Superwhisper and Granola came back into tool_pool.json
for this one, since the roster is what the reword keeps.

Backgrounds picked with the gen-daily-batch algorithm (hook-only vibes skipped
on app slides, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most
one person) and frozen so the post rebuilds identically. Three of the picker's
choices were replaced after reading the render, which is the check the numbers
cannot do: bg-h46 is one of the two frames that measure fine and still read
badly, bg-h35 put the body copy across a white supercar, and bg-h49 ran it over
monitor bezels until the leading dashes disappeared. bg-h88 and bg-n04 are the
calmest frames in the band (std dev 9 and 38 against bg-h49's 41).
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs)

TOPIC = 'do-all-the-work'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
THEME = 'planning'
TOOLS = ['ARCO', 'Superwhisper', 'Granola', 'Claude', 'CleanShot X']
BGS = ['bg-h31.jpg', 'bg-h22.jpg', 'bg-h24.jpg', 'bg-h88.jpg',
       'bg-h45.jpg', 'bg-n04.jpg']

BODY = {
 'Superwhisper': [
    'One shortcut turns speech into',
    'clean text inside any app.',
    '',
    'A message you would type for two',
    'minutes takes fifteen seconds.',
 ],
 'Granola': [
    'It records the call and rewrites',
    'your rough notes from the audio.',
    '',
    'Two words typed in the meeting',
    'come back as a written summary.',
 ],
 'Claude': [
    'Dictate the messy version and ask',
    'for the clean draft back.',
    '',
    'You edit something that exists',
    'instead of facing a blank page.',
 ],
 'CleanShot X': [
    'It reads the text inside a',
    'screenshot and copies it out.',
    '',
    'An error on a photo of a screen',
    'becomes something you can paste.',
 ],
}

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
    app_slide(bg, icons[tool], f'{n}. {tool}', body, f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
