#!/usr/bin/env python3
"""business-at-19-2: second outing of the business-at-19 hook, fresh roster.

"the tools i use to run my business / at 19 years old" (build pillar,
eligible, least recently used; first outing was business-at-19 with ARCO,
Claude, Notion, Canva, RevenueCat).

What is deliberately different from that outing:

  roster    ARCO, Codex, Stripe, Higgsfield, Buffer. Codex is the LLM: the
            last posts ran Claude, ChatGPT, Cursor, Manus, Perplexity and
            Antigravity; Codex last appeared in ship-alone-3.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and therefore avoided: Codex from-a-description, sandbox
            PR, AGENTS.md, PR review, phone/cloud start, screenshot input,
            parallel attempts, one-terminal-command; the MCP-connection
            point (business-at-19 spent it on Claude under this same hook);
            Stripe payment links, test mode, customer portal and tax;
            Higgsfield batch frames and face consistency; Buffer's
            per-platform queue times and one-box-per-channel edits.
  photos    picked with the gen-daily-batch.py approach: hook from the
            unused pool (bg-h44, window-silhouette, the post's single
            person), app slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeats, nothing from the
            previous post (best-for-last-3).

Usage:
    python3 tools/gen-business-at-19-2.py            # every slide
    python3 tools/gen-business-at-19-2.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'business-at-19-2'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to run my business', 'at 19 years old']
PILLAR = 'build'
# The hook promises the stack behind a business, so ARCO answers on planning
# the day and protecting the hours, not on study or screen time.
THEME = 'business'

TOOLS = ['ARCO', 'Codex', 'Stripe', 'Higgsfield', 'Buffer']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Codex', '3. Stripe',
          '4. Higgsfield', '5. Buffer']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h44.jpg',   # 01 hook       window-silhouette (person)
       'bg-h21.jpg',   # 02 ARCO       lounge-night       band luma 64.6
       'bg-h22.jpg',   # 03 Codex      lounge-day         band luma 53.5
       'bg-h29.jpg',   # 04 Stripe     supercars-dusk     band luma 18.7
       'bg-h31.jpg',   # 05 Higgsfield lounge-night       band luma 19.7
       'bg-h35.jpg']   # 06 Buffer     supercars-dusk     band luma 37.2

BODY = {
 'Codex': [
    "One command resumes yesterday's",
    'session, context and all.',
    '',
    'Monday picks up mid-feature, with',
    'nothing re-explained.',
 ],
 'Stripe': [
    'Invoices carry automatic',
    'reminders on a schedule you set.',
    '',
    'The follow-up email sends itself',
    'until the invoice gets paid.',
 ],
 'Higgsfield': [
    'A motion preset animates a still',
    'image with a named camera move.',
    '',
    'One product photo becomes video',
    'b-roll with nothing filmed.',
 ],
 'Buffer': [
    'It reads your past engagement and',
    'names the best hour per channel.',
    '',
    'You schedule into those slots',
    'instead of guessing when.',
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
