#!/usr/bin/env python3
"""three-hours-back-2: screentime pillar, method post.

The hook promises hours back WITHOUT deleting anything, so every step is a
change to a phone that keeps all its apps: focus mode locks them for a
session, alerts arrive twice a day, YouTube's home feed goes blank, the
phone stops suggesting the feeds, and each feed is signed out but installed.

ARCO copy drawn by next_arco_angle('screentime') on the first build (f1) and
frozen here. Backgrounds picked with the gen-daily-batch walk and frozen.
"""
from _screentime_common import build

build(
    topic='three-hours-back-2',
    hook=['i cut 3 hours of screen time', 'without deleting a single app'],
    bgs=['bg-h71.jpg',   # hook   desk-led-neon
         'bg-h31.jpg',   # ARCO   lounge-night
         'bg-h32.jpg',   # 2      window-silhouette (the one person)
         'bg-h37.jpg',   # 3      supercars-dusk
         'bg-n04.jpg',   # 4      villa-day
         'bg-h35.jpg'],  # 5      supercars-dusk
    # bg-h34 and bg-h46 were the walk's first picks; on the render the copy
    # crossed monitors and a chair edge and the dashes washed out.
    arco_lines=['Focus mode blocks every app on my', 'list for the whole session.', '',
                'The phone stops being a decision', 'while the timer runs.', '',
                'My holy grail.'],
    rules=[
        ('Alerts come twice a day', [
            'Put every feed app in the Scheduled',
            'Summary at noon and 8pm.', '',
            'The pings arrive together, not',
            'forty times across the day.']),
        ('YouTube history is paused', [
            'Pause watch history and the home',
            'feed goes blank.', '',
            'You open it to search one video and',
            'there is nothing else to fall into.']),
        ('No app suggestions', [
            'Turn off Siri suggestions for the',
            'feed apps in Settings, then Siri.', '',
            'The phone stops offering TikTok at',
            'the hour you usually open it.']),
        ('Signed out, still installed', [
            'Log out of each feed on the phone',
            'and keep the app.', '',
            'Opening it now starts at a login',
            'screen instead of a video.']),
    ])
