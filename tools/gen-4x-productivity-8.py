#!/usr/bin/env python3
"""4x-productivity-8: eighth outing of the 4x hook, icon shelf, fresh roster.

"the tools i used to / 4x my productivity" (tools pillar). Third least
recently used of the four hooks hook_rules.eligible(pillar='tools')
returned on 2026-09-17: 4x-productivity-7, six posts back.

  roster    ARCO, Antigravity, ElevenLabs, Linear, Cloudflare. Antigravity
            is the LLM: third least recently used model (4x-productivity-7,
            which is the last outing of this same hook, but it carried the
            browser-testing point there and a different one here).
            ElevenLabs is content lane, Linear and Cloudflare build lane.
  teaching  every point checked against every caption in tools/hooks.json.
            Burned and avoided: Antigravity agent manager in parallel,
            browser click-through; ElevenLabs voice clone, dubbing; Linear
            cycles, branch-name linking, triage; Cloudflare tunnel.
            Fresh here: Antigravity's plan artifact you comment on before
            it codes, the ElevenLabs reader app reading a pdf or link
            aloud, Sentry crashes filing themselves into Linear, Cloudflare
            email routing on your own domain for free.
  ARCO      4x productivity is a how-the-day-runs question, THEME
            'planning'.
  photos    hook bg-h62 (desk-led-neon), next least recently used hook-only
            frame without a person after h53 and h59 went to the other two
            posts of this batch. App slides from non-hook-only vibes under
            BAND_MAX_LUMA, no adjacent vibe repeat, no person, nothing from
            pay-for-twelve, best-for-last-4 or study-four-hours-2.

Usage:
    python3 tools/gen-4x-productivity-8.py            # every slide
    python3 tools/gen-4x-productivity-8.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (app_slide, hook_slide, mark_hook_used, next_arco_angle,
                     preflight, record_post_bgs, record_post_tools)

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = '4x-productivity-8'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i used to', '4x my productivity']
PILLAR = 'tools'
THEME = 'planning'

TOOLS = ['ARCO', 'Antigravity', 'ElevenLabs', 'Linear', 'Cloudflare']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Antigravity', '3. ElevenLabs',
          '4. Linear', '5. Cloudflare']

HOOK_GRAD = (0.85, 0.40, 300, 1300)

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h62.jpg',   # 01 hook         desk-led-neon
       'bg-h39.jpg',   # 02 ARCO         supercars-dusk    band luma 35.8
       'bg-n06.jpg',   # 03 Antigravity  desk-empty-day    band luma 53.6
       'bg-h88.jpg',   # 04 ElevenLabs   supercars-dusk    band luma 28.2
       'bg-h52.jpg',   # 05 Linear       desk-city-day     band luma 62.6
       'bg-n03.jpg']   # 06 Cloudflare   villa-day         band luma 63.6

BODY = {
 'Antigravity': [
    'The agent writes its plan as a doc',
    'you comment on before it codes.',
    '',
    'A wrong assumption is fixed in a',
    'note, not in a finished diff.',
 ],
 'ElevenLabs': [
    'The reader app reads any pdf or',
    'link aloud in a voice you pick.',
    '',
    'A 30 page paper gets read on the',
    'walk instead of after it.',
 ],
 'Linear': [
    'Sentry crashes file themselves in',
    'Linear with the stack trace on.',
    '',
    'Bugs are in the backlog before',
    'anyone has reported them.',
 ],
 'Cloudflare': [
    'Email routing forwards any address',
    'on your domain to gmail, free.',
    '',
    'A hello@ address works the day',
    'the domain does, no mail plan.',
 ],
}


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    icons = json.load(open(c.TOOL_POOL))['icons']
    shelf = [icons[t] for t in TOOLS]

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
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', grad=HOOK_GRAD, icons=shelf)
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        body = next_arco_angle(THEME) if tool == 'ARCO' else BODY[tool]
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
