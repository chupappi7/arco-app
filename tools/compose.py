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
    **{f'bg-h{i:02d}.jpg': (0, 1) for i in range(1, 20)},
}

# Backgrounds must be true 1080x1920. The bg-dNN pool was built by upscaling
# small desktop images 3x-6.7x and reads visibly soft on a phone screen; it is
# retired from full-bleed use. Anything below MIN_BG_PX of real pixels raises.
MIN_BG_PX = (1000, 1700)

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
    """lines[0] = the big subject, lines[1] = the smaller qualifier."""
    im = base_photo(bg, grad)
    im = frame_for_band(im, 690, 1060)
    adaptive_scrim(im, 660, 1080, target=104)
    if style is None:
        style = HOOK_STYLES[sum(ord(c) for c in bg) % len(HOOK_STYLES)]
    big, small = lines[0].upper(), lines[1]
    d = ImageDraw.Draw(im)

    # The subject runs edge to edge; the qualifier is roughly 40% of its
    # height. That ratio is what makes the hook readable at thumb speed.
    # Compressed display type, set large: the subject fills the width, the
    # qualifier is roughly 40% of its height.
    if style == 'stack':
        fb = _fit(big, 'Compressed Black', 260, max_width=1000, floor=110)
        fs = _fit(small.upper(), 'Condensed Bold', int(fb.size * 0.36), max_width=980)
        _shadowed(im, (540, 840), big, fb, WHITE, 'ms')
        _shadowed(im, (540, 862), small.upper(), fs, WHITE, 'ma')

    elif style == 'highlight':
        fb = _fit(big, 'Compressed Black', 250, max_width=1010, floor=104)
        fs = _fit(small.upper(), 'Compressed Black', int(fb.size * 0.92),
                  max_width=1010, floor=96)
        _shadowed(im, (540, 800), big, fb, WHITE, 'ms')
        _shadowed(im, (540, 812), small.upper(), fs, accent, 'ma')

    elif style == 'boxed':
        fb = _fit(big, 'Compressed Black', 260, max_width=1000, floor=110)
        fs = _fit(small, 'Condensed Bold', int(fb.size * 0.32), max_width=860)
        w = d.textlength(small, font=fs)
        _shadowed(im, (540, 828), big, fb, WHITE, 'ms')
        pad, h = 32, int(fs.size * 1.5)
        d.rounded_rectangle((540 - w / 2 - pad, 856, 540 + w / 2 + pad, 856 + h),
                            radius=14, fill=accent)
        d.text((540, 856 + h / 2), small, font=fs, fill=(10, 10, 10), anchor='mm')

    else:  # serif — compressed sans subject over an elegant Didot qualifier
        fb = _fit(big, 'Compressed Black', 265, max_width=1000, floor=112)
        fs = _fit(small, None, int(fb.size * 0.42), max_width=950,
                  maker=lambda sz: serif_font(sz))
        _shadowed(im, (540, 815), big, fb, WHITE, 'ms')
        _shadowed(im, (540, 838), small, fs, WHITE, 'ma')

    im.save(out, quality=92)
    print('wrote', out, f'[{style}]')


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


def adaptive_scrim(im, y0, y1, target=96, feather=140):
    """Darken the copy band only as much as this photo needs.

    A fixed scrim ruins already-dark photos: the band goes to pure black and
    the slide reads as text on nothing. Measure first, then apply only the
    deficit, and skip entirely when the photo is dark enough on its own.
    """
    luma = band_luma(im, y0, y1)
    if luma <= target:
        return 0.0
    strength = min(0.55, 1 - (target / luma))
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
    body_f = font(50, 'Semibold')
    y = 995
    for ln in body_lines:
        if ln == '':
            y += 26
            continue
        items.append((85, y, ln, body_f, 'la', (255, 255, 255)))
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

