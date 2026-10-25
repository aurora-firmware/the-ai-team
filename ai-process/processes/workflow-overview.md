---
title: "AI Team Workflow Overview"
status: approved
created: 2026-03-10
---

# AI Team Workflow Overview

## End-to-End Flow

```
Feature Request (human)          Change Request (human)
    ↓                                      │
┌──────────────────────────┐               │  lighter intake —
│  PLANNER: Brainstorm     │  ← interactive│  no full brainstorm
│  Explore ideas           │   exploration │  or Gate 1 needed
│  Produce design doc      │               │
└─────────┬────────────────┘               │
          ↓                                │
   ★ GATE 1: Spec Approval (human) ★       │
          ↓                                │
┌──────────────────────────┐               │
│  PLANNER: Task Breakdown │◄──────────────┘
│  Atomic tasks            │  ← structured decomposition
│  Dependencies mapped     │
│  Verification defined    │
└─────────┬────────────────┘
          ↓
┌──────────────────────────┐
│  GATE 2: Task Plan       │  ← Architect evaluates
│  Preflight               │
│  Validate decomposition  │
│  Catch conflicts early   │
└─────────┬────────────────┘
          ↓
┌──────────────────────────────────────────────────────┐
│  DEVELOPMENT LOOP (human-invoked, runs autonomously) │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │  SEQUENTIAL EXECUTION (per task)              │   │
│  │                                               │   │
│  │  ┌─────────────┐                              │   │
│  │  │  DEVELOPER  │  ← test-driven development   │   │
│  │  │ (one task)  │                              │   │
│  │  └──────┬──────┘                              │   │
│  │         ↓  (max 2 retries)                    │   │
│  │  ┌─────────────┐  FAIL ──────────────┐        │   │
│  │  │  REVIEWER   │  ← two-stage review │        │   │
│  │  └──────┬──────┘                     │        │   │
│  │         │ PASS                       │        │   │
│  │         ↓                            ↑        │   │
│  │  Integration → merge + test + done   │        │   │
│  │  Repeat for next task ───────────────┘        │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  Stops on: empty queue │ blocked task │ escalation   │
└─────────┬────────────────────────────────────────────┘
          ↓
   ★ GATE 5: Final Merge Sign-off (human) ★
          ↓
       ✓ DONE
```

## Phase Details

### 0. System Overview (S-000)

**Role:** Planner.
**Procedure:** `new-system-overview`.
**Input:** What the project is for and how it divides into components, as described by the human; for an existing project, also its approved specs, accepted ADRs, documentation, and code.
**Output:** The system overview specification, S-000, in `ai-team/specs/`.

For a new project the Planner proposes `new-system-overview` before brainstorming the first feature, so every later spec is written against a shared description of the system.
The step is optional for projects that already have specs; the human may add S-000 at any time.
It is also the entry point for brownfield adoption: a project with existing code uses S-000 to record what the project is for and how it divides, not how it is built today, before new features are specified.

S-000 describes the system as a whole. It produces only the project bootstrap tasks, which cover its development-infrastructure components; solution work comes from feature specs, and S-000 is the reference they are checked against.

S-000's own planning branch does not wait for Gate 2; only its bootstrap task plan does. After Gate 1, the Planner sets S-000 to `approved` and merges its planning branch into `dev-agent` with `--no-ff`.
For a brownfield S-000, the Planner then proposes a change request that brings the existing specs in line with S-000's components, from the overlaps, gaps, and disagreements the draft reported; the human decides which side of each disagreement changes.

### Project bootstrap

**Role:** Planner.
**Procedure:** `spec-breakdown` on S-000.
**Input:** The approved S-000.
**Output:** The bootstrap task plan, which passes Gate 2 and runs through the development loop.

There is no bootstrap spec; the tasks come directly from S-000. They record the answers to every Decisions needed and set up the development environment, the project's coding guidelines, the agent guidance, and the README's project description. In a brownfield project the bootstrap covers only what is missing, and the human may skip items that already exist.
While no baseline test command exists, the development loop runs these tasks after the human confirms that no automated baseline is available.

### 1. Brainstorm

**Role:** Planner (creative mode).
**Procedure:** Interactive brainstorming.
**Input:** Feature request or problem description from a human.
**Output:** Specification document in `ai-team/specs/`, written after the human has confirmed the direction.

This phase is **interactive**. The Planner does not produce a finished document for cold review — it works with the human through a dialogue:

1. Reads the request and checks for ambiguities.
2. Asks focused clarifying questions (batched, about five per round as a recommendation) if material unknowns exist, covering the six internal brainstorm categories. Runs a second round if coverage requires it. Stops and waits for answers.
3. Generates at least two solution alternatives and presents them briefly.
4. Asks the human to pick a direction (or provide the deciding constraint). Stops and waits.
5. Asks follow-up questions on scope or behaviour if the chosen direction still has gaps. One round maximum.
6. Confirms the approach in 2–3 sentences and gets explicit human sign-off before writing.
7. Writes the specification.
8. Resolves any remaining human-answerable `[TODO]` markers one at a time before handing the draft to the Architect for Architecture Consistency Review or to the human for Gate 1 approval.

**Ends when:** Human approves the specification at Gate 1.
Because the human shaped the spec throughout the dialogue, Gate 1 approval should be quick.

**Lighter path — change-request:** For smaller changes that do not warrant a full new spec, the Planner uses a change-request (`CR-NNN-<slug>.md` in the local tracker) instead of the full brainstorm flow. A change-request records desired changes and possible spec amendments, then produces tasks and amendments as needed. The Planner resolves human-answerable `[TODO]` markers one at a time before the human approves the change-request. Once the human approves a TODO-free change-request, that approved artifact becomes the authoritative statement of intended scope for Planner-owned consistency fixes and spec amendments. Larger features still use the full brainstorm, Gate 1 approval, and task breakdown path. The CLI command `ai-team change-request new` creates a change-request document from the bundled template.

New feature specs use the `behavior-v1` template: feature-specific journeys, stable behavioral and quality REQ identifiers, linked AC scenarios and verification, external contracts, and explicit assumptions and open-question handling.
All approved discovery decisions about observable behavior must survive into these requirements before review; task decomposition cannot invent missing product decisions.
The guide `guides/spec-authoring-guide.md` owns this authoring contract, which is embedded in the exported new-spec instructions.
Existing unmarked specs and the S-000 overview keep their formats.

### 2. Task Breakdown + Gate 2

**Role:** Planner (structured mode), then Architect (Gate 2 evaluator).
**Procedure:** Structured task decomposition.
**Input:** Approved specification (or approved change-request).
**Output:** Set of tasks in the local tracker, created as `planned`, validated by the Architect, and set to `pending` once the planning branch merges.

During breakdown the Planner explicitly considers whether the spec changes require documentation updates or test coverage updates. When they do, those updates are planned as implementation tasks or acceptance criteria — not as prerequisites before task creation. If documentation and test updates are not needed, the Planner omits them without creating placeholder tasks.

The Planner also chooses each task's verification mode: a test, or, for a prose-only task, a design review against the source spec, the accepted ADRs, and S-000 when it exists. Each task regenerates the generated files its own change affects and lists them in Files to Touch, so a plan has no trailing "regenerate everything" task.

Before task breakdown starts, the input artifact must be ready for execution: an approved spec must already be free of human-answerable `[TODO]` markers, and an approved change-request must already be TODO-free, human-approved, and reconciled against Architect consistency findings that do not change the approved intent. If a consistency finding would alter the approved change-request's intended scope, the process stops for a human decision instead of letting the Planner reinterpret the request.

After the Planner writes the task files, the Architect automatically reviews the task plan at Gate 2. Gate 2 focuses on technical task-plan readiness — dependencies, file conflict risks, architectural consistency with existing decision records, atomicity, and verifiability. It does not reopen product or spec approval questions already settled at Gate 1.
- Checks dependency correctness and completeness.
- Identifies any two tasks that modify the same file without a declared dependency (merge conflict risk).
- Verifies architectural consistency with existing decision records.
- Returns a correction request to the Planner if problems are found; product-scope concerns that do not block technical readiness are noted as follow-up items, not Gate 2 failures.

Gate 2 is automated and does not require human approval.
When the Architect passes the task plan at Gate 2, the human starts the development loop.

### 3 & 4. Implementation + Code Review

After Gate 2 passes, a human starts the development loop. From that point the loop runs autonomously — no human intervention until the queue is empty, a task is blocked, or escalation is required.

#### Work-item state model

Tasks, bugs, and change-requests live in the local tracker (`ai-team tracker path`), outside version control and outside every branch.
Their lifecycle state is the frontmatter `status` field; no folder or branch encodes it.
Every git worktree of the repository resolves the same tracker, so every role reads the same file from any branch.

1. Developers return Diagnosis Log and Work Log entries to the active loop as part of their handoff.
2. The active loop appends those entries to the task or bug file in the tracker before review starts.
3. Reviewers append Review Verdict entries to the same file.
4. The active loop and the integration procedure read verdicts from that file.

None of these steps creates a commit or needs a branch switch. Task-regression bug branches, based on a preserved task branch, read the bug file from the tracker like every other branch.

#### What the development loop does

Before claiming the first task, the loop discovers the project's documented baseline test command from project-specific guidance and runs it. It starts with root guidance files such as `CLAUDE.md` and `AGENTS.md`, then follows clear references to project-local docs such as `ai-team/docs/coding_guidelines.md`, README files, build configuration, or other documented test instructions. If no automated baseline command is documented, or multiple plausible commands are documented without a clear baseline, the loop asks the human for the command or for explicit confirmation that no automated baseline test is available. If the command fails, the loop stops and reports the failure.

1. Picks the next `pending` task (priority → dependency readiness → creation date), using `ai-team list tasks --state pending`.
2. Sets it to `in-progress` with `ai-team task start` and creates the task branch from `dev-agent`.
3. Assigns the task to the **Developer** for test-driven implementation and debugging — waits for completion and a Work Log handoff.
4. Appends the Developer's Work Log entry to the task file in the tracker.
5. Assigns the completed task to the **Reviewer** for two-stage code review — waits for a recorded verdict.
6. Reads the verdict (`PASS` / `FAIL` / `ESCALATE`) from the task file.
7. On **PASS**: runs the integration procedure to merge the task branch into `dev-agent`, run tests, and set the task to `completed`. Picks the next task.
8. On **FAIL** (cycle 1): sends the task back to the same Developer with the reviewer's feedback. On **FAIL** (cycle 2): sends it to a fresh Developer on the most capable model tier, which reads the task file instead of inheriting the failed session.
9. On **FAIL** (cycle 3) or **ESCALATE**: consults the Architect first. If the Architect cannot resolve it, sets the task to `blocked` with the reason, and stops for human action.

#### Developer details

**Role:** Developer.
**Procedure:** Test-driven implementation and debugging; for a design-review task, a design review of the changed text against the listed references.
**Input:** An `in-progress` task file in the tracker.
**Output:** Working code with passing tests on the task branch (for a design-review task, a recorded design review in the Work Log in place of passing tests), plus a Work Log entry returned to the development loop for the task file.

#### Reviewer details

**Role:** Reviewer.
**Procedure:** Two-stage code review.
**Input:** Completed task with code changes and Developer Work Log entry.
**Output:** Verdict appended to the task file under `### Review Verdict — [date]`.
**Two stages:**
1. Spec compliance — does the code do what the task requires?
2. Code quality — is it clean, secure, and maintainable?

**On review failure:**
1. The task stays `in-progress`.
2. Reviewer appends the verdict and specific, actionable feedback under `### Review Verdict — [date]`.
3. The development loop routes the task back to the Developer for fixes on the same branch.
4. Up to two retries (three total review attempts): the first retry keeps the same Developer, the second uses a fresh Developer on the most capable tier. On a third failure, the development loop escalates to Architect. The Architect may park specific findings, each of which becomes a filed bug or a recorded deviation in the work item file.

#### When the development loop stops

| Condition | Task state | Action required |
|---|---|---|
| Queue empty | All `completed` | Human approves final merge to `main` (Gate 5) |
| Task blocked | Set to `blocked` | Human resolves blocker, restarts the development loop |
| Human escalation | Set to `blocked` after Architect consultation fails | Human adjusts spec or task, restarts the development loop |
| A task already `in-progress` at startup | Unchanged | Human decides whether to resume or abandon |

### 5. Final Merge

Integration happens per-task inside the development loop: after each Reviewer PASS, the integration procedure merges the task branch into `dev-agent`, runs the full test suite, and sets the task to `completed` (Gate 4).
If integration fails because the task branch introduces a regression, the integration procedure reverts the merge, files a bug report that records the preserved task branch as `source_branch`, and leaves `dev-agent` clean.
The development loop stops until the regression bug is fixed on a branch based from that preserved task branch.

Once the queue is empty and all tasks are `completed`, the development loop ends with a short run summary in the chat and does not write a report.
Before Gate 5 the Architect runs spec-truth reconciliation (`architecture-consistency-review` in completion mode, ADR-002) for each approved spec the work touched, then the human runs `/status-report`, which produces the status summary. Reporting is on demand.
The status summary lists the approved specification, completed tasks, unresolved bugs by severity, and latest integration-test result.
The human reviews that status summary and approves the merge to `main` (Gate 5).
This is a sign-off — the human confirms the outcome matches the spec intent, not individual code diffs.

**Ends when:** Human approves the merge from `dev-agent` to `main` (Gate 5).

### Bug-Fix Flow

When the development loop stops because the integration procedure found regressions, bugs are filed automatically as bug reports and the feature branch is preserved.
To fix these regressions, the human starts the bug-fix loop.

From that point the loop runs autonomously — same structure as the development loop but operating on `open` bugs instead of `pending` tasks.
Unlike feature tasks, bug fixes are diagnosis-first.
The Developer must reproduce or otherwise confirm the defect, gather evidence, isolate the fault, and record a root-cause hypothesis before changing production code.

#### Bug intake

Bugs may be filed by humans, Reviewers, Developers, or the integration procedure.
Before a bug report is filed as `open`, the creator must capture enough diagnostic context for the bug-fix loop to start without guessing:

1. State the observable symptom and impact.
2. Record reproduction status: confirmed, intermittent, or not yet reproduced.
3. Include reproduction steps or the exact command/test that failed.
4. Capture relevant logs, stack traces, error output, screenshots, or failing assertions.
5. Record environment details and branch context, including `source_branch` for task-regression bugs.
6. Identify the suspected area if known, or explicitly say "unknown".
7. Define the fix-verification command or manual check.

If the issue cannot be reproduced yet, the bug may still be filed, but the report must say what evidence exists and what diagnostic step should be tried first.

#### What the bug-fix loop does

1. Picks the highest-severity open bug (critical → high → medium → low, oldest first on ties).
2. Sets it to `in-progress` with `ai-team bug start`, creates a bug branch, and chooses the branch base from the bug type:
   - Existing defect on `dev-agent`: create the bug branch from `dev-agent`.
   - Regression introduced by a task branch: create the bug branch from the bug report's non-empty `source_branch`.
3. Assigns the bug to the **Developer** for diagnosis — passes the bug file path and waits for a Diagnosis Log handoff before implementation continues.
4. The Developer reproduces or confirms the defect, gathers logs, isolates the likely fault, and records the root cause or the reason reproduction is impossible.
5. The bug-fix loop appends the Diagnosis Log entry to the bug file in the tracker. That recorded Diagnosis Log entry is the fix contract: the implementation step must address the isolated fault and root cause it records.
6. The Developer fixes the isolated cause with the smallest change that resolves the defect, preferably by first adding or updating a failing regression test.
7. The bug-fix loop appends the Developer's Work Log entry to the bug file.
8. Assigns the completed fix to the **Reviewer** — waits for a verdict recorded in the bug file.
9. On **PASS**: runs the integration procedure to merge the bug branch into its target branch, then sets the bug to `resolved` with `ai-team bug resolve`.
   - Existing-defect bugs target `dev-agent`.
   - Task-regression bugs target the preserved task branch, after which the human restarts the development loop to retry task integration.
10. On **FAIL** (cycle 1): sends the bug back to the same Developer with the reviewer's feedback. On **FAIL** (cycle 2): sends it to a fresh Developer on the most capable model tier.
11. On **FAIL** (cycle 3) or **ESCALATE**: consults the Architect first. If the Architect cannot resolve it, stops and escalates to the human.

#### When to start the bug-fix loop

- After the development loop stops due to integration regressions — fix the filed bugs before restarting the development loop.
- Independently, whenever `open` bugs exist that need autonomous resolution.

The development loop and bug-fix loop do not run concurrently.
The typical cycle after regressions: development loop stops → bugs filed → human starts bug-fix loop → bugs resolved → human restarts development loop.

## Lifecycle State Machines

### Task Lifecycle

| State | Owner | Entry condition | Exit condition |
|---|---|---|---|
| `planned` | Planner | Task is created during spec breakdown, on behalf of a planning branch | The planning branch merges after Gate 2 (`pending`) or its spec or change-request is abandoned (`cancelled`) |
| `pending` | Planner | The planning branch merged after Gate 2, or the task is a follow-up routed by spec-truth reconciliation, which is exempt from Gate 2 (ADR-002) | Development loop selects it |
| `in-progress` | Development loop | Task is claimed and a task branch is created | Reviewer passes, task is blocked, or task is abandoned |
| task branch | Developer | Developer receives assignment | Developer submits for review |
| review pending | Reviewer | Developer reports completion | PASS, FAIL, or ESCALATE verdict |
| integration pending | Integration procedure | Reviewer returns PASS | Integration succeeds or fails |
| `completed` | Integration procedure | Merge and tests pass | Task is included in the Gate 5 status summary |
| `blocked` | Development loop or Escalation procedure | Max retries, escalation, or unresolved blocker | Human or Planner resolves blocker and returns task to `pending` or `in-progress` |
| `cancelled` | Planner | Its spec or change-request was abandoned before work started | — |

The development loop owns task state transitions and records Developer Work Log handoffs in the task file.
The Developer owns source, test, and project artifact changes on the task branch, plus the Work Log content handed to the loop.
The Reviewer owns review verdict content and records verdicts in the task file.
The integration procedure owns merge and post-merge validation.

### Bug Lifecycle

| State | Owner | Entry condition | Exit condition |
|---|---|---|---|
| `open` | Bug creator (human, Reviewer, Developer, or integration procedure) | Regression or defect is filed | Bug-fix loop selects it |
| `in-progress` | Bug-fix loop | Bug branch is created | Reviewer passes, or escalation stops the bug-fix loop |
| diagnosis pending | Developer | Developer receives bug assignment | Defect is reproduced or evidence-backed non-reproduction is documented |
| bug branch | Developer | Root cause or fault hypothesis is recorded | Developer submits fix for review |
| review pending | Reviewer | Developer reports completion | PASS, FAIL, or ESCALATE verdict |
| integration pending | Integration procedure | Reviewer returns PASS | Integration succeeds or fails |
| `resolved` | Bug-fix loop | Fix is merged and tests pass | Bug is included in the Gate 5 status summary |

Bug branch base is part of the bug contract.
Existing-defect bugs use `dev-agent` as both source and target branch.
Task-regression bugs use the preserved task branch as both source and target branch, then the development loop retries the original task integration.
The bug file stays in the tracker even when the bug branch is based on another branch.
The bug-fix loop records Developer Diagnosis Log and Work Log handoffs in that file, and the Reviewer records verdicts there before the loop reads them.

### Gate Lifecycle

| Gate | Controls transition | Evaluator | Output |
|---|---|---|---|
| Gate 1: Specification Approval | Feature request → TODO-free approved spec | Human | Approved specification |
| Gate 2: Task Plan Preflight | Task plan draft (from approved spec **or** approved change-request) → implementation-ready task queue; follow-up tasks from spec-truth reconciliation are exempt (ADR-002) | Architect | Approved task queue or correction request |
| Gate 3: Code Review | Developer-complete task → integration-ready branch | Reviewer | PASS, FAIL, or ESCALATE |
| Gate 4: Integration Tests | Reviewed branch → completed task or bug | Integration procedure | Merged/completed or regression report |
| Gate 5: Final Merge Sign-off | Completed queue → production merge | Human | Approval to merge `dev-agent` to `main` |

Change-requests are a lighter intake path that may bypass Gate 1, but they do not bypass intent completion: the Planner resolves human-answerable `[TODO]` markers before approval, the human approves the TODO-free request, and the Planner then carries forward only those Architect consistency fixes that preserve the approved intent. Approved change-requests then feed into the existing Task Breakdown and Gate 2 flow without adding a new human review gate. Full features still go through Brainstorm, Gate 1, and Task Breakdown.

Each gate's timing, evaluator, pass criteria, and failure handling are defined in `ai-process/processes/quality-gates.md`.

## Git Branching Strategy

Full rules and commit format: `ai-process/guidelines/git-conventions.md`.

**Branches:**
- `main` — human-only, production releases.
- `dev-agent` — integration target. The integration procedure merges task branches here during the development loop; the Integrator handles manual merges and conflict resolution. The Planner merges planning branches here after Gate 2 (S-000: after Gate 1, see the git conventions). Architects commit ADRs raised outside planning here.
- `plan/S-NNN-short-description` or `plan/CR-NNN-short-description` — planning branch for one spec or change-request. It carries the spec, spec amendments, and ADRs raised by its consistency review, and is merged into `dev-agent` only after Gate 2 passes (S-000: after Gate 1, see the git conventions); its tasks stay `planned` in the tracker until then.
- `task/T-NNN-short-description` — implementation branch for a single task, deleted after successful integration.
- `bug/B-NNN-short-description` — implementation branch for a single bug, created by the bug-fix loop from `dev-agent` or the bug report's `source_branch`, deleted after successful integration.

**Key constraints:**
- No automated role ever commits to `main`.
- The Developer never commits to `dev-agent`.
- The integration procedure is the standard path for merging task branches into `dev-agent`. The Integrator handles manual merges and conflict resolution.
- The integration procedure is also the standard path for merging bug branches into their target branch.
- Tasks, bugs, and change-requests live in the local tracker, outside version control; no branch holds lifecycle state and no lifecycle change creates a commit.
- Branches blocked at review stay open on their task branch until the blocker is resolved.
- Spec and change-request work never lands on `dev-agent` before its task plan passes Gate 2. There are two exceptions: a follow-up task routed by spec-truth reconciliation, which the reconciliation re-run checks instead (ADR-002), and S-000, whose own planning branch merges after Gate 1; only its bootstrap task plan goes through Gate 2.
- Every orchestrating procedure applies the Workspace Hygiene check from the git conventions before it starts, before every branch switch, after every merge, and before it ends. No procedure leaves untracked files or uncommitted changes behind.

## Escalation

At any point, if a role cannot complete its work:
1. **Architect consultation** — the Architect reviews the situation and advises (one automatic attempt).
2. **Human escalation** — if the Architect cannot resolve it, the issue is surfaced to a human.

See `ai-process/processes/escalation-procedure.md` for details.

## Quality Gates

Five gates control the workflow (see `ai-process/processes/quality-gates.md` for full criteria):

| Gate | Checkpoint | Evaluator | Phase boundary |
|------|-----------|-----------|----------------|
| 1 | Spec Approval | Human | Brainstorm → Task Breakdown (skipped for change-request intake) |
| 2 | Task Plan Preflight | Architect | Task Breakdown → Development Loop (applies to both spec and change-request derived tasks) |
| 3 | Code Review | Reviewer | Implementation → Integration (per-task, inside the development loop) |
| 4 | Integration Tests | Integration procedure | Review → Completed (per-task, inside the development loop) |
| 5 | Final Merge Sign-off | Human | `dev-agent` → `main` |

Gates 1 and 5 are human touchpoints — design approval and final production sign-off.
Gate 1 is required for full feature specs, and those specs must be TODO-free before Architecture Consistency Review and human approval. Change-requests bypass Gate 1, but they still must become TODO-free and human-approved before Architect consistency work and Task Breakdown continue.
Gate 2 is automated — it catches structural problems in the task plan before implementation starts, not product-intent questions already settled by an approved spec or approved change-request.
Gates 3 and 4 are automated role and procedure checks — they catch defects during execution.
