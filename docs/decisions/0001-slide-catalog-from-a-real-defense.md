# 0001. Slide catalog from a real defense

- Status: proposed
- Date: 2026-11-22
- Proposed by: Claude Code
- Accepted by: pending

## Context

The old template had 19 layouts with placeholders, but the owner's real defense, which is how the template should look, draws every slide on the blank layout and does not use those layouts. The owner wants the real look and a build that fills the slides from text.

## Decision

The template is a catalog of 17 pattern slides taken from that defense, with the author's text, pictures, icons and metadata removed. Text becomes `{{markers}}` and shape names tell the build what each shape is. `scripts/build_deck.py` copies the patterns and fills them. `scripts/make_catalog.py` rebuilds the catalog from the source deck.

## Alternatives considered

- Redraw the 19 layouts to match the defense. PowerPoint's "New slide" menu would work, but it takes longer and the result drifts from the real design.
- Draw each slide in code. Every design detail would have to be rewritten by hand.

## Consequences

The catalog looks exactly like the real defense and a student can still open the .potx and copy patterns by hand. A design change means editing the source deck and running `make_catalog.py`, which only the owner can do. To undo, restore the previous .potx from git history.
