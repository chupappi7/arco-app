# ARCO — project context

ARCO (formerly SIXSIX) is a day planner + app blocker for iOS. This repo holds the
marketing site (GitHub Pages), App Store web pages, and the TikTok content pipeline.

## Repo map

| Repo | What | Current branch |
|---|---|---|
| `chupappi7/SIXSIX` | iOS app source (Xcode) | **`pivot-timer`** — the live dev branch (v2.0.0). `main` is stale (v1.0.3, Apr 2026). |
| `chupappi7/arco-app` | This repo: marketing site, TikTok drafts, pipeline tooling | `main` |
| `chupappi7/sixsix-v2` | Empty leftover, ignore | — |

## App state (as of 2026-07-30)

- Branch `pivot-timer`, MARKETING_VERSION 2.0.0, latest work: Blocked Hours Phase 1
  (recurring auto app-block windows), habit schedule merge, insights dedupe.
- `feature/scheduled-reorder` holds the shelved drag-reorder feature, planned for 2.1.

## SIXSIX → ARCO rebrand status

Done: app display name is ARCO; user-facing copy (onboarding, paywall, settings,
shields, live activities) says ARCO; icon drafts in `SIXSIX/icons/arco-v*.html`.

Remaining safe fixes (user-visible): extension display names (SIXSIXShield,
SIXSIXActivityMonitor, SIXSIXUsageReport, SIXSIXWidget in pbxproj), calendar title
"SIXSIX" in CalendarBridge.swift (possibly dead code — sync removed 2026-07-01),
log text "Settings → SIXSIX" in LiveActivityManager.swift.

DO NOT rename: bundle IDs (`com.thinh.sixsix.*`), app group keys, `sixsix.*`
UserDefaults/notification/DeviceActivity identifiers (breaks existing installs),
RevenueCat entitlement `"SIXSIX Premium"` (must match RC dashboard).

## TikTok content pipeline

Format: photo-carousel "slideshow" posts, 1080×1920 JPGs. Two proven styles:

1. **Story/listicle over photo** (existing batches in `drafts/*/`): white bold
   lowercase text over dark moody photos; hook slide then numbered points.
2. **App-stack listicle** (checkvibe.dev style, current direction): hook slide
   "5 apps i use to actually lock in.", then one app per slide — big rounded app
   icon + "N. AppName" + two short lines (what it is / personal payoff). ARCO is
   inserted at #2 among famous apps (Claude, Notion, Google Calendar, Endel) so the
   post reads as advice, not an ad.

Slide template specs (see `tools/slides/`): Inter 600/700 (Google Fonts), text
left/right margin 72px, hook text 64px w700 lh1.32 at top:520px, app slide: icon
190px radius 44px + name 88px w700, body 47px w600 lh1.38, dark gradient overlay,
text-shadow for legibility. Backgrounds: AI-generated (Higgsfield soul_2, 9:16,
"moody underexposed cinematic, film grain, quiet luxury, large dark negative
space") or user photos. Render: headless Chrome screenshot of the HTML
(`chrome --headless --screenshot --window-size=1080,1920 --virtual-time-budget=3000`).

Publishing flow:
1. Slides committed to `drafts/<topic>/01.jpg…` on `main` → hosted by GitHub Pages
   at `https://chupappi7.github.io/arco-app/drafts/<topic>/…`
2. The `tiktok*.txt` files in repo root are TikTok developer-app **domain
   verification** — do not delete; they let TikTok's Content Posting API PULL_FROM_URL
   the hosted images.
3. Drafts are pushed to the TikTok inbox via the Content Posting API using the
   user's TikTok developer app. The access token is NOT stored anywhere in git —
   supply it via `TIKTOK_ACCESS_TOKEN` env var. (Unaudited dev apps → draft/inbox
   mode only, which is intentional: user publishes manually in the TikTok app.)

Account strategy: new TikTok account targeting US audience via English-only
content; don't rely on VPN region spoofing. Post at US evening hours
(early morning Vietnam time).

## Lessons from previous sessions (July 2026 launch)

- **ARCO is LIVE on the App Store**: `apps.apple.com/app/id6761037446`. Website
  CTAs point there (official badge in hero + closing CTA).
- The launch-era pipeline had `autopost.js` + `hooks.json` + a TikTok **refresh
  token** (auto-renewing) — all of it lived only in an ephemeral cloud container
  and is **lost**. Rebuild it as committed code in `tools/` and keep tokens in
  env vars, never in a container only.
- TikTok Content Posting API returns transient Akamai 504/503 on publish init —
  always retry with backoff before assuming failure.
- Posting cautions learned the hard way: turn the US VPN on **before** posting,
  and space posts a few hours apart — publishing several at once triggered a
  TikTok review hold.
- Inbox-draft sends are capped at **5 UNRESOLVED deliveries per account**
  (`spam_risk_too_many_pending_share`) — no time component. A delivery stays
  "pending" until its inbox notification (Inbox → System notifications →
  "your photo is ready") is opened/cleared; deleting the resulting draft alone
  does NOT free it. Fix when blocked: clear ALL such notifications, however
  old, then resend. And never send intermediate versions — finish and verify
  all slides locally first, send once.
- The three launch batches (`drafts/launch-*`) use "native text post" style:
  hook slides are plain text on black (intentional, mimics TikTok text posts),
  with app-screenshot slides after. The user prefers photo backgrounds — use the
  photo-bg template in `tools/slides/` for new batches.
- iOS app open items from that era: Blocked Hours timeline band (Phase 2 — a
  read-only shaded band on the Today timeline showing blocked windows), and an
  on-device shield test for Blocked Hours (simulator can't test shields).

## Marketing site

`index.html` (landing), `support.html`, `privacy.html`, `terms.html`, `press.html`
on GitHub Pages: https://chupappi7.github.io/arco-app/
