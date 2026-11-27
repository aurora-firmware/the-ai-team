---
id: ADR-004
title: Every skill is invocable by the model and any agent
status: accepted
created: '2026-11-27'
---

# ADR-004: Every skill is invocable by the model and any agent

## Context

`status-report` set `disable-model-invocation: true`, and the skill template recommended it for product-owner-only actions, to keep roles from running a gate step on their own.
In practice the product owner had to name the skill explicitly whenever the main session should run it, adopter projects kept memories to work around it, and the main session could not start the step when asked in plain words.

## Decision

No skill sets `disable-model-invocation`. Every skill can be invoked by the model, the main session and any agent.
What keeps a role from overriding a gate is gate ownership in `ai-process/`: the product owner still decides Gate 1 and Gate 5, and the loops still start only when the product owner asks (`using-ai-team`).

## Consequences

- `status-report` runs whenever the product owner asks in any words, and the main session can run it for them.
- The skill template and the customization guide drop the `disable-model-invocation` guidance; the rule that a `Skill()` target must stay model-invocable (ADR-001, ADR-003) now holds for every skill by default.
- A skill that runs a product-owner decision relies on its description and on `using-ai-team`, not on the harness, to stay unused when nobody asked.

## Alternatives Considered

- **Keep the flag on `status-report` only:** it is the only user of the flag, and the friction it caused outweighed the protection, since the report itself decides nothing.
