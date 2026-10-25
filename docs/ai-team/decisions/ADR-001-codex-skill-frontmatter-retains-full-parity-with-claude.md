---
id: ADR-001
title: Codex skill frontmatter retains full parity with Claude
status: superseded
superseded_by: ADR-003
created: '2026-06-05'
---

# ADR-001: Codex skill frontmatter retains full parity with Claude

## Context

The AI-team framework ships skills for two runtime targets: Claude (`.claude/skills/`) and
Codex (`.codex/skills/`). Since CR-002 (2026-10-20), Codex skills are exported to
`.agents/skills/`; the decision below is unaffected. Each skill is authored once in a source tree and exported as a
scaffold for both tools.

During the 2026-05 full-skills review (issue P2), a question arose
about whether the `[codex]` section of every exported `SKILL.md` should carry the same
frontmatter keys as the `[claude]` section or a reduced subset. The concern was that some
keys — `allowed-tools`, `argument-hint`, `effort`, and `disable-model-invocation` — might
be Claude-specific and unnecessary overhead for Codex.

The decision was confirmed with the human maintainer: Codex retains full frontmatter parity.

## Decision

The `[codex]` section header in every exported `SKILL.md` retains the complete frontmatter
key set: `allowed-tools`, `argument-hint`, `effort`, and `disable-model-invocation`. No key
is stripped or omitted from the Codex section relative to the Claude section.

Parity is relative between the two runtime headers, not a requirement that every optional
key appear on every skill. When an optional key does not apply, it is omitted from both
headers. In particular, a skill referenced through `Skill(<name>)` must not set
`disable-model-invocation: true`, because doing so makes the declared in-process call
unreachable; omitting that key from both headers preserves parity.

Skill-to-skill wiring expressed via `Skill(<name>)` in `allowed-tools` (e.g.,
`Skill(new-adr)`) is preserved as-is in the Codex section. Future skill-creator
passes MUST NOT strip these keys from Codex headers.

## Consequences

### Positive

- A single authoring rule applies to both runtime targets — maintainers do not need to
  reason about which keys are valid for which tool.
- Skill-to-skill wiring via `Skill()` in `allowed-tools` works identically for both Claude
  and Codex consumers of the same exported scaffold.
- Declared skill-to-skill calls cannot target a skill that disables model invocation.
- Adding support for a new frontmatter key in future requires no special handling for Codex.

### Negative

- Codex scaffolds carry keys that Codex may not currently act on (e.g., `effort`). These
  are inert overhead until the Codex runtime gains support for them.

### Neutral

- The source-to-scaffold sync script (`sync_init_scaffolds.py`) requires no changes; it
  already copies frontmatter keys identically across both tool sections.

## Alternatives Considered

### Alternative A: Strip Codex-irrelevant keys from `[codex]` sections

**Description:** Identify keys only recognised by Claude (e.g., `effort`) and omit them
from Codex section headers, keeping Codex scaffolds minimal.

**Rejected because:** It creates a two-track authoring burden — authors must know which
keys apply to which tool — and risks accidentally removing keys like `allowed-tools` or
`Skill()` wiring that are semantically meaningful to any tool performing skill discovery
or routing. Parity is the simpler invariant to enforce.

### Alternative B: Maintain separate source files per runtime target

**Description:** Author a `body-claude.md` and `body-codex.md` for each skill, allowing
full divergence of frontmatter and body content between targets.

**Rejected because:** Substantially increases authoring effort and creates drift risk
between the two copies of every skill. The current single-source model is preferred.
