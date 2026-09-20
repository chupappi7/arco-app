#!/usr/bin/env python3
"""rest-of-my-life: first outing of Thinh's new hook, tools pillar.

  hook      "5 apps i will use / for the rest of my life". Thinh supplied it
            on 2026-09-20 and it was added to tools/hook_pool.json as a tools
            hook in the same build; this is its first post.
  roster    ARCO, ChatGPT, Obsidian, GitHub, Raycast. ChatGPT is the LLM:
            with Manus it is the least recently used model (ten-x-7, eight
            posts back). The other three are apps a solo builder keeps for
            years, which is what the hook promises.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: ChatGPT tasks, custom instructions, canvas,
            study mode, codex from the phone, drive connector, projects,
            memory, record mode, agent mode, and deep research (burned on
            Gemini and Perplexity, same point); Obsidian markdown files,
            backlinks, unlinked mentions, bases, canvas, daily note, block
            links, web clipper, slides; GitHub actions on push and on a
            schedule, pages, codespaces, student pack, release notes,
            dependabot, auto merge, the full stop key; Raycast clipboard,
            quicklinks, snippets, floating notes, extensions, script
            commands, menu search, app hotkeys, meeting countdown, hyper key.
            Fresh here: ChatGPT branching a chat from any message, Obsidian
            Sync end to end encryption, GitHub push protection, the Raycast
            calculator reading time zones and dates in plain words.
  ARCO      the hook is about the apps that stay, so THEME is 'planning' and
            the slide carries the task and focus copy.
  photos    hook bg-h66 (desk-led-neon), the next hook-only frame the hook
            log has not used. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, one person at most
            (bg-h32, slide 6), nothing from the previous post
            (run-it-all-at-19-2). bg-n05 rendered first for GitHub and was
            replaced: its lit monitors sit under the copy.

Usage:
    python3 tools/gen-rest-of-my-life.py            # every slide
    python3 tools/gen-rest-of-my-life.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)
from PIL import Image, ImageDraw

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'rest-of-my-life'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['5 apps i will use', 'for the rest of my life']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'ChatGPT', 'Obsidian', 'GitHub', 'Raycast']
TITLES = ['1. ARCO: Day Planner & Focus', '2. ChatGPT', '3. Obsidian',
          '4. GitHub', '5. Raycast']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h66.jpg',   # 01 hook      desk-led-neon
       'bg-h36.jpg',   # 02 ARCO      supercars-dusk     band luma 20.3
       'bg-h22.jpg',   # 03 ChatGPT   lounge-day         band luma 53.5
       'bg-h31.jpg',   # 04 Obsidian  lounge-night       band luma 19.7
       'bg-n06.jpg',   # 05 GitHub    desk-empty-day     band luma 53.6
       'bg-h32.jpg']   # 06 Raycast   window-silhouette  band luma 38.8, person

BODY = {
 'ChatGPT': [
    'Any message in a chat can branch',
    'into a new chat from that point.',
    '',
    'Two directions get tried from one',
    'setup, with nothing pasted twice.',
 ],
 'Obsidian': [
    'Obsidian Sync is end to end',
    'encrypted with your own password.',
    '',
    'Notes move between devices and',
    'nobody in between can read a line.',
 ],
 'GitHub': [
    'Push protection scans every commit',
    'for api keys before it lands.',
    '',
    'A leaked key stops at the push,',
    'not at the bill a month later.',
 ],
 'Raycast': [
    'The calculator takes plain words:',
    '3pm in tokyo, or in six weeks.',
    '',
    'The time zone maths is done in',
    'the search bar, no app opened.',
 ],
}

BODY_MAX_W = 800


def assert_body_fits(body):
    f = c.font(50, 'Semibold')
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    for tool, lines in body.items():
        for ln in lines:
            if not ln:
                continue
            w = d.textbbox((0, 0), ln, font=f)[2]
            if w > BODY_MAX_W:
                raise SystemExit(f'{tool}: "{ln}" is {w}px wide, over {BODY_MAX_W}')


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

    c.assert_audience(TOOLS)
    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    assert_body_fits(BODY)
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
