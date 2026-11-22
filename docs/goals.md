# Goals

<!-- Written by the owner. AI tools may format or translate this file, never invent its content. Replace every TODO(owner) line. -->
<!-- Transcribed from the owner's answers on 2026-11-22. -->

## Vision

A public template that any UTEM student can use to build a thesis defense presentation that looks like the owner's real defense, in language anyone on the commission understands.

## Users

UTEM undergraduate students of any faculty who are preparing their thesis defense. Each student creates a copy with "Use this template", puts their thesis in `thesis/` and works with Claude Code inside that copy.

## Objectives

1. A catalog of slide patterns taken from the owner's real defense (doc_tesis), made generic with [markers].
2. Claude Code reads the thesis and writes the slide text, the speaker script with seconds per slide, the hidden backup slides and a rehearsal plan.
3. One command builds the presentation from that text.
4. Plain language, so students and commission members outside the specialty understand it.

## Non-goals

1. Per-faculty color variants. The template uses only the UTEM blue and green.
2. Publishing third-party material: workshop videos and transcripts stay local, official UTEM documents are linked, not uploaded.
3. Copying or linking the owner's own defense. Only its method and design are reused.

## Success criteria

1. The template follows the UTEM visual identity manual: colors 004EAA and 78BF26, the right logo and its clear space.
2. Claude Code never invents numbers. Every missing figure, chart or piece of evidence is marked with [brackets].
3. The guide includes what the owner learned in the real defense: timing per slide, backup slides and the questions the commission asks.

## Priorities

1. Plain language over technical detail.
2. The look of the real defense over the old template.

## Constraints

1. PowerPoint files (.pptx and .potx) with the Calibri font.
2. Claude Code inside the student's copy of the repository. The thesis stays local in `thesis/`.
3. The repository is public: nothing private of the owner or the students, and no file whose license does not allow it.
