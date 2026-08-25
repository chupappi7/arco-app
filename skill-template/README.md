# TikTok slideshow pipeline, skill template

A Claude Code skill that drafts TikTok photo-carousel posts and delivers them
to one or more accounts as inbox drafts, through the official Content Posting
API. You review and publish manually in the app.

This is the **template**: all the machinery and the rules, none of anyone's
taste. It interviews you on first run and writes your answers into
`examples.md`, which it then uses as its calibration set.

## Install

```bash
cp -R tiktok-pipeline ~/.claude/skills/
```

Then open Claude Code in your project and say `/tiktok-pipeline calibrate`.

## What happens on first run

1. **Calibration** (`calibration.md`), it asks you for your app's approved
   line, three hooks in your own words, one hook you would never post, one
   example slide body, your tool pool and your content pillars. That becomes
   `examples.md`.
2. **Setup** (`setup.md`), TikTok developer app, sandbox, target users, OAuth
   token minting, GitHub Pages hosting.
3. **Backgrounds** (`backgrounds.md`), generate or supply images, ingest them
   into a tagged pool.
4. **Draft**, it renders a post, shows you every slide, and waits for your go
   before anything reaches TikTok.

## What you need

- A public GitHub repo with Pages enabled (images must be publicly fetchable
  for the API to pull them).
- A TikTok developer app in Sandbox mode with Login Kit and Content Posting
  API, and each target account added as a sandbox target user.
- macOS for the fonts (`SFNS.ttf`), swap the font path in `compose.py` on
  other platforms.
- Python with Pillow, and Node for the delivery scripts.

## Hard limits worth knowing before you start

- **Five pending drafts per account per rolling 24 hours.** Only publishing
  frees a slot; deleting a draft does not. At four posts a day you must claim
  and publish daily or the pipeline jams.
- Drafts are drafts. Publishing stays manual, which is also the quality gate.
- A brand new TikTok account will reject deliveries with
  `app_version_check_failed` until it has been used like a human on a real
  phone for about a day.

## Layout

```
tiktok-pipeline/
  SKILL.md          entry point and the 14 critical rules
  calibration.md    first-run interview (run this first)
  examples.md       your approved and rejected copy (starts empty)
  setup.md          TikTok developer app, OAuth, tokens
  backgrounds.md    images, prompts, icon sourcing
  content.md        formats, layout specs, copy rules
  operations.md     delivery, errors, accounts, scheduling
  tools/
    compose.py          slide rendering and every build-time guard
    ingest_bg.py        crop, downscale and quality-gate images
    map_bg_sources.py   map pooled backgrounds to their sources by hash
    sync_bg.py          retire backgrounds deleted upstream
    autopost.js         deliver a post to an account
    tiktok-auth.js      OAuth token minting
    app_angles.json     your app's approved line and its variations
    tool_pool.json      approved tools and verified icon filenames
    hooks.json          post registry
```

## Licence

Do what you like with it.
