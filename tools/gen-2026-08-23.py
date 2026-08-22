#!/usr/bin/env python3
"""Daily batch 2026-08-23: story, study listicle, app demo, deep-work listicle."""
import shutil
import sys
sys.path.insert(0, '/Users/thinh/SIXSIX/arco-app/tools')
from compose import (app_slide, hook_slide, shot_slide, base_photo,
                     draw_text_block, font)

REPO = '/Users/thinh/SIXSIX/arco-app'
RAW = '/Users/thinh/SIXSIX/screenshots/redesign/raw'
import os

def story_slide(bg, para1, para2, out, grad=(0.5, 0.75, 900, 1500)):
    im = base_photo(bg, grad)
    items = []
    f1 = font(62, 'Bold')
    y = 400
    for ln in para1:
        items.append((85, y, ln, f1, 'la', (255, 255, 255)))
        y += 82
    y += 40
    f2 = font(47, 'Semibold')
    for ln in para2:
        items.append((85, y, ln, f2, 'la', (235, 235, 235)))
        y += 64
    draw_text_block(im, items)
    im.save(out, quality=92)
    print('wrote', out)

# ---------- 09: story "phone-another-room" ----------
A = f'{REPO}/drafts/phone-another-room'
os.makedirs(A, exist_ok=True)
hook_slide('src-hook.jpg', ['i left my phone in another room.', 'it lasted two days.'], f'{A}/01.jpg')
story_slide('bg-d13.jpg',
            ['the plan was willpower.'],
            ['check messages once, then work.', 'by tuesday the phone was back', 'on the desk.'],
            f'{A}/02.jpg')
story_slide('bg-d09.jpg',
            ['the problem was never', 'the phone.'],
            ['it was that nothing stopped', 'the first tap.'],
            f'{A}/03.jpg')
story_slide('bg-d11.jpg',
            ['so i scheduled the', 'blocking instead.'],
            ['9 to 12, every weekday,', 'the feeds just do not open.'],
            f'{A}/04.jpg')
story_slide('bg-d12.jpg',
            ['no decision to make at 9am.'],
            ['the window starts, the apps close,', 'work begins.'],
            f'{A}/05.jpg')
story_slide('bg-d06.jpg',
            ['three weeks in: mornings', 'are quiet.'],
            ['it was never about distance.', 'it is about the door being locked.'],
            f'{A}/06.jpg', grad=(0.45, 0.7, 900, 1500))
shutil.copy(f'{REPO}/drafts/btl/07.jpg', f'{A}/07.jpg')
print('wrote', f'{A}/07.jpg')

# ---------- 12: listicle "study-tools" ----------
B = f'{REPO}/drafts/study-tools'
os.makedirs(B, exist_ok=True)
hook_slide('bg-d07.jpg', ['the 5 tools that got me', 'through exam season'], f'{B}/01.jpg',
           grad=(0.4, 0.7, 700, 1300))
app_slide('bg-d03.jpg', 'icon-claude.jpg', '1. Claude',
          ['Explains what the textbook', 'would not. Practice questions,', 'worked examples, endless patience.',
           '', 'Like a tutor on retainer.'], f'{B}/02.jpg', grad=(0.42, 0.72, 1000, 1550))
app_slide('bg-d05.jpg', 'icon-arco.png', '2. ARCO: Day Planner & Focus',
          ['Class times and study blocks on', 'one timeline. Social apps lock', 'during revision hours.',
           '', 'The library, enforced.'], f'{B}/03.jpg', grad=(0.42, 0.72, 1000, 1550))
app_slide('bg-d02.jpg', 'icon-obsidian.jpg', '3. Obsidian',
          ['Notes that link the way the', 'subject actually works. Review', 'gets faster every week.'],
          f'{B}/04.jpg', grad=(0.42, 0.72, 1000, 1550))
app_slide('bg-d04.jpg', 'icon-gcal.jpg', '4. Google Calendar',
          ['Every deadline, seminar and', 'shift in one grid.',
           '', 'Sunday planning, zero surprises.'], f'{B}/05.jpg', grad=(0.42, 0.72, 1000, 1550))
app_slide('bg-d01.jpg', 'icon-endel.jpg', '5. Endel',
          ['Focus sound without lyrics.', 'Headphones on, chapter open,', 'gone.'],
          f'{B}/06.jpg', grad=(0.42, 0.72, 1000, 1550))

# ---------- 18: app demo "one-app-day" ----------
C = f'{REPO}/drafts/one-app-day'
os.makedirs(C, exist_ok=True)
hook_slide('bg-d14.jpg', ['a full day, planned and', 'protected by one app'], f'{C}/01.jpg')
shot_slide(f'{RAW}/Plan.png', 150, ['the night before:', 'tomorrow planned in a minute'], f'{C}/02.jpg')
shot_slide(f'{RAW}/Timeline.png', 150, ['the day runs on one timeline'], f'{C}/03.jpg')
shot_slide(f'{RAW}/BlockedHours.png', 150, ['distracting apps lock on schedule'], f'{C}/04.jpg')
shot_slide(f'{RAW}/Tasks.png', 150, ['projects and priorities,', 'nothing slips'], f'{C}/05.jpg')
hook_slide('bg-d07.jpg', ['the app is ARCO.', 'on the App Store.'], f'{C}/06.jpg',
           grad=(0.4, 0.7, 700, 1300))

# ---------- 21: listicle "deep-work-stack" ----------
D = f'{REPO}/drafts/deep-work-stack'
os.makedirs(D, exist_ok=True)
hook_slide('src-lamp.jpg', ['the stack that finally', 'made deep work stick'], f'{D}/01.jpg')
app_slide('bg-d12.jpg', 'icon-endel.jpg', '1. Endel',
          ['Sound designed for focus.', 'No lyrics, no playlist decisions.',
           '', 'Press play, disappear.'], f'{D}/02.jpg')
app_slide('bg-d11.jpg', 'icon-obsidian.jpg', '2. Obsidian',
          ['One vault for thinking.', 'Ideas link up instead of', 'getting lost in folders.'],
          f'{D}/03.jpg')
app_slide('bg-d10.jpg', 'icon-arco.png', '3. ARCO: Day Planner & Focus',
          ['Timer, day plan and app blocking', 'in one place. The session starts', 'and the exits close.',
           '', 'Hours come back every week.'], f'{D}/04.jpg', grad=(0.45, 0.72, 1000, 1550))
app_slide('bg-d08.jpg', 'icon-claude.jpg', '4. Claude',
          ['The rubber duck that answers', 'back. Unstuck in minutes,', 'not afternoons.'],
          f'{D}/05.jpg', grad=(0.45, 0.72, 1000, 1550))
app_slide('bg-d14.jpg', 'icon-clickup.jpg', '5. ClickUp',
          ['Where the output lands.', 'Tasks closed, projects moving,', 'nothing living in your head.'],
          f'{D}/06.jpg')
