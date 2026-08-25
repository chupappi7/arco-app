# Backgrounds: getting and managing the image pool

Slides are white text over photographs. The photograph is the composition;
the text is a caption on it. Everything here exists so the text stays
readable and the feed stops looking templated.

## Where images come from

Two routes, and they end in the same place:

1. **Generate them** (the source pipeline used Higgsfield; any 9:16 image
   model works). Generate in the web app if the user has an unlimited plan --
   **an MCP integration usually bills credits per image even when the web app
   is unlimited.** Check before generating hundreds.
2. **The user supplies their own photos.** Same pipeline, same rules.

Either way, run every image through `tools/ingest_bg.py`, which crops to 9:16,
downscales to 1080x1920, and runs a quality gate that rejects anything too
low-resolution or too flat to hold white text. It keeps a ledger at
`bg/.ingested.txt` so repeat passes are free.

```bash
python3 tools/ingest_bg.py <url-or-path> [...]
python3 tools/ingest_bg.py --ledger        # what has been ingested
```

## Prompt recipe

The four things every prompt needs:

1. **`9:16` / "vertical"**, anything else gets centre-cropped and loses its
   composition.
2. **Somewhere dark for the text.** Say it explicitly: "large dark negative
   space in the upper half for text overlay".
3. **`no text, no watermark`**, generators love inventing signage, and a
   background with baked-in text has to be repaired or thrown away.
4. **A grade.** "moody desaturated", "cinematic", "photorealistic". Without
   it you get stock-photo lighting.

Working prompts from the source pipeline, as a starting point:

```
office in a modern penthouse, glass wall with a view, great setup, 3 monitors,
gaming chair, nighttime, some orange and yellow led lights, more comfy
```
```
Vertical cinematic photo, two supercars parked in front of a modern dark
concrete mansion at dusk, one white one black, moody desaturated grade,
overcast evening, dark sky and building at the top of the frame for text
overlay, photorealistic, no people, no text, no watermark
```
```
Cinematic vertical photo. A man in a tailored dark suit, back to camera,
standing at a floor-to-ceiling penthouse window at dawn overlooking a city
skyline. Very dark moody colour grade, deep blacks, subtle warm amber rim
light. Large dark negative space in the upper half for text overlay. Face not
visible. No text, no watermarks. 35mm, shallow depth of field.
```
```
luxury modern villa, view to pool, cool sunny weather but not too orange,
vibrant theme
```

> **Add your own here.** Paste the prompt that produces your look and delete
> the ones above. The aesthetic should be the user's, not this template's.

## The rules that matter

**App slides need dark backgrounds.** An app slide carries five lines of white
body copy. Daylight scenes wash it out no matter how hard the scrim pushes,
and it is unreadable on a phone. Only the hook survives a bright background,
because it is two short lines. Keep app slides on night desks, dusk
exteriors, silhouettes, lamp-lit rooms.

**At most one background with a person per post.** Two photos of a person at a
desk in one carousel reads as stock imagery. Prefer empty rooms.
`compose.assert_one_person()` enforces it.

**No two adjacent slides share a vibe.** A night LED desk followed by another
night LED desk reads as one long slide; the eye needs a scene change between
cards. Tag every background in `bg/manifest.json` with a vibe
(`lounge-day`, `desk-led-neon`, `supercars-dusk`, ...) and call
`compose.assert_varied([...backgrounds in slide order...])` before saving.

**Never repeat a hook background until the pool is exhausted.** The hook
decides the scroll, so it must never look familiar. `compose.pick_hook_bg()`
tracks usage in `bg/hook_usage.json` and resets when every background has been
used once.

**The background is decoration, not argument.** Any good photo works; it does
not have to illustrate the hook. Never write a hook claiming a generated scene
is the user's own place -- it is an AI image and the claim is false.

## When the user deletes images upstream

Backgrounds are stored permanently in the repo, so deleting a generation in
the web app does not reach the pool and the deleted image keeps appearing.

```bash
python3 tools/map_bg_sources.py <every live rawUrl>   # builds bg/.sources.json
python3 tools/sync_bg.py --yes                        # retires the orphans
```

`map_bg_sources.py` re-renders each live source through the ingest pipeline
and matches md5s, which gives an exact `bg-hNN -> source` mapping. **Do not
map by ledger position**: the ledger records rejected images as well as
accepted ones, so index N is not `bg-hN`. Getting this wrong retires the wrong
files, silently.

## Icons

Each tool slide needs a square app icon. Source them in this order, and
**look at every one before it ships**:

1. **App Store artwork**, but only when the seller name matches the brand.
   Search returns knockoffs -- the top three hits for "Descript" are copycat
   apps by unrelated sellers.
2. **The company's GitHub org avatar**, after confirming the org's display
   name and website via `api.github.com/users/<org>`. `github.com/raindropio`
   is an unrelated private person's account.
3. **The site's `apple-touch-icon.png`**, or `<domain>/icon.png`.

Never use a homepage `og:image`: those are 1200x630 marketing banners, not
marks. Pad non-square art to a square before use or `rounded_icon` distorts
it, and crop the transparent margin off macOS-style icons or the corners
composite as black.

Fastest check on a batch: build one labelled contact sheet and view it once,
rather than opening 28 files.
