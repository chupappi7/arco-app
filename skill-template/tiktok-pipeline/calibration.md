# Calibration: interview the user before writing anything

Run this once, on first use, before drafting a single post. Do not skip it and
do not guess the answers from the repo. A pipeline calibrated to somebody
else's taste produces posts that are technically correct and tonally wrong,
and the user will reject every one of them without being able to say why.

Write the answers into `examples.md` as you go. That file becomes the
calibration set, and it is read before every draft from then on.

Use `AskUserQuestion` where the answer is a choice; ask in plain text where
the answer is copy the user has to write.

---

## 1. The app and the constant

> What is your app called, and what is its full App Store name?

Write both into `compose.ALWAYS_ALLOWED`. The app is exempt from every roster
rule and always appears at slide 2.

> In one or two sentences, in the voice of a real user and not a marketer,
> what does your app do for you personally?

This becomes the approved line. Push back if it sounds like App Store copy.
The test: would a friend say this sentence out loud? Then ask:

> Give me a short closing line for the app slide. Something you would
> actually say, not a slogan.

Write the line and its closer into `tools/app_angles.json` as `v1`, then
generate 9 variations that keep the register identical and rotate which
feature is named. Show all ten and get them approved before use.

**Worked example** (from the pipeline this template came from):

```
I manage all my tasks here and plan
the day in 30 seconds.

Focus mode puts every distraction
away.

My holy grail.
```

The closer `My holy grail.` repeats on about 75% of variations; the rest use
same-register alternates. That consistency is what makes it read as a person
rather than a rotating ad.

## 2. Hooks: ask the user to write three

Do not write hooks for the user at this stage. Ask:

> Write me three hooks in your own words, the way you would say them out
> loud. Two lines each, and do not try to make them clever.

Then ask for the opposite, which is more informative:

> Now give me one hook you would never post, so I know what to avoid.

Record all four in `examples.md` under approved and rejected. Only after that
should you generate new hooks; show 10-15 and ask which land. Record the
misses too, with the user's reason if they give one.

**What the register looked like for the source pipeline** (yours will
differ, this is the shape not the content):

- `the tools i used to / 4x my productivity`
- `the tools i use to run my business at 19 years old`
- `the 5 apps i would keep / if i deleted everything else`
- `i pay for 12 apps, these 5 do all the work`

Rejected there: anything corny, anything with an exclamation mark, and
anything that says "i built this app". The app earns attention at slide 2 by
being useful, never by being announced in the hook.

## 3. Teaching contexts: ask for one, then calibrate

> Pick one tool you actually use. Write the two lines you would put on its
> slide: what the feature is, and what it lets you do.

This single answer tells you the depth the user wants. Then check it against
the two failure modes and show them both, because most people have to see
the failures to recognise the target:

| Failure | Example | Why it fails |
|---|---|---|
| Too obvious | "Claude works in the terminal and edits files" | Everyone knows it. No reason to follow. |
| A verdict | "Everything else hands me text to paste. This one does the work." | An opinion, not something the viewer can go and do. |

The working shape: **first paragraph is the mechanism, second is the concrete
consequence.** Both teach.

```
You can define your own agents and
run them at the same time.

One builds, one reviews, each with
its own clean context window.
```

`compose.assert_teaches()` runs inside `app_slide` and fails the build on
verdict phrasing. It cannot catch "too obvious" -- that stays your judgment.

## 4. The tool pool

> Which apps do you actually use and would happily recommend?

Then calibrate the tier, because this is where most drafts go wrong:

- **Too small** (Raindrop.io, Soulver, Proxyman): naming them is free
  promotion for someone else, and the viewer stops to work out what the thing
  even is instead of learning the slide.
- **Too default** (Apple Notes, Google Sheets, Shortcuts): everyone has them,
  so being named teaches nothing.
- **Right** (Canva, CapCut, Notion, GitHub, Raycast, Figma): known and wanted,
  where the *feature* is the surprise.

Ask whether the user wants the reuse cooldown on. Default is off
(`TOOL_COOLDOWN = 0`) because a stack that changes completely every post reads
as invented; what has to stay fresh is the teaching point. Set it to 3 if they
want more variety enforced.

Write the approved list into `tools/tool_pool.json` grouped by category, with
the verified icon filename for each.

## 5. Content pillars

> What are the three to five things your audience wants to become?

Each pillar owns a different want and keeps the feed from being one long tool
list. Write them into `content.md`. Every post belongs to exactly one, and the
user names the pillar when asking for a draft.

## 6. Accounts and cadence

> How many TikTok accounts, and which region is each aimed at?
> How many posts per day do you want?

Then state the constraint plainly before they answer the second one: **five
pending drafts per account per rolling 24h**, and the only thing that frees a
slot is publishing. At four posts a day the user must claim and publish daily
or the pipeline jams.

## 7. Backgrounds

Walk `backgrounds.md`. Ask whether they will generate images or supply their
own, and get one approved look before building a pool.

---

## Done when

- `examples.md` has at least three approved hooks, one rejected hook, one
  approved slide body, and the app's own line.
- `tools/app_angles.json` has ten approved variations.
- `tools/tool_pool.json` lists the tools with verified icons.
- `compose.ALWAYS_ALLOWED` names the user's app.
- The user has seen and approved one complete rendered post.

Do not deliver anything to TikTok until that last one is true.
