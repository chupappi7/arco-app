#!/usr/bin/env python3
"""deleted-twenty: tools pillar in the photo look (_tools_photo).

  hook      "i deleted 20 apps / these 5 took over", from the approved pool, word for word.
  theme     planning -- hook_pool.json binds it.
  roster    ChatGPT, Notion, CleanShot X, ClickUp. ChatGPT is the one LLM.
  new      written 2026-11-11.
  points    Rule of 2026-11-11 (Thinh): a point may return once 3 weeks have
            passed since it last went out. Checked against every caption
            sent or scheduled within 21 days either side of this post.
  ARCO      angle drawn with next_arco_angle('planning') and frozen below.
  photos    hook frame least recently used as a hook; app frames shuffled
            per post, 3-post cooldown, at most 2 shared with any of the last 10.
  cta       none. Tools and build posts end on the fifth app (Thinh, 2026-11-10).
  test      frequency test week 1, 14-20 Nov.

Usage: python3 tools/gen-deleted-twenty.py [slide numbers to redo]
"""
from _tools_photo import main

main(
    topic='deleted-twenty',
    hook=['i deleted 20 apps', 'these 5 took over'],
    theme='planning',
    bgs=[
        'bg-h69.jpg',    # hook         desk-led-neon
        'bg-h35.jpg',    # ARCO         supercars-dusk
        'bg-n04.jpg',    # ChatGPT      villa-day
        'bg-h37.jpg',    # Notion       supercars-dusk
        'bg-h52.jpg',    # CleanShot X  desk-city-day
        'bg-n01.jpg',    # ClickUp      villa-day
    ],
    arco=['Habits take a real slot on the day,', 'the same as any task.', '', 'Mine lasted past the first month', 'because the day made room for it.', '', 'That is why they finally stuck.'],
    tools=[
        ('ChatGPT',
         ['Connect Google Drive and ChatGPT answers from your own files.',
          'The separate search tool for your documents goes.']),
        ('Notion',
         ['Notion Forms send every answer straight into a database.',
          'The form app and the copy into a table both go.']),
        ('CleanShot X',
         ['CleanShot X records the screen as a video or a GIF and shows your clicks and keys.',
          'One app covers screenshots and screen recordings.']),
        ('ClickUp',
         ['In a ClickUp Doc, any line becomes a task with one click.',
          'Notes and tasks stop living in two different apps.']),
    ],
)
