# Design rounds

Mockups made with ChatGPT image generation, three rounds, 2026-10-25.

- **r1** (2026-10-25): warm cream, sunrise seagulls, serif headlines, bottom tab bar (Home · Thesis · Arena · Swarm).
- **r2**: honest stacked bar for the three paths, plain-language "about a coin flip" lead, AI Arena card, graded
  receipts as hit/miss chips, scam-safety line. Phone + desktop.

Build notes (don't copy from the mockup): the arena names "Sage" and "DeepThink" are invented, show only real
forecasters; the "theflock.ai" address is a mockup placeholder; no image or font from outside, the sunrise art must
be ours.
- **r3** (2026-10-25, approved): portfolio-first layout: sunrise band kept narrow, one 3-part allocation bar (no donut),
  all holdings as tap-to-expand rows, side cards (what changed, track record, this week), rules and avoiding row,
  help band. This is the spec `site/` is built from (`r3-phone-top`, `r3-desktop-top`, `r3-desktop-bottom`).
  Built page notes: type sizes are larger than the mockup (it is drawn small, so copying its sizes literally would give
  about 11px text on a 390px phone), long `why` text in `holdings.json` is shortened to its first clause in the row and shown in full when
  the row is opened.
