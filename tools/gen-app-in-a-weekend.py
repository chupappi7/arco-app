#!/usr/bin/env python3
"""app-in-a-weekend: the ship-in-a-weekend hook on a fresh roster.

Third outing of "how i ship in a weekend / what used to take a month" (build
pillar, eligible, last out in month-in-a-weekend-2 eight posts back). Thinh
asked for this hook with a five-tool roster, ARCO first.

What is deliberately different from month-in-a-weekend and -2, which both ran
ARCO, Codex, GitHub, Linear, Stripe:

  roster    ARCO, Claude, Supabase, TestFlight, Sentry. Claude is the LLM:
            Codex carried both prior outings of this hook, and Claude is the
            least recently used model whose fresh angle answers a shipping
            hook.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and therefore avoided: Claude agents in parallel, quiz
            builder, dictated-draft, in-chat tool builder, custom styles,
            MCP connections; Supabase auth-in-an-afternoon and row level
            security; the public TestFlight 10,000-tester link; Sentry
            session replay.
  photos    hook on bg-h44 (window-silhouette, first hook outing, the post's
            single person); app slides on the genuinely dark frames only.
            month-in-a-weekend recorded that daylight frames passing the luma
            gate still failed the read, so freshness is chosen inside the
            dark set. h29 and h88 are both supercars-dusk but different
            scenes from the h35-h39 villa family; they sit at slides 2 and 4
            so no vibes touch.

Usage:
    python3 tools/gen-app-in-a-weekend.py            # every slide
    python3 tools/gen-app-in-a-weekend.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'app-in-a-weekend'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['how i ship in a weekend', 'what used to take a month']
PILLAR = 'build'
# The hook asks how a month of work fits into a weekend, so ARCO answers on
# planning the day and protecting the hours, not on study or screen time.
THEME = 'build'

TOOLS = ['ARCO', 'Claude', 'Supabase', 'TestFlight', 'Sentry']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Claude', '3. Supabase',
          '4. TestFlight', '5. Sentry']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h44.jpg',   # 01 hook       window-silhouette  (person, first hook outing)
       'bg-h29.jpg',   # 02 ARCO       supercars-dusk     band luma 18.7
       'bg-h31.jpg',   # 03 Claude     lounge-night       band luma 19.7
       'bg-h88.jpg',   # 04 Supabase   supercars-dusk     band luma 28.2
       'bg-h22.jpg',   # 05 TestFlight lounge-day (night) band luma 53.5
       'bg-h24.jpg']   # 06 Sentry     lounge-night       band luma 49.8

BODY = {
 'Claude': [
    'Paste a mockup into Claude Code',
    'and ask it to build that screen.',
    '',
    'The UI you drew on friday is',
    'running on saturday morning.',
 ],
 'Supabase': [
    'Every table you create gets its',
    'own API endpoint, instantly.',
    '',
    'The backend is live before you',
    'write a single server file.',
 ],
 'TestFlight': [
    'Internal builds skip beta review',
    'and land minutes after upload.',
    '',
    'A sunday fix is on real phones',
    'the same evening.',
 ],
 'Sentry': [
    'Link the repo and it flags the',
    'suspect commit for each crash.',
    '',
    'The fix starts at the diff that',
    'broke it, not in a debugger.',
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
