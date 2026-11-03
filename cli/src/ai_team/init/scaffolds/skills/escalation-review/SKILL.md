---
name: escalation-review
description: Analyse blocked work after a role has exhausted self-recovery, and own the escalation request and product owner escalation report formats. Use when a Development Loop or Bug-Fix Loop routes a Developer, Reviewer or Integrator escalation request and the Architect must issue guidance or escalate to the product owner.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(new-adr), Skill(git-conventions)
effort: high
---

# Escalation Consultation

The Architect consultation gives one response per escalation: guidance, or the product owner.
This skill owns the Escalation Request block and the Product Owner Escalation Report that every escalating skill uses.

## Input Requirements

- **Escalation request** — the block in [Escalation Request Block](#escalation-request-block).
- **Work item** — the task or bug file path in the tracker.
- **Relevant logs** — Work Log, Diagnosis Log, Review Verdicts, test output, or merge-conflict context.
- **Findings to rule on** — the IDs of every finding still `Open` in the latest Review Verdict, when the loop passes them.
- **Approved spec and ADRs** — when the problem may affect scope or architecture.

Return `BLOCKED` when the escalation request or the work item is missing.

## Escalation Request Block

Every skill or role that escalates uses these four fields, with these names and in this order.
Each emitter keeps a local copy whose placeholders fit its own trigger.

```text
Problem: [what went wrong: the criterion that will not pass, or the boundary that was hit]
Attempted: [what was tried, including the number of retries]
Failed because: [the specific reason: test output, scope mismatch, contradictory requirement]
Question: [the specific question for the Architect, or the decision for the product owner]
```

## Procedure

### Step 1: Read the Full Context

Read the request, the work item, every log it names, and the approved spec and ADRs when the problem may touch scope, architecture, task dependencies or prior decisions.

### Step 2: Classify the Blocker

| Classification | Meaning |
|---|---|
| `execution` | Solvable within the current task or bug scope |
| `work-item` | The task or bug file needs clearer requirements, without a spec change |
| `architecture` | Needs structural guidance or an ADR, within the approved spec |
| `specification` | Needs an approved spec, or an approved change-request's intent, to change |
| `unresolved` | Cannot be resolved after full analysis |

### Step 3: Rule on Open Findings

For each finding still `Open` in the latest Review Verdict, decide from its Basis, the Developer's latest answer and the Reviewer's latest note:

- **upheld** — the finding holds. The Developer fixes it and the Reviewer confirms the fix. How to fix it stays the Developer's decision: never prescribe it.
- **parked** — the work item meets its criteria without it.

### Step 4: Issue Guidance or Escalate

For `execution`, `work-item` or `architecture`, give a directive the blocked role can follow without another clarification round: what to change, where, and how to verify it.
The directive never covers an upheld finding; the ruling is the whole instruction for it. When the blocker is only the open findings, the Directive is `none beyond the rulings`.

- **`work-item`** — recommend the exact amendment to the task or bug file; the Planner owns task-plan edits, so the Architect never makes it.
- **`architecture`** — record a durable decision with `new-adr`, status `accepted`, giving as `description` the request, the work item path and why the decision affects future work; `new-adr` commits it and runs its consistency review. Rely on the ADR only when that review returns `PASS`; otherwise the decision needs an approved spec to change, so escalate. To amend an existing ADR instead, edit it and commit it on the branch `git-conventions` names for the Architect.

For `specification` or `unresolved`, return `ESCALATE` with the [Product Owner Escalation Report](#product-owner-escalation-report).

## Output Format

The verdict goes in `Result:`: `PASS` when the guidance or the rulings resolve the blocker, `ESCALATE` when the product owner must decide, `BLOCKED` when an input is missing.

```text
Classification: <execution | work-item | architecture | specification | unresolved>

Analysis:
- <root cause of the blocker>

Directive:
- <what to change, where, and how to verify it — or "none beyond the rulings">

Finding rulings:
- <finding ID: upheld | parked — the evidence that decides it, for every finding still Open; or "none">

ADR:
- <ADR ID, its commit and its consistency-review verdict, or "none">

Product owner escalation required because:
- <only when Result is ESCALATE>
```

### Product Owner Escalation Report

The Architect writes this report whenever one of its skills returns `ESCALATE`: here after a consultation, and in `feature-architecture`, `spec-breakdown-review` and `architecture-consistency-review`, where the Architect is the role that is stuck and no consultation precedes it.
The caller passes it to the product owner unchanged.

```text
## Product Owner Escalation Report

Subject: <task or bug ID and tracker path | spec or change-request ID and path | task plan of <spec or change-request ID>>
Raised by: <dev-loop | bug-loop | feature-architecture | spec-breakdown-review (Gate 2) | architecture-consistency-review>
Date: <YYYY-MM-DD>

### Original request
<The Escalation Request block, verbatim.>

### Self-recovery attempts
<What was tried before escalating, with retry counts, review cycles or merge attempts; for an Architect skill, the options and checks it ran.>

### Architect analysis
<Classification, root cause, and any directive or rulings issued, or "no resolution possible".>

### Why product owner input is required
<The approved spec or change-request intent must change, or the problem is unresolvable, and why.>

### Decision needed
<The options that apply to the subject, each with its effect:
- Revise the spec — the Planner amends the spec on its open planning branch, or on an amendment planning branch once that branch has merged (git-conventions), and logs it in the Amendment Log; the Architect runs architecture-consistency-review on it; on PASS the Planner merges. The loop notes the amendment on each affected in-progress task, and the stopped item resumes.
- Modify the task or bug — the product owner updates the work item file, or the Planner raises a change-request; the stopped item resumes and the Developer re-reads it.
- Provide guidance — the guidance is recorded in the work item file; the stopped item resumes and the blocked role applies it.
- Defer — the task or bug stays blocked with the reason noted; no loop resumes it until it is unblocked.>
```

A stopped task or bug resumes once the product owner runs `ai-team task unblock <id>` or `ai-team bug unblock <id>`: the next loop run picks it up on its existing branch.

## Quality Criteria

- The analysis names the root cause, not the symptom the role already reported.
- Every finding still `Open` has a ruling.
- The directive never changes approved scope; a needed scope change is escalated.

## Common Pitfalls

- Giving vague advice such as "refactor" or "simplify".
