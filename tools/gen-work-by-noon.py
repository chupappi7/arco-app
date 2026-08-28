#!/usr/bin/env python3
"""work-by-noon: tools pillar, ARCO leading, one LLM (Manus).

Hook comes from tools/hook_pool.json and is marked used here. Backgrounds are
picked by the guards, not by hand, using the same rule as gen-daily-batch:
hook slide gets a photo nobody has seen, app slides skip the hook-only vibes,
anything whose copy band stays brighter than BAND_MAX_LUMA is dropped, no two
adjacent slides share a vibe, at most one person in the whole carousel.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     mark_hook_used, record_post_tools, record_post_bgs,
                     pick_hook_bg)

REPO = '/Users/thinh/SIXSIX/arco-app'
LUMA = {}          # bg -> copy_band_luma, measured once (each call re-renders)

# compose.py says only caption-free photos are left in the pool, but this one
# still carries the scar of the removal: a column of vertical smears with hard
# edges sits in the upper third, right where the icon and title go. It measures
# as the darkest background available, so a darkest-first picker reaches for it
# first and puts the artefact on the ARCO slide. Retire it here until the file
# is replaced or moved to bg/_captioned_retired/ like the rest of the src-* set.
SCARRED = {'src-cars-clean.jpg'}


def grad_for(bg):
    """Gradient for an app slide, chosen from how bright the copy band is.

    adaptive_scrim aims for a band luma of 96 but caps its strength at 0.55,
    so on a daylight photo it runs out of room and the copy ends up sitting
    on a bright sky or a lit monitor. The luma gate lets those through
    because it measures the mean and a dark chair pulls the average down.
    Pushing the gradient itself down first gives the scrim something to work
    with; dark photos keep the default and stay readable as photographs.
    """
    luma = LUMA.get(bg)
    if luma is None:
        luma = LUMA[bg] = c.copy_band_luma(bg)
    if luma >= 55:
        return (0.58, 0.40, 300, 1250)
    if luma >= 35:
        return (0.72, 0.55, 300, 1250)
    return (0.85, 0.68, 300, 1250)


def pick_bgs(topic, n=5):
    recent = [e for e in c.bg_history() if e['topic'] != topic][-c.BG_COOLDOWN:]
    rb = {b for e in recent for b in e['bgs']}
    log = json.load(open(f'{c.SP}/hook_usage.json'))
    fresh = [b for b in sorted(c.VIBES) if b not in log and b not in rb
             and os.path.exists(f'{c.SP}/{b}')]
    if not fresh:
        sys.exit(f'{topic}: no hook background is both unused and outside the cooldown')
    hook = pick_hook_bg(prefer=fresh[0])
    used = rb | {hook}
    pool = [b for b in sorted(c.VIBES)
            if c.VIBES[b] not in c.HOOK_ONLY_VIBES and b not in used
            and b not in SCARRED
            and os.path.exists(f'{c.SP}/{b}')]
    for b in pool:
        LUMA[b] = c.copy_band_luma(b)
    pool = [b for b in pool if LUMA[b] <= c.BAND_MAX_LUMA]
    # Darkest first, skipping anything that repeats the previous vibe.
    # Walking the sorted-by-filename pool hits a dead end here (the survivors
    # are three single-vibe clusters, so it takes one from each and then
    # skips every sibling) and it also spends the bright end of the pool
    # first. Ordering by measured band luma puts the photos that hold white
    # copy best on the slides, and the vibe check still stops two adjacent
    # slides looking like one long card.
    ranked = sorted(pool, key=lambda b: (LUMA[b], b))
    out, person, last = [], hook in c.HAS_PERSON, c.VIBES.get(hook)
    while len(out) < n:
        for b in ranked:
            if b in out or c.VIBES[b] == last:
                continue
            if b in c.HAS_PERSON:
                if person:
                    continue
                person = True
            out.append(b)
            last = c.VIBES[b]
            break
        else:
            break
    return [hook] + out


TOPIC = 'work-by-noon'
HOOK = ['the tools i use to do', 'a full day of work by noon']
TOOLS = ['ARCO', 'Manus', 'n8n', 'Cloudflare', 'Vercel']
ICONS = [None, 'icon-manus.png', 'icon-n8n.png', 'icon-cloudflare.png',
         'icon-vercel.png']
BODY = [
    None,
    ['Tasks run on its own cloud machine',
     'and keep going after you close the tab.',
     '',
     'You hand off the long job and come',
     'back to a finished file.'],
    ['You can host it yourself, so a workflow',
     'reaches local files and private APIs.',
     '',
     'The automation a cloud tool cannot',
     'touch runs on your own machine.'],
    ['A tunnel puts your local server on a',
     'public https url with no port opened.',
     '',
     'You send someone the link while the',
     'site still runs on your laptop.'],
    ['Any past deployment can be promoted',
     'back to production in one click.',
     '',
     'A bad release is undone in seconds,',
     'not rebuilt and shipped again.'],
]

out = f'{REPO}/drafts/{TOPIC}'
os.makedirs(out, exist_ok=True)
bgs = pick_bgs(TOPIC)
preflight(TOPIC, TOOLS, bgs)

hook_slide(bgs[0], HOOK, f'{out}/01.jpg')
mark_hook_used(HOOK)

for i, (tool, icon, body) in enumerate(zip(TOOLS, ICONS, BODY)):
    n = i + 1
    if tool == 'ARCO':
        app_slide(bgs[n], 'icon-arco.png', '1. ARCO', next_arco_angle(),
                  f'{out}/{n+1:02d}.jpg', grad=grad_for(bgs[n]))
    else:
        app_slide(bgs[n], icon, f'{n}. {tool}', body, f'{out}/{n+1:02d}.jpg',
                  grad=grad_for(bgs[n]))

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, bgs)
print(f"\n  {TOPIC}  {' / '.join(HOOK)}  |  {', '.join(TOOLS)}")
print(f"  bgs: {', '.join(bgs)}")
