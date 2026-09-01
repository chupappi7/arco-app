#!/usr/bin/env python3
"""best-for-last: tools pillar. A replication of 4x-productivity-3, which the
sync marked performing -- the shape is kept (an approved two-line hook that
promises a productivity roster, five tools, ARCO leading), everything that
would read as the same post again is new.

What carries over is the hook's shape, not its words: "5 tools to stay
productive / i saved the best for last" is the same promise as "the tools i
used to / 4x my productivity" and is the only hook in the pool that has never
been out, while the source hook is blocked for four more posts anyway.

The roster is the one suggested for this build with one substitution. It was
Notion, ARCO, ClickUp, Raycast, Superwhisper, which carries no LLM and so
cannot pass assert_one_llm. Notion is the name that went, because it ran in
each of the last two posts and is the repeat risk in the set; ChatGPT takes
the slot, last out nine posts ago. ARCO moves to #1 and Superwhisper closes,
so the two Mac utilities nobody posts about land where the hook points.

None of the five teaching points appears in any caption in hooks.json:

  ARCO         Anytime holds the untimed tasks       (captions have the
               (angle v12)                            timeline, habits, the
                                                      30-second plan, Blocked
                                                      Hours, Insights)
  ChatGPT      connect Drive and it answers from     (captions have tasks,
               your own files                         custom instructions,
                                                      canvas, study mode,
                                                      cloud agent)
  ClickUp      one task in several lists, uncopied   (captions have custom
                                                      views and blocking
                                                      dependencies)
  Raycast      Search Menu Items finds any command   (captions have clipboard
               in the app you are in                  history, quicklinks,
                                                      snippets, floating
                                                      notes, extensions,
                                                      script commands)
  Superwhisper modes reformat what you dictate       (every previous outing
                                                      taught plain speech to
                                                      text and nothing else)

Backgrounds picked with the gen-daily-batch guards (hook-only vibes at index 0
only, copy band under BAND_MAX_LUMA, no adjacent vibe repeat, no person) and
frozen here so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'best-for-last'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['5 tools to stay productive', 'i saved the best for last']
PILLAR = 'tools'
TOOLS = ['ARCO', 'ChatGPT', 'ClickUp', 'Raycast', 'Superwhisper']

# 01 hook          bg-h78  desk-led-neon    first hook outing
# 02 ARCO          bg-h36  supercars-dusk   band luma 20.3
# 03 ChatGPT       bg-n06  desk-empty-day   band luma 53.6
# 04 ClickUp       bg-h31  lounge-night     band luma 19.7
# 05 Raycast       bg-n05  desk-empty-day   band luma 57.1
# 06 Superwhisper  bg-h22  lounge-day       band luma 53.5
# Set after reading the first render, which shot bg-h49 at 3 and bg-h35 at 6.
# Two things came back wrong. bg-h49 is the daylight office and put the copy
# across bright glass, which washed the leading dashes out -- the same failure
# the all-of-it-at-19 note records, so the whole desk-city-day family
# (h46/48/49/51/52) is out. And bg-h35 turned out to be the same villa and the
# same two cars as bg-h36: h35, h36, h38, h39 and h88 are one shoot, so the
# post takes exactly one of them. bg-h36 is that one, on the ARCO card,
# because it has the darkest band in the pool and the card is the longest body
# in the post at seven lines. bg-h31 is two posts old rather than three, which
# BG_COOLDOWN allows, and it is the only dark frame left outside the villa
# set. bg-n05 is the weakest frame here -- the copy crosses three lit monitors
# and the leading dashes go thin -- so it sits at 5, the slide carrying the
# least, and bg-h22 takes 6, where the hook has promised a payoff.
BGS = ['bg-h78.jpg', 'bg-h36.jpg', 'bg-n06.jpg',
       'bg-h31.jpg', 'bg-n05.jpg', 'bg-h22.jpg']

# The six frames 4x-productivity-3 shot, excluded from the walk.
SOURCE_BGS = ['bg-h56.jpg', 'bg-h20.jpg', 'bg-h21.jpg', 'bg-h29.jpg',
              'bg-h32.jpg', 'bg-h34.jpg']

# next_arco_angle('planning') has spent every planning angle, so it would
# reset the cycle and hand back v1 -- the most repeated three lines in the
# feed. v12 is written for this build instead and marked used in
# arco_angles.json: Anytime is a real part of the model (a task with no time
# yet) and no caption here has ever named it.
BODY = {
 'ARCO': [
    'Tasks without a time wait in Anytime',
    'until the day has room for them.',
    '',
    'Focus mode blocks the apps I chose',
    'for exactly that block.',
    '',
    'My holy grail.',
 ],
 'ChatGPT': [
    'Connect your Drive and it answers',
    'from your own files, not the web.',
    '',
    'You ask about last month’s notes',
    'instead of digging for the folder.',
 ],
 'ClickUp': [
    'One task can sit in several lists',
    'at once without being copied.',
    '',
    'You update it once and every board',
    'it lives on is already current.',
 ],
 'Raycast': [
    'Search Menu Items finds any command',
    'in the app you are in, by name.',
    '',
    'You stop hunting menus for the one',
    'you use twice a month.',
 ],
 'Superwhisper': [
    'Modes rewrite what you dictate: an',
    'email mode returns a written email.',
    '',
    'You ramble once and the text comes',
    'out already formatted.',
 ],
}

assert set(BGS).isdisjoint(SOURCE_BGS), 'a 4x-productivity-3 frame leaked back in'
preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)

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
