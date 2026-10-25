---
title: "Quality Gates"
status: approved
created: 2026-03-10
---

# Quality Gates

Gates are checkpoints where work must meet defined criteria before proceeding. They prevent defects from propagating downstream where they become more expensive to fix.

## Gate 1: Specification Approval

**When:** After the Planner produces a design document from interactive brainstorming and resolves any human-answerable `[TODO]` markers.
**Evaluator:** Human.
**Pass criteria:**
- The problem is clearly defined.
- The proposed solution addresses the stated problem.
- Architecture is described with enough detail to derive tasks.
- Exclusions are explicitly stated.
- No unresolved open questions.
- No remaining human-answerable `[TODO]` markers.

**S-000 pass criteria:** for S-000 (the system overview), these replace the criterion that the architecture is detailed enough to derive tasks:
- The content is in plain language.
- There is no technology or interfaces.
- Every use case is tied to a pain point.
- Every component has a boundary and a responsibility.
- Components are placed in the solution and development-infrastructure groups.
- Every development-infrastructure component has a Decisions needed field.
- There is no unresolved `[TODO]`.

**On failure:** Return to Planner with feedback for revision.

For newly generated feature specs marked `spec-format: behavior-v1`, Gate 1 also requires stable REQ identifiers, one obligation per requirement, linked AC scenarios and verification methods, explicit confirmed assumptions, sufficient external contracts, and no unresolved behavior or feasibility questions.
The author runs `ai-team validate --specs` on the review-ready document and also checks completeness and feasibility semantically; structural validation is not approval.
Existing specs without the marker retain their authoring contract and are not rewritten solely to adopt it; S-000 retains its own overview criteria.

## Gate 2: Task Plan Preflight

**When:** After the Planner writes the task plan from either an approved specification or an approved change-request, before the development loop starts. Follow-up tasks routed by spec-truth reconciliation are exempt: they are created `pending`, and the reconciliation re-run checks them (ADR-002).
**Evaluator:** Architect.
**Scope:** Gate 2 focuses on **technical task-plan readiness**. The Architect evaluates dependencies, file conflicts, architectural consistency with existing decisions, atomicity, and verifiability. Gate 2 does not reopen product or spec approval questions that were already settled at Gate 1 or by human approval of a TODO-free change-request. If the Architect finds a product-scope concern that does not block technical readiness, it is noted as follow-up feedback rather than a Gate 2 failure. Only a contradiction against the approved spec, the approved change-request intent, or existing ADRs causes a Gate 2 failure or escalation. The same consistency principle applies whenever a spec, ADR, or change-request itself changes — see [Architecture Consistency Review](#architecture-consistency-review) below.
**Pass criteria:**
- Task plan covers every requirement in the approved specification (spec-coverage verification). For S-000, coverage means the bootstrap scope only: every development-infrastructure component and every Decisions needed question has a task, or the human recorded it as skipped (brownfield). S-000's solution components never need tasks.
- Task dependencies are correct and complete.
- File conflict risks are identified and resolved through dependencies or task changes.
- Interfaces are consistent across tasks: every type, function, or file a task consumes is produced by a task it depends on (or already exists), under the same name and signature.
- Task plan is architecturally consistent with existing decisions.
- Tasks are atomic, independently verifiable, and ready for implementation. Verification is a test or, for a task that changes only prose, a named design review that lists its references (the source spec, accepted ADRs, and S-000 when it exists); a task that changes behaviour a test can observe has a test.
- No task contains placeholder text (`TBD`, `TODO`, "implement later", "add appropriate error handling", "similar to Task N", or a reference to something no task defines).

**On failure:** Architect returns a correction request to the Planner. The Planner revises the task plan and resubmits it to Gate 2. The one exception: the Architect may fix an obvious missing dependency, file ordering, or naming mismatch directly in the planned task files, as the `spec-breakdown-review` skill allows.

## Architecture Consistency Review

**When:** Whenever a specification, an ADR, or a change-request is created, accepted, amended, or superseded — at ADR authoring time (`new-adr`), after a draft spec is made TODO-free and before Gate 1 approval, after an amended spec is made TODO-free and before Architect consistency review continues, and after a change-request becomes TODO-free and gains human approval. This is a standing duty, not a numbered gate. It also runs on **completion**: after the task queue drains and before Gate 5 sign-off, the Architect re-reads each approved spec the work touched against the completed Work Logs, the ADRs created mid-flight, and the deferred-Minor roll-up, then confirms the spec is still true or routes corrections to the Planner: an amendment when the spec is stale, or follow-up tasks when the spec is right and the work falls short (ADR-002). The completion review does not include S-000: its bootstrap tasks answer questions S-000 only asks, so S-000 makes no assertion for that work to drift from.
**Evaluator:** Architect.
**Executable procedure:** the `architecture-consistency-review` skill, exported by `ai-team init`, owns the actual check, finding routing, and escalation behaviour. This section is the spec-layer description of *why* and *when* the duty runs; the skill is *how* it runs. The Architect runs it directly when authoring an ADR; for a created or amended spec or an approved change-request, the Planner-owned procedure hands the changed artifact to the Architect (Next Owner: Architect), who runs the review and returns findings — the same Planner↔Architect handoff pattern as Gate 2.
**Why:** Approved specs and accepted ADRs are both binding sources of truth (see Gate 2). A new or changed decision can silently contradict something an existing spec or ADR already records, leaving two authoritative artifacts that disagree until someone notices by hand.
**Check:** The Architect reads the changed artifact against every other approved spec and accepted ADR and confirms they remain mutually consistent. For draft specs and amended specs, this check only starts once human-answerable `[TODO]` markers are resolved; for change-requests, it starts only after the human has approved a TODO-free request. Gate 2's `spec-breakdown-review` makes the equivalent consistency check on a *task plan* independently; this review covers the *artifact change itself*, regardless of whether any task plan is in flight. The two reviews are separate skills with separate inputs.
**On drift:** The Architect names every affected artifact and routes the correction — the Planner amends affected specs (recording the change, and the driving ADR ID, in the Amendment Log), and the Architect amends or supersedes affected ADRs. In completion mode, when the spec is right and the completed work falls short, the Planner creates follow-up tasks instead of amending the spec. When the changed artifact is an approved change-request, the Planner treats that approved TODO-free request as authoritative for Planner-owned consistency fixes. If an Architect finding would alter the approved change-request's intent, the process stops for a human decision instead of applying the change procedurally. When reconciling the drift requires changing an approved specification beyond an in-flight amendment, the Architect escalates to the human per the [escalation procedure](escalation-procedure.md).

## Gate 3: Code Review

**When:** After a Developer completes a task or bug fix.
**Evaluator:** Reviewer role (two stages).
**Output:** Review Verdict entry recorded in the task or bug file in the local tracker.

### Stage 1: Spec Compliance
**Pass criteria:**
- All acceptance criteria from the task are met.
- No functionality is missing.
- No unspecified behavior was added.

### Stage 2: Code Quality
**Pass criteria:**
- Code follows the coding standards: `ai-process/guidelines/coding-standards.md` (general) and `ai-team/docs/coding_guidelines.md` (project-specific tech-stack rules, if present).
- Relevant tests exist for the changed behavior.
- The Developer's Work Log records local test evidence or explains why a local test run was not possible.
- For a design-review task, the Work Log records the design review — documents checked, each conflict found and fixed, and the result — in place of test evidence, and the Reviewer checks the planning choice.
- No security vulnerabilities introduced.
- No performance regressions.
- Code is readable and maintainable.

### Bug Fix Criteria
For bug fixes, the Reviewer also verifies:
- The complete diagnosis→fix evidence chain is present: the recorded Diagnosis Log entry (the fix contract) records reproduction status, captured evidence, isolated fault, root cause or fault hypothesis, and planned verification; the fix addresses that isolated cause; and the Fix Verification steps from the bug report confirm the defect is resolved.
- The Diagnosis Log records reproduction status, captured evidence, isolated fault, root cause or fault hypothesis, and planned verification.
- The fix targets the isolated cause rather than masking the symptom downstream.
- A regression test exists when the defect can be tested automatically, or the Work Log explains why only manual verification is possible.
- The Fix Verification steps from the bug report were run or a clear reason is recorded.

**On failure:** The Reviewer records specific feedback in the work item file. The active loop returns the work item to the Developer for another implementation cycle. After the third failed review or any `ESCALATE` verdict, the active loop consults the Architect before stopping for human action.

## Gate 4: Integration Tests

**When:** After each task or bug fix passes code review (Gate 3), during integration by the active loop.
**Evaluator:** Automated test suite, run by the integration procedure.
**Pass criteria:**
- The latest PASS verdict recorded in the work item file confirms the branch passed Gate 3 before the merge is attempted.
- All unit tests pass on the source branch (pre-merge).
- All unit and integration tests pass on the destination branch after the merge (regression check).
- No unresolved merge conflicts remain.

**On failure:** The integration procedure reverts the merge commit, files a bug report in the tracker for each regression, and stops the active loop. The source branch is preserved for fixing.
Regression bug reports must record the preserved source branch as `source_branch` so the bug-fix loop can branch from and merge back into that branch before integration is retried.

## Development Loop Baseline Guard

Before the development loop claims its first task it discovers the documented baseline test command from project-specific guidance. It starts with root guidance files such as `CLAUDE.md` and `AGENTS.md`, then follows clear references to project-local docs, README files, build configuration, or other documented test instructions. If no automated baseline command is documented, or the available guidance is ambiguous, the loop asks the human for the intended command or for explicit confirmation that no automated baseline test is available. If a command is present but fails, the loop stops and reports the output. This is an operational startup check, not a numbered quality gate — it is distinct from Gate 4 (integration test suite), which runs after each task merge.

## Gate 5: Final Merge Sign-off

**When:** After the task queue is empty and all tasks are `completed`.
**Evaluator:** Human.
**Input:** The status summary the human requests on demand with `/status-report`. The loops do not produce it automatically.
**Pass criteria:**
- Integration tests are green.
- No open bugs with severity `critical` or `high`.
- The status summary matches the approved specification.
- The latest spec-truth reconciliation returned `PASS`, or every correction it routed is done: each spec amendment applied, and each follow-up task completed with a re-run that returns `PASS` (see [Architecture Consistency Review](#architecture-consistency-review)).
- The status summary lists completed tasks, unresolved bugs by severity, and latest integration-test result.

**Before sign-off:** The Architect runs spec-truth reconciliation (ADR-002) — `architecture-consistency-review` in completion mode — for every approved spec the completed work touched. This completion review does not include S-000: its bootstrap tasks answer questions S-000 only asks, so S-000 makes no assertion for that work to drift from (see [Architecture Consistency Review](#architecture-consistency-review)). The Architect returns each completion-mode verdict as a dated Amendment Log row, which the Planner records in the reconciled spec's Amendment Log (or in the change-request file for change-request work), as defined in the `architecture-consistency-review` skill.

**On failure:** Human provides feedback. New tasks are created to address issues.

> This is a sign-off, not a code review. The human reviews the status summary and confirms the outcome matches the spec intent — not individual diffs. Detailed code quality was already verified at Gates 3 and 4.
