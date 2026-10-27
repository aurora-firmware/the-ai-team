# Development Documentation

Internal documentation for the people and agents developing ai-team (S-000,
Internal documentation). None of it is delivered to adopting projects. This file
is the index of those documents; the rules agents follow are in the root
[`AGENTS.md`](../../AGENTS.md).

| Document | Where |
|---|---|
| Project rules and commands agents read first | [`AGENTS.md`](../../AGENTS.md) |
| Framework rules, the single source of truth | [`ai-process/`](../../ai-process/) (processes, guidelines, architecture) |
| Architecture of the solution components | [`architecture.md`](architecture.md) |
| Technology choices and infrastructure answers | [`tech_stack.md`](tech_stack.md) |
| Specs and ADRs for this repository | [`docs/ai-team/specs/`](../ai-team/specs/), [`docs/ai-team/decisions/`](../ai-team/decisions/), described in [`docs/ai-team/AGENTS.md`](../ai-team/AGENTS.md) |
| Coding guidelines | [`docs/ai-team/docs/coding_guidelines.md`](../ai-team/docs/coding_guidelines.md), extending [`ai-process/guidelines/coding_standards.md`](../../ai-process/guidelines/coding_standards.md) |
| Authoring contracts for agents, skills, specs and the system overview (S-000 has its own section in the spec authoring guide) | [`guides/agent_template.md`](../../guides/agent_template.md), [`guides/skill_template.md`](../../guides/skill_template.md), [`guides/spec_authoring_guide.md`](../../guides/spec_authoring_guide.md) |
| Method for testing a skill change | [`guides/skill_testing_guide.md`](../../guides/skill_testing_guide.md) |
| Maintainer notes (module map, adding a command, tests, scaffolds, build, release, release hygiene) | [`cli/docs/usage.md`, For Maintainers](../../cli/docs/usage.md#for-maintainers) |
| CI pipeline | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), described in [`tech_stack.md`](tech_stack.md#ci-pipelines) |
| Readme | [`README.md`](../../README.md) |
