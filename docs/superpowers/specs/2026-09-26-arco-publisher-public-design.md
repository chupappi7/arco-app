# ARCO Publisher, public: design

Date: 2026-09-26 · Status: draft for review

## Why

TikTok's Direct Post audit refuses "a utility tool to help upload contents to
the account(s) you or your team manages" and requires clients "intended for a
wide audience". ARCO Publisher today posts only ARCO's slideshows to ARCO's
accounts, so it cannot pass. The fix is to make it what the application says:
a free, open TikTok photo-post scheduler that anyone can use, with ARCO as one
of its users.

Success means:

1. A stranger can sign in with TikTok, upload their own photos, and post or
   schedule a photo post, with every step matching the Content Sharing
   Guidelines.
2. ARCO schedules its posts from the local dashboard, and they publish with
   every laptop closed.
3. Every statement in the prepared Direct Post application is true, and a new
   demo video shows the public flow. Then the application is submitted.

## Decisions already made

| Question | Decision |
|---|---|
| What can be posted | Photo slideshows only (up to 35 images). Video later |
| Where scheduled posts run | A new Cloudflare Worker with D1 and R2, cron every minute |
| Name and address | Keep "ARCO Publisher", icon and `arco-publisher.vercel.app`. No app revision |
| Sign-in | TikTok Login Kit. First sign-in creates a workspace; "Add account" connects more |
| Price | Free, open sign-up, with limits |
| How ARCO posts | The dashboard's existing Direct Post panel calls the API with a workspace API key |

## Architecture

```
Browser (creator)            Vercel: arco-publisher.vercel.app        Cloudflare Worker: arco-publisher-api
  web app pages   ─────────►  static pages + /api/* thin proxy  ─────►  auth, uploads, posts, accounts
                              /api/auth/callback (only redirect URI)   D1: workspaces, accounts, posts
                              /media/* rewritten to the Worker          R2: uploaded images
                                                                        cron * * * * *: publish due posts
ARCO dashboard (local) ─── HTTPS + API key ─────────────────────────►  same API
TikTok ◄── PULL_FROM_URL arco-publisher.vercel.app/media/... (already a verified URL prefix)
```

- **Vercel stays the front door.** The live app's only redirect URI is the
  Vercel callback, and `https://arco-publisher.vercel.app/` is already a
  verified URL prefix. Serving images at `/media/...` on that domain (a Vercel
  rewrite to the Worker) means no new domain verification and no app revision.
- **The Worker owns all state.** Vercel functions are stateless proxies that
  attach the session and forward the call.
- **Separate from `arco-metrics`.** Public users' tokens and images never share
  a database with ARCO's analytics.

## Data (D1)

- `workspaces`: id, created_at, api_key_hash, deleted_at.
- `accounts`: id, workspace_id, open_id (unique), display_name, avatar_url,
  refresh_token_enc, token_updated_at, connected_at.
- `sessions`: id_hash, workspace_id, expires_at. Browser gets an httpOnly,
  signed cookie holding the session id.
- `posts`: id, workspace_id, account_id, status (`draft` / `queued` /
  `publishing` / `published` / `failed` / `cancelled`), title, caption,
  image_keys (JSON list), cover_index, settings (privacy, disable_comment,
  auto_add_music, brand_organic, branded_content), scheduled_at, attempts,
  publish_id, public_post_id, fail_reason, created_at, updated_at.

Refresh tokens are encrypted with AES-GCM using a Worker secret. API keys and
session ids are stored as SHA-256 hashes. Nothing else from TikTok is stored:
`creator_info` is read live.

## Creator flow (web app)

1. **Sign in with TikTok.** New `open_id` creates a workspace; a known one
   signs back in. "Add account" runs the same consent screen and attaches the
   new account to the current workspace.
2. **New post.** Drop images (JPG/PNG, resized client-side to at most 1080x1920),
   reorder, pick the cover, write title (90 chars) and caption (4000).
3. **Posting panel** — the audited one, unchanged in substance: account
   picker; creator avatar and nickname from a fresh `creator_info`; privacy
   dropdown with no default, options from `privacy_level_options`; comment and
   music toggles, duet and stitch shown disabled for photos; disclosure toggle
   off by default with Your Brand / Branded Content and the resulting label;
   branded content removes "Only me"; preview of every slide; Music Usage
   Confirmation (plus Branded Content Policy when relevant). New: **Post now**
   or **Schedule** with a date and time, validated at least 5 minutes ahead.
4. **Calendar.** Week grid per account, like the dashboard's Instagram page:
   queued posts with cancel/edit, published with a link, failed with the
   reason and Retry.
5. **Settings.** Connected accounts with Disconnect; API key (create/rotate,
   shown once); Delete workspace.

## Publishing (Worker cron, every minute)

- Claim due posts atomically (`queued` → `publishing` with a single UPDATE),
  so a post cannot be sent twice.
- Refresh the account's access token and store the rotated refresh token.
- Re-read `creator_info`. If the chosen privacy is no longer offered, or
  branded content is private, fail with that reason instead of posting.
- `content/init` with `DIRECT_POST`, `PHOTO`, `PULL_FROM_URL` from `/media/`.
- Poll `publish/status/fetch` to a terminal status. Only
  `PUBLISH_COMPLETE` marks `published`; store `public_post_id`.
- Transient errors (5xx, rate limit, `internal_error`) retry up to 3 times,
  roughly 1, 5 and 10 minutes apart. Anything else fails with TikTok's message.
- At most 6 requests a minute per access token; posts sharing a minute are
  staggered.
- A revoked or expired refresh token marks the account "needs reconnect" and
  fails its queued posts with that reason.

## ARCO dashboard

- `.env` gains `ARCO_PUBLISHER_API_KEY` for ARCO's workspace. ARCO's six
  accounts are connected once through the web app's "Add account".
- The dashboard's Direct Post panel stays the confirmation surface. Its
  Schedule and Post now buttons upload the slides (from `drafts/<topic>/`) and
  create the post through the API. Its privacy options come from the API's
  `creator_info`, not the local one.
- The TikTok page becomes the Instagram-style week calendar, read from the API.
- Inbox drafting and the local scheduler for TikTok retire. The sandbox stays
  only for analytics (`TIKTOK_STATS_*`) until production gets the stats scopes.

## Limits (free tier)

- 10 connected accounts and 30 queued posts per workspace; 35 images per post,
  5 MB each after resize; 200 MB of images per workspace.
- Images are deleted 7 days after a post publishes, fails permanently, or is
  cancelled. Drafts untouched for 30 days are deleted.
- Delete workspace removes accounts, posts, images and sessions immediately.

## Site and policies

- Home page becomes a product page for creators: what it does, how it works,
  what we access, limits, FAQ. ARCO appears as the maker, not the only user.
- Privacy policy and terms updated to match the stored data, retention, and
  deletion above.

## Testing

- Unit tests for the Worker: token encryption round-trip, claim-once, retry
  policy, privacy re-check, limits.
- End-to-end, before the audit: a second TikTok account (not ARCO's) signs in,
  uploads, schedules; the post publishes. Unaudited clients force private, so
  expect `SELF_ONLY` results — that is the expected pre-audit behaviour.
- Same from the dashboard with the API key.
- Then record the demo: sign in, consent, upload, posting panel with the
  privacy dropdown opened, schedule, the post arriving on the profile.

## Out of scope

Video posts, other platforms, billing, teams/multiple users per workspace,
AI features, analytics in the public tool.

## Submitting

After testing: refill the prepared answers, upload the new demo, tick the
three declarations, submit. Expect days to weeks; a rejection returns a reason
and the application can be resubmitted.
