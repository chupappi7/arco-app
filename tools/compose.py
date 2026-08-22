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

BANDS = {
    'src-hook.jpg': (350, 730), 'src-claude.jpg': (370, 660), 'src-lamp.jpg': (370, 745),
    'src-bed.jpg': (370, 650), 'src-notion.jpg': (470, 690), 'src-pool.jpg': (1140, 1430),
    'src-pool2.jpg': (1130, 1520), 'src-rc.jpg': (370, 650), 'src-cars.jpg': (670, 1120),
    'src-higgs.jpg': (375, 1055),
    'src-cars-clean.jpg': (0, 1),
    # bg-nNN: true 1440x2560+ sources, downscaled to 1080x1920. No captions.
    **{f'bg-n{i:02d}.jpg': (0, 1) for i in range(1, 11)},
    # bg-hNN: pulled straight from Higgsfield via tools/ingest_bg.py
    **{f'bg-h{i:02d}.jpg': (0, 1) for i in range(1, 13)},
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

def hook_slide(bg, lines, out, grad=(0.62, 0.62, 300, 1300)):
    im = base_photo(bg, grad)
    text_scrim(im, 700, 990, strength=0.55)
    hf = font(74, 'Bold')
    items = [(540, 790, lines[0], hf, 'mm', (255, 255, 255)),
             (540, 895, lines[1], hf, 'mm', (255, 255, 255))]
    draw_text_block(im, items)
    im.save(out, quality=92)
    print('wrote', out)

# TikTok overlays its own UI on a photo post: search bar across the top ~12%,
# caption and username across the bottom ~28%, action buttons down the right
# ~15%. Copy therefore lives in the middle band, left of x=945.
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

def app_slide(bg, icon, title, body_lines, out, grad=(0.72, 0.55, 300, 1250)):
    im = base_photo(bg, grad)
    text_scrim(im, 600, 1300)
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

