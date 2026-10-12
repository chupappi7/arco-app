#!/usr/bin/env python3
"""pay-for-twelve-7: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "i pay for 12 apps / these 5 do all the work", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Manus, Higgsfield, Supabase, ElevenLabs. Manus is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook says five apps do the work of twelve, so every point retires another bill: an internal tool you own instead of rent, two video models in one plan, login with no auth service, music with no stock library.
  ARCO      angle v1, drawn once with next_arco_angle('business') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-pay-for-twelve-7.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='pay-for-twelve-7',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='business',
    bgs=[
         'bg-h53.jpg',    # hook
         'bg-h32.jpg',    # ARCO
         'bg-h36.jpg',    # Manus
         'bg-n04.jpg',    # Higgsfield
         'bg-h38.jpg',    # Supabase
         'bg-h22.jpg',    # ElevenLabs
    ],
    arco=['I manage all my tasks here and plan', 'the day in 30 seconds.', '', 'Focus mode puts every distraction', 'away.', '', 'My holy grail.'],
    tools=[
        ('Manus',
         ['Manus builds a full web app with its own database and login from one prompt.',
          'The internal tool you were paying for monthly becomes one you own.']),
        ('Higgsfield',
         ['Higgsfield runs Veo and Kling from the same prompt box.',
          'You test one shot on two video models without paying for two subscriptions.']),
        ('Supabase',
         ['Supabase Auth covers 50,000 monthly active users on the free plan.',
          'Login, magic links and Sign in with Apple need no separate auth bill.']),
        ('ElevenLabs',
         ['ElevenLabs writes a music track from a prompt, licensed for commercial use on paid plans.',
          'The background music for an ad needs no stock music subscription.']),
    ])
