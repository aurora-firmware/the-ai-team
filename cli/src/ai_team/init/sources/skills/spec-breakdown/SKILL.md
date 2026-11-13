---
name: spec-breakdown
description: Decompose an approved specification into atomic, independent tasks. Use when a spec needs to be broken into executable work units.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(new-task), Skill(git-conventions)
effort: high
---

# Spec Breakdown

**Ownership boundary:** spec-breakdown owns plan coverage (the full set of tasks covers the entire spec), dependency ordering between tasks, and task boundary decisions (splitting or merging units of work).
Per-task shape rules are owned by the `new-task` skill.
Gate 2 technical readiness is owned by the `spec-breakdown-review` skill.

## Input Requirements

- **Approved work** — the path and ID of the approved specification (Gate 1 passed) or approved change-request.
- **Project structure** — the existing codebase layout to determine file paths.
- **Existing tasks** — current tasks from `ai-team list tasks --json`, to avoid conflicts or duplication.
- **Architecture documents** — the documents the project guidance names for architecture and technology (by default `docs/development/architecture.md` and `docs/development/tech_stack.md`), as updated by Step 0a.

S-000 is accepted as input for the project bootstrap tasks only. Every other input is a feature spec or a change-request.

## Procedure

Twice this procedure hands back to its caller for the Architect: at Step 0a and at Step 6.
Each time, stop and return the `role-report` report with `Result: PASS`, `Next Owner: Architect`, and a `Next Action` that names the Architect's skill, its inputs, and "then resume the Planner at `spec-breakdown` Step <n> with the Architect's report".
When you are resumed with that report, continue from the step that handed back.

### Step 0: Check Out the Planning Branch

**S-000.** If the request asks to plan solution work from S-000, refuse before any branch checkout: say that S-000 produces no solution work, create no task, and name the feature specs (listed by `ai-team list specs`) as the input.
Otherwise plan only the project bootstrap tasks for its development-infrastructure components, created in Step 3 with `spec` and `plan` set to `S-000` and `status: planned`. They produce:
- the answers to every Decisions needed, written by default to `docs/development/architecture.md` (high-level design of the solution components) and `docs/development/tech_stack.md` (the answers) at the repository root; when the project's rules say where such documents go, those rules win, and a task records the chosen location in the project guidance;
- environment configuration (container or environment manager, environment variables and settings) and a remote access check;
- coding guidelines (by default `docs/development/coding_guidelines.md`);
- internal documentation placeholders for the remaining documents;
- project guidance with the common rules and the build, test, lint and run commands;
- the README project description, written from S-000.

In a brownfield project (one with existing code, specs or documents), plan only the missing items; the product owner may skip items that already exist.

**Branch.** The breakdown runs on the planning branch of the spec or change-request it decomposes (`plan/<id>-…`), never on `{{integration_branch}}`.
If that branch exists, run the before-point Workspace Hygiene check from `git-conventions` and check it out.
If it does not — the approved spec is already on `{{integration_branch}}`, as S-000 is after Gate 1 — open one as **Opening a Planning Branch** in `git-conventions` describes.

**Change-request amendments.** For a change-request, apply each amendment its Possible Spec Amendments section proposes, on the planning branch: edit the spec, bump its minor `version`, add an Amendment Log row that names the change-request and the REQ/AC identifiers added, changed or retired, and commit (`docs(specs): amend <spec-id> for <cr-id>`). The product owner's approval covered the proposed amendments, not the wording you wrote. Then hand back for the Architect's `architecture-consistency-review` of each amended spec, with the approved change-request's path, and revise on its findings before Step 0a. This adds no product owner gate.

### Step 0a: Feature Architecture

Skip this step for S-000: its bootstrap tasks write the first architecture documents.

Hand back for the Architect's `feature-architecture` with the approved spec or change-request ID and path and the planning branch `plan/<id>-<slug>`.
When resumed, act on the Architect's `Result`:
- `PASS` — if the report lists Spec findings, apply each one on the planning branch, restating a technology choice as the requirement the technology must meet: amend a spec and record the change in its Amendment Log, or update a change-request's body in the tracker. Ask the product owner first when the restated requirement would change approved behaviour or the approved change-request intent. Then hand back for the Architect's `architecture-consistency-review` of the amended spec or change-request, and revise on its findings before Step 1. With no Spec findings, continue to Step 1.
- `BLOCKED` — when the work is S-000, skip this step. Otherwise supply the missing input it names and hand back again; if you cannot, return `Result: BLOCKED` with `Next Owner: Product Owner`, naming the input.
- `ESCALATE` — stop. Return `Result: ESCALATE` with `Next Owner: Product Owner`, appending the Architect's Escalation Request and Product Owner Escalation Report unchanged, as `role-report` Step 4 describes.

### Step 1: Identify Components

Read the specification and the architecture documents, and list every distinct unit of work: something that produces a single testable outcome.
Tasks follow the architecture documents and the ADRs. A task never chooses a technology or a design the architecture has not decided; a gap found while planning goes back to the Architect through Step 0a.

### Step 2: Define Dependencies

For each unit, determine what must exist before it can start: if one unit reads a file another creates, it depends on it.
Maximize independence — units that touch different files should not depend on each other. Where two units would create the same file, one creates it and the other modifies it, with a dependency.

### Step 3: Write Task Files

For each unit, invoke `new-task` with every input it lists, filled from the plan:
- `title` (starting with a verb: Implement, Add, Create, Fix), `priority`, `assigned-role` (the intended owner, or `unassigned`), `description`, `source-requirements`, `acceptance-criteria` and `interfaces`;
- `dependencies` from Step 2, and `files-to-touch`;
- `verification`, with the method chosen by `new-task`'s rule for choosing the method;
- `spec`: the ID of the spec or change-request whose requirements the task implements. A task that implements an amendment this plan makes to another approved spec carries that other spec's ID;
- `plan`: the ID of the spec or change-request being decomposed, for every task;
- `status`: `planned`.

The plan adds these rules to the inputs:
- **Regeneration** — a task regenerates the generated files (scaffolds, docs) its own change affects and lists them in `files-to-touch`. A plan never ends with a separate "regenerate everything" task.
- **Command reference** — a task that changes a command's arguments, options or help text lists the project's generated command reference, named in its guidance, in `files-to-touch`.
- **Documentation and tests** — when the spec changes user-facing behavior, commands, templates, guides, or workflow expectations, the documentation and test updates are tasks or acceptance criteria of this plan, not prerequisites. When none are needed, add no placeholder task.

Never invent product behavior during decomposition; unresolved behavior goes back to the product owner.

### Step 4: Validate the Plan

- **Coverage:** map every feature-spec REQ and AC to at least one task and its verification; use section-based coverage for change-requests, and the bootstrap scope (Step 0) for S-000.
- **Isolation:** if two tasks modify the same file, add a dependency between them.
- **Atomicity:** split any task that cannot be completed in a single agent pass.

### Step 5: Place Tasks

The tasks are `planned` in the tracker, outside version control: there is nothing to commit, and `/dev-loop` ignores them until Step 7 activates them.

### Step 6: Architect Preflight (Gate 2)

Run `ai-team list tasks --state planned --plan <spec-or-cr-id> --json` and collect the absolute `path` of each task; the tracker is outside the repository, so the Architect needs these paths.
Hand back for the Architect's `spec-breakdown-review` with the spec or change-request ID and path, the planning branch, and each task as `<task-id>: <absolute path>`.
When resumed, act on the Architect's `Result`:
- `PASS` — continue to Step 7.
- `FAIL` — make the Planner corrections it lists in the task files, then hand back again. For an architecture gap, run Step 0a again first, then revise the task to follow its decision.
- `BLOCKED` — supply the missing input it names and hand back again.
- `ESCALATE` — the approved specification must change. Stop and return `Result: ESCALATE` with `Next Owner: Product Owner`, appending the Architect's Escalation Request and Product Owner Escalation Report unchanged.

### Step 7: Merge the Planning Branch and Activate the Tasks

Only after Gate 2 returns `PASS`:
1. Run the before-point Workspace Hygiene check, then `git checkout {{integration_branch}}`.
2. If the planning branch has commits (`git rev-list --count {{integration_branch}}..plan/<id>-<slug>` is not 0), run `git merge --no-ff plan/<id>-<slug> -m "chore(plan): merge <id> <short-description>"`.
   If the merge conflicts, abort it with `git merge --abort` and stop: report the conflicting planning files to the product owner. Do not resolve planning conflicts automatically.
   A planning branch with no commits — S-000's bootstrap branch, or a change-request that amends no spec and changes no architecture document — is not merged.
3. Run the after-point Workspace Hygiene check.
4. Delete the planning branch with `git branch -d plan/<id>-<slug>`. If `-d` refuses, stop and report — never force deletion.
5. Activate the plan: for every task in `ai-team list tasks --state planned --plan <id>`, run `ai-team task set-status <task-id> pending`.

Until this step the tasks stay `planned`, and `{{integration_branch}}` carries none of the spec or change-request changes.

## Escalation

This skill raises no escalation of its own. It returns `ESCALATE` only to pass on the Architect's, from Step 0a or Step 6, with `Next Owner: Product Owner`.

## Output Format

- **Hand-back report** (Steps 0a and 6): `Result: PASS`, `Next Owner: Architect`, and the `Next Action` described at the top of the Procedure.
- **Final response:** the tasks now `pending`, approved at Gate 2 and activated after the planning branch merged. The plan is ready for the product owner to start `/dev-loop`; no further product owner review of the task plan is needed. Or the blocker or passed-on escalation that stopped the procedure.

## Quality Criteria

- Every task passes `new-task`'s Task Quality Rules.
- No two tasks modify the same file without an explicit dependency between them.
- The full set of tasks covers 100% of the specification (for S-000, its bootstrap scope).
