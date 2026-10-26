---
name: bug-loop
description: Fully autonomous bug-fix loop. Picks open bugs one at a time, creates a dedicated branch from the correct base, drives each through diagnosis-first Developer → Reviewer cycles until the reviewer passes, then moves to the next bug. Stops only when the queue is empty or a bug cannot be resolved after full escalation. Use only when the product owner asks to run the bug-fix loop.
argument-hint: "[bug-id ...] — optional space-separated bug IDs (e.g., B-001 B-003). If omitted, processes all open bugs."
allowed-tools: Read, Glob, Grep, Bash, Agent, Skill(integrate), Skill(new-bug), Skill(git-conventions)
---

# Bug Loop

Autonomous orchestrator that processes the open bug queue without product owner intervention.
Each bug gets its own branch — bugs are never mixed on the same branch.
Stops only when the queue is empty or when a bug requires product owner resolution after full escalation.

## Input Requirements

Optional: one or more bug IDs as `$ARGUMENTS` (e.g., `B-001 B-003`).
- If bug IDs are provided, the loop processes only those bugs — skipping all others in the queue.
- If omitted, the loop processes every bug with status `open`.

Bugs live in the local tracker, outside version control. Their lifecycle state is the frontmatter `status` field.
The orchestrator reads and changes bug state only through the `ai-team` CLI:
- `ai-team list bugs --state open` — work queue
- `ai-team list bugs --state in-progress` — active bug slot
- `ai-team show <bug-id> --json` — the bug file's `path` and current frontmatter
- `ai-team bug start|resolve <bug-id>` — lifecycle transitions

Because the bug file is outside every branch, every role reads it from the same path, including on task-regression bug branches based on a preserved task branch.
Recording lifecycle state never creates a commit and never needs a branch switch.

## Workspace Hygiene

The loop applies the **Workspace Hygiene** check from the `git-conventions` skill at these points:

- **Startup** — before claiming a bug, on the branch the loop starts from.
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
- Parse it as a space-separated list of bug IDs (e.g., `B-001 B-003`).
- For each ID, run `ai-team show <id> --json` and confirm its `status` is `open`.
- If any ID does not exist or is not `open`, stop with: "Bug <id> is not an open bug. Verify the ID and status."
- Use this filtered list as the queue for the entire run.

If `$ARGUMENTS` is empty, use `ai-team list bugs --state open` as the queue.

If the queue is empty, proceed directly to **Step 8: Loop Complete** so the workspace is checked
and the run summary is returned before the loop stops.

### Step 2: Pick the Next Bug

Select the highest-severity unblocked bug:
1. **Severity order:** critical → high → medium → low (read from bug frontmatter `severity` field)
2. **Tiebreak:** oldest `created` date first

### Step 3: Claim the Bug

1. Run `ai-team bug start B-NNN`. This sets the status to `in-progress`; there is nothing to commit.
2. Read the bug file at the path reported by `ai-team show B-NNN --json`.
3. Determine the bug branch base and target:
   - If the bug frontmatter has a non-empty `source_branch`, use that branch as both the base and target.
   - Otherwise use `{{integration_branch}}` as both the base and target.
4. Switch to the selected base and create the bug branch from it: `git checkout -b bug/B-NNN-short-description`
   - Derive the branch name from the bug filename (e.g., `B-001-system-prompt-exposed` → `bug/B-001-system-prompt-exposed`)
5. Record the base: `git rev-parse HEAD` on the new branch is `BASE`. Append `Base commit: <sha>` under `## Work Log` in the bug file, so it survives a restart of the loop. Step 6 reviews `BASE..HEAD`.

### Step 4: Diagnosis Cycle

**Spawn the Developer subagent** (tier: standard) with this prompt:

> "Diagnose the bug described in the bug file `<bug-path>`.
> You are on branch `bug/B-NNN-...`.
> Use the debug skill first.
> The bug file is in the local tracker, outside version control: do not edit it, and never add it to a commit.
> Do not change production code during diagnosis.
> Reproduce or confirm the defect, gather relevant logs or command output, isolate the fault, and return a Diagnosis Log handoff entry.
> The Diagnosis Log entry must record reproduction status, evidence captured, isolated fault, root cause or fault hypothesis, and planned verification.
> If the bug cannot be reproduced and no evidence-backed fault hypothesis can be formed, return ESCALATE with the four-field escalation request block defined in the debug skill — do not guess.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the Developer to complete diagnosis before continuing.
If the Developer returns `ESCALATE`, go directly to **On ESCALATE**.
If the Developer does not return a Diagnosis Log handoff entry, stop with `BLOCKED` and report the missing handoff.

Record the Diagnosis Log handoff: append the Developer's entry under `## Diagnosis Log` in the bug file.
Stay on the bug branch — no switch and no commit. That recorded entry is the fix contract for Step 5.

### Step 5: Implementation Cycle

**Spawn the Developer subagent** (tier: standard) with this prompt:

> "Fix the diagnosed bug described in the bug file `<bug-path>`.
> You are on branch `bug/B-NNN-...`.
> Use the recorded Diagnosis Log as the implementation contract.
> The bug file is in the local tracker, outside version control: do not edit it, and never add it to a commit.
> Use the tdd skill where applicable: add or update a failing regression test when the defect can be tested automatically, verify it fails, implement the minimal fix, and verify it passes.
> Commit after each red→green→refactor cycle.
> Return a Work Log handoff entry at session end. The entry's heading is `### Session N — YYYY-MM-DD`; the body is free prose covering what was done, what was tried and rejected, and what remains. The loop will append it to the bug file.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the Developer to complete before continuing.
If the Developer returns `ESCALATE`, go directly to **On ESCALATE**.
If the Developer does not return a Work Log handoff entry, stop with `BLOCKED` and report the missing handoff.

Record the Work Log handoff: append the Developer's entry under `## Work Log` in the bug file. No switch and no commit.

### Step 6: Review Cycle

**Write the review package.** Record the range as `BASE..HEAD` of the bug branch, with `BASE` from the claim in Step 3.
Write one file, `<tracker-path>/review-packages/<id>.md` (find `<tracker-path>` with `ai-team tracker path`), holding the output of:

```bash
git log --oneline BASE..HEAD
git diff --stat BASE..HEAD
git diff -U10 BASE..HEAD
```

Rewrite it before every review cycle so it covers the whole range, including commits from earlier cycles. Delete it when the bug leaves the loop. It lives in the tracker, so it is never committed.

**Spawn the Reviewer subagent** (tier: standard) with this prompt:

> "Review the bug fix described in the bug file `<bug-path>` using the code-review skill.
> The Developer has completed their work on branch `bug/B-NNN-...`.
> The review range and its diff are in the review package `<package-path>`; read that one file instead of deriving the diff yourself.
> Verify the Diagnosis Log records reproduction status, evidence captured, isolated fault, root cause or fault hypothesis, and planned verification.
> Verify the fix addresses the isolated cause and passes the Fix Verification steps in the bug file.
> Verify a regression test exists when practical, or that the Work Log explains why only manual verification was possible.
> Append your verdict to the bug file under `### Review Verdict — YYYY-MM-DD`. The bug file is outside version control: do not commit it.
> Treat the Work Log as unverified claims about the code and check them against the diff. Do not re-run tests the Work Log already shows passing.
> Rate each finding Critical, Important, or Minor as the code-review skill defines. List Minor findings under `#### Deferred Minor findings` and anything you cannot confirm from the diff under `#### ⚠️ Cannot verify from diff`.
> Verdict must be one of: PASS, FAIL, or ESCALATE. On ESCALATE, include the four-field escalation request block defined in the code-review skill.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Wait for the reviewer to complete before continuing.

**Keep the Reviewer prompt neutral.** It names the work item, the branch, and the skill, and nothing else about what to conclude. If the prompt you are writing contains "do not flag", "don't treat X as a defect", "at most Minor", or "the plan chose", stop: you are pre-judging the review, usually to spare yourself a review loop. Put the context the Reviewer needs in the bug file, not in a verdict hint.

### Step 7: Read the Verdict

Read the bug file and find the most recent `### Review Verdict` entry.
Extract the verdict: **PASS**, **FAIL**, or **ESCALATE**.

#### On PASS

If the verdict lists `⚠️ Cannot verify from diff` items, resolve each one before integration, using what the loop knows (other completed work items' Work Logs, the approved spec, the repository). Append the resolution under the verdict. If an item cannot be confirmed, treat the verdict as FAIL for that item and go to **On FAIL**.

Apply the same handling to a deferred Minor finding. If the loop's own checks show that a finding the Reviewer listed under `#### Deferred Minor findings` is a real failure, for example it breaks CI or contradicts the bug's fix contract, treat the verdict as FAIL for that item and go to **On FAIL**. This is the same handling as an unconfirmable `⚠️ Cannot verify from diff` item. When promoting a finding, append ` — resolved: promoted to FAIL` to that entry's line in the verdict's `#### Deferred Minor findings` list, so the Gate 5 roll-up shows it as resolved rather than still deferred.

Before invoking integration, confirm that the bug file holds the Diagnosis Log, the Developer
Work Log, and the Review Verdict recorded in Steps 4, 5, and 6. The `integrate` skill verifies
that the latest verdict in the bug file is PASS before it merges.

1. Invoke the `integrate` skill to merge the reviewed branch into the target branch chosen in Step 3:
   > `/integrate bug/B-NNN-... <target-branch>`

   The integrate skill handles test verification, the merge, regression checks, and branch deletion.
   It reads the bug file for diagnosis and fix-verification context, but bug state changes remain owned by bug-loop.

2. **If integrate succeeds** — run `ai-team bug resolve B-NNN`; there is nothing to commit.
   Then go back to **Step 1** to pick the next bug.

3. **If integrate fails** — stop the loop entirely and report:
   - The failure reason (pre-merge test failure, unmet fix criteria, or post-merge regression).
   - Which bug IDs were filed (if regressions were found).
   - That the bug branch was NOT deleted, the target branch was left clean (integrate reverts on regression), and the bug status is still `in-progress`.
   - Next step for the product owner: resolve the filed regression bugs before re-running the loop.

#### On FAIL

Increment the review cycle counter.

Climb the capability ladder — each rung changes who attempts the fix, so a stuck bug is not retried identically:

- If **cycle = 1**: go back to **Step 5** with the same Developer, who keeps the continuity of the session. The Developer fixes the issues noted in the Review Verdict.
- If **cycle = 2**: go back to **Step 5** with a **fresh Developer subagent on the most capable tier**. Pass only the bug file path: its Work Log and Review Verdicts carry everything the fresh Developer needs, and it does not inherit the failed session's reasoning. This happens before any Architect consultation is spent.
- If **cycle = 3**: treat as ESCALATE (max review cycles exceeded).

#### On ESCALATE

Follow the Phase 2 escalation chain below. Step 1 is a single Architect consultation; Step 2 is product owner escalation. The chain is linear — no second Architect round.

**Phase 2, Step 1 — Architect Consultation:**
**Spawn the Architect subagent** (tier: most capable) with this prompt:

> "Use the escalation-review skill for the bug in `<bug-path>`.
> Problem: <what the reviewer found>
> Attempted: <what the Developer tried, including diagnosis attempts and review cycles>
> Failed because: <why the bug still cannot pass>
> Question: <specific guidance needed to continue within the bug report and approved specification>
> Populate every field of the Output Format block, including `Obstacles Encountered`."

If the Architect resolves the issue, go back to **Step 4** with the Architect's guidance when the escalation was raised during diagnosis, or to **Step 5** otherwise.

If the Architect adjudicates that specific findings of the last FAIL verdict should be **parked** rather than fixed — the bug meets its criteria without them — the loop makes each parked finding a durable artifact before continuing; a ledger line in the chat is not one:
- file it as a new bug with the `new-bug` skill, naming this bug and the finding, or
- record it under a `### Recorded deviation — YYYY-MM-DD` heading in the bug file with the Architect's rationale.

Then spawn the Reviewer again (Step 6). Its prompt stays neutral; the recorded deviation is in the bug file, where the Reviewer reads it. Parked findings never count toward the cycle cap and are never deleted with the workspace.
If the Architect cannot resolve it, proceed to Step 2.

**Phase 2, Step 2 — Product Owner Escalation:**
1. Leave the bug `in-progress` — there is no `blocked` status for bugs. Append a dated `Escalated to the product owner` entry to the bug's Work Log so the escalation is visible in the bug file.
2. Stop the loop entirely.
3. Produce the report using the Phase 2 Product Owner Escalation Report template defined in the `escalation-review` skill. Fill every section (Work item, Original request, Self-recovery attempts, Architect analysis, Why product owner input is required, Decision needed).

### Step 8: Loop Complete

Reporting is on demand. Do not invoke the `status-report` skill and do not write a report file.
The product owner runs `/status-report` when they want the full Gate 5 summary.

1. Run the after-point Workspace Hygiene check and restore any changes this run parked.
2. Return a short run summary in the chat — a few lines, not a report:
   - Bugs resolved and merged this run, with bug IDs and merge commits
   - Bugs escalated and still `in-progress`, with the reason
   - Regression bugs filed this run, and any integration failure that stopped the loop
   - Changes parked or restored, and `.gitignore` patterns added, by the hygiene check
   - The next suggested action — for example `/bug-loop` for filed regressions, or, when the queue is empty, asking the Architect for spec-truth reconciliation and then running `/status-report` for Gate 5 sign-off context

## Cycle Counter Reset

The review cycle counter resets to 0 each time a new bug is picked up in Step 2.
It is local to each bug — one bug failing twice does not affect the counter for the next bug.

## Commit Conventions

All commits follow the `git-conventions` skill.
The loop itself makes no commits: bug state, Diagnosis Log, Work Log, and Review Verdict entries live in the tracker, outside version control.
Implementation commits are made by the Developer on the bug branch, and the merge commit is made by the `integrate` skill.
The orchestrator does not touch implementation or test files.

## Hard Stops (Do Not Continue)

- A bug reaches product owner escalation (Phase 2) — stop the loop, notify the product owner
- A git operation fails (branch already exists, conflict on `{{integration_branch}}`, etc.) — stop and report the git error before attempting anything else
- A bug already has status `in-progress` when the loop starts — stop and ask the product owner whether to resume that bug or treat it as abandoned
- The Developer cannot reproduce the bug and cannot form an evidence-backed fault hypothesis — escalate instead of patching by guesswork

## What This Skill Does NOT Do

- Does not touch `main` — product-owner-only branch
- Does not modify specifications or task files
- Does not fix integration failures — regressions are filed as bugs and the loop stops; fixing is the Developer's job on a subsequent cycle
