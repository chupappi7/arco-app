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

## People, workspaces and separation

People sign in with email: a 6-digit code (hashed, 10 minutes, 5 guesses,
5 codes an hour per address), no passwords. TikTok, Instagram and Facebook
are only connections a workspace owns; connecting one needs an owner or admin
session. Workspaces from before email sign-in still open with their TikTok
until someone adds an email, which makes them that workspace's owner.

- **owner**: everything, including the API key and deleting the workspace
- **admin**: accounts, brands, posts, invites (not the owner, not other admins)
- **member**: posts and schedules; can be limited to some brands, and then
  never sees other brands' accounts, posts or images

Separation is enforced in the Worker's queries, not the page: every read of
accounts, posts, brands and image copies is filtered by workspace and, for
a limited member, by brand (`src/scope.js`). `test/users.test.js` tries to
reach another workspace's and another brand's data through every endpoint.

Mail goes through Resend: Worker secrets `RESEND_API_KEY` and `MAIL_FROM`
(a sender on a domain verified in Resend).

## Instagram and Facebook

Two logins, because Meta has two:

- **Instagram Login** (`api/auth/instagram/*` → Worker `/internal/ig-oauth`)
  connects a professional Instagram account directly, no Facebook Page
  needed. Scopes `instagram_business_basic,instagram_business_content_publish`;
  publishing goes to `graph.instagram.com`. The token lasts 60 days; the cron
  renews any within 20 days of expiry (it must be at least a day old). "Add
  another" sends `force_reauth=true` so a second account can sign in without
  logging out the first.
- **Facebook Login** (`api/auth/meta/*` → Worker `/internal/meta-oauth`)
  connects the Pages the person picks. Page tokens do not expire.

Signing in without a session finds a workspace only by who signed in (the
Instagram account itself, or the same Facebook person), never by a Page they
can manage; a Page already in someone else's workspace is refused.

Setup, once, in the Meta app at developers.facebook.com:

1. Instagram › API setup with Instagram login: add the redirect URI
   `https://arco-publisher.vercel.app/api/auth/instagram/callback`. Its
   Instagram app ID and secret are `IG_APP_ID` / `IG_APP_SECRET`.
2. Facebook Login for Business: add the redirect URI
   `https://arco-publisher.vercel.app/api/auth/meta/callback`. The app's own
   ID and secret are `META_APP_ID` / `META_APP_SECRET`.
3. Privacy policy URL `/privacy.html`, data deletion URL `/privacy.html#data-deletion`.
4. Vercel env: `IG_APP_ID`, `META_APP_ID`. Worker secrets: all four.
5. Live D1, in order: `migrations/002-meta.sql`, `003-brands.sql`, `004-users.sql`, `005-drafts.sql`
   (`npx wrangler d1 execute arco-publisher --remote --file=<file>`)
6. Until App Review grants Advanced Access (Instagram:
   `instagram_business_basic`, `instagram_business_content_publish`; Pages:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `business_management`), only people with a role on the app can connect.

A workspace holds up to 25 accounts across platforms (several per platform is
the point: one person running many brands), with up to 200 posts queued.

Limits the composer and the Worker both enforce for Instagram: 10 images,
JPEG, 2,200-character caption, 30 hashtags, aspect ratio 4:5 to 1.91:1, and
every carousel image at the first one's ratio (Instagram crops to it), so the
browser pads them all to that ratio; nothing is cropped. 100 posts per 24h.

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
