# ARCO Publisher

The public posting surface for the ARCO TikTok integration, and the screen
TikTok audits. It is deliberately separate from `tools/dashboard.py`: the
dashboard drives this machine (agents, Chrome, git, the delivery log) and
cannot be hosted, while this is only OAuth plus two API calls and can live
anywhere.

Deployed on Vercel so it stays up whether or not a laptop is on — a reviewer
may open it days after submission.

## Layout

    api/_lib.js            endpoints, signed cookies, TikTok envelope handling
    api/auth/start.js      -> TikTok consent screen (PKCE S256 + state)
    api/auth/callback.js   <- code exchange, token into an httpOnly cookie
    api/auth/logout.js
    api/creator-info.js    creator's own settings, never cached
    api/drafts.js          slide listing from the public repo
    api/publish.js         photo DIRECT_POST, rules re-checked server side
    api/status.js          publish polling
    public/index.html      the posting page

## Environment

Set in the Vercel project (use the **sandbox** credentials until the app is
audited):

    TIKTOK_CLIENT_KEY       from the developer portal
    TIKTOK_CLIENT_SECRET    from the developer portal
    SESSION_SECRET          openssl rand -base64 32

Optional:

    GITHUB_TOKEN            lifts the unauthenticated 60/hour API limit
    GH_OWNER, GH_REPO       default chupappi7 / arco-app
    PAGES_BASE              default https://chupappi7.github.io/arco-app

The redirect URI is `<deployment origin>/api/auth/callback` and must be
registered in the portal character for character.

## Instagram and Facebook

One Facebook Login (`api/auth/meta/start.js` → `callback.js` → the Worker's
`/internal/meta-oauth`) connects each Facebook Page the person picks and the
Instagram professional account linked to it. The Page token is stored
encrypted and does not expire; a revoked one marks the account "Reconnect".

Setup, once:

1. developers.facebook.com → the Meta app → add **Facebook Login for Business**
   and **Instagram** (API setup with Facebook login).
2. Valid OAuth redirect URI: `https://arco-publisher.vercel.app/api/auth/meta/callback`
3. Privacy policy URL `/privacy.html`, data deletion URL `/privacy.html#data-deletion`.
4. Vercel env: `META_APP_ID`. Worker secrets: `META_APP_ID`, `META_APP_SECRET`.
5. Live D1: `npx wrangler d1 execute arco-publisher --remote --file=migrations/002-meta.sql`
6. Until App Review grants Advanced Access to `pages_manage_posts`,
   `pages_read_engagement`, `pages_show_list`, `business_management`,
   `instagram_basic` and `instagram_content_publish` (with Business
   Verification), only people with a role on the Meta app can connect.

A workspace holds up to 25 accounts across platforms (several per platform is
the point: one person running many brands), with up to 200 posts queued.

Limits the composer and the Worker both enforce for Instagram: 10 images,
JPEG, 2,200-character caption, 30 hashtags, aspect ratio 4:5 to 1.91:1 (tall
slides are padded in the browser, never cropped).

## Why there is no database

The only thing worth storing is the user's access token, and it lives in a
signed httpOnly cookie for the length of its own life. A dropped session means
logging in again, which is the right trade for never holding someone's TikTok
token on a host we do not control. It also makes the Login Kit flow easy to
demonstrate, which the audit requires.

## What must stay in the UI

The content-sharing guidelines make these mandatory, not optional polish. Do
not simplify them away:

- the creator's nickname and avatar, re-read on every render
- a privacy dropdown with **no default**, listing only levels the creator has
- comment/duet/stitch shown, and shown disabled where they do not apply
- a commercial disclosure toggle, off by default, with Your Brand / Branded
  Content and the matching "Promotional content" / "Paid partnership" label
- branded content may not be combined with a private post
- a preview of the slides
- the Music Usage Confirmation consent line, plus the Branded Content Policy
  when branded content is on
- publish disabled until the disclosure is resolved, and a processing state
  polled to a terminal status
