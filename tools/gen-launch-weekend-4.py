#!/usr/bin/env python3
"""launch-weekend-4: build pillar in the photo look (_tools_photo, pillar='build').

  hook      "launch an app / in one weekend", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  lens      every tool point answers: the launch step it handles. Check the
            code (Codex), take money (Stripe), guard the waitlist
            (Cloudflare), hear from users (PostHog).
  roster    Codex is the one LLM. Points not taught before: Codex /review,
            Apple Pay on Stripe Checkout, Cloudflare Turnstile, PostHog
            surveys.
  ARCO      angle drawn once with next_arco_angle('build') and frozen below.
  photos    pick_bgs from gen-daily-batch on 2026-11-10 with BG_COOLDOWN
            raised to 3, so it shares no frame with ship-weekend-6.
  cta       none. Tools and build posts end on the fifth app: ARCO reads as
            one recommendation among peers, and the ask drew 2 comments on
            ~10.6k views (27 Oct - 9 Nov). Thinh, 2026-11-10.

Usage: python3 tools/gen-launch-weekend-4.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='launch-weekend-4',
    hook=['launch an app', 'in one weekend'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h44.jpg',    # hook        window-silhouette
        'bg-h04.jpg',    # ARCO        lounge-day
        'bg-h38.jpg',    # Codex       supercars-dusk
        'bg-h48.jpg',    # Stripe      desk-city-day
        'bg-n01.jpg',    # Cloudflare  villa-day
        'bg-n05.jpg',    # PostHog     desk-empty-day
    ],
    arco=['The block I am in sits on the Lock', 'Screen with the time left running.', '', 'I pick the phone up and it tells me', 'to get back to work.', '', 'My holy grail.'],
    tools=[
        ('Codex',
         ['Run /review in Codex and it reads your uncommitted changes the way a reviewer would.',
          'The bug in Saturday’s code gets found before it ships on Sunday.']),
        ('Stripe',
         ['Stripe Checkout shows Apple Pay and Google Pay with no extra code on your side.',
          'The first sale on launch day takes two taps on a phone.']),
        ('Cloudflare',
         ['Cloudflare Turnstile replaces the captcha on your waitlist form for free.',
          'Bots stop filling the list and real people never solve a puzzle.']),
        ('PostHog',
         ['A PostHog survey asks one question inside the product at the moment you pick.',
          'Launch week feedback comes from people using it, not a form nobody opens.']),
    ],
)
