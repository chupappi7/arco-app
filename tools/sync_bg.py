#!/usr/bin/env python3
"""Retire pooled backgrounds whose Higgsfield source the user has deleted.

  python3 tools/sync_bg.py <live-rawUrl> [...]

Backgrounds are downloaded and stored permanently, so deleting a generation
in the Higgsfield web app does not reach the pool. Pass the rawUrls currently
present in the account (from show_generations) and anything in the pool whose
source is no longer among them is moved to bg/_deleted_by_user/ and dropped
from the manifest, the hook rotation and the vibe map.

Only ingested-from-Higgsfield files are considered; local imports (src-*) are
left alone.
"""
import json
import os
import re
import shutil
import sys

BG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slides', 'bg')
GONE = os.path.join(BG, '_deleted_by_user')


def basename(u):
    return re.sub(r'.*/', '', u.strip())


def main(live_urls):
    if not live_urls:
        sys.exit(__doc__)
    live = {basename(u) for u in live_urls}
    ledger_path = os.path.join(BG, '.ingested.txt')
    ledger = [l.strip() for l in open(ledger_path) if l.strip()]

    # ledger order matches bg-hNN assignment order for Higgsfield sources
    hf = [l for l in ledger if 'cloudfront' in l]
    pooled = sorted(f for f in os.listdir(BG) if f.startswith('bg-h') and f.endswith('.jpg'))
    if len(hf) != len(pooled):
        print(f'note: {len(hf)} ledger entries vs {len(pooled)} pooled files; '
              'mapping is best-effort, verify before trusting a mass retire')

    os.makedirs(GONE, exist_ok=True)
    manifest_path = os.path.join(BG, 'manifest.json')
    m = json.load(open(manifest_path))
    hook_path = os.path.join(BG, 'hook_usage.json')
    hooks = json.load(open(hook_path)) if os.path.exists(hook_path) else []

    retired = []
    for src, fname in zip(hf, pooled):
        if basename(src) not in live and os.path.exists(os.path.join(BG, fname)):
            shutil.move(os.path.join(BG, fname), os.path.join(GONE, fname))
            m['vibes'].pop(fname, None)
            m['has_person'] = [x for x in m['has_person'] if x != fname]
            hooks = [x for x in hooks if x != fname]
            retired.append(fname)

    json.dump(m, open(manifest_path, 'w'), indent=2)
    json.dump(hooks, open(hook_path, 'w'), indent=1)
    print(f'{len(retired)} retired' + (': ' + ', '.join(retired) if retired else ''))


if __name__ == '__main__':
    main(sys.argv[1:])
