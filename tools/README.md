# TikTok draft pipeline

Turns post definitions into 1080×1920 slides, hosts them on GitHub Pages, and
pushes them to the TikTok inbox as a photo draft.

```
tools/hooks.json  --render.js-->  drafts/<topic>/NN.jpg  --git push-->  GitHub Pages
                                                          --autopost.js-->  TikTok inbox
```

Nothing here needs `npm install` — Node 18+ (for global `fetch`), Google Chrome,
and macOS `sips` are the only requirements.

## Setup

Secrets live in the environment and nowhere else. Add these to your shell
profile:

```sh
export TIKTOK_CLIENT_KEY='...'
export TIKTOK_CLIENT_SECRET='...'
export TIKTOK_REFRESH_TOKEN='...'   # from tools/tiktok-auth.js, see below
```

### One-time: mint the refresh token

The redirect URI must match one registered on your app at
developers.tiktok.com → your app → Login Kit → Redirect URI, byte for byte.

```sh
export TIKTOK_REDIRECT_URI='https://...'      # whatever you registered
node tools/tiktok-auth.js
```

The helper picks its capture mode from the URI:

- `http://localhost:PORT/...` — starts a throwaway server and grabs the code
  automatically.
- anything else (TikTok generally requires https) — prints the authorize URL,
  you approve in the browser, then paste the full redirected URL back into the
  prompt.

Add `--pkce` if your app is registered as a desktop/mobile client. It prints the
`export TIKTOK_REFRESH_TOKEN=...` line to copy into your profile.

Refresh tokens last 365 days. TikTok may also **rotate** the refresh token on
any refresh — `autopost.js` prints a loud warning with the new value when that
happens, and you must update your env or the next run will fail.

## Rendering slides

```sh
node tools/render.js              # every post in hooks.json
node tools/render.js btl          # one topic
node tools/render.js btl --open   # ...and reveal the folder
```

Output goes to `drafts/<topic>/01.jpg`, `02.jpg`, … at exactly 1080×1920.

A post in `hooks.json` looks like:

```jsonc
{
  "topic": "btl",
  "title": "How to block TikTok on iPhone (for real)",
  "caption": "used as the TikTok description",
  "slides": [
    { "bg": "rooftop-city-dusk.jpg", "text": ["first paragraph.", "second paragraph."] },
    { "bg": "poolside-sunset.jpg", "align": "low", "text": ["..."] },
    { "type": "cta", "bg": "supercars-driveway.jpg" }
  ]
}
```

- `text` — one or more paragraphs, rendered as a stacked block in the upper
  third. Wrapping is automatic; don't hand-break lines.
- `align` — `top` (default), `center`, or `low`. Use `low` when the photo is
  bright at the top; it also flips the scrim so the copy stays legible.
- `type: "cta"` — the closing slide. Falls back to `defaults.cta` for the icon,
  app name and subtitle.
- `bg` — a filename in `tools/slides/bg/`. Missing files fall back to a
  placeholder gradient with a warning rather than failing the render.

Templates live in `tools/slides/` (`text.html`, `cta.html`, shared `base.css`).
Inter is vendored in `tools/slides/fonts/` so renders work offline and stay
byte-stable.

## Posting

Commit and push the rendered slides first — `autopost.js` uses `PULL_FROM_URL`,
so TikTok fetches them from the public site. They must be live before you post.

```sh
git add drafts/btl && git commit -m "Auto-poster: host draft batch" && git push
node tools/autopost.js btl --dry-run    # validate URLs, print the payload
node tools/autopost.js btl              # push to the inbox
```

Useful flags: `--title`, `--description`, `--cover N`, `--wait` (poll status),
`--base-url`, and `--direct-post` (publishes immediately instead of drafting;
needs the `video.publish` scope rather than `video.upload`).

Before posting, every slide URL is checked for https, a 200, no redirect, and
the 20 MB per-image cap — TikTok's pull service fails opaquely otherwise, and a
failed post still burns one of your five pending-share slots.

`autopost.js` retries 500/502/503/504 and network errors with exponential
backoff (honouring `Retry-After`), and fails fast on 4xx.

## Limits worth remembering

| Limit | Value |
|---|---|
| Images per photo post | 35 |
| Size per image | 20 MB |
| Pending inbox shares | 5 per rolling 24 h |
| Access token lifetime | 24 h (auto-refreshed) |
| Refresh token lifetime | 365 days, may rotate |

`PULL_FROM_URL` only works from a domain verified under URL properties in the
developer portal. `chupappi7.github.io` is verified by the two `tiktok*.txt`
files at the repo root — don't delete them.

## Known gaps

- **The background photo library was lost.** `tools/slides/bg/` is empty; see
  the README there. Renders fall back to a placeholder gradient until you
  repopulate it.
- **Only `btl` is transcribed in `hooks.json`.** The other 16 topics exist as
  rendered JPGs under `drafts/` but their source copy went with the old
  pipeline.
- `render.js` shells out to `sips` for PNG→JPEG, so it is macOS-only as written.
- Chrome 150's `--headless=new` writes the screenshot but never exits;
  `render.js` waits for the file to settle and then reaps the process itself.
