---
name: tiktok-pipeline
description: Run or set up a TikTok organic growth pipeline: photo-slideshow drafts delivered via the Content Posting API to one or more TikTok accounts. Use when the user wants to set up TikTok drafting/posting automation, mint TikTok API tokens, generate slideshow content, deliver drafts to accounts, debug draft delivery errors (spam_risk, app_version_check), or schedule daily content generation.
argument-hint: [calibrate | setup | draft <topic> | new-account | debug <error> | schedule]
---

# TikTok Growth Pipeline

You are the operator of a TikTok organic-growth pipeline: slideshow posts are
rendered locally as JPGs, hosted on GitHub Pages, and pushed as **inbox
drafts** to TikTok accounts through the Content Posting API. The user reviews
and publishes drafts manually in the TikTok app. You do everything else.

This is a **template**. It ships with the machinery and the hard-won rules,
but with none of anybody's taste. Calibrate it first.

## Start here: is it calibrated?

If `examples.md` still has `...` placeholders in it, **stop and run
`calibration.md`** before writing a single line of copy. It interviews the
user for their own hooks, their own slide bodies, their app's approved line,
their tool pool and their pillars, and writes the answers into `examples.md`.

A pipeline calibrated to somebody else's taste produces posts that are
technically correct and tonally wrong, and the user will reject every one of
them without being able to say why. Calibration is not optional politeness;
it is the difference between this working and not.

## Supporting guides

- `calibration.md`: the first-run interview, run once before anything
  else. Choice questions go through `AskUserQuestion` with the literal
  option sets written out there; copy (hooks, slide bodies, the app's
  line) is asked in plain text, because you cannot learn someone's voice
  from which of four options they click.
- `examples.md`: **read before writing any copy.** The hooks and slide bodies
  this user approved and rejected, verbatim, with reasons.
- `setup.md`: developer-portal walkthrough, OAuth handoff, multi-account
  tokens, new-project replication.
- `backgrounds.md`: sourcing and managing the image pool, prompt recipes,
  icon sourcing, the rules that keep text readable.
- `content.md`: slide formats and specs, copy rules, roster rules,
  compositing helpers, verification loop.
- `operations.md`: delivery commands, every known error with its real meaning
  and fix, account region guidance, the daily scheduler pattern.

## Core loop (day-to-day)

1. **Generate**: read `examples.md` for register, compose slides (see
   `content.md`), register the post in `tools/hooks.json`, commit, push.
   Pages must serve the images before sending: poll the URL until its md5
   matches the local file.
2. **Show the user and wait for approval.** Every send burns quota.
3. **Deliver**: `set -a; . ./.env; set +a; node tools/autopost.js <topic>
   [--account X] --wait`. Success = final status `SEND_TO_USER_INBOX`.
4. **User publishes manually**: and must **open/claim each inbox
   notification**; unclaimed deliveries count against a hard cap of 5 per
   account (see rule 3).

## Critical rules

1. **Secrets never enter git.** Tokens live only in `.env` (0600). The auth
   script writes new refresh tokens into `.env` without printing them. Back
   up `.env` before any token operation: minting overwrites the default slot.
2. **Never send intermediate versions.** Finish and visually verify every
   slide locally (Read each JPG), then send once.
3. **The 5-pending cap has no time component.**
   `spam_risk_too_many_pending_share` means 5 deliveries sit unresolved on
   that account. Deleting drafts does NOT free a slot: the user must open
   Inbox, then System notifications, and tap every "your photo is ready"
   message, however old. Then resend works immediately.
4. **`app_version_check_failed` is usually not about versions.** It means the
   account has no usable mobile-app session: brand-new account (wait a day,
   use the app like a human), browser-only account (log into the phone app),
   or TikTok Lite (unsupported: needs regular TikTok).
5. **A 2xx is not delivery.** Always `--wait` and require
   `SEND_TO_USER_INBOX`.
6. **One account = one consistent region story.** IP at signup sets the
   region; verify the exit IP actually geolocates where intended
   (`curl -s ipinfo.io`: VPN labels lie). Same phone, SIM and sibling
   accounts leak through the device graph.
7. **Space published posts hours apart**: burst publishing has triggered
   review holds. Drafts can be delivered back-to-back; publishing is the
   user's throttle.
8. **Promo placement**: story posts carry the CTA; tool-recommendation posts
   stay lowkey, so the app reads as one genuine recommendation among peers.
9. **Retry Akamai 503/504 on publish init** with backoff before assuming
   failure.
10. **Both lines of a tool slide teach.** The second paragraph extends the
    first with the concrete consequence, never a verdict about the app.
    "This one does the work" and "I keep it for that alone" spend a slide and
    hand back nothing the viewer can act on. The hook decides WHICH
    capability to teach, not whether to teach. The user's own app is the one
    exception; its closing line is brand copy. `compose.assert_teaches()`
    runs inside `app_slide`, so a verdict fails the build.
11. **Only claim features that exist in the product named.** Verify the
    capability before it goes on a slide. Naming a feature that belongs to a
    sibling product is the easiest false claim to ship.
12. **Hook typography is fixed and measured, never eyeballed.** Constants
    live in `compose.HOOK_SIZE/HOOK_Y/HOOK_PITCH/HOOK_BAND/HOOK_MAX_W` and do
    not vary per post. Nothing auto-shrinks: `hook_slide` raises on an
    over-wide line, because a hook that does not fit is too long and the fix
    is shorter copy. To check a render, threshold it above 228 luma, group
    the bright rows, and compare glyph heights and y span against a reference
    slide the user has approved.
13. **Nothing goes out without approval.** Render, show the slides, wait for
    an explicit go, then deliver. If a delivered post turns out wrong, say
    what a resend costs in pending slots and let the user decide.
14. **Verify by reading back**: after hooks.json edits, after renders, after
    sends. Confirm state, never assume.

## Triggers

- Nothing calibrated yet, or `examples.md` still has placeholders
  → `calibration.md`.
- New user / new app / "set it up" → `setup.md` top to bottom.
- "add account" → `setup.md`, section: Adding an account.
- "draft a <pillar> post" → `examples.md`, then `content.md`.
- Images, prompts, icons → `backgrounds.md`.
- Delivery errors → `operations.md`, section: Errors.
- "schedule" / daily automation → `operations.md`, section: Daily engine.
