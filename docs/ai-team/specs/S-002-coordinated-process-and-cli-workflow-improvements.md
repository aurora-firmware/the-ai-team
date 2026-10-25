---
title: Coordinated Process and CLI Workflow Improvements
version: '0.4'
status: approved  # draft | review | approved | superseded
created: '2026-05-28'
author: planner
id: S-002
---

# Coordinated Process and CLI Workflow Improvements

<!--
This spec describes requirements and measurable criteria in prose.
It is not the implementation. Do not paste full configuration files,
build manifests, or implementation code into the sections below.
Concrete code belongs in the tasks the spec-breakdown skill produces
and in the Developer's output. See the Spec Authoring Guide for the
content contract this template implements.
-->

## Purpose

User feedback shows that the framework is too heavy for small changes, too easy
to run without documented project commands, and not explicit enough that
documentation and test updates must be planned as part of the work derived from
a specification. These gaps matter because the AI-team process relies on written
contracts: if task breakdown does not carry tests, docs, and project guidance
into implementation work, later autonomous loops either guess or escalate late.
When this work is complete, the framework has a lightweight change-request path,
spec breakdown plans documentation and test updates where relevant, review
skills steer agents toward technical verification, `ai-team init` creates stable
guidance-file templates, and `dev-loop` refuses to start when baseline tests
cannot be discovered or do not pass.

## Exclusions

What this specification explicitly does NOT cover:

- **Final field-level change-request schema.** This specification creates the
  first-class document type and defines its role, lifecycle expectations, and
  required relationships to tasks and spec amendments. The exact section
  layout, frontmatter fields, and CLI prompts are left to task breakdown and
  implementation design.
- **Network-sourced best-practice lookup during init.** Guidance-file contents
  must come from stable templates owned by this repository. Future releases may
  update those templates, but `ai-team init` must not depend on live external
  lookups.
- **Splitting this work into separate specs.** A process-only spec and a
  CLI-only spec were considered and rejected because the dev-loop baseline test
  rule depends on the project guidance files that init creates.
- **Replacing the full brainstorm path.** `change-request` is a lighter path
  for smaller changes. Larger features still use brainstorm, full spec
  approval, task breakdown, and Gate 1/Gate 2 as defined by the workflow.

Alternatives considered:

- **Coordinated framework and CLI spec.** Chosen because the baseline-test
  startup guard, generated guidance files, and lighter change intake reinforce
  one another.
- **Process-first spec with CLI templates deferred.** Rejected because it would
  require `dev-loop` to discover documented test commands before init helps
  users create the guidance files that hold those commands.
- **CLI-led onboarding spec with process changes secondary.** Rejected because
  the lightweight change path is a first-class user need, not a follow-up to
  init behavior.

## Architecture

### Design Principles

- **Small changes must have a smaller intake path.** The process must support
  change descriptions and spec amendments without forcing every request through
  the full brainstorm-to-spec flow.
- **Project-specific commands must be documented, not guessed.** Autonomous
  loops must discover test commands from project guidance or escalate to a
  human when the command is missing or ambiguous.
- **Generated guidance must be stable and reviewable.** Templates for
  `AGENTS.md` must live in this repository, be versioned with
  the CLI, and be updateable through normal review.
- **Review gates must stay focused on their owner.** `spec-breakdown-review`
  must evaluate technical readiness of the task plan, not reopen broad product
  or spec approval questions already handled by Gate 1.
- **Documentation and tests are derived-work concerns.** Spec breakdown must
  explicitly consider whether documentation and tests need updates and, when
  they do, include those updates in the generated implementation tasks.

### System Diagram

```
Human request
  |
  +--> brainstorm ------------------> spec ------------------> spec-breakdown
  |        |                            |                           |
  |        +--> requirements context    +--> docs/tests task planning
  |                                                                v
  +--> change-request ---------------> tasks and/or amendments -> Gate 2
                                                                  |
                                                                  v
ai-team init -> guidance templates -> project/root guidance -> dev-loop
                                                        |          |
                                                        +----------+
                                                   test command discovery
```

### Responsibility Separation

| Component | Responsibility | Notes |
|---|---|---|
| Spec breakdown flow | Produces implementation tasks from specifications and plans documentation and test updates as work items when relevant. | Includes `spec-breakdown`, `new-task`, and task authoring guidance. |
| Change-request flow | Captures smaller desired changes, links them to tasks and possible spec amendments, and avoids unnecessary full-spec ceremony. | New document type with CLI and process support. |
| Gate 2 review | Validates task-plan technical readiness. | Feedback focuses on dependencies, file conflicts, architecture consistency, atomicity, and verification. |
| Init guidance files | Creates stable guidance files that explain project artifacts and root project commands. | `ai-team/AGENTS.md` is always generated; root `AGENTS.md` is an optional prompt when missing (CR-007). |
| Dev loop | Starts autonomous task execution only when the baseline is suitable. | Uses the CLI task listing interface and escalates when tests are failing or undiscoverable. |

## Components

### Component 1: Spec Breakdown Planning Updates

**Purpose:** Ensure task breakdown explicitly considers documentation changes and test coverage as implementation work derived from the spec.
Amendment 2026-10-19: each task also names the interfaces it consumes and produces, and carries no placeholder text (see the Amendment Log).
Amendment 2026-10-20 (CR-003):
- **Verification mode per task.** Spec breakdown decides, for each task, whether it is verified by a **test** or by a **design review**. A task that changes code, CLI output, or a rule a test can observe gets a test, and the test file is in Files to Touch. A task that changes only prose (guides, process docs, skill wording that no test pins) gets a design review: a consistency check of the changed text against the source spec, accepted ADRs and the system overview (S-000) when it exists. The Verification section of a design-review task names the review and lists every reference it checks, including S-000 when it exists, instead of a test command. The Developer records the review in the Work Log (documents checked, each conflict found and fixed, result), and the Reviewer checks that record and the planning choice.
- **Regeneration inside each task.** A task regenerates the scaffolds and docs its own change affects and lists the generated files in Files to Touch; a plan never ends with a separate "regenerate everything" task. A task that changes a command's arguments, options or help text lists the project's generated command reference (in this repository, `cli/docs/commands.md`) in Files to Touch; the command that regenerates it is the consuming project's own, named in its guidance, and the skills do not hardcode it.
- **Verification run context.** Each Verification line runs from the repository root in a fresh shell, independently of the other lines; a line that needs another directory changes into it on that line. The task template, `new-task` and the integration step that runs the verification command set follow this rule.
**Estimated size:** Small.
**Interfaces:** `spec-breakdown`, `new-task`, `tdd` (design-review tasks), `integrate`, task template guidance, spec authoring guide references.

### Component 2: Change Request Document Type

**Purpose:** Provide a lightweight artifact for smaller changes that may produce tasks and spec amendments without a full new spec.
**Estimated size:** Medium.
**Interfaces:** New CLI artifact command, template, Planner process, task creation and amendment workflows.

### Component 3: Technical Gate 2 Review

**Purpose:** Make `spec-breakdown-review` feedback focus on technical task-plan criteria.
Amendment 2026-10-19: the technical criteria include type and name consistency of the interfaces tasks consume and produce (see the Amendment Log).
Amendment 2026-10-20 (CR-003): Gate 2 accepts a named design review, with its listed references, as the verification of a task that changes only prose; a task that changes behaviour a test can observe still needs a test (see Component 1).
**Estimated size:** Small.
**Interfaces:** `spec-breakdown-review` skill, quality gates, workflow overview, Architect role guidance.

### Component 4: Init Guidance Templates

**Purpose:** Generate repository-owned guidance files for project artifact explanation and root project commands.
**Estimated size:** Medium.
**Interfaces:** `ai-team init`, packaged templates, setup/customization guides, CLI docs and tests.

### Component 5: Dev Loop Startup Guard

**Purpose:** Prevent autonomous development from starting when the branch has failing tests or no clear test command.
**Estimated size:** Small to medium.
**Interfaces:** `dev-loop` skill, CLI task listing, project guidance files, escalation procedure.

## Workflow

```
Human requests a large feature
  ↓
Planner uses brainstorm to create a full spec
  ↓
★ Gate 1 approval
  ↓
Spec breakdown identifies required docs/tests work
  ↓
Technical Gate 2 review
```

```
Human requests a smaller change
  ↓
Planner uses change-request intake
  ↓
Change request records desired changes and possible spec amendments
  ↓
Tasks and amendments are created as needed
  ↓
Technical Gate 2 review
```

```
Human runs ai-team init
  ↓
CLI creates ai-team/AGENTS.md
  ↓
CLI asks whether to create a missing root AGENTS.md
  ↓
Root guidance captures project commands, including tests when known
```

```
Human starts dev-loop
  ↓
dev-loop discovers pending tasks through the ai-team CLI state filter
  ↓
dev-loop discovers and runs the documented baseline test command
  ↓
Tests pass -> task execution begins
Tests fail or command is missing/ambiguous -> escalate to human
```

## Configuration Requirements

- **What must exist:** A stable `ai-team/AGENTS.md`
  template that explain the purpose of generated project artifact folders and
  files.
  **Where it lives:** CLI package template sources and generated init
  scaffolds.
  **Constraints:** Generated on every init run unless collision protection
  refuses overwrite; content is repository-owned and reviewable.
  **Missing-value behaviour:** If the destination exists and overwrite is not
  allowed, init must report the collision rather than silently replacing it.

- **What must exist:** A stable root `AGENTS.md` template for
  project-specific agent guidance.
  **Where it lives:** CLI package template sources, offered by `ai-team init`
  for the target repository root.
  **Constraints:** The CLI asks before creating a missing root `AGENTS.md`; existing
  root files are not overwritten without explicit overwrite behavior.
  **Missing-value behaviour:** If the human declines creation, init completes
  but prints follow-up guidance that autonomous loops need documented project
  commands.

- **What must exist:** A discoverable project test command or explicit statement
  that no automated tests are available.
  **Where it lives:** Root guidance files, project-local docs referenced by
  root guidance, or other documented project command surfaces accepted by the
  framework.
  **Constraints:** The command must be clear enough for `dev-loop` to run
  without choosing between alternatives. It must represent the baseline test
  check for the current branch before task execution starts.
  **Missing-value behaviour:** `dev-loop` escalates to the human instead of
  starting.

- **What must exist:** A CLI-supported way to list tasks by lifecycle state.
  **Where it lives:** `ai-team list tasks` command and CLI documentation.
  **Constraints:** `dev-loop` must use the CLI task listing interface, including
  the documented state filter such as `ai-team list tasks --state <state>`, rather
  than treating filesystem listing as the primary queue API.
  **Missing-value behaviour:** If the CLI task listing cannot produce a
  trustworthy queue, `dev-loop` stops and reports the command failure.

## Implementation Order

| Phase | What | Depends On |
|---|---|---|
| 1 | Update process and skill guidance so spec breakdown plans docs/tests work and Gate 2 review remains technical. | Nothing |
| 2 | Add the change-request artifact contract, CLI support, and process references at a high level. | Phase 1 |
| 3 | Add stable guidance-file templates and init behavior for project and root `AGENTS.md`. | Phase 1 |
| 4 | Update dev-loop to use CLI task listing and enforce baseline test discovery/pass before starting. | Phases 1 and 3 |
| 5 | Update CLI docs, setup/customization guides, generated scaffolds, and tests for all new behavior. | Phases 2-4 |

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-19 | Task template gains an `Interfaces: Consumes / Produces` block; `new-task` bans placeholder text in a task; Gate 2 adds a type and name consistency check across tasks. Driven by issue #31 (superpowers comparison report items 2.1 and 2.2). | Gate 2 checked dependencies and file conflicts but could not catch one task defining `clearLayers()` while another calls `clearFullLayers()`, and nothing stopped placeholder vagueness reaching a task file. | None in flight |
| 2026-10-20 | Component 1: each task's verification mode is chosen during breakdown (test, or a design review whose Verification section lists the source spec, accepted ADRs and S-000 when it exists); each task regenerates the scaffolds and docs its change affects and lists `cli/docs/commands.md` when it changes a command's arguments, options or help; Verification lines run from the repository root in a fresh shell, one line at a time. Component 3: Gate 2 accepts a named design review for a prose-only task. Driven by CR-003 (report #8, #10, #12) and its Architecture Consistency Review findings F2 and F6. | A documentation-only task had no TDD path, so the Developer added an undeclared test that broke CI; a Verification block failed when run as one script; command-option tasks omitted `commands.md` and a final regeneration task found nothing to do; Gate 2 required a test or command for every task. | None in flight |
| 2026-10-22 | The init guidance files are `ai-team/CLAUDE.md` and `ai-team/AGENTS.md`, not `project/…`; the `dev-loop` queue uses `ai-team list tasks --state <state>`, not `--filter state`. Version bumped to 0.2 under the spec authoring guide's amendment rule. | The default project folder was renamed from `project` to `ai-team` on 2026-10-16, and `ai-team list` filters by state with `--state`. | None in flight |
| 2026-10-25 | The init guidance file is `AGENTS.md` only, in the project directory and at the root; `CLAUDE.md` is no longer generated. Driven by CR-007 and ADR-003. | Codex support was dropped and current Claude Code reads `AGENTS.md`. | None in flight |
| 2026-10-25 | Implementation Order phase 3 names `AGENTS.md` only. Wording only. Driven by the CR-007 spec-truth reconciliation (D1). | The CR-007 amendment missed this line; the merged init generates only `AGENTS.md`. | None in flight |
