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

## Verification Modes

A task is verified by a **test** or by a **design review**. `spec-breakdown` chooses the mode; `new-task` records the choice in the task's Verification section.

- **Test task** — the task changes code, CLI output, or a rule that a test can observe. Its Verification holds the command(s), and the test file is listed in Files to Touch.
- **Design-review task** — the task changes only prose (guides, process docs, skill wording that no test pins). In place of a command block, its Verification section holds the line `Design review:` followed by one bullet per reference the changed text must agree with: the source spec, each accepted ADR it must agree with, and the system overview S-000 when it exists. It holds no test command.
  Other skills detect a design-review task by this `Design review:` line.

### Verification run context

Each Verification line runs from the repository root in a fresh shell, independently of the other lines.
A line that needs another directory changes into it on that same line, for example `cd <dir> && <command>`.

## Task Quality Rules

Every task file produced by this skill must be:

- **Atomic** — one clear outcome. If the task delivers two independent outcomes, split it into two tasks.
- **One-shottable** — completable in a single agent session without running out of context. Rules of thumb: touches at most **3–4 files**, has at most **5 acceptance criteria**, and the Description fits in roughly **20 lines**. If a draft task exceeds any of these, split it or narrow the scope.
- **Verifiable** — has a concrete `Verification` command that proves the task is done. A task that changes only prose is verified by a design review instead (see **Verification Modes**). If neither is possible, the Verification section states the exact manual steps.
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
- **No verification command** — if the task has no way to prove it's done, its acceptance criteria are not specific enough. A prose-only task takes the design-review alternative (a `Design review:` line with its reference bullets) instead of a command.
- **Placeholder survives** — "add error handling" or "similar to T-004" reads like a plan but is not one. Name the handling or repeat the content.
- **Mismatched interface names** — the task consumes `clearFullLayers()` while its dependency produces `clearLayers()`. Copy names from the producing task.
- **Hidden dependency** — the task reads a file a sibling task creates but no dependency is listed. The `spec-breakdown` Gate 2 preflight will catch this, but it's cheaper to catch here.
