#!/usr/bin/env python3
"""twelve-down-to-five: a tools post replicating the shape of type-less-2.

type-less-2 is the post worth copying: 1,007 views on getarco against a
155-view outing on vn, on identical slides. What carried it is the shape, not
the words, so the shape is all that comes across.

Kept from the source:
  - the hook's shape. type-less-2 opened "i barely type anymore / these 5
    tools do it for me": a first-person claim on line 1, then a count that
    credits the tools with the result on line 2. "i pay for 12 apps / these 5
    do all the work" is the only hook in the pool built the same way, and it
    is 11 posts past its last outing (do-all-the-work), well clear of
    HOOK_COOLDOWN. Its numbers there were weak (138/106), which is exactly
    the case the reshoot rule covers: views are bimodal and a weak result is
    distribution, not copy.
  - the roster pattern: five tools, one per slide, exactly one LLM, no CTA.

Changed, so it is not a repeat:
  - the roster. Notion, Obsidian, Codex and ClickUp, none of them on
    type-less-2's Superwhisper/Granola/Claude/CleanShot X card. ARCO leads at
    #1 (the source still ran the old ARCO-at-#2 order).
  - all five teaching points, each checked against every caption in
    hooks.json before it was written:
      Notion    rollups. Taught before through databases/views, automations,
                template buttons, synced blocks, Notion AI and forms; never
                a rollup. "rollup" appears nowhere in the corpus.
      Obsidian  Canvas. Taught before through backlinks, plain markdown
                files, the link graph and Bases; never Canvas.
      Codex     image input. month-in-a-weekend, the post immediately before
                this one, took the ChatGPT-phone-app angle, so that one is
                burnt. Also not: writing from a description, the sandbox PR,
                the tagged diff review, or AGENTS.md.
      ClickUp   dependencies. Only ever taught through custom views.
  - six fresh backgrounds.

The ARCO card is next_arco_angle('planning') -> v7, written out literally so
a rebuild cannot hand this post copy the caption does not describe.

Backgrounds follow the gen-daily-batch walk (hook-only vibes on slide 1 only,
copy band under BAND_MAX_LUMA, no adjacent vibe repeat, at most one person)
with the exclusion window widened from the one post BG_COOLDOWN requires to
three, same as wish-at-17. Five posts starves the walk: only three app
backgrounds clear the luma gate at that width.

The walk's fourth pick was bg-h46, and it was replaced by hand after reading
the render. bg-h46, bg-h49 and bg-n05/n06 all clear the luma gate and all
fail the same way month-in-a-weekend, stack-at-19 and ten-x-2 found: they are
daylight offices, so after frame_for_band pans them the copy lands across
monitor bezels and a bright sky and the dashes disappear. bg-n04 puts the
band on a dark hedge and driveway instead. bg-h39 read best of all but it is
the same concrete villa and pair of Lamborghinis as bg-h35 on slide 2, a few
metres apart, so only one of that family is used.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

TOPIC = 'twelve-down-to-five'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

HOOK = ['i pay for 12 apps', 'these 5 do all the work']
TOOLS = ['ARCO', 'Notion', 'Obsidian', 'Codex', 'ClickUp']
BGS = ['bg-h69.jpg',   # 01 hook      desk-led-neon      first outing, hook-only vibe
       'bg-h35.jpg',   # 02 ARCO      supercars-dusk     band luma 37.2
       'bg-h45.jpg',   # 03 Notion    window-silhouette  band luma 54.3, the one person
       'bg-n04.jpg',   # 04 Obsidian  villa-day          band luma 57.8
       'bg-h88.jpg',   # 05 Codex     supercars-dusk     band luma 28.2
       'bg-n01.jpg']   # 06 ClickUp   villa-day          band luma 66.3

BODY = {
 # next_arco_angle('planning') -> v7, frozen so a rebuild matches the caption.
 'ARCO': [
    'Every task, every habit, planned in',
    '30 seconds.',
    '',
    'Focus mode puts every distraction',
    'away.',
    '',
    'My holy grail.',
 ],
 'Notion': [
    'A rollup reads a number off every',
    'linked row and totals it on the',
    'parent page.',
    '',
    'A project shows the hours across',
    'every task under it, added up for',
    'you.',
 ],
 'Obsidian': [
    'Canvas puts your notes on a board',
    'as cards you link with arrows.',
    '',
    'You lay a project out visually and',
    'editing a card edits the file.',
 ],
 'Codex': [
    'Attach a screenshot of the broken',
    'screen to the task and it works',
    'from the image.',
    '',
    'You point at the bug instead of',
    'describing it in words.',
 ],
 'ClickUp': [
    'Mark one task as blocking another',
    'and their dates move together.',
    '',
    'Push one date back and everything',
    'after it reschedules itself.',
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
