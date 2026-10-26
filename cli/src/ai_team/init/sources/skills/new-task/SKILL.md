---
name: new-task
description: Create a new task via the ai-team CLI. Use when a task file must be created, such as during spec breakdown or for a follow-up task.
argument-hint: "[optional: task title]"
allowed-tools: Read, Write, Bash
---

# New Task

Create a new task.

**Ownership boundary:** new-task owns per-task shape — every field of a single task file: title, description, acceptance criteria, verification, and task quality rules.
Plan-level rules (coverage, dependency ordering, file conflicts across tasks) are owned by the `spec-breakdown` skill.
Gate 2 technical readiness review is owned by the `spec-breakdown-review` skill.

## Input Requirements

Provide these values directly when possible:
- `title` — required
- `description` — required when the caller wants Description filled immediately
- `priority` — required (`critical`, `high`, `medium`, or `low`)
- `assigned-role` — optional; defaults to `unassigned`
- `acceptance-criteria` — optional list to replace `AC-1 ...` placeholders
- `spec` — optional; the source spec or change-request ID
- `status` — optional; `planned` for tasks created during a spec breakdown (kept out of `/dev-loop` until the plan merges), otherwise `pending`

When invoked by another skill, the caller should provide every required field in the invocation text and this skill must use them without asking follow-up questions.
When invoked directly by a human and required fields are missing, ask for the missing values before proceeding.

## Procedure

1. Resolve inputs:
   - Use the caller-provided `title`, `description`, `priority`, and `assigned-role` when they are present.
   - If invoked directly and some required fields are missing, ask only for the missing fields.
   - Use `$ARGUMENTS` as the title when it is the only provided input.
2. Run `ai-team task new "<title>" --priority <priority> [--assigned-role <assigned-role>] [--spec <spec>] [--status <status>] --json`.
   The task file is created in the local tracker, outside version control: never commit it.
3. Parse the JSON response and capture:
   - `id` (e.g., `T-003`)
   - `path` (absolute path to the created file)
4. If `description` was provided, replace the default text in `## Description` with the caller-provided content.
5. If `acceptance-criteria` were provided, replace placeholder `AC-*` lines in `## Acceptance Criteria` with the caller-provided list.
6. Leave Dependencies, Interfaces, Files to Touch, and Verification as template text only when the caller provided no values for them and the task will be completed before it leaves the Planner; a task that reaches Gate 2 contains no template text (see **No placeholders**).
7. Verify the drafted task (or placeholders that will be completed) can satisfy the Task Quality Rules below.
8. Confirm creation using the CLI response values (`id` and `path`).

## Verification Methods

A task is verified by one of three methods. `spec-breakdown` chooses the method; `new-task` records it in the task's Verification section.

- **Test** — an automated check in the project's test suite that runs the product and passes or fails by assertion. It is used for behavior the product exhibits. A test may check structure the product depends on, such as frontmatter that must parse. A test never asserts the wording of prose: skills, process documents, guides, user documentation, or specs.
  The Verification section holds the command(s), and the test files are listed in Files to Touch.
- **Inspection** — a reviewer reads the changed artifact, checks the observation each acceptance criterion states, and records what was checked and the pass or fail result. For prose, the inspection also checks that the text agrees with its references. It is used for prose, configuration, and changes that only remove something.
  The Verification section holds the line `Inspection:` followed by one bullet per acceptance criterion to check and one bullet per reference: the source spec, each accepted ADR the text must agree with, and the system overview S-000 when it exists.
- **Demonstration** — someone runs the product or a pipeline once, outside the test suite, and observes the outcome. It is used when the behavior depends on an environment the test suite cannot reproduce, such as a CI run or a published release.
  The Verification section holds the line `Demonstration:` followed by the command or steps to run and the expected observation.

Other skills detect an inspection or demonstration task by its `Inspection:` or `Demonstration:` line. The task template's Verification comment may precede that line, so they detect the line, not the first line of the section.
Every task, whatever its method, also runs the project's full test suite as a regression check; an inspection or demonstration task lists that command under its method's bullets.

**Choosing the method.** A task takes the method its source acceptance criteria name. When the source is a change-request or S-000, which have no acceptance criteria, apply the same rule: a test for product behavior that is added or changed, an inspection for prose, configuration, or a change that only removes something, and a demonstration for behavior that depends on the environment.

### Verification run context

Each Verification line runs from the repository root in a fresh shell, independently of the other lines.
A line that needs another directory changes into it on that same line, for example `cd <dir> && <command>`.

## Task Quality Rules

Every task file produced by this skill must be:

- **Atomic** — one clear outcome. If the task delivers two independent outcomes, split it into two tasks.
- **One-shottable** — completable in a single agent session without running out of context. Rules of thumb: touches at most **3–4 files**, has at most **5 acceptance criteria**, and the Description fits in roughly **20 lines**. If a draft task exceeds any of these, split it or narrow the scope.
- **Verifiable** — its Verification section proves the task is done by the method chosen under **Verification Methods**: a test command, an `Inspection:` list, or a `Demonstration:` with its steps and expected observation.
- **Self-contained** — the Description provides enough context for an agent to start without asking follow-up questions. Any prior decisions, files, or conventions the task depends on are named explicitly.
- **Source-traceable** — fill Source Requirements with the source spec ID, REQ identifiers, and AC scenarios implemented or verified. For a change-request or S-000, cite the relevant sections rather than inventing feature requirement identifiers. Preserve approved behavior when deriving task criteria.
- **EARS-compliant acceptance criteria** — every AC matches one of the five EARS patterns documented in the template (Ubiquitous, Event-driven, Unwanted-behaviour, State-driven, Optional). An AC that resists EARS usually means the task is not atomic.
- **Dependency-honest** — if the task reads or modifies something that another pending task creates, list that other task ID under `Dependencies`.
- **Interface-explicit** — the `Interfaces` block names, exactly as they will appear in code, each type, function, or file the task **Consumes** (and the task that produces it) and **Produces**. Write `none` when there are none; never leave the block empty.
- **No placeholders** — none of these appear in a task: `TBD`, `TODO`, "implement later", "fill in details"; "add appropriate error handling", "add validation", or "handle edge cases" without saying what; "write tests for the above" without naming the behavior to test; "similar to Task N" instead of the actual content; or a reference to a type, function, or method that no task defines. Replace each with the concrete content before the task leaves this skill.

Rules that govern the *set of tasks* (no two tasks modifying the same file without a dependency, full coverage of the specification) are enforced by the `spec-breakdown` skill, not here. `new-task` enforces per-task shape; `spec-breakdown` enforces the plan as a whole.

## Common Pitfalls

- **Task is really two tasks** — reads like "Implement X AND migrate Y". Split.
- **Description is a ticket title, not enough to start** — agent has to open the spec or ask questions. Expand.
- **Acceptance criteria are aspirational, not testable** — "Works well under load" is not an AC. Name the measurable behaviour.
- **No verification** — if the task has no way to prove it's done, its acceptance criteria are not specific enough.
- **A test that pins prose** — a test that asserts the wording of a skill, guide, or process document. That change is verified by inspection.
- **A test that proves a removal** — such as "command is not registered". A change that only removes something is verified by inspection, with the full suite as the regression check.
- **Placeholder survives** — "add error handling" or "similar to T-004" reads like a plan but is not one. Name the handling or repeat the content.
- **Mismatched interface names** — the task consumes `clearFullLayers()` while its dependency produces `clearLayers()`. Copy names from the producing task.
- **Hidden dependency** — the task reads a file a sibling task creates but no dependency is listed. The `spec-breakdown` Gate 2 preflight will catch this, but it's cheaper to catch here.
