#!/usr/bin/env python3
"""work-by-noon-3: re-shoot of work-by-noon. Same words, new photos.

This is gen-work-by-noon.py with two things changed and nothing else: the
topic slug and the six backgrounds. Every hook line, card title, body line
and the caption registered in hooks.json come straight from the source post,
byte for byte, so the only difference a viewer sees is the photography.

The slug is -3, not -2. work-by-noon-2 is already a live post: it was
delivered to all three accounts and carries stats (199 views on vn), so
rebuilding onto that folder would overwrite a published carousel.

Two literals had to be frozen rather than left as calls, because both of the
source's calls return something different today:

  - The ARCO card was next_arco_angle() with no theme, which handed the
    source v4. The used-list has moved on since, so the same call now returns
    v9 and the caption in hooks.json -- which describes v4 -- would stop
    matching the slide. v4 is written out literally; it was read back off
    drafts/work-by-noon/02.jpg to be sure which angle shipped.
  - pick_bgs() is replaced by the frozen BGS list below, picked with the same
    walk and then written down so a rebuild reproduces this post rather than
    a third set of photos. Its grad_for() helper stays, because the gradient
    is a function of the background and the backgrounds changed.

How BGS was picked -- the gen-daily-batch walk, unchanged: hook-only vibes
skipped on app slides, every candidate's copy band measured with
copy_band_luma and dropped above BAND_MAX_LUMA, no two adjacent slides
sharing a vibe, at most one background with a person, and nothing
assert_bg_fresh rejects. On top of the guards, SOURCE_BGS is excluded: the
six photographs work-by-noon itself was shot on, because a re-shoot that
reuses the source's own frames is not a re-shoot.

Two things the walk does not decide on its own, both settled by rendering
the post and reading all six slides back.

The exclusion window is the one post BG_COOLDOWN asks for, not the widened
two. Widening it was the first attempt and it cost the walk five frames (16
clear the gate at one post, 11 at two) and, worse, four of the seven vibes:
what was left was five supercars-dusk and four desk-city-day, so the walk
came back with bg-h29, bg-h37 and bg-h39 on slides 2, 4 and 6. All three are
the same dark villa with a white supercar on the left and a dark one on the
right; the vibe guard passes them because none are adjacent, and the
carousel still read as one photograph printed three times. It also had to
reach for bg-h49, whose copy band lands across three lit monitors.

So the set takes one frame per vibe rather than the darkest five, which is
what actually stops a carousel reading as one scene. Five vibes, five
places: a night lounge, a villa forecourt at dusk, a man at a window, a
daylight lounge, an empty desk. bg-h31, bg-h32 and bg-h22 were in ten-x-3,
which BG_COOLDOWN allows -- keep-five-2 sits between it and this post -- and
that is the trade this pool forces at seven usable vibes. Reusing nothing
from ten-x-3 is possible but only at 54-66 band luma on four of the five
slides, which buys freshness with legibility.

The order is not the source's darkest-first. bg-h29 measures darkest at 18.7
and would take slide 2, but slide 2 is the ARCO card and bg-h29 is another
dark villa with the same two supercars work-by-noon's own ARCO card was shot
on. On a re-shoot the first card after the hook is the one that has to look
different, so bg-h31 (19.7, a point brighter and a different room) takes it
and bg-h29 moves to slide 3.

The hook background is claimed by hand. pick_hook_bg narrows its candidates
to the unused hook-only vibes whenever any exist and then silently ignores
`prefer`, so calling it through pick_bgs logs a background this post never
renders. bg-h73 is the first unused desk-led-neon and is exactly what it
would have returned.

The hook is reused on purpose, and both hook guards still run: it is in
hook_pool.json and hook_rules.status() clears it -- its last outing was
work-by-noon itself, well past HOOK_COOLDOWN. mark_hook_used records this
outing under the new topic so the cooldown counts the repeat.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)

REPO = '/Users/thinh/SIXSIX/arco-app'
LUMA = {}          # bg -> copy_band_luma, measured once (each call re-renders)


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


TOPIC = 'work-by-noon-3'
HOOK = ['the tools i use to do', 'a full day of work by noon']
TOOLS = ['ARCO', 'Manus', 'n8n', 'Cloudflare', 'Vercel']
ICONS = [None, 'icon-manus.png', 'icon-n8n.png', 'icon-cloudflare.png',
         'icon-vercel.png']

BGS = ['bg-h73.jpg',   # 01 hook        desk-led-neon      first outing, hook-only vibe
       'bg-h31.jpg',   # 02 ARCO        lounge-night       band luma 19.7
       'bg-h29.jpg',   # 03 Manus       supercars-dusk     band luma 18.7
       'bg-h32.jpg',   # 04 n8n         window-silhouette  band luma 38.8, the one person
       'bg-h22.jpg',   # 05 Cloudflare  lounge-day         band luma 53.5
       'bg-n06.jpg']   # 06 Vercel      desk-empty-day     band luma 53.6

# The six photographs the source post was shot on. Excluded from the walk.
SOURCE_BGS = ['bg-h30.jpg', 'bg-h38.jpg', 'bg-n04.jpg',
              'bg-h46.jpg', 'bg-n03.jpg', 'bg-h51.jpg']

BODY = [
    # next_arco_angle() -> v4 on the source build, frozen so a rebuild cannot
    # hand this post copy the registered caption does not describe.
    ['All my tasks live here and I plan the',
     'whole day in 30 seconds.',
     '',
     'Focus mode puts every distraction',
     'away.',
     '',
     'My holy grail.'],
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
preflight(TOPIC, TOOLS, BGS, pillar='tools', hook=HOOK)

# Claim the hook background by hand: see the note above on pick_hook_bg.
log = json.load(open(f'{c.SP}/hook_usage.json'))
if BGS[0] not in log:
    json.dump(log + [BGS[0]], open(f'{c.SP}/hook_usage.json', 'w'), indent=1)

hook_slide(BGS[0], HOOK, f'{out}/01.jpg')
mark_hook_used(HOOK, TOPIC)

for i, (tool, icon, body) in enumerate(zip(TOOLS, ICONS, BODY)):
    n = i + 1
    if tool == 'ARCO':
        app_slide(BGS[n], 'icon-arco.png', '1. ARCO', body,
                  f'{out}/{n+1:02d}.jpg', grad=grad_for(BGS[n]))
    else:
        app_slide(BGS[n], icon, f'{n}. {tool}', body, f'{out}/{n+1:02d}.jpg',
                  grad=grad_for(BGS[n]))

record_post_tools(TOPIC, TOOLS)
record_post_bgs(TOPIC, BGS)
print(f"\n  {TOPIC}  {' / '.join(HOOK)}  |  {', '.join(TOOLS)}")
print(f"  bgs: {', '.join(BGS)}")
