#!/usr/bin/env python3
"""Daily batch: five tools posts, backgrounds chosen by the guards not by hand."""
import json, os, sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, preflight, next_arco_angle,
                     record_post_tools, record_post_bgs, pick_hook_bg)

REPO = '/Users/thinh/SIXSIX/arco-app'

def pick_bgs(topic, n=5):
    """Hook plus n app backgrounds that satisfy every guard.

    The hook has to clear the cross-post cooldown too. pick_hook_bg only knows
    about hook usage, so ask it for a candidate that is also absent from the
    last few posts rather than taking whatever comes back first.
    """
    recent = [e for e in c.bg_history() if e['topic'] != topic][-c.BG_COOLDOWN:]
    recent_bgs = {b for e in recent for b in e['bgs']}
    log = json.load(open(f'{c.SP}/hook_usage.json'))
    fresh = [b for b in sorted(c.VIBES)
             if b not in log and b not in recent_bgs and os.path.exists(f'{c.SP}/{b}')]
    if not fresh:
        sys.exit(f'{topic}: no hook background is both unused and outside the cooldown')
    hook = pick_hook_bg(prefer=fresh[0])
    used = recent_bgs | {hook}
    pool = [b for b in sorted(c.VIBES)
            if c.VIBES[b] not in c.HOOK_ONLY_VIBES and b not in used
            and os.path.exists(f'{c.SP}/{b}')]
    # Drop anything whose copy band stays too bright after the scrim: the
    # dashes and thin strokes dissolve into the photo and the slide reads as
    # washed out on a phone.
    pool = [b for b in pool if c.copy_band_luma(b) <= c.BAND_MAX_LUMA]
    out, person = [], (hook in c.HAS_PERSON)
    last_vibe = c.VIBES.get(hook)
    for b in pool:
        if len(out) == n:
            break
        v = c.VIBES[b]
        if v == last_vibe:
            continue
        if b in c.HAS_PERSON:
            if person:
                continue
            person = True
        out.append(b)
        last_vibe = v
    if len(out) < n:
        sys.exit(f'{topic}: only {len(out)} backgrounds satisfy the guards')
    return [hook] + out


POSTS = [
 dict(topic='before-nine', hook=['5 tools', 'i open before 9am'],
      tools=['ChatGPT', 'ARCO', 'Raycast', 'CleanShot X', 'Endel'],
      icons=['icon-chatgpt.png', None, 'icon-raycast.png', 'icon-cleanshot.png', 'icon-endel.jpg'],
      body=[
       ['Tasks run a prompt on a schedule', 'and message you the result.', '',
        'A morning brief writes itself', 'before you are awake.'],
       None,
       ['Clipboard history searches all', 'of it, weeks back.', '',
        'The link you lost on tuesday is', 'two keystrokes away.'],
       ['Scrolling capture takes the whole', 'page, not just the screen.', '',
        'A long thread becomes one image', 'with nothing cut off.'],
       ['The soundscape shifts with the', 'time of day, not a playlist.', '',
        'Nothing ends, so nothing pulls', 'you out to pick the next track.'],
      ]),
 dict(topic='ship-with', hook=['5 tools', 'i ship with'],
      tools=['Codex', 'ARCO', 'Linear', 'Vercel', 'Sentry'],
      icons=['icon-codex.png', None, 'icon-linear.png', 'icon-vercel.png', 'icon-sentry.png'],
      body=[
       ['Give it a task and it works in its', 'own sandbox, then opens a PR.', '',
        'You review a diff instead of', 'watching it type.'],
       None,
       ['Cycles carry unfinished issues', 'into the next one on their own.', '',
        'Nothing gets quietly dropped at', 'the end of a sprint.'],
       ['Every pull request gets its own', 'live preview URL.', '',
        'You send the link, not a build', 'and a set of instructions.'],
       ['Session replay shows the exact', 'clicks before the crash.', '',
        'You stop guessing how to', 'reproduce it.'],
      ]),
 dict(topic='posting-daily', hook=['5 tools', 'for posting every day'],
      tools=['Claude', 'ARCO', 'Descript', 'OpusClip', 'Buffer'],
      icons=['icon-claude.jpg', None, 'icon-descript.png', 'icon-opusclip.png', 'icon-buffer.png'],
      body=[
       ['A Project holds your files and', 'rules for every chat inside it.', '',
        'You stop pasting the same', 'context at the top of each one.'],
       None,
       ['Edit the video by deleting words', 'from the transcript.', '',
        'Cutting a sentence cuts the', 'footage with it.'],
       ['It scores each clip before you', 'post, not after.', '',
        'You publish the ones it rates', 'high and skip the rest.'],
       ['One queue, with its own posting', 'times per platform.', '',
        'You load a week on sunday and', 'it goes out without you.'],
      ]),
 dict(topic='saved-hours', hook=['5 tools', 'that saved me hours this week'],
      tools=['Perplexity', 'ARCO', 'Make', 'Photoroom', 'ElevenLabs'],
      icons=['icon-perplexity.png', None, 'icon-make.png', 'icon-photoroom.png', 'icon-elevenlabs.png'],
      body=[
       ['You can aim a search at academic', 'papers or reddit alone.', '',
        'The answer stops averaging the', 'whole internet.'],
       None,
       ['A scenario shows the data moving', 'through every step.', '',
        'You watch where it breaks instead', 'of reading a log.'],
       ['Point it at a folder and it cuts', 'the background from all of them.', '',
        'Fifty product shots take one', 'pass, not fifty.'],
       ['It clones a voice from about a', 'minute of clean audio.', '',
        'After that it reads anything you', 'write in the same voice.'],
      ]),
 dict(topic='selling-online', hook=['5 tools', 'to sell something online'],
      tools=['Gemini', 'ARCO', 'Stripe', 'Gumroad', 'beehiiv'],
      icons=['icon-gemini.png', None, 'icon-stripe.png', 'icon-gumroad.png', 'icon-beehiiv.png'],
      body=[
       ['A Gem is a saved version with its', 'own instructions and files.', '',
        'You build the assistant once and', 'open it like an app.'],
       None,
       ['A payment link sells a product', 'with no website at all.', '',
        'You paste it in a bio and take', 'money the same day.'],
       ['It handles the VAT and delivers', 'the file after purchase.', '',
        'No tax rules to read and no', 'download page to build.'],
       ['The referral program is built in,', 'not a plugin.', '',
        'Readers bring readers without', 'you wiring anything up.'],
      ]),
]

for p in POSTS:
    out = f"{REPO}/drafts/{p['topic']}"
    os.makedirs(out, exist_ok=True)
    bgs = pick_bgs(p['topic'])
    preflight(p['topic'], p['tools'], bgs)
    hook_slide(bgs[0], p['hook'], f'{out}/01.jpg')
    for i, (tool, icon, body) in enumerate(zip(p['tools'], p['icons'], p['body'])):
        n = i + 1
        if tool == 'ARCO':
            app_slide(bgs[n], 'icon-arco.png', f'{n}. ARCO', next_arco_angle(), f'{out}/{n+1:02d}.jpg')
        else:
            app_slide(bgs[n], icon, f'{n}. {tool}', body, f'{out}/{n+1:02d}.jpg')
    record_post_tools(p['topic'], p['tools'])
    record_post_bgs(p['topic'], bgs)
    print(f"  {p['topic']:16s} {' / '.join(p['hook'])}  |  {', '.join(p['tools'])}")
    print(f"  {'':16s} bgs: {', '.join(bgs)}\n")
