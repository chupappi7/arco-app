#!/usr/bin/env python3
"""wish-i-knew-at-17-11: tools pillar in the photo look (_tools_photo).

  hook      "5 apps i wish someone / showed me at 17", from the approved pool, word for word.
  theme     study -- hook_pool.json binds it, so ARCO's slide answers the
            question slide one asked rather than a theme chosen by hand.
  lens      every tool point answers: what it would have saved you at seventeen
  roster    Perplexity, ClickUp, CapCut, Figma. One LLM, no seller tooling.
  ARCO      angle drawn once with next_arco_angle('study') and frozen below,
            because drawing it here would rotate the pool on every rebuild.
  photos    hook frame unused on any hook; app frames under BAND_MAX_LUMA
            measured with the blur applied, no adjacent vibe repeat, nothing
            shared with the post before.

Usage: python3 tools/gen-wish-i-knew-at-17-11.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='wish-i-knew-at-17-11',
    hook=['5 apps i wish someone', 'showed me at 17'],
    theme='study',
    bgs=[
        'bg-h40.jpg',    # hook
        'bg-h19.jpg',    # ARCO
        'bg-h39.jpg',    # Perplexity
        'bg-h51.jpg',    # ClickUp
        'bg-h01.jpg',    # CapCut
        'bg-h21.jpg',    # Figma
    ],
    arco=['Focus mode puts every distracting', 'app away for the whole session.', '', 'An hour of work is an hour now, not', 'forty minutes and a scroll.', '', 'I get the time back.'],
    tools=[
        ('Perplexity',
         ['Perplexity answers with the sources listed underneath the answer.',
          'At seventeen I would have learned to check a claim instead of repeating it.']),
        ('ClickUp',
         ['ClickUp holds every assignment with its due date in one list you can sort.',
          'The deadline I missed because it lived on a different app would not have.']),
        ('CapCut',
         ['CapCut cuts, captions and exports a vertical video entirely on the phone.',
          'You can learn to edit without owning a computer that can run an editor.']),
        ('Figma',
         ['Figma is free for one person and every real design file opens in the browser.',
          'You learn by taking apart work that shipped, not by reading about it.']),
    ])
