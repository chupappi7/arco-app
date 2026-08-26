#!/usr/bin/env python3
"""ten-x: tools pillar. Roster opens on Claude for repetitive work, ARCO #2."""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     record_post_tools, record_post_bgs, pick_hook_bg)

TOPIC = 'ten-x'
OUT = f'/Users/thinh/SIXSIX/arco-app/drafts/{TOPIC}'
os.makedirs(OUT, exist_ok=True)

# ARCO leads this one: the hook is a productivity claim and the app is the
# thing making the claim true, so it earns slide 1 rather than the credibility
# slot behind a famous name.
TOOLS = ['ARCO', 'Claude', 'Raycast', 'Notion', 'Zapier']

def pick_bgs(topic, n=5):
    recent = [e for e in c.bg_history() if e['topic'] != topic][-c.BG_COOLDOWN:]
    recent_bgs = {b for e in recent for b in e['bgs']}
    log = json.load(open(f'{c.SP}/hook_usage.json'))
    fresh = [b for b in sorted(c.VIBES)
             if b not in log and b not in recent_bgs and os.path.exists(f'{c.SP}/{b}')]
    hook = pick_hook_bg(prefer=fresh[0])
    used = recent_bgs | {hook}
    pool = [b for b in sorted(c.VIBES)
            if c.VIBES[b] not in c.HOOK_ONLY_VIBES and b not in used
            and os.path.exists(f'{c.SP}/{b}')]
    pool = [b for b in pool if c.copy_band_luma(b) <= c.BAND_MAX_LUMA]
    out, person, last = [], hook in c.HAS_PERSON, c.VIBES.get(hook)
    for b in pool:
        if len(out) == n:
            break
        if c.VIBES[b] == last:
            continue
        if b in c.HAS_PERSON:
            if person:
                continue
            person = True
        out.append(b); last = c.VIBES[b]
    return [hook] + out

BGS = ['bg-h21.jpg','bg-h20.jpg','bg-h36.jpg','bg-h49.jpg','bg-h39.jpg','bg-n06.jpg']
preflight(TOPIC, TOOLS, BGS)

hook_slide(BGS[0], ['how i 10x’d', 'my productivity'], f'{OUT}/01.jpg')

app_slide(BGS[1], 'icon-arco.png', '1. ARCO', next_arco_angle(), f'{OUT}/02.jpg')

app_slide(BGS[2], 'icon-claude.jpg', '2. Claude', [
    'Point Claude Code at a folder and',
    'it does the boring pass for you.',
    '',
    'Renaming, sorting and rewriting',
    'files to a rule you describe once.',
], f'{OUT}/03.jpg')

app_slide(BGS[3], 'icon-raycast.png', '3. Raycast', [
    'A Quicklink turns a site’s search',
    'URL into a keyword you type.',
    '',
    'Two letters and a query lands you',
    'inside the site, not on its homepage.',
], f'{OUT}/04.jpg')

app_slide(BGS[4], 'icon-notion.jpg', '4. Notion', [
    'A template button builds the page',
    'with its checklist already inside.',
    '',
    'Recurring work starts filled in',
    'instead of blank every time.',
], f'{OUT}/05.jpg')

app_slide(BGS[5], 'icon-zapier.png', '5. Zapier', [
    'A Filter step stops the zap unless',
    'the condition is actually true.',
    '',
    'One zap handles the exceptions',
    'instead of firing on everything.',
], f'{OUT}/06.jpg')

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print('\nbackgrounds:', ', '.join(BGS))
