---
name: architecture-consistency-review
description: Check that a created or changed spec, ADR or change-request stays consistent with every approved spec and accepted ADR, and, in completion mode, that each approved spec the finished work touched is still true of what was built. Use when an ADR is created or accepted, a TODO-free spec is created or amended, the product owner approves a TODO-free change-request, or the task queue drains before Gate 5 sign-off.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(new-adr), Skill(git-conventions)
effort: high
---

# Architecture Consistency Review

**Ownership boundary:** this skill checks a created or changed artifact — an ADR, a spec or a change-request — against the binding set: every `accepted` ADR and every `approved` spec. Task plans are Gate 2's (`spec-breakdown-review`). The review reports findings and routes corrections; it never edits a spec.

## When This Runs

- **ADR created or accepted** — after `new-adr` records it.
- **Spec created or amended** — once it has no product-owner-answerable `[TODO]` left: a new spec before Gate 1, an amended approved spec on its planning branch or amendment planning branch, including a spec amended for an approved change-request.
- **Change-request approved** — after the product owner approves the TODO-free change-request, before its spec amendments are applied. The approved change-request is the authoritative intent for every correction.
- **Completion (spec-truth reconciliation)** — the main session runs it when the task queue drains, before Gate 5 sign-off; see [Completion Mode](#completion-mode).

## Input Requirements

- **Changed artifact** — the path of the ADR, spec or change-request and which kind it is; for an amendment or change-request, the decision, section or requirement that changed.
- **Decision records** — all ADRs in `{{project_dir}}/decisions/`.
- **Specifications** — all specs in `{{project_dir}}/specs/`.
- **Approved change-request** — when the changed artifact is a spec amended for one, its tracker path.
- **Branch** — the planning branch or amendment planning branch the change is on, when there is one.
- **Completion mode only** — the paths of the approved specs the work touched (never S-000), and the tracker paths of the completed tasks and resolved bugs that implemented each. When the paths are not given, list them with `ai-team list tasks` and `ai-team list bugs`.

Return `BLOCKED` when the changed artifact is missing, a changed spec still has a product-owner-answerable `[TODO]`, a change-request is not yet approved, or a spec amended for a change-request comes without it.

## Procedure

### Step 1: Isolate What Changed

Identify the decision, requirement or contract the changed artifact now asserts. For an amendment or change-request, isolate the delta, not the whole document. Read an approved change-request as written; do not reinterpret it through downstream draft wording. When the changed artifact is a spec amended for an approved change-request, also check each written amendment against that change-request: it adds no behaviour change the change-request does not state.

### Step 2: Read the Binding Set

Read every `accepted` ADR and every `approved` spec. A `proposed` ADR or a `draft` spec does not bind.

### Step 3: Check for Contradiction

For each binding artifact, decide whether the change contradicts it: it asserts a different decision for the same concern, removes a guarantee another artifact relies on, or restates a rule with different content. Two artifacts that describe the same decision with different content are a contradiction even when neither names the other. Record each one with the artifact, the conflicting statements, and which one is intended to be authoritative.

For a feature spec, also check its readiness: requirement completeness, consistent terminology, feasibility, mutually compatible constraints, assumptions, acceptance coverage, resolved behavioural and feasibility questions, and precise public contract references. Apply the `new-spec` authoring contract, including its content-boundary rule: a spec that makes a technology choice or records implementation design has a readiness gap.

### Step 4: Check Against S-000

When an approved S-000 exists, confirm that a new or changed spec stays within S-000's purpose and respects each component's boundary and responsibility. When a spec needs something S-000 does not cover, report it as either an S-000 amendment or a spec cut back to scope, naming which.

When the changed artifact is S-000 itself, check it for internal consistency and against the `new-system-overview` pre-submission checklist instead of against other specs.

### Step 5: Route Each Finding

Route each finding to the owner of the side that must change:

| The side that must change | Correction |
|---|---|
| A draft spec, before Gate 1 | The Planner revises the draft. No Amendment Log entry |
| The approved spec under review, on its open planning branch or amendment planning branch, or the approved spec an open change-request planning branch amends | The Planner amends it on that branch and records the change, and the driving ADR ID, in its Amendment Log |
| Another approved spec, while the branch spec's Gate 1 is still ahead | A cross-spec amendment on that branch, approved at that Gate 1 as `git-conventions` Cross-Spec Amendments describes |
| An ADR | The Architect amends it, or supersedes it with `new-adr` |
| A change-request finding that keeps its approved intent | The Planner applies it, anchored to the approved change-request |

When the Architect amends an ADR directly, commit it as `git-conventions` describes for the Architect: on the branch of the change under review, otherwise on `{{integration_branch}}`.

### Step 6: Decide the Verdict

| Result | When | Next Owner |
|---|---|---|
| `PASS` | No contradiction and no readiness gap remains, or every one was an ADR correction the Architect made and committed | `Planner` (in completion mode, to record the reconciliation row), or `none` when no Planner step follows |
| `FAIL` | A finding is routed to the Planner, and every finding has a correction in Step 5 | `Planner` |
| `BLOCKED` | An input is missing (Input Requirements) | `Planner` when the Planner requested the review, otherwise `Product Owner` |
| `ESCALATE` | A condition under [Escalation](#escalation) | `Product Owner` |

After the Planner applies the corrections, run the review again on the corrected artifacts.

## Completion Mode

Completion mode confirms that each touched approved spec is still true of what was built. It uses the same binding set, verdicts and output, with these differences:

- **Step 1** isolates what each spec asserts (requirements, interfaces, guarantees), not a delta.
- **Step 3** checks each assertion against the Work Logs of the completed tasks and resolved bugs, and every ADR created or amended while the work was in flight: a requirement the work did not deliver, behaviour the work added that the spec does not describe, or an interface that now differs. Record each drift with the spec statement and the evidence. A spec is never confirmed from the spec alone.
- **Step 5** first decides which side is authoritative for each drift:
  - **The spec is stale** (the work is right) — the Planner amends the spec on an amendment planning branch.
  - **The work falls short** (the spec is right) — the Planner creates follow-up tasks with `new-task` under the same spec or change-request, with no planning branch, each naming the finding and the spec statement it must satisfy. They are created `pending` and skip Gate 2, because the finding and the approved spec fix their scope. Once they are completed, the main session runs completion mode again for that spec. Never amend a spec to match work that fell short.
- **Record** — return the verdict as `Reconciliation record:`, one Amendment Log row `| YYYY-MM-DD | spec-truth reconciliation — PASS or FAIL | <one-line summary> | none |`. The Planner records it in the change-request file for change-request work, otherwise in the reconciled spec's Amendment Log as `git-conventions` **Amendment Planning Branch** describes. The row changes no scope and does not bump `version`.

## Escalation

The Architect is the escalation target, so this escalation goes to the product owner. Return `ESCALATE` when:

- an approved spec must change and no Step 5 row covers it, such as a cross-spec amendment with no Gate 1 ahead to approve it;
- a finding would change an approved change-request's intent: the product owner revises, rejects or reaffirms it before any downstream artifact is amended;
- in completion mode, it is unclear whether the spec or the work is authoritative, both need to change, or a re-run still finds a drift whose follow-up tasks are completed.

Append the Escalation Request block and the Product Owner Escalation Report, both in the formats `escalation-review` owns:

```text
Problem: [the contradiction or drift, with the conflicting statements]
Attempted: [the routing considered and why it does not apply]
Failed because: [why an approved spec or change-request intent must change, or why the authoritative side is unclear]
Question: [the decision the product owner must make]
```

## Output Format

The verdict goes in `Result:`.

```text
Artifact reviewed: <path of the changed ADR, spec or change-request, or the touched specs in completion mode>
Binding set checked: <count> accepted ADRs, <count> approved specs

Findings:
- <artifact>: <the contradiction and which statement is authoritative>

Corrections routed:
- <artifact>: <Planner draft revision | Planner approved-spec amendment | Planner follow-up task | Architect ADR amendment or supersession (commit) | escalation>

Reconciliation record:
- <completion mode only: the Amendment Log row>
```

## Quality Criteria

- Every accepted ADR and approved spec was read before the verdict.
- Each finding names the exact conflicting statements, not a vague "may conflict".
- In completion mode, each drift states which side is authoritative before it is routed.
