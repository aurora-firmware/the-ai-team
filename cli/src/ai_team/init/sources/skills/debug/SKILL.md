---
name: debug
description: Diagnostic debugging procedure for bugs and unexpected failures. Use before fixing any bug, when tests fail unexpectedly, when code misbehaves, or when an integration failure has been traced to a source branch.
allowed-tools: Read, Grep, Glob, Edit, Bash
---

# Debug

This skill is **diagnosis-only**. It ends with a fix contract in the Diagnosis Log. The
Developer or tdd skill applies the fix; debug does not change production code.

## Input Requirements

- **Failing test or error report** — what is failing, including the error message.
- **Code under investigation** — the files involved.
- **Expected behavior** — what should happen (from the task's acceptance criteria).
- **Actual behavior** — what is happening instead.
- **Available evidence** — reproduction steps, logs, stack traces, environment details, branch context, and prior Work Log or Diagnosis Log entries.

Task and bug files live in the local tracker, outside version control; the active loop passes their path.
Read their existing Work Log and Diagnosis Log entries, but return new diagnosis content as a handoff to the active loop instead of editing lifecycle files directly.

## Procedure

### Step 0: Read Existing Context

Read the bug or task file, including every existing Work Log and Diagnosis Log entry.
Identify:
- Observable symptom.
- Expected behavior.
- Actual behavior.
- Reproduction status.
- Known environment and branch context.
- Fix Verification steps.

Do not change production code during this step.

### Step 1: Reproduce or Confirm the Failure

Run the failing test or trigger the error.
Confirm it fails consistently (not flaky).
Record the exact command, error message, stack trace, logs, failing assertion, or other observable evidence.

If the issue is intermittent, run enough attempts to establish a pattern and record the frequency.
If the issue cannot be reproduced, do not guess at a fix.
Record what was tried, what evidence still exists, and the next diagnostic step; then return `ESCALATE` with the structured four-field block below if no evidence-backed fault hypothesis can be formed. The active loop routes the request to the Architect via the `escalation-review` skill.

```text
Problem: [the observed symptom and why reproduction has failed]
Attempted: [reproduction strategies, instrumentation, logs inspected]
Failed because: [what evidence is missing, what assumptions could not be validated]
Question: [specific decision or guidance needed from the Architect]
```

### Step 2: Gather Context and Logs

Collect the smallest useful evidence set:
- Runtime logs or test output.
- Relevant configuration and environment values.
- Input data or fixture details.
- Recent related changes when branch history is relevant.
- A minimal failing command or manual path.

Avoid adding permanent logging or debug prints.
If temporary instrumentation is needed, remove it before completion and mention it in the Work Log.

### Step 3: Isolate the Fault
Narrow down the failing component:
- Which function or method is producing the wrong result?
- What input triggers the failure?
- Does it fail with the simplest possible input?

Strategies:
- **Binary search**: Comment out or bypass sections to narrow the scope.
- **Minimal reproduction**: Create the smallest test case that still fails.
- **Trace the data flow**: Follow the input from entry point to the point of failure.

### Step 4: Identify the Root Cause
Once isolated, determine WHY it fails:
- Logic error (wrong condition, off-by-one, missing case).
- State error (variable has unexpected value due to earlier operation).
- Environment error (missing dependency, wrong configuration).
- Specification error (the spec itself is contradictory or incomplete).

Record the root cause.
If the evidence supports only a fault hypothesis, label it as a hypothesis and explain why it is the best current explanation.

### Step 5: Prepare the Diagnosis Handoff (Fix Contract)

Prepare a bug file Diagnosis Log entry — the **fix contract** — before any production code
change is made. The fix contract must include all five of the following fields; entries
that omit any field are incomplete and must not be treated as a green light to implement:

- **Reproduction status** — confirmed, intermittent, or unconfirmed (with rationale).
- **Evidence captured** — the exact commands, outputs, and artifacts gathered.
- **Isolated fault** — the specific function, module, or line responsible for the defect.
- **Root cause or fault hypothesis** — the root cause recorded in Step 4, or the labeled fault hypothesis.
- **Planned verification** — the test command or manual step that will confirm the fix.

Return this fix contract to the active loop. The loop appends it to the bug file in
the tracker. The tdd skill then consumes the fix contract as the implementation target.

**Stop here.** Do not change production code in this skill. The tdd skill owns the
red→green→refactor cycle that follows.

## Output Format

- **Diagnosis Log handoff (fix contract)** — a dated entry for the active loop to record in the bug file before implementation begins.
- **Root cause** — brief explanation of what was wrong and why.
- **Reproduction status** — confirmed, intermittent, or unconfirmed.

## Quality Criteria

- The root cause or fault hypothesis is identified and documented before any code change.
- Reproduction status and evidence are recorded.
- The fix contract is complete: all five fields are present.
- No production code is changed by this skill.
- No new debugging artifacts remain in the codebase (print statements, commented-out code).

## Rationalizations

These thoughts mean stop and return to evidence gathering before any fix.

| Excuse | Reality |
|---|---|
| "I can see the fix already." | A fix without an isolated cause treats a symptom. Record the evidence first; the fix contract needs it. |
| "I will try a quick patch and see." | Each guess adds noise and can hide the real fault. Change one thing at a time, and only after the cause is isolated. |
| "It cannot be reproduced, so I will guess." | Without a reproduction you need an evidence-backed fault hypothesis. If you have neither, escalate. |
| "The failing test is probably flaky." | Flakiness is a cause to isolate, not a reason to skip diagnosis. Re-run and record what varies. |
| "While I am here I will clean this up." | Unrelated changes widen the diff, hide the fix, and fail review. File a separate item. |
| "The Diagnosis Log can be filled in after the fix." | The log is the contract the fix is reviewed against. Filling it in afterwards invalidates the evidence chain. |

## Common Pitfalls

- **Fixing symptoms, not causes** — if a function returns the wrong value, do not add a corrective step downstream. Fix the function.
- **Shotgun debugging** — making multiple changes at once and hoping one of them fixes it. Change one thing at a time and test after each change.
- **Skipping reproduction** — do not patch from a vague symptom unless a reproduction is impossible and the evidence still supports a clear fault hypothesis.
- **Bypassing the fix contract** — returning to the tdd skill before all five fix contract fields are recorded in the Diagnosis Log invalidates the evidence chain.
- **Leaving debug code** — remove all print statements, logging additions, and temporary code before completing the diagnosis.
- **Broadening scope** — the urge to "clean up while I'm here" leads to larger diffs, more risk, and harder reviews. Stay focused on the bug.
