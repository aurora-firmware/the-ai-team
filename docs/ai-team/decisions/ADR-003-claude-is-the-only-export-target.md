---
id: ADR-003
title: Claude is the only export target
status: accepted
created: '2026-10-25'
supersedes: ADR-001
---

# ADR-003: Claude is the only export target

## Context

The framework exported its agents and skills for Claude and Codex: each skill carried a `[claude]` and a `[codex]` header, each agent existed as Markdown and TOML, and `ai-team init` and `ai-team check-layout` branched per tool.
CR-007, approved by the product owner on 2026-10-25, removes Codex support, asks to simplify wherever the two-tool design added indirection, and names `AGENTS.md` as the generated guidance file.

## Decision

Claude is the only export target: `ai-team init` always writes the Claude agents and skills, with no tool selection, and generates `AGENTS.md` as the only guidance file. Codex and the `[init].tools` setting get no backward compatibility.
ADR-001 is superseded. Its one tool-independent rule, that a skill referenced through `Skill(<name>)` must not set `disable-model-invocation: true`, stays in force and is owned by `guides/skill_template.md`.

## Consequences

- Each skill and agent is authored once, and `init`, the layout check, the generator and the tests lose their per-tool branches.
- Projects that use Codex lose support with no migration path, and projects whose guidance lives in `CLAUDE.md` must provide `AGENTS.md`.
- Adding another tool later needs a new decision and a new export design.

## Alternatives Considered

- **Keep ADR-001, limited to the Claude header:** a parity rule with one header says nothing, and the surviving rule already lives in `guides/skill_template.md`.
- **Keep the per-tool layout for a future tool:** the product owner chose to simplify wherever possible (CR-007).
