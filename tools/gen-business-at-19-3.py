#!/usr/bin/env python3
"""business-at-19-3: third outing of the business-at-19 hook, build pillar.

  hook      "the tools i use to run my business / at 19 years old". One of
            the two hooks hook_rules.eligible(pillar='build') returned on
            2026-09-23.
  roster    ARCO, Gemini, Stripe, PostHog, Airtable. Gemini is the LLM: the
            least recently used model (4x-productivity-9).
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Gemini live screen share, Gmail/Drive,
            Chrome tabs, textbook upload, YouTube, Gems, Deep Research on its
            own; Stripe payment links, invoice reminders, tax, test mode,
            customer portal; PostHog surveys, flags with replay; Airtable
            forms, interfaces, lookups. Loom was dropped because its AI
            chapters are already taught. Gemini Canvas turning a report into a
            web page went to pay-for-twelve-3, built alongside. Fresh here:
            Gemini Audio Overview, Stripe Smart Retries, PostHog funnels,
            Airtable AI fields.
  ARCO      the hook is about running a business, so THEME is 'business';
            next_arco_angle('business') drew v7.
  photos    the gen-daily-batch walk: pick_hook_bg gave bg-h16, and the app
            slides come from frames under BAND_MAX_LUMA with no person (the
            hook has one), no adjacent vibe repeat, and nothing in the post
            recorded just before (BG_COOLDOWN = 1). Several builds ran
            alongside this one and kept rewriting bg_history, so frames
            were chosen to avoid their posts where the pool allowed and
            never to clash with the neighbouring post. Desk-city-day frames
            put the copy over monitors; they sit between darker scenes.

Usage:
    python3 tools/gen-business-at-19-3.py            # every slide
    python3 tools/gen-business-at-19-3.py --only 03  # one slide, for redos
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
TOPIC = 'business-at-19-3'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i use to run my business', 'at 19 years old']
PILLAR = 'build'
THEME = 'business'

TOOLS = ['ARCO', 'Gemini', 'Stripe', 'PostHog', 'Airtable']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Gemini', '3. Stripe',
          '4. PostHog', '5. Airtable']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# Drawn once with next_arco_angle(THEME) and written out, so a redo of one
# slide does not advance the rotation and change the copy.
ARCO_BODY = ['Every task, every habit, planned in', '30 seconds.', '', 'Focus mode puts every distraction', 'away.', '', 'My holy grail.']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h16.jpg',   # 01 hook      desk-person-night  the one person
       'bg-h24.jpg',   # 02 ARCO      lounge-night       band luma 49.8
       'bg-h50.jpg',   # 03 Gemini    desk-city-day      band luma 64.7
       'bg-h29.jpg',   # 04 Stripe    supercars-dusk     band luma 18.7
       'bg-h34.jpg',   # 05 PostHog   desk-empty-day     band luma 62.4
       'bg-h21.jpg']   # 06 Airtable  lounge-night       band luma 64.6

BODY = {
 'Gemini': [
    'Audio Overview turns a doc you',
    'upload into a two host podcast.',
    '',
    'A 30 page contract gets heard on',
    'a walk, not read at a desk.',
 ],
 'Stripe': [
    'Smart Retries charge a failed card',
    'again when it is likely to pass.',
    '',
    'A declined renewal comes back as',
    'revenue with no email from you.',
 ],
 'PostHog': [
    'A funnel shows the exact step',
    'where people drop out of signup.',
    '',
    'You fix the one screen losing the',
    'most users, not every screen.',
 ],
 'Airtable': [
    'An AI field fills a column by',
    'reading every row for you.',
    '',
    '200 customer messages get tagged',
    'by topic without reading one.',
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
