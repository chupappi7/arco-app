#!/usr/bin/env python3
"""4x-productivity-12: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-07: a tools post is a five-app listicle with every
            slide in the same visual language, icon, number and name, two
            lines, over a photo. ARCO is one of the five and gets the same
            app_slide as the rest, titled App Blocker & Focus: ARCO. No phone
            mockup anywhere.
  hook      "the tools i used to / 4x my productivity", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Claude, ElevenLabs, Figma, Sentry. Claude is the one LLM, rotated across the
            2026-10-07 photo batch.
  answers   the hook promises a multiplier, so every point takes out a job that eats time without producing anything: re-explaining context, replaying audio, renaming layers, checking the site by hand.
  ARCO      angle v10, drawn once with next_arco_angle('planning') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame from those never used on a hook; app frames under
            BAND_MAX_LUMA, no desk frame (their monitors and chairs sit
            behind the copy), no hook-only vibe, at most one person, no adjacent
            vibe, nothing shared with the post before.

Usage: python3 tools/gen-4x-productivity-12.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='4x-productivity-12',
    hook=['the tools i used to', '4x my productivity'],
    theme='planning',
    bgs=[
         'bg-h11.jpg',    # hook
         'bg-h88.jpg',    # ARCO
         'bg-h31.jpg',    # Claude
         'bg-h35.jpg',    # ElevenLabs
         'bg-n01.jpg',    # Figma
         'bg-h45.jpg',    # Sentry
    ],
    arco=['I manage all my tasks here and plan', 'the day in 30 seconds.', '', 'Focus mode puts every distraction', 'away.', '', 'The one I actually open every day.'],
    tools=[
        ('Claude',
         ['Ask Claude what you decided in last week’s chat and it searches your past conversations.',
          'You pick up where you left off without scrolling back or explaining it again.']),
        ('ElevenLabs',
         ['Scribe transcribes an hour of audio with every speaker labelled and timestamped.',
          'The interview becomes quotes you can search before you would have replayed it once.']),
        ('Figma',
         ['Select a frame and Figma AI renames every Frame 1847 layer by what it is.',
          'The file is ready to hand off without an afternoon of tidying.']),
        ('Sentry',
         ['Sentry Uptime checks your site on a schedule and alerts you when it goes down.',
          'You hear about the outage before a user has to tell you.']),
    ])
