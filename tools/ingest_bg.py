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
