# 0002. Spanish field names and guide

- Status: proposed
- Date: 2026-11-22
- Proposed by: Claude Code
- Accepted by: pending

## Context

The users are UTEM students who write in Spanish, and the owner asked for language that anyone can follow. The standard asks for English everywhere except the document text in `content/`.

## Decision

Everything a student reads or writes is in Spanish and lives in `content/`: the guide, the slide content and the rehearsal plan. The fields of `content/01-defensa.yml` and the pattern names are Spanish words (`titulo`, `laminas`, `respaldo-alcance`), because students type them. Code, scripts, docs and commits stay in English.

## Alternatives considered

English field names, as in the code. Students would have to learn a second vocabulary to fill a Spanish presentation.

## Consequences

The build script maps Spanish keys, so renaming a field means changing the catalog markers and the example. The README stays in English and points to the guide.
