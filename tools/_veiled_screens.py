"""Screentime on real screens, over a veiled photograph.

The under-an-hour concept (hook photo, then ARCO screens in a handset with the
step beside each, then the icon card) put the handsets on a flat dark fade.
Thinh's note (2026-09-23): same concept, but on normal backgrounds with the
opacity turned down so only a little of the photo shows. The fade stays as
the base and the photo is laid over it at VEIL, so every slide keeps the
fade's legibility while no two slides look identical.
"""
import json
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from PIL import Image
import compose as c
import hook_rules
from compose import (hook_slide, phone_slide, cta_slide, linear_ground,
                     preflight, assert_teaches, mark_hook_used,
                     record_post_tools, record_post_bgs)

SHOTS = '/Users/thinh/Desktop/appstore screens'
SIM = 'Simulator Screenshot - iPhone 17 Pro - 2026-09-21 at'
SHIELD = ('Screenshot 2026-09-21 at 2.37.56.png', 40)
CONTROL = ('IMG_4283.PNG', 120)
BAD_HABITS = ('Screenshot 2026-09-21 at 2.35.22.png', 60)
PLAN_DAY = (f'{SIM} 02.48.07.png', 150)
GOOD_HABITS = (f'{SIM} 02.52.56.png', 150)
TODAY = (f'{SIM} 03.09.49.png', 150)

FADE = linear_ground((26, 28, 33), (9, 9, 11))
VEIL = 0.22          # ceiling on how much of the photograph shows through
VEIL_LUMA = 11       # the light a photo may add, so bright frames stay faint

STYLE = {'side': 'right', 'col_x': 72, 'col_w': 392, 'col_y': 665,
         'title_face': 'Semi Condensed Heavy', 'body_face': 'Semi Condensed Medium',
         'app_face': 'Semi Condensed Bold',
         'title_size': 62, 'body_size': 35, 'app_size': 28, 'lead': 1.05,
         'ink': (248, 248, 250), 'sub': (176, 176, 184),
         'eyebrow': (248, 248, 250)}


def veiled(bg):
    """The photo over the fade, held to the copy-band ceiling.

    A fixed opacity let a daylight villa show far more than a night lounge, so
    the alpha scales down with the photo's brightness: every frame adds about
    VEIL_LUMA of light, never more than VEIL of the picture.
    """
    photo = c.base_photo(bg, (1.0, 1.0, 0, 1))
    alpha = min(VEIL, VEIL_LUMA / max(1.0, c.band_luma(photo, 0, 1920)))
    im = Image.blend(FADE, photo, alpha)
    if c.band_luma(im, 600, 1300) > c.BAND_MAX_LUMA:
        raise SystemExit(f'{bg}: veiled ground too bright for the copy band')
    return im


def pick_bgs(topic, n, exclude=()):
    """gen-daily-batch.pick_bgs, with extra exclusions for a same-day sibling."""
    recent = [e for e in c.bg_history() if e['topic'] != topic][-c.BG_COOLDOWN:]
    recent_bgs = {b for e in recent for b in e['bgs']} | set(exclude)
    log = json.load(open(f'{c.SP}/hook_usage.json'))
    fresh = [b for b in sorted(c.VIBES)
             if b not in log and b not in recent_bgs and os.path.exists(f'{c.SP}/{b}')]
    if not fresh:
        sys.exit(f'{topic}: no hook background is both unused and outside the cooldown')
    hook = c.pick_hook_bg(prefer=fresh[0])
    used = recent_bgs | {hook}
    pool = [b for b in sorted(c.VIBES)
            if c.VIBES[b] not in c.HOOK_ONLY_VIBES and b not in used
            and os.path.exists(f'{c.SP}/{b}')]
    pool = [b for b in pool if c.copy_band_luma(b) <= c.BAND_MAX_LUMA]
    out, person = [], (hook in c.HAS_PERSON)
    last_vibe = c.VIBES.get(hook)
    for b in pool:
        if len(out) == n:
            break
        v = c.VIBES[b]
        if v == last_vibe:
            continue
        if b in c.HAS_PERSON:
            if person:
                continue
            person = True
        out.append(b)
        last_vibe = v
    if len(out) < n:
        sys.exit(f'{topic}: only {len(out)} backgrounds satisfy the guards')
    return [hook] + out


def build(topic, hook, bgs, slides, closer):
    """bgs: hook, one per screen, then the closing card's."""
    out = f'{c.REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    if len(bgs) != len(slides) + 2:
        raise SystemExit('need a background for the hook, each screen and the card')
    if not any(h['lines'] == hook for h in hook_rules.eligible(topic, 'screentime')):
        raise SystemExit(f'hook not eligible: {hook}')
    preflight(topic, ['ARCO'], bgs, pillar='screentime', hook=hook)
    for (_, _, title, body) in slides:
        assert_teaches(title, [body])

    hook_slide(bgs[0], hook, f'{out}/01.jpg')
    if not any(e.get('topic') == topic for e in hook_rules.history()):
        mark_hook_used(hook, topic)

    for i, (((src, crop), num, title, body), bg) in enumerate(zip(slides, bgs[1:-1]), 2):
        phone_slide(veiled(bg), f'{SHOTS}/{src}', crop, num, title, body,
                    f'{out}/{i:02d}.jpg', style=STYLE)

    cta_slide(None, f'{out}/{len(slides) + 2:02d}.jpg', subtitle=closer,
              badge=True, card=veiled(bgs[-1]),
              style={'icon': 240, 'box': (96, 984, 520, 1400), 'name_size': 62,
                     'ink': (248, 248, 250), 'sub': (176, 176, 184)})

    if not any(e.get('topic') == topic for e in c.tool_history()):
        record_post_tools(topic, ['ARCO'])
    record_post_bgs(topic, bgs)
