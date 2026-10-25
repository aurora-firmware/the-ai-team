---
name: escalation-review
description: Analyse blocked work after a role has exhausted self-recovery. Use when a Developer, Reviewer, Integrator, Development Loop, or Bug-Fix Loop sends a structured escalation request and the Architect must issue guidance or escalate to a human.
allowed-tools: Read, Grep, Glob, Write, Edit, Skill(new-adr)
effort: high
---

# Escalation Consultation

## Input Requirements

- **Structured request** — see [Escalation Request Block (FROZEN)](#escalation-request-block-frozen) below.
- **Original work item** — task or bug file.
- **Relevant logs** — Work Log, Diagnosis Log, Review Verdicts, test output, or merge-conflict context.
- **Approved specification and ADRs** when the issue may affect scope or architecture.

## Escalation Request Block (FROZEN)

This is the single canonical source for the four-field escalation request format. Every skill or
role that emits an escalation must use these exact field names in this exact order. The block is
kept inline at each emission point for locality; this section freezes the field names so all
copies stay consistent.

```text
Problem: [the criterion that will not pass, or the boundary that was violated]
Attempted: [implementations tried on retry, or why the boundary cannot be honoured as written]
Failed because: [the specific reason — test output, scope mismatch, contradictory requirement]
Question: [specific guidance needed to continue within the approved specification]
```

## Procedure

### Step 1: Read The Full Context

Read the escalation request, the work item, and all relevant logs.
Read the approved specification and ADRs if the problem may affect scope, architecture, branch flow, task dependencies, or prior decisions.

### Step 2: Classify The Blocker

Classify the blocker as one of:

- **Execution issue** — can be solved within the current task or bug scope.
- **Task or bug description issue** — needs clearer requirements but not a spec change.
- **Architecture issue within spec bounds** — needs structural guidance or an ADR.
- **Specification issue** — requires changing an approved spec.
- **Unresolvable with current evidence** — needs human judgment.

### Step 3: Issue Guidance Or Escalate

If the issue can be resolved within the approved spec, provide a specific directive to the requesting role.
The directive must include what to change, where to apply it, and how to verify it.

If the task or bug file needs clarification within existing scope, recommend the exact amendment and the owner who should make it.

If the issue is architecture-affecting and within the approved spec, use `new-adr` or amend an existing ADR before implementation continues.
When invoking `new-adr`, provide the full required input set:
- `title`: concise decision title derived from the architectural guidance
- `description`: the escalation request, work item path, approved spec or ADR context, and why the decision affects future work
- `status`: `accepted` — the Architect is adopting the decision now as the authoritative resolution to the escalation

If the issue requires changing the approved spec, or cannot be resolved after full analysis, escalate to the human with a compact context package.

## Output Format

The Architect role envelope wraps this block. The escalation verdict goes in the envelope's `Result:` line: `Result: PASS` when the guidance resolves the blocker, or `Result: ESCALATE` when human escalation is required.

Use this structure:

```text
Classification: <execution | work-item | architecture | specification | unresolved>

Analysis:
- <root cause of the blocker>

Directive:
- <specific action for the requesting role>

Verification:
- <command or check that proves the directive worked>

Parked findings:
- <finding from the last FAIL verdict that the work item meets its criteria without, and why — or "none">

Human escalation required because:
- <only when Result is ESCALATE>
```

### Phase 2 — Human Escalation Report Template

When `Result` is `ESCALATE`, also produce a Phase 2 Human Escalation Report. This is the single canonical template that all callers (dev-loop, bug-loop, spec-breakdown, and any future orchestrator) use when handing off to a human. The report is plain markdown appended to the final output.

```text
## Human Escalation Report

Work item: <task or bug ID and path to its tracker file>
Source skill / loop: <dev-loop | bug-loop | spec-breakdown | other>
Date: <YYYY-MM-DD>

### Original request
<The blocked role's escalation request, verbatim — the four-field Problem / Attempted / Failed because / Question block.>

### Self-recovery attempts
<What the blocked role tried before escalating, including retry counts, review cycles, or merge attempts.>

### Architect analysis
<Classification, root-cause analysis, and any directive the Architect issued (or "no resolution possible — see reason below").>

### Why human input is required
<Precise reason the Architect cannot resolve: approved spec must change, contradictory constraints, etc.>

### Decision needed
<Enumerated options for the human, each with its downstream effect:
- Revise the spec — Planner edits spec and re-runs Gate 2.
- Modify the task/bug — task or bug file is updated in place; work resumes.
- Provide guidance — blocked role applies guidance and continues.
- Defer — work item moves to blocked/deferred state.>
```

## Quality Criteria

- The response addresses root cause, not symptoms.
- Guidance is specific enough for the blocked role to continue without another clarification round.
- The directive stays within the approved specification unless escalating to human.
- ADRs are created or amended only for durable architecture-affecting decisions.
- The human escalation package includes the original work item, attempts, failure reason, Architect analysis, and precise decision needed.

## Common Pitfalls

- Repeating the failed role's troubleshooting without adding structural analysis.
- Giving vague advice such as "refactor" or "simplify".
- Silently changing approved scope.
- Skipping human escalation when the spec must change.
- Creating a loop of repeated Architect consultations instead of resolving or escalating.
