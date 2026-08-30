#!/usr/bin/env python3
"""launch-weekend: the builder stack that makes a weekend launch real.

The post shipped on 2026-08-24 from an ad-hoc script that was never committed,
so this file is a reconstruction of that spec: backgrounds recovered by
matching each rendered slide against the pool, copy read back off the slides.

Slide 2 changed on 2026-08-30. It was rendered on bg-h13, which Thinh has
since moved to bg/_deleted_by_user/, so the slide could not be rebuilt at all
and the frame was one he had rejected. It is now bg-h21 (lounge-night): no
person, not a hook-only vibe, copy band at 64.6 against the 70 ceiling, and a
different vibe from both neighbours, which are night desks.

Legacy guard waivers -- why this does not call preflight()
----------------------------------------------------------
The post predates four rules and its untouched slides break them. preflight()
would abort a rebuild over slides that are out of scope for the slide-2 redo,
so the guards that this post *can* satisfy are called individually below and
the rest are recorded here:

  * assert_one_person  -- bg-h17 (slide 1) and bg-h16 (slide 3) both show a
                          person; the rule allows one per post.
  * assert_bg_roles    -- bg-h16 on slide 3 is desk-person-night, a hook-only
                          vibe, and it is not the hook.
  * assert_varied      -- slides 4, 5 and 6 are all lounge-day, so two pairs
                          of adjacent slides share a vibe.
  * assert_hook_approved -- "launch an app / in one weekend" predates
                          hook_pool.json and is not in it.

Fixing any of those means re-rendering slides Thinh did not ask about, which
also drags them onto the current dashed body style (compose gained that on
2026-08-25, the day after this post). Rebuild the post properly when he wants
it rebuilt; do not do it silently inside a slide redo.

Usage:
    python3 tools/gen-launch-weekend.py            # every slide
    python3 tools/gen-launch-weekend.py --only 02  # one slide, for redos
"""
import os
import sys

sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import app_slide, hook_slide

REPO = '/Users/thinh/SIXSIX/arco-app'
TOPIC = 'launch-weekend'

HOOK = ['launch an app', 'in one weekend']

# index 0 is the hook, 1..5 are the app slides in order
BGS = [
    'bg-h17.jpg',   # 01 hook        desk-person-night
    'bg-h21.jpg',   # 02 Claude      lounge-night   (was bg-h13, deleted by user)
    'bg-h16.jpg',   # 03 ARCO        desk-person-night
    'bg-h09.jpg',   # 04 Supabase    lounge-day
    'bg-h02.jpg',   # 05 Vercel      lounge-day
    'bg-h04.jpg',   # 06 RevenueCat  lounge-day
]

TOOLS = ['Claude', 'ARCO', 'Supabase', 'Vercel', 'RevenueCat']
ICONS = ['icon-claude.jpg', 'icon-arco.png', 'icon-supabase.png',
         'icon-vercel.png', 'icon-revenuecat.png']
TITLES = ['1. Claude', '2. ARCO: Day Planner & Focus', '3. Supabase',
          '4. Vercel', '5. RevenueCat']
BODY = [
    ['Claude Code runs in my terminal.', 'It reads the whole project and',
     'edits the files directly.'],
    ['A weekend build only works with', 'locked focus. My tasks, the plan',
     'and app blocking in one place.', '', 'My holy grail.'],
    ['A real database with auth in one', 'afternoon. The free tier covers',
     'a whole MVP.'],
    ['Push to GitHub and the site is', 'live seconds later, with a preview',
     'link for every branch.'],
    ['Subscriptions without a payment', 'server. One line tells the app',
     'who paid.'],
]


def check_app_bg(i):
    """The guards an app background has to clear, for slide index i in BGS."""
    bg = BGS[i]
    vibe = c.VIBES.get(bg)
    if vibe in c.HOOK_ONLY_VIBES:
        raise SystemExit(f'{bg} is {vibe}, a hook-only vibe, on slide {i+1}')
    for j in (i - 1, i + 1):
        if 0 <= j < len(BGS) and c.VIBES.get(BGS[j]) == vibe:
            raise SystemExit(f'slide {i+1} repeats the vibe "{vibe}" of slide {j+1}')
    luma = c.copy_band_luma(bg)
    if luma > c.BAND_MAX_LUMA:
        raise SystemExit(f'{bg} copy band is {luma:.1f}, over {c.BAND_MAX_LUMA}')
    return luma


def main(only=None):
    out = f'{REPO}/drafts/{TOPIC}'
    os.makedirs(out, exist_ok=True)
    c.assert_bg_fresh(BGS, TOPIC)
    if only in (None, 1):
        hook_slide(BGS[0], HOOK, f'{out}/01.jpg')
    for i, (title, icon, body) in enumerate(zip(TITLES, ICONS, BODY), start=1):
        if only not in (None, i + 1):
            continue
        luma = check_app_bg(i)
        app_slide(BGS[i], icon, title, body, f'{out}/{i+1:02d}.jpg')
        print(f'  {BGS[i]}  {c.VIBES.get(BGS[i]):18s} band luma {luma:.1f}')


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
