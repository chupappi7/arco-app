#!/usr/bin/env python3
"""wish-i-knew-at-17-9: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "5 apps i wish someone / showed me at 17", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, ChatGPT, GitHub, CapCut, Obsidian. ChatGPT is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook is what a 17 year old should have been shown, so every point lands on that age: the first interview rehearsed, a portfolio before a CV, the school video cut for every platform, notes that outlive whatever app is popular.
  ARCO      angle l1, drawn once with next_arco_angle('study') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-wish-i-knew-at-17-9.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-9',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
         'bg-h70.jpg',    # hook
         'bg-h22.jpg',    # ARCO
         'bg-h24.jpg',    # ChatGPT
         'bg-h29.jpg',    # GitHub
         'bg-h32.jpg',    # CapCut
         'bg-h36.jpg',    # Obsidian
    ],
    arco=['I put the study block in and the', 'distracting apps close with it.', '', 'The session ends when the timer', 'does, not when I give in.', '', 'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['ChatGPT voice mode runs a mock interview out loud and asks follow up questions.',
          'Your first real interview is the second time you have answered them.']),
        ('GitHub',
         ['A repo named after your username becomes the front page of your GitHub profile.',
          'Your projects read as a portfolio anyone can open, before you have a CV.']),
        ('CapCut',
         ['CapCut auto reframe keeps the subject centred when a wide clip goes to 9:16.',
          'One school project video fits TikTok and YouTube from a single edit.']),
        ('Obsidian',
         ['Obsidian saves every note as a plain text file in a folder you own.',
          'Notes you start at 17 still open in any app at 30, with no account to lose.']),
    ])
