#!/usr/bin/env python3
"""home-screen-five: the home screen as an argument, not a list of favourites.

  hook    "the 5 apps on my home screen / everything else is in a folder",
          new to hook_pool 2026-10-31 (pillar tools, theme focus).
  lens    why it earns a place on the home screen. A home screen slot is paid
          for in taps per day, so every payoff is about the moment of
          reaching -- speed, or being there before the impulse passes. A
          feature that is merely good does not earn a slot.
  roster  phone apps only. Raycast, CleanShot X and Granola are Mac tools and
          cannot sit on a home screen, which is why they are not here.
          ChatGPT is the one LLM.
  ARCO    angle a8: the block on the Lock Screen with the time left running.
          It is the only angle about the phone's own front surface, which is
          the argument the hook is making.
"""
from _tools_photo import main

main(
    topic='home-screen-five',
    hook=['the 5 apps on my home screen', 'everything else is in a folder'],
    theme='focus',
    bgs=['bg-n09.jpg',   # hook         desk-led-neon      luma 79
         'bg-h51.jpg',   # ARCO         desk-city-day      luma 60
         'bg-n06.jpg',   # ChatGPT      desk-empty-day     luma 55
         'bg-h49.jpg',   # Obsidian     desk-city-day      luma 58
         'bg-h39.jpg',   # Endel        supercars-dusk     luma 32
         'bg-n04.jpg'],  # CapCut       villa-day          luma 54
    arco=['The block I am in sits on the Lock',
          'Screen with the time left running.', '',
          'I pick the phone up and it tells me', 'to get back to work.', '',
          'My holy grail.'],
    tools=[
        ('ChatGPT',
         ['Voice mode answers while the screen is still in your hand and your thumb is nowhere.',
          'You ask the question in the three seconds you have, instead of losing it.']),
        ('Obsidian',
         ['Obsidian keeps every note as a plain file on the phone itself, with no sign in.',
          'The thought gets written down before the lift doors open or the signal returns.']),
        ('Endel',
         ['One tap starts the soundscape, with no playlist to choose and nothing to set up.',
          'The session begins in the second before you could talk yourself out of it.']),
        ('CapCut',
         ['CapCut cuts, captions and exports the whole clip on the phone that filmed it.',
          'The video is posted from the street instead of waiting for you to reach a desk.']),
    ])
