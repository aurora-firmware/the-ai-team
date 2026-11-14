---
name: integrate
description: Integrate a reviewed task or bug branch into a destination branch. Use when a branch's latest Review Verdict is PASS and it must be merged, or when a loop hands a reviewed branch to integration.
argument-hint: "<branch | task-id | bug-id> [destination-branch]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill(merge-conflicts), Skill(new-bug), Skill(git-conventions)
---

# Integrate

Merge one reviewed task or bug branch into a destination branch, verifying it before and after the merge.
This skill also owns the Discovery Order for the project's baseline test command (Step 3).

## Input Requirements

Argument: `$ARGUMENTS`

- **Required:** the source branch (`task/T-012-settings-api`, `bug/B-003-login-crash`) or a work item ID (`T-012`, `B-003`).
- **Optional:** the destination branch. Default: `{{integration_branch}}`.
- **The work item file** in the local tracker.
- **A PASS verdict**, confirmed by the caller: the loop's `review-cycle` checks the latest Review Verdict before it invokes this skill, and the product owner who spawns an Integrator is responsible for it. This skill does not check it again.
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

**Source command**, which Step 5 runs on the source branch:

1. The concrete automated commands in the work item's `## Verification` or `## Fix Verification` section. A task whose Verification holds an `Inspection:` or `Demonstration:` line contributes only its full-suite command; its record was checked at review. When it lists no full-suite command because the project documents none, there is no source command: Step 5 is skipped.
2. Otherwise the project's verification command, found with the Discovery Order below.
3. Otherwise stop `BLOCKED` and ask the product owner for the project's verification command.

**Destination command**, which Step 7 runs after the merge to catch regressions outside the work item's scope. Never default it to the source command:

1. A separate destination or baseline check that the work item or the project guidance names.
2. Otherwise the baseline command found with the Discovery Order.
3. When it differs from the source command, Step 7 runs both, except on the identical tree Step 7 describes.
4. When no baseline command is discoverable, Step 7 runs only the source command, or nothing when there is none. Record this as a **coverage gap**. A coverage gap is reported with the result and never presented as full coverage; it never blocks integration by itself.

#### Discovery Order

1. Read the root project guidance that exists, especially `AGENTS.md`, or equivalent instructions given in the session.
2. Read the project-local docs it references for test, build or verification commands, such as the coding guidelines the guidance names (default `docs/development/coding_guidelines.md`).
3. Read README files and package or build manifests when the guidance points there or no root guidance exists.
4. Take the smallest documented automated command that verifies the whole project. Prefer an explicitly documented command over one inferred from dependencies or filenames.

When several plausible baseline commands are documented, none is named the baseline, and the product owner has not named one in this session, stop `BLOCKED` and ask which to run.

### Step 4: Check the Diff

1. `git checkout <source-branch>`, then read `git diff <destination>...<source-branch> --stat`.
2. Note whether the destination is an ancestor of the source branch: `git merge-base --is-ancestor <destination> <source-branch>` exits 0. Then the merge produces the source branch's tree, and Step 7 runs only what Step 5 did not.
3. An empty diff, with a PASS verdict whose record shows the criteria are met on the destination (Gate 4), has nothing to merge: skip Steps 5 to 8 and go to Step 9. When the record does not show it, stop `FAIL` with a gap report.
4. A diff that adds or changes a lifecycle file (a tracker file, or legacy `tasks/`, `bugs/` or `change-requests/` files in the project directory) stops `FAIL`: lifecycle state belongs in the tracker, never in a branch.
5. **Gap check.** Skip it when the caller is a development or bug-fix loop and the latest Review Verdict's `Reviewed through:` commit is the source branch's HEAD (`git rev-parse <source-branch>`): the Reviewer already checked every criterion against this diff. Otherwise read the full diff; a diff that does not address the work item stops `FAIL` with a gap report: an acceptance criterion with no trace in the diff, or a bug fix that leaves the isolated fault of the Diagnosis Log untouched.

### Step 5: Run the Source Command

Run each line of the command set from the repository root in a fresh shell, independently of the other lines; a line that needs another directory changes into it on that line. Never run the set as one script.
Capture stdout and stderr.

If a test fails, stop `FAIL` with the failing tests and their output: a pre-merge failure, nothing merged.

### Step 6: Merge

1. `git checkout <destination>`.
2. Merge without fast-forward:
   ```bash
   git merge --no-ff <source-branch> -m "chore(<kind>): merge <work-item-id> <short-description>"
   ```
   `<kind>` is `tasks` or `bugs`; the description comes from the work item title or the branch slug, shortened so the whole subject is at most 72 characters (`git-conventions`). When the project's commit conventions require trailers, add them as a second `-m "<trailer lines>"`.
3. On a conflict, invoke the `merge-conflicts` skill with the source branch, the destination and the work item file. It either concludes the merge or aborts it and returns `ESCALATE`. On `ESCALATE`, confirm that no merge is in progress (`git merge --abort` if `.git/MERGE_HEAD` still exists) and stop `ESCALATE` with its escalation block.

### Step 7: Run the Destination Command

On the destination branch, run the destination command set the same way as Step 5, and report any coverage gap with the result.
When Step 4 found the destination to be an ancestor of the source branch, the merged tree is the tree Step 5 verified: run only the destination command lines Step 5 did not run, and report the others as verified pre-merge on the identical tree. When Step 5 ran them all, nothing runs here.
When everything passes, go to Step 9; otherwise go to Step 8.

### Step 8: Regression Path

1. Take the failing set: the union of failing tests across every command Step 7 ran. Note the merge commit.
2. Revert the merge with the required message:
   ```bash
   git revert -m 1 --no-commit HEAD
   git commit -m "chore(<kind>): revert merge of <source-branch> — regression in <test-names>"
   ```
3. Attribute every failing test to the source branch, without re-running anything on the reverted destination: the process trusts the destination to be green before the merge (Gate 4). When the cause lies elsewhere, the regression bug's diagnosis finds it.
4. File one bug with the `new-bug` skill for each failing test. Bug reports live in the tracker: no branch switch and no commit. Classify each for evidence only: a **true regression** passed in Step 5; a **previously-uncovered failure** ran only in the baseline command. Give the full input set:
   - `title`: a concise regression title
   - `severity`: from user impact, data risk, security risk and how much of the system is blocked
   - `summary`: the merge commit, the destination, the source branch, and the classification
   - `source_branch`: the source branch, so the bug-fix loop fixes the regression on that preserved branch before integration is retried
   - `expected_behavior`: the command passes after integration
   - `actual_behavior`: the failing test name and error message
   - `evidence`: the failing command and an output summary, the merge commit, the destination and source branches, and whether Step 5 ran and passed the test
   - `fix_verification`: the destination command that must pass after the fix
   - `details`: Reproduction Status `confirmed`; Reproduction Steps: the destination command that fails; Environment: the runtime details known from the run; Suspected Area: the changed files implicated, or `unknown`
5. Run the after-point Workspace Hygiene check on the destination, then `git checkout <source-branch>`.
6. Stop `FAIL`: the regressions found, the bug IDs, the reverted merge and the kept source branch. Integration is retried once those bugs are resolved on the source branch.

### Step 9: Finalize

1. **Task:** run `ai-team task complete <task-id>`, then confirm that `ai-team show <task-id> --json` reports `status: completed`; if not, stop and report that the lifecycle update did not land. **Bug:** leave its status `in-progress`; the caller sets it `resolved` with `ai-team bug resolve`.
2. Delete the source branch with `git branch -d <source-branch>`; after an empty diff there is no merge, and `-d` still applies. Never use `-D`. If `-d` is refused, stop and report its error output and the merge commit, and ask the product owner to delete the branch by hand once satisfied it is safe.
3. Run the after-point Workspace Hygiene check on the destination, then restore the changes parked in Step 1 on the branch where they were parked, or on the destination when that branch was the deleted source branch.
4. Report `PASS`.

## Stops

Before reporting any stop, abort a merge or revert still in progress (`git merge --abort`, `git revert --abort`), run the after-point Workspace Hygiene check, and restore the changes parked in Step 1.
On every stop the work item's status is unchanged and the source branch is kept; the caller decides what happens next.

| Condition | Result |
|---|---|
| Branch, destination, work item or verification command missing; ambiguous baseline | `BLOCKED` |
| Lifecycle files in the diff; the diff does not address the work item; the source command fails | `FAIL`, nothing merged |
| Post-merge regression | `FAIL`, bugs filed and merge reverted |
| A conflict `merge-conflicts` cannot resolve | `ESCALATE` |

## Escalation

The self-recovery threshold is one merge attempt.
Return `ESCALATE` with the four-field request in the format `escalation-review` owns when Step 6 hits a conflict `merge-conflicts` cannot resolve (pass on its block):

```text
Problem: [the unresolved conflict]
Attempted: [the merge attempt and the merge-conflicts run]
Failed because: [why the conflict cannot be resolved]
Question: [which work item owns the behavior, which spec applies, or how to resolve]
```

Do not force-resolve a conflict or pick a side.

## Output Format

- **Result:** `PASS`, `FAIL`, `BLOCKED` or `ESCALATE`, with the stop condition.
- **Merge evidence:** the source and destination branches, the merge commit, and the revert commit if one was made.
- **Verification:** the pre-merge and post-merge commands and results, and the coverage gap when there is one, or why verification could not run.
- **State changes:** the task set to `completed`, regression bugs filed, the source branch deleted or kept, and `.gitignore` patterns added and changes parked or restored by the hygiene check.

## Quality Criteria

- The work item file in the tracker gave the acceptance or fix-verification context.
- The source branch was verified before the merge, and the destination after it unless the merge produced the tree verified before it.
- Regression bugs carry enough evidence for the bug-fix loop to reproduce and fix them on the preserved source branch.
- The destination branch is clean: `git status --porcelain --untracked-files=all` is empty.

## What This Skill Does NOT Do

- Does not fix regressions: they are filed as bugs.
- Does not touch `main`, which is product-owner-only.
- Does not modify specifications or ADRs.
- Does not skip tests or bypass hooks (`--no-verify` is forbidden).
- Does not merge more than one branch per invocation.
- Does not merge lifecycle files from implementation branches.
- Does not change a bug's status.
