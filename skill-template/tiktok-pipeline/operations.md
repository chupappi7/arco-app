# Operations: delivery, errors, accounts, scheduling

## Delivery

```bash
cd <repo> && set -a; . ./.env; set +a
node tools/autopost.js <topic> [--account <name>] [--us] --wait
```

- Preflights all image URLs (reachable, non-redirecting, size): if these
  fail right after a push, Pages hasn't rebuilt; poll the image URL until
  its md5 matches the local file.
- Refreshes the access token per run; if TikTok rotates the refresh token
  the script prints the new one: update the matching `.env` var.
- Success is the polled status `SEND_TO_USER_INBOX`. That status is
  terminal for drafts; it does NOT advance when the user claims/publishes.
- Debugging past sends: `fetchPostStatus({accessToken, publishId})` from
  `tools/lib/tiktok.js`: publish_ids look like `p_inbox_url~v2.NNN`.

## Errors: real meanings and fixes

| Error | Real meaning | Fix |
|---|---|---|
| `spam_risk_too_many_pending_share` | Official rule: "at most 5 pending shares within any 24-hour period" (rolling). A delivery counts until the creator PUBLISHES it or it expires. Deleting a draft never frees a slot; opening the notification alone is not reliable. | Publish the pending drafts, or wait for the rolling window to age sends out. Budget sends: with 4 posts/day, send each once. |
| `app_version_check_failed` | Account has no usable mobile session: minutes-old account, browser-only login, or TikTok Lite | Log the account into regular TikTok on a phone, use it like a human, retry after ~a day. Not an actual version problem when the app is current. |
| Akamai 503/504 on init | Transient edge failure | Retry with backoff. |
| `preflight failed` | Pages not serving the new images yet | Wait for deploy (md5 poll), retry. |
| Auth errors on refresh | Token rotated/expired or wrong slot | Re-mint via the OAuth handoff; check which account's slot you overwrote. |

## Account hygiene (region + device graph)

- Region is set at signup by IP and is sticky. Verify the VPN exit actually
  geolocates to the target country (`curl -s ipinfo.io`): server labels
  lie (a "Seattle" node can resolve as Panama, which region-tags the
  account Panama).
- TikTok also weighs SIM country, device language, and other accounts on
  the same device. A US-targeted account operated on a VN phone with a VN
  SIM next to VN accounts will drift VN. Reliable fix: dedicated reset
  device, no SIM, VPN on from first boot, only that account.
- Judge the real bucket by analytics viewer territories, not settings.
- Warm a new account 2–3 days before posting: scroll/search/like as the
  target persona, on the target IP. Before each post, scroll ~2 min.
- Publish spacing: hours apart; target audience's evening. Bursts have
  triggered review holds.

## Daily engine (session-scheduled)

Pattern in production (adjust times to the user):

- **05:07 generation job** (CronCreate, recurring): compose 4 new posts
  (rotate formats, fresh copy: check hooks.json for what exists), verify
  slides visually, register, commit, push, then overwrite `tools/queue.json`:
  `{"date": "...", "slots": {"09": t1, "12": t2, "18": t3, "21": t4}}`.
  Also verify the four send jobs still exist (CronList) and recreate any
  missing (they auto-expire after 7 days).
- **Send jobs at 09:02 / 12:02 / 18:02 / 21:02**: read queue.json, send that
  slot's topic to every configured account sequentially with `--wait`,
  report one line per account. On `spam_risk_too_many_pending_share`, tell
  the user to claim that account's notifications: do not retry.

Hard constraints to tell the user up front:
1. Session-only: the schedule lives in the Claude session: the session
   must stay open and the machine awake. Re-arm after restarts.
2. The 5-pending cap means daily claiming of drafts is mandatory at
   4 posts/day; the engine will report the first clogged account.
3. Drafts ≠ posts: publishing stays manual, which is also the quality and
   spacing gate.

## Offer codes (promo funnel support)

Subscription offer codes are created via the App Store Connect API
(`subscriptionOfferCodes` + `subscriptionOfferCodeCustomCodes`; FREE_TRIAL
offers take territory-only inline prices; custom codes have a 500 minimum).
Redemption URL pattern:
`https://apps.apple.com/redeem?ctx=offercodes&id=<appId>&code=<CODE>`.
The user replies to comments with this link; scarcity claims on slides must
match reality (they control it by only replying to the first N).
