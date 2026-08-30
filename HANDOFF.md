# Handoff: ARCO TikTok pipeline

Paste this at the start of a new session. Everything else lives in files.

## What this is

Photo-carousel TikTok posts, rendered locally, hosted on GitHub Pages, pushed
as inbox drafts to three accounts (`vn` = arco.app, `getarco` = getarcoapp,
`us` = emiliagonzalez389). Thinh publishes manually. Repo:
`/Users/thinh/SIXSIX/arco-app`.

The rules live in `~/.claude/skills/tiktok-pipeline/` — read `examples.md`
for register before writing any copy, `content.md` for the mechanics. Do not
work from memory; most of the mistakes this project has had came from that.

## Dashboard

```bash
python3 tools/dashboard.py     # prints local, wifi and tailscale URLs
```

A local UI for the pipeline: Inbox, Drafted, Published, Performing, Archive.
Buttons run real work through headless `claude -p`: Create (slider + niche),
Redo a slide, Replicate concept. Approve, Schedule and Draft stay manual.
Post view is three gated steps: Review, Deliver, Publish.

## Guards that fail the build (in `tools/compose.py`)

- `assert_hook_approved` — hooks only from `tools/hook_pool.json`
- `assert_hook_fresh` — a hook sits out 8 posts, 4 if it was marked performing
- `assert_audience` — roster must serve a young solo builder; `tool_pool.json`
- `assert_one_llm` — exactly one LLM per post, rotated
- `assert_teaches` — both body lines teach, never a verdict
- `assert_bg_roles` — night desk backgrounds on the hook slide only
- `assert_varied` — no adjacent vibe repeat, at most one person per post
- `assert_bg_fresh` — a background may repeat, but not in consecutive posts
- `copy_band_luma` — rejects frames too bright to hold white body copy
- `hook_slide` — fixed size and position, raises rather than shrinking

## Rules that are judgment, not code

- Every slide must answer the hook, including ARCO's. Pass the hook's theme to
  `next_arco_angle(theme)`; it raises on an unknown theme rather than guessing.
- ARCO leads at slide 1.
- Never generate or ingest backgrounds. The pool is Thinh's, curated.
- No em dashes.

## Current state

- Hooks are reusable on a cooldown (`tools/hook_rules.py`), not burn-once.
  `hook_rules.eligible()` is the real count; the `used` flag gates nothing.
- `bg/_unapproved/` holds backgrounds a build ingested on its own; keep them out.
- Pending: a 5am job for 5 tools posts plus one from each other category.
- Delivery sometimes appears to skip an account; per-account logging is now in
  the server output, so read `/tmp/dash.log` next time it happens.

## Cost

This project's chat sessions cost roughly 14x a headless build, because cache
read scales with session length. Start a fresh session per task. Prefer the
dashboard for routine builds. Do not call `show_generations` unless Thinh says
he generated new images.
