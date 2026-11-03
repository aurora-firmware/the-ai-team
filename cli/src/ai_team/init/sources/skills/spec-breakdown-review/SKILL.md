---
name: spec-breakdown-review
description: Validate a planned task plan before development starts (Gate 2). Use when the Planner has decomposed an approved spec or change-request into planned tasks and hands back with Next Owner Architect, and the plan's coverage, dependencies, file conflicts, architecture consistency, atomicity and readiness must be confirmed.
allowed-tools: Read, Grep, Glob, Write, Edit
effort: high
---

# Spec Breakdown Review

**Ownership boundary:** this skill owns Gate 2, the technical readiness of a task plan: coverage, dependencies, file conflicts, consistency with the architecture, atomicity and verifiability. It does not reopen product or spec questions settled at Gate 1 or by the product owner's approval of a change-request. Plan content is `spec-breakdown`'s and `new-task`'s.

The main session runs this skill when the Planner stops after writing the task files with Next Owner: Architect, and resumes the Planner with the result.

## Input Requirements

- **Approved work** — the path of the approved spec or approved change-request the plan implements.
- **Planned task files** — the absolute path of every planned task file. The tracker is outside the repository, so do not search for task files under `{{project_dir}}/`.
- **Decision records** — the ADRs in `{{project_dir}}/decisions/`; `accepted` ones are binding.
- **Architecture documents** — the documents the project guidance names for architecture and technology (by default `docs/development/architecture.md` and `docs/development/tech_stack.md`).
- **Project structure** — the current files, to verify paths and conflict risk.

Return `BLOCKED` when the approved work or the task paths are missing.

## Procedure

### Step 1: Read the Planning Context

Read the approved spec or change-request, every task file, the ADRs and the architecture documents.
Note each task's dependencies, files to touch, acceptance criteria and verification method.

### Step 2: Check Coverage

- **Feature spec** — every REQ and AC is covered by some task's Source Requirements and Verification; flag missing coverage and behaviour no requirement asks for.
- **Change-request** — every requested change is covered, and no task contradicts the approved change-request's intent.
- **S-000** — the bootstrap scope only: every development-infrastructure component and every Decisions needed question has a task, or the product owner recorded it as skipped (brownfield). Solution components never need tasks.

### Step 3: Check Dependencies

Every declared dependency names a real task.
Flag a missing dependency wherever a task reads, modifies or relies on files or behaviour another task creates, and every circular dependency.

### Step 4: Check File Conflicts

Every pair of tasks that creates or modifies the same file is ordered by a dependency.

### Step 5: Check Architecture Consistency

- A task that contradicts an accepted ADR, the architecture documents, the approved spec or the change-request intent is a plan defect.
- A task that relies on a technology or design that no architecture document or ADR decides is an architecture gap: the Planner runs Feature Architecture again (`spec-breakdown` Step 0a) and revises the task to follow its decision.

### Step 6: Check Interfaces

For each task's `Interfaces` block:

- Every **Consumes** entry is produced by a task listed under its `Dependencies`, or already exists in the repository.
- The consumed name and signature match the producing task's **Produces** entry exactly, including spelling, argument order and types.
- No two tasks **Produce** the same name with different signatures.
- No task body refers to a type, function or file that no task produces and the repository does not contain.

### Step 7: Check Atomicity and Verification

Flag a task that:

- exceeds the one-shottable limits in `new-task`'s Task Quality Rules;
- has no Verification in a form `new-task`'s Verification Methods define (a test command, an `Inspection:` list, or a `Demonstration:` with steps and expected observation), or omits the project's full-suite command when the project documents one;
- records more than one method, or a method other than the one its source acceptance criteria name (for a change-request or S-000, the one `new-task`'s rule for choosing the method gives);
- plans a test that asserts the wording of a skill, guide or process document, or only proves a removal: that needs an inspection;
- is an inspection of prose whose reference list is empty or omits the source spec;
- contains placeholder text: `TBD`, `TODO`, "implement later", "add appropriate error handling", "similar to Task N", or an undefined reference.

### Step 8: Correct and Decide

Fix these directly in the planned task files and list each under `Corrections made`: an obvious missing dependency, a file-ordering dependency, an obvious naming mismatch. Every other finding is a correction request to the Planner, naming the task IDs and what must change; never rewrite a task's intent.

A product-scope concern that does not block technical readiness is noted as non-blocking feedback, not a finding.

| Result | When | Next Owner |
|---|---|---|
| `PASS` | No finding is left, including when every finding was fixed under `Corrections made` | `Planner`, who merges the planning branch and sets the tasks `pending` |
| `FAIL` | Any correction request remains, including an architecture gap | `Planner`, who revises and hands back for Gate 2 again |
| `BLOCKED` | An input is missing | `Planner` |
| `ESCALATE` | The plan can be made ready only by changing the approved spec or the approved change-request intent | `Product Owner` |

## Escalation

The Architect is the escalation target, so this escalation goes to the product owner.
Return `ESCALATE` only when the approved spec or the approved change-request intent must change; every other problem is a `FAIL` back to the Planner.
Append the Escalation Request block and the Product Owner Escalation Report, both in the formats `escalation-review` owns:

```text
Problem: [the requirement or intent the plan cannot be made consistent with]
Attempted: [the checks run and the corrections made or requested]
Failed because: [why the approved spec or change-request must change]
Question: [the decision the product owner must make]
```

## Output Format

The verdict goes in `Result:`.

```text
Work reviewed: <path of the approved spec or change-request>
Tasks reviewed: <count>

Findings:
- <task ID or area>: <finding and the change required>

Corrections made:
- <task ID>: <edit made>

Non-blocking feedback:
- <product-scope concern, or "none">
```

## Quality Criteria

- Every planned task was checked against every step.
- Every finding names the task and the exact change required.
