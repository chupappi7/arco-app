# Examples: the calibration set

**This file starts empty on purpose.** Fill it during `calibration.md`, then
read it before writing any hook or slide body from then on.

The point is calibration by example rather than by adjective. "Make it
punchy" means nothing; a list of ten lines the user approved and four they
rejected means everything. When a new line is in doubt, the test is not "is
it good", it is "does it sit in this set".

---

## Approved hooks

> Ask the user to write three in their own words before you generate any.
> Then add the ones they approve from your generated batch.

- `...`
- `...`
- `...`

**The register in one line:** _(describe it once the pattern is visible --
lowercase? specific numbers? first person? Write it down so it survives.)_

## Rejected hooks and why

> The reasons matter more than the lines. Record the user's own words.

| Rejected | Why |
|---|---|
| `...` | ... |

Two rejections that hold for almost everyone, worth stating up front:

- **Anything naming the app in the hook.** The post has to read as advice
  among peers. The app earns attention at slide 2 by being useful, never by
  being announced.
- **Anything corny or exclamation-marked.**

## Approved teaching contexts

> One per tool. First paragraph is the mechanism, second is the concrete
> consequence. Both teach.

**ToolName**
```
First line of the mechanism,
second line of it.

What that lets you actually do,
in one more sentence.
```

## Rejected contexts and why

| Rejected copy | Why |
|---|---|
| `...` | ... |

Two failure modes to watch for, from the source pipeline:

| Failure | Example | Why it fails |
|---|---|---|
| Too obvious | "Claude works in the terminal and edits files" | Everyone knows it. Nothing to follow you for. |
| A verdict | "Everything else hands me text to paste. This one does the work." | An opinion, not something the viewer can go and do. |

`compose.assert_teaches()` fails the build on verdict phrasing. It cannot
catch "too obvious" -- that stays your judgment, which is why this file
exists.

## The app's own slide

> One approved line and its variations, rotated by `compose.next_app_angle()`
> from `tools/app_angles.json`. This is the one exception to the no-verdicts
> rule: its closing line is deliberate brand copy.

```
...
```

Closing line: `...` -- repeats on about 75% of variations, with same-register
alternates for the rest. Never invent a new register for this slide.

## Hook and context must agree

The hook sets a question; every slide answers it. The hook decides **which**
capability to teach, never whether to teach.

Test: if a slide would sit unchanged under a completely different hook, it is
not answering this one.

| Hook | A slide that answers it | A slide that does not |
|---|---|---|
| `...` | ... | ... |

## Post structure

1. **Hook slide** -- photo background, two lines, no icon, no numbering.
2. **Slides 2-6, one tool each** -- rounded icon, `N. Name` title, two dashed
   paragraphs. **The user's app is always #2.** #1 is a well known tool that
   buys credibility; #3 to #5 follow.
3. **Closing card** (story posts only) -- app icon, full store name, "On the
   App Store". Tool-recommendation posts get no CTA: the app has to read as
   one genuine recommendation among peers.

Six slides is the norm. Viewers read the first two or three and scroll, so
nothing load-bearing goes at #5.
