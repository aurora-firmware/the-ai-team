---
id: ADR-003
title: Claude is the only export target
status: accepted
created: '2026-10-25'
supersedes: ADR-001
---

# ADR-003: Claude is the only export target

## Context

The framework exported its agents and skills for two tools, Claude and Codex. Each skill
carried a `[claude]` and a `[codex]` header, each agent existed as Markdown and TOML, and
`ai-team init` and `ai-team check-layout` branched per tool. ADR-001 fixed one rule of that
design: the `[codex]` skill header keeps full frontmatter parity with the `[claude]` header.

CR-007, approved by the product owner on 2026-10-25, removes Codex support and asks that the
framework be simplified wherever the two-tool design added indirection. It also names the
generated guidance file `AGENTS.md`, which current Claude Code reads.

## Decision

Claude is the only export target. `ai-team init` always writes the Claude agents and skills,
with no tool selection, and generates `AGENTS.md` as the only guidance file. There is no
backward compatibility for Codex or for the `[init].tools` setting.

ADR-001 is superseded: with no `[codex]` header, a parity rule between headers has no
subject. Its one tool-independent rule — a skill referenced through another skill's
`Skill(<name>)` declaration must not set `disable-model-invocation: true` — stays in force.
`guides/skill_template.md` already owns it (the `disable-model-invocation` rules and the
authoring checklist); this ADR does not restate it.

## Consequences

### Positive

- Each skill and agent is authored once, in the form Claude reads, with no header merge.
- `init`, the layout check, the generator and the tests lose their per-tool branches.

### Negative

- Projects that use Codex lose support, with no migration path.
- Projects whose guidance lives in `CLAUDE.md` must provide `AGENTS.md`.

### Neutral

- Adding another tool later would need a new decision and a new export design.

## Alternatives Considered

### Alternative A: Keep ADR-001 and limit it to the Claude header

**Description:** Keep ADR-001 accepted and read it as "the single header keeps the full key set".
**Rejected because:** A one-header parity rule says nothing; the surviving rule already lives
in `guides/skill_template.md`.

### Alternative B: Keep the per-tool layout for a future tool

**Description:** Drop Codex but keep `--tools`, `[init].tools` and per-tool folders.
**Rejected because:** The product owner chose to simplify wherever possible (CR-007).
