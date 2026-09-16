#!/usr/bin/env python3
"""ship-weekend-4: fourth outing of the ship-in-a-weekend hook.

Hook "how i ship in a weekend / what used to take a month" (build pillar,
eligible, last out in app-in-a-weekend 3 posts back). The other eligible
build hook was "everything i run my business on / at 19", but business-at-19-2
went out 0 posts ago on a near-identical at-19 line, so this one carries.

What is deliberately different from the three prior outings (Codex/GitHub/
Linear/Stripe twice, then Claude/Supabase/TestFlight/Sentry):

  roster    ARCO, Gemini, Vercel, Superwall, PostHog. Gemini is the LLM:
            least recently used (11 posts, vs Antigravity 8, Codex 0,
            Claude 2). Superwall is a first outing; PostHog's second.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Gemini deep research / gems / textbook
            upload / live screen share / gmail+drive; Vercel instant deploy,
            preview URLs, one-click rollback (x4); PostHog feature flags +
            session replay; Firebase remote config covers the "change the
            live app from a dashboard" shape, so Superwall's point leans on
            the review wait, not the dashboard.
  photos    hook on bg-h46 (desk-city-day, next in the hook rotation, no
            person). App slides h88/h24/h38/h32/h34: one person (h32), one
            of the h35-h39 villa-cars family (h38), no adjacent vibe
            repeats, none from business-at-19-2 (BG_COOLDOWN), all under
            the luma gate. h34 is the brightest at 62; judged on the render.

Usage:
    python3 tools/gen-ship-weekend-4.py            # every slide
    python3 tools/gen-ship-weekend-4.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'ship-weekend-4'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['how i ship in a weekend', 'what used to take a month']
PILLAR = 'build'
# The hook asks how a month of work fits into a weekend, so ARCO answers on
# planning the day and protecting the hours.
THEME = 'build'

TOOLS = ['ARCO', 'Gemini', 'Vercel', 'Superwall', 'PostHog']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Gemini', '3. Vercel',
          '4. Superwall', '5. PostHog']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h46.jpg',   # 01 hook      desk-city-day     (next in hook rotation)
       'bg-h88.jpg',   # 02 ARCO      supercars-dusk    band luma 28.2
       'bg-h24.jpg',   # 03 Gemini    lounge-night      band luma 49.8
       'bg-h38.jpg',   # 04 Vercel    supercars-dusk    band luma 21.2
       'bg-h32.jpg',   # 05 Superwall window-silhouette band luma 38.8 (person)
       'bg-h34.jpg']   # 06 PostHog   desk-empty-day    band luma 62.4

BODY = {
 'Gemini': [
    'Gemini CLI runs a coding agent',
    'in your repo, free with a Google',
    'account, 1,000 requests a day.',
    '',
    'A weekend of building costs',
    'nothing in API bills.',
 ],
 'Vercel': [
    'Drop a file in the api folder and',
    'it deploys as a live endpoint.',
    '',
    'Your webhook or form handler is',
    'live with no server to set up.',
 ],
 'Superwall': [
    'The paywall loads from a',
    'dashboard, not the app binary.',
    '',
    'A new price or design goes live',
    'with no App Store review.',
 ],
 'PostHog': [
    'Autocapture logs every click and',
    'pageview with no tracking code.',
    '',
    'Ship sunday and see monday what',
    'people actually touched.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    # preflight only runs the LLM and cooldown guards on the tools pillar, and
    # this post is build, so those two are asked for by name.
    c.assert_one_llm(TOOLS)
    c.assert_fresh_tools(TOOLS)
    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            c.pick_hook_bg(prefer=BGS[0])
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
        mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
        app_slide(bg, icons[tool], TITLES[i], body, f'{OUT}/{n+1:02d}.jpg')
        print(f'  {bg}  {c.VIBES.get(bg):16s} band luma '
              f'{c.copy_band_luma(bg):.1f}')

    if only is None:
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
