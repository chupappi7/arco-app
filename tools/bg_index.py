#!/usr/bin/env python3
"""Everything the background gallery needs to know, cached to one file.

  python3 tools/bg_index.py            # refresh slides/bg/.index.json

The dashboard is stdlib-only and the gallery wants facts that only PIL can
answer — chiefly copy_band_luma, which is what decides whether five lines of
white text survive on a photo. Measuring 83 full-res frames takes a minute,
so it happens here and the dashboard just reads the result.

Re-run after adding backgrounds. The dashboard also triggers this in the
background when it sees a file the index does not know about.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(HERE, 'slides', 'bg')
INDEX = os.path.join(BG, '.index.json')


def build(quiet=False):
    sys.path.insert(0, HERE)
    import compose
    man = json.load(open(os.path.join(BG, 'manifest.json')))
    vibes, person = man['vibes'], set(man['has_person'])
    old = {}
    try:
        old = {b['name']: b for b in json.load(open(INDEX))['bgs']}
    except Exception:
        pass
    out = []
    files = sorted(f for f in os.listdir(BG) if f.endswith('.jpg'))
    for i, name in enumerate(files, 1):
        # Luma is the expensive part and a photo never changes once pooled,
        # so a name already measured is taken from the old index.
        luma = (old.get(name) or {}).get('luma')
        if luma is None:
            try:
                luma = round(compose.copy_band_luma(name), 1)
            except Exception as exc:
                luma = None
                if not quiet:
                    print('  %s: %s' % (name, exc))
        vibe = vibes.get(name)
        out.append({
            'name': name,
            'vibe': vibe or 'untagged',
            'person': name in person,
            # Night desks and the jet are the strongest frames in the pool and
            # are barred from body slides, so the gallery has to say so before
            # you pick one for slide 3.
            'hook_only': vibe in compose.HOOK_ONLY_VIBES,
            'luma': luma,
            'copy_ok': luma is not None and luma <= compose.BAND_MAX_LUMA,
        })
        if not quiet and i % 10 == 0:
            print('  %d/%d' % (i, len(files)), flush=True)
    data = {'bgs': out, 'band_max_luma': compose.BAND_MAX_LUMA,
            'hook_only_vibes': sorted(compose.HOOK_ONLY_VIBES)}
    with open(INDEX, 'w') as fh:
        json.dump(data, fh, indent=1)
    return data


if __name__ == '__main__':
    d = build()
    print('indexed %d backgrounds -> %s' % (len(d['bgs']), INDEX))
