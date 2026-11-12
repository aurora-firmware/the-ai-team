---
name: dev-loop
description: Fully autonomous implementation loop that drives tasks through Developer and Reviewer cycles to integration, one task at a time, resuming in-progress tasks before pending ones. Use when Gate 2 has passed and pending or resumable tasks are ready for development. Use only when the product owner asks to run the development loop.
argument-hint: "[task-id | task-branch] — optional single task to process (e.g., T-012 or task/T-012-my-feature). If omitted, processes the full queue."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill(review-cycle), Skill(integrate), Skill(new-bug), Skill(git-conventions)
---

# Dev Loop

Processes the task queue without product owner intervention: it resumes `in-progress` tasks first, then works `pending` tasks one at a time through the `review-cycle` skill.

## Input Requirements

Argument: `$ARGUMENTS`

- **Optional:** one task ID or task branch (`T-012` or `task/T-012-my-feature`). The loop then processes only that task and stops after it.
- Without an argument, the loop processes the whole queue.
- Each single-task run repeats the baseline guard; one run over the whole queue pays for it once.

Tasks live in the local tracker, outside version control; their state is the frontmatter `status`.
The loop reads and changes it only through the `ai-team` CLI:

- `ai-team list tasks --state in-progress|pending|completed`
- `ai-team show <task-id> --json`: the file `path` and the frontmatter fields (`status`, `priority`, `created`, ...) at the top level
- `ai-team task start <task-id>`; `review-cycle` runs `ai-team task block`

## Procedure

### Step 1: Start

1. Invoke the `review-cycle` skill. Its Workspace Hygiene, Dispatch Discipline and Reading a Role's Result rules apply to the whole run. Run the startup hygiene check.
2. **Baseline test guard**, once per run. Find the project's baseline test command with the Discovery Order of the `integrate` skill, and run it from the repository root:
   - **None documented**, or the documentation says no automated tests exist: stop with `BLOCKED: no automated baseline test command is documented. Provide the command to run, or confirm that this project has no automated baseline test.` If the product owner confirms there is none, record that in the run summary and continue without a baseline run.
   - **Several plausible commands**, none named the baseline: stop with `BLOCKED: multiple plausible baseline test commands are documented. Confirm which command the loop should run before claiming tasks.`
   - **Fails:** stop with `BLOCKED: baseline test command failed before any task was claimed. Failing command: <command>. Output summary: <last 20 lines of combined stdout/stderr>.`
   - **Passes:** continue.

### Step 2: Select the Next Task

**With an argument:** extract the task ID from it and run `ai-team show <task-id> --json`.
An `in-progress` task goes to Step 3, a `pending` task to Step 4.
Anything else stops the loop with: "Task <task-id> is not a pending or in-progress task. Check the task ID and its current status."

**Without an argument:**

1. **Resume first.** Take the first `in-progress` task (`ai-team list tasks --state in-progress`) that has not returned `WAITING` in this run, and go to Step 3.
2. **Then pending work.** From `ai-team list tasks --state pending` (`planned` tasks are not in the queue), pick the task with the highest `priority` (critical → high → medium → low), then the oldest `created`, then the lowest ID, whose dependencies are all `completed`. The dependencies are the task IDs under `## Dependencies` in its file (``- `T-NNN` — reason``, or `- None`). Go to Step 4.
3. If nothing is left, go to Step 6. When pending tasks remain whose dependencies are not completed, list each with the tasks it waits for in the run summary.

### Step 3: Resume the Task

Run `review-cycle` from its Step 1, with the target branch `{{integration_branch}}`.
Then go to Step 5.

### Step 4: Claim the Task

1. Run `ai-team task start T-NNN`.
2. Check out `{{integration_branch}}` and create the task branch from it: `git checkout -b task/T-NNN-<slug>`, with the slug from the task filename.
3. Record BASE: append `Base commit: <git rev-parse HEAD>` under `## Work Log` in the task file.
4. Run `review-cycle` from its Step 2, with the target branch `{{integration_branch}}`. Then go to Step 5.

### Step 5: Act on the Outcome

| Outcome | Next |
|---|---|
| `DONE` | Step 2 |
| `WAITING` | Note the task and its unresolved bugs for the run summary; Step 2 |
| `REGRESSION` | Step 6. Next action: `/bug-loop` for the filed bugs, then `/dev-loop`, which resumes the task and retries its integration |
| `ESCALATED` | Step 6, with the report or escalation block `review-cycle` returned |
| `STOPPED` | Step 6, with the cause |

With a single-task argument, go to Step 6 after any outcome.

### Step 6: Loop Complete

1. Run the after-point Workspace Hygiene check and restore any changes this run parked.
2. Return a short run summary in the chat, a few lines and no report file:
   - tasks completed this run, with their merge commits;
   - tasks blocked, waiting on regression bugs, or stopped, with the reason;
   - bugs filed this run;
   - changes parked or restored and `.gitignore` patterns added by the hygiene check;
   - the next action: `/bug-loop` for filed bugs; for a blocked task, the product owner's decision and `ai-team task unblock`; when no task is pending, in-progress or blocked, say that the queue is drained: the main session runs completion reconciliation with the Architect for the specs this work touched, then the product owner runs `/status-report` for Gate 5.

Do not invoke `status-report`: the product owner runs it on demand.

## Commit Conventions

All commits follow the `git-conventions` skill.
The Developer commits on the task branch.
The loop session commits the hygiene check's `.gitignore` patterns and, running `integrate`, the merge and revert commits.
Task state, Work Logs and Review Verdicts live in the tracker and are never committed.

## Hard Stops (Do Not Continue)

Every stop goes through Step 6.

- The baseline test guard stops `BLOCKED`.
- `review-cycle` returns `REGRESSION`, `ESCALATED` or `STOPPED`.
- No pending task has all its dependencies completed, and no task can be resumed.

## What This Skill Does NOT Do

- Does not touch `main`, which is product-owner-only.
- Does not modify specifications or decisions, or touch implementation and test files itself.
- Does not fix integration failures: regressions are filed as bugs, and the bug-fix loop fixes them.
