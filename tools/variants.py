#!/usr/bin/env python3
"""Crop the 9:16 slides into the shapes other platforms accept.

  python3 tools/variants.py <topic> [<topic> ...]
  python3 tools/variants.py --all

Instagram's publishing API refuses anything taller than 4:5 — stricter than
the Instagram app itself, so a carousel that posts fine from a phone is
rejected when an API submits it. Pinterest wants 2:3.

This does NOT re-render. Every slide type puts its type between y=300 and
y=1650 — the icon sits at 335, the hook band at 620-990, body copy ends by
1300 — so a fixed window keeps all of it and throws away only background.
Checked by eye across hook, tool, numbered-rule, icon-shelf and closing
cards before being trusted; a contact sheet is written each run so it stays
checkable.
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DRAFTS = os.path.join(os.environ.get('ARCO_PAGES_REPO', REPO), 'drafts')

# name -> (top, height). Width is always the full 1080.
SIZES = {
    # 5px inside 4:5 rather than exactly on it. 1080x1350 is 0.8000, the
    # documented floor, and a boundary value is the wrong thing to bet a
    # delivery on. The five pixels are empty background.
    'ig':  (300, 1345),   # ~4:5 — Instagram feed, carousels, Threads
    'pin': (150, 1620),   # 2:3  — Pinterest
}
SRC = (1080, 1920)


def variant(topic, name, quiet=False):
    top, height = SIZES[name]
    src = os.path.join(DRAFTS, topic)
    dst = os.path.join(src, name)
    slides = sorted(f for f in os.listdir(src)
                    if f.endswith('.jpg') and f[0].isdigit())
    if not slides:
        raise SystemExit('no slides in %s' % src)
    os.makedirs(dst, exist_ok=True)
    out = []
    for f in slides:
        im = Image.open(os.path.join(src, f)).convert('RGB')
        if im.size != SRC:
            raise SystemExit('%s/%s is %s, not %s — the window is only valid '
                             'for the standard canvas' % (topic, f, im.size, SRC))
        im.crop((0, top, 1080, top + height)).save(
            os.path.join(dst, f), 'JPEG', quality=92, optimize=True)
        out.append(f)
    sheet(topic, name, out)
    if not quiet:
        print('%s/%s: %d slides at 1080x%d' % (topic, name, len(out), height))
    return out


def sheet(topic, name, slides):
    """One strip of everything that was written, to be looked at."""
    w, h = 200, int(200 * SIZES[name][1] / 1080)
    im = Image.new('RGB', (len(slides) * (w + 6) + 6, h + 12), (10, 15, 30))
    for i, f in enumerate(slides):
        c = Image.open(os.path.join(DRAFTS, topic, name, f)).resize((w, h), Image.LANCZOS)
        im.paste(c, (6 + i * (w + 6), 6))
    im.save(os.path.join(DRAFTS, topic, name, '_sheet.jpg'), 'JPEG', quality=88)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = [n for n in SIZES if '--%s' % n in sys.argv] or list(SIZES)
    if '--all' in sys.argv:
        args = sorted(d for d in os.listdir(DRAFTS)
                      if os.path.isdir(os.path.join(DRAFTS, d))
                      and not d.startswith('_'))
    if not args:
        raise SystemExit(__doc__)
    for topic in args:
        for name in names:
            try:
                variant(topic, name)
            except SystemExit as exc:
                print('! %s/%s: %s' % (topic, name, exc))


if __name__ == '__main__':
    main()
