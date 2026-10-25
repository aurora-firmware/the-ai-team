---
title: Local Work-Item Tracker
version: '0.3'
status: approved  # draft | review | approved | superseded
created: '2026-10-15'
author: planner
id: S-006
---

# Local Work-Item Tracker

## Purpose

This spec covers the work-item tracking of the S-000 **CLI** component and the
lifecycle-recording steps of the **Team definition** skills that use it. Task and bug
lifecycle state lived inside the project repository: each state was a folder, every
state change a file move, and every move, Work Log and Review Verdict a commit on
`dev-agent`, so one task cost about four lifecycle commits and six to eight branch
switches on top of the work, and task-regression bugs needed their content relayed by
hand. Tasks, bugs and change-requests now live in a local tracker folder outside
version control, configured in `.ai-team.toml`, with the frontmatter `status` field as
the only lifecycle state, while specs and ADRs stay in the repository. Recording any
lifecycle change produces no commit and no branch switch, so the only commits a task
produces are its implementation commits and its merge commit.

This is phase 1 of moving task tracking out of the repository. Phase 2 (an external
GitHub backend) is excluded below and depends on the CLI and skill seams this spec
creates.

## Users and Journeys

| Actor | Goal | Priority | Outcome | Requirements |
|---|---|---|---|---|
| Development and bug loops (agents) | Claim, log, review and complete work items without lifecycle commits or branch switches | P1 | Every state change is an `ai-team` command; Work Logs and verdicts are appended to the tracker file from any branch | REQ-003, REQ-004, REQ-007, REQ-008, REQ-013 |
| Planner | Create a task plan that the development loop cannot pick up before Gate 2 | P1 | Planned tasks stay out of the `pending` queue until set to `pending` | REQ-005, REQ-014 |
| Developer or Reviewer in a separate worktree | See the same work items as the loop in the main checkout | P1 | Every worktree resolves the same tracker folder | REQ-001, REQ-002 |
| Human setting up a project | Get a working tracker with no manual configuration | P1 | `ai-team init` configures, creates and git-ignores the tracker | REQ-009 |
| Human or agent with an existing project | Move legacy work items into the tracker | P2 | Commands warn until migration is done, and a documented procedure guides it | REQ-011, REQ-012 |
| Human checking progress | See the state of the work | P2 | `list`, `show`, `status`, `report` and `validate` read state from the tracker | REQ-007, REQ-010 |

## Exclusions

- **GitHub or any other remote tracker backend.** Deferred to phase 2. This spec only ensures that skills reach tracker data through `ai-team` commands, so that a later backend does not change the skills a second time.
- **Moving specs, ADRs, or docs.** They are design documents that belong next to the code and stay in the project directory under version control. Spec amendments and ADRs raised by a change-request are still committed on its planning branch.
- **Sharing the tracker across machines or collaborators.** The tracker is local to one working copy. Making the tracker folder its own repository, or syncing it, is left to the human.
- **History of task, bug, and change-request files.** Git history no longer records them or their lifecycle changes. The Work Log and Review Verdict entries inside each file remain the record.
- **Changing the Work Log, Diagnosis Log, or Review Verdict formats.** Only where they are written changes, not what they contain.
- **Shared ID allocation for specs and ADRs.** Task, bug, and change-request IDs come from the single tracker folder and stop colliding across planning branches; spec and ADR IDs keep today's allocation from the files on the current branch.
- **A migration command.** No command moves files out of a repository; migration is a documented manual procedure (REQ-012).

## Architecture

### Design Principles

- **Work items out, design documents in.** Tasks, bugs, and change-requests are work items and live in the tracker. Specs and ADRs are design documents and live in the repository (REQ-003).
- **One source of truth for state.** A work item's lifecycle state is its frontmatter `status` value. No folder, filename, or branch encodes state (REQ-003, REQ-010).
- **Outside version control, inside the workspace.** The tracker is never committed, survives branch switches untouched, and lives where a dev container mounts the workspace by default (REQ-001, REQ-008, REQ-009).
- **One tracker per repository.** Every git worktree of a repository resolves the same tracker folder, so a Developer working in a worktree and a loop working in the main checkout see the same state (REQ-002).
- **Skills never touch tracker paths directly.** Skills locate, create, and transition tasks, bugs, and change-requests only through `ai-team` commands, and every state change is a command. A role may read and edit the body of a work-item file whose path an `ai-team` command reported, and a caller may pass such a reported path to another role. Every agent role that runs these skills has a shell. The one exception is scratch files that are not work items (REQ-013).
- **Existing projects migrate explicitly.** No command moves files out of a repository. An agent migrates by hand, following a documented procedure, and commands warn while unmigrated files remain (REQ-011, REQ-012).

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

### Alternatives Considered

- **Keeping lifecycle folders in the repository.** Rejected: every state change is a
  file move and a commit on `dev-agent`, which costs about four lifecycle commits and
  six to eight branch switches per task (Purpose).
- **Resolving a relative tracker path against the git top level.** Rejected in the
  PR #32 review: a project in a repository subfolder would lose its tracker from beside
  its configuration. Relative paths resolve against the `.ai-team.toml` folder in the
  main working tree instead.
- **A migration command.** Rejected: no command moves files out of a repository, so
  migration stays a documented manual procedure with a warning (REQ-011, REQ-012).

## Interfaces

**Exposed — tracker folder layout (REQ-003).** **Contract:**

| Path under the tracker | Holds | Allowed `status` values |
|---|---|---|
| `tasks/T-NNN-<slug>.md` | Tasks | `planned`, `pending`, `in-progress`, `blocked`, `completed`, `cancelled` |
| `bugs/B-NNN-<slug>.md` | Bugs | `open`, `in-progress`, `resolved` |
| `change-requests/CR-NNN-<slug>.md` | Change-requests | `pending`, `approved`, `rejected` |
| `archive/YYYY-MM/` | Archived completed tasks and resolved bugs | — |
| `review-packages/<id>.md` | Loop scratch files, not work items | — |

**Exposed — commands (REQ-002, REQ-004, REQ-007).**
- `ai-team tracker path` prints the resolved absolute tracker folder.
- `ai-team task set-status`, `ai-team bug set-status` and
  `ai-team change-request set-status <id> <status>` set any allowed status;
  `--reason` records why. The existing transitions (`task start`, `block`, `unblock`,
  `complete`; `bug start`, `resolve`) keep their names.
- `ai-team list tasks|bugs|change-requests --state <s>` filters on the `status` field
  and keeps its JSON row shape: `id`, `title`, `state`, `priority`, `assigned-role`
  for tasks.
- `ai-team show <id>` finds a work item in the tracker and its archive.
- A command that cannot find an ID reports the tracker folder it searched and exits
  non-zero.

**Exposed — legacy warning (REQ-011).** Written to stderr by tracker commands:
`Warning: legacy work-item folders still hold files: <folders>. …`, naming the folders
and the migration procedure.

**Consumed.**
- `.ai-team.toml`: `[tracker] dir` and `[project] dir`.
- git, to find the main working tree or bare repository of a worktree.

## Workflow

1. `ai-team init` writes a `[tracker]` section with the default folder, creates the folder, and makes git ignore it (REQ-009). ★ For an existing project, an agent follows the documented migration procedure once and commits the removal of the legacy folders (REQ-012).
2. `/change-request` creates the change-request in the tracker with status `pending` and opens a planning branch for any spec amendments or ADRs it drives; human approval sets it to `approved`, rejection to `rejected` (REQ-004). `/new-spec` opens its planning branch as before.
3. `spec-breakdown` creates tasks with status `planned` on the planning branch's behalf; the tracker is shared, so the tasks exist immediately but stay invisible to `/dev-loop` (REQ-005).
4. After Gate 2 and the planning-branch merge, `spec-breakdown` sets that plan's tasks to `pending`. A planning branch with no commits — a change-request that amends no spec and raises no ADR — is deleted instead of merged. If a spec or change-request is abandoned, its planned tasks become `cancelled` (REQ-004, REQ-005).
5. `/dev-loop` lists `pending` tasks, sets the chosen one to `in-progress`, and creates the task branch. No commit (REQ-008, REQ-013).
6. The loop appends the Developer's Work Log and the Reviewer appends the Review Verdict to the task file, from whatever branch is checked out. No commit, no switch (REQ-013).
7. `integrate` reads the verdict from the task file, merges, and on success sets the task to `completed`. The merge commit is the only commit on `dev-agent` (REQ-013).
8. The bug loop follows the same pattern. Task-regression bug branches no longer need bug content relayed, because the bug file is outside every branch.
9. ★ The human runs `/status-report` on demand; it reads state from the tracker (REQ-007).

Failure and boundary paths: an unknown status or an unexpected source status is
rejected without changing the file; a command run again on an item already in the
destination status succeeds without change (REQ-004). An unknown ID names the
searched tracker folder (REQ-007). A missing tracker folder reads as empty and is
created on the first write (REQ-001). Legacy files in the project directory are
ignored by commands and trigger the warning (REQ-011).

## Behavioral Requirements

### REQ-001 — Tracker location

The CLI SHALL locate the tracker from the `dir` setting of the `[tracker]` section of
`.ai-team.toml`, defaulting to `.ai-team/tracker` when the section or key is absent. A
relative path SHALL resolve against the folder holding `.ai-team.toml`, taken in the
main working tree of the repository (or in the bare repository folder, for the
worktrees of a bare repository); an absolute or `~` path SHALL be used as given.
Reading commands SHALL treat a missing tracker folder as empty, and creating a work
item SHALL create it.

#### AC-001.1 — Default and configured paths

- **Given:** a marker with no `[tracker]` section, or with a relative, absolute or `~`
  `dir`
- **When:** the tracker path is resolved
- **Then:** it is `.ai-team/tracker` beside the marker, the relative path beside the
  marker, or the absolute or home path as given

**Verification:** Tests: `test_tracker_path_defaults_to_repository_root` and
`test_tracker_dir_honours_relative_absolute_and_home_paths` in
`cli/tests/test_tracker.py`.

#### AC-001.2 — Project in a subfolder

- **Given:** a project whose `.ai-team.toml` lives in a repository subfolder
- **When:** the tracker path is resolved
- **Then:** the tracker lies beside that marker, not at the repository top level

**Verification:** Test:
`test_project_in_a_repository_subfolder_keeps_its_tracker_beside_it` in
`cli/tests/test_tracker.py`.

### REQ-002 — One tracker per repository

Every worktree of a repository SHALL resolve the same tracker folder, and
`ai-team tracker path` SHALL print that folder as an absolute path.

#### AC-002.1 — Worktrees agree

- **Given:** a repository with a second worktree
- **When:** `ai-team tracker path` runs in each
- **Then:** both print the same absolute path

**Verification:** Test: `test_every_worktree_resolves_the_same_tracker` in
`cli/tests/test_tracker.py`.

#### AC-002.2 — Bare repositories

- **Given:** worktrees of one bare repository, and a second, sibling bare repository
- **When:** each resolves its tracker
- **Then:** the worktrees of one bare repository share a tracker inside it, and the
  sibling keeps its own

**Verification:** Tests: `test_bare_repository_worktrees_share_one_tracker` and
`test_sibling_bare_repositories_keep_separate_trackers` in `cli/tests/test_tracker.py`.

### REQ-003 — Field-based store

Tasks, bugs and change-requests SHALL be stored in the flat per-kind tracker folders
from Interfaces, with lifecycle state held only in the frontmatter `status` field; a
state change SHALL rewrite `status` in place and SHALL NOT move the file. Specs and
ADRs SHALL stay in the project directory.

#### AC-003.1 — Transition in place

- **Given:** a pending task
- **When:** `ai-team task start` runs on it
- **Then:** its `status` becomes `in-progress` and the file keeps its path

**Verification:** Tests: `test_transition_updates_status_in_place` in
`cli/tests/test_task_lifecycle.py` and `test_bug_transition_updates_status_in_place` in
`cli/tests/test_bug_lifecycle.py`.

### REQ-004 — Status transitions

The CLI SHALL let any allowed status from Interfaces be set through the kind's
`set-status` command, recording a given `--reason`, and SHALL reject a status outside
the allowed values. A named transition command SHALL reject an unexpected source status
and SHALL succeed without change when the item is already in the destination status.

#### AC-004.1 — Allowed and unknown statuses

- **Given:** a task
- **When:** `task set-status` runs with each allowed status, and then with `done`
- **Then:** each allowed status is written; `done` is rejected and the file is
  unchanged

**Verification:** Tests: `test_set_status_accepts_every_allowed_status` and
`test_set_status_rejects_unknown_status` in `cli/tests/test_task_lifecycle.py`.

#### AC-004.2 — Reason recorded

- **Given:** a task or bug
- **When:** `set-status` runs with `--reason "migrated from done"`
- **Then:** the reason is recorded in the file

**Verification:** Tests: `test_set_status_records_reason_in_work_log` in
`cli/tests/test_task_lifecycle.py` and `test_bug_set_status_records_reason` in
`cli/tests/test_bug_lifecycle.py`.

#### AC-004.3 — Idempotent and guarded transitions

- **Given:** a task already `in-progress`, and a `completed` task
- **When:** `task start` runs on each
- **Then:** the first succeeds without change; the second is rejected

**Verification:** Tests:
`test_lifecycle_command_is_idempotent_when_already_in_destination_status` and
`test_lifecycle_command_rejects_unexpected_source_status` in
`cli/tests/test_task_lifecycle.py`, and their bug equivalents in
`cli/tests/test_bug_lifecycle.py`.

#### AC-004.4 — Change-request decisions

- **Given:** a pending change-request
- **When:** `change-request set-status <id> rejected` runs
- **Then:** its `status` is `rejected`, and `show` and `list --state rejected` report it

**Verification:** Test: `test_change_request_set_status_and_show` in
`cli/tests/test_tracker.py`.

### REQ-005 — Planned tasks

Tasks created with status `planned` SHALL NOT appear in the `pending` queue until set
to `pending`.

#### AC-005.1 — Activation

- **Given:** two planned tasks and one pending task
- **When:** `list tasks --state pending` runs, then one planned task is set to
  `pending`, then the list runs again
- **Then:** the first list holds only the pending task; the second also holds the
  activated one

**Verification:** Test: `test_planned_tasks_stay_out_of_the_pending_queue_until_activated`
in `cli/tests/test_tracker.py`.

### REQ-006 — ID allocation

The next task, bug or change-request ID SHALL be one above the highest number of its
kind found in the tracker and its archive.

#### AC-006.1 — Archive counts

- **Given:** `T-007` in the tracker and `T-012` in its archive
- **When:** the next task ID is allocated
- **Then:** it is `T-013`

**Verification:** Tests: `test_next_task_id_uses_highest_number_across_tracker_and_archive`
and `test_next_bug_id_scans_tracker_and_archive_and_ignores_non_matching` in
`cli/tests/test_ids.py`.

### REQ-007 — Commands read the tracker

`task`, `bug`, `change-request`, `list`, `show`, `status`, `report`, `validate` and
`archive` SHALL read and write work items in the tracker. State filters SHALL match the
`status` field, `list` JSON row shapes SHALL stay unchanged, and a command that cannot
find an ID SHALL name the tracker folder it searched. `archive` SHALL move old
completed tasks and resolved bugs into the tracker's `archive/YYYY-MM/`.

#### AC-007.1 — State filter

- **Given:** tasks in several statuses
- **When:** `list tasks --state <s> --json` runs
- **Then:** it returns exactly the tasks whose `status` is `<s>`, each row with `id`,
  `title`, `state`, `priority` and `assigned-role`

**Verification:** Tests: `test_planned_tasks_stay_out_of_the_pending_queue_until_activated`
in `cli/tests/test_tracker.py` and
`test_list_tasks_state_filter_only_includes_matching_folder` in `cli/tests/test_list.py`.

#### AC-007.2 — Not found

- **Given:** no task `T-999`
- **When:** `task start T-999` runs
- **Then:** it fails and names the tracker folder searched

**Verification:** Tests: `test_lifecycle_command_reports_not_found_and_names_tracker_folder`
in `cli/tests/test_task_lifecycle.py` and
`test_bug_lifecycle_command_reports_not_found_and_names_tracker_folder` in
`cli/tests/test_bug_lifecycle.py`.

#### AC-007.3 — Archive

- **Given:** a completed task and a resolved bug older than the cutoff
- **When:** `ai-team archive` runs
- **Then:** both move into the tracker's `archive/YYYY-MM/` for their creation month

**Verification:** Test:
`test_archive_moves_old_completed_tasks_and_resolved_bugs_to_created_month` in
`cli/tests/test_archive.py`.

### REQ-008 — No lifecycle commits

Creating a task, bug or change-request, moving it through every status and appending
text to it SHALL leave the repository's working tree unchanged.

#### AC-008.1 — Clean working tree

- **Given:** an initialised git repository with a clean working tree
- **When:** a task, a bug and a change-request are created, moved through their
  statuses, and a Review Verdict is appended to the task file
- **Then:** `git status --porcelain` prints nothing

**Verification:** Test: `test_full_lifecycle_leaves_the_working_tree_clean` in
`cli/tests/test_tracker.py`.

### REQ-009 — Init sets up the tracker

`ai-team init` SHALL write `[tracker] dir` with the default folder, create the folder,
and, when it lies inside the repository, add an ignore rule for it to the root
`.gitignore` once, keeping existing rules. The project directory SHALL have no
`tasks/`, `bugs/` or `change-requests/` folders and SHALL keep `specs/` and
`decisions/`.

#### AC-009.1 — Idempotent setup

- **Given:** a repository whose `.gitignore` already holds a rule
- **When:** `init` runs twice
- **Then:** the marker records `.ai-team/tracker`, the folder exists, the existing rule
  stays first, and the tracker rule appears once

**Verification:** Test: `test_init_configures_tracker_and_ignores_it_idempotently` in
`cli/tests/test_init.py`.

#### AC-009.2 — No work-item folders in the project

- **Given:** an empty git repository
- **When:** `init` runs
- **Then:** the project directory holds `specs/` and `decisions/` and no `tasks/`,
  `bugs/` or `change-requests/`, and `git check-ignore` succeeds for the tracker

**Verification:** Test:
`test_init_defaults_to_cwd_and_scaffolds_project_claude_and_marker` in
`cli/tests/test_init.py` (specs present, no `tasks/`, tracker created); demonstration
with `git check-ignore` after `init`.

### REQ-010 — Validation of status

`ai-team validate` SHALL report any task, bug or change-request whose `status` is not
an allowed value for its kind, and SHALL NOT compare folders with `status`.

#### AC-010.1 — Invalid status

- **Given:** a task with `status: done`
- **When:** `validate` runs
- **Then:** it reports a `status-invalid` error for that file and exits non-zero

**Verification:** Test: `test_validate_emits_error_when_status_is_not_an_allowed_value`
in `cli/tests/test_validate.py`.

### REQ-011 — Legacy warning

WHILE a legacy `tasks/`, `bugs/`, `change-requests/` or `archive/` folder in the
project directory holds a markdown file, every tracker command SHALL write to stderr a
warning naming the folders and the migration procedure, and SHALL ignore those files.
Once the folders are empty or gone, no warning SHALL be written.

#### AC-011.1 — Warning while files remain

- **Given:** a legacy `tasks/pending/T-009-old.md` in the project directory
- **When:** `list tasks --json` runs, then runs again after the file is removed
- **Then:** the first run returns `[]` and warns on stderr naming the folder and
  "Migrating to the local tracker"; the second run does not warn

**Verification:** Tests: `test_commands_warn_while_legacy_folders_hold_files` and
`test_legacy_archive_folder_triggers_the_warning` in `cli/tests/test_tracker.py`.

### REQ-012 — Migration procedure

The setup guide SHALL document a manual procedure that moves legacy tasks, bugs and
change-requests into the tracker with their content unchanged, correcting each task's
or bug's `status` to the state folder it came from where the two disagree, and adding
the ignore rule.

#### AC-012.1 — Procedure present

- **Given:** `guides/setup-guide.md`
- **When:** its "Migrating to the Local Tracker" section is read
- **Then:** it says there is no migration command and gives the steps, including the
  status reconciliation with `set-status --reason` and the commit of the folder
  removal

**Verification:** Inspection of `guides/setup-guide.md`.

### REQ-013 — Skills record lifecycle through commands

The generated skills and agents SHALL change work-item state only through `ai-team`
commands, SHALL NOT commit a task, bug or change-request file, and SHALL NOT switch
branches to record lifecycle state. A role MAY read and edit the body of a work-item
file whose path an `ai-team` command reported, and MAY pass that path to another role.
Every agent that runs these skills SHALL list `Bash` in its `tools:`. The only
non-command writes to the tracker SHALL be loop review packages under
`<tracker>/review-packages/`, located with `ai-team tracker path`. The process rules
themselves are owned by the `git-conventions`, `dev-loop`, `bug-loop` and `integrate`
skills.

#### AC-013.1 — Loops append without commits

- **Given:** the `dev-loop` and `bug-loop` skill sources and their exports
- **When:** their handoff steps are read
- **Then:** they append the Work Log or Diagnosis Log to the tracker file with "no
  switch and no commit", and no `chore(tasks)` or `chore(bugs)` record commit remains

**Verification:** Tests: `test_dev_loop_records_work_log_in_tracker_without_commit_or_switch`,
`test_bug_loop_records_diagnosis_log_in_tracker_without_commit_or_switch` and
`test_bug_loop_records_work_log_in_tracker_without_commit` in
`cli/tests/test_t063_integration_guards.py`.

#### AC-013.2 — Integration completes through the CLI

- **Given:** the `integrate` skill
- **When:** its completion step is read
- **Then:** it sets the task to `completed` with `ai-team` and confirms the status,
  with no lifecycle commit

**Verification:** Tests:
`test_integrate_completes_task_through_the_cli_without_a_lifecycle_commit` and
`test_integrate_confirms_completed_status_before_reporting_success` in
`cli/tests/test_t063_integration_guards.py`.

#### AC-013.3 — Commit rule

- **Given:** the `git-conventions` skill and the Developer agent
- **When:** their hard rules are read
- **Then:** committing a lifecycle file is forbidden

**Verification:** Tests: `test_git_conventions_hard_rules_covers_lifecycle_file_commits`
and `test_claude_developer_never_touch_forbids_git_add_and_commit` in
`cli/tests/test_b016_developer_lifecycle_boundary.py`.

### REQ-014 — Change-request as task source

A task's `spec` field MAY name a change-request ID, and `list --spec` SHALL match every
form of a spec reference.

#### AC-014.1 — Task citing a change-request

- **Given:** a task created with `--spec CR-002`
- **When:** `list tasks --spec CR-002` runs
- **Then:** the task is listed

**Verification:** Tests: `test_tasks_may_cite_a_change_request_as_their_spec` and
`test_list_spec_filter_matches_every_form_of_a_spec_reference` in
`cli/tests/test_tracker.py`.

## Quality Requirements

None. The tracker is a local, single-user folder of Markdown files: no security,
privacy, accessibility or performance target applies, and no guarantee for concurrent
writes was agreed.

## Configuration Requirements

**Tracker folder** (REQ-001)
- **What must exist:** a `dir` setting in a `[tracker]` section of `.ai-team.toml`.
- **Where it lives:** the repository's `.ai-team.toml`, beside the existing `[project]` section.
- **Constraints:** a relative path resolves against the folder that holds `.ai-team.toml`, taken in the main working tree of the repository rather than the current worktree; in a bare repository with worktrees, the bare repository folder itself stands in for the main working tree. An absolute path or a `~` path is used as given. Default value: `.ai-team/tracker`.
- **Missing-value behaviour:** when the section or key is absent, commands use the default folder. When the folder does not exist, creating a work item creates it; reading commands treat it as empty.

**Git ignore** (REQ-009)
- **What must exist:** an ignore rule covering the tracker folder whenever it lies inside the repository.
- **Where it lives:** the repository's root `.gitignore`.
- **Constraints:** `ai-team init` adds the rule idempotently and never removes existing rules; the migration procedure tells the agent to add it.
- **Missing-value behaviour:** `check-layout` reports a finding when the tracker folder is inside the repository and not ignored (S-003).

## Assumptions and Dependencies

- **git is installed** and the project is a git repository; the worktree and
  bare-repository resolution of REQ-001 and REQ-002 asks git for the main working
  tree.
- **The tracker folder is writable** from every worktree and dev container that works
  on the repository. A dev container that mounts only one worktree cannot see a
  tracker outside it.
- **One working copy per tracker.** No locking across machines is provided (see
  Exclusions).
- **S-003 `check-layout`** reports an unignored in-repository tracker and unmigrated
  legacy folders.
- **The skills that record lifecycle** (`dev-loop`, `bug-loop`, `integrate`,
  `code-review`, `spec-breakdown`, `change-request`, `git-conventions`) follow
  REQ-013; a skill that commits a work-item file would break REQ-008.

## Success Criteria

1. After `ai-team init` in an empty git repository, the project directory contains no `tasks/`, `bugs/`, or `change-requests/` folders and still contains `specs/` and `decisions/`, the tracker folder exists, and `git check-ignore` succeeds for it (REQ-009).
2. Creating a task, bug, or change-request, moving it through every status, and appending text to it leaves `git status --porcelain` empty (REQ-008).
3. `ai-team list tasks --state <s>` returns exactly the tasks whose `status` field is `<s>`, and its JSON shape is unchanged (REQ-007).
4. Run from two worktrees of the same repository, `ai-team tracker path` prints the same absolute path (REQ-002).
5. `ai-team validate` reports a finding for any task, bug, or change-request whose `status` is not one of the allowed values, and no longer reports folder/status mismatches (REQ-010).
6. While a legacy `tasks/`, `bugs/`, `change-requests/`, or `archive/` folder in the project directory still holds a markdown file, every tracker command prints a warning to stderr naming the folder and the migration procedure; once the folders are empty or gone, no warning is printed (REQ-011).
7. Following the migration procedure on this repository moves every task, bug, and change-request out of `docs/ai-team/` into the tracker with contents unchanged except `status` corrected from the folder where the two disagreed, and `ai-team validate` reports no findings afterwards (REQ-012).
8. In the generated skills, no step commits a task, bug, or change-request file, and no step switches branches to record lifecycle state (REQ-013).
9. The full CLI test suite passes, including tests updated from folder-based to field-based state (REQ-001–REQ-014).

## Implementation Order

1. **Tracker core** — configuration, worktree-aware path resolution, field-based store, ID allocation. Observable: the store unit tests pass.
2. **CLI commands** — all commands on the tracker, new status-transition and path commands, `init` and `check-layout` changes. Depends on phase 1. Observable: the success criteria for init, list, validate, and worktrees pass.
3. **Migration** — the documented procedure and the legacy warning, then this repository's own migration. Depends on phase 2. Observable: the two migration criteria pass.
4. **Process skills and docs** — skills, agents, git conventions, workflow docs, regenerated scaffolds. Depends on phase 2. Observable: the generated-skill criterion passes.

## Open Questions

None.

## Amendment Log

- **2026-10-16 (PR #32 review):** relative tracker paths resolve against the `.ai-team.toml` folder within the main working tree, not the git top level, so projects in a repository subfolder keep their tracker beside their configuration; the worktrees of a bare repository share one tracker kept inside that bare repository; the legacy `archive/` folder triggers the migration warning; a task's `spec` may name a change-request ID.
- **2026-10-20 (CR-003):** the "Skills never touch tracker paths directly" principle now states that every role running the tracker skills has a shell (Claude `tools:` includes `Bash`; Codex roles take their sandbox from the parent session, which must allow writes for roles that create files or commit: Architect, Planner, Developer, Reviewer, Integrator — the CR-003 §8 role list completed under its own rule, since the Reviewer appends Review Verdicts and files bugs), that a role may read and edit the body of a work-item file whose path an `ai-team` command reported while state changes stay command-only, and that a caller may pass such a path to another role. Driven by CR-003 §1 and §8 (report #3, #21) and Architecture Consistency Review finding F1: the Claude Architect had no shell at Gate 2 and read tracker files directly; the Reviewer was added to the writable-role list by Review 2 finding R2-1.
- **2026-10-22 (consistency review):** the "Skills never touch tracker paths directly" principle now allows loop scratch files that are not work items: review packages under `<tracker>/review-packages/` (written by `dev-loop` and `bug-loop`), located with `ai-team tracker path`; the System Diagram shows the folder. Version bumped to 0.2 under the spec authoring guide's amendment rule. Driven by the loops already writing `<tracker-path>/review-packages/<id>.md`, which the principle forbade.
- **2026-10-25 (CR-007):** the "Skills never touch tracker paths directly" principle drops the Codex sandbox sentence; every agent lists `Bash` in its `tools:`. Version bumped to 0.3. Driven by CR-007 and ADR-003: Claude is the only export target.
- **2026-10-25 (format restructure):** restructured to the spec format from PR #51: added Users and Journeys, Alternatives Considered, Interfaces (tracker layout, allowed statuses, commands, legacy warning), Behavioral Requirements REQ-001–REQ-014 with acceptance scenarios, Quality Requirements, Assumptions and Dependencies and Open Questions; renamed Measurable Success Criteria to Success Criteria and linked each to its requirements; the Components section became requirements; the migration-command exclusion is stated explicitly. Format restructure only, no scope change, so the version is unchanged.
