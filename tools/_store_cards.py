"""Store-card slideshow: a photo hook, then one app per slide on light grey.

Each app slide puts the app icon, a bold name and a short grey paragraph on the
left, and the app's own screenshot in a black phone frame on the right. 3:4
(1080x1440), matching the photo-mode posts this layout was taken from.

Rendered as HTML with headless Chrome. Fonts: Inter Tight 800 for names and the
hook, Manrope 500 for body copy (Google Fonts).
"""
import html, os, subprocess, sys, tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
W, H = 1080, 1440

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@800'
         '&family=Manrope:wght@400;500&display=block" rel="stylesheet">')
BASE = f'''*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{-webkit-font-smoothing:antialiased}}'''


def url(p):
    return 'file://' + os.path.abspath(p)


def hook_html(bg, title, sub):
    t = '<br>'.join(html.escape(x) for x in title)
    return f'''<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{BASE}
body{{background:#222 url("{url(bg)}") center/cover}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(0,0,0,.38) 100%)}}
.t{{position:absolute;left:78px;top:810px;font:800 158px/0.88 'Inter Tight';letter-spacing:-0.055em;color:#fff;
   text-shadow:0 2px 24px rgba(0,0,0,.18)}}
.s{{position:absolute;left:86px;top:1112px;font:400 62px 'Manrope';letter-spacing:-0.02em;color:rgba(255,255,255,.92)}}
.w{{position:absolute;left:92px;top:1268px;font:500 36px 'Manrope';color:rgba(255,255,255,.85)}}
</style></head><body><div class="shade"></div><div class="t">{t}</div>
<div class="s">{html.escape(sub)}</div><div class="w">Swipe &rarr;</div></body></html>'''


def app_html(icon, name, body, shot, name_px=72):
    return f'''<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{BASE}
body{{background:#f2f2f0}}
.col{{position:absolute;left:62px;top:0;bottom:0;width:440px;display:flex;flex-direction:column;justify-content:center}}
.ic{{width:162px;height:162px;border-radius:38px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08);margin-bottom:34px}}
.ic img{{width:100%;height:100%;display:block}}
.n{{font:800 {name_px}px/1.02 'Inter Tight';letter-spacing:-0.045em;color:#141414;margin-bottom:30px}}
.b{{font:500 38px/1.36 'Manrope';letter-spacing:-0.01em;color:#4b4b4b}}
.ph{{position:absolute;left:546px;top:228px;width:472px;height:986px;border-radius:78px;background:#0c0c0c;
    padding:13px;box-shadow:0 40px 60px -20px rgba(0,0,0,.28),0 10px 22px rgba(0,0,0,.10)}}
.ph div{{width:100%;height:100%;border-radius:66px;overflow:hidden;background:#000}}
.ph img{{width:100%;height:100%;object-fit:cover;object-position:top;display:block}}
</style></head><body>
<div class="col"><div class="ic"><img src="{url(icon)}"></div>
<div class="n">{html.escape(name)}</div><div class="b">{html.escape(body)}</div></div>
<div class="ph"><div><img src="{url(shot)}"></div></div></body></html>'''


def shoot(page, out):
    with tempfile.TemporaryDirectory() as d:
        src, png = f'{d}/s.html', f'{d}/s.png'
        open(src, 'w').write(page)
        subprocess.run([CHROME, '--headless=new', '--hide-scrollbars', '--force-device-scale-factor=1',
                        f'--window-size={W},{H}', '--virtual-time-budget=6000',
                        '--allow-file-access-from-files', f'--screenshot={png}', url(src)],
                       check=True, capture_output=True)
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '92', png, '--out', out],
                       check=True, capture_output=True)


def build(topic, hook_bg, hook, sub, apps, only=None):
    """apps: [(icon, name, body, shot)] -- ARCO first."""
    out = f'{REPO}/drafts/{topic}'
    os.makedirs(out, exist_ok=True)
    pages = [hook_html(hook_bg, hook, sub)] + [app_html(*a) for a in apps]
    for i, p in enumerate(pages, 1):
        if only and i not in only:
            continue
        shoot(p, f'{out}/{i:02d}.jpg')
        print(f'{out}/{i:02d}.jpg')


def main(**kw):
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}
    build(**kw, only=only or None)
