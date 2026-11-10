#!/usr/bin/env python3
"""wish-i-knew-at-17-12: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i wish someone / showed me at 17", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it.
  lens      every tool point answers: what it would have saved you at seventeen
  roster    Gemini, Notion, Canva, GitHub. Gemini is the one LLM. Points not
            taught before: Gemini Guided Learning, the Notion web clipper,
            Canva charts from a pasted table, GitHub Skills courses.
  ARCO      angle drawn once with next_arco_angle('study') and frozen below.
  photos    pick_bgs from gen-daily-batch on 2026-11-10.
  cta       none. Tools and build posts end on the fifth app: ARCO reads as
            one recommendation among peers, and the ask drew 2 comments on
            ~10.6k views (27 Oct - 9 Nov). Thinh, 2026-11-10.

Usage: python3 tools/gen-wish-i-knew-at-17-12.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-12',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
        'bg-h32.jpg',    # hook     window-silhouette
        'bg-h02.jpg',    # ARCO     lounge-day
        'bg-h31.jpg',    # Gemini   lounge-night
        'bg-h34.jpg',    # Notion   desk-empty-day
        'bg-h35.jpg',    # Canva    supercars-dusk
        'bg-h46.jpg',    # GitHub   desk-city-day
    ],
    arco=['Focus mode blocks every app on my', 'list for the whole session.', '', 'The phone stops being a decision', 'while the timer runs.', '', 'My holy grail.'],
    tools=[
        ('Gemini',
         ['Gemini Guided Learning breaks a topic into steps and checks each one before moving on.',
          'You finish the chapter able to explain it, not just holding the answer.']),
        ('Notion',
         ['The Notion web clipper saves any article into a database with its link attached.',
          'Research for an essay sits in one place instead of forty open tabs.']),
        ('Canva',
         ['Paste a table into a Canva chart and it draws the graph in the style of the deck.',
          'A class presentation stops being a screenshot of a spreadsheet.']),
        ('GitHub',
         ['GitHub Skills runs free courses inside a repo of your own and checks each step you push.',
          'You learn git by making real commits, not by watching a video about it.']),
    ],
)
