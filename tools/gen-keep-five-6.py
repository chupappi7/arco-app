#!/usr/bin/env python3
"""keep-five-6: sixth outing of the "5 apps i would keep" hook, icon shelf.

"the 5 apps i would keep / if i deleted everything else" (tools pillar).
Third least recently used of the three hooks hook_rules.eligible(
pillar='tools') returned on 2026-09-18: keep-five-5, five posts back.

  roster    ARCO, Perplexity, Supabase, Obsidian, ClickUp. Perplexity is
            the LLM: third least recently used model (wish-i-knew-at-17-4,
            six posts back) and this hook has never carried it. Five jobs,
            one app each: the day, the web, the backend, the notes, the
            work.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Perplexity spaces, source focus, labs,
            pages, deep research; Supabase auth, RLS, instant API,
            realtime, cron, image transforms; Obsidian links, backlinks,
            bases, canvas, daily note template, block links, unlinked
            mentions, plain markdown, web clipper; ClickUp views,
            dependencies, multi-list tasks, automations, doc highlight to
            task, list email. Fresh here: the Perplexity Comet browser
            acting on the page, Supabase branching per pull request, the
            Obsidian Slides core plugin, ClickUp Clips transcribed inside
            a task. Each verified by search on 2026-09-18 before it went
            on a slide.
  ARCO      the cull asks what runs the day, so THEME is 'planning'.
  photos    hook bg-h64 (desk-led-neon), next hook-only frame without a
            person the hook log has not used after h58 and h63 went to
            the other two posts of this batch. App slides from
            non-hook-only vibes under BAND_MAX_LUMA, no adjacent vibe
            repeat, no person, nothing from the previous post
            (wish-i-knew-at-17-5) and disjoint from 4x-productivity-9.
            h37 and h21 last ran on best-for-last-5, three posts back,
            outside the cooldown.

Usage:
    python3 tools/gen-keep-five-6.py            # every slide
    python3 tools/gen-keep-five-6.py --only 03  # one slide, for redos
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
TOPIC = 'keep-five-6'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the 5 apps i would keep', 'if i deleted everything else']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Perplexity', 'Supabase', 'Obsidian', 'ClickUp']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Perplexity', '3. Supabase',
          '4. Obsidian', '5. ClickUp']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h64.jpg',   # 01 hook        desk-led-neon
       'bg-h88.jpg',   # 02 ARCO        supercars-dusk    band luma 28.2
       'bg-h32.jpg',   # 03 Perplexity  window-silhouette band luma 38.8, person
       'bg-h37.jpg',   # 04 Supabase    supercars-dusk    band luma 22.7
       'bg-n01.jpg',   # 05 Obsidian    villa-day         band luma 66.3
       'bg-h21.jpg']   # 06 ClickUp     lounge-night      band luma 64.6

BODY = {
 'Perplexity': [
    'Comet is a browser whose assistant',
    'does the task on the page itself.',
    '',
    'It fills the form and books the',
    'table while you watch it type.',
 ],
 'Supabase': [
    'Supabase branching gives each pull',
    'request a database of its own.',
    '',
    'A schema change is tried on the',
    'branch and merged, never run live.',
 ],
 'Obsidian': [
    'Put three dashes between sections',
    'and Slides presents the note.',
    '',
    'The revision notes become the',
    'talk with nothing rebuilt.',
 ],
 'ClickUp': [
    'Record a clip inside a ClickUp task',
    'and it transcribes what you said.',
    '',
    'Feedback on a screen is a video in',
    'the task, not a paragraph under it.',
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
