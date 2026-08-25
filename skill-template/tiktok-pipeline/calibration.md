# Calibration: interview the user before writing anything

Run this once, on first use, before drafting a single post. Do not skip it and
do not guess the answers from the repo. A pipeline calibrated to somebody
else's taste produces posts that are technically correct and tonally wrong,
and the user will reject every one of them without being able to say why.

Write the answers into `examples.md` as you go. That file becomes the
calibration set, and it is read before every draft from then on.

## How to ask

Two kinds of question, and using the wrong tool for each is why calibration
interviews fail:

- **Choices** go through `AskUserQuestion` with real options. The literal
  option sets are written out below: use them, do not improvise a prose
  version. Every question also gets a free-text "Other" automatically, so a
  user who wants something not listed is never boxed in.
- **Copy** cannot be multiple choice. Ask for it in plain text and wait. You
  cannot offer a user four hooks and learn their voice from which one they
  pick; you learn it from what they write unprompted.

Batch the choice questions: `AskUserQuestion` accepts up to four at a time,
so steps 1, 5, 6 and 7 below can go out together rather than as eight
separate interruptions.

---

## Step 1: the app and its constant

**Ask** (choice, can be batched):

```
question: "Where should your own app sit in a listicle?"
header:   "App slot"
options:
  - label: "Slide 2 (recommended)"
    description: "Slide 1 is a famous tool that buys credibility, then yours
      lands while people are still watching. Viewers read two or three slides
      and scroll, so this is where it actually gets seen."
  - label: "Last slide"
    description: "Builds to it as the payoff. Works with a hook that promises
      a best-for-last, but most viewers never reach slide 5."
  - label: "Varies per post"
    description: "Rotate the position. More natural across a feed, harder to
      keep consistent."
```

**Write** (free text, ask and wait):

> What is your app called, and what is its full App Store name?

Put both into `compose.ALWAYS_ALLOWED`. The app is exempt from every roster
rule.

> In one or two sentences, in the voice of a real user and not a marketer,
> what does your app do for you personally?

This becomes the approved line. Push back if it sounds like App Store copy.
The test: would a friend say this sentence out loud?

> Give me a short closing line for the app slide. Something you would
> actually say, not a slogan.

Write the line and closer into `tools/app_angles.json` as `v1`, generate 9
variations that keep the register identical and rotate which feature is
named, then show all ten and get them approved before use.

**Worked example** from the pipeline this template came from:

```
I manage all my tasks here and plan
the day in 30 seconds.

Focus mode puts every distraction
away.

My holy grail.
```

The closer repeats on about 75% of variations; the rest use same-register
alternates. That consistency is what makes it read as a person rather than a
rotating ad.

## Step 2: hooks, in the user's own words

**Write** (free text). Do not generate hooks first, and do not offer a menu.

> Write me three hooks in your own words, the way you would say them out
> loud. Two lines each, and do not try to make them clever.

Then the more informative half:

> Now give me one hook you would never post, so I know what to avoid.

Record all four in `examples.md`. Only then generate 10 to 15 new hooks in
that register and ask which land. Record the misses with the user's reason.

**The shape** it took for the source pipeline (yours will differ; this is
register, not content):

- `the tools i used to / 4x my productivity`
- `the tools i use to run my business at 19 years old`
- `i pay for 12 apps, these 5 do all the work`

Rejected there: anything corny, anything exclamation-marked, and anything
saying "i built this app". The app earns attention at slide 2 by being
useful, never by being announced in the hook.

## Step 3: one teaching context, then calibrate

**Write** (free text):

> Pick one tool you actually use. Write the two lines you would put on its
> slide: what the feature is, and what it lets you do.

That single answer tells you the depth the user wants. Then show both failure
modes, because most people need to see them to recognise the target:

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

`compose.assert_teaches()` fails the build on verdict phrasing. It cannot
catch "too obvious", which stays your judgment. That is what `examples.md`
is for.

## Step 4: the tool pool

**Write** (free text):

> Which apps do you actually use and would happily recommend?

Then calibrate the tier out loud, because this is where drafts go wrong:

- **Too small** (Raindrop.io, Soulver, Proxyman): naming them is free
  promotion for someone else, and the viewer stops to work out what the thing
  is instead of learning the slide.
- **Too default** (Apple Notes, Google Sheets, Shortcuts): everyone has them,
  so being named teaches nothing.
- **Right** (Canva, CapCut, Notion, GitHub, Raycast, Figma): known and
  wanted, where the *feature* is the surprise.

Write the approved list into `tools/tool_pool.json` by category, with a
verified icon filename for each. Sourcing rules are in `backgrounds.md`.

## Step 5: repetition policy

**Ask** (choice, can be batched):

```
question: "Can the same tool appear in more than one post?"
header:   "Repeats"
options:
  - label: "Yes, freely (recommended)"
    description: "TOOL_COOLDOWN = 0. Nobody reads every post, and a stack that
      changes completely each time reads as invented. What stays fresh is the
      teaching point, not the logo."
  - label: "Not within 3 posts"
    description: "TOOL_COOLDOWN = 3. Forces variety. Workable if your pool is
      large."
  - label: "Not within 6 posts"
    description: "TOOL_COOLDOWN = 6. Strictest. Warning: this starves a small
      pool and pushes posts toward whatever is left, which is how filler gets
      in."
```

## Step 6: pillars

**Ask** (multi-select, can be batched):

```
question: "Which of these does your audience want to become?"
header:   "Pillars"
multiSelect: true
options:
  - label: "More productive"
    description: "Tool stacks, workflows, doing more in less time."
  - label: "Off their phone"
    description: "Screen time, doomscrolling, focus. Story-shaped."
  - label: "More disciplined"
    description: "Locking in, systems that survive low motivation. Method-led."
  - label: "A builder / founder"
    description: "Shipping, launching, running something solo."
```

Add "study and exams" as a fifth if the audience is students; the user can
also type their own. Every post belongs to exactly one pillar, and the user
names it when asking for a draft ("draft a screentime one").

## Step 7: accounts and cadence

**Ask** (choice, can be batched). State the constraint in the option text so
the answer is informed:

```
question: "How many posts per day do you want to draft?"
header:   "Cadence"
options:
  - label: "1 per day (recommended to start)"
    description: "Leaves plenty of headroom under the 5-pending cap and gives
      you time to actually judge what works."
  - label: "2 per day"
    description: "Comfortable. Claim and publish daily and you will never hit
      the cap."
  - label: "4 per day"
    description: "The cap becomes a daily chore: 5 pending drafts per account
      per rolling 24h, and ONLY publishing frees a slot. Deleting a draft does
      not. Miss a day and the pipeline jams."
```

**Write** (free text):

> How many TikTok accounts, and which country is each aimed at?

Region is set by the IP at signup and is sticky. See `operations.md`.

## Step 8: backgrounds

**Ask** (choice):

```
question: "Where will the slide backgrounds come from?"
header:   "Images"
options:
  - label: "Generate them"
    description: "Any 9:16 image model. Generate in the web app if you have an
      unlimited plan: an MCP integration usually bills credits per image even
      when the web app does not."
  - label: "My own photos"
    description: "Same pipeline and same rules. Needs enough dark, uncluttered
      frames to hold white text."
  - label: "Both"
    description: "Generated for volume, your own where it matters."
```

Then walk `backgrounds.md` and get one look approved before building a pool.

---

## Done when

- `examples.md` has at least three approved hooks, one rejected hook, one
  approved slide body, and the app's own line.
- `tools/app_angles.json` has ten approved variations.
- `tools/tool_pool.json` lists the tools with verified icons.
- `compose.ALWAYS_ALLOWED` names the user's app.
- The user has seen and approved one complete rendered post.

Do not deliver anything to TikTok until that last one is true.
