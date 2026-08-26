#!/usr/bin/env python3
"""Two tools posts, ARCO leading. Picker and guards as in gen-daily-batch."""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     record_post_tools, record_post_bgs, pick_hook_bg)

def pick_bgs(topic, n=5):
    recent = [e for e in c.bg_history() if e['topic'] != topic][-c.BG_COOLDOWN:]
    rb = {b for e in recent for b in e['bgs']}
    log = json.load(open(f'{c.SP}/hook_usage.json'))
    fresh = [b for b in sorted(c.VIBES) if b not in log and b not in rb
             and os.path.exists(f'{c.SP}/{b}')]
    hook = pick_hook_bg(prefer=fresh[0])
    used = rb | {hook}
    pool = [b for b in sorted(c.VIBES)
            if c.VIBES[b] not in c.HOOK_ONLY_VIBES and b not in used
            and os.path.exists(f'{c.SP}/{b}')
            and c.copy_band_luma(b) <= c.BAND_MAX_LUMA]
    out, person, last = [], hook in c.HAS_PERSON, c.VIBES.get(hook)
    for b in pool:
        if len(out) == n: break
        if c.VIBES[b] == last: continue
        if b in c.HAS_PERSON:
            if person: continue
            person = True
        out.append(b); last = c.VIBES[b]
    return [hook] + out

POSTS = [
 dict(topic='killed-busywork', hook=['5 tools', 'that killed my busywork'],
      tools=['ARCO','ChatGPT','Figma','Loom','Airtable'],
      icons=[None,'icon-chatgpt.png','icon-figma.png','icon-loom.png','icon-airtable.png'],
      body=[None,
       ['Custom instructions apply to every','chat you ever open.','',
        'You stop restating how you want','answers written.'],
       ['Auto layout resizes the frame to','whatever is inside it.','',
        'Text gets longer and nothing','needs nudging back into place.'],
       ['Viewers comment at a timestamp,','not under the video.','',
        'Feedback lands on the exact frame','it is about.'],
       ['An Interface turns the base into a','clean page for other people.','',
        'They fill in the form and never','see the spreadsheet.'],
      ]),
 dict(topic='found-sooner', hook=['5 tools', 'i wish i found sooner'],
      tools=['ARCO','Cursor','CleanShot X','Stripe','PostHog'],
      icons=[None,'icon-cursor.png','icon-cleanshot.png','icon-stripe.png','icon-posthog.png'],
      body=[None,
       ['Tab predicts your next edit across','the file, not the next word.','',
        'It follows the change you already','started making.'],
       ['Pin a screenshot and it floats','above every other window.','',
        'You copy from it without switching','back and forth.'],
       ['Test mode gives you fake cards','that behave like real ones.','',
        'You run the whole checkout before','taking a single payment.'],
       ['Feature flags and session replay','sit in the same tool.','',
        'Ship to ten percent and watch what','those users actually did.'],
      ]),
]

for p in POSTS:
    out = f"/Users/thinh/SIXSIX/arco-app/drafts/{p['topic']}"
    os.makedirs(out, exist_ok=True)
    bgs = pick_bgs(p['topic'])
    preflight(p['topic'], p['tools'], bgs)
    hook_slide(bgs[0], p['hook'], f'{out}/01.jpg')
    for i,(tool,icon,body) in enumerate(zip(p['tools'],p['icons'],p['body'])):
        n = i+1
        if tool == 'ARCO':
            app_slide(bgs[n], 'icon-arco.png', '1. ARCO', next_arco_angle(), f'{out}/{n+1:02d}.jpg')
        else:
            app_slide(bgs[n], icon, f'{n}. {tool}', body, f'{out}/{n+1:02d}.jpg')
    record_post_tools(p['topic'], p['tools'])
    record_post_bgs(p['topic'], bgs)
    print(f"  {p['topic']:16s} {' / '.join(p['hook'])} | {', '.join(p['tools'])}")
