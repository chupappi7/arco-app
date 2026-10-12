#!/usr/bin/env python3
"""work-by-noon-12: tools pillar in the photo look (_tools_photo).

  request   Thinh, 2026-10-12: a five-app listicle, all five slides the same
            treatment, icon, number and name, two lines over a photo, never
            the phone-mockup screens format. ARCO is titled App Blocker &
            Focus: ARCO and gets the same app_slide as the rest.
  hook      "the tools i use to do / a full day of work by noon", from
            hook_rules.eligible(pillar='tools'), word for word.
  roster    ARCO, Gemini, Superwhisper, Linear, Sentry. Gemini is the one LLM, rotated across the
            2026-10-12 batch.
  answers   the hook promises a day finished by noon, so every point is work already done when the morning starts: an email summary waiting at 7, the walk's voice memo already text, the monday checks already on the list, a failed overnight job flagged at 8.
  ARCO      angle v15, drawn once with next_arco_angle('planning') and
            frozen below.
  teaching  every tool point checked against the captions in tools/hooks.json.
  photos    hook frame least recently used as a hook; app frames under
            BAND_MAX_LUMA, no desk frame, no hook-only vibe, at most one
            person, no adjacent vibe, nothing shared with the post before.

Usage: python3 tools/gen-work-by-noon-12.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='work-by-noon-12',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=[
         'bg-h50.jpg',    # hook
         'bg-h45.jpg',    # ARCO
         'bg-h88.jpg',    # Gemini
         'bg-h20.jpg',    # Superwhisper
         'bg-h29.jpg',    # Linear
         'bg-h21.jpg',    # Sentry
    ],
    arco=['Habits repeat into the day and take', 'their own slot on the timeline.', '', 'The plan is half built before I open', 'it. Focus mode guards each block.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Gemini scheduled actions run a prompt at the time you set and send the result.',
          'A summary of your unread email is waiting at 7am, before you open Gmail.']),
        ('Superwhisper',
         ['Drop an audio file into Superwhisper and it transcribes it on your Mac.',
          'The voice memo from your walk is text before you sit down at the desk.']),
        ('Linear',
         ['A Linear recurring issue creates itself on the schedule you set.',
          'The Monday checks are on the list before you open the app.']),
        ('Sentry',
         ['Sentry cron monitors alert you when a scheduled job did not run on time.',
          'A broken nightly backup is an alert at 8am, not a surprise a week later.']),
    ])
