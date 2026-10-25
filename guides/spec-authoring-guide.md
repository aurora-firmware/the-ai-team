---
title: "Spec Authoring Guide"
status: draft
created: 2026-05-15
---

# Spec Authoring Guide

A practical playbook for writing a specification that passes Gate 1 and gives the Planner enough information to decompose it into atomic tasks.

This guide is for the **author** of a spec — usually the Planner working interactively with the human during `/brainstorm`. Read it once before writing your first spec; refer back to the section recipes while writing.

## Before you write

A specification is a **contract**, not an implementation. Its readers are:

- The Planner, who must derive tasks from it.
- The Developer, who must satisfy every requirement.
- The Reviewer, who must verify the work matches the spec's intent.

Write so all three can do their job from the spec alone, without guessing what you meant.

## The content boundary

> A specification describes requirements, contracts, and measurable criteria in prose. It does not embed implementation code, configuration files, or build manifests.

**Belongs in the spec:** the problem, the outcome, the constraints, the interface contracts of the component or feature it covers (the decomposition into components lives in S-000), the success criteria, the exclusions.

**Does not belong in the spec:** function signatures, class layouts, full YAML/TOML/JSON config files, complete CI manifests, executable code that *is* the implementation, file-by-file task lists.

**Rare exception:** a code or config block is acceptable when the block *is itself the contract* — a public API schema, a wire-protocol fragment, an externally-fixed configuration key. Mark such blocks **Contract**, not **Example**. If unsure, use prose.

If you find yourself pasting a near-complete file, you are writing the implementation. Stop. Describe what the file must guarantee instead.

## How to write each section

The spec template follows this structure. The recipes below tell you how to write each section well, with a strong and a weak example for each.

### Purpose

**Recipe:** Three to four sentences, naming the S-000 component the spec covers.
1. The problem (what is broken or missing today).
2. Why it matters now (the constraint or trigger that forced the spec).
3. The outcome (what is observably true when the work is done).
4. Optional: the metric that confirms success.

**Strong:**
> CI does not run on pull requests, so broken tests reach `main` and block the next release. After the last release was delayed twice by lint failures discovered post-merge, we need automated checks on every PR. When this spec is satisfied, every PR targeting `main` runs the full test and lint suite before merge is enabled, and a failing check blocks the merge button in GitHub.

**Weak:** "Add CI to the project." (No problem, no outcome, no success metric.)

### Exclusions

**Strategy:** for every alternative considered during brainstorm, name what was rejected and why. For every scope-expanding question you heard ("should we also…?"), record the answer as an exclusion.

Almost every spec has at least one exclusion. "No exclusions apply" should be rare, and should follow an explicit confirmation from the human.

**Strong:**
> - **Deployment pipelines.** Excluded because this spec covers PR validation only; release pipelines are tracked separately under S-NNN.
> - **Coverage reporting.** Excluded because the team has not decided on a threshold; revisit after one month of PR-validation data.

**Weak:** "No exclusions." (Almost never true; often masks unresolved scope.)

### Architecture — Design Principles

**Recipe:** scoped to this spec, principles are **constraints on the design space**, not implementation choices. State each as a property the design must satisfy.

**Strong:**
> - Validation must run in under three minutes on the median PR so reviewers are not blocked.
> - The pipeline must reject unknown configuration keys instead of ignoring them.
> - All network access during validation must be limited to the repository's own dependency mirror.

**Weak:** "Use GitHub Actions." (Picks the implementation; better as a constraint: "must integrate with the project's existing PR review surface.")

### Interfaces

**Recipe:** cover the component or feature of this spec only; system-wide structure lives in S-000. Three lines max:

- **Purpose:** one sentence — what it does.
- **Estimated size:** a complexity hint (small / medium / large, or a rough effort estimate).
- **Interfaces:** what it exposes and what it consumes, named at the interface level.

Do not list functions. Do not list fields. Do not describe other components; point to S-000 instead.

### Workflow

**Recipe:** end-to-end flow from trigger to completion. Each step is a sentence or short phrase. Mark human gates with ★. Show error paths if a failure mode is interesting.

**Strong:**
```
PR opened or updated
  ↓
CI runner triggers test + lint suite
  ↓
Results posted as PR check
  ↓
★ Reviewer approves or requests changes (human)
  ↓
Merge enabled / blocked by check status
```

**Weak:** a code-flow walkthrough of one CI runner.

### Configuration Requirements

**Recipe:** for each setting, four bullets:

- **What must exist** — the requirement, named.
- **Where it lives** — env var, config file, CI variable, secret store — described, not pasted.
- **Constraints** — allowed range, format, security class.
- **Missing-value behaviour** — default, error, or refuse-to-start.

Do not paste a real configuration file. The Developer writes the file against the project's conventions; this section tells them what the file must guarantee.

**Strong:**
> - **Test command.** Must be discoverable from the project's `AGENTS.md` or `ai-team/docs/coding_guidelines.md`. The CI runner must read it from there, not hard-code it. If not found, the runner must fail with an actionable error rather than guessing.

**Weak:** a 20-line `ci.yml` snippet.

### Success Criteria

**Recipe:** a numbered list of criteria that together show the spec is satisfied. Each one is measurable; see [How to write measurable success criteria](#how-to-write-measurable-success-criteria).

### Implementation Order

**Recipe:** coarse phases (typically two to five), each delivering an observable outcome. State each phase's dependency on the previous ones.

A phase is not a task. The `spec-breakdown` skill produces the actual tasks from these phases.

**Strong:**
> | Phase | What | Depends on |
> |---|---|---|
> | 1 | PR-validation pipeline runs and reports its result on every PR. | — |
> | 2 | Merge button is blocked when the pipeline fails. | Phase 1 |
> | 3 | Pipeline results are visible in the project status dashboard. | Phase 1 |

**Weak:** a list of file paths and the functions to edit in each.

### Amendment Log

**Recipe:** leave the table empty when the spec is first written. Add rows only after Gate 1 approval, when scope changes while tasks are in flight. Each row: date, what changed, why, affected tasks. Each amendment bumps the spec's minor `version` (for example `0.1` → `0.2`). A spec-truth reconciliation row records a verdict, changes no scope, and does not bump `version`.

## The system overview spec (S-000)

S-000 is the canonical project-overview spec: one document that says what the project is, who it serves, and which components make it up. It is written in plain language for a reader who has never seen the project. It has seven sections, in this order:

1. **Purpose** — one short paragraph: what the project is and the outcome it exists to deliver.
2. **Users** — the users of the solution and in what situations, one line per kind of user, naming what each needs from it.
3. **Pain points** — the concrete problems those users have today that the project removes.
4. **Use cases** — the main things a user does with the system, each as one short scenario from the user's point of view and each tied to the pain point it removes.
5. **Solution overview** — how the system addresses the pain points, in a few paragraphs, without naming technologies.
6. **Components** — the parts the system is divided into. Each component entry gives its name, its owned responsibility (what it is for), its boundary (what it is not responsible for), and the other components it works with. Components are split into the Solution and Development infrastructure groups (below).
7. **Project exclusions** — what the project deliberately does not do, each with a one-line reason.

S-000 contains no technology choices, interface definitions, configuration, implementation order, or per-component status. Those belong in feature specs, ADRs, and the tracker.

**What a component is.** A component is a part of the software solution, or something that affects the solution's use, delivery or deployment. A component can be software, documentation (internal or for end users), delivery and deployment (pipelines, scripts), or tooling (development environment, debugging interfaces, test harnesses). Each component passes three checks: it serves at least one use case, or, in the infrastructure group, affects the solution's use, delivery or deployment; one spec could own its contract; and its boundary would hold if the implementation were reorganised.

**Component groups.** Components fall into two groups, written as `### Solution` and `### Development infrastructure` subsections of Components; the seven top-level sections and their order do not change.

- **Solution** — the software delivered to the end user that removes the pain points.
- **Development infrastructure** — everything the project needs to build, check, document and deliver the solution; it is not delivered to the end user. Each infrastructure component also has a **Decisions needed** field: the questions that must be answered before development starts, such as the language and version, how the environment is reproduced, the test harness, the continuous-integration service, and where decisions are recorded. S-000 asks technology questions and never answers them; the answers belong in the project's internal development documentation, later specs and ADRs.

**Users scope.** Users names the users of the solution. The people and agents who develop the project are served by the development infrastructure and are not listed unless they also use the solution.

An S-000 with a single flat Components list, written before the groups existed, stays valid; the groups and Decisions needed apply when S-000 is created or amended.

**Boundary rule:** S-000 owns the decomposition — which components exist and what each is for. A spec owns the contract of one component or feature. A spec's Purpose names the S-000 component it covers.

## How to write measurable success criteria

A criterion is **measurable** when an outside party can run a check (a command, an observation, a metric query) and get an unambiguous pass or fail. The Reviewer must be able to run this check.

**Good:**
- "Every PR targeting `main` shows a `ci/tests` check that has either passed or failed within five minutes of the PR being opened."
- "Merging a PR with a failing `ci/tests` check is rejected by branch protection (verified by attempting the merge and observing the API response)."

**Vague (avoid):**
- "The CI is fast."
- "The CI works well."
- "Coverage is high."

If you cannot describe how to check whether a criterion is met, the criterion is not yet measurable.

## Worked example (compact)

Feature request: "Run our test suite automatically on every PR so we stop merging broken code."

```markdown
## Purpose
PR reviewers cannot tell whether a change breaks the test suite without running it
locally, so broken tests reach `main`. The last two releases were delayed by lint
and test failures discovered post-merge. After this spec is satisfied, every PR
targeting `main` displays an automated check whose pass/fail status reflects the
full test and lint suite, and the merge button is disabled until the check passes.

## Exclusions
- **Release pipelines.** Excluded; covered by a separate forthcoming spec.
- **Coverage reporting.** Excluded; team has not agreed on a threshold.
- **Self-hosted runners.** Excluded; the project's CI surface is project-hosted.

## Architecture
### Design Principles
- Validation must run in under three minutes on the median PR.
- The pipeline must reject unknown configuration keys instead of silently ignoring them.
- The test command must be discovered from project documentation, not hard-coded.

## Interfaces
### CI Runner
Purpose: Run the project's full test and lint suite on a PR's HEAD commit.
Estimated size: medium.
Interfaces: consumes PR events; emits a runner result with pass/fail + log URL.

## Workflow
PR opened or updated → CI runner triggers → results posted as PR check →
★ Reviewer approves → merge enabled iff check passes.

## Configuration Requirements
- **Test command.** Must be discoverable from `AGENTS.md` or `ai-team/docs/coding_guidelines.md`.
  If not found, the runner must fail with an actionable error.
- **Trigger event filter.** Must be configurable to PR-opened, PR-updated, and rerun-on-request.
- **Network policy.** During validation, network access must be limited to the project's dependency mirror.

## Success Criteria
1. Every PR targeting `main` shows a check that passed or failed within five minutes of opening.
2. A PR with a failing test cannot be merged.

## Implementation Order
| Phase | What | Depends on |
|---|---|---|
| 1 | PR-validation pipeline runs on every PR and reports its result. | — |
| 2 | Merge button is blocked when the pipeline fails. | Phase 1 |
| 3 | Pipeline results visible in the project status dashboard. | Phase 1 |
```

This is ~40 lines, has no implementation code, no YAML, no function names — and it is sufficient for the Planner to derive tasks for the runner and the merge-block configuration.

## Pre-submission checklist

Before declaring the spec ready for Gate 1, the author confirms each of these:

- [ ] **Problem is concrete.** Purpose names the problem, the trigger, and the observable outcome.
- [ ] **At least one exclusion.** Or a human-confirmed "no exclusions apply" statement.
- [ ] **Each design principle is a constraint, not an implementation choice.**
- [ ] **No implementation artefacts.** No full config files, no CI manifests, no function-by-function decompositions. Where a literal value is the contract, it is labelled **Contract**.
- [ ] **Every requirement is measurable.** An outside reader can describe how to verify it.
- [ ] **Interfaces are described for this spec's own component or feature**, at the interface level. No method signatures, no attribute lists.
- [ ] **Success Criteria are listed**, each one measurable.
- [ ] **Implementation Order has coarse phases**, not tasks.
- [ ] **Amendment Log is empty** (until amendments arrive after Gate 1).

If every box is checked, the spec is ready for Gate 1.

## Implementations of this guide

The recipes above are embedded into the CLI sources that fire when `/new-spec` is invoked or when `/brainstorm` produces a spec. Update them together when this guide changes:

| Implements this guide | File |
|---|---|
| Spec document shape | `cli/src/ai_team/templates/spec.md` |
| Section-by-section authoring instructions used by `/new-spec` | `cli/src/ai_team/init/sources/skills/new-spec/SKILL.md` |
| Spec-writing handoff in interactive brainstorm | `cli/src/ai_team/init/sources/skills/brainstorm/SKILL.md` |
| Planner role's spec quality bar | `cli/src/ai_team/init/sources/agents/planner.md` |
| System overview (S-000) document shape | `cli/src/ai_team/templates/system-overview.md` |
| Authoring instructions used by `new-system-overview` | `cli/src/ai_team/init/sources/skills/new-system-overview/SKILL.md` |

After changing this guide, mirror the relevant content into the files above and regenerate scaffolds with `cli/scripts/sync_init_scaffolds.py`.
