#!/usr/bin/env python3
"""launch-weekend-5: build pillar in the photo look (_tools_photo).

  hook      "how i ship in a weekend / what used to take a month", from the approved pool, word for word.
  theme     build -- hook_pool.json binds it.
  roster    Codex, GitHub, Figma, Framer. Codex is the one LLM.
  re-shoot of launch-weekend-2, a top performer, on new frames.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('build') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-launch-weekend-5.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='launch-weekend-5',
    hook=['how i ship in a weekend', 'what used to take a month'],
    theme='build',
    pillar='build',
    bgs=[
        'bg-h77.jpg',    # hook         desk-led-neon
        'bg-h88.jpg',    # ARCO         supercars-dusk
        'bg-h04.jpg',    # Codex        lounge-day
        'bg-n01.jpg',    # GitHub       villa-day
        'bg-h32.jpg',    # Figma        window-silhouette
        'bg-h39.jpg',    # Framer       supercars-dusk
    ],
    arco=['Every task I have is in here and the', 'day gets planned in 30 seconds.', '', 'Focus mode puts every distraction', 'away while I work.', '', 'My holy grail.'],
    tools=[
        ('Codex',
         ['Write one setup script and Codex runs it before every cloud task.',
          'Every job starts in a project that already builds and tests.']),
        ('GitHub',
         ['Mark a repo as a template and one click copies the whole setup.',
          'The next app starts with CI, lint and folders already in place.']),
        ('Figma',
         ['Add 1x, 2x and 3x export settings to a frame and export once.',
          'Every icon and screenshot size comes out in one go.']),
        ('Framer',
         ['A form block stores submissions in the site with no backend.',
          'The waitlist is live on the landing page saturday night.']),
    ],
)
