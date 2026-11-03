---
name: debug
description: Diagnostic debugging procedure for bugs and unexpected failures. Use before fixing any bug, when tests fail unexpectedly, when code misbehaves, or when an integration failure has been traced to a source branch.
allowed-tools: Read, Grep, Glob, Edit, Bash
---

# Debug

This skill is **diagnosis-only**: it ends with a fix contract and fixes nothing.
The `tdd` skill applies the fix afterwards.

Temporary diagnostic edits (instrumentation, bypassing a section to bisect, a scratch reproduction) are allowed while diagnosing.
Revert every one before the handoff, never commit one, and name each in the fix contract's Evidence captured field.
No production code change survives this skill.

## Input Requirements

- **Failing test or error report** — what fails, with the error message.
- **Code under investigation** — the files involved.
- **Expected behavior** — the bug's Expected Behavior section, or the task's acceptance criteria.
- **Actual behavior** — what happens instead.
- **Available evidence** — reproduction steps, logs, stack traces, environment and branch context, and every prior Work Log and Diagnosis Log entry.

Task and bug files live in the local tracker, outside version control; the active loop passes their path.
Read them, but never edit them: return new content as a handoff.

## Procedure

### Step 0: Read Existing Context

Read the bug or task file, including every Work Log and Diagnosis Log entry.
Identify the observable symptom, expected and actual behavior, reproduction status, environment and branch context, and the Fix Verification steps.

### Step 1: Reproduce or Confirm the Failure

Run the failing test or trigger the error, and confirm it fails consistently.
Record the exact command, error message, stack trace, logs, failing assertion or other observable evidence.

If the failure is intermittent, run enough attempts to establish a pattern and record the frequency.
If it cannot be reproduced, record what was tried, what evidence still exists, and the next diagnostic step.
If no evidence-backed fault hypothesis can be formed either, apply the Escalation section; never guess at a fix.

### Step 2: Gather Context and Logs

Collect the smallest useful evidence set: runtime logs or test output, relevant configuration and environment values, input data or fixtures, recent related changes when branch history matters, and a minimal failing command or manual path.

### Step 3: Isolate the Fault

Narrow down which function or method produces the wrong result, which input triggers it, and whether it fails with the simplest input.
Strategies:
- **Binary search** — temporarily bypass sections to narrow the scope.
- **Minimal reproduction** — the smallest test case that still fails.
- **Trace the data flow** — follow the input from the entry point to the failure.

Change one thing at a time and re-run after each change.

### Step 4: Identify the Root Cause

Determine why it fails: a logic error (wrong condition, off-by-one, missing case), a state error (an unexpected value from an earlier operation), an environment error (missing dependency, wrong configuration), or a specification error (the spec is contradictory or incomplete).
When the evidence supports only a hypothesis, label it a fault hypothesis and say why it is the best current explanation.

### Step 5: Write the Fix Contract

Revert every temporary diagnostic edit, and confirm with `git status` that none remains.
Then write the fix contract — this skill owns its heading, fields and values:

```markdown
### Diagnosis N — YYYY-MM-DD
Reproduction status: confirmed | intermittent | not yet reproduced — <rationale>
Evidence captured: <exact commands, outputs and artifacts; temporary instrumentation used>
Isolated fault: <the function, module or line responsible>
Root cause or fault hypothesis: <the cause from Step 4, or the labelled hypothesis>
Planned verification: <the test command or manual step that will confirm the fix>
```

`N` increments across all Diagnosis Log entries of the bug.
A contract missing any field is incomplete and is not a green light to implement.

Where it goes:
- **Bug diagnosis cycle** — return it as the Diagnosis Log handoff. The Bug-Fix Loop appends it under `## Diagnosis Log`, and `tdd` implements against it.
- **Unexpected failure during a `tdd` session** (a task, or a bug fix already diagnosed) — put the same fields in that session's Work Log handoff (`tdd` Step 9) instead, then return to `tdd`.

**Stop here.** The red→green→refactor cycle belongs to `tdd`.

## Escalation

Return `ESCALATE` when the failure cannot be reproduced and no evidence-backed fault hypothesis can be formed.
The active loop routes the request to the Architect through `escalation-review`.

```text
Problem: [the observed symptom and why reproduction failed]
Attempted: [reproduction strategies and attempts, instrumentation, logs inspected]
Failed because: [the missing evidence or the assumptions that could not be validated]
Question: [the decision or guidance needed from the Architect]
```

## Output Format

- **Fix contract** — the Step 5 entry, as a Diagnosis Log handoff or inside the Work Log handoff.
- **Working tree** — no diagnostic edit left in it.

## Quality Criteria

- All five fields are filled, and the reproduction status uses one of the three values.
- Every claim in the contract rests on recorded evidence; a hypothesis is labelled as one.
- No diagnostic edit remains, and none was committed.

## Rationalizations

These thoughts mean stop and return to evidence gathering.

| Excuse | Reality |
|---|---|
| "I can see the fix already." | A fix without an isolated cause treats a symptom. Record the evidence first; the fix contract needs it. |
| "The failing test is probably flaky." | Flakiness is a cause to isolate, not a reason to skip diagnosis. Re-run and record what varies. |
