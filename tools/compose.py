YELLOW = (255, 214, 10)
WHITE = (255, 255, 255)
#!/usr/bin/env python3
"""Slide-composition helpers for the TikTok pipeline (see the tiktok-pipeline skill).
Backgrounds in tools/slides/bg (BANDS maps caption zones needing inpainting;
bg-dNN.jpg files are clean). Icons in tools/slides/icons."""
import os
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SF = '/System/Library/Fonts/SFNS.ttf'
SP = '/Users/thinh/SIXSIX/arco-app/tools/slides/bg'      # backgrounds
ICONS = '/Users/thinh/SIXSIX/arco-app/tools/slides/icons'  # app icons
REPO = '/Users/thinh/SIXSIX/arco-app'
SHOTS = '/Users/thinh/SIXSIX/screenshots'

def font(size, variation):
    f = ImageFont.truetype(SF, size)
    f.set_variation_by_name(variation)
    return f

def near_white(px, t=150, spread=80):
    r, g, b = px[:3]
    return r > t and g > t and b > t and (max(px[:3]) - min(px[:3])) < spread

def inpaint_band(im, y_lo, y_hi, x_lo=40, x_hi=1040):
    region = im.crop((x_lo, y_lo, x_hi, y_hi))
    w, h = region.size
    mask = Image.new('L', (w, h), 0)
    mp = mask.load()
    rp = region.load()
    for y in range(h):
        for x in range(w):
            if near_white(rp[x, y]):
                mp[x, y] = 255
    mask = mask.filter(ImageFilter.MaxFilter(13))
    mp = mask.load()
    for x in range(w):
        y = 0
        while y < h:
            if mp[x, y]:
                s = y
                while y < h and mp[x, y]:
                    y += 1
                e = y
                top = rp[x, s - 1] if s > 0 else (rp[x, e] if e < h else (0, 0, 0))
                bot = rp[x, e] if e < h else top
                n = e - s + 1
                for i in range(s, e):
                    t = (i - s + 1) / n
                    rp[x, i] = tuple(int(top[c] + (bot[c] - top[c]) * t) for c in range(3))
            else:
                y += 1
    soft = region.filter(ImageFilter.GaussianBlur(6))
    blend = mask.filter(ImageFilter.GaussianBlur(3))
    region.paste(soft, (0, 0), blend)
    im.paste(region, (x_lo, y_lo))

def smoothstep(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    t = (x - a) / (b - a)
    return t * t * (3 - 2 * t)

def gradient_darken(im, f_top, f_bot, ramp_a, ramp_b):
    h = im.height
    alpha = Image.new('L', (1, h))
    ap = alpha.load()
    for y in range(h):
        f = f_top + (f_bot - f_top) * smoothstep(ramp_a, ramp_b, y)
        ap[0, y] = int(255 * (1 - f))
    alpha = alpha.resize(im.size)
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0), alpha)

def rounded_icon(path, size=210, radius=48):
    ic = Image.open(path).convert('RGB').resize((size, size), Image.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return ic, mask

def fit_font(text, variation, start, max_width=860, floor=44):
    size = start
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    while size > floor:
        f = font(size, variation)
        if probe.textlength(text, font=f) <= max_width:
            return f
        size -= 2
    return font(floor, variation)

def draw_text_block(im, items, shadow_alpha=170):
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for x, y, txt, f, anchor, fill in items:
        sd.text((x, y + 3), txt, font=f, fill=(0, 0, 0, shadow_alpha), anchor=anchor)
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0), shadow.split()[3])
    d = ImageDraw.Draw(im)
    for x, y, txt, f, anchor, fill in items:
        d.text((x, y), txt, font=f, fill=fill, anchor=anchor)

# Only clean, caption-free photos remain in the pool. The old src-*.jpg set
# had marketing text baked in; removing it with inpaint_band flattens a wide
# strip right above the copy, which is what produced "text on dead black".
# Those files are retired under bg/_captioned_retired/ rather than patched.
BANDS = {
    'src-cars-clean.jpg': (0, 1),
    **{f'bg-n{i:02d}.jpg': (0, 1) for i in range(1, 11)},
    **{f'bg-h{i:02d}.jpg': (0, 1) for i in range(1, 91) if i != 23},
}

# Backgrounds must be true 1080x1920. The bg-dNN pool was built by upscaling
# small desktop images 3x-6.7x and reads visibly soft on a phone screen; it is
# retired from full-bleed use. Anything below MIN_BG_PX of real pixels raises.
MIN_BG_PX = (1000, 1700)

# Backgrounds containing a person. At most ONE of these may appear in a
# single post: two photos of a man at a desk in one carousel reads as stock
# imagery. `assert_one_person(list_of_bgs)` enforces it at build time.
import json as _json
import hook_rules
try:
    HAS_PERSON = set(_json.load(open(f'{SP}/manifest.json'))['has_person'])
except Exception:
    HAS_PERSON = set()


try:
    VIBES = _json.load(open(f'{SP}/manifest.json'))['vibes']
    # A background the user removed from the pool must never come back, even
    # if its file lingers. Only files actually present count.
    VIBES = {k: v for k, v in VIBES.items() if os.path.exists(f'{SP}/{k}')}
except Exception:
    VIBES = {}


def assert_one_person(bgs):
    """Raise if a post uses more than one person-containing background."""
    used = [b for b in bgs if b in HAS_PERSON]
    if len(used) > 1:
        raise SystemExit(
            f'post uses {len(used)} backgrounds with a person ({", ".join(used)}); '
            'at most one is allowed')
    return True


HOOK_LOG = f'{SP}/hook_usage.json'
TOOL_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tool_usage.json')
# Off. Reusing a tool is fine: the audience is not reading every post, and a
# stack that changes completely each time reads as made up. What actually
# annoyed people was the same five names in the same order, which the format
# rotation and fresh teaching points handle. Set above 0 to switch it back on.
TOOL_COOLDOWN = 0          # posts a tool must sit out before it can return


def tool_history():
    try:
        return _json.load(open(TOOL_LOG))
    except Exception:
        return []


def tools_on_cooldown():
    """Tools used in the last TOOL_COOLDOWN posts — do not use these."""
    if TOOL_COOLDOWN <= 0:
        return set()
    recent = tool_history()[-TOOL_COOLDOWN:]
    return {t for post in recent for t in post['tools']}


def record_post_tools(topic, tools):
    h = tool_history()
    h.append({'topic': topic, 'tools': tools})
    _json.dump(h, open(TOOL_LOG, 'w'), indent=1)


# ARCO is the deliberate constant: it appears in every listicle at #2 and is
# exempt from the cooldown. Everything AROUND it must be new — a feed where
# Claude, Codex and ClickUp show up every time teaches nothing after the
# first post, and that is what costs followers.
ALWAYS_ALLOWED = {'ARCO', 'ARCO: Day Planner & Focus'}

ARCO_ANGLES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'arco_angles.json')


def next_arco_angle(theme=None):
    """Return ARCO body copy that answers the hook, cycling within that theme.

    Rotating blindly is how a study hook about not touching your phone got a
    slide that opens on planning the day in 30 seconds. The app slide has to
    answer the same question the hook asked, so pass the hook's theme
    (focus, study, screentime, discipline, planning, build, business,
    insights) and the copy is drawn from angles tagged for it.

    ARCO appears in every listicle, which makes its slide the most repeated
    text in the feed. Rotating the angle means a returning viewer learns a
    different feature each time instead of rereading the same three lines.
    """
    d = _json.load(open(ARCO_ANGLES))
    pool = d['angles']
    if theme:
        matching = [a for a in pool if theme in a.get('themes', [])]
        if matching:
            pool = matching
        else:
            raise SystemExit(
                f'no ARCO angle for theme "{theme}". Add one to arco_angles.json '
                'rather than shipping copy that answers a different question.')
    unused = [a for a in pool if a['id'] not in d['used']]
    if not unused:
        d['used'] = [x for x in d['used'] if x not in {a['id'] for a in pool}]
        unused = pool
    pick = unused[0]
    d['used'].append(pick['id'])
    _json.dump(d, open(ARCO_ANGLES, 'w'), indent=1)
    return pick['lines']


# Exactly one LLM per post, never zero and never two. Zero reads as a post
# that missed the thing everyone is actually curious about; two is the same
# slide twice, because nobody can tell two models apart from a one line
# description. Which model appears rotates between posts.
LLMS = {
    'Claude', 'Codex', 'ChatGPT', 'Gemini', 'Perplexity', 'Manus',
    'Antigravity', 'Cursor', 'Copilot', 'Grok', 'DeepSeek', 'v0', 'Lovable',
}


def assert_one_llm(tools):
    """Raise unless a post names exactly one LLM or AI coding agent."""
    used = [t for t in tools if t in LLMS]
    if len(used) > 1:
        raise SystemExit(
            f'{len(used)} LLMs in one post: {", ".join(used)}. '
            'Pick one; the second is the same slide twice.')
    if not used:
        raise SystemExit(
            'no LLM in this post. Every post carries exactly one; rotate '
            f'which: {", ".join(sorted(LLMS))}.')
    return True


def assert_fresh_tools(tools, allow=()):
    """Raise if a post reuses a non-ARCO tool that is still on cooldown."""
    hot = tools_on_cooldown() - set(allow) - ALWAYS_ALLOWED
    clash = [t for t in tools if t in hot]
    if clash:
        raise SystemExit(
            f'tools used within the last {TOOL_COOLDOWN} posts: {", ".join(clash)}. '
            'Pick different ones; the audience follows to learn.')
    return True



def pick_hook_bg(prefer=None):
    """Return a background not yet used on a hook slide.

    The hook is the slide that decides the scroll, so it must never look
    familiar. Usage is tracked in bg/hook_usage.json; every background is
    used once before any repeats, and when the pool is exhausted the log
    resets and the least-recently-used comes back first.
    """
    import os
    pool = sorted(b for b in VIBES if os.path.exists(f'{SP}/{b}'))
    try:
        used = _json.load(open(HOOK_LOG))
    except Exception:
        used = []
    unused = [b for b in pool if b not in used]
    # Night desk setups are the strongest images in the pool and read as
    # "someone's actual setup", which is the note the first slide wants. They
    # are barred from app slides, so the hook is the only place they can go.
    preferred = [b for b in unused if VIBES.get(b) in HOOK_ONLY_VIBES]
    if preferred:
        unused = preferred
    if not unused:                      # full cycle done: start over
        used, unused = [], pool
    if prefer and prefer in unused:
        choice = prefer
    else:
        choice = unused[0]
    used.append(choice)
    _json.dump(used, open(HOOK_LOG, 'w'), indent=1)
    return choice


def hook_bg_status():
    import os
    pool = sorted(b for b in VIBES if os.path.exists(f'{SP}/{b}'))
    try:
        used = _json.load(open(HOOK_LOG))
    except Exception:
        used = []
    return len(used), len(pool)


# Night desk setups with monitors are HOOK ONLY. They are the strongest
# images in the pool and they read as "someone's actual setup", which is
# exactly the note the first slide needs. Behind five lines of body copy the
# monitors and LED strips fight the text instead, and a carousel of them looks
# like one long slide. Use them at index 0 and nowhere else.
HOOK_ONLY_VIBES = {'desk-led-neon', 'desk-led-warm', 'desk-person-night',
                   'desk-lamp-night',
                   # jet-mountain passes the luma gate (the sky is dark) but
                   # the copy lands across bright snow and a dark suit, so the
                   # dashes and thin strokes break up. Hook only.
                   'jet-mountain'}


def assert_bg_roles(bgs):
    """Raise if a hook-only background is used on anything but the hook."""
    bad = [(i, b, VIBES.get(b)) for i, b in enumerate(bgs)
           if i > 0 and VIBES.get(b) in HOOK_ONLY_VIBES]
    if bad:
        detail = '; '.join(f'slide {i+1} uses {b} ({v})' for i, b, v in bad)
        raise SystemExit(
            f'night desk setups are hook only: {detail}. '
            'Move it to slide 1 or pick a different scene.')
    return True


BG_HISTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'bg_history.json')
# One, not three: a background may come back, it just must not appear in the
# very next post. Forcing a fresh set every time starves a pool this size, but
# two posts running with the same photo is the thing that reads as templated.
BG_COOLDOWN = 1           # posts a background sits out before it can return


def bg_history():
    try:
        return _json.load(open(BG_HISTORY))
    except Exception:
        return []


def record_post_bgs(topic, bgs):
    h = [e for e in bg_history() if e['topic'] != topic]
    h.append({'topic': topic, 'bgs': list(bgs)})
    _json.dump(h, open(BG_HISTORY, 'w'), indent=1)


def assert_bg_fresh(bgs, topic=None):
    """Raise if a background appeared in any of the last BG_COOLDOWN posts.

    assert_varied only looks inside one post, so three posts in a row can use
    the same five photos in the same order and each one passes. Across a feed
    that reads as one templated post repeated, which is the thing the vibe
    rule exists to prevent.
    """
    if BG_COOLDOWN <= 0:          # [-0:] is the whole list, not none of it
        return True
    recent = [e for e in bg_history() if e['topic'] != topic][-BG_COOLDOWN:]
    seen = {b: e['topic'] for e in recent for b in e['bgs']}
    clash = [(b, seen[b]) for b in bgs if b in seen]
    if clash:
        detail = '; '.join(f'{b} was in "{t}"' for b, t in clash)
        raise SystemExit(
            f'backgrounds reused within {BG_COOLDOWN} posts: {detail}. '
            'Pick different photos; the feed is what the viewer sees, not '
            'the single post.')
    return True


BAND_MAX_LUMA = 70        # mean luma of the copy band after the scrim


def copy_band_luma(bg):
    """Mean luma where the body copy lands, measured after the scrim.

    Brightness alone does not decide legibility, but past about 70 the dashes
    and the thinner strokes start dissolving into the photo. Cheap enough to
    run on every candidate, so the picker never offers one that will not hold
    five lines of white text.
    """
    im = base_photo(bg, (0.85, 0.68, 300, 1250))
    im = frame_for_band(im, 600, 1300)
    adaptive_scrim(im, 600, 1300)
    g = im.convert('L').crop((85, 980, 1000, 1310))
    px = list(g.getdata())
    return sum(px) / len(px)


TOOL_POOL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'tool_pool.json')
LANE_EXCLUDED = {'seller'}


def assert_audience(tools):
    """Raise if a roster drifts off the reader the account is written for.

    A pool is a menu, not a target. Selling tooling is in the pool because it
    was added deliberately, but a post built around it addresses someone
    running a store, which is not this audience. That is how a roster ended
    up pairing a day planner with a payments processor.
    """
    pool = _json.load(open(TOOL_POOL))
    tags = pool.get('audience', {})
    off = [t for t in tools if tags.get(t) in LANE_EXCLUDED]
    if off:
        raise SystemExit(
            'tools outside the lane: ' + ', '.join(off) + '. ' + pool.get('_lane', ''))
    unknown = [t for t in tools if t not in tags]
    if unknown:
        raise SystemExit('untagged tools: ' + ', '.join(unknown) +
                         '. Add them to tool_pool.json audience map.')
    return True


def preflight(topic, tools, bgs, pillar='tools', hook=None):
    """Every guard, in one call, before anything renders.

    assert_one_llm used to be opt-in and a generator could simply forget it,
    which is how a post shipped with no LLM at all. Generators call this and
    get the whole set.
    """
    if pillar == 'tools':
        assert_one_llm(tools)
        assert_fresh_tools(tools)
    assert_audience(tools)
    assert_varied(bgs)
    assert_bg_fresh(bgs, topic)
    if hook:
        assert_hook_approved(hook)
        assert_hook_fresh(hook, topic)
    return True


def assert_varied(bgs):
    """Raise if two adjacent slides share a vibe.

    A night LED desk followed by another night LED desk reads as one long
    slide; the eye needs a change of scene between cards. Vibes are tagged
    in bg/manifest.json.
    """
    assert_one_person(bgs)
    assert_bg_roles(bgs)
    for a, b in zip(bgs, bgs[1:]):
        va, vb = VIBES.get(a), VIBES.get(b)
        if va and va == vb:
            raise SystemExit(
                f'adjacent slides share vibe "{va}": {a} then {b}. '
                'Pick a different scene for one of them.')
    return True

def base_photo(name, grad):
    im = Image.open(f'{SP}/{name}').convert('RGB')
    if im.width < MIN_BG_PX[0] or im.height < MIN_BG_PX[1]:
        raise SystemExit(f'background {name} is {im.size}, below {MIN_BG_PX}: too soft for full bleed')
    inpaint_band(im, *BANDS[name])
    gradient_darken(im, *grad)
    return im

# ---------------------------------------------------------------- hook slides
#
# The first slide has one job: stop a thumb. Flat one-size centred text does
# not do that. Every style here uses the three things the best-performing
# hooks share: a size jump between the subject and its qualifier, a heavy
# black stroke so the words read on any photo, and a colour accent on the
# part that carries the promise.

HOOK_STYLES = ('stack', 'highlight', 'boxed', 'serif')


def _shadowed(im, xy, text, f, fill, anchor, offset=(0, 10), blur=18, alpha=200):
    """Soft drop shadow, not an outline.

    A stroke rings every glyph and reads as clip-art; the hooks that look
    professional sit on a blurred dark shadow offset downward, which lifts
    the text off the photo without drawing a border around it.
    """
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((xy[0] + offset[0], xy[1] + offset[1]), text, font=f,
            fill=(0, 0, 0, alpha), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0), layer.split()[3])
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor=anchor)


DIDOT = '/System/Library/Fonts/Supplemental/Didot.ttc'


def display_font(size, variation='Compressed Black'):
    """Heavy compressed display type.

    SF's default Black is a UI weight: wide, evenly spaced, and it reads as a
    system label blown up. The compressed cuts are the ones that look like
    display type on a photo, which is what every high-performing hook uses.
    """
    f = ImageFont.truetype(SF, size)
    f.set_variation_by_name(variation)
    return f


def serif_font(size, index=1):
    return ImageFont.truetype(DIDOT, size, index=index)


def _fit(text, variation, start, max_width=930, floor=40, maker=None):
    maker = maker or (lambda sz: display_font(sz, variation))
    size = start
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    while size > floor:
        f = maker(size)
        if probe.textlength(text, font=f) <= max_width:
            return f
        size -= 3
    return maker(floor)


# Hook typography, measured off the posts that performed: the stacked
# uppercase style from tools-nobody-posts and ship-alone. Line 1 is a short
# punchy headline in Compressed Black, line 2 is the rest in Condensed Bold
# underneath it. Numbers come from measuring those renders, not from taste:
# line 1 glyph height 181 spanning y 662-842, line 2 height 63 at y 883-945,
# both centred, both fitted to a 930px safe width.
HOOK_L1_SIZE = 250        # Compressed Black ceiling, shrinks to fit
HOOK_L2_SIZE = 86         # Condensed Bold ceiling, shrinks to fit
HOOK_L1_TOP = 655         # glyph top, not baseline
HOOK_L2_TOP = 881
HOOK_MAX_W = 930
HOOK_BAND = (620, 990)


def _fit_display(text, variation, start, max_w):
    size = start
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    while size > 40:
        f = display_font(size, variation)
        if probe.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return display_font(40, variation)


HOOK_POOL = hook_rules.HOOK_POOL


def assert_hook_approved(lines):
    """Raise unless this exact hook is one the user wrote or signed off.

    Hooks written from memory drift out of his voice, and he only finds out
    after the post has shipped. Membership in the pool is the only thing this
    checks; whether the hook is due back is assert_hook_fresh.
    """
    for h in hook_rules.pool():
        if hook_rules.key(h['lines']) == hook_rules.key(lines):
            return True
    ready = [' / '.join(h['lines']) for h in hook_rules.eligible()]
    raise SystemExit(
        'hook not in the approved pool: "' + ' / '.join(lines) + '". '
        'Use an eligible approved hook or ask for new ones. '
        'Eligible now: ' + '; '.join(ready[:6]))


def assert_hook_fresh(lines, topic=None):
    """Raise if this hook went out too recently.

    Hooks are not burn-once. A hook sits out hook_rules.HOOK_COOLDOWN posts,
    or half that if its last post was marked performing, and only a manual
    `retired: true` takes one out for good. The old boolean was advisory: it
    lived in a prompt, so a build could ignore it and did.
    """
    ok, why = hook_rules.status(lines, topic)
    if ok:
        return True
    ready = [' / '.join(h['lines']) for h in hook_rules.eligible(topic)]
    raise SystemExit(
        'hook "' + ' / '.join(lines) + '" is not eligible: ' + why + '. '
        'Eligible now: ' + ('; '.join(ready[:6]) if ready else
                            'none, ask Thinh for new hooks'))


def mark_hook_used(lines, topic=None):
    """Record the outing. `topic` is what lets the cooldown name the post and
    read its performance later, so pass it."""
    pool = _json.load(open(HOOK_POOL))
    for h in pool['hooks']:
        if hook_rules.key(h['lines']) == hook_rules.key(lines):
            h['used'] = True
    _json.dump(pool, open(HOOK_POOL, 'w'), indent=1, ensure_ascii=False)
    hook_rules.record(lines, topic)


def hook_slide(bg, lines, out, grad=(0.85, 0.72, 300, 1300), style=None,
               accent=YELLOW):
    """Stacked uppercase hook: big headline, smaller line under it.

    `lines[0]` is the headline and should be SHORT (two or three words); it
    is the thing that stops the scroll. `lines[1]` carries the rest. Both are
    uppercased here, so callers can pass either case.

    Sizes shrink to fit the safe width but never grow past the ceilings, so a
    long headline gets smaller rather than running off the slide. If line 1
    lands far under its ceiling the headline is too long: shorten it.
    """
    assert_hook_approved(lines)
    # drafts/<topic>/01.jpg — the topic is already in the path, so the guard
    # works without every generator remembering to pass it.
    assert_hook_fresh(lines, os.path.basename(os.path.dirname(os.path.abspath(out))))
    im = base_photo(bg, grad)
    im = frame_for_band(im, HOOK_BAND[0], HOOK_BAND[1])
    adaptive_scrim(im, HOOK_BAND[0], HOOK_BAND[1], target=88, strength_cap=0.62)

    l1, l2 = lines[0].upper(), lines[1].upper()
    f1 = _fit_display(l1, 'Compressed Black', HOOK_L1_SIZE, HOOK_MAX_W)
    f2 = _fit_display(l2, 'Condensed Bold', HOOK_L2_SIZE, HOOK_MAX_W)

    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    b1 = probe.textbbox((0, 0), l1, font=f1)
    b2 = probe.textbbox((0, 0), l2, font=f2)

    draw_text_block(im, [
        # anchor 'mm' centres the glyph box on y, so glyph top = y - h/2
        (540, HOOK_L1_TOP + (b1[3] - b1[1]) / 2, l1, f1, 'mm', WHITE),
        (540, HOOK_L2_TOP + (b2[3] - b2[1]) / 2, l2, f2, 'mm', WHITE),
    ])
    im.save(out, quality=92)
    print('wrote', out, '[stacked]')


def band_interest(im, y0, y1):
    """Std-dev of the copy band: how much is actually visible there."""
    g = im.convert('L').crop((0, y0, im.width, y1))
    px = list(g.getdata())
    m = sum(px) / len(px)
    return (sum((v - m) ** 2 for v in px) / len(px)) ** 0.5


# Above the copy band there is a large visible zone. Some photos put all
# their content in the lower third, leaving that zone flat black — the slide
# then looks like text floating on nothing, which is what "bad dark bg" means
# in practice. Detect a dead top zone and pan the photo down into frame.
TOP_ZONE = (200, 690)
MIN_TOP_INTEREST = 12


def frame_for_band(im, y0, y1, zoom=1.35):
    top_now = band_interest(im, *TOP_ZONE)
    if top_now >= MIN_TOP_INTEREST:
        return im
    w, h = im.size
    big = im.resize((int(w * zoom), int(h * zoom)), Image.LANCZOS)
    x0 = int((big.width - w) / 2)
    span = big.height - h

    def score(c):
        # both zones must carry something; the weaker one decides
        return min(band_interest(c, *TOP_ZONE), band_interest(c, y0, y1))

    best, best_score = im, score(im)
    for frac in (0.35, 0.5, 0.65, 0.8, 0.92, 1.0):
        off = min(span, int(span * frac))
        cand = big.crop((x0, off, x0 + w, off + h))
        sc = score(cand)
        if sc > best_score:
            best, best_score = cand, sc
    return best


def band_luma(im, y0, y1):
    g = im.convert('L').crop((0, y0, im.width, y1))
    px = list(g.getdata())
    return sum(px) / len(px)


def adaptive_scrim(im, y0, y1, target=96, feather=140, strength_cap=0.55):
    """Darken the copy band only as much as this photo needs.

    A fixed scrim ruins already-dark photos: the band goes to pure black and
    the slide reads as text on nothing. Measure first, then apply only the
    deficit, and skip entirely when the photo is dark enough on its own.
    """
    luma = band_luma(im, y0, y1)
    if luma <= target:
        return 0.0
    strength = min(strength_cap, 1 - (target / luma))
    text_scrim(im, y0, y1, strength=strength, feather=feather)
    return strength


def text_scrim(im, y0, y1, strength=0.62, feather=120):
    """Local darkening behind the copy band only, so text always reads while
    the rest of the photo stays visible."""
    band = Image.new('L', (1, im.height), 0)
    bp = band.load()
    for y in range(im.height):
        if y0 <= y <= y1:
            bp[0, y] = int(255 * strength)
        elif y0 - feather < y < y0:
            bp[0, y] = int(255 * strength * (y - (y0 - feather)) / feather)
        elif y1 < y < y1 + feather:
            bp[0, y] = int(255 * strength * (1 - (y - y1) / feather))
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0), band.resize(im.size))

# Both lines of an app slide teach. The second paragraph extends the first
# with the concrete consequence; it is never a verdict about the app. A
# verdict spends a slide the viewer gave you and hands back nothing they can
# act on, and it is the easiest thing to write, so it needs a guard.
# ARCO is exempt: its closing line is deliberate brand copy.
FILLER = [
    r'\bdoes the work\b', r'\bkeep it for that\b', r'\bsurvives?\b',
    r'\bnothing else (comes|does|touches|compares)', r'\bgame ?changer\b',
    r'\bchanged my life\b', r'\bbest app\b', r'\bworth every\b',
    r'\bcannot live without\b', r"\bcan't live without\b",
    r'\bi use it every day\b', r'\bgoes hard\b', r'\bunderrated\b',
]


def assert_teaches(title, body_lines, allow=False):
    """Raise if an app slide's copy is a verdict instead of a teaching point."""
    if allow or any(a.split(':')[0].lower() in title.lower() for a in ALWAYS_ALLOWED):
        return True
    text = ' '.join(body_lines).lower()
    hits = [p for p in FILLER if re.search(p, text)]
    if hits:
        raise SystemExit(
            f'{title}: copy reads as a verdict, not a teaching point '
            f'({", ".join(h.strip(chr(92) + "b") for h in hits)}). '
            'Say what the feature does and what it lets the viewer go and do.')
    return True


def app_slide(bg, icon, title, body_lines, out, grad=(0.85, 0.68, 300, 1250)):
    assert_teaches(title, body_lines)
    im = base_photo(bg, grad)
    im = frame_for_band(im, 600, 1300)
    adaptive_scrim(im, 600, 1300)
    ic, mask = rounded_icon(f'{ICONS}/{icon}')
    im.paste(ic, (88, 610), mask)
    tf = fit_font(title, 'Black', 84)
    items = [(85, 865, title, tf, 'la', (255, 255, 255))]
    # Body lines are dashed like the title's "1. Claude" numbering: a leading
    # dash on the first line of each paragraph gives the block structure and
    # stops it reading as a wall of sentences.
    body_f = font(50, 'Semibold')
    y = 995
    new_para = True
    for ln in body_lines:
        if ln == '':
            y += 26
            new_para = True
            continue
        if new_para:
            items.append((85, y, '-', body_f, 'la', (150, 150, 150)))
            new_para = False
        items.append((125, y, ln, body_f, 'la', (255, 255, 255)))
        y += 72
    draw_text_block(im, items)
    im.save(out, quality=92)
    print('wrote', out)

def rule_slide(bg, number, title, body_lines, out, grad=(0.85, 0.68, 300, 1250)):
    """A tool slide with a numbered badge where the app icon would be.

    Method-led pillars (discipline, screentime) have no app to show, and
    earlier posts in those pillars dropped the icon, the numbered title AND
    the dashes, which left a wall of sentences that read nothing like the
    tools posts. This keeps the exact tools layout: same badge box, same
    title position, same dashed body, so a viewer moving between pillars
    sees one format.
    """
    im = base_photo(bg, grad)
    im = frame_for_band(im, 600, 1300)
    adaptive_scrim(im, 600, 1300)

    # Badge in the icon slot: rounded square, big number, matching 210px box.
    badge = Image.new('RGBA', (210, 210), (0, 0, 0, 0))
    ImageDraw.Draw(badge).rounded_rectangle((0, 0, 209, 209), radius=48,
                                            fill=(255, 255, 255, 235))
    bd = ImageDraw.Draw(badge)
    nf = display_font(150, 'Compressed Black')
    # anchor 'mm' already centres the glyph box; do not offset by the bbox too
    bd.text((105, 105), str(number), font=nf, fill=(18, 18, 20), anchor='mm')
    im.paste(badge, (88, 610), badge)

    assert_teaches(title, body_lines)
    tf = fit_font(title, 'Black', 84)
    items = [(85, 865, title, tf, 'la', (255, 255, 255))]
    body_f = font(50, 'Semibold')
    y = 995
    new_para = True
    for ln in body_lines:
        if ln == '':
            y += 26
            new_para = True
            continue
        if new_para:
            items.append((85, y, '-', body_f, 'la', (150, 150, 150)))
            new_para = False
        items.append((125, y, ln, body_f, 'la', (255, 255, 255)))
        y += 72
    draw_text_block(im, items)
    im.save(out, quality=92)
    print('wrote', out, '[rule]')


def shot_slide(src, crop_top, lines, out, dark_text=False):
    shot = Image.open(src).convert('RGB')
    w, h = shot.size
    crop = shot.crop((0, crop_top, w, h))
    bg_px = crop.load()[15, crop.height - 15]
    canvas = Image.new('RGB', (1080, 1920), bg_px)
    scale_h = 1560
    sw = int(crop.width * scale_h / crop.height)
    if sw > 1020:
        sw = 1020
        scale_h = int(crop.height * sw / crop.width)
    crop = crop.resize((sw, scale_h), Image.LANCZOS)
    canvas.paste(crop, ((1080 - sw) // 2, 1920 - scale_h))
    fill = (10, 10, 10) if dark_text else (255, 255, 255)
    items = []
    for i, ln in enumerate(lines):
        f = fit_font(ln, 'Bold', 56, max_width=950)
        items.append((540, 150 + i * 90, ln, f, 'mm', fill))
    draw_text_block(canvas, items, shadow_alpha=0 if dark_text else 170)
    canvas.save(out, quality=92)
    print('wrote', out)

def closing_slide(bg, lines, out):
    hook_slide(bg, lines, out)



def cta_slide(bg, out, subtitle='Planner and app blocker in one.'):
    """Closing card for story posts: app icon, full store name, one line.

    No promo copy and never the word free; the promo CTA returns only when
    the in-app Redeem flow ships (2.0.2)."""
    im = base_photo(bg, (0.72, 0.5, 300, 1250))
    im = frame_for_band(im, 600, 1300)
    adaptive_scrim(im, 560, 1340, target=88)
    ic, mask = rounded_icon(f'{ICONS}/icon-arco.png', size=250, radius=56)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((415, 625, 665, 875), radius=56, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0), sh.split()[3])
    im.paste(ic, (415, 610), mask)
    name_f = font(58, 'Bold')
    sub_f = font(42, 'Semibold')
    store_f = font(36, 'Medium')
    draw_text_block(im, [
        (540, 940, 'ARCO: Day Planner & Focus', name_f, 'ma', (255, 255, 255)),
        (540, 1035, subtitle, sub_f, 'ma', (235, 235, 235)),
        (540, 1115, 'On the App Store', store_f, 'ma', (255, 214, 10)),
    ])
    im.save(out, quality=92)
    print('wrote', out)
