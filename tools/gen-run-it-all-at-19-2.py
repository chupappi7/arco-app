#!/usr/bin/env python3
"""run-it-all-at-19-2: month-in-a-weekend's shape on a new hook, roster, photos.

month-in-a-weekend ("how i ship in a weekend / what used to take a month") is
the post being replicated. What is kept is the two things that made it work:
a build-pillar hook a solo builder wants to be true of themselves, and the
roster pattern, ARCO leading plus exactly one LLM plus build-lane peers, one
tool per slide, no CTA.

What is deliberately different, so this does not read as the same post again:

  hook      "everything i run my business on / at 19" (build pillar). The
            least recently used of the three build hooks
            hook_rules.eligible(pillar='build') returned on 2026-09-18; the
            source's own hook is the second on that list and is not reused.
  roster    ARCO, Claude, Figma, Framer, Firebase (the suggested roster).
            No prior post carries these five; stack-at-19 had Figma and
            Framer but with Codex and GitHub. Claude is the LLM; the source
            and both earlier outings of this hook carried Codex/Perplexity.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Claude agents in parallel, projects, MCP,
            plan mode, checkpoints, routines, skills, custom styles, the
            folder pass, mockup to screen, dictation to draft, quiz and
            tool building; Figma components, auto layout, variables and
            modes, dev mode, prototype links, community files, slides;
            Framer design-is-the-site, CMS collections, analytics, A/B
            testing; Firebase remote config (twice), scheduled push.
            Fresh here: Claude Code hooks running a command after every
            edit, Figma Buzz bulk create from a spreadsheet, Framer
            localization with a URL per language, a Firebase Cloud
            Function firing on account creation.
  ARCO      the hook asks what the business runs on, so THEME is 'business'.
  photos    hook bg-h65 (desk-led-neon), the next hook-only frame the hook
            log has not used. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, one person at most,
            nothing from the previous post (keep-five-6) and nothing from
            the source post or either earlier outing of this hook.

Usage:
    python3 tools/gen-run-it-all-at-19-2.py            # every slide
    python3 tools/gen-run-it-all-at-19-2.py --only 03  # one slide, for redos
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
TOPIC = 'run-it-all-at-19-2'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['everything i run my business on', 'at 19']
PILLAR = 'build'
THEME = 'business'

TOOLS = ['ARCO', 'Claude', 'Figma', 'Framer', 'Firebase']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Claude', '3. Figma',
          '4. Framer', '5. Firebase']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h65.jpg',   # 01 hook      desk-led-neon
       'bg-h29.jpg',   # 02 ARCO      supercars-dusk     band luma 18.7
       'bg-n04.jpg',   # 03 Claude    villa-day          band luma 57.8
       'bg-h39.jpg',   # 04 Figma     supercars-dusk     band luma 35.8
       'bg-h20.jpg',   # 05 Framer    lounge-day         band luma 67.0
       'bg-h45.jpg']   # 06 Firebase  window-silhouette  band luma 54.3, person

# The photos of the source post and of this hook's two earlier outings. None
# may reappear: this post is the source's shape, so sharing its photos too
# would make it a re-shoot, and the hook's earlier posts are the ones a
# returning viewer would compare it against.
SOURCE_BGS = ['bg-h68.jpg', 'bg-h38.jpg', 'bg-h31.jpg', 'bg-h22.jpg',
              'bg-h32.jpg', 'bg-h24.jpg',
              'bg-h40.jpg', 'bg-h34.jpg', 'bg-h35.jpg',
              'bg-h74.jpg', 'bg-h51.jpg', 'bg-h21.jpg']

BODY = {
 'Claude': [
    'A hook runs a command of yours',
    'after every edit Claude Code makes.',
    '',
    'The formatter and the tests run',
    'before you ever review the change.',
 ],
 'Figma': [
    'Figma Buzz fills one template from',
    'a spreadsheet, one row per asset.',
    '',
    'Fifty ad variants with their own',
    'names and prices land in one go.',
 ],
 'Framer': [
    'Framer localization translates',
    'the site into a second language.',
    '',
    'Each language gets its own URL,',
    'so a second market opens without',
    'building a second site.',
 ],
 'Firebase': [
    'A Cloud Function can fire the',
    'moment a new account is created.',
    '',
    'The welcome email sends itself and',
    'no server has to stay running.',
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

    clash = sorted(set(BGS) & set(SOURCE_BGS))
    if clash:
        raise SystemExit(f'reuses source-lineage photos: {", ".join(clash)}')

    # preflight only runs the LLM guard on the tools pillar, and this post is
    # build, so it is asked for by name.
    c.assert_one_llm(TOOLS)
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
