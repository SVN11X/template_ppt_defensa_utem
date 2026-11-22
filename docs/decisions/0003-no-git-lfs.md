# 0003. No Git LFS

- Status: proposed
- Date: 2026-11-22
- Proposed by: Claude Code
- Accepted by: pending

## Context

The owner's other repositories keep large slides and PDFs in Git LFS. This repository is a GitHub template, and "Use this template" does not copy LFS files into the new repository.

## Decision

Keep every file under 5 MB and out of LFS. The catalog weighs about 160 KB and each brand manual PDF about 1 MB.

## Alternatives considered

LFS for the PDFs, as in other repositories. Students would get pointer files instead of the manuals.

## Consequences

Large media, like the workshop videos, stay out of git. If a file over 5 MB is ever needed, link it instead.
