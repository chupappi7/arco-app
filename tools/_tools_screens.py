"""Tools posts in the screens look.

Thinh's request of 2026-10-04: the ship-weekend-screens format (hook photo,
ARCO's real screen in a handset over a veiled photo, the icon card with the
App Store badge) for the tools pillar. A tools post is a roster, so the hook
carries the icon shelf, ARCO leads at #1 on its own screen, and the other
tools follow on the same veiled ground with their icon where the handset
would be: same eyebrow, numbered title and body column as phone_slide, so the
set reads as one format. The card closes on next_arco_angle(theme) and the
"arco focus" search line.
"""
import json
import os
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from PIL import Image, ImageDraw, ImageFilter
import compose as c
import hook_rules
from compose import (hook_slide, phone_slide, cta_slide, preflight,
                     assert_teaches, assert_roster_allowed, mark_hook_used,
                     record_post_tools, record_post_bgs)
from _veiled_screens import SHOTS, STYLE, KICKER, CARD_OUTLINE, veiled

PROMO = ['Search “arco focus” on the App Store.']

TOOL = {'x': 72, 'w': 936, 'icon': 220, 'icon_y': 560, 'title_size': 76,
        'body_size': 44, 'app_size': 34}


def wrap_px(text, f, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        trial = f'{cur} {w}'.strip()
        if cur and f.getlength(trial) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def widow(name, lines):
    """A wrapped block may not end on a lone word: it reads as a mistake."""
    if len(lines) > 1 and len(lines[-1].split()) == 1:
        raise SystemExit(f'{name}: "{lines[-1]}" sits alone on the last line')


def tool_slide(ground, icon, name, number, title, body, out):
    """A roster tool on the veiled ground: icon, name, numbered claim, body.

    `body` is two sentences, the mechanism then what it lets you do.
    """
    assert_roster_allowed(out)
    assert_teaches(title, body)
    im = ground.copy()
    T, X = TOOL, TOOL['x']
    size = T['icon']
    ic, mask = c.rounded_icon(f'{c.ICONS}/{icon}', size=size, radius=int(size * 0.225))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        (X + 4, T['icon_y'] + 16, X + size + 4, T['icon_y'] + size + 16),
        radius=int(size * 0.225), fill=(0, 0, 0, 150))
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0),
             sh.filter(ImageFilter.GaussianBlur(24)).split()[3])
    # A thin ring keeps a black icon (Notion, ChatGPT) from melting into the fade.
    pad = 4
    ring = Image.new('L', (size + 2 * pad, size + 2 * pad), 0)
    ring.paste(mask, (pad, pad))
    ring = ring.filter(ImageFilter.MaxFilter(5))
    im.paste(Image.new('RGB', ring.size, (70, 70, 76)), (X - pad, T['icon_y'] - pad), ring)
    im.paste(ic, (X, T['icon_y']), mask)

    head = f'{number}. {title}'
    for s in range(T['title_size'], T['title_size'] - 20, -2):
        tf = c.font(s, STYLE['title_face'])
        tlines = wrap_px(head, tf, T['w'])
        if len(tlines) <= 2:
            break
    widow(name, tlines)
    bf = c.font(T['body_size'], STYLE['body_face'])
    y = T['icon_y'] + size + 56
    items = [(X, y, name, c.font(T['app_size'], STYLE['app_face']), 'la', STYLE['eyebrow'])]
    y += 62
    for ln in tlines:
        items.append((X, y, ln, tf, 'la', STYLE['ink']))
        y += round(tf.size * STYLE['lead'])
    y += 30
    for para in body:
        lines = wrap_px(para, bf, T['w'])
        widow(name, lines)
        for ln in lines:
            items.append((X, y, ln, bf, 'la', STYLE['sub']))
            y += round(bf.size * 1.32)
        y += 22
    if y > 1640:
        raise SystemExit(f'{name}: copy runs to y={y}, into the caption zone')
    c.draw_text_block(im, items, shadow_alpha=0)
    im.save(out, quality=94)
    print('wrote', out)


def build(topic, hook, theme, bgs, arco, tools, closer, only=None):
    """arco: (screen, title, body) for ARCO's slide. tools: [(name, title,
    [mechanism, consequence])] in roster order after ARCO. closer: the card's
    lines, drawn once from next_arco_angle(theme) and frozen in the generator.
    bgs: hook, ARCO, each tool, then the card."""
    out = f'{c.REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    roster = ['ARCO'] + [t[0] for t in tools]
    if len(bgs) != len(roster) + 2:
        raise SystemExit('need a background for the hook, each tool and the card')
    if not any(h['lines'] == hook for h in hook_rules.eligible(topic, 'tools')):
        raise SystemExit(f'hook not eligible: {hook}')
    c.assert_audience(roster)
    preflight(topic, roster, bgs, pillar='tools', hook=hook)
    assert_teaches(arco[1], [arco[2]])
    icons = json.load(open(c.TOOL_POOL))['icons']

    want = (lambda n: only is None or n in only)
    if want(1):
        hook_slide(bgs[0], hook, f'{out}/01.jpg', kicker=KICKER,
                   icons=[icons[t] for t in roster])
    if only is None and not any(e.get('topic') == topic for e in hook_rules.history()):
        mark_hook_used(hook, topic)

    if want(2):
        (src, crop), title, body = arco
        phone_slide(veiled(bgs[1]), f'{SHOTS}/{src}', crop, '1', title, body,
                    f'{out}/02.jpg', style=STYLE)
    for i, ((name, title, body), bg) in enumerate(zip(tools, bgs[2:-1]), 3):
        if want(i):
            tool_slide(veiled(bg), icons[name], name, i - 1, title, body,
                       f'{out}/{i:02d}.jpg')

    n = len(roster) + 2
    if want(n):
        cta_slide(None, f'{out}/{n:02d}.jpg', subtitle=closer, promo=PROMO,
                  badge=True, card=veiled(bgs[-1]),
                  style={'icon': 240, 'box': (96, 984, 520, 1400), 'name_size': 62,
                         'ink': (248, 248, 250), 'sub': (176, 176, 184),
                         **CARD_OUTLINE})

    if only is not None:
        return
    if not any(e.get('topic') == topic for e in c.tool_history()):
        record_post_tools(topic, roster)
    record_post_bgs(topic, bgs)
