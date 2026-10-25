---
title: Local Work-Item Tracker
version: '0.3'
status: approved  # draft | review | approved | superseded
created: '2026-10-15'
author: planner
id: S-006
---

# Local Work-Item Tracker

<!--
This spec describes requirements and measurable criteria in prose.
It is not the implementation. Do not paste full configuration files,
build manifests, or implementation code into the sections below.
-->

## Purpose

Task and bug lifecycle state lives inside the project repository today: each state is a folder, every state change is a file move, and every move, Work Log, and Review Verdict is a commit on `dev-agent`.
Processing one task therefore costs about four lifecycle commits and six to eight branch switches on top of the actual work, and task-regression bugs need their content relayed by hand because their branch does not contain the bug file.
This spec moves tasks, bugs, and change-requests out of version control into a local tracker folder configured in `.ai-team.toml`, and makes the frontmatter `status` field the only source of lifecycle state.
Specs and ADRs stay in the project repository: they are design documents that are versioned and reviewed with the code.
When it is done, recording any lifecycle change — claim, Work Log, verdict, completion — produces no commit and no branch switch, and the only commits a task produces are its implementation commits and its merge commit.

This is phase 1 of moving task tracking out of the repository. Phase 2 (an external GitHub backend) is excluded below and depends on the CLI and skill seams this spec creates.

## Exclusions

- **GitHub or any other remote tracker backend.** Deferred to phase 2. This spec only ensures that skills reach tracker data through `ai-team` commands, so that a later backend does not change the skills a second time.
- **Moving specs, ADRs, or docs.** They are design documents that belong next to the code and stay in the project directory under version control. Spec amendments and ADRs raised by a change-request are still committed on its planning branch.
- **Sharing the tracker across machines or collaborators.** The tracker is local to one working copy. Making the tracker folder its own repository, or syncing it, is left to the human.
- **History of task, bug, and change-request files.** Git history no longer records them or their lifecycle changes. The Work Log and Review Verdict entries inside each file remain the record.
- **Changing the Work Log, Diagnosis Log, or Review Verdict formats.** Only where they are written changes, not what they contain.
- **Shared ID allocation for specs and ADRs.** Task, bug, and change-request IDs come from the single tracker folder and stop colliding across planning branches; spec and ADR IDs keep today's allocation from the files on the current branch.

## Architecture

### Design Principles

- **Work items out, design documents in.** Tasks, bugs, and change-requests are work items and live in the tracker. Specs and ADRs are design documents and live in the repository.
- **One source of truth for state.** A work item's lifecycle state is its frontmatter `status` value. No folder, filename, or branch encodes state.
- **Outside version control, inside the workspace.** The tracker is never committed, survives branch switches untouched, and lives where a dev container mounts the workspace by default.
- **One tracker per repository.** Every git worktree of a repository resolves the same tracker folder, so a Developer working in a worktree and a loop working in the main checkout see the same state.
- **Skills never touch tracker paths directly.** Skills locate, create, and transition tasks, bugs, and change-requests only through `ai-team` commands, and every state change is a command. A role may read and edit the body of a work-item file whose path an `ai-team` command reported — appending a Work Log or Review Verdict, the Planner filling task bodies, the Architect applying Gate 2 corrections — and a caller may pass such a reported path to another role. Every agent role that runs these skills has a shell: each agent lists `Bash` in its `tools:`. The one exception is scratch files that are not work items: a loop may write review packages under `<tracker>/review-packages/`, locating the folder with `ai-team tracker path`.
- **Existing projects migrate explicitly.** No command moves files out of a repository. An agent migrates by hand, following a documented procedure, and commands warn while unmigrated files remain.

### System Diagram

```
 .ai-team.toml ──[tracker] dir──┐
                                ▼
 ai-team CLI ──────────► <tracker>/tasks/T-NNN-*.md            status: planned … completed
 (new, set-status,       <tracker>/bugs/B-NNN-*.md             status: open … resolved
  list, show, status,    <tracker>/change-requests/CR-NNN-*.md status: pending … rejected
  report, validate,      <tracker>/archive/YYYY-MM/
  archive, tracker path) <tracker>/review-packages/   loop scratch files
                                  ▲
                                  │ append Work Log / Verdict to returned path
                                  │
 skills (loops, integrate, ───────┘        project repo (git)
 code-review, spec-breakdown,  ───────►   specs, ADRs, source, tests
 change-request)
```

### Responsibility Separation

| Component | Responsibility | Interface notes |
|---|---|---|
| Tracker configuration | Resolve the tracker folder for the current repository | Reads `.ai-team.toml`; exposes the resolved absolute path to every command |
| Work-item store | Create, find, transition, archive tasks, bugs, and change-requests by ID | Field-based state; one flat folder per kind |
| CLI commands | Human and skill entry points for tracker data | Existing command names keep working; state filters read the `status` field |
| Migration | Guide an agent through moving legacy tasks, bugs, and change-requests into the tracker | A documented manual procedure plus a legacy-folder warning from the CLI |
| Process skills and docs | Drive lifecycle through CLI commands, without lifecycle commits | Loops, integrate, code-review, spec-breakdown, change-request, git-conventions, workflow docs |

## Components

### Component 1: Tracker Configuration
- **Purpose:** resolve one tracker folder per repository from `.ai-team.toml`, shared by all worktrees.
- **Estimated size:** small.
- **Interfaces:** consumed by every CLI command; exposed through a command that prints the resolved path.

### Component 2: Field-Based Work-Item Store
- **Purpose:** store tasks, bugs, and change-requests in flat per-kind folders with state in the `status` field.
- **Estimated size:** medium.
- **Interfaces:** ID allocation, lookup by ID, status transition, archive.

### Component 3: CLI Command Updates
- **Purpose:** make `task`, `bug`, `change-request`, `list`, `show`, `status`, `report`, `validate`, `archive`, `init`, and `check-layout` use the tracker and the `status` field.
- **Estimated size:** medium.
- **Interfaces:** existing command names and JSON output shapes; new generic status-transition and path commands; new `planned` and `cancelled` task states.

### Component 4: Migration Procedure
- **Purpose:** let an agent move legacy `tasks/<state>/`, `bugs/<state>/`, and `change-requests/` files into the tracker by hand.
- **Estimated size:** small.
- **Interfaces:** a documented procedure in the setup guide; a warning from tracker commands, naming the legacy folders and the procedure, while legacy files remain.

### Component 5: Process Skills and Documentation
- **Purpose:** remove lifecycle commits, the "canonical on `dev-agent`" rule, and content relaying from the process.
- **Estimated size:** medium.
- **Interfaces:** `dev-loop`, `bug-loop`, `integrate`, `code-review`, `tdd`, `debug`, `new-task`, `new-bug`, `change-request`, `architecture-consistency-review`, `spec-breakdown`, `status-report`, `git-conventions`, the agent role files, and `ai-process/` docs.

## Workflow

1. `ai-team init` writes a `[tracker]` section with the default folder, creates the folder, and makes git ignore it. ★ For an existing project, an agent follows the documented migration procedure once and commits the removal of the legacy folders.
2. `/change-request` creates the change-request in the tracker with status `pending` and opens a planning branch for any spec amendments or ADRs it drives; human approval sets it to `approved`, rejection to `rejected`. `/new-spec` opens its planning branch as before.
3. `spec-breakdown` creates tasks with status `planned` on the planning branch's behalf; the tracker is shared, so the tasks exist immediately but stay invisible to `/dev-loop`.
4. After Gate 2 and the planning-branch merge, `spec-breakdown` sets that plan's tasks to `pending`. A planning branch with no commits — a change-request that amends no spec and raises no ADR — is deleted instead of merged. If a spec or change-request is abandoned, its planned tasks become `cancelled`.
5. `/dev-loop` lists `pending` tasks, sets the chosen one to `in-progress`, and creates the task branch. No commit.
6. The loop appends the Developer's Work Log and the Reviewer appends the Review Verdict to the task file, from whatever branch is checked out. No commit, no switch.
7. `integrate` reads the verdict from the task file, merges, and on success sets the task to `completed`. The merge commit is the only commit on `dev-agent`.
8. The bug loop follows the same pattern. Task-regression bug branches no longer need bug content relayed, because the bug file is outside every branch.
9. ★ The human runs `/status-report` on demand; it reads state from the tracker.

## Configuration Requirements

**Tracker folder**
- **What must exist:** a `dir` setting in a `[tracker]` section of `.ai-team.toml`.
- **Where it lives:** the repository's `.ai-team.toml`, beside the existing `[project]` section.
- **Constraints:** a relative path resolves against the folder that holds `.ai-team.toml`, taken in the main working tree of the repository rather than the current worktree; in a bare repository with worktrees, the bare repository folder itself stands in for the main working tree. An absolute path or a `~` path is used as given. Default value: `.ai-team/tracker`.
- **Missing-value behaviour:** when the section or key is absent, commands use the default folder. When the folder does not exist, creating a work item creates it; reading commands treat it as empty.

**Git ignore**
- **What must exist:** an ignore rule covering the tracker folder whenever it lies inside the repository.
- **Where it lives:** the repository's root `.gitignore`.
- **Constraints:** `ai-team init` adds the rule idempotently and never removes existing rules; the migration procedure tells the agent to add it.
- **Missing-value behaviour:** `check-layout` reports a finding when the tracker folder is inside the repository and not ignored.

## Measurable Success Criteria

- After `ai-team init` in an empty git repository, the project directory contains no `tasks/`, `bugs/`, or `change-requests/` folders and still contains `specs/` and `decisions/`, the tracker folder exists, and `git check-ignore` succeeds for it.
- Creating a task, bug, or change-request, moving it through every status, and appending text to it leaves `git status --porcelain` empty.
- `ai-team list tasks --state <s>` returns exactly the tasks whose `status` field is `<s>`, and its JSON shape is unchanged.
- Run from two worktrees of the same repository, `ai-team tracker path` prints the same absolute path.
- `ai-team validate` reports a finding for any task, bug, or change-request whose `status` is not one of the allowed values, and no longer reports folder/status mismatches.
- While a legacy `tasks/`, `bugs/`, `change-requests/`, or `archive/` folder in the project directory still holds a markdown file, every tracker command prints a warning to stderr naming the folder and the migration procedure; once the folders are empty or gone, no warning is printed.
- Following the migration procedure on this repository moves every task, bug, and change-request out of `docs/ai-team/` into the tracker with contents unchanged except `status` corrected from the folder where the two disagreed, and `ai-team validate` reports no findings afterwards.
- In the generated skills, no step commits a task, bug, or change-request file, and no step switches branches to record lifecycle state.
- The full CLI test suite passes, including tests updated from folder-based to field-based state.

## Implementation Order

1. **Tracker core** — configuration, worktree-aware path resolution, field-based store, ID allocation. Observable: the store unit tests pass.
2. **CLI commands** — all commands on the tracker, new status-transition and path commands, `init` and `check-layout` changes. Depends on phase 1. Observable: the success criteria for init, list, validate, and worktrees pass.
3. **Migration** — the documented procedure and the legacy warning, then this repository's own migration. Depends on phase 2. Observable: the two migration criteria pass.
4. **Process skills and docs** — skills, agents, git conventions, workflow docs, regenerated scaffolds. Depends on phase 2. Observable: the generated-skill criterion passes.

## Amendment Log

- **2026-10-16 (PR #32 review):** relative tracker paths resolve against the `.ai-team.toml` folder within the main working tree, not the git top level, so projects in a repository subfolder keep their tracker beside their configuration; the worktrees of a bare repository share one tracker kept inside that bare repository; the legacy `archive/` folder triggers the migration warning; a task's `spec` may name a change-request ID.
- **2026-10-20 (CR-003):** the "Skills never touch tracker paths directly" principle now states that every role running the tracker skills has a shell (Claude `tools:` includes `Bash`; Codex roles take their sandbox from the parent session, which must allow writes for roles that create files or commit: Architect, Planner, Developer, Reviewer, Integrator — the CR-003 §8 role list completed under its own rule, since the Reviewer appends Review Verdicts and files bugs), that a role may read and edit the body of a work-item file whose path an `ai-team` command reported while state changes stay command-only, and that a caller may pass such a path to another role. Driven by CR-003 §1 and §8 (report #3, #21) and Architecture Consistency Review finding F1: the Claude Architect had no shell at Gate 2 and read tracker files directly; the Reviewer was added to the writable-role list by Review 2 finding R2-1.
- **2026-10-22 (consistency review):** the "Skills never touch tracker paths directly" principle now allows loop scratch files that are not work items: review packages under `<tracker>/review-packages/` (written by `dev-loop` and `bug-loop`), located with `ai-team tracker path`; the System Diagram shows the folder. Version bumped to 0.2 under the spec authoring guide's amendment rule. Driven by the loops already writing `<tracker-path>/review-packages/<id>.md`, which the principle forbade.
- **2026-10-25 (CR-007):** the "Skills never touch tracker paths directly" principle drops the Codex sandbox sentence; every agent lists `Bash` in its `tools:`. Version bumped to 0.3. Driven by CR-007 and ADR-003: Claude is the only export target.
