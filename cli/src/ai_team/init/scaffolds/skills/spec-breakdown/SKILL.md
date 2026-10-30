---
name: spec-breakdown
description: Decompose an approved specification into atomic, independent tasks. Use when a spec needs to be broken into executable work units.
allowed-tools: Read, Grep, Glob, Write, Bash, Agent, Skill(new-task), Skill(git-conventions)
effort: high
---

# Write Plan

**Ownership boundary:** spec-breakdown owns plan coverage (the full set of tasks covers the entire spec), dependency ordering between tasks, and task boundary decisions (splitting or merging units of work).
Per-task shape rules are owned by the `new-task` skill.
Gate 2 technical readiness is owned by the `spec-breakdown-review` skill.

## Input Requirements

- **Approved specification** — the spec that passed Gate 1 (Spec Approval).
- **Project structure** — the existing codebase layout to determine file paths.
- **Existing tasks** — current tasks from `ai-team list tasks --json`, to avoid conflicts or duplication.
- **Architecture documents** — the documents the project guidance names for architecture and technology (by default `docs/development/architecture.md` and `docs/development/tech_stack.md`), as updated by the Feature Architecture step below.

S-000 is the project overview. It is accepted as input for the project bootstrap tasks only, which cover its development-infrastructure components. Every other input is a feature spec or a change-request.

## Procedure

### Step 0: Check Out the Planning Branch
If the spec to break down is S-000, plan only the project bootstrap tasks for its development-infrastructure components, using `ai-team task new --spec S-000`; the plan goes through Gate 2 (Steps 6 and 7) as usual. If the request asks to plan solution work from S-000, refuse before any branch checkout, say that S-000 produces no solution work, create no task, and name the feature specs (listed by `ai-team list specs`) as the input.
The bootstrap tasks produce: the answers to every Decisions needed, written by default to the `docs/development/` folder at the repository root, in `docs/development/architecture.md` (high-level design of the solution components) and `tech_stack.md` (the answers); when the project's rules say where such documents go, those rules win, and a task records the chosen location in the project guidance; environment configuration (container or environment manager, environment variables and settings); a remote access check; coding guidelines; internal documentation placeholders for the remaining documents; project guidance with the common rules and the build, test, lint and run commands; and the README project description written from S-000.
In a brownfield project (one with existing code, specs or documents), plan only the missing items; the product owner may skip items that already exist.
The breakdown runs on the planning branch of the spec or change-request it decomposes (`plan/<id>-…`), never on `{{integration_branch}}`.
If that branch exists, run the before-point Workspace Hygiene check from the `git-conventions` skill and check it out.
If it does not exist — the approved spec is already on `{{integration_branch}}` — open one as described in **Opening a Planning Branch** in the `git-conventions` skill.

### Step 0a: Feature Architecture
Skip this step for S-000: its bootstrap tasks write the first architecture documents.
For a feature spec or change-request, the Architect decides how the work is built before any task is written.

**Spawn the Architect subagent** (tier: most capable) with this prompt:

> "Decide the feature architecture for the approved spec or change-request `<spec-or-cr-id>` at `<path>`, on the planning branch `plan/<id>-<slug>`.
> Use the feature-architecture skill.
> Return `Result: PASS` with the Covered and Decided lists when every need is covered or decided, or `Result: ESCALATE` when a need must go to the product owner.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the Architect to complete.
If the Architect escalates, stop and return the escalation to the product owner using the Phase 2 product owner report template defined in the `escalation-review` skill.
If the output lists Spec findings, amend the spec on the planning branch to state the requirement instead of the technology, and record the change in its Amendment Log. When the restated requirement would change approved behaviour, ask the product owner first.

### Step 1: Identify Components
Read the specification and the architecture documents, and list every distinct unit of work.
Tasks follow the architecture documents and the ADRs; a task never chooses a technology or a design the architecture has not decided. A gap found while planning goes back to the Architect through Step 0a.
A unit of work is something that produces a single testable outcome.

### Step 2: Define Dependencies
For each unit, determine what must exist before it can start.
Draw a dependency graph.
Maximize independence — units that touch different files should not depend on each other.

### Step 3: Write Task Files
For each unit, invoke the `new-task` skill to create the task file. Provide the full required input set in the invocation text:
- `title`: the task title
- `description`: the task description
- `priority`: the task priority
- `assigned-role`: the intended owner, or `unassigned`
- `spec`: the ID of the spec or change-request being decomposed
- `status`: `planned`

The `new-task` skill handles template loading, ID assignment, filename, and frontmatter scaffolding. Because all required fields are provided here, it should not ask follow-up questions.

Then fill in the task body so it satisfies:
- **Title**: Clear, descriptive, starts with a verb (Implement, Add, Create, Fix).
- **Description**: Enough context to start without asking questions.
- **Source requirements**: Name each feature-spec REQ and AC covered by the task. For change-requests and S-000, cite sections instead. Never invent product behavior during decomposition; unresolved behavior goes back to the product owner for clarification.
- **Acceptance criteria**: Author every criterion using one of the five EARS patterns documented in the task file the CLI created (Ubiquitous, Event-driven, Unwanted-behaviour, State-driven, Optional).
- **Dependencies**: List of task IDs that must complete first.
- **Files to touch**: Exact file paths that will be created or modified.
- **Verification method**: the Planner gives each task one method, a **test**, an **inspection**, or a **demonstration**, as defined and recorded by the `new-task` skill's Verification Methods. The task takes the method its source acceptance criteria name; when the criteria name different methods, split the work into one task per method. For a change-request or S-000, apply `new-task`'s rule for choosing the method. A test task lists its test files in Files to Touch. Never plan a test that asserts the wording of a skill, guide, or process document, or one that only proves something was removed: those changes are verified by inspection. When the project documents a full-suite command, every task's `## Verification` includes it as a regression check, in addition to any module-scoped command.
- **Regeneration**: a task regenerates the generated files (scaffolds, docs) its own change affects and lists them in Files to Touch. A plan never ends with a separate "regenerate everything" task.
- **Command reference**: a task that changes a command's arguments, options or help text lists the project's generated command reference, named in its guidance, in Files to Touch. The command that regenerates it is the project's own, named in its guidance.

During task writing, consider documentation updates as implementation work derived from the approved spec, not as a prerequisite before creating tasks.
If the spec changes user-facing behavior, commands, templates, guides, or workflow expectations, add the required documentation updates as tasks or acceptance criteria in this breakdown.
Also consider test updates and verification changes as implementation work derived from the approved spec.
If documentation or test updates are not needed, omit them without placeholder tasks.

### Step 4: Validate the Plan
Verify completeness: does the full set of tasks cover the entire specification? For S-000, the bootstrap scope only (Step 0).
Map every feature-spec REQ and AC to at least one task and its verification; use section-based coverage for change-requests and S-000.
Verify isolation: do any two tasks modify the same file? If yes, add a dependency between them.
Verify atomicity: can each task be completed in a single agent pass? If a task feels too large, split it.
Verify regeneration: does each task list the generated files its own change affects? If the plan ends with a separate "regenerate everything" task, move each regeneration into the task whose change requires it.

### Step 5: Place Tasks
The tasks are already in the tracker with status `planned`, listed by `ai-team list tasks --state planned --spec <spec-or-cr-id>`.
They are outside version control: there is nothing to commit, and `/dev-loop` ignores them until Step 7 activates them.

### Step 6: Architect Preflight
Run `ai-team list tasks --state planned --spec <spec-or-cr-id> --json`, then `ai-team show <task-id> --json` for each listed task, and collect each task's absolute `path`.
The tracker is outside the repository, so the Planner passes the Architect the absolute task paths that `ai-team` reported in the prompt.

**Spawn the Architect subagent** (tier: most capable) with this prompt:

> "Review the planned task plan for the spec or change-request `<spec-or-cr-id>`.
> The planned task files are: <task-id>: <absolute path>, one per task.
> Use the spec-breakdown-review skill.
> Validate dependency correctness, file conflict risk, architectural consistency with the architecture documents and `{{project_dir}}/decisions/`, atomicity, and implementation readiness.
> If all is sound, return `Result: PASS` and state that the plan is ready for /dev-loop.
> If issues are found, return `Result: FAIL` with exact Planner corrections, or `Result: ESCALATE` only when a problem requires changing the approved specification.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the Architect to complete.
If the Architect requests Planner revisions, address them in the task files and re-trigger the preflight.
If the Architect escalates because the approved specification must change, stop and return the escalation to the product owner using the Phase 2 product owner report template defined in the `escalation-review` skill.

### Step 7: Merge the Planning Branch and Activate the Tasks
Only after the Architect returns `PASS`:
1. Run the before-point Workspace Hygiene check, then `git checkout {{integration_branch}}`.
2. If the planning branch has commits (`git rev-list --count {{integration_branch}}..plan/<id>-<slug>` is not 0), run `git merge --no-ff plan/<id>-<slug> -m "chore(plan): merge <id> <short-description>"`.
   If the merge conflicts, abort it with `git merge --abort` and stop: report the conflicting planning files to the product owner. Do not resolve planning conflicts automatically.
   A planning branch with no commits — a change-request that amends no spec and raises no ADR — is not merged.
3. Run the after-point Workspace Hygiene check.
4. Delete the planning branch with `git branch -d plan/<id>-<slug>`. If `-d` refuses, stop and report — never force deletion.
5. Activate the plan: for every task in `ai-team list tasks --state planned --spec <id>`, run `ai-team task set-status <task-id> pending`.

Until this step, the tasks stay `planned` and invisible to `/dev-loop`, and `{{integration_branch}}` carries none of the spec or change-request changes.

## Output Format

- A set of validated tasks in the tracker with status `pending`, approved by the Architect preflight and activated after the planning branch merged the spec or change-request changes they implement.
- The plan is ready for the product owner to invoke `/dev-loop` — no further product owner review of the task plan is required.

## Quality Criteria

- Every task is **atomic** — one clear outcome.
- Every task is **one-shottable** — completable in a single agent session without running out of context. Rules of thumb: touches at most 3–4 files, has at most 5 acceptance criteria, and the description fits in ~20 lines. If a task exceeds any of these, split it.
- Every task is **verifiable** — its Verification section proves it by a test, an inspection, or a demonstration.
- Every task is **self-contained** — the description provides enough context to start.
- Every AC uses one of the five EARS patterns.
- No two tasks modify the same file without an explicit dependency between them.
- The full set of tasks covers 100% of the specification (for S-000, its bootstrap scope; see Step 0).

## Common Pitfalls

- **Tasks too large** — if a task description is longer than ~20 lines, it probably needs splitting.
- **Missing dependencies** — trace the data flow: if Task B reads a file that Task A creates, Task B depends on Task A.
- **Criteria that do not match an EARS pattern** — if a criterion resists EARS, the task is probably not atomic.
- **Forgetting verification** — every task must have a way to prove it is done: a test, an inspection, or a demonstration. If you can name none, the acceptance criteria are not specific enough.
- **Tests for prose or removals** — a test that pins the wording of a skill or guide, or that proves a command is gone, adds upkeep without checking product behavior. Plan an inspection instead.
- **File conflicts** — two tasks creating the same file will cause merge conflicts. Restructure so one task creates the file and the other modifies it (with a dependency).
- **Choosing the technology in a task** — a task that names a framework, library, or design the architecture documents and ADRs do not decide. Send the gap to the Architect instead.
- **Planning solution work from S-000** — S-000 yields only the project bootstrap tasks. Refuse a request for solution work and name a feature spec as the input instead.
