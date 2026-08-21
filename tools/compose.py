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

def fit_font(text, variation, start, max_width=925, floor=44):
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
    'src-hook.jpg': (350, 730), 'src-claude.jpg': (370, 660), 'src-lamp.jpg': (370, 660),
    'src-bed.jpg': (370, 650), 'src-notion.jpg': (470, 690), 'src-pool.jpg': (1140, 1430),
    'src-pool2.jpg': (1130, 1520), 'src-rc.jpg': (370, 650), 'src-cars.jpg': (670, 1120),
    'src-higgs.jpg': (375, 1055),
    'src-cars-clean.jpg': (0, 1),
    **{f'bg-d{i:02d}.jpg': (0, 1) for i in range(1, 15)},
}

def base_photo(name, grad):
    im = Image.open(f'{SP}/{name}').convert('RGB')
    inpaint_band(im, *BANDS[name])
    gradient_darken(im, *grad)
    return im

def hook_slide(bg, lines, out, grad=(0.55, 0.80, 700, 1200)):
    im = base_photo(bg, grad)
    hf = font(74, 'Bold')
    items = [(540, 445, lines[0], hf, 'mm', (255, 255, 255)),
             (540, 550, lines[1], hf, 'mm', (255, 255, 255))]
    draw_text_block(im, items)
    im.save(out, quality=92)
    print('wrote', out)

def app_slide(bg, icon, title, body_lines, out, grad=(0.55, 0.78, 1000, 1550)):
    im = base_photo(bg, grad)
    ic, mask = rounded_icon(f'{ICONS}/{icon}')
    im.paste(ic, (88, 335), mask)
    tf = fit_font(title, 'Black', 84)
    items = [(85, 585, title, tf, 'la', (255, 255, 255))]
    body_f = font(50, 'Semibold')
    y = 713
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

