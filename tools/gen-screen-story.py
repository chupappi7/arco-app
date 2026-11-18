#!/usr/bin/env python3
"""Screen-story slideshows: ARCO's port of the LockViet variant carousel Thinh made
on 2026-11-17 (~/Downloads/Lockvi-marketing/scripts/slideshow.py).

Each slide is a centred two-line title and a short line on top, over a blurred
photograph, with the real app screen in an iPhone frame rising from the bottom.
Slide 1 zooms in (bigger phone). The last slide is the app icon. 3:4, 1080x1440.

Screens are real captures: Oct 7 (design/control-center) and Aug 21
(screenshots/redesign/raw). The simulator was busy with other sessions.

Usage: python3 tools/gen-screen-story.py [variant ...]   (default: all)
"""
import os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
BG = TOOLS / 'slides/bg'
ICON = TOOLS / 'slides/icons/icon-arco.png'
CC = Path.home() / 'SIXSIX/design/control-center/appstore/assets'
RAW = Path.home() / 'SIXSIX/screenshots/redesign/raw'
FD = str(Path.home() / 'Library/Fonts/SF-Pro-Display-')
W, H = 1080, 1440
APP_STORE_NAME = 'App Blocker & Focus: ARCO'
TITLE_Y, LINE, SUB_Y, PHONE_Y, PHONE_W = 215, 96, 420, 495, 600

SCREENS = {
    'today': CC / 'scr-today.png',            # in-app Today, 7 Oct
    'widgets': CC / 'screen-widgets.png',     # home screen: habit grids, focus chart
    'habits': CC / 'scr-habits.png',
    'timeline': CC / 'scr-timeline.png',      # home screen: today's-timeline widget
    'shield': CC / 'screen-shield.png',       # what a blocked app shows
    'screentime': CC / 'screen-insights.png', # Insights, bad habits: screen time
    'blocked': RAW / 'BlockedHours.png',
    'plan': RAW / 'Plan.png',
    'tasks': RAW / 'Tasks.png',
    'insights': RAW / 'Insights.png',         # Insights, good habits: habit time
}

# topic: (background, [(title 1, title 2, line, screen)])
VARIANTS = {
    'arco-ss-block': ('bg-h63.jpg', [
        ('Block TikTok', 'on a schedule', 'Your apps lock during the hours you set.', 'blocked'),
        ('Open Instagram,', 'get a question', 'What does this add to your day?', 'shield'),
        ('Start focus', 'from your plan', 'A timer on any block, distractions locked out.', 'today'),
        ('See where', 'the hours went', 'Screen time, split app by app.', 'screentime'),
    ]),
    'arco-ss-day': ('bg-h19.jpg', [
        ('My whole day', 'on one screen', 'Tasks, habits and focus, drawn to scale.', 'today'),
        ('Plan it', 'in a minute', 'Tap a task or a habit to give it a time.', 'plan'),
        ('Every project', 'gets a colour', 'Each task with a priority flag and a time.', 'tasks'),
        ('Your plan on', 'the home screen', "Today's timeline in a widget.", 'timeline'),
    ]),
    'arco-ss-habits': ('bg-n10.jpg', [
        ('Habits that', 'fit your day', 'Each one gets its own time in the plan.', 'widgets'),
        ('Right there', 'in the timeline', 'With a timer or a check, next to your tasks.', 'today'),
        ('Watch the', 'grid fill up', 'Every habit as a grid on your home screen.', 'habits'),
        ('Hours, not', 'just ticks', 'Insights adds up the time for each one.', 'insights'),
    ]),
    'arco-ss-screentime': ('bg-h22.jpg', [
        ('Where did', 'my day go?', 'ARCO shows it, app by app.', 'screentime'),
        ('Lock the', 'worst ones', 'TikTok and Instagram stay shut in Blocked Hours.', 'blocked'),
        ('A pause', 'before the scroll', 'Open a blocked app and ARCO asks why.', 'shield'),
        ('Then give', 'the hours a job', 'Your day as timed blocks.', 'today'),
    ]),
}


def f(weight, size): return ImageFont.truetype(f'{FD}{weight}.otf', size)


def background(name):
    b = Image.open(BG / name).convert('RGB')
    y = (b.height - round(b.width * H / W)) // 2
    b = b.crop((0, max(0, y), b.width, max(0, y) + round(b.width * H / W))).resize((W, H))
    b = b.filter(ImageFilter.GaussianBlur(26))
    return ImageEnhance.Brightness(b).enhance(0.72).convert('RGBA')


def centred(im, y, text, font, fill):
    d = ImageDraw.Draw(im)
    d.text(((W - d.textlength(text, font=font)) / 2, y), text, font=font, fill=fill)


def rounded(im, r):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    im = im.convert('RGBA'); im.putalpha(m); return im


def phone(screen, width):
    s = Image.open(SCREENS[screen]).convert('RGB')
    s = s.resize((width, round(width * s.height / s.width)), Image.LANCZOS)
    r = round(width * 55 / 393)
    bez, rim = round(width * 0.022), 3
    body = Image.new('RGBA', (s.width + 2 * (bez + rim), s.height + 2 * (bez + rim)), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((0, 0, body.width - 1, body.height - 1), r + bez + rim, fill=(150, 152, 156, 255))
    d.rounded_rectangle((rim, rim, body.width - 1 - rim, body.height - 1 - rim), r + bez, fill=(12, 12, 14, 255))
    body.alpha_composite(rounded(s, r), (bez + rim, bez + rim))
    return body


def slide(bg, t1, t2, sub, screen, hero):
    im = background(bg)
    centred(im, TITLE_Y, t1, f('Bold', 80), (255, 255, 255, 255))
    centred(im, TITLE_Y + LINE, t2, f('Bold', 80), (255, 255, 255, 255))
    centred(im, SUB_Y, sub, f('Regular', 38), (255, 255, 255, 220))
    p = phone(screen, 780 if hero else PHONE_W)
    x = (W - p.width) // 2
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x, PHONE_Y + 30, x + p.width, PHONE_Y + p.height + 30), 110, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    im.alpha_composite(p, (x, PHONE_Y))
    return im.convert('RGB')


def last(bg):
    im = background(bg)
    ic = rounded(Image.open(ICON).convert('RGB').resize((420, 420), Image.LANCZOS), 94)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((330, 400, 750, 820), 94, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(36)))
    im.alpha_composite(ic, (330, 370))
    ImageDraw.Draw(im).rounded_rectangle((330, 370, 749, 789), 94, outline=(255, 255, 255, 70), width=3)
    # The App Store name, word for word, so a viewer can search for it.
    centred(im, 870, APP_STORE_NAME, f('Bold', 64), (255, 255, 255, 255))
    centred(im, 966, 'Plan your day. Block the rest.', f('Regular', 38), (255, 255, 255, 220))
    bdg = Image.open(TOOLS / 'slides/icons/appstore-badge.png').convert('RGBA')
    bdg = bdg.resize((400, round(bdg.height * 400 / bdg.width)), Image.LANCZOS)
    im.alpha_composite(bdg, ((W - bdg.width) // 2, 1046))
    return im.convert('RGB')


def build(topic):
    bg, slides = VARIANTS[topic]
    out = REPO / 'drafts' / topic
    out.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(slides, 1):
        slide(bg, *s, hero=(i == 1)).save(out / f'{i:02d}.jpg', quality=92)
    last(bg).save(out / f'{len(slides) + 1:02d}.jpg', quality=92)
    print(out)


for t in (sys.argv[1:] or VARIANTS):
    build(t)
