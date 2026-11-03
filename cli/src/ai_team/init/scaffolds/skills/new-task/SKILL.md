---
name: new-task
description: Create a new task via the ai-team CLI. Use when a task file must be created, such as during spec breakdown or for a follow-up task.
argument-hint: "[optional: task title]"
allowed-tools: Read, Write, Edit, Bash
---

# New Task

Create one task file and fill every section of it.
This skill owns the shape of a single task: its fields, the Verification Methods and the Task Quality Rules.
Plan-level rules (coverage, dependency ordering, file conflicts across tasks) belong to `spec-breakdown`, and Gate 2 to `spec-breakdown-review`.

## Input Requirements

Argument: `$ARGUMENTS`

- `title` — required
- `priority` — required: `critical`, `high`, `medium` or `low`
- `description` — the Description section
- `source-requirements` — the source spec ID, REQ identifiers and AC scenarios; for a change-request or S-000, its sections
- `acceptance-criteria` — the EARS criteria, replacing the `AC-*` placeholders
- `dependencies` — task IDs that must complete first, each with what it provides, or `None`
- `interfaces` — the **Consumes** and **Produces** names, or `none` for each
- `files-to-touch` — each file and the change it needs
- `verification` — the content for the method chosen (see Verification Methods)
- `assigned-role` — optional; defaults to `unassigned`
- `spec` — optional; the ID of the spec or change-request whose requirements the task implements
- `plan` — optional; the ID of the spec or change-request whose breakdown introduces the task, which can differ from `spec` when the task implements an amendment to another spec
- `status` — `planned` (the default): the task stays out of `/dev-loop` until its plan merges after Gate 2. `pending` only when the caller states the task is exempt from Gate 2, such as a follow-up task routed by spec-truth reconciliation

Every input except `assigned-role`, `spec`, `plan` and `status` is needed before the task can leave this skill.
A calling skill provides them all in the invocation text, and this skill uses them without follow-up questions.
When the product owner invokes it directly, ask only for the missing values.

## Procedure

1. Resolve the inputs. When the argument is the only input, it is the title.
2. Run `ai-team task new "<title>" --priority <priority> --status <status> [--assigned-role <role>] [--spec <spec>] [--plan <plan>] --json`, and capture `id` and `path` from the JSON response.
   The task file is in the local tracker, outside version control: never commit it.
3. Replace the template text of each section with its input: Description, Source Requirements, Acceptance Criteria, Dependencies, Interfaces, Files to Touch and Verification. For Verification, keep the template comment and replace the command block, as the method requires.
4. Check the filled task against the Task Quality Rules. Fix what fails, or, when an input is the cause, return it to the caller naming the rule.
5. Confirm creation with the `id` and `path` from the CLI.

## Verification Methods

A task is verified by one method. `spec-breakdown` chooses it; this skill records it in the Verification section.

- **Test** — an automated check in the project's test suite that runs the product and passes or fails by assertion, for behavior the product exhibits. A test may check structure the product depends on, such as frontmatter that must parse, but never asserts the wording of prose (skills, process documents, guides, user documentation, specs) and never only proves that something was removed (such as "command is not registered").
  The Verification section holds the command(s); the test files are listed in Files to Touch.
- **Inspection** — someone reads the changed artifact, checks the observation each acceptance criterion states, and records what was checked and the result; for prose, also that the text agrees with its references. The Developer carries it out and records it, and the Reviewer re-checks it. It is used for prose, configuration, and changes that only remove something.
  The Verification section holds the line `Inspection:`, one bullet per acceptance criterion to check, and one bullet per reference: the source spec, each accepted ADR the text must agree with, and S-000 when it exists.
- **Demonstration** — someone runs the product or a pipeline once, outside the test suite, and observes the outcome. It is used when the behavior depends on an environment the test suite cannot reproduce, such as a CI run, and must be observable from the task branch, because its record is checked before integration.
  The Verification section holds the line `Demonstration:`, the command or steps to run, and the expected observation.

A task is an inspection or demonstration task when its Verification section holds an `Inspection:` or `Demonstration:` line. The template's comment may precede that line, so detect the line, not the first line of the section.
Every task also runs the project's full test suite as a regression check when the project documents one; an inspection or demonstration task lists that command under its method's bullets.

**Choosing the method.** A task has the one method its source acceptance criteria name. When the criteria a piece of work covers name different methods, split it into one task per method. For a change-request or S-000, which have no acceptance criteria: a test for product behavior that is added or changed, an inspection for prose, configuration or a change that only removes something, and a demonstration for behavior that depends on the environment.

**Run context.** Each Verification line runs from the repository root in a fresh shell, independently of the other lines. A line that needs another directory changes into it on that line: `cd <dir> && <command>`.

## Task Quality Rules

Every task file this skill produces is:

- **Atomic** — one clear outcome. "Implement X and migrate Y" is two tasks.
- **One-shottable** — completable in one agent session: at most **3–4 files**, at most **5 acceptance criteria**, and a Description of about **20 lines**. Split or narrow a draft that exceeds them.
- **Verifiable** — its Verification section proves the task done by its method: a test command, an `Inspection:` list, or a `Demonstration:` with steps and the expected observation.
- **Self-contained** — the Description gives an agent enough context to start without questions, naming every prior decision, file and convention it depends on.
- **Source-traceable** — Source Requirements cites the source spec ID, REQ identifiers and AC scenarios implemented or verified; for a change-request or S-000, its sections, never invented identifiers. Approved behavior is preserved in the derived criteria.
- **EARS-compliant** — every acceptance criterion matches one of the five EARS patterns in the template, and is measurable ("works well under load" is not). A criterion that resists EARS usually means the task is not atomic.
- **Dependency-honest** — a task that reads or modifies something another pending task creates lists that task under `Dependencies`.
- **Interface-explicit** — `Interfaces` names, exactly as they will appear in code, each type, function or file the task **Consumes** (with the task that produces it) and **Produces**, copied from the producing task (a task consuming `clearFullLayers()` from one that produces `clearLayers()` fails). `none` when there are none; never empty.
- **No placeholders** — no `TBD`, `TODO`, "implement later" or "fill in details"; no "add appropriate error handling", "add validation" or "handle edge cases" without saying what; no "write tests for the above" without naming the behavior; no "similar to Task N" in place of the content; no reference to a type, function or method that no task defines.
