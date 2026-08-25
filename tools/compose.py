YELLOW = (255, 214, 10)
WHITE = (255, 255, 255)
#!/usr/bin/env python3
"""Slide-composition helpers for the TikTok pipeline (see the tiktok-pipeline skill).
Backgrounds in tools/slides/bg (BANDS maps caption zones needing inpainting;
bg-dNN.jpg files are clean). Icons in tools/slides/icons."""
import os
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
    **{f'bg-h{i:02d}.jpg': (0, 1) for i in range(1, 81) if i != 23},
}

# Backgrounds must be true 1080x1920. The bg-dNN pool was built by upscaling
# small desktop images 3x-6.7x and reads visibly soft on a phone screen; it is
# retired from full-bleed use. Anything below MIN_BG_PX of real pixels raises.
MIN_BG_PX = (1000, 1700)

# Backgrounds containing a person. At most ONE of these may appear in a
# single post: two photos of a man at a desk in one carousel reads as stock
# imagery. `assert_one_person(list_of_bgs)` enforces it at build time.
import json as _json
try:
    HAS_PERSON = set(_json.load(open(f'{SP}/manifest.json'))['has_person'])
except Exception:
    HAS_PERSON = set()


try:
    VIBES = _json.load(open(f'{SP}/manifest.json'))['vibes']
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
TOOL_COOLDOWN = 6          # posts a tool must sit out before it can return


def tool_history():
    try:
        return _json.load(open(TOOL_LOG))
    except Exception:
        return []


def tools_on_cooldown():
    """Tools used in the last TOOL_COOLDOWN posts — do not use these."""
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


def next_arco_angle():
    """Return the next unused ARCO body copy, cycling through all angles.

    ARCO appears in every listicle, which makes its slide the most repeated
    text in the feed. Rotating the angle means a returning viewer learns a
    different feature each time instead of rereading the same three lines.
    """
    d = _json.load(open(ARCO_ANGLES))
    unused = [a for a in d['angles'] if a['id'] not in d['used']]
    if not unused:
        d['used'], unused = [], d['angles']
    pick = unused[0]
    d['used'].append(pick['id'])
    _json.dump(d, open(ARCO_ANGLES, 'w'), indent=1)
    return pick['lines']


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


def assert_varied(bgs):
    """Raise if two adjacent slides share a vibe.

    A night LED desk followed by another night LED desk reads as one long
    slide; the eye needs a change of scene between cards. Vibes are tagged
    in bg/manifest.json.
    """
    assert_one_person(bgs)
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


def hook_slide(bg, lines, out, grad=(0.85, 0.72, 300, 1300), style=None,
               accent=YELLOW):
    """Quiet hook: lowercase, regular weight, one size, centred in the safe band.

    This is the treatment that actually performed. Heavy compressed uppercase
    was borrowed from talking-head references where the text has to compete
    with a person on screen; on a photo carousel the photo IS the composition
    and shouting over it reads as a template. `style` is accepted and ignored
    so existing callers keep working.
    """
    im = base_photo(bg, grad)
    im = frame_for_band(im, 690, 1000)
    adaptive_scrim(im, 690, 1000, strength_cap=0.42)
    f = _fit(' '.join(lines), 'Bold', 64, max_width=900, floor=44,
             maker=lambda sz: font(sz, 'Bold'))
    # one size for both lines, generous line gap, sitting mid-frame
    draw_text_block(im, [
        (540, 790, lines[0], f, 'mm', WHITE),
        (540, 790 + int(f.size * 1.42), lines[1], f, 'mm', WHITE),
    ])
    im.save(out, quality=92)
    print('wrote', out, '[quiet]')


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

def app_slide(bg, icon, title, body_lines, out, grad=(0.85, 0.68, 300, 1250)):
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
