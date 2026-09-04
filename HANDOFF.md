# Handoff: ARCO TikTok pipeline

Open a new session in this repo and say: **"read HANDOFF.md, use
/tiktok-pipeline"**. That is the whole handover. `CLAUDE.md` loads on its own,
the skill carries the rules, this file carries what changes.

## What this is

Photo-carousel TikTok posts, rendered locally, hosted on GitHub Pages, pushed
as inbox drafts to three accounts. Thinh publishes by hand in the TikTok app.
Repo: `/Users/thinh/SIXSIX/arco-app`.

| key | account | notes |
|---|---|---|
| `vn` | arco.app | 70 followers, most posts |
| `getarco` | getarcoapp | 15 followers |
| `us` | emiliagonzalez389 | 17 followers, **6x the median reach of the others** |

The rules live in `~/.claude/skills/tiktok-pipeline/` — read `examples.md` for
register before writing any copy, `content.md` for the mechanics,
`operations.md` for delivery and errors. Do not work from memory; most of the
mistakes this project has had came from that.

---

## Guards that fail the build (`tools/compose.py`)

- `assert_hook_approved` — hooks only from `tools/hook_pool.json`
- `assert_hook_fresh` — a hook sits out 4 posts, 2 if it was marked performing
- `assert_hook_pillar` — every hook is tagged with a pillar and the tag binds:
  the hook decides the post's shape, not the build request
- `assert_roster_allowed` — `hook_slide` writes `.hook.json` into the draft and
  `app_slide` reads it. Under a screentime, discipline or learn hook it refuses
  to draw a roster at all; those pillars answer the hook with `rule_slide` steps
- `assert_audience` — roster must serve a young solo builder; `tool_pool.json`
- `assert_one_llm` — exactly one LLM per post, rotated
- `assert_teaches` — both body lines teach, never a verdict
- `assert_bg_roles` — night desk backgrounds on the hook slide only
- `assert_varied` — no adjacent vibe repeat, at most one person per post
- `assert_bg_fresh` — a background may repeat, but not in consecutive posts
- `copy_band_luma` — rejects frames too bright to hold white body copy
- `hook_slide` — fixed size and position, raises rather than shrinking

## Hooks (`tools/hook_rules.py`)

Not burn-once. A hook sits out `HOOK_COOLDOWN = 4` posts, or
`HOOK_COOLDOWN_PERFORMING = 2` if its last outing was marked performing.
`retired: true` takes one out for good.

- `hook_rules.eligible(pillar=...)` is the real count. The `used` flag is a
  lifetime marker and gates nothing.
- A light rewording passes (`hook_rules.parent`, 0.82 similarity — measured:
  distinct hooks never exceed 0.70, one-word edits score 0.91+). Rewording does
  **not** reset the cooldown; the parent hook is what counts.
- `tools/hook_history.json` is the order hooks went out.
  `mark_hook_used(HOOK, TOPIC)` appends to it. Always pass the topic.
- Deleting a post calls `hook_rules.forget(topic)`, so a post that never ran
  does not hold its hook down.

## Rules that are judgment, not code

- Every slide must answer the hook, including ARCO's. Pass the hook's theme to
  `next_arco_angle(theme)`; it raises on an unknown theme rather than guessing.
- ARCO leads at slide 1.
- Never generate or ingest backgrounds. The pool is Thinh's, curated.
  `bg/_unapproved/` holds ones a build ingested on its own; keep them out.
- No em dashes.

---

## Dashboard (`tools/dashboard.py`, port 4500)

Stdlib only, one HTML page, no external libraries. Charts are hand-rolled SVG.

**Tabs**: Review (built, never drafted, under a week old) · Published (two
bands: "Publish next" = drafted and waiting, oldest first; "Done") ·
Performing · Analytics · All posts · Archive.

**Cards** carry the action: Draft to all → Repost, plus a fire toggle. There is
no "mark published" anywhere — the sync detects it. Per-account chips live in
the post detail only, since every post goes to all three accounts.

**Post detail** is one screen: sticky bar (back, chips, one contextual primary,
Redo, Replicate, Repost) over a row of six slides, title and caption below,
autosaved on blur. No gated step sections.

**Keyboard**: `J`/`K` next/prev, `D` draft, `F` performing, `R` redo, `1`–`6`
pick slides, `Esc` back.

**Buttons that spend tokens**: Redo (multi-slide, one run) and Replicate (three
modes: reword / same words new backgrounds / new take). Both hand off to
headless `claude -p` and show a progress toast driven by `DATA.runs`. **Repost**
re-sends existing slides with no agent at all. Drafting and publishing are never
automatic.

**iPhone**: responsive at 900px and 430px, verified at 393×852.

### Things that bit, now fixed — do not undo

- **Agent runs are serialised** behind `_agent_gate`. They do plain
  read-modify-write on `hooks.json`, `hook_history.json` and `bg_history.json`,
  so two at once silently lose a write. That is how a replica shipped with no
  caption.
- **`PUSH_RULE` forbids polling GitHub Pages.** It used to tell agents to poll
  until md5 parity with no deadline; one agent sat burning quota for four hours.
  The dashboard checks parity itself before every delivery.
- **Restarting the server orphans a running agent.** Its files still land, its
  queue entry says `interrupted`, and its replicate lineage is never recorded.
  Check `drafts/` before assuming an interrupted run failed.
  `reconcile_queues()` closes stale entries at startup.
- **A "busy" post checks job status, not just `done`.** An interrupted job is
  never done, so the spinner used to run forever.
- **`stateOf()` archives on age alone.** Adding a `seen` condition once left 29
  never-reviewed posts stuck in Review permanently.

---

## Analytics

Powered by TikTok's **Display API**, synced every 30 minutes by the dashboard's
scheduler thread. Costs no tokens — HTTPS, not an agent.

**Scopes on all three accounts**: `user.info.basic`, `user.info.stats`,
`video.upload`, `video.publish`, `video.list`.

**What the sync does** (`sync_account`):

1. Pages through every post (`--list-posts` follows the cursor; accounts have
   29–49 posts and the endpoint returns 20 at a time)
2. Matches posts to topics on the caption, which comes back verbatim
3. Marks published automatically — a post on the profile *is* published
4. Records views/likes/comments/shares per topic **per account**
5. Auto-flags performing at 1,000 views, **except** promoted posts
6. Snapshots into `stats_history.json`, so view velocity becomes possible

**Files**: `post_stats.json` (per topic per account), `stats_history.json`
(time series), `account_stats.json` (followers, daily sample),
`untracked_posts.json` (posts with no matching topic, mostly launch-era),
`promoted.json` (paid posts, excluded from organic medians).

**Tabs**: Totals (TikTok Studio shape, all accounts summed) · Accounts (the
cross-account comparison TikTok can never show) · Posts (matrix, top 20,
sortable) · What to do (four computed panels).

**Marking promoted matters.** Three creatives were promoted on 26 Aug for
109 Kč plus a 78.93 Kč Apple fee: 17,549 views, 234 profile visits, **7
followers**. Paid reach was setting the performing flag, which feeds the hook
cooldown and the replicate suggestions. Use the `$` button in the matrix.

### What the numbers say (31 Aug)

- ~24% of uploads clear 1,000 views; about half of posts clear it *somewhere*
- **The same post swings up to 30x between accounts** — 1,211 vs 36 on identical
  slides. Content cannot explain it
- `emiliagonzalez389` runs a median around 1,064 against roughly 170 for the
  other two
- Likes track views (r = 0.75). Median like rate 2.2%; posts well above it that
  never cleared 1,000 are the best reshoot candidates
- Views land bimodally: TikTok kills at the test audience or pushes. A weak post
  is not slightly weak, it is unpushed — which is why reshooting works

### What the API cannot give

Profile views, watch time, retention, traffic source, follows-per-post. The
Display API exposes views, likes, comments, shares and follower count, nothing
more. Research and Business APIs are unavailable to an unaudited app.

---

## Direct Post — built, parked

`autopost.js --direct-post` works and a full compliance panel was built, then
removed from the UI at Thinh's request. Backend stays (`run_publish`,
`creator_info`, `/api/publish_direct`).

Findings, so nobody researches this twice:

- The pipeline runs on the **Sandbox** app `arco-demo`, not production. The
  production app is an empty draft, never submitted.
- `unaudited_client_can_only_post_to_private_accounts` means the **target
  account** must be private in TikTok's settings. It is not about
  `privacy_level`: `SELF_ONLY` to a public account fails identically.
- Lifting it needs a separate 4-step audit application at
  `developers.tiktok.com/application/content-posting-api`, on top of app review.
  That form is written for organisations serving many creators; a first-party
  tool posting to three of its own accounts is a weak case.
- Photo post fields: `title` (90 UTF-16 runes), `description` (4000),
  `privacy_level`, `disable_comment`, `auto_add_music`, `brand_organic_toggle`,
  `brand_content_toggle`. No duet or stitch for photos. Branded content cannot
  be `SELF_ONLY`.

Honest verdict: direct posting saves about ten seconds per post and removes the
5-pending cap. It is not what limits this pipeline.

---

## Running it 24/7

`tools/deploy/install.sh` installs the dashboard as a launchd agent
(`RunAtLoad` + `KeepAlive`). Full instructions in `tools/deploy/README.md`,
including the three System Settings a headless Mac mini needs: auto-login,
restart after power failure, and never sleep — a sleeping Mac runs no scheduler
and no sync.

The machine needs `node`, a logged-in `claude` CLI, and `.env` copied across by
hand. `.env` and `tools/.dashboard_token` are gitignored; neither ever travels
through git. Two machines running builds share one subscription quota.

---

## Current state

- **Nothing creates posts automatically.** The Create button was removed on the
  understanding that a 5am job would replace it. That job was never built.
  Review only fills when Replicate runs or a build is triggered by hand.
- Replication lineage is in `post_status.json` as `from_replicate` +
  `replicate_mode`, written by `run_replicate` from the agent's `BUILT <topic>`
  line. Cards show it as a badge; originals show `replicated 2x`.
- Follower history started 30 Aug. The daily-change chart needs a second
  snapshot before it draws.
- Display names and bios were rewritten 31 Aug. The 26 Aug promotion ran against
  a profile with no bio, which is the likeliest reason 17.5k views produced 7
  followers.

## Cost

Cache read grows with the square of session length: every turn re-reads the
whole conversation. One session on 30 Aug reached 6,194 turns and 2.89B cache
read, 75% of everything spent that day, and exhausted a weekly limit.

**One session per task.** Finish, `/clear`, reopen with the line at the top of
this file. `/compact` trims but the thread regrows; it is for staying on one
task, not switching between them. Prefer dashboard buttons over asking in chat —
a headless run starts near zero context. Do not call `show_generations` unless
Thinh says he generated new images.
