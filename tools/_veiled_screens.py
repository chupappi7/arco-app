"""Screentime on real screens, over a veiled photograph.

The under-an-hour concept (hook photo, then ARCO screens in a handset with the
step beside each, then the icon card) put the handsets on a flat dark fade.
Thinh's note (2026-09-23): same concept, but on normal backgrounds with the
opacity turned down so only a little of the photo shows. The fade stays as
the base and the photo is laid over it at VEIL, so every slide keeps the
fade's legibility while no two slides look identical.

Thinh's note on schedule-not-personality (2026-09-23), for every post built
from here on: end the hook with "here is why" (`kicker`), and ring the card's
icon and App Store badge in a thin white outline (`CARD_OUTLINE`). Both are
opt-in so the posts already out rebuild unchanged.
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

# The current app, captured 4-7 Oct against 2.1.2, kept in the repo rather
# than on a desktop so a post cannot quietly ship a build nobody runs any
# more. Every screenshot above this line is from 21 September, and one post
# reached back to an August capture and went out showing a plan screen dated
# "Sat 22 Aug" -- which is how it came to be rejected. Prefer these.
NOW = '/Users/thinh/SIXSIX/design/control-center/appstore/assets'
# (file, crop_top). The 1320x2868 captures are 0.4602 wide-to-tall and the
# handset's glass is 0.4600, so they already fill it: crop_top stays 0 or the
# screenshot zooms and its top row slides under the drawn dynamic island --
# which is what blacked out the "Today . ARCO" header at 165. The two older
# 1206x2622 shots keep 150, which clears their status bar.
#
# Only scr-today, screen-shield and screen-insights are pages inside the app.
# The rest are HOME screens carrying ARCO widgets, and copy that calls them
# app screens is describing something the slide does not show.
WIDGETS = (f'{NOW}/screen-widgets.png', 0)      # home: habit, timer, gym
TODAY_NOW = (f'{NOW}/scr-today.png', 0)         # in-app Today, 7 Oct
TIMELINE = (f'{NOW}/scr-timeline.png', 0)       # home: today's-timeline widget
TASKS = (f'{NOW}/scr-tasks.png', 0)             # home: tasks widget
HABITS = (f'{NOW}/scr-habits.png', 0)           # a second take of WIDGETS
SHIELD_NOW = (f'{NOW}/screen-shield.png', 150)  # in-app shield
INSIGHTS_NOW = (f'{NOW}/screen-insights.png', 150)   # in-app Insights

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

KICKER = 'here is why'

# Thinh, 2026-11-02: "make some ctas with comment setup or app to get the app
# or for promo code". The screens posts close on the icon card, and until now
# the card only described the app. These are the three closers a post can
# pick, kept here so the choice is a named constant and analytics can tell
# which card a post shipped with.
#
# CTA_COMMENT gates the setup the slides just showed: it is the one thing a
# comment gets you that searching the store does not, and the comment wall
# fills with the brand name rather than with "app". CTA_STORE is the plain
# search term for a post that has already asked for enough. A promo code
# needs an offer code minted in App Store Connect first, so there is no
# constant for one here yet.
CTA_COMMENT = ['Comment \u201cARCO\u201d and I\u2019ll send my setup.',
               'Search \u201carco focus\u201d on the App Store.']
CTA_STORE = ['Search \u201carco focus\u201d', 'on the App Store.']
CARD_OUTLINE = {'icon_outline': 3, 'badge_outline': 3}

# Design variants of the step slide, 2026-10-17. The posted look is
# 'control'; the other two came out of tools/screens_lab.py and are being
# tried on live posts to see whether either beats it. A generator names one
# and nothing else about it changes, so the comparison is design-only.
DESIGNS = {
    'control': {},
    # The screenshot is the argument, so give it the frame: no photograph,
    # copy in a full-width band, handset centred underneath and stacked so a
    # three-line body pushes it down rather than through it.
    'big-screen': {'phone_w': 660, 'phone_y': 450, 'phone_x': 210,
                   'stack': 64, 'col_x': 72, 'col_w': 936, 'col_y': 140,
                   'title_size': 74, 'body_size': 40, 'app_size': 30,
                   'ground': 'flat'},
    # Mirrors the posted layout. Costs nothing and breaks the sameness of a
    # set where every slide puts the device on the same side.
    'left-rail': {'side': 'left', 'col_x': 616, 'col_w': 400, 'col_y': 540,
                  'title_size': 58, 'body_size': 34},
    # Thinh, 2026-11-02: "make it more clean there are too many two row
    # sentences". Beside the handset the column is 392px, which is about 25
    # characters -- every sentence straddled a row however short it was
    # written. Here the copy is a full-width band above the device, 936px or
    # roughly 58 characters, and `sentence_lines` gives each sentence a row
    # of its own. The handset is 500 rather than big-screen's 660 so its
    # bottom lands at 1564, clear of the floor TikTok's caption sits on;
    # big-screen puts it at 1885, under the caption.
    'wide-band': {'phone_w': 500, 'phone_x': 290, 'phone_y': 450, 'stack': 72,
                  'col_x': 72, 'col_w': 936, 'col_y': 140,
                  'title_size': 74, 'body_size': 40, 'app_size': 30,
                  'sentence_lines': True, 'ground': 'flat'},
}

STYLE = {'side': 'right', 'col_x': 72, 'col_w': 392, 'col_y': 665,
         'title_face': 'Semi Condensed Heavy', 'body_face': 'Semi Condensed Medium',
         'app_face': 'Semi Condensed Bold',
         'title_size': 62, 'body_size': 35, 'app_size': 28, 'lead': 1.05,
         'ink': (248, 248, 250), 'sub': (176, 176, 184),
         'eyebrow': (248, 248, 250)}


FLAT = linear_ground((20, 21, 25), (8, 8, 10))

# The wide band on a photograph rather than the flat ground: what the closing
# slide of a photo listicle uses, so it keeps the look of the six slides
# before it and still gets a column wide enough to hold a whole sentence.
WIDE = {k: v for k, v in {**STYLE, **DESIGNS['wide-band']}.items()
        if k != 'ground'}


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


def build(topic, hook, bgs, slides, closer, pillar='screentime', kicker=None,
          card_style=None, only=None, promo=None, design='control',
          hook_accent=None):
    """bgs: hook, one per screen, then the closing card's. `pillar` is the
    hook's own tag; discipline posts use the same screens. `kicker` is the
    line under the hook, `card_style` extends the closing card's style,
    `promo` puts bold call-to-action lines on the card.
    `only` (slide numbers) re-renders just those slides and leaves the rest,
    and the hook and background histories, untouched. `design` names a key of
    DESIGNS, `hook_accent` recolours the hook's second line."""
    if design not in DESIGNS:
        raise SystemExit('unknown design %r, have %s'
                         % (design, ', '.join(DESIGNS)))
    over = dict(DESIGNS[design])
    flat_ground = over.pop('ground', None) == 'flat'
    style = {**STYLE, **over}
    out = f'{c.REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    if len(bgs) != len(slides) + 2:
        raise SystemExit('need a background for the hook, each screen and the card')
    if not any(h['lines'] == hook for h in hook_rules.eligible(topic, pillar)):
        raise SystemExit(f'hook not eligible: {hook}')
    preflight(topic, ['ARCO'], bgs, pillar=pillar, hook=hook)
    for (_, _, title, body) in slides:
        assert_teaches(title, [body])

    want = (lambda n: only is None or n in only)
    if want(1):
        hook_slide(bgs[0], hook, f'{out}/01.jpg', kicker=kicker,
                   **({'accent': hook_accent} if hook_accent else {}))
    if only is None and not any(e.get('topic') == topic for e in hook_rules.history()):
        mark_hook_used(hook, topic)

    for i, (((src, crop), num, title, body), bg) in enumerate(zip(slides, bgs[1:-1]), 2):
        if not want(i):
            continue
        # A name from the current set is already an absolute path; only the
        # older desktop captures need SHOTS joined on.
        shot = src if os.path.isabs(src) else f'{SHOTS}/{src}'
        phone_slide(FLAT.copy() if flat_ground else veiled(bg),
                    shot, crop, num, title, body,
                    f'{out}/{i:02d}.jpg', style=style)

    if want(len(slides) + 2):
        cta_slide(None, f'{out}/{len(slides) + 2:02d}.jpg', subtitle=closer,
                  promo=promo, badge=True, card=veiled(bgs[-1]),
                  style={'icon': 240, 'box': (96, 984, 520, 1400), 'name_size': 62,
                         'ink': (248, 248, 250), 'sub': (176, 176, 184),
                         **(card_style or {})})

    if only is not None:
        return
    if not any(e.get('topic') == topic for e in c.tool_history()):
        record_post_tools(topic, ['ARCO'])
    record_post_bgs(topic, bgs)
    record_design(topic, design)


def record_design(topic, design):
    """Write which design this post was built with into post_status.json.

    The design was a keyword argument and nothing else: it changed the pixels
    and left no trace, so two posts built to compare two designs were
    indistinguishable from the other 400 by the time their numbers arrived.
    Analytics reads this field; without it the comparison cannot be made at
    all, only remembered.
    """
    path = f'{c.REPO}/tools/post_status.json'
    try:
        with open(path) as fh:
            st = json.load(fh)
    except Exception:
        st = {}
    st.setdefault(topic, {})['design'] = design
    tmp = f'{path}.tmp{os.getpid()}'
    with open(tmp, 'w') as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
