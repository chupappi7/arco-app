#!/usr/bin/env python3
"""launch-weekend-2: launch-weekend replicated, not re-shot.

launch-weekend (2026-08-24) was the builder stack that makes a weekend launch
real: Claude, ARCO, Supabase, Vercel, RevenueCat under "launch an app / in one
weekend". This keeps what made it work, the weekend-launch hook shape and the
roster pattern (one coding agent, ARCO, then the tools that carry a launch),
and changes everything that would make it a repeat:

  hook      "how i ship in a weekend / what used to take a month" from
            tools/hook_pool.json: build pillar, the same promise as the source
            hook, and the least recently used eligible build hook (last out in
            app-in-a-weekend, ~26 posts back). The source hook predates the
            pool and is not in it.
  roster    ARCO, Codex, GitHub, Figma, Framer, ARCO leading at #1. Codex is
            the one LLM.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Codex writes/runs/fixes, sandbox + PR,
            AGENTS.md, phone start, screenshot input, parallel attempts, one
            terminal command, session resume, network-off sandbox, browser
            screenshots, PR review; GitHub Actions on push, on a schedule,
            Pages, Codespaces, student pack, release notes, Dependabot,
            auto merge, the full stop key, push protection, branch
            protection; Figma components, auto layout, variables, dev mode,
            prototype links, community files, slides, Buzz; Framer canvas
            publish, CMS collections, analytics, A/B tests, localization.
  photos    none of the six frames launch-weekend was shot on (bg-h17, h21,
            h16, h09, h02, h04) and none from the post before this one.
            Hook on bg-h70, the first desk-led-neon frame with no person that
            the hook log has not used. App slides on the dark set:
            month-in-a-weekend recorded that daylight frames passing the
            luma gate still failed the read.

  01 hook    bg-h70  desk-led-neon
  02 ARCO    bg-h31  lounge-night       copy_band_luma 19.7
  03 Codex   bg-h38  supercars-dusk     copy_band_luma 21.2
  04 GitHub  bg-h22  lounge-day         copy_band_luma 53.5
  05 Figma   bg-h39  supercars-dusk     copy_band_luma 35.8
  06 Framer  bg-h45  window-silhouette  copy_band_luma 54.3, the one person

Usage:
    python3 tools/gen-launch-weekend-2.py            # every slide
    python3 tools/gen-launch-weekend-2.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'launch-weekend-2'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['how i ship in a weekend', 'what used to take a month']
PILLAR = 'build'
# The hook asks how a month of work fits into a weekend, so ARCO answers on
# planning the day and protecting the hours.
THEME = 'build'

TOOLS = ['ARCO', 'Codex', 'GitHub', 'Figma', 'Framer']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Codex', '3. GitHub',
          '4. Figma', '5. Framer']

# The six photographs the source post was shot on. Never used here.
SOURCE_BGS = ['bg-h17.jpg', 'bg-h21.jpg', 'bg-h16.jpg',
              'bg-h09.jpg', 'bg-h02.jpg', 'bg-h04.jpg']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h70.jpg',   # 01 hook    desk-led-neon
       'bg-h31.jpg',   # 02 ARCO    lounge-night       band luma 19.7
       'bg-h38.jpg',   # 03 Codex   supercars-dusk     band luma 21.2
       'bg-h22.jpg',   # 04 GitHub  lounge-day         band luma 53.5
       'bg-h39.jpg',   # 05 Figma   supercars-dusk     band luma 35.8
       'bg-h45.jpg']   # 06 Framer  window-silhouette  band luma 54.3, person

BODY = {
 'Codex': [
    'Write one setup script and Codex',
    'runs it before every cloud task.',
    '',
    'Every job starts in a project',
    'that already builds and tests.',
 ],
 'GitHub': [
    'Mark a repo as a template and one',
    'click copies the whole setup.',
    '',
    'The next app starts with CI, lint',
    'and folders already in place.',
 ],
 'Figma': [
    'Add 1x, 2x and 3x export settings',
    'to a frame and export once.',
    '',
    'Every icon and screenshot size',
    'comes out in one go.',
 ],
 'Framer': [
    'A form block stores submissions',
    'in the site with no backend.',
    '',
    'The waitlist is live on the',
    'landing page saturday night.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    # preflight only runs the LLM and cooldown guards on the tools pillar, and
    # this post is build, so those two are asked for by name.
    c.assert_one_llm(TOOLS)
    c.assert_fresh_tools(TOOLS)
    c.assert_audience(TOOLS)
    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    assert not set(BGS) & set(SOURCE_BGS), 'a replicate must not reuse the source photos'
    for bg in BGS[1:]:
        luma = c.copy_band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        # Logged by hand: pick_hook_bg narrows to unused night-desk frames and
        # can log one this post never rendered.
        log = json.load(open(f'{c.SP}/hook_usage.json'))
        if BGS[0] not in log:
            json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'),
                      indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg')
        mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
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
        record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
