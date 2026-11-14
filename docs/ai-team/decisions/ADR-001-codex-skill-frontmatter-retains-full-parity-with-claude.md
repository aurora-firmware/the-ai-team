---
id: ADR-001
title: Codex skill frontmatter retains full parity with Claude
status: superseded
created: '2026-06-05'
---

# ADR-001: Codex skill frontmatter retains full parity with Claude

## Context

The framework exported every skill for two tools, Claude and Codex, so each exported `SKILL.md` carried a `[claude]` and a `[codex]` frontmatter header (Codex skills go to `.agents/skills/` since CR-002).
The 2026-05 full-skills review asked whether the Codex header should drop the keys that looked Claude-specific: `allowed-tools`, `argument-hint`, `effort` and `disable-model-invocation`.

## Decision

The `[codex]` header keeps the same frontmatter keys as the `[claude]` header, including the `Skill(<name>)` wiring in `allowed-tools`, as the product owner confirmed.
An optional key that does not apply is omitted from both headers; in particular, a skill referenced through `Skill(<name>)` must not set `disable-model-invocation: true`.

## Consequences

- One authoring rule covers both tools, and `Skill()` wiring works the same for both.
- A declared skill-to-skill call cannot target a skill that disables model invocation.
- Codex scaffolds carry keys Codex may not act on yet, such as `effort`.
- `sync_init_scaffolds.py` needs no change.

## Alternatives Considered

- **Strip Codex-irrelevant keys from the `[codex]` header:** authors would need to know which keys apply to which tool, and meaningful keys such as `allowed-tools` or `Skill()` wiring could be removed by mistake.
- **Separate source files per tool:** more authoring effort, and the two copies of every skill would drift.
