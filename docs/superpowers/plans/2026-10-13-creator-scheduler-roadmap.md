# Creator scheduler roadmap

Goal: a social media scheduler for creators, marketing managers and anyone who
wants to post automatically, in the spirit of Blotato. People sign in with an
account, write or AI-generate titles and captions, edit them per platform, and
schedule or post to many accounts at once. Free for now; billing comes later.
"Just works" beats feature count.

`[x]` is done and committed on `publisher-public`; `[ ]` is to do. Phases are
in order: each one leaves a product that works end to end.

---

## Phase 0: Ship what is built (week 1)

Nothing is live yet. Platform reviews take the longest, so they start first.

**Start the reviews now (the critical path):**
- [x] TikTok: Direct Post audit has passed. No new review is needed: same
      scopes (`user.info.basic`, `video.publish`, `video.upload`, which also
      covers video), same audited posting panel, connection still through
      Login Kit. A new review is needed only for new scopes, or a change to the
      app's name, icon, description, redirect URI or verified domain
- [ ] Meta: Business Verification, then App Review for Advanced Access:
      `instagram_business_basic`, `instagram_business_content_publish`,
      `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
      `business_management`. Until then only people with a role on the app
      can connect
- [ ] Decide the product name: keep "ARCO Publisher", or rename and accept a
      TikTok app revision

**Set up and deploy:**
- [ ] Resend: verify a sending domain; Worker secrets `RESEND_API_KEY`, `MAIL_FROM`
- [ ] Meta app: Instagram Login redirect URI and Facebook Login redirect URI;
      Worker secrets `IG_APP_ID`, `IG_APP_SECRET`, `META_APP_ID`, `META_APP_SECRET`;
      Vercel env `IG_APP_ID`, `META_APP_ID`
- [ ] D1 migrations, in order: `002-meta.sql` … `005-drafts.sql` (see publisher/README.md)
- [ ] Deploy the Worker, then Vercel
- [ ] Merge `publisher-public` into `main` and push

**Prove it with real posts (one each):**
- [ ] Sign up with email, invite a second person, accept
- [ ] TikTok photo post (Only me until the audit)
- [ ] Instagram carousel with a 9:16 slide (checks the 4:5 padding)
- [ ] Facebook Page multi-photo post (Meta never documented this flow end to end)
- [ ] A scheduled post that fires with every laptop closed
- [ ] An old TikTok-only workspace adding its email

**Already done:**
- [x] Email sign-in with codes; owner, admin and member roles; email invites
- [x] Workspaces fully separated; members can be limited to brands
- [x] TikTok, Instagram (Instagram Login) and Facebook Page publishing
- [x] Several accounts per platform; brands; Business Suite style "Post to"
- [x] Scheduler cron that is fair across workspaces and fits the free plan
- [x] Instagram token renewal; images padded for Instagram, never cropped

---

## Phase 1: Make posting feel finished (weeks 2–3)

The everyday loop has to be smooth before anything is added.

**Editable titles and captions:**
- [x] One caption for everywhere, plus an optional override per platform
      (Blotato's main editing pattern), with each platform's limits live as
      you type: TikTok title 90 / caption 4,000, Instagram 2,200 with 30
      hashtags, Facebook ~63,000
- [x] Edit a scheduled post: caption and time in place (detail panel, drag on
      the calendar); images and accounts through the editor
- [x] Drafts: save a post (several accounts, their captions) without scheduling it, reopen it later
- [ ] Duplicate a post ("Post again" exists; extend it to drafts)

**Scheduling basics:**
- [x] Time zone per workspace, shown on every time
- [x] Calendar: drag a post to another day; month view next to week
- [x] Queue / posting slots: set "Mon–Fri 9:00, 18:00" per brand, and "Add to
      queue" picks the next free slot

**Know what happened:**
- [x] Email when a post fails, with the reason and a Retry link (one email per person per run)
- [x] A post detail view: status, photos, full caption, error, live link; fix the caption in place
- [ ] Weekly email summary (optional, off by default)

**Sign-in polish:**
- [ ] "Continue with Google" (needs a Google OAuth client)
- [x] Transfer ownership (the owner can never leave or be removed, so a workspace always has one)

---

## Phase 2: AI titles and captions (weeks 3–4)

- [ ] "Write with AI" in the composer: from the photos (vision) plus an
      optional one-line brief, generate a title and captions per platform
- [ ] Options: tone (casual, professional, playful…), length, emoji, hashtags,
      call to action, language
- [ ] Rewrite / shorten / make it punchier for an existing caption
- [ ] Brand voice: a short description and example posts saved per brand,
      used in every generation for that brand
- [ ] Runs in the Worker on the Claude API (Haiku for speed and cost, Sonnet
      for "better" rewrites); the API key stays server side
- [ ] Free-plan quota per workspace (for example 50 generations a day), shown
      in the UI, to cap cost and abuse
- [ ] Nothing generated is posted without the person seeing it first

---

## Phase 3: Video (weeks 5–6)

Most creators post video; photos-only will not hold them.

- [ ] Direct-to-R2 uploads (multipart, resumable) for files up to ~1 GB;
      the Worker hands out short-lived upload URLs
- [ ] Instagram Reels: `REELS` containers, cover image or frame, `share_to_feed`,
      `audio_name` (original audio only: the API cannot add Instagram music)
- [ ] TikTok video Direct Post
- [ ] Facebook Page video and Reels
- [ ] Per-platform checks before scheduling: length, size, aspect ratio, codec
- [ ] Thumbnail picker

---

## Phase 4: More platforms (weeks 6–9)

In order of value for effort:
- [ ] Threads (Meta API, same app; quick win)
- [ ] YouTube Shorts (Google OAuth, upload API)
- [ ] LinkedIn (personal profile and company page)
- [ ] Bluesky (open API, simple)
- [ ] Pinterest
- [ ] X / Twitter (the API is paid; decide whether it is worth it)

Each new platform: connect flow, publish in the cron, limits in the composer,
icon, tests including the cross-workspace isolation tests.

---

## Phase 5: Run it like a product (alongside phases 1–4)

**Reliability:**
- [ ] Error tracking and alerts (Worker exceptions, failed-post rate)
- [ ] D1 backups (Time Travel retention checked) and a restore drill
- [ ] Status page; publish-success rate per platform on an internal dashboard
- [ ] Move the Worker to the paid plan once traffic needs it (50 → 1,000
      outbound calls per run; the per-tick budget then rises)

**Abuse and safety (free attracts spam):**
- [ ] Per-workspace limits: posts per day, accounts, storage, AI generations
- [ ] Sign-up throttling by IP; block disposable email domains
- [ ] A way to report abuse; terms that forbid spam and impersonation

**Legal and trust:**
- [ ] Terms and privacy policy reviewed for the multi-platform, team product
- [ ] Meta data deletion callback endpoint (needed for App Review)
- [ ] Export my data (posts, captions) as a download
- [ ] A short security page: email codes, separation, encryption at rest

**Growth basics:**
- [ ] Landing page that explains it in one screen, with a demo video
- [ ] Onboarding: sign up → connect first account → first scheduled post,
      with an empty state that walks you through it
- [ ] Product analytics on that funnel

---

## Phase 6: Billing (later)

- [ ] Choose a provider. Paddle or Lemon Squeezy (merchant of record, works
      from Vietnam, card data never touches us); Stripe needs a non-Vietnam entity
- [ ] Plans: free (1 brand, 3 accounts, AI quota) and paid tiers by accounts
      and AI usage
- [ ] Webhooks verified by signature; subscription state per workspace;
      limits enforced in the Worker, not the page
- [ ] Trial, upgrade and downgrade flows; what happens to scheduled posts when
      a plan lapses (pause, never delete)
- [ ] Update the TikTok and Meta app descriptions if they say "free"

---

## Not now

Post analytics (views and likes per post), comment inbox, team approval
workflows, content library, browser extension, mobile app. Each is worth
doing after the core loop is solid and people are asking for it.
