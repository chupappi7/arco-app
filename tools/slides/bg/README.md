# Slide backgrounds

Drop the full-bleed photos referenced by `bg` in `tools/hooks.json` here, as
plain filenames (`rooftop-city-dusk.jpg`, etc.).

- Portrait, at least 1080×1920. Anything larger is cropped to centre by
  `object-fit: cover`.
- Dark or dark-able images work best — `base.css` already applies
  `brightness(0.52)` plus a gradient scrim, but a bright sky will still fight
  white copy. For those, set `"align": "low"` on the slide.

If a referenced file is missing, `render.js` falls back to a dark placeholder
gradient and prints a warning naming every file it could not find. The render
still succeeds, so you can lay out a post before the artwork exists.

**The original background library was lost along with the old pipeline.** The
photos baked into the existing `drafts/*/**.jpg` are the only surviving copies;
they cannot be recovered as clean plates from the rendered slides.
