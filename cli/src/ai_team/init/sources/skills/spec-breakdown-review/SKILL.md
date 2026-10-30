---
name: spec-breakdown-review
description: Validate a planned task plan before development starts. Use when the Planner has decomposed an approved specification into tasks and Gate 2 must confirm dependency correctness, file conflict risk, ADR consistency, atomicity, and implementation readiness.
allowed-tools: Read, Grep, Glob, Write, Edit
effort: high
---

# Gate 2 Preflight

**Ownership boundary:** spec-breakdown-review owns Gate 2 technical readiness — it validates whether a task plan is safe to hand to `/dev-loop`.
Plan content (coverage decisions, splitting, EARS-pattern authoring in the task file the CLI creates) is owned by `spec-breakdown` and `new-task`.
The result of this skill is a Findings block, which the architect role envelope wraps (see Output Format).

## Input Requirements

- **Approved specification** — the spec that passed Gate 1.
- **Planned task files** — the absolute path of every planned task file, passed by the caller. The tracker is outside the repository, so do not search for task files under `{{project_dir}}/`.
- **Decision records** — existing ADRs in `{{project_dir}}/decisions/`.
- **Architecture documents** — the documents the project guidance names for architecture and technology (by default `docs/development/architecture.md` and `docs/development/tech_stack.md`).
- **Project structure** — current files needed to verify paths and conflict risk.

## Procedure

Gate 2 is a technical preflight. During review, focus findings only on technical task-plan readiness: dependency correctness, file conflict ordering, ADR/spec consistency, atomicity, and verifiable execution.

### Step 1: Read Planning Context

Read the approved specification and all task files for the plan under review.
Read existing decision records in `{{project_dir}}/decisions/` and the architecture documents.
Identify each task's dependencies, files to touch, acceptance criteria, and verification method.

### Step 2: Check Spec Coverage

Verify spec coverage: confirm that the full set of planned tasks covers the entire approved specification with no features, sections, or behaviors left unaddressed.
If any part of the spec is not covered by at least one task, flag the gap.
For feature specs, check every REQ and AC against the tasks' Source Requirements and verification; flag missing coverage and invented behavior. For change-requests and S-000, use their sections.
For S-000, coverage means the bootstrap scope only: every development-infrastructure component and every Decisions needed question has a task, or the product owner recorded it as skipped (brownfield). S-000's solution components never need tasks.
Do not pass Gate 2 if the plan leaves spec sections unimplemented without explicit justification.

### Step 3: Check Dependency Correctness

Verify that every declared dependency refers to a real task.
Check for missing dependencies where one task reads, modifies, or relies on files or behavior created by another task.
Flag circular dependencies.

### Step 4: Check File Conflict Risk

Identify tasks that create or modify the same file.
If overlapping edits are intentional, ensure a dependency orders them.
If no dependency exists, add the dependency directly when the correction is obvious; otherwise request Planner revision.

### Step 5: Check Architectural Consistency

Compare the task plan against existing ADRs and the architecture documents.
If a task contradicts an existing decision or requires changing an approved specification, do not pass Gate 2.
If a task relies on a technology or design that no architecture document or ADR decides, do not pass Gate 2: record it as an architecture gap and return it to the Planner, who runs Feature Architecture again (`spec-breakdown` Step 0a) and revises the task to follow the decision.
When assessing architecture, if the plan contradicts the approved spec or existing ADRs, fail or escalate by following the existing Gate 2 procedure.
Escalate to the product owner through the Planner when the approved spec must change.

### Step 5a: Check Interface Consistency

For each task, read its `Interfaces` block and check names across the plan:

- Every **Consumes** entry is produced by a task listed under that task's `Dependencies`, or already exists in the repository.
- The consumed name and signature match the producing task's **Produces** entry exactly, including spelling, argument order, and types.
- No two tasks **Produce** the same name with different signatures.
- No task body refers to a type, function, or file that no task produces and the repository does not contain.

Fix an obvious naming mismatch directly in the task files; request Planner revision when the mismatch needs a design choice.

### Step 6: Check Atomicity And Verification

Confirm each task is independently implementable and verifiable.
Flag tasks that exceed the one-shottable threshold:

- More than 3-4 files.
- More than 5 acceptance criteria.
- Description too large or ambiguous for one implementation session.
- No clear verification: a task's Verification section does not record one method in the form the `new-task` skill's Verification Methods define (a test command, an `Inspection:` list, or a `Demonstration:` with steps and expected observation), or it omits the project's full-suite command when the project documents one.
- A method that does not match the source: the task records more than one method, or its method differs from the one its source acceptance criteria name, or, for a change-request or S-000, from the one `new-task`'s rule for choosing the method gives.
- A test that asserts the wording of a skill, guide, or process document, or that only proves something was removed: it needs an inspection instead.
- An inspection task for prose whose reference list is empty or omits the source spec.
- Placeholder text: `TBD`, `TODO`, "implement later", "add appropriate error handling", "similar to Task N", or an undefined reference.

### Step 7: Produce Verdict

If the plan passes, state that Gate 2 passes and the plan is ready to merge and activate for `/dev-loop`.

If the plan fails:

- For obvious missing dependencies or file-ordering issues, edit the affected task files directly.
- For decomposition or atomicity issues, return a correction request to the Planner with exact task IDs and required changes.
- Do not fail Gate 2 for product-scope concerns that do not block technical readiness; record them as non-blocking follow-up feedback.
- For spec contradictions, escalate because an approved specification change is required.

## Output Format

There are no duplicated Result/Summary fields in this output: the verdict goes in the architect envelope's `Result: PASS | FAIL | BLOCKED | ESCALATE` line, not in the Findings block.

Use this structure for the Findings block:

```text
Spec reviewed: {{project_dir}}/specs/<file>
Tasks reviewed: <count>

Findings:
- <task-id or area>: <finding and required action>

Corrections made:
- <task-id>: <edit made>

Next owner:
- Planner | Development Loop | Product Owner
```

`BLOCKED` is returned when required inputs are missing (for example, the approved specification path was not provided).

When `Result` is `ESCALATE`, append an Escalation Request block after the fields above:

```text
Problem: [why the plan cannot be validated — spec contradiction, irresolvable circular dependency, unresolved architecture decision]
Attempted: [checks already run and any corrections attempted in-place]
Failed because: [why the problem requires changing the approved specification]
Question: [specific decision or guidance needed from the product owner]
```

Then produce a Phase 2 Product Owner Escalation Report using the template defined in the `escalation-review` skill. The Planner (caller of Gate 2) forwards the report to the product owner alongside the preflight verdict.

## Quality Criteria

- Every planned task in the plan was checked.
- Dependencies are complete and refer to real tasks.
- File conflict risks are resolved by dependency order or Planner correction.
- Interface names and signatures are consistent across tasks.
- No task contains placeholder text.
- Existing ADRs were consulted before approval.
- All tasks are atomic, verifiable, and ready for implementation.
- Product owner escalation is used only when the approved specification or unresolved architecture decision must change.

## Common Pitfalls

- Treating Gate 2 as a second spec approval.
- Passing a plan with hidden file conflicts.
- Fixing decomposition problems by silently rewriting task intent.
- Creating ADRs for routine implementation choices.
- Surfacing task-plan corrections to the product owner when the approved spec does not need to change.
