#!/usr/bin/env python3
"""already-deleted: deleting the app failed, so answer why it failed.

  hook    "you already tried deleting the app / try these 5 instead", new to
          hook_pool 2026-10-31 (pillar screentime, theme discipline).
  lens    what it does that deleting the app did not. The viewer has already
          run the experiment and lost, so every step closes one of the four
          ways a deletion gets undone: the browser, the reinstall, the saved
          login, the thumb.
  ARCO    angle a3 (the shield meets the reflex). Deleting removes the app and
          leaves the reflex; a3 is the only angle that addresses the reflex
          itself, which is exactly the gap the hook names.
  count   ARCO plus four rules is the five the hook promises.
"""
from _screentime_common import build

build(
    topic='already-deleted',
    hook=['you already tried deleting the app', 'try these 5 instead'],
    bgs=['bg-h57.jpg',   # hook         desk-led-warm      luma 29
         'bg-h49.jpg',   # ARCO         desk-city-day      luma 58
         'bg-h39.jpg',   # 2            supercars-dusk     luma 32
         'bg-h50.jpg',   # 3            desk-city-day      luma 64
         'bg-h38.jpg',   # 4            supercars-dusk     luma 20
         'bg-h46.jpg'],  # 5            desk-city-day      luma 62
    arco_lines=['Every time I open TikTok the shield',
                'comes up instead of the feed.', '',
                'The reflex still happens, it just',
                'turns into a reminder to lock in.', '',
                'That is the whole app.'],
    rules=[
        ('The browser is the back door', [
            'Block the site itself in Content',
            'Restrictions, not just the app.', '',
            'Deleting the app leaves the feed',
            'one Safari tab away.']),
        ('Someone else holds the passcode', [
            'Set a Screen Time passcode and let',
            'a friend pick the four digits.', '',
            'Reinstalling takes four taps. This',
            'takes a conversation.']),
        ('Log out before you delete', [
            'Sign out and clear the saved',
            'password first, then remove it.', '',
            'The reinstall gets you a login',
            'screen instead of your feed.']),
        ('Leave the hole in the grid', [
            'Do not close the gap where the',
            'icon used to sit.', '',
            'Your thumb lands on nothing and',
            'the reach ends there.']),
    ])
