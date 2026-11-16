#!/usr/bin/env python3
"""blow-my-mind: store-card layout (_store_cards), copied from a photo-mode
post Thinh sent on 2026-11-16.

  hook      "Apps for iPhone / That blow my mind", Thinh's pick, word for word.
  roster    ARCO first (Thinh), then Claude, Superwhisper, Endel. Claude is the one LLM.
  shots     ARCO: the in-app Today screen. Others: their own App Store screenshots.

Usage: python3 tools/gen-blow-my-mind.py [slide numbers to redo]
"""
from _store_cards import main

I, S = 'slides/icons/', 'slides/store/'

main(
    topic='blow-my-mind',
    hook_bg='slides/bg/bg-h01.jpg',
    hook=['Apps for', 'iPhone'],
    sub='That blow my mind',
    apps=[
        (I + 'icon-arco.png', 'ARCO',
         'Plan your day as timed blocks, with tasks and habits inline. '
         'Start a focus timer on any block, and it locks TikTok and Instagram '
         'during the hours you set, every day.',
         S + 'arco-today.jpg'),
        (I + 'icon-claude.jpg', 'Claude',
         'Talk a problem through out loud in voice mode, then ask for the result '
         'as a real file: a doc, a deck or a spreadsheet you can send.',
         S + 'claude-files.jpg'),
        (I + 'icon-superwhisper.jpg', 'Superwhisper',
         'Talk instead of typing in any app. Its keyboard turns speech into clean '
         'text with punctuation, so a two-minute ramble becomes a message ready to send.',
         S + 'superwhisper-type.jpg', 64),
        (I + 'icon-endel.jpg', 'Endel',
         'Soundscapes that adapt to the time of day and your heart rate. Start '
         'Focus with a timer and it ends with the session, no playlist to pick.',
         S + 'endel-focus.jpg'),
    ],
)
