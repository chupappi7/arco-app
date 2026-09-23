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
from compose import (rule_slide, hook_slide, preflight, mark_hook_used,
                     record_post_tools, record_post_bgs)


def build(topic, hook, bgs, arco_lines, rules):
    out = f'{c.REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    preflight(topic, ['ARCO'], bgs, pillar='screentime', hook=hook)
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

    rule_slide(bgs[1], 1, '1. ARCO: Day Planner & Focus', arco_lines,
               f'{out}/02.jpg', badge=False, title_fill=c.YELLOW)
    for i, (title, body) in enumerate(rules, 2):
        rule_slide(bgs[i], i, f'{i}. {title}', body, f'{out}/{i + 1:02d}.jpg',
                   badge=False, title_fill=c.YELLOW)

    if not any(e.get('topic') == topic for e in c.tool_history()):
        record_post_tools(topic, ['ARCO'])
    record_post_bgs(topic, bgs)
    print('\nbackgrounds:', ', '.join(bgs))
