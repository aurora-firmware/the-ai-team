---
name: dev-loop
description: Fully autonomous implementation loop that drives pending tasks through Developer and Reviewer cycles to integration, one task at a time. Use when Gate 2 has passed and pending tasks are ready for development. Use only when the human asks to run the development loop.
argument-hint: "[task-id | task-branch] — optional single task to process (e.g., T-012 or task/T-012-my-feature). If omitted, processes the full pending queue."
allowed-tools: Read, Glob, Grep, Bash, Agent, Skill(integrate), Skill(new-bug), Skill(git-conventions)
---

# Dev Loop

Autonomous orchestrator that processes the pending task queue without human intervention.
Stops only at hard gates: empty queue, blocked task, or escalation.

## Input Requirements

Optional: a single task ID or branch name as `$ARGUMENTS` (e.g., `T-012` or `task/T-012-my-feature`).
- If provided, the loop processes only that task — it does not continue to the next task after completion or failure.
- If omitted, the loop processes the full pending queue until empty, blocked, or escalated.

Tasks live in the local tracker, outside version control. Their lifecycle state is the frontmatter `status` field.
The orchestrator reads and changes task state only through the `ai-team` CLI:
- `ai-team list tasks --state pending` — pending work queue
- `ai-team list tasks --state in-progress` — active task slot
- `ai-team show <task-id> --json` — the task file's `path` and current frontmatter
- `ai-team task start|block <task-id>` — lifecycle transitions

Recording lifecycle state never creates a commit and never needs a branch switch: the task file is outside every branch.
Developer branches carry implementation artifacts only.

## Workspace Hygiene

The loop applies the **Workspace Hygiene** check from the `git-conventions` skill at these points:

- **Startup** — before the baseline guard, on the branch the loop starts from.
- **Before every branch switch** — a checkout refused because of a dirty tree is not a hard stop; run the check, then retry the checkout once.
- **After every `integrate` invocation** — whether it succeeded or stopped.
- **Before the loop ends** — in Step 8 and before reporting any hard stop.

Changes parked by this run are restored when the loop ends, on the branch where they were parked.
A run never ends with untracked files or uncommitted changes that the run itself created.

## Dispatch Discipline

Each subagent starts cold, and the orchestrator's context is the scarce resource. These rules keep both small:

- **Model tier at every spawn.** State the tier explicitly in each **Spawn** block, using the table below. The role's agent definition sets a default; the tier named at the spawn overrides it for that dispatch.
- **Never paste prior-work-item history into a dispatch.** Pass the work item file path. A subagent reads what it needs from the file, and earlier items' logs do not belong in its prompt.
- **Review packages, not diffs in context.** The loop writes the review range to a single file and passes its path (Step 6). The diff never enters the orchestrator's context.
- **Record BASE before the Developer starts.** The branch's base commit is the start of every review range.

| Tier | Use for |
|---|---|
| cheap | Mechanical, fully specified work items: a rename, a config change, a transcription from the spec |
| standard | The default for the Developer, the Reviewer, and manual integration |
| most capable | Architect consultation, the fresh Developer on the third attempt (capability ladder) |

## Procedure

### Step 1: Check the Queue

If `$ARGUMENTS` is non-empty:
- Parse it as a task ID (e.g., `T-012`) or branch name (e.g., `task/T-012-my-feature`). Extract the task ID either way.
- Run `ai-team show <task-id> --json` and confirm its `status` is `pending`.
- If the task does not exist or is not `pending`, stop with: "Task <task-id> is not a pending task. Check the task ID and its current status."
- Use this single task as the queue. After it completes (success, blocked, or escalated), stop — do not continue to other tasks.

If `$ARGUMENTS` is empty, discover pending tasks using: `ai-team list tasks --state pending`.
Tasks with status `planned` are not part of the queue: their planning branch has not merged yet.
If the queue is empty, proceed directly to **Step 8: Loop Complete** so the workspace is checked
and the run summary is returned before the loop stops.

### Step 2: Baseline Test Guard

The baseline guard runs once at loop startup. It is NOT re-checked between tasks. Rationale: post-merge regressions are caught by the integrate skill's destination-branch test step; re-checking between tasks adds latency without adding coverage.

Discover and run the project's baseline test command from project-specific guidance before claiming any task. Start with root guidance (`CLAUDE.md`, `AGENTS.md`, or equivalent instructions provided in the session), then follow clear references to project-local docs such as `{{project_dir}}/docs/coding_guidelines.md`, README files, build configuration, or other documented test instructions. Prefer an explicitly documented test command over inferring one from dependencies or filenames.

Skip this step when looping back after a completed task (control returns to Step 1, which skips Step 2 on subsequent iterations).

#### Discovery Order

1. Read root project guidance files that exist, especially `CLAUDE.md` and `AGENTS.md`.
2. Read any project-local docs referenced by those files for test, build, or verification commands.
3. Read common project documentation or configuration files when guidance points there or no root guidance exists, such as README files, package/build manifests, or project-specific coding guidelines.
4. Identify the smallest documented automated command that verifies the project starts green enough for task work.

#### Missing or Unavailable

If no automated baseline test command is documented, or the documentation explicitly says no automated tests exist, ask the human for one of these before claiming a task:

- The intended baseline test command to run.
- Explicit confirmation that no automated baseline test is available for this project.

Stop until the human responds. Report:
`BLOCKED: no automated baseline test command is documented. Provide the command to run, or confirm that this project has no automated baseline test.`

If the human confirms that no automated baseline test is available, record that confirmation in the loop summary and continue to Step 3 without running a baseline command.

#### Ambiguous

If multiple plausible automated baseline commands are documented and no source clearly identifies which one is the baseline, ask the human which command to use before claiming a task.

Stop until the human responds. Report:
`BLOCKED: multiple plausible baseline test commands are documented. Confirm which command the loop should run before claiming tasks.`

#### Runnable

If a clear baseline test command is documented, run it.

- If the baseline test command passes, continue to Step 3.
- If the baseline test command fails, stop immediately and report: `BLOCKED: baseline test command failed before any task was claimed. Failing command: <command>. Output summary: <last 20 lines of combined stdout/stderr>.`

### Step 3: Pick the Next Task

Select the highest-priority task whose dependencies are all satisfied:
1. **Priority order:** critical → high → medium → low (read from task frontmatter `priority` field)
2. **Dependency check:** for each candidate task, open the file at the `path` reported by `ai-team show T-NNN --json` and read the task IDs listed under its `## Dependencies` section (lines of the form ``- `T-NNN` — reason``). Confirm each of those tasks has status `completed` (`ai-team list tasks --state completed`). A `- None` entry means the task has no dependencies.
3. **Tiebreak:** oldest `created` date first

If no task has all dependencies satisfied, stop and report which tasks are waiting and what they are waiting for.

### Step 4: Claim the Task

1. Run `ai-team task start T-NNN`. This sets the status to `in-progress`; there is nothing to commit.
2. Switch to `{{integration_branch}}` and create the task branch from it: `git checkout -b task/T-NNN-short-description` (derive from the task filename).
3. Record the base: `git rev-parse HEAD` on the new branch is `BASE`. Append `Base commit: <sha>` under `## Work Log` in the task file, so it survives a restart of the loop. Step 6 reviews `BASE..HEAD`.

### Step 5: Implementation Cycle

Read the task file at the path reported by `ai-team show T-NNN --json`, and check out the task branch `task/T-NNN-...`.

**Spawn the Developer subagent** (tier: standard, or cheap for a mechanical task) with this prompt:

> "Pick up the task from the task file `<task-path>` and implement it using the tdd skill.
> You are on branch `task/T-NNN-...`. Follow the task's declared verification mode using the tdd skill. For test tasks, commit after each red→green→refactor cycle. For design-review tasks, commit the reviewed changes and include the design-review record in your Work Log handoff.
> The task file is in the local tracker, outside version control: do not edit it, and never add it to a commit.
> Return a Work Log handoff entry at session end. The entry's heading is `### Session N — YYYY-MM-DD`; the body is free prose covering what was done, what was tried and rejected, and what remains. The loop will append it to the task file.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the Developer to complete before continuing.
If the Developer returns `ESCALATE`, go directly to **On ESCALATE**.
If the Developer does not return a Work Log handoff entry, stop with `BLOCKED` and report the missing handoff.

Record the Work Log handoff: append the Developer's entry under `## Work Log` in the task file.
Stay on the task branch — no switch and no commit. Bug files the Developer filed through `new-bug` are already in the tracker.

### Step 6: Review Cycle

**Write the review package.** Record the range as `BASE..HEAD` of the task branch, with `BASE` from the claim in Step 4.
Write one file, `<tracker-path>/review-packages/<id>.md` (find `<tracker-path>` with `ai-team tracker path`), holding the output of:

```bash
git log --oneline BASE..HEAD
git diff --stat BASE..HEAD
git diff -U10 BASE..HEAD
```

Rewrite it before every review cycle so it covers the whole range, including commits from earlier cycles. Delete it when the task leaves the loop. It lives in the tracker, so it is never committed.

**Spawn the Reviewer subagent** (tier: standard) with this prompt:

> "Review the task in the task file `<task-path>` using the code-review skill.
> The Developer has completed their work on branch `task/T-NNN-...`.
> The review range and its diff are in the review package `<package-path>`; read that one file instead of deriving the diff yourself.
> Append your verdict to the task file's Review section under `### Review Verdict — YYYY-MM-DD`. The task file is outside version control: do not commit it.
> Treat the Work Log as unverified claims about the code and check them against the diff. Do not re-run tests the Work Log already shows passing.
> Rate each finding Critical, Important, or Minor as the code-review skill defines. List Minor findings under `#### Deferred Minor findings` and anything you cannot confirm from the diff under `#### ⚠️ Cannot verify from diff`.
> Verdict must be one of: PASS, FAIL, or ESCALATE. On ESCALATE, include the four-field escalation request block defined in the code-review skill.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the reviewer to complete before continuing.

**Keep the Reviewer prompt neutral.** It names the work item, the branch, and the skill, and nothing else about what to conclude. If the prompt you are writing contains "do not flag", "don't treat X as a defect", "at most Minor", or "the plan chose", stop: you are pre-judging the review, usually to spare yourself a review loop. Put the context the Reviewer needs in the task file, not in a verdict hint.

### Step 7: Read the Verdict

Read the task file and find the most recent `### Review Verdict` entry.
Extract the verdict: **PASS**, **FAIL**, or **ESCALATE**.

#### On PASS

If the verdict lists `⚠️ Cannot verify from diff` items, resolve each one before integration, using what the loop knows (other completed work items' Work Logs, the approved spec, the repository). Append the resolution under the verdict. If an item cannot be confirmed, treat the verdict as FAIL for that item and go to **On FAIL**.

Apply the same handling to a deferred Minor finding. If the loop's own checks show that a finding the Reviewer listed under `#### Deferred Minor findings` is a real failure, for example it breaks CI or contradicts the task, treat the verdict as FAIL for that item and go to **On FAIL**. This is the same handling as an unconfirmable `⚠️ Cannot verify from diff` item. When promoting a finding, append ` — resolved: promoted to FAIL` to that entry's line in the verdict's `#### Deferred Minor findings` list, so the Gate 5 roll-up shows it as resolved rather than still deferred.

Before invoking integration, confirm that the task file holds both the Developer Work Log entry
and the Review Verdict recorded in Steps 5 and 6. The `integrate` skill verifies that the latest
verdict in the task file is PASS before it merges.

1. Invoke the `integrate` skill to merge the reviewed branch into `{{integration_branch}}`:
   > `/integrate task/T-NNN-... {{integration_branch}}`

   The integrate skill handles test verification, the merge, regression checks, setting the task to `completed`, and branch deletion.

2. **If integrate succeeds** — the branch is merged and deleted, and the task status is `completed`. Go back to **Step 1** to pick the next task.

3. **If integrate fails** — stop the loop entirely and report:
   - The failure reason (pre-merge test failure, unmet acceptance criteria, or post-merge regression).
   - Which bug IDs were filed (if regressions were found).
   - That the feature branch was NOT deleted and `{{integration_branch}}` was left clean (integrate reverts on regression).
   - Next step for the human: run `/bug-loop` to autonomously fix the filed regressions, then re-run `/dev-loop`.

#### On FAIL

Increment the review cycle counter.

Climb the capability ladder — each rung changes who attempts the fix, so a stuck task is not retried identically:

- If **cycle = 1**: go back to **Step 5** with the same Developer, who keeps the continuity of the session. The Developer fixes the issues noted in the Review Verdict.
- If **cycle = 2**: go back to **Step 5** with a **fresh Developer subagent on the most capable tier**. Pass only the task file path: its Work Log and Review Verdicts carry everything the fresh Developer needs, and it does not inherit the failed session's reasoning. This happens before any Architect consultation is spent.
- If **cycle = 3**: treat as ESCALATE (max review cycles exceeded).

#### On ESCALATE

Follow the Phase 2 escalation chain below. Step 1 is a single Architect consultation; Step 2 is human escalation. The chain is linear — no second Architect round.

**Phase 2, Step 1 — Architect Consultation:**
**Spawn the Architect subagent** (tier: most capable) with this prompt:

> "Use the escalation-review skill for the task in `<task-path>`.
> Problem: <what the reviewer or loop found>
> Attempted: <what the Developer tried and how many review cycles occurred>
> Failed because: <why the task still cannot pass>
> Question: <specific guidance needed to continue within the approved specification>
> Populate every field of the Output Format block, including `Obstacles Encountered`."

If the Architect resolves the issue, go back to **Step 5** with the Architect's guidance.

If the Architect adjudicates that specific findings of the last FAIL verdict should be **parked** rather than fixed — the task meets its criteria without them — the loop makes each parked finding a durable artifact before continuing; a ledger line in the chat is not one:
- file it as a new bug with the `new-bug` skill, naming this task and the finding, or
- record it under a `### Recorded deviation — YYYY-MM-DD` heading in the task file with the Architect's rationale.

Then spawn the Reviewer again (Step 6). Its prompt stays neutral; the recorded deviation is in the task file, where the Reviewer reads it. Parked findings never count toward the cycle cap and are never deleted with the workspace.

**Phase 2, Step 2 — Human Escalation:**
If the Architect cannot resolve the issue:
1. Run `ai-team task block T-NNN --reason "<one-line reason>"`. The reason is recorded in the task's Work Log; there is nothing to commit.
2. Stop the loop entirely.
3. Produce the report using the Phase 2 Human Escalation Report template defined in the `escalation-review` skill. Fill every section (Work item, Original request, Self-recovery attempts, Architect analysis, Why human input is required, Decision needed).

### Step 8: Loop Complete

Reporting is on demand. Do not invoke the `status-report` skill and do not write a report file.
The human runs `/status-report` when they want the full Gate 5 summary.

1. Run the after-point Workspace Hygiene check and restore any changes this run parked.
2. Return a short run summary in the chat — a few lines, not a report:
   - Tasks completed and merged this run, with task IDs and merge commits
   - Tasks blocked or escalated, with the reason
   - Bugs filed this run, and any integration failure that stopped the loop
   - Changes parked or restored, and `.gitignore` patterns added, by the hygiene check
   - The next suggested action — for example `/bug-loop` for filed regressions, or, when the queue is empty, asking the Architect for spec-truth reconciliation and then running `/status-report` for Gate 5 sign-off context

## Cycle Counter Reset

The review cycle counter resets to 0 each time a new task is picked up in Step 3.
It is local to each task — one task failing twice does not affect the counter for the next task.

## Commit Conventions

All commits follow the `git-conventions` skill.
The loop itself makes no commits: task state, Work Log entries, and Review Verdicts live in the tracker, outside version control.
Implementation commits are made by the Developer on the task branch, and the merge commit is made by the `integrate` skill.
The orchestrator does not touch implementation or test files.

## Hard Stops (Do Not Continue)

- A task is set to `blocked` — stop the loop, notify the human
- Integration fails for any reason (pre-merge test failure, unmet criteria, post-merge regression) — stop the loop, report the failure and any filed bug IDs
- A git operation fails (branch already exists, merge conflict on `{{integration_branch}}`, etc.) — stop and report the git error before attempting anything else
- A task already has status `in-progress` when the loop starts — stop and ask the human whether to resume that task or treat it as abandoned

## What This Skill Does NOT Do

- Does not touch `main` — human-only branch
- Does not modify specifications or decisions
- Does not fix integration failures — regressions are filed as bugs and the loop stops; fixing is the Developer's job on a subsequent cycle
