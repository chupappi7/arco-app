#!/usr/bin/env python3
"""ten-x-3: a tools post on the "how i 10x'd / my productivity" hook.

The build was asked for "i pay for 12 apps / these 5 do all the work". That
hook went out on the post immediately before this one (twelve-down-to-five),
so hook_rules.status() blocks it for another 4 posts and assert_hook_fresh
would refuse the render. Rewording it does not help either: the cooldown keys
on the parent hook, and anything close enough to read as the same hook scores
above VARIANT_MIN.

What the request was actually after was the short first line — "i pay for 12
apps" is what makes the two-tone treatment work, because a short line 1 hits
the HOOK_L1_SIZE ceiling instead of shrinking toward line 2. Of the five
hooks eligible for the tools pillar, "how i 10x'd" is the shortest opener in
the pool at 11 characters, so it renders at the ceiling with the widest size
gap to the yellow line under it. It last went out on ten-x-2, eight posts
back, well clear of HOOK_COOLDOWN.

Not "5 tools to stay productive / i saved the best for last", the one hook in
the pool that has never gone out: it promises the best pick is last, and this
post leads with ARCO at #1.

Sharing a hook with ten-x-2 means the roster and every teaching point have to
be different, or it is the same post twice. ten-x-2 ran ARCO, Superwhisper,
Granola, Claude, CleanShot X; none of those four return here.

Teaching points, each checked against every caption in hooks.json first:
  Gemini      Live screen sharing. Gemini has been taught through Gems
              (selling-online), Deep Research (pay-double) and whole-file
              upload (showed-me-at-17); never Live. Deliberately not the
              "runs on a schedule" angle, which before-nine already spent on
              ChatGPT tasks.
  Raycast     script commands you write yourself. Taught before through
              quicklinks, extensions, snippets, floating notes and clipboard
              history; never your own scripts.
  Zapier      Digest. Taught before through paths, filters and schedules.
  Higgsfield  batch generation. Named in three captions, never once taught.

LLM rotation: the last four tools posts ran Codex, ChatGPT, Codex, Codex.
Gemini's last outing was pay-double-2, six posts back.

The ARCO card is next_arco_angle('planning') -> v8, written out literally so
a rebuild cannot hand this post copy the caption does not describe. 'planning'
is the theme the hook asks for: "10x my productivity" is answered by the day
being planned and the distractions being shut, not by blocking as a subject.

Backgrounds follow the gen-daily-batch walk (hook-only vibes on slide 1 only,
copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most one person),
at the one-post exclusion window BG_COOLDOWN requires rather than the widened
three wish-at-17 and twelve-down-to-five used. Widening it starves the walk
down to the eleven brightest frames in the pool, and the first render proved
what that costs: it put bg-h51 on #6, a daylight office with the copy across
three monitors and a bright sky, and it seated slides #2 and #4 on bg-h37 and
bg-h39, the same villa and the same two supercars a few metres apart. The
vibe guard passes both because they are not adjacent; the carousel still
reads as one scene twice.

At the one-post window the walk has 21 frames and every slide is a different
place: a dark chandelier lounge, a single car on a wet drive, a night lounge
over the city, a villa forecourt, a man at a window.

Three frames were dropped by eye rather than by the gate, all of them inside
BAND_MAX_LUMA: bg-h51 (body copy across three lit monitors), bg-h21 (the last
line over a cream sofa) and bg-n04. bg-n04 is the one worth writing down,
because twelve-down-to-five used it and reported the band sitting on the dark
driveway. It does not do that here. This post's Raycast card is six lines
deep against that post's five, so frame_for_band pans further up and the copy
lands across the lit villa facade and the hedge line instead. The frame is
fine; the pan depends on how much copy the slide carries, so a background
that worked at five lines has to be looked at again at six.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'ten-x-3'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ["how i 10x'd", 'my productivity']
TOOLS = ['ARCO', 'Gemini', 'Raycast', 'Zapier', 'Higgsfield']
BGS = ['bg-h71.jpg',   # 01 hook        desk-led-neon      first outing, hook-only vibe
       'bg-h31.jpg',   # 02 ARCO        lounge-night       band luma 19.7
       'bg-h88.jpg',   # 03 Gemini      supercars-dusk     band luma 28.2
       'bg-h22.jpg',   # 04 Raycast     lounge-day         band luma 53.5
       'bg-h35.jpg',   # 05 Zapier      supercars-dusk     band luma 37.2
       'bg-h32.jpg']   # 06 Higgsfield  window-silhouette  band luma 38.8, the one person

BODY = {
 # next_arco_angle('planning') -> v8, frozen so a rebuild matches the caption.
 'ARCO': [
    'I manage all my tasks here and the',
    'day is planned in half a minute.',
    '',
    'Focus mode puts every distraction',
    'away until I am done.',
    '',
    'My holy grail.',
 ],
 'Gemini': [
    'A Live session can see your screen',
    'while you share it.',
    '',
    'You ask about the error in front',
    'of you instead of retyping it.',
 ],
 'Raycast': [
    'Drop your own shell script in and',
    'it becomes a command with its own',
    'keyword.',
    '',
    'The thing you opened the terminal',
    'for now runs from the search bar.',
 ],
 'Zapier': [
    'A Digest step collects items and',
    'releases them as one message on a',
    'schedule.',
    '',
    'Ten alerts through the week arrive',
    'as one summary on friday.',
 ],
 'Higgsfield': [
    'One prompt runs as a batch and',
    'comes back as several finished',
    'frames.',
    '',
    'You pick the shot instead of',
    'rewriting the prompt ten times.',
 ],
}

preflight(TOPIC, TOOLS, BGS, pillar='tools', hook=HOOK)

# pick_hook_bg narrows to unused hook-only vibes and silently ignores
# `prefer` when any exist, so claim the background by hand rather than let it
# log one this post never rendered.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'), indent=1)

hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
mark_hook_used(HOOK, TOPIC)

icons = json.load(open(c.TOOL_POOL))['icons']
for i, tool in enumerate(TOOLS):
    n, bg = i + 1, BGS[i + 1]
    app_slide(bg, icons[tool], f'{n}. {tool}', BODY[tool], f'{OUT}/{n+1:02d}.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
