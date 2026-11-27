---
name: integrate
description: Integrate a reviewed task or bug branch into a destination branch. Use when a branch's latest Review Verdict is PASS and it must be merged, or when a loop hands a reviewed branch to integration.
argument-hint: "<branch | task-id | bug-id> [destination-branch]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill(git-conventions)
---

# Integrate

Merge one reviewed task or bug branch into a destination branch once its tests pass.
The branch already contains the destination: the Developer merged it in before review (`git-conventions`, Syncing a Work Branch), so the merge reproduces the tree that was reviewed and tested here, and a failure merges nothing.
This skill also owns the Discovery Order for the project's baseline test command (Step 3).

## Input Requirements

Argument: `$ARGUMENTS`

- **Required:** the source branch (`task/T-012-settings-api`, `bug/B-003-login-crash`) or a work item ID (`T-012`, `B-003`).
- **Optional:** the destination branch. Default: `{{integration_branch}}`.
- **The work item file** in the local tracker.
- **A PASS verdict**, confirmed by the caller: the loop's `review-cycle` checks the latest Review Verdict before it invokes this skill, and the product owner who asks for a manual integration is responsible for it. This skill does not check it again.
- **The caller**, when it is a development or bug-fix loop: it decides whether Step 4 runs its gap check.

## Procedure

### Step 1: Resolve the Branches

1. For a work item ID, run `git branch --list 'task/<id>-*' 'bug/<id>-*'`; it must list exactly one branch. For a branch name, `git branch --list <name>` must list it. Otherwise stop `BLOCKED`: "Branch for <input> not found. Check that the branch exists locally."
2. `git branch --list <destination>` must list the destination. Otherwise stop `BLOCKED`: "Destination branch '<destination>' not found."
3. Run the before-point Workspace Hygiene check of the `git-conventions` skill, and note the branch if it parks anything.

### Step 2: Read the Work Item

1. Take the work item ID from the branch name (`task/T-012-…` → `T-012`, `bug/B-003-…` → `B-003`) and run `ai-team show <id> --json` for the file `path`. Read the file there, never a copy in a branch. Without a work item file, stop `BLOCKED`: integration needs its verification commands and criteria.
2. Read the file: for a task its Description, Acceptance Criteria, Verification, Work Log and Review; for a bug its Summary, Diagnosis Log, Fix Verification, Work Log and Review.

### Step 3: Determine the Verification Commands

**Command set**, which Step 5 runs on the source branch:

1. The concrete automated commands in the work item's `## Verification` or `## Fix Verification` section. A task whose Verification holds an `Inspection:` or `Demonstration:` line contributes only its full-suite command; its record was checked at review.
2. Otherwise the project's verification command, found with the Discovery Order below.
3. Otherwise stop `BLOCKED` and ask the product owner for the project's verification command.

Add the baseline command found with the Discovery Order, and any separate destination or baseline check the work item or the project guidance names, when they are not already in the set. The Developer runs the full suite at most once, to check its base before its first change (`tdd`), so this is the only full run on the finished branch.
When no baseline command is discoverable, record a **coverage gap**: report it with the result, never present it as full coverage; it never blocks integration by itself. When the set is empty, Step 5 is skipped.

#### Discovery Order

1. Read the root project guidance that exists, especially `AGENTS.md`, or equivalent instructions given in the session.
2. Read the project-local docs it references for test, build or verification commands, such as the coding guidelines the guidance names (default `docs/development/coding_guidelines.md`).
3. Read README files and package or build manifests when the guidance points there or no root guidance exists.
4. Take the smallest documented automated command that verifies the whole project. Prefer an explicitly documented command over one inferred from dependencies or filenames.

When several plausible baseline commands are documented, none is named the baseline, and the product owner has not named one in this session, stop `BLOCKED` and ask which to run.

### Step 4: Check the Diff

1. `git checkout <source-branch>`, then read `git diff <destination>...<source-branch> --stat`.
2. The destination must be an ancestor of the source branch: `git merge-base --is-ancestor <destination> <source-branch>` exits 0. Otherwise stop `FAIL`, nothing merged: the destination moved since the Developer last merged it, and the Developer merges it in again.
3. An empty diff, with a PASS verdict whose record shows the criteria are met on the destination (Gate 4), has nothing to merge: skip Steps 5 and 6 and go to Step 7. When the record does not show it, stop `FAIL` with a gap report.
4. A diff that adds or changes a lifecycle file (a tracker file, or legacy `tasks/`, `bugs/` or `change-requests/` files in the project directory) stops `FAIL`: lifecycle state belongs in the tracker, never in a branch.
5. **Gap check.** Skip it when the caller is a development or bug-fix loop and the latest Review Verdict's `Reviewed through:` commit is the source branch's HEAD (`git rev-parse <source-branch>`): the Reviewer already checked every criterion against this diff. Otherwise read the full diff; a diff that does not address the work item stops `FAIL` with a gap report: an acceptance criterion with no trace in the diff, or a bug fix that leaves the isolated fault of the Diagnosis Log untouched.

### Step 5: Run the Command Set

Run each line of the command set from the repository root in a fresh shell, independently of the other lines; a line that needs another directory changes into it on that line. Never run the set as one script.
Capture stdout and stderr.

If a test fails, stop `FAIL` with the failing tests and their output: nothing merged.

### Step 6: Merge

1. `git checkout <destination>`.
2. Merge without fast-forward:
   ```bash
   git merge --no-ff <source-branch> -m "chore(<kind>): merge <work-item-id> <short-description>"
   ```
   `<kind>` is `tasks` or `bugs`; the description comes from the work item title or the branch slug, shortened so the whole subject is at most 72 characters (`git-conventions`). When the project's commit conventions require trailers, add them as a second `-m "<trailer lines>"`.
   The destination is an ancestor of the source branch, so the merge cannot conflict and its tree is the one Step 5 verified: nothing runs after it.

### Step 7: Finalize

1. **Task:** run `ai-team task complete <task-id>`, then confirm that `ai-team show <task-id> --json` reports `status: completed`; if not, stop and report that the lifecycle update did not land. **Bug:** leave its status `in-progress`; the caller sets it `resolved` with `ai-team bug resolve`.
2. Delete the source branch with `git branch -d <source-branch>`; after an empty diff there is no merge, and `-d` still applies. Never use `-D`. If `-d` is refused, stop and report its error output and the merge commit, and ask the product owner to delete the branch by hand once satisfied it is safe.
3. Run the after-point Workspace Hygiene check on the destination, then restore the changes parked in Step 1 on the branch where they were parked, or on the destination when that branch was the deleted source branch.
4. Report `PASS`.

## Stops

Before reporting any stop, abort a merge still in progress (`git merge --abort`), run the after-point Workspace Hygiene check, and restore the changes parked in Step 1.
On every stop the work item's status is unchanged and the source branch is kept; the caller decides what happens next.

| Condition | Result |
|---|---|
| Branch, destination, work item or verification command missing; ambiguous baseline | `BLOCKED` |
| The destination is not an ancestor of the source branch; lifecycle files in the diff; the diff does not address the work item; the command set fails | `FAIL`, nothing merged |

## Output Format

- **Result:** `PASS`, `FAIL` or `BLOCKED`, with the stop condition.
- **Merge evidence:** the source and destination branches and the merge commit.
- **Verification:** the commands run on the source branch and their results, and the coverage gap when there is one, or why verification could not run.
- **State changes:** the task set to `completed`, the source branch deleted or kept, and `.gitignore` patterns added and changes parked or restored by the hygiene check.

## Quality Criteria

- The work item file in the tracker gave the acceptance or fix-verification context.
- The source branch contained the destination and passed the command set before the merge.
- The destination branch is clean: `git status --porcelain --untracked-files=all` is empty.

## What This Skill Does NOT Do

- Does not resolve merge conflicts or fix failing tests: the Developer does, on the source branch.
- Does not touch `main`, which is product-owner-only.
- Does not modify specifications or ADRs.
- Does not skip tests or bypass hooks (`--no-verify` is forbidden).
- Does not merge more than one branch per invocation.
- Does not merge lifecycle files from implementation branches.
- Does not change a bug's status.
