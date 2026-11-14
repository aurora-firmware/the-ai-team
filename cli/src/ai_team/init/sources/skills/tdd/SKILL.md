---
name: tdd
description: Implements assigned tasks using their planned verification method, a test-driven cycle for test tasks or a recorded inspection or demonstration for the others. Applies the test-driven cycle to bug fixes after a Diagnosis Log exists.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(debug), Skill(receive-code-review), Skill(git-conventions)
---

# Test-Driven Development (TDD)

## Input Requirements

- **Task or bug file** — with acceptance criteria, or with Fix Verification steps and a recorded Diagnosis Log.
- **Project test setup** — test framework, directory structure and how to run the tests, including the full suite when the project documents one. An inspection task also needs the references its Verification section lists.
- **Target-project coding guidance** — the project `AGENTS.md`, the coding guidelines and architecture documents the project guidance names, README, build configuration, and any product-owner instructions. The framework standards are the `coding-standards` skill.

Task and bug files live in the local tracker, outside version control; the active loop passes their path.
Read them, but never edit them: return new log content as a handoff.

## Procedure

### Step 0: Read the Work Log

Before anything else, read every existing Work Log entry.
If the latest Review Verdict lists `Open` findings, answer them with `receive-code-review` before new work.

For a bug fix, also read the Diagnosis Log. It must hold a complete fix contract, as the `debug` skill defines it.
If it has none, or the latest one is incomplete, return `BLOCKED` naming what is missing: diagnosis is a separate, recorded cycle and never runs inline here.
The fix contract is the implementation target.

**Base state.** Before the first change on the work item, know whether the full suite is green on the base, so a later failure is clearly yours or clearly pre-existing:

- The active loop states the base is green: trust it and do not run the suite before starting. Cite the statement under Verification (Step 9).
- Otherwise (the loop states the base is not known green, or says nothing about it): run the full suite before your first change and list the run under Verification.
- A bug fix: the Diagnosis Log records the base state; cite it.

A test that fails on the base is pre-existing: name it in the Work Log and leave it alone unless the work item covers it.
On a later session of the same work item (after a review), the base state is already recorded: do not establish it again.

### Step 1: Read the Acceptance Criteria or Fix Verification

For each task criterion or Fix Verification step, identify the testable behavior: its input, expected output, and edge cases (boundaries, empty input, error conditions).
For a bug fix, the first test reproduces the diagnosed defect when practical.

### Step 2: Write the Test

Write one failing test for the next criterion, following the `coding-standards` testing rules.

### Step 3: Verify the Test Fails

Run it. It must fail, for the reason the criterion describes.
If it passes, it does not test the new behavior: rewrite it.

### Step 4: Write the Minimal Implementation

Write the simplest code that makes the test pass, with no logic, error handling or features beyond what the test requires.

### Step 5: Verify the Test Passes

Run it. It must pass. If it fails, fix the implementation, not the test (unless the test was wrong).
If Step 4 → Step 5 fails three consecutive times on the same criterion, apply the Escalation section.
If a test fails in a way the cycle does not explain, or code misbehaves, apply the `debug` skill; its fix contract goes in this session's Work Log entry (Step 9).

### Step 6: Refactor

Clean up without changing behavior, then run the tests of the code you changed again. The full suite runs once per session, after its last change (Step 9).

### Step 7: Commit the Cycle

Commit the red → green → refactor cycle on the assigned `task/…` or `bug/…` branch with the `git-conventions` skill.
When code came before its test, remove the code, commit the failing test on its own, then write the code against it in the next commit; a failing test in a branch's history is acceptable.

### Step 8: Repeat

Return to Step 2 until every criterion has a passing test.

### Step 9: Write the Work Log Handoff

This skill owns the Work Log entry. Write one per session:

```markdown
### Session N — YYYY-MM-DD
<Free prose: what was done, decisions made, what was tried and rejected, what remains,
and anything the Reviewer should look at.>

Verification:
- `<command>` — <decisive output: exit code, pass and fail counts, failing test names>

Scenarios:
- <AC scenario cited in Source Requirements> — <the test or check that verifies it>
```

- **Verification** lists every command run as evidence this session: the base state (Step 0), the task's Verification commands or the bug's Fix Verification, and the full suite when the project documents one, run once after the session's last change. Record the output you saw; a command not run is listed as `not verified: <command> — <reason>`. The Reviewer cites these lines instead of re-running them. Every command is re-runnable from the branch: a script it runs is committed or quoted in full in the entry.
- **Scenarios** appears only when Source Requirements cites AC scenarios.
- Add the inspection or demonstration record, a `debug` fix contract, and the `#### Review answers` block from `receive-code-review` when they apply.
- `N` increments across all sessions on the work item.

Return the entry to the active loop, which appends it under `## Work Log`.
The `Base commit:` line the loop wrote there stays as it is; the loop reads it to resume.

## Inspection and Demonstration Tasks

These apply when the task's Verification section holds an `Inspection:` or `Demonstration:` line, anywhere in the section (a template comment may precede it).
Work through them in place of Steps 2-6, and write no test:

1. Make the change within Files to Touch.
2. **Inspection:** check each listed acceptance criterion against the changed artifact. For prose, read every listed reference (the source spec, the accepted ADRs, and S-000 when listed, read now rather than at session start) and fix every conflict in the changed text.
   **Demonstration:** run the listed command or steps and compare the outcome with the expected observation.
3. Run the full test suite as the regression check, when the project documents one.
4. Commit as in Step 7. The Step 9 entry holds the record: for an inspection, each criterion and reference checked, each conflict found and how it was fixed, and the result; for a demonstration, the command or steps run and the observed outcome.
5. If the change alters product behavior a test should cover, or a conflict can be resolved only by changing a reference document, apply the Escalation section instead of adding an undeclared test.

Steps 0, 7 and 9 still apply.

## Escalation

Return `ESCALATE` on any of these, and do not resume until the Architect responds. The active loop routes the request through `escalation-review`.

- **Retry threshold** — three consecutive Step 4 → Step 5 failures on the same criterion.
- **Boundary violations** (escalate on first detection):
  - The work needs a file outside its scope: for a task, a file not under `Files to Touch`; for a bug, code beyond the fix contract's isolated fault and its regression test.
  - It depends on another task not listed under `Dependencies`.
  - The criteria cannot be met without changing the approved specification.
  - The requirements are contradictory, ambiguous or untestable.

```text
Problem: [the criterion that will not pass, or the boundary hit]
Attempted: [implementations tried and the retry count, or why the boundary cannot be honoured]
Failed because: [test output, scope mismatch, or the contradictory or ambiguous requirement]
Question: [the guidance needed to continue within the approved specification]
```

## Output Format

- **Commits** — tests and implementation (or the inspected or demonstrated change) on the assigned branch, one per cycle, plus the failing-test commit of a Step 7 recovery.
- **Work Log handoff** — the Step 9 entry.

## Quality Criteria

- Every criterion has a test that was seen failing and then passing, or, for an inspection or demonstration task, a record that covers every listed criterion and reference or step.
- Tests cover success and failure paths, and all of them pass together.
- No code exists that no test requires.
- The Work Log entry lists every verification command with the output actually seen.

## Rationalizations

These thoughts mean stop and return to the test-first cycle.

| Excuse | Reality |
|---|---|
| "It is too simple to need a test first." | Simple code breaks too. The test takes a minute and fixes the behavior in place. |
| "I already wrote the code; deleting it is wasteful." | Rewriting from a failing test gives code you can trust; tests bolted on afterwards do not. |
| "I will add the tests right after." | A test written after the code passes on its first run, so it proves nothing. |
| "I will break the code afterwards to show the test fails." | Breaking code after the fact is not a red step; recover as Step 7 says. |
| "I manually checked it, so it works." | A manual check is not repeatable or recorded. The next change breaks it unnoticed. |

## Common Pitfalls

- **Over-refactoring** — refactor only what slows the next cycle, never preemptively.
- **Giant test functions** — a test checks one behavior; split one whose assertions check several.
