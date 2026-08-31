#!/usr/bin/env python3
"""month-in-a-weekend: launch-weekend's shape on a new hook, roster and photos.

launch-weekend ("launch an app / in one weekend") is the post being replicated.
What is kept is the two things that made it work: the hook's shape -- a
shipping-speed claim a solo builder wants to be true -- and the roster pattern,
ARCO plus exactly one LLM plus build-lane peers, one tool per slide.

What is deliberately different, so this does not read as the same post again:

  hook      "how i ship in a weekend / what used to take a month" (build
            pillar, eligible, last out in weekend-not-month ~12 posts back).
  roster    ARCO, Codex, GitHub, Linear, Stripe.
  photos    six backgrounds that appear in neither launch-weekend nor
            stack-at-19, the other post in this lineage.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and therefore avoided: Codex writing a feature from a
            description, Codex in a sandbox opening a PR, Codex reviewing a
            tagged diff, AGENTS.md; GitHub Actions on push, on a schedule,
            branch protection, Dependabot, repo backup; Linear cycles
            carrying issues forward; Stripe payment links, test mode and the
            customer portal.

Roster note -- why this is not the roster that was suggested
-----------------------------------------------------------
The suggestion was Codex, ARCO, GitHub, Figma, Framer. Those five names are
exactly stack-at-19's roster, which went out two posts ago, so shipping them
again is the "same five names in the same order" failure compose.py warns
about in TOOL_COOLDOWN. Codex, ARCO and GitHub are kept; Figma and Framer are
replaced by Linear and Stripe, which sit in the same build lane and answer the
same hook (the weekend ends with something merged and something sellable).

Usage:
    python3 tools/gen-month-in-a-weekend.py            # every slide
    python3 tools/gen-month-in-a-weekend.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'month-in-a-weekend'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['how i ship in a weekend', 'what used to take a month']
PILLAR = 'build'
# The hook asks how a month of work fits in a weekend, so ARCO answers on
# planning and protecting the hours, not on a study block or a screen time
# number.
THEME = 'build'

TOOLS = ['ARCO', 'Codex', 'GitHub', 'Linear', 'Stripe']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Codex', '3. GitHub',
          '4. Linear', '5. Stripe']

# index 0 is the hook, 1..5 are the app slides in order.
# First pass ran slides 3 and 5 on the freshest photos that cleared the luma
# gate, bg-n06 (53.6) and bg-h49 (54.8). Both are daylight offices and both
# failed the read exactly the way stack-at-19 recorded: after frame_for_band
# pans the photo the copy lands on bright glass and sky, the leading dashes
# vanish and the thin strokes dissolve. The gate is necessary, not sufficient.
# Only genuinely dark frames hold five lines, so freshness is chosen inside
# that set. Inside it, every supercars-dusk frame (h35, h37, h38, h39) is the
# same concrete villa with the same two cars a few metres apart, which is the
# near-duplicate deleted-everything cut h36 for, so exactly one of that family
# is used. bg-h22 is tagged lounge-day and is in fact a warm lounge at night;
# it is the fifth distinct dark scene the pool has.
BGS = ['bg-h68.jpg',   # 01 hook    desk-led-neon      (first hook outing)
       'bg-h38.jpg',   # 02 ARCO    supercars-dusk     band luma 21.2
       'bg-h31.jpg',   # 03 Codex   lounge-night       band luma 19.7
       'bg-h22.jpg',   # 04 GitHub  lounge-day (night) band luma 53.5
       'bg-h32.jpg',   # 05 Linear  window-silhouette  band luma 38.8
       'bg-h24.jpg']   # 06 Stripe  lounge-night       band luma 49.8

# The six photographs launch-weekend was shot on. None may reappear: this post
# is that post's shape, so sharing its photos too would make it a re-shoot.
SOURCE_BGS = ['bg-h17.jpg', 'bg-h21.jpg', 'bg-h16.jpg', 'bg-h09.jpg',
              'bg-h02.jpg', 'bg-h04.jpg']
# Four of the app-slide photos have been out before (h24 and h31 in
# stack-at-19, h31, h32 and h37 in deleted-everything). That is accepted
# rather than banned: the dark half of the pool is about a dozen frames, the
# never-used half is all daylight lounges at 72-90 luma, and an unfamiliar
# photo the copy cannot be read on costs more than a familiar one it can.
# assert_bg_fresh still bars anything from the immediately preceding post.

BODY = {
 'Codex': [
    'You can start a task from the',
    'ChatGPT app on your phone.',
    '',
    'It runs in the cloud, so a task is',
    'still going while you are out.',
 ],
 'GitHub': [
    'Pages serves a folder in the repo',
    'as a live site, on push, for free.',
    '',
    'The landing page ships the same',
    'weekend as the app, with no host.',
 ],
 'Linear': [
    'Put the issue ID in the branch',
    'name and Linear picks it up.',
    '',
    'The issue moves itself to done the',
    'moment the pull request merges.',
 ],
 'Stripe': [
    'Stripe Tax works out the sales tax',
    "for the buyer's country at checkout.",
    '',
    'It also flags where you have',
    'crossed a registration threshold.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    clash = sorted(set(BGS) & set(SOURCE_BGS))
    if clash:
        raise SystemExit(f'reuses launch-weekend photos: {", ".join(clash)}')

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
