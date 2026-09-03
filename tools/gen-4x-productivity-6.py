#!/usr/bin/env python3
"""4x-productivity-6: the 4x hook, icon-shelf opening.

hook_rules.eligible(pillar='tools') returns three hooks and this is the least
recently used of them: "the tools i used to / 4x my productivity" last went
out on 4x-productivity-5, nine posts back, against five for wish-i-knew-at-17
and four for five-do-the-work. It ships verbatim. The build follows
gen-keep-five-3.py: a shelf of the five roster icons under the headline so
the viewer sees the post before reading a word, ARCO leading, one teaching
point per app, mechanism then consequence.

The only thing carried over from the three earlier posts on this hook is the
hook. All three ran the identical roster (ARCO, Codex, Notion, Obsidian,
CapCut), which is exactly what a returning viewer would recognise as a
repeat, so none of those five appear here.

  roster ARCO, Antigravity, n8n, OpusClip, ElevenLabs. Exactly one LLM, and
         Antigravity is the only one in the pool that has never shipped:
         Cursor, Manus, Gemini, ChatGPT, Claude, Perplexity and Codex have
         carried the last seven posts between them. Nothing tagged 'seller',
         no overlap with the previous post's set.
         The five answer "4x" as multiplication rather than as a stack tour:
         every one of them turns a single unit of work into several finished
         ones. The day's plan takes what fits, one prompt becomes three
         agents, one saved run becomes every test, one recording becomes ten
         clips, one video becomes another language. That is the shape the
         hook promises, and a roster of "apps i like" would not have it.
  copy   every point is a capability no caption in tools/hooks.json has
         taught. That ruled out the obvious ones: n8n has already taught
         self-hosting, OpusClip its virality score, ElevenLabs voice cloning
         from a minute of audio. So this post teaches pinned step output,
         speaker-tracking reframe and dubbing in your own voice.
         Vercel was the first pick for slide 5 and was dropped: preview URLs
         per pull request, instant deploy and one-click promote have all
         been captions already, and nothing real was left to teach.
  ARCO   "the tools i used to 4x my productivity" asks how more gets done in
         the same day, so THEME is 'planning'. next_arco_angle('planning')
         would hand back v2, which is v1 with two words moved. v12 is used
         instead: it has never shipped, and Anytime holding the untimed
         tasks until the day has room is the one angle that is about the
         day's capacity, which is what "4x" actually asks about.
  photos six frames, none of them in the last post, walked with the
         gen-daily-batch guards: hook plain and dark where the shelf lands,
         app frames free of hook-only vibes, every copy band under
         BAND_MAX_LUMA, no adjacent vibe repeat, no person at all. Three of
         the five app frames have not been used in forty posts or more and
         two have never shipped at all.
         bg-h52 was rendered for slide 4 first and replaced: it passes the
         luma gate at 52.7 as a mean, but the mean hides three lit monitors
         sitting exactly where the grey paragraph dashes go, and both dashes
         disappeared into them on the render. bg-h36 is 16.0 and clean.

The hook frame is picked for the shelf before it is picked for the text. The
icons land at y1105-1447, so the lower half of slide 1 has to be plain and
dark or they stop reading as a set. Measured over the shelf box on the real
render, bg-h63 is 11.0 luma at sd 12.3, an unlit wall behind a dark desk:
second plainest in the pool and the plainest that has not been near the feed
lately. bg-h59 measures 10.3 but carried the hook one post back on
best-for-last-2; bg-h39 is 15.5 and went out two posts back. Everything
never yet used as a hook fails the shelf outright: the four day frames left
in that set run 72 to 103 luma across the shelf box, which puts five icons
on a lit window. bg-h63 last carried a hook twenty-five posts ago on
ship-alone-2, under the old style with no shelf.

As in gen-keep-five-3.py the app frames carry GRAD_DARK (f_bot 0.42) rather
than app_slide's default 0.68; BAND_MAX_LUMA is a mean and the default ramp
leaves highlights sitting behind the grey paragraph dashes. Every frame here
is a daylight one, so all five use it.

  01 hook        bg-h63  desk-led-neon    shelf zone luma 11.0, sd 12.3
  02 ARCO        bg-h33  desk-empty-day   band luma 55.8
  03 Antigravity bg-h04  lounge-day       band luma 56.4
  04 n8n         bg-h36  supercars-dusk   band luma 16.0
  05 OpusClip    bg-h28  villa-day        band luma 56.6
  06 ElevenLabs  bg-h09  lounge-day       band luma 57.8

Usage:
    python3 tools/gen-4x-productivity-6.py            # every slide
    python3 tools/gen-4x-productivity-6.py --only 03  # one slide, for redos
"""
import json
import os
import sys

sys.path.insert(0, '/Users/thinh/arco-app/tools')
import compose as c
from compose import (app_slide, hook_slide, mark_hook_used, preflight,
                     record_post_bgs, record_post_tools)

REPO = '/Users/thinh/arco-app'
TOPIC = '4x-productivity-6'
OUT = f'{REPO}/drafts/{TOPIC}'

HOOK = ['the tools i used to', '4x my productivity']
PILLAR = 'tools'
# Four times the work out of the same day is a question about how the day is
# run, not about screen time or a study session, so ARCO answers on planning.
THEME = 'planning'

TOOLS = ['ARCO', 'Antigravity', 'n8n', 'OpusClip', 'ElevenLabs']
TITLES = ['1. ARCO: Day Planner & Focus', '2. Antigravity', '3. n8n',
          '4. OpusClip', '5. ElevenLabs']

# Roster order, ARCO first. This is what the hook slide's shelf shows.
SHELF = ['icon-arco.png', 'icon-antigravity.png', 'icon-n8n.png',
         'icon-opusclip.png', 'icon-elevenlabs.png']

# index 0 is the hook, 1..5 are the app slides in order.
BGS = ['bg-h63.jpg',   # 01 hook        desk-led-neon   plain dark shelf zone
       'bg-h33.jpg',   # 02 ARCO        desk-empty-day  band luma 55.8
       'bg-h04.jpg',   # 03 Antigravity lounge-day      band luma 56.4
       'bg-h36.jpg',   # 04 n8n         supercars-dusk  band luma 16.0
       'bg-h28.jpg',   # 05 OpusClip    villa-day       band luma 56.6
       'bg-h09.jpg']   # 06 ElevenLabs  lounge-day      band luma 57.8

GRAD = (0.85, 0.68, 300, 1250)          # app_slide's default
GRAD_DARK = (0.85, 0.42, 300, 1250)     # same ramp, much lower floor
GRADS = {}

# Angle v12 from arco_angles.json, written out literally rather than drawn
# from next_arco_angle(THEME) at render time: the rotating call moves the
# pointer, so a rebuild would come back with different copy and `--only 02`
# could not redo the slide that shipped.
ARCO_BODY = [
    'Tasks without a time wait in Anytime',
    'until the day has room for them.',
    '',
    'Focus mode blocks the apps I chose',
    'for exactly that block.',
    '',
    'My holy grail.',
]

BODY = {
 'ARCO': ARCO_BODY,
 'Antigravity': [
    'The agent manager runs several',
    'agents at once on separate tasks.',
    '',
    'You come back to three jobs finished',
    'in the time one prompt used to take.',
 ],
 'n8n': [
    'Pin a step and n8n keeps its output',
    'as you build the rest of the run.',
    '',
    'You test step nine on real data',
    'without firing the trigger again.',
 ],
 'OpusClip': [
    'It tracks the speaker and moves the',
    'crop, so a wide take goes vertical.',
    '',
    'One recording comes back as ten',
    'clips, captions already burned in.',
 ],
 'ElevenLabs': [
    'Dubbing translates the video and',
    'keeps your own voice speaking it.',
    '',
    'The same recording goes out in',
    'Spanish without recording again.',
 ],
}


def band_luma(bg):
    """copy_band_luma, but measured with the gradient this slide will use.

    compose.copy_band_luma hardcodes the default gradient, so it would gate
    these frames on a render that never happens.
    """
    im = c.base_photo(bg, GRADS.get(bg, GRAD_DARK))
    im = c.frame_for_band(im, 600, 1300)
    c.adaptive_scrim(im, 600, 1300)
    g = im.convert('L').crop((85, 980, 1000, 1310))
    px = list(g.getdata())
    return sum(px) / len(px)


def main(only=None):
    os.makedirs(OUT, exist_ok=True)

    preflight(TOPIC, TOOLS, BGS, pillar=PILLAR, hook=HOOK)
    for bg in BGS[1:]:
        luma = band_luma(bg)
        if luma > c.BAND_MAX_LUMA:
            raise SystemExit(f'{bg} copy band is {luma:.1f}, over '
                             f'{c.BAND_MAX_LUMA}')

    if only in (None, 1):
        # Log the frame this post actually renders. pick_hook_bg gives unused
        # hook-only vibes priority over `prefer` and would hand back a
        # different background, burning one frame unused.
        path = f'{c.SP}/hook_usage.json'
        log = json.load(open(path))
        if BGS[0] not in log:
            log.append(BGS[0])
            json.dump(log, open(path, 'w'), indent=1)
        hook_slide(BGS[0], HOOK, f'{OUT}/01.jpg', icons=SHELF)
        import hook_rules
        if not any(e.get('topic') == TOPIC for e in hook_rules.history()):
            mark_hook_used(HOOK, TOPIC)

    icons = json.load(open(c.TOOL_POOL))['icons']
    for i, tool in enumerate(TOOLS):
        n, bg = i + 1, BGS[i + 1]
        if only not in (None, n + 1):
            continue
        app_slide(bg, icons[tool], TITLES[i], BODY[tool],
                  f'{OUT}/{n+1:02d}.jpg', grad=GRADS.get(bg, GRAD_DARK))
        print(f'  {bg}  {c.VIBES.get(bg):18s} band luma {band_luma(bg):.1f}')

    if only is None:
        # record_post_bgs de-dupes on topic; record_post_tools and
        # hook_rules.record append blindly, so a rebuild would log this post
        # twice and push an unrelated hook further down its cooldown.
        if not any(e.get('topic') == TOPIC for e in c.tool_history()):
            record_post_tools(TOPIC, TOOLS)
        record_post_bgs(TOPIC, BGS)
    print('\nbackgrounds:', ', '.join(BGS))


if __name__ == '__main__':
    n = None
    if '--only' in sys.argv:
        n = int(sys.argv[sys.argv.index('--only') + 1])
    main(n)
