#!/usr/bin/env python3
"""work-by-noon-9: tools pillar in the screens look (_tools_screens).

  request   Thinh, 2026-10-04: ship-weekend-screens format for tools posts,
            "arco focus" search CTA on the card.
  hook      "the tools i use to do / a full day of work by noon", the
            strongest eligible tools hook by median views (1575 over five
            outings) in hook_rules.eligible(pillar='tools').
  roster    ARCO, Gemini, Notion, ClickUp. Gemini is the LLM: least recently
            used model with Perplexity, Claude, Codex and Manus in the last
            five tools posts.
  teaching  each checked against every caption in tools/hooks.json:
            ARCO     Plan your day: a habit can be stepped to another time for
                     today only ("Just this once", PlanDayPrototypeView), or
                     flipped to become its usual time. Moves the gym out of
                     the morning without rewriting the habit.
            Gemini   Canvas turns a finished doc into a web page from its
                     Create menu (burned: deep research, audio overview, gems,
                     chrome tabs, video, mail and files, live screen share).
            Notion   @remind with a time inside a page sends a notification
                     then (burned: automations, templates, synced blocks,
                     rollups, forms, mail, calendar, clipper, sites, AI).
            ClickUp  time estimate beside tracked time on the task (burned:
                     multiple lists, list email, docs to tasks, automations,
                     dependencies, clips, recurring, views).
  ARCO card angle drawn once with next_arco_angle('planning') and frozen.
  photos    _veiled_screens.pick_bgs, then frozen.

Usage: python3 tools/gen-work-by-noon-9.py [slide numbers to redo]
"""
import sys
from _veiled_screens import PLAN_DAY
from _tools_screens import build

build(
    topic='work-by-noon-9',
    hook=['the tools i use to do', 'a full day of work by noon'],
    theme='planning',
    bgs=['bg-h05.jpg',   # hook     lounge-day
         'bg-h21.jpg',   # ARCO     lounge-night
         'bg-h22.jpg',   # Gemini   lounge-day
         'bg-h24.jpg',   # Notion   lounge-night
         'bg-h29.jpg',   # ClickUp  supercars-dusk
         'bg-h31.jpg'],  # card     lounge-night
    arco=(PLAN_DAY, 'The gym moves out of the morning.',
          'Open a habit in Plan your day and step it to 13:00. Just this '
          'once moves it today only. Tomorrow it is back at 09:00.'),
    tools=[
        ('Gemini', 'A doc turns into a site.',
         ['Write the update in Canvas, then pick Web page from the Create menu.',
          'The client opens one link instead of scrolling ten pages.']),
        ('Notion', 'The page reminds you.',
         ['Type @remind tomorrow 9am anywhere in a page.',
          'Notion pings you at 9 with that page open, so the follow up '
          'sits next to the notes it needs.']),
        ('ClickUp', 'Estimates meet the clock.',
         ['Give a task an estimate and start its timer.',
          'The task shows 2h estimated against 40m tracked, so tomorrow '
          'gets planned on real numbers.']),
    ],
    closer=['Habits repeat into the day and take their own slot.',
            'The plan is half built before I open it.',
            'Focus mode guards each block. My holy grail.'],
    only={int(a) for a in sys.argv[1:]} or None)
