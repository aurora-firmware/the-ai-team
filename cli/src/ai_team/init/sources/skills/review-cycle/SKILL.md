---
name: review-cycle
description: Shared Developer → Reviewer → Architect → integrate cycle of the development and bug-fix loops, including the review-cycle cap and the resume of an in-progress work item. Use when dev-loop or bug-loop has claimed or resumed a task or bug and drives it through review and integration.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill(integrate), Skill(new-bug), Skill(git-conventions)
user-invocable: false
---

# Review Cycle

`dev-loop` and `bug-loop` run this cycle in process, for one work item at a time.
It ends with one of the outcomes in Step 9, and the loop continues from there.

## Input Requirements

The calling loop provides:

- **Work item:** its ID, its kind (task or bug), and its file `path` from `ai-team show <id> --json`.
- **Branch:** the work item branch (`task/T-NNN-<slug>` or `bug/B-NNN-<slug>`).
- **Target branch:** where `integrate` merges the branch: `{{integration_branch}}` for a task, the base `bug-loop` chose for a bug.
- **BASE:** the last `Base commit: <sha>` line under `## Work Log` in the work item file.
- **Entry point:** Step 1 (resume), Step 2 (after a claim or a diagnosis), or Step 7 (a diagnosis escalation from `bug-loop`).
- **Loop name:** `Development Loop` or `Bug-Fix Loop`, the Next Owner value the roles return to.

Work item files live in the local tracker, outside version control.
The loop writes Base commits, Work Log and Diagnosis Log entries, finding rulings and deviations into them with Write or Edit; none of these needs a commit or a branch switch.

## Run-wide Rules

These rules hold for the whole loop run, from its startup to its run summary.

### Workspace Hygiene

Apply the Workspace Hygiene check of the `git-conventions` skill:

- **At startup**, on the branch the loop starts from.
- **Before every branch switch.** A checkout refused because of a dirty tree is not a stop: run the check, then retry the checkout once.
- **After every `integrate` invocation**, whether it succeeded or stopped.
- **Before the loop ends**, including before reporting any stop.

Changes parked by this run are restored when the loop ends, on the branch where they were parked.
A run never ends with untracked files or uncommitted changes that the run itself created.

### Dispatch Discipline

Each subagent starts cold, and the loop's context is the scarce resource:

- **Name the model tier at every spawn**, from the table below; it overrides the agent definition's default for that dispatch.
- **Never paste history into a dispatch.** Pass the work item file path; the subagent reads what it needs from the file.
- **Pass the diff as a review package**, never through the loop's context (Step 3).

| Tier | Agent `model` | Use for |
|---|---|---|
| cheap | `haiku` | Mechanical, fully specified tasks: a rename, a config change, a transcription from the spec |
| standard | `sonnet` | The default for the Developer and the Reviewer |
| most capable | `opus` | The Architect, the Planner, and the fresh Developer of the retry ladder |

### Reading a Role's Result

Every spawned role returns the report `role-report` defines.
Read its `Result` and `Next Owner`:

- `Result: ESCALATE` or `BLOCKED`, or `Next Owner: Architect` or `Product Owner`: go to Step 7, passing on the escalation block the role appended. For a `BLOCKED` result without one, write the four fields yourself, naming the missing input.
- Exception: a Developer `BLOCKED` because a bug's fix contract is missing or incomplete goes back to diagnosis: return `DIAGNOSE`.
- `Next Owner:` the loop name: continue with the current step.

## Procedure

### Step 1: Resume an In-Progress Item

The loop resumes an `in-progress` item without asking the product owner.

1. Find the branch with `git branch --list '<kind>/<ID>-*'` and BASE in the Work Log. If either is missing, return `STOPPED`, naming what is missing.
2. Check out the branch (Workspace Hygiene first).
3. When an Amendment Log row of the item's approved spec names this item and the work item file does not cite it yet (a product owner's "Revise the spec" decision), add `### Spec amendment — YYYY-MM-DD` under `## Work Log`, citing the row, and re-enter at Step 2.
4. Otherwise choose where to re-enter, from the work item file:
   - A bug with no `### Diagnosis` entry: return `DIAGNOSE`.
   - More `### Session` and `### Architect guidance — … (re-review)` entries under `## Work Log` than `### Review Verdict` entries: Step 3.
   - The latest Review Verdict is PASS with a `⚠️ Cannot verify from diff` item that has no resolution under it: Step 4.
   - The latest Review Verdict is PASS and none of its findings is `Open`: Step 6.
   - Otherwise: Step 2. The Developer answers the open findings and applies any guidance or amendment recorded since the latest verdict.

### Step 2: Implementation

**Spawn the Developer subagent** (tier: standard; cheap for a mechanical task; most capable on the fresh-Developer rung of Step 5) with this prompt:

> "Implement the <task | bug> in the <task | bug> file `<path>` with the tdd skill. For a bug, the latest Diagnosis Log entry is the fix contract.
> You are on branch `<branch>`; commit there.
> The <task | bug> file is in the local tracker, outside version control: do not edit it, and never add it to a commit.
> If its latest Review Verdict lists Open findings, first answer every one with the receive-code-review skill. Apply any Architect or product owner guidance, and any spec or task amendment, recorded in the file since that verdict.
> Return the Work Log handoff entry tdd Step 9 defines; the loop appends it to the file.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Read the result (Reading a Role's Result).
If it has no Work Log handoff entry, return `STOPPED` and report the missing handoff.
Append the entry under `## Work Log` in the work item file, then go to Step 3.

### Step 3: Review

**Write the review package**: `<tracker-path>/review-packages/<id>.md` (find `<tracker-path>` with `ai-team tracker path`), holding the output of:

```bash
git log --oneline BASE..HEAD
git diff --stat BASE..HEAD
git diff -U10 BASE..HEAD
```

From the second review on, also add `git diff -U10 LAST..HEAD`, where `LAST` is the `Reviewed through:` commit of the latest Review Verdict.
Rewrite the package before every review so it covers the whole range. It lives in the tracker and is never committed.

**Spawn the Reviewer subagent** (tier: standard) with this prompt:

> "Review the <task | bug> in the <task | bug> file `<path>` with the code-review skill.
> The Developer's work is on branch `<branch>`. The review range and its diff are in the review package `<package-path>`; read that file instead of deriving the diff.
> Append your verdict to the file's `## Review` section under `### Review Verdict — YYYY-MM-DD`. The file is outside version control: do not commit it.
> Verdict: PASS, FAIL, or ESCALATE.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

Keep the prompt neutral: it names the work item, the branch, the package and the skill, nothing about what to conclude.
If it contains "do not flag", "don't treat X as a defect", "at most Minor" or "the plan chose", you are pre-judging the review: delete it, and put the context the Reviewer needs in the work item file.

### Step 4: Read the Verdict

Read the most recent `### Review Verdict` in the work item file.

- **ESCALATE:** go to Step 7 with the Reviewer's escalation block.
- **FAIL:** go to Step 5.
- **PASS:** resolve each `⚠️ Cannot verify from diff` item from what the loop knows (other work items' Work Logs, the approved spec, the repository), and append the resolution under the verdict. If an item cannot be confirmed, add it under the verdict as a new finding in the code-review format, with the next unused finding ID and `**Status:** Open`, and go to Step 5. Otherwise go to Step 6.

### Step 5: Retry Ladder

The review-cycle cap is three review attempts per work item.
Count each failed attempt (a FAIL verdict, or a PASS turned into a failure in Step 4 or Step 6):

- **First failure:** Step 2 with the same Developer subagent, which keeps its session.
- **Second failure:** Step 2 with a fresh Developer subagent on the most capable tier and the Step 2 prompt unchanged. It reads the work item file and inherits nothing from the failed session.
- **Third failure:** the cap is reached. Go to Step 7 with an escalation block written by the loop (Attempted: three review attempts and what each Developer changed).

### Step 6: Integration

Confirm that the work item file holds the Developer's Work Log entry, the PASS verdict, and for a bug its Diagnosis Log entry.
Run `ai-team list bugs --json`; when any bug whose `source_branch` is this branch is not `resolved`, return `WAITING` with their IDs.
Invoke the `integrate` skill with `<branch> <target-branch>`.
It resolves merge conflicts in process with `merge-conflicts`; a conflict reaches this cycle only as `ESCALATE`.
Run the after-point Workspace Hygiene check, then act on its `Result`:

| Result | Action |
|---|---|
| `PASS` | A task is already `completed`. For a bug, run `ai-team bug resolve <id>`. Return `DONE` |
| `FAIL`, nothing merged (a gap in the diff, lifecycle files in the diff, or a failing source-branch command) | Add integrate's failure under the latest verdict as a new `Open` finding, as in Step 4, and go to Step 5 |
| `FAIL`, merge reverted on a regression | The item stays `in-progress` with its branch preserved. Return `REGRESSION` with the filed bug IDs |
| `BLOCKED` or `ESCALATE` | Go to Step 7 with integrate's escalation block, or, for `BLOCKED` without one, four fields naming what is missing |

### Step 7: Architect Consultation

A work item gets one Architect consultation per loop run.
When it already had one, the Architect is spawned only to hand the item to the product owner: add to the prompt "This item already had an Architect consultation in this run and is still blocked: escalate to the product owner."

**Spawn the Architect subagent** (tier: most capable) with this prompt:

> "Use the escalation-review skill for the <task | bug> in `<path>`.
> Approved spec: `<the spec the task's Source Requirements cite, or the bug's Related section names; or none>`.
> <the escalation block, unchanged>
> Rule on every finding still Open in the latest Review Verdict: <finding IDs, or none>.
> Populate every field of the Output Format block, including `Obstacles Encountered`."

The escalation block is the one the Developer, the Reviewer or `integrate` returned, or the one the loop wrote, in the format `escalation-review` owns.

**On `Result: PASS`** (Next Owner: the loop):

1. Append the Architect's directive to the Work Log as `### Architect guidance — YYYY-MM-DD`, adding ` (re-review)` to the heading when step 5 continues at Step 3.
2. Record each entry of its `Finding rulings` under the latest Review Verdict. An upheld finding stays `Open`.
3. Make each **parked** finding durable before going on, never just a line in the chat: file it with the `new-bug` skill, naming this work item and the finding (pass `task` only when the work item is a task; for a bug, name the bug in the new bug's Summary and Related section and pass no `task`), or record it under `### Recorded deviation — YYYY-MM-DD` in the work item file with the Architect's rationale. Parked findings never count toward the cap.
4. When the Classification is `work-item`, the Architect has blocked the item. **Spawn the Planner subagent** (tier: most capable) with this prompt:

   > "The Architect blocked the <task | bug> in `<path>` with a `work-item` ruling: its latest `### Architect guidance` entry names the amendment. Amend the file as it requires, and anything else the item needs to continue, and note the change under `## Work Log` as `### Task amendment — YYYY-MM-DD`.
   > If the item can continue, run `ai-team <task | bug> unblock <id>` and return Next Owner: <loop name>. Otherwise leave it blocked and return `Result: ESCALATE`, Next Owner: Product Owner, with the escalation block.
   > Populate every field of the Output Format block, including `Obstacles Encountered`."

   When the Planner unblocked the item, return `DIAGNOSE` from a diagnosis escalation, otherwise go to Step 2. When it did not, return `ESCALATED` with the Planner's escalation block; the item stays `blocked`.
5. Continue:
   - from a diagnosis escalation: return `DIAGNOSE`;
   - when a finding is upheld or the directive asks for changes on the branch: Step 2;
   - when the directive only settles an integration question: Step 6;
   - otherwise (findings only parked or dismissed): Step 3.

**On `Result: ESCALATE`:** go to Step 8.

**On `Result: BLOCKED`** (the request or the work item is missing): supply what it names and spawn it once more; if it is still `BLOCKED`, return `STOPPED`.

### Step 8: Product Owner Escalation

1. Block the item: `ai-team task block <id> --reason "<one-line reason>"`, or `ai-team bug block <id> --reason "<one-line reason>"`. The reason lands in the Work Log; there is nothing to commit.
2. Return `ESCALATED` with the Phase 2 Product Owner Escalation Report the Architect wrote, passed on unchanged.

The item stays `blocked` until the product owner has decided and runs `ai-team task unblock` or `ai-team bug unblock`; the next loop run then resumes it (Step 1).
An item the product owner defers stays `blocked`.

### Step 9: Return to the Loop

Delete the review package unless the outcome is `DIAGNOSE`, and hand the loop one outcome:

| Outcome | Work item | Loop |
|---|---|---|
| `DONE` | Merged; task `completed` or bug `resolved`; branch deleted | Picks the next item |
| `DIAGNOSE` | Bug, `in-progress` | Runs its diagnosis step, then Step 2 |
| `WAITING` | `in-progress`; bugs on its branch are unresolved | Skips the item this run |
| `REGRESSION` | `in-progress`; merge reverted, branch preserved, regression bugs filed | Stops |
| `ESCALATED` | `blocked` | Stops with the Phase 2 report, or the Planner's escalation block |
| `STOPPED` | Unchanged | Stops and reports the cause |

Return `STOPPED` also when a git operation fails, other than a checkout refused on a dirty tree (Workspace Hygiene) or a merge conflict (`integrate`): report the git error before attempting anything else.

## Cycle Counter Reset

The failure count of Step 5 and the Architect consultation of Step 7 belong to one work item in one loop run.
Both start at zero when the loop claims or resumes the item, and never carry over to the next item.
