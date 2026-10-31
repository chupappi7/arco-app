#!/usr/bin/env python3
"""twelve-apps-8: i pay for 12 apps / these 5 do all the work.

  hook    from hook_rules.eligible(pillar=...), word for word.
  lens    the work it absorbs that another subscription was doing.
          Every point after ARCO answers it; that is not enforced by
          any guard, only printed, so it is checked here by hand.
  ARCO    angle v15 [planning,build,business], drawn once and frozen
          below so a rebuild cannot rotate it.
  photos  allocated across the whole batch: copy band under 65 rather
          than the guard's 80, no frame twice in one post, nothing
          shared with the post before.
"""
from _tools_photo import main

main(
    topic='twelve-apps-8',
    hook=['i pay for 12 apps', 'these 5 do all the work'],
    theme='business',
    bgs=['bg-h58.jpg',   # hook         desk-led-warm      luma 54
         'bg-n04.jpg',   # ARCO         villa-day          luma 54
         'bg-h45.jpg',   # Perplexity   window-silhouette  luma 50 (the one person)
         'bg-h37.jpg',   # Canva        supercars-dusk     luma 23
         'bg-h34.jpg',   # Supabase     desk-empty-day     luma 61
         'bg-h36.jpg'],  # Vercel       supercars-dusk     luma 24
    arco=['Every task has a time and the block',
          'that protects it is the same app.', '',
          'I stopped running a planner and a',
          'blocker that knew nothing about', 'each other.', '',
          'One app, one day.'],
    tools=[
        ('Perplexity',
         ['Perplexity aims a search at academic papers or one site alone and cites what it used.',
          'That is the research tool and the citation manager arriving on one bill.']),
        ('Canva',
         ['Canva resizes a single design into every format a platform asks for in one click.',
          'It took over the thumbnail tool and the slide deck tool at the same time.']),
        ('Supabase',
         ['Supabase gives you a database, auth and file storage behind one project.',
          'Three services you were paying for separately now sit on one free tier.']),
        ('Vercel',
         ['Vercel builds the site, hosts it and gives every branch its own preview URL.',
          'The host, the CI runner and the staging server stopped being three bills.']),
    ])
