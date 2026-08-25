# Setup: from zero to first draft

Walk these phases in order for a brand-new user. Each phase says what YOU do
and what to tell the USER (their steps happen in a browser you may not
control: hand them the exact text in the quote blocks).

## Phase 1: TikTok developer app

Tell the user:

> Go to https://developers.tiktok.com and log in with any TikTok account
> (a dedicated one is fine). Create an app: Manage apps → Connect an app.
> Name it after your brand (e.g. "<Brand> Publisher"). You do NOT need to
> submit it for review: we'll use Sandbox mode.

In the app's settings the user (or you, via browser automation if available)
must configure:

1. **Create a Sandbox** (top switcher: Production / Sandbox). Unreviewed apps
   can only talk to sandbox target users: that's all we need for drafting.
2. **Basic information**: name, category, description, Terms of Service URL
   and Privacy Policy URL (any real pages on the user's site), platform Web
   with the site URL.
3. **Add products**: **Login Kit** and **Content Posting API**.
4. **Login Kit → Redirect URI**: a page the user controls, e.g. their GitHub
   Pages root `https://<user>.github.io/<repo>/`. The OAuth code arrives
   there as a query param: no server code needed, the user just copies the
   final URL from the address bar.
5. **Content Posting API**: leave "Direct Post" off (drafts only).
   **Verify domains** for PULL_FROM_URL: TikTok gives a `tiktokXXXX.txt`
   verification file: commit it to the repo root so Pages serves it, then
   click Verify. Never delete these files.
6. **Scopes**: `user.info.basic`, `video.upload` (covers photo drafts).
7. **Sandbox settings → Target Users → Add account**: this opens a TikTok
   login; whichever account logs in gets allowlisted. Tell the user:

> Target Users is the allowlist of TikTok accounts this unreviewed app may
> touch. Click "Add account" and log in as the account you want to post to
> (use the right VPN/IP for that account). Repeat for each account.

8. Copy **Client key** and **Client secret** from Sandbox → Credentials
   (sandbox has its own pair: production credentials will not work).

## Phase 2: repo + .env

The pipeline needs a public GitHub repo with Pages enabled (images must be
publicly fetchable for PULL_FROM_URL). Copy `tools/` from the reference repo
(the `tools/` folder shipped with this template): `tiktok-auth.js`,
`autopost.js`, `lib/tiktok.js`,
`hooks.json` (empty the posts array), plus a `drafts/` directory.

Create `.env` in the repo root (ensure `.gitignore` covers it, `chmod 600`):

```
TIKTOK_CLIENT_KEY=<sandbox client key>
TIKTOK_CLIENT_SECRET=<sandbox client secret>
TIKTOK_REDIRECT_URI=https://<user>.github.io/<repo>/
TIKTOK_REFRESH_TOKEN=
```

Load it per-command with `set -a; . ./.env; set +a`: never export in
profiles, never echo values.

## Phase 3: mint a token (OAuth URL-handoff)

```bash
rm -f tools/.auth-state.json && node tools/tiktok-auth.js --print-url
```

Send the printed URL to the user with:

> Open this while logged into TikTok **as the account being connected**
> (check the name on the approval screen: a browser session for another
> account will silently authorize the wrong one). Approve, then paste me the
> full URL of the page you land on (it contains ?code=...).

Exchange it:

```bash
node tools/tiktok-auth.js --redirected "<pasted url>"
```

The refresh token (~365 days) is written into `.env` as
`TIKTOK_REFRESH_TOKEN`: **it overwrites that slot**, so back up `.env`
first when the slot already holds another account's token. Verify the
`open_id` in the output differs per account; record which open_id is which.

## Adding an account (multi-account)

1. User adds it to Sandbox Target Users (Phase 1 step 7).
2. Back up `.env`, run the Phase-3 handoff logged in as the new account.
3. Move the freshly written token into its own variable
   (`TIKTOK_REFRESH_TOKEN_<NAME>`), restore the default slot from backup.
4. Register the account in `autopost.js`'s `ACCOUNTS` map
   (env var + human label) so `--account <name>` selects it.
5. First delivery to a brand-new account fails with
   `app_version_check_failed` until the account has aged ~a day and is
   logged into the regular TikTok mobile app. Expect it; retry next day.

## Phase 4: first post

Compose slides per `content.md`, register topic in `tools/hooks.json`,
commit, push, wait for Pages (poll the raw image URL until its md5 equals
the local file), then:

```bash
node tools/autopost.js <topic> --wait
```

`SEND_TO_USER_INBOX` = success. Tell the user to open TikTok → Inbox →
System notifications → tap the "your photo is ready" message to claim the
draft (this matters: see operations.md § the pending cap), then publish
when ready.
