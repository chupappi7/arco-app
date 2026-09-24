#!/usr/bin/env python3
"""ship-weekend-5: fifth outing of the ship-in-a-weekend hook, build pillar.

  hook      "how i ship in a weekend / what used to take a month". The least
            recently used of the four hooks hook_rules.eligible(pillar='build')
            returned on 2026-09-24.
  roster    ARCO, Cursor, Supabase, Stripe, TestFlight. Cursor is the LLM:
            least recently used model (17 posts back). The rest answer the
            hook in build order: backend, payments, beta.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Cursor tab, rules, cmd k, bugbot, docs
            indexing, slack agents; checkpoints (Claude Code), parallel
            attempts (Codex), plan docs and browser testing (Antigravity).
            Supabase per-table api, rls, branching, cron, realtime, storage
            transforms. Stripe payment links, test mode, portal, tax,
            invoices, smart retries. TestFlight public links, internal
            builds. Fresh here: Cursor custom slash commands, Supabase
            generated types, Stripe CLI webhook forwarding, TestFlight
            screenshot feedback.
  ARCO      the hook is about shipping, so THEME is 'build';
            next_arco_angle('build') drew v9.
  photos    the gen-daily-batch filters: pick_hook_bg gave bg-h76 (night
            desk, hook only), app slides under BAND_MAX_LUMA, no person, no
            adjacent vibe repeat, nothing from boring-phone-screens. 04 first
            drew bg-h49 and put the copy over bright monitors; swapped to
            h32, the one person in the post.

Usage:
    python3 tools/gen-ship-weekend-5.py            # every slide
    python3 tools/gen-ship-weekend-5.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)
from PIL import Image, ImageDraw

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'ship-weekend-5'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['how i ship in a weekend', 'what used to take a month']
PILLAR = 'build'
THEME = 'build'

TOOLS = ['ARCO', 'Cursor', 'Supabase', 'Stripe', 'TestFlight']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Cursor', '3. Supabase',
          '4. Stripe', '5. TestFlight']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# Drawn once with next_arco_angle(THEME) and written out, so a redo of one
# slide does not advance the rotation and change the copy.
ARCO_BODY = ['All of my tasks sit here and planning', 'the day takes 30 seconds.', '', 'Focus mode puts every distraction', 'away, and Blocked Hours repeats it', 'every weekday.', '', 'My holy grail.']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h76.jpg',   # 01 hook        desk-led-neon      pick_hook_bg
       'bg-h29.jpg',   # 02 ARCO        supercars-dusk     band luma 18.7
       'bg-h22.jpg',   # 03 Cursor      lounge-day         band luma 53.5
       'bg-h32.jpg',   # 04 Supabase    window-silhouette  band luma 38.8 (the one person)
       'bg-h24.jpg',   # 05 Stripe      lounge-night       band luma 49.8
       'bg-h38.jpg']   # 06 TestFlight  supercars-dusk     band luma 21.2

BODY = {
 'Cursor': [
    'Save a prompt in .cursor/commands',
    'and it becomes a slash command.',
    '',
    'Your whole release checklist runs',
    'from typing /ship in the chat.',
 ],
 'Supabase': [
    'One CLI command generates the',
    'TypeScript types from your tables.',
    '',
    'A renamed column breaks the build',
    'on your laptop, not the live app.',
 ],
 'Stripe': [
    'The Stripe CLI forwards webhook',
    'events to the app on your laptop.',
    '',
    'You test a paid signup end to end',
    'before anything is deployed.',
 ],
 'TestFlight': [
    'Testers screenshot the beta and',
    'send feedback from inside the app.',
    '',
    'It lands in App Store Connect with',
    'the device and build attached.',
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
    # preflight only checks the LLM count for the tools pillar; build posts
    # carry exactly one model too.
    c.assert_one_llm(TOOLS)
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
        body = ARCO_BODY if tool == 'ARCO' else BODY[tool]
        if tool == 'ARCO':
            print('  ARCO angle:', ' / '.join(l for l in body if l))
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma '
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
