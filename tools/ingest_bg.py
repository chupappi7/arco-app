#!/usr/bin/env python3
"""Ingest background photos into tools/slides/bg from URLs or local paths.

  python3 tools/ingest_bg.py <url-or-path> [...]

Crops to 9:16, downscales to 1080x1920 (never upscales), skips anything whose
real resolution is too low, and skips images already in the pool (content hash
of the processed result). Prints what landed.
"""
import hashlib
import io
import os
import subprocess
import sys

from PIL import Image

BG = os.path.join(os.path.dirname(__file__), 'slides', 'bg')
MIN_CROP_W = 1000        # real pixels across after the 9:16 crop

# Auto-quality gate. A background only has to do one job: hold white text in
# the copy band (y 600-1300) after the scrim. These thresholds reject the two
# ways that fails — a band so bright the scrim cannot save it, and a band so
# busy that glyph edges compete with detail.
BAND = (600, 1300)
MAX_BAND_LUMA = 180      # mean brightness of the copy band, 0-255
MAX_BAND_DETAIL = 46     # mean abs. gradient in the band: texture/busyness
MIN_GLOBAL_STD = 12      # reject flat/empty frames (grey walls, blank sky)


def quality(im):
    """Return (ok, reason, metrics) for a 1080x1920 candidate.

    Scores a 270x480 thumbnail, not the full frame: brightness and texture
    survive downsampling, and the full-resolution loop took ~40s per image,
    which timed the daily ingest out.
    """
    g = im.convert('L').resize((270, 480), Image.BILINEAR)
    band = g.crop((0, int(BAND[0] / 4), 270, int(BAND[1] / 4)))
    px = list(band.getdata())
    n = len(px)
    luma = sum(px) / n
    w, h = band.size
    # mean absolute horizontal gradient, sampled every other row for speed
    detail, count = 0, 0
    for y in range(0, h, 2):
        row = px[y * w:(y + 1) * w]
        for x in range(0, w - 4, 4):
            detail += abs(row[x] - row[x + 4])
            count += 1
    detail /= max(1, count)
    gp = list(g.getdata())
    mean = sum(gp) / len(gp)
    std = (sum((v - mean) ** 2 for v in gp) / len(gp)) ** 0.5
    m = f'luma={luma:.0f} detail={detail:.0f} std={std:.0f}'
    if luma > MAX_BAND_LUMA:
        return False, 'copy band too bright for white text', m
    if detail > MAX_BAND_DETAIL:
        return False, 'copy band too busy behind text', m
    if std < MIN_GLOBAL_STD:
        return False, 'image too flat/empty', m
    return True, '', m


def existing_hashes():
    out = {}
    for f in os.listdir(BG):
        if f.endswith('.jpg'):
            p = os.path.join(BG, f)
            out[hashlib.md5(open(p, 'rb').read()).hexdigest()] = f
    return out


def fetch(src):
    if src.startswith(('http://', 'https://')):
        raw = subprocess.run(['curl', '-sL', src], capture_output=True).stdout
        return Image.open(io.BytesIO(raw))
    return Image.open(src)


def next_index():
    used = [f for f in os.listdir(BG) if f.startswith('bg-h') and f.endswith('.jpg')]
    nums = [int(f[4:6]) for f in used if f[4:6].isdigit()]
    return max(nums, default=0) + 1


def main(sources):
    seen = existing_hashes()
    idx = next_index()
    added = skipped = 0
    for src in sources:
        try:
            im = fetch(src).convert('RGB')
        except Exception as exc:
            print(f'  FAIL  {src[:60]}: {exc}')
            continue
        w, h = im.size
        cw = int(h * 9 / 16)
        if cw <= w:
            if cw < MIN_CROP_W:
                print(f'  SKIP  {src[-28:]}: only {cw}px across after crop')
                skipped += 1
                continue
            im = im.crop(((w - cw) // 2, 0, (w + cw) // 2, h))
        else:
            ch = int(w * 16 / 9)
            if w < MIN_CROP_W:
                print(f'  SKIP  {src[-28:]}: only {w}px wide')
                skipped += 1
                continue
            top = max(0, (h - ch) // 2)
            im = im.crop((0, top, w, min(h, top + ch)))
        im = im.resize((1080, 1920), Image.LANCZOS)
        ok, why, metrics = quality(im)
        if not ok:
            print(f'  REJECT {src[-28:]}: {why}  [{metrics}]')
            skipped += 1
            continue
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=94)
        digest = hashlib.md5(buf.getvalue()).hexdigest()
        if digest in seen:
            print(f'  DUP   {src[-28:]} == {seen[digest]}')
            skipped += 1
            continue
        name = f'bg-h{idx:02d}.jpg'
        open(os.path.join(BG, name), 'wb').write(buf.getvalue())
        seen[digest] = name
        print(f'  ADD   {name}  <- {src[-40:]}')
        idx += 1
        added += 1
    print(f'\n{added} added, {skipped} skipped')
    if added:
        print('Register them in compose.BANDS with (0, 1) — these have no baked captions.')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
