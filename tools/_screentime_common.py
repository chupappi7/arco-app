"""Shared build for the screentime method posts in the 2026-09-23 batch.

A screentime hook promises a method, so the slides are numbered rule_slide
steps (app_slide refuses under this pillar). ARCO leads at 1 in the same
layout as every other step. Styling follows Thinh's notes on
screentime-100h: no numbered squares, the number lives in the yellow title.

No icon shelf on the hook: the shelf shows a tools roster, and a screentime
post has none. A lone ARCO icon under the hook would announce the app on the
slide that has to read as advice.
"""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
import hook_rules
from compose import (rule_slide, hook_slide, phone_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)


def build(topic, hook, bgs, arco_lines, rules, screen=None):
    out = f'{c.REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    # rule_slide serves both method-led pillars, and assert_hook_pillar takes
    # the pillar from the hook, so hardcoding screentime here rejected a
    # discipline hook that wants exactly this shape.
    pillar = hook_rules.pillar_of(hook) or 'screentime'
    preflight(topic, ['ARCO'], bgs, pillar=pillar, hook=hook)
    for b in bgs[1:]:
        luma = c.copy_band_luma(b)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{b}: copy band luma {luma:.1f} > {c.BAND_MAX_LUMA}')

    log = json.load(open(f'{c.SP}/hook_usage.json'))
    if bgs[0] not in log:
        c.pick_hook_bg(prefer=bgs[0])

    hook_slide(bgs[0], hook, f'{out}/01.jpg')
    # A rebuild must not append a second outing for the same post.
    if not any(e.get('topic') == topic for e in hook_rules.history()):
        mark_hook_used(hook, topic)

    # Thinh, 2026-11-02: the yellow headline is out, and the headline size has
    # to be the same on every slide. fit_font sizes each title on its own, so
    # the longest step set the floor and the rest rendered bigger -- size the
    # whole post by its longest title instead.
    titles = ['1. ARCO Focus'] + [f'{i}. {t}' for i, (t, _) in enumerate(rules, 2)]
    size = min(c.fit_font(t, 'Black', 84).size for t in titles)
    if screen:
        # Thinh, 2026-11-02: show the app rather than describe it. A method
        # post has no roster, so ARCO's step is the one slide that can carry a
        # real screen, and the screens posts in this pillar out-engage the
        # all-text ones. The remaining steps stay on photos: four handsets in
        # a row would read as an ad, not a method.
        from _veiled_screens import SHOTS, STYLE, veiled
        src, crop, stitle, sbody = screen
        phone_slide(veiled(bgs[1]), f'{SHOTS}/{src}', crop, '1', stitle, sbody,
                    f'{out}/02.jpg', style=STYLE)
    else:
        rule_slide(bgs[1], 1, titles[0], arco_lines,
                   f'{out}/02.jpg', badge=False, title_size=size)
    for i, ((title, body), full) in enumerate(zip(rules, titles[1:]), 2):
        rule_slide(bgs[i], i, full, body, f'{out}/{i + 1:02d}.jpg',
                   badge=False, title_size=size)

    if not any(e.get('topic') == topic for e in c.tool_history()):
        record_post_tools(topic, ['ARCO'])
    record_post_bgs(topic, bgs)
    print('\nbackgrounds:', ', '.join(bgs))
