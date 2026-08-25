#!/usr/bin/env python3
"""Rebuild the exact bg-hNN -> Higgsfield source mapping by content hash.

  python3 tools/map_bg_sources.py <live-rawUrl> [...]

Pooled backgrounds are the byte-exact output of ingest_bg's crop+resize+JPEG
pass, so re-running that pass on a live source and hashing the result
identifies which pooled file came from it. Writes bg/.sources.json:
{"bg-h07.jpg": "<rawUrl>", ...}. Anything pooled with no live source is
reported as orphaned (the user deleted that generation in Higgsfield).
"""
import certifi, hashlib, io, json, os, ssl, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

CTX = ssl.create_default_context(cafile=certifi.where())

BG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slides', 'bg')
DIRS = [BG] + [os.path.join(BG, d) for d in
               ('_deleted_by_user', '_captioned_retired', '_lowres_retired')]
MIN_CROP_W = 760


def rendered_hash(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    raw = urllib.request.urlopen(req, timeout=90, context=CTX).read()
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    w, h = im.size
    cw = int(h * 9 / 16)
    if cw <= w:
        if cw < MIN_CROP_W:
            return None
        im = im.crop(((w - cw) // 2, 0, (w + cw) // 2, h))
    else:
        ch = int(w * 16 / 9)
        if w < MIN_CROP_W:
            return None
        top = max(0, (h - ch) // 2)
        im = im.crop((0, top, w, min(h, top + ch)))
    im = im.resize((1080, 1920), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=94)
    return hashlib.md5(buf.getvalue()).hexdigest()


def main(urls):
    if not urls:
        sys.exit(__doc__)
    pool = {}
    for d in DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.startswith('bg-h') and f.endswith('.jpg'):
                pool[hashlib.md5(open(os.path.join(d, f), 'rb').read()).hexdigest()] = f

    def one(u):
        try:
            return u, rendered_hash(u)
        except Exception as exc:
            print(f'  FAIL {u[-32:]}: {exc}')
            return u, None

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(one, urls))

    mapping = {}
    for u, digest in results:
        if digest and digest in pool:
            mapping[pool[digest]] = u
    json.dump(dict(sorted(mapping.items())), open(os.path.join(BG, '.sources.json'), 'w'), indent=1)
    live_named = set(mapping)
    orphans = sorted(set(pool.values()) - live_named)
    print(f'{len(mapping)}/{len(pool)} pooled files matched to a live source')
    print('orphaned (source deleted in Higgsfield): ' + (', '.join(orphans) or 'none'))


if __name__ == '__main__':
    main(sys.argv[1:])
