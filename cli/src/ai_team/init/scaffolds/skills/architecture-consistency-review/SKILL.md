---
name: architecture-consistency-review
description: Check that a created or changed architecture artifact stays consistent with every approved spec and accepted ADR. Use when an ADR is created or accepted, a spec is created or amended, or a change-request proposes a spec amendment.
allowed-tools: Read, Grep, Glob, Write, Edit, Skill(new-adr)
effort: high
---

# Architecture Consistency Review

**Ownership boundary:** this skill owns the consistency check for a *created or changed architecture artifact* — an ADR, spec, or change-request — confirming it stays consistent with every approved spec and accepted ADR. It does **not** review task plans: Gate 2's `spec-breakdown-review` independently checks task-plan consistency and readiness. The two reviews are separate skills with separate inputs — a changed artifact here, a task plan there.

Approved specs and accepted ADRs are both binding sources of truth. A new or changed decision can silently contradict something an existing spec or ADR already records, leaving two authoritative artifacts that disagree until someone notices by hand. This review catches that drift at the moment of change.

The result is a Findings block, which the Architect role envelope wraps (see Output Format).

## When This Runs

Whenever an architecture artifact changes:

- **New or accepted ADR** — after `new-adr` records the decision (run by the Architect).
- **New or amended spec** — after a spec is created (`new-spec`, before Gate 1 sign-off settles) or amended (an Amendment Log entry added during spec revision or change-request intake).
- **Completed work (spec-truth reconciliation, ADR-002)** — after the task queue drains and before the product owner gives Gate 5 sign-off. Here the trigger is completion, not a changed artifact; see **Completion Mode** below.
- **Change-request** — after the product owner approves a TODO-free change-request and before the proposed spec amendments are applied. The approved change-request is the authoritative intent for any Planner-owned consistency fixes.

## Completion Mode

In completion mode the review confirms that each approved spec is still true of what was built. It uses the same binding set, findings block, routing rules, and verdicts as every other trigger, with these differences:

- **Changed artifact** — each approved spec touched by the completed work, named by the caller. Do not review specs the work did not touch.
- **Evidence read in place of a delta** — the Work Logs of the completed tasks and resolved bugs that implemented the spec, and every ADR created or amended while the work was in flight.
- **Step 1** isolates what the spec asserts (requirements, interfaces, guarantees) instead of what changed.
- **Step 3** checks each assertion against the evidence: a requirement the work did not deliver, behavior the work added that the spec does not describe, or an interface that now differs. Record each drift with the spec statement and the evidence that contradicts it.
- **Routing** first decides, for each drift, which side is authoritative: the spec or the completed work.
  - **The spec is stale** (the work is right) → the Planner amends the approved spec on a planning branch and records the change in its Amendment Log.
  - **The work falls short** (the spec is right) → the Planner creates follow-up tasks with `new-task` under the same spec or change-request. Each task names the finding and the spec statement it must satisfy. The Planner chooses each follow-up task's verification method by the `new-task` rule for choosing the method (a test, an inspection, or a demonstration) and fills every section without placeholder text, as `new-task` requires. Follow-up tasks are created `pending` and are exempt from Gate 2: their scope is fixed by the finding and the approved spec. After the development loop completes them, the Architect re-runs completion mode for that spec. If the re-run still finds drift on a finding that already had follow-up tasks, escalate to the product owner instead of routing another round. Never amend a spec to match work that fell short.
  - **The authoritative side is unclear**, or both sides need to change → escalate to the product owner.
  - The Architect amends or supersedes ADRs, as for any other trigger.
- **Record** — the verdict is recorded durably as one Amendment Log row in the reconciled spec, `| YYYY-MM-DD | spec-truth reconciliation — PASS or FAIL | <one-line summary> | none |`, or as the same line in the change-request file for change-request work. A reconciliation row changes no scope and does not bump `version`. The Architect returns the line as `Reconciliation record:`; the Planner records it, since the Architect never edits specs.

S-000 is never a touched spec in completion mode: its bootstrap tasks answer questions S-000 only asks, so S-000 makes no assertion for that work to drift from.

A `PASS` means every touched spec is still true. Gate 5 accepts a `PASS`, or a `FAIL` whose routed corrections are all done: every spec amendment applied, and every follow-up task completed with a re-run that returns `PASS`.

## Input Requirements

- **Changed artifact** — the ADR, spec, or change-request just created or amended, and which kind it is; in completion mode, the approved specs the completed work touched. If it was not provided, return `BLOCKED`.
- **Decision records** — all ADRs in `{{project_dir}}/decisions/`; treat `accepted` ones as binding.
- **Specifications** — all specs in `{{project_dir}}/specs/`; treat `approved` ones as binding.
- **Change scope** — for an amendment or change-request, the specific decision, section, or requirement that changed.

## Procedure

### Step 1: Isolate What Changed

Identify exactly what decision, requirement, or contract the changed artifact now asserts. For an amendment or change-request, isolate the delta — not the whole document.

For an approved change-request, treat the approved change-request itself as the authoritative intent. The review checks the binding set against that approved intent; it does not reinterpret the requested change through downstream draft wording.

### Step 2: Read the Binding Set

Read every accepted ADR in `{{project_dir}}/decisions/` and every approved spec in `{{project_dir}}/specs/`. These are the artifacts the change must not contradict.

### Step 3: Check for Contradiction

For each binding artifact, decide whether the changed artifact contradicts it — asserts a different decision for the same concern, removes a guarantee another artifact relies on, or restates a rule with different content. Record each contradiction with the specific artifact, the conflicting statements, and which one is now intended to be authoritative.

For a feature spec, also assess its own requirement completeness, consistent terminology, feasibility, mutually compatible constraints, assumptions, and acceptance coverage; a lack of conflicts with other documents alone does not establish readiness.
Check that unresolved behavioral or feasibility questions have been resolved, and that public contract references are precise.
Use the new-spec authoring contract for feature specifications; S-000 follows its system-overview contract.

### Step 3b: Check Against S-000

When an approved S-000 exists, also confirm that a new or changed spec stays within S-000's purpose and respects each component's boundary and responsibility. Report a violation as drift and route it as Step 4 says. When a spec needs something S-000 does not cover, report it as either an S-000 amendment or a spec cut back to scope, naming which.

When the changed artifact is S-000 itself, review it for internal consistency and plain-language content instead of checking it against other specs. Also check that its components sit in the Solution and Development infrastructure groups, that every infrastructure component has its Decisions needed, and that every component passes the three component checks (it serves a use case or, in the infrastructure group, affects the solution's use, delivery or deployment; one spec could own its contract; its boundary would hold if the implementation were reorganised).

### Step 4: Report Findings and Route Corrections

This review **reports** contradictions as findings to the owning role — it does not edit specs or apply amendments itself. This is the same model as `spec-breakdown-review`, which returns findings to the Planner for revision. Route each contradiction by which artifact is the wrong side:

- **The changed artifact is a pre-Gate-1 draft spec** → return the findings to the Planner, who revises the draft directly. Do **not** add an Amendment Log entry — a draft's Amendment Log stays empty until Gate 1 approval. The Architect and Planner iterate until the draft is consistent; the product owner then approves at Gate 1 as usual.
- **An approved spec is the affected side** → return the findings to the Planner, who amends the approved spec in place — on the planning branch of the spec or change-request under review, never directly on `{{integration_branch}}` — and records the change in its Amendment Log, naming the driving ADR ID when an ADR caused the change. For findings raised from an approved change-request, the Planner uses the approved change-request as the authoritative intent while applying those consistency fixes.
- **An ADR is the affected side** → the Architect amends or supersedes the ADR; use `new-adr` to record a superseding decision.
- **A finding can be resolved procedurally without changing the approved change-request intent** → route the correction to the owning role and continue; Planner-owned amendments stay anchored to the approved change-request.
- **A finding would change the approved change-request intent** → stop and ask the product owner to revise, reject, or reaffirm the CR before any downstream artifact is amended.
- **Reconciling the drift requires changing an approved spec beyond an in-flight amendment** → escalate to the product owner through the Planner per the escalation procedure. In completion mode, amending a stale spec to match the completed work is the routed Planner amendment above, not an escalation.

The Architect reports findings and routing; the Architect never edits specs directly. Draft revision and approved-spec amendment are both the Planner's.

### Step 5: Produce the Verdict

- No contradiction or feature-readiness gap → `PASS`: the change is consistent with the binding set.
- Contradictions or feature-readiness gaps with a clear owner and routing → `FAIL` with the named corrections.
- A contradiction that requires changing an approved spec beyond an in-flight amendment → `ESCALATE`. A completion-mode amendment of a stale spec is a `FAIL` routed to the Planner.
- A contradiction that would change approved change-request intent → `ESCALATE` to the product owner so the CR can be revised, rejected, or reaffirmed.
- In completion mode, a drift where it is unclear whether the spec or the completed work is authoritative, where both need to change, or that a re-run still finds after its follow-up tasks completed → `ESCALATE` to the product owner to decide.

## Output Format

The verdict goes in the Architect envelope's `Result: PASS | FAIL | BLOCKED | ESCALATE` line, not in the Findings block.

```text
Artifact reviewed: <path of the changed ADR / spec / change-request>
Binding set checked: <count> accepted ADRs, <count> approved specs

Findings:
- <artifact>: <the contradiction and which statement is authoritative>

Corrections routed:
- <artifact>: <Planner draft revision | Planner approved-spec amendment | Planner follow-up task | Architect ADR amendment/supersede | escalation>

Next owner:
- Planner | Architect | Product Owner | none

Reconciliation record:
- <completion mode only: the Amendment Log row or change-request line>
```

`BLOCKED` is returned when the changed artifact was not provided. When `Result` is `ESCALATE`, append an Escalation Request block and then a Phase 2 Product Owner Escalation Report using the template defined in the `escalation-review` skill.

## Quality Criteria

- Every accepted ADR and approved spec was read before the verdict.
- Each contradiction names the exact conflicting statements, not a vague "may conflict."
- Corrections are routed to the owning role (Planner for specs, Architect for ADRs); the Architect never edits specs directly.
- In completion mode, each drift states whether the spec or the completed work is authoritative before it is routed.
- An approved change-request remains the authoritative intent for Planner-owned consistency fixes until the product owner changes that intent.
- Escalation is used only when reconciling the drift requires changing an approved specification beyond an in-flight amendment (a completion-mode amendment of a stale spec is a routed `FAIL`), would change approved change-request intent, or, in completion mode, needs the product owner to decide which side is authoritative or persists after its follow-up tasks.

## Common Pitfalls

- **Skipping the evidence in completion mode.** A spec cannot be confirmed from the spec alone; read the Work Logs and mid-flight ADRs.
- **Reviewing the whole artifact instead of the change.** For an amendment, check the delta against the binding set, not every line.
- **Editing a spec to fix drift.** Specs are the Planner's; route the amendment, do not write it.
- **Amending a spec to match work that fell short.** When the spec is right, route follow-up tasks instead.
- **Treating a `proposed` ADR or `draft` spec as binding.** Only `accepted` ADRs and `approved` specs constrain the change.
- **Silently passing a near-miss.** If two artifacts describe the same decision with different content, that is drift even when neither says the other is wrong.
