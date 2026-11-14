---
name: bug-loop
description: Fully autonomous bug-fix loop. Resumes in-progress bugs, then picks open bugs one at a time, creates a dedicated branch from the correct base, and drives each through diagnosis-first Developer → Reviewer cycles to integration. Stops when the queue is empty or a bug needs the product owner. Use only when the product owner asks to run the bug-fix loop.
argument-hint: "[green] [bug-id ...] — optional `green` when the integration branch is known green, and optional space-separated bug IDs (e.g., green B-001 B-003). If no bug is given, processes the full queue."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill(review-cycle), Skill(integrate), Skill(new-bug), Skill(git-conventions)
---

# Bug Loop

Processes the bug queue without product owner intervention: it resumes `in-progress` bugs first, then works `open` bugs one at a time.
Each bug is diagnosed before it is fixed, and gets its own branch.
The fix, review and integration run through the `review-cycle` skill.

## Input Requirements

Argument: `$ARGUMENTS`

- **Optional:** one or more bug IDs (`B-001 B-003`). The loop then processes only those bugs.
- Without bug IDs, the loop processes the whole queue.
- **Optional:** the word `green`, or a statement in the request that `{{integration_branch}}` is green. The caller vouches that the suite passes on it; the loop passes that on to each diagnosis (Step 5) as the `review-cycle` Green Base rule describes.

Bugs live in the local tracker, outside version control; their state is the frontmatter `status`.
The loop reads and changes it only through the `ai-team` CLI:

- `ai-team list bugs --state in-progress|open`
- `ai-team show <bug-id> --json`: the file `path` and the frontmatter fields (`status`, `severity`, `created`, `source_branch`, ...) at the top level
- `ai-team bug start <bug-id>`; `review-cycle` runs `ai-team bug resolve` and `ai-team bug block`

Every role reads the bug file from the same tracker path, also on a bug branch based on a preserved task branch.

## Procedure

### Step 1: Start

Invoke the `review-cycle` skill.
Its Workspace Hygiene, Green Base, Dispatch Discipline and Reading a Role's Result rules apply to the whole run.
Run the startup hygiene check.

### Step 2: Select the Next Bug

With bug IDs, each listed bug must be `open` or `in-progress`; otherwise stop with "Bug <id> is not an open or in-progress bug. Verify the ID and status."
Select only among the listed bugs.

1. **Resume first.** Take the first `in-progress` bug that has not returned `WAITING` in this run, and go to Step 3.
2. **Then open bugs.** Pick the `open` bug with the highest `severity` (critical → high → medium → low), then the oldest `created`, and go to Step 4.
3. If nothing is left, go to Step 7.

The loop never picks a `blocked` bug. A bug stopped by escalation stays `blocked`, also when the product owner defers it, until the product owner runs `ai-team bug unblock`; the next run then resumes it.

### Step 3: Resume the Bug

Run `review-cycle` from its Step 1, with the bug's target branch: its `source_branch` when non-empty, otherwise `{{integration_branch}}`.
A `DIAGNOSE` outcome goes to Step 5; every other outcome goes to Step 6.

### Step 4: Claim the Bug

1. Run `ai-team bug start B-NNN` and read the bug file.
2. Choose the base and target branch: the bug's `source_branch` when non-empty, otherwise `{{integration_branch}}`. The bug branch is created from it and merges back into it.
3. Check out the base and create the bug branch: `git checkout -b bug/B-NNN-<slug>`, with the slug from the bug filename.
4. Record BASE: append `Base commit: <git rev-parse HEAD>` under `## Work Log` in the bug file.

### Step 5: Diagnosis

**Spawn the Developer subagent** (tier: standard) with this prompt:

> "Diagnose the bug in the bug file `<bug-path>` with the debug skill. You are on branch `bug/B-NNN-<slug>`.
> The bug file is in the local tracker, outside version control: do not edit it, and never add it to a commit.
> Return the fix contract (debug) as your Diagnosis Log handoff entry; the loop appends it to the bug file.
> If the bug cannot be reproduced and no evidence-backed fault hypothesis can be formed, return ESCALATE: do not guess.
> <base line>
> Populate every field of the Output Format block, including `Obstacles Encountered`."

The `<base line>` follows the `review-cycle` Green Base rule for the bug's base branch:

- known green: "The base `<BASE>` is green: <the caller's statement | the baseline run | the integration of <ID> | the pre-merge run recorded in this bug's evidence>. Do not run the full suite to establish the base state."
- not known green: "The base `<BASE>` is not known green: run the full suite on it before any diagnostic edit and record the result."

Read the result (`review-cycle`, Reading a Role's Result):

- `ESCALATE` or `BLOCKED`: run `review-cycle` from its Step 7 with the Developer's escalation block, as a diagnosis escalation. A `DIAGNOSE` outcome repeats this step; every other outcome goes to Step 6.
- No Diagnosis Log handoff entry: stop, and report the missing handoff (Step 7).
- Otherwise: append the entry under `## Diagnosis Log` in the bug file. It is the fix contract. Run `review-cycle` from its Step 2, then go to Step 6.

### Step 6: Act on the Outcome

| Outcome | Next |
|---|---|
| `DONE` | Step 2 |
| `WAITING` | Note the bug and its unresolved regression bugs for the run summary; Step 2 |
| `REGRESSION` | Step 7. The filed bugs are `open` and the next run works them first; the parent bug resumes once they are resolved |
| `ESCALATED` | Step 7, with the report or escalation block `review-cycle` returned |
| `STOPPED` | Step 7, with the cause |

### Step 7: Loop Complete

1. Run the after-point Workspace Hygiene check and restore any changes this run parked.
2. Return a short run summary in the chat, a few lines and no report file:
   - bugs resolved this run, with their merge commits;
   - bugs blocked, waiting on regression bugs, or stopped, with the reason;
   - regression bugs filed this run;
   - changes parked or restored and `.gitignore` patterns added by the hygiene check;
   - the next action: `/bug-loop` for filed regressions; for a blocked bug, the product owner's decision and `ai-team bug unblock`; `/dev-loop` when a task waits for its regression fixes, which resumes the task and retries its integration; when no bug is open, in-progress or blocked and no task is pending, in-progress or blocked, say that the queue is drained: the main session runs completion reconciliation with the Architect for the specs this work touched, then the product owner runs `/status-report` for Gate 5.

Do not invoke `status-report`: the product owner runs it on demand.

## Commit Conventions

All commits follow the `git-conventions` skill.
The Developer commits on the bug branch.
The loop session commits the hygiene check's `.gitignore` patterns and, running `integrate`, the merge and revert commits.
Bug state, Diagnosis Logs, Work Logs and Review Verdicts live in the tracker and are never committed.

## Hard Stops (Do Not Continue)

Every stop goes through Step 7.

- `review-cycle` returns `REGRESSION`, `ESCALATED` or `STOPPED`.
- The Developer returns no Diagnosis Log handoff entry.

## What This Skill Does NOT Do

- Does not touch `main`, which is product-owner-only.
- Does not modify specifications or task files, or touch implementation and test files itself.
- Does not mix bugs on one branch.
- Does not patch a bug it cannot reproduce or explain: that bug is escalated.
