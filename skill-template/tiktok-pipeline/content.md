# Content: formats, specs and copy rules

Read `examples.md` first. This file is the mechanics; that file is the taste.

## Formats (rotate them; never two identical rosters in a row)

1. **Tool listicle** (the workhorse): hook slide, then one tool per slide with
   a rounded icon, `N. Name` title and two dashed paragraphs. **The user's own
   app is always #2** and is exempt from every roster rule. #1 is a well known
   tool that buys credibility.
2. **App demo**: hook, then 3-4 slides of real app screenshots with numbered
   explanatory lines, closing slide names the app once.
3. **Story**: hook, then 4-5 narrative slides in first person, ending on the
   change. Closing card with the app icon and store name.

## Roster rules

- **Reusing a tool across posts is fine** (`TOOL_COOLDOWN = 0`). The audience
  is not reading every post, and a stack that changes completely each time
  reads as invented. What must be fresh is the **teaching point**: the same
  app can carry three posts if each teaches a different capability. Set
  `TOOL_COOLDOWN` to 3 if the user wants variety enforced.
- **Max one LLM per post** (`compose.assert_one_llm`). Claude, Codex, ChatGPT,
  Gemini, Perplexity, Manus, Antigravity and Cursor all read the same in a one
  line description, so a second one is the same slide twice. Rotate which
  appears.
- **Tier matters more than category.** Not so small the viewer has to look the
  thing up, not so default that naming it teaches nothing. See
  `calibration.md`, section 4.
- Call `compose.record_post_tools(topic, [...names...])` after saving so
  `tools/tool_usage.json` stays accurate.

## Layout specs (match exactly for consistency)

- **Hook slide**: centered SF Bold at `HOOK_SIZE`, two lines, line centres at
  `HOOK_Y` and `HOOK_Y + HOOK_PITCH`, adaptive scrim over `HOOK_BAND`, soft
  shadow. Never auto-shrunk.
- **Tool slide**: rounded app icon 210px (radius 48) at (88, 610); title SF
  Black 84 at (85, 865), auto-shrinking until it fits 925px; body SF Semibold
  50 from y=995, line pitch 72, paragraph gap +26, about 34 chars per line.
- **Screenshot slide**: text lines centered from y=150 (pitch 90), screenshot
  scaled to height <= 1560 pasted bottom-centre, canvas filled with the
  screenshot's own edge colour.
- **Font**: `/System/Library/Fonts/SFNS.ttf` with `set_variation_by_name`
  (Black / Bold / Semibold). Soft shadow: black text offset +3px, gaussian
  blur 5, then white text on top.

## Hook typography is fixed, and measured

Do not eyeball this and do not let it auto-shrink.

Pick the size and position **by measuring a post the user has approved**, then
freeze them as `HOOK_SIZE`, `HOOK_Y`, `HOOK_PITCH`, `HOOK_BAND`. To measure:
threshold the slide above 228 luma, group bright rows into blocks, and record
glyph heights, the y span and the block centre. Match those numbers.

A hook that does not fit at that size is **too long**. `hook_slide` raises
rather than shrinking, and the fix is shorter copy.

Two traps that cost the source pipeline several rounds:

- **Fitting the joined string.** If the two lines are drawn separately, fit
  the widest *rendered line*. Measuring `' '.join(lines)` sizes for a string
  that never appears on the slide, so long hooks silently collapse to the
  floor and ship undersized.
- **Measuring the wrong file.** The reference is the render that was actually
  **published**, which may not be the file on disk: a later pass can overwrite
  it. Pull it from git history if needed.

## Copy rules

- **Hooks are quiet, lowercase, one size.** Both lines the same size, light
  scrim, no drop-shadow drama, no compressed display type. The photo is the
  composition; the hook is a caption on it. Heavy uppercase is borrowed from
  talking-head video where text competes with a face on screen, and it makes a
  carousel look templated.
- **Body text is dashed.** Each paragraph of a tool slide starts with a
  leading dash, matching the numbered title. `app_slide` does this
  automatically; keep paragraphs to 2-3 lines with a blank string between.
- **Both lines teach.** First paragraph is the mechanism, second is the
  concrete consequence. Never a verdict. `compose.assert_teaches()` fails the
  build on verdict phrasing; it cannot catch "everyone already knows this",
  which stays your judgment.
- **The teaching point must be real.** A specific capability the viewer can go
  and use, not a description of what the app is. If a viewer who already uses
  the tool learns nothing, the slide is wasted.
- **No em dashes anywhere.** They read as machine-written.
- **Captions stay lowercase; slide bodies stay sentence case.**

## Compositing (PIL, no external services)

Helpers in `compose.py`:

- `hook_slide(bg, [line1, line2], out)`, the hook.
- `app_slide(bg, icon, title, body_lines, out)`, a tool slide. Runs
  `assert_teaches` automatically.
- `cta_slide(bg, out, subtitle=...)`, closing card for story posts.
- `pick_hook_bg()` / `hook_bg_status()`, no-repeat hook background rotation.
- `assert_varied([...bgs...])`, adjacent-vibe and one-person guards.
- `assert_one_llm([...tools...])`, `record_post_tools(topic, tools)`.
- `next_app_angle()`, rotates the user's app copy from `app_angles.json`.
- `inpaint_band(im, y_lo, y_hi)`, glyph-level repair for backgrounds with
  baked-in text. Per-column interpolation, never a blurred rectangle:
  feathered blur boxes read as smears and the user will spot them.
- `adaptive_scrim(im, y0, y1)`, darkens only as much as the band needs.
- `frame_for_band(im, y0, y1)`, pans the crop so the text band lands on the
  least busy part of the photo.

## Registration

Every post gets an entry in `tools/hooks.json`:

```json
{ "topic": "slug", "title": "the hook, one line", "caption": "the TikTok caption" }
```

Slides live in `drafts/<topic>/01.jpg ... 06.jpg` and are served by GitHub
Pages. Commit and push before delivering, then poll the public URL until its
md5 matches the local file: Pages lags behind the push, and preflight failures
right after a push are almost always a stale deploy rather than a broken URL.

## Verification loop

1. Render, then **Read every JPG**. Undersized text, washed-out copy and a
   wrong icon are all obvious by eye and invisible in the code.
2. Check the deck against the hook: would any slide sit unchanged under a
   different hook?
3. Poll Pages for md5 parity.
4. Show the user. Wait for approval.
5. Deliver with `--wait`, require `SEND_TO_USER_INBOX`.
