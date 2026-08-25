#!/usr/bin/env python3
"""Retire pooled backgrounds whose Higgsfield source the user has deleted.

  python3 tools/map_bg_sources.py <live-rawUrl> ...   # rebuild bg/.sources.json
  python3 tools/sync_bg.py                            # retire what it orphaned

Backgrounds are downloaded and stored permanently, so deleting a generation in
the Higgsfield web app does not reach the pool. map_bg_sources.py identifies
each pooled file's source by re-rendering every live generation through the
ingest pipeline and matching content hashes; anything pooled with no live
source is moved to bg/_deleted_by_user/ and dropped from the manifest, the
vibe map and the hook rotation.

Local imports (src-*) and bg-n* are not Higgsfield-sourced and are left alone.
"""
import json
import os
import shutil
import sys

BG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slides', 'bg')
GONE = os.path.join(BG, '_deleted_by_user')
SOURCES = os.path.join(BG, '.sources.json')


def main(argv):
    if not os.path.exists(SOURCES):
        sys.exit('no bg/.sources.json - run tools/map_bg_sources.py <live urls> first')
    live = json.load(open(SOURCES))
    pooled = sorted(f for f in os.listdir(BG) if f.startswith('bg-h') and f.endswith('.jpg'))
    orphans = [f for f in pooled if f not in live]
    if not orphans:
        print('pool is in sync with Higgsfield')
        return
    if '--yes' not in argv:
        print('would retire: ' + ', '.join(orphans))
        print('re-run with --yes to move them')
        return

    os.makedirs(GONE, exist_ok=True)
    manifest_path = os.path.join(BG, 'manifest.json')
    m = json.load(open(manifest_path))
    hook_path = os.path.join(BG, 'hook_usage.json')
    hooks = json.load(open(hook_path)) if os.path.exists(hook_path) else []

    for fname in orphans:
        shutil.move(os.path.join(BG, fname), os.path.join(GONE, fname))
        m['vibes'].pop(fname, None)
        m['has_person'] = [x for x in m['has_person'] if x != fname]
        hooks = [x for x in hooks if x != fname]

    json.dump(m, open(manifest_path, 'w'), indent=2)
    json.dump(hooks, open(hook_path, 'w'), indent=1)
    print(f'{len(orphans)} retired: ' + ', '.join(orphans))


if __name__ == '__main__':
    main(sys.argv[1:])
