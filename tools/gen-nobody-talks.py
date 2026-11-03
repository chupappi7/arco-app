#!/usr/bin/env python3
"""nobody-talks: four tools that hold up a part of the day without being named.

  hook    "nobody talks about these 5 apps / and they run my whole day", new
          to hook_pool 2026-10-31 (pillar tools, theme planning).
  lens    the part of the day it quietly runs. Each payoff names a specific
          stretch -- the research hour, the afternoon of calls, the first
          draft, the evening admin -- because "runs my whole day" is a claim
          about coverage, and a roster of vague wins does not make it.
  roster  the hook rules out the obvious picks, so no Claude, Notion or
          Figma here. Manus is the one LLM.
  ARCO    angle v14: the plan and the block that protects it in one app. It
          is the planning angle that is about running a day rather than
          about a single feature.
"""
from _tools_photo import main
from _veiled_screens import TIMELINE

main(
    topic='nobody-talks',
    hook=['nobody talks about these 5 apps', 'and they run my whole day'],
    theme='planning',
    bgs=['bg-n08.jpg',   # hook         desk-led-neon      luma 55
         'bg-h31.jpg',   # ARCO         lounge-night       luma 20
         'bg-h29.jpg',   # Manus        supercars-dusk     luma 21
         'bg-h24.jpg',   # Granola      lounge-night       luma 48
         'bg-h52.jpg',   # Superwhisper desk-city-day      luma 64
         'bg-n05.jpg'],  # n8n          desk-empty-day     luma 51
    arco=['One app holds the plan and the', 'block that protects it.', '',
          'Tasks get a time on the timeline and',
          'Focus mode shuts the apps for it.', '', 'My holy grail.'],
    tools=[
        ('Manus',
         ['Manus works a task through its own browser session and hands back the finished file.',
          'The research hour you keep postponing is done while you are sitting in a meeting.']),
        ('Granola',
         ['Granola writes the meeting notes from your Mac audio with no bot joining the call.',
          'An afternoon of calls leaves behind notes that you never had to take.']),
        ('Superwhisper',
         ['Superwhisper turns speech into text on device, straight into whatever app has focus.',
          'The first draft of anything happens at talking speed instead of typing speed.']),
        ('n8n',
         ['n8n runs your automations on your own machine rather than a metered cloud account.',
          'The admin that used to take an evening a week now runs while you are asleep.']),
    ],
    cta=(TIMELINE,
         'Comment \u201cARCO\u201d.',
         'I will send the blocks and the schedule I use. '
         'Or search \u201carco focus\u201d on the App Store.'))
