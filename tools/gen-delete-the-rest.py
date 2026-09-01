#!/usr/bin/env python3
"""delete-the-rest: tools pillar. A replication of twelve-apps -- its shape is
kept (an approved two-line hook that reduces a big number down to five, five
tools one per slide, ARCO leading), everything that would read as the same
post again is new.

What carries over is the hook's SHAPE, not its words. "the 5 apps i would keep
/ if i deleted everything else" makes the same move as "i pay for 12 apps /
these 5 do all the work": everything you own, cut to five. The source's own
hook is eligible again but reusing it would be the repeat this build exists to
avoid; the keep hook last went out five posts ago (keep-five-2), one clear of
HOOK_COOLDOWN.

The roster is the one suggested for this build, reordered so ARCO leads:
CapCut, ARCO, Claude, GitHub, Framer -> ARCO, CapCut, Claude, GitHub, Framer.
The suggestion put ARCO second, which is the old examples.md ordering; the
rule the last three posts actually shipped on, and the one content.md carries,
is that the app leads at #1. Claude is the single LLM.

None of the five teaching points appears in any caption in hooks.json:

  ARCO     the running block on the Lock     (captions have Blocked Hours in
           Screen (angle v13, written for     ten posts, the timeline, habits,
           this build)                        Anytime, Insights, the 30-second
                                              plan -- never a widget or a Live
                                              Activity)
  CapCut   auto captions translated in place (captions have text to speech,
                                              motion tracking, auto reframe,
                                              apply-style-to-all)
  Claude   a custom Style learned from one   (captions have Claude Code,
           writing sample                     skills, agents, MCP, projects,
                                              quizzes, dictation to draft)
  GitHub   Codespaces runs the project in    (captions have Actions on push,
           the browser                        Actions on a schedule, branch
                                              protection, Pages)
  Framer   native A/B tests off a right      (captions have publish-from-
           click                              canvas, CMS collections,
                                              built-in analytics)

Verified before writing: Framer ships A/B testing natively (right-click a page
-> New A/B Test, traffic split, winner flagged at >90% probability); CapCut
translates generated captions into a target language in the same project;
Claude custom Styles are built from a pasted writing sample; the ARCO claim is
the Live Activity in SIXSIXWidget/FocusLiveActivity.swift, which draws
Text(timerInterval:) counting down on the Lock Screen.

Backgrounds picked with the usual guards (hook-only vibes at index 0 only,
copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most one person)
and frozen here so the post rebuilds identically.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'delete-the-rest'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'
TOOLS = ['ARCO', 'CapCut', 'Claude', 'GitHub', 'Framer']

# 01 hook    bg-h79  desk-led-neon      first hook outing
# 02 ARCO    bg-h29  supercars-dusk     band luma 18.7
# 03 CapCut  bg-h32  window-silhouette  band luma 38.8  (the one person)
# 04 Claude  bg-h88  supercars-dusk     band luma 28.2
# 05 GitHub  bg-h20  lounge-day         band luma 67.0
# 06 Framer  bg-h34  desk-empty-day     band luma 62.4
# The dark end of this pool is one shoot: h35, h36, h37, h38 and h39 are all
# the same white-and-black supercar pair outside the same concrete villa, and
# best-for-last already ran h36. So none of them come back. h29 is the same
# cars at a different building on wet tarmac and has the darkest band in the
# pool, which is why it carries the ARCO card and its seven lines; h88 is the
# single car in fog and reads as a different photograph entirely, so the two
# supercars-dusk frames here do not pair up. h20 and h34 are the two
# brightest frames that still clear the gate, so they sit at 5 and 6 where
# the least is riding on the read; both have carried five lines before
# (keep-five-2 shot its Claude and Notion cards on them). Slide 4 first ran
# on bg-n04 and came back wrong: the copy crossed a white villa facade in
# daylight, the leading dashes went thin and it was the one bright card in a
# dark set. That is the failure stack-at-19 and all-of-it-at-19 both
# recorded, so the daylight pools n01/n03/n04 and the desk-city-day family
# stay out -- they clear BAND_MAX_LUMA and still lose the text.
BGS = ['bg-h79.jpg', 'bg-h29.jpg', 'bg-h32.jpg',
       'bg-h88.jpg', 'bg-h20.jpg', 'bg-h34.jpg']

# The six frames twelve-apps shot, excluded from this build.
SOURCE_BGS = ['bg-h02.jpg', 'bg-h35.jpg', 'bg-h24.jpg', 'bg-h45.jpg',
              'bg-h36.jpg', 'bg-h21.jpg']

# next_arco_angle() would hand back s1 (Blocked Hours on a schedule), and
# Blocked Hours is already the ARCO line in ten captions, the most recent two
# posts ago. v13 is written for this build and marked used in
# arco_angles.json: the Live Activity is real (FocusLiveActivity draws a
# countdown on the Lock Screen) and no caption has ever named it.
BODY = {
 'ARCO': [
    'The block I’m in sits on the Lock',
    'Screen with the time left on it.',
    '',
    'Picking up the phone shows the plan',
    'before it shows a feed.',
    '',
    'My holy grail.',
 ],
 'CapCut': [
    'Auto captions can be translated',
    'into another language in place.',
    '',
    'One edit becomes the English and',
    'the Spanish cut, not two projects.',
 ],
 'Claude': [
    'A custom Style learns your voice',
    'from one writing sample you paste.',
    '',
    'Every answer after that comes back',
    'in your words, not the model’s.',
 ],
 'GitHub': [
    'Codespaces runs the whole project',
    'in the browser, already installed.',
    '',
    'Any borrowed laptop becomes your',
    'dev machine in about a minute.',
 ],
 'Framer': [
    'Right click a page and Framer makes',
    'a control and a variant of it.',
    '',
    'Traffic splits itself and it names',
    'the winner once one pulls ahead.',
 ],
}

assert set(BGS).isdisjoint(SOURCE_BGS), 'a twelve-apps frame leaked back in'
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
