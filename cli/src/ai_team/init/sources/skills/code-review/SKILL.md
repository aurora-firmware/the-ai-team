---
name: code-review
description: Two-stage code review for completed tasks and bug fixes. Use when a Developer submits work and the Reviewer must check task acceptance or bug diagnosis criteria before reviewing code quality.
allowed-tools: Read, Edit, Grep, Glob, Bash, Skill(new-bug)
effort: high
---

# Code Review

## Input Requirements

- **Task or bug file** — the task definition with acceptance criteria, or the bug report with diagnosis and fix-verification steps.
- **Code changes** — the review package the loop wrote (`git log`, `git diff --stat`, and `git diff -U10` for `BASE..HEAD`), or a `BASE..HEAD` range to diff yourself. Review the whole range. Never review `HEAD~1` alone: a multi-commit branch silently loses its earlier commits.
- **Test results** — the test evidence in the Developer's Work Log (command and output). Do not re-run tests the Work Log already shows passing; run a command only to check something the Work Log does not cover.

The task or bug file lives in the local tracker, outside version control; `ai-team show <id> --json` reports its path.
Review verdicts are written there, never committed, and never placed on the implementation branch.
The two-stage checklist below is the canonical quality bar for all code reviews.

## Procedure

### Step 1: Read the Work Item
Read the task or bug file completely.
Treat the Work Log and every summary in it as unverified claims about the code, and check each claim against the diff. A stated rationale never lowers a finding's severity.
For tasks, understand what was asked, what the acceptance criteria are, and which files should have been modified.
For bugs, understand the symptom, reproduction status, diagnostic evidence, isolated fault, root cause or fault hypothesis, and Fix Verification steps.

For bug fixes, verify the diagnosis→fix evidence chain before proceeding to Stage 1:
- Does the Diagnosis Log exist and contain a complete fix contract (reproduction status, evidence captured, isolated fault, root cause or fault hypothesis, planned verification)?
- If the evidence chain is missing or incomplete, return **FAIL** immediately. Do not infer intent from the diff.

### Step 2: Stage 1 — Acceptance Or Bug Criteria
For tasks, check each acceptance criterion against the code:
- Is the criterion met? (yes/no, with evidence)
- Was any unspecified behavior or functionality added?
- Were unexpected files modified?

For bug fixes, check:
- Does the Diagnosis Log include reproduction status and evidence?
- Does the fix address the isolated fault or documented root cause from the fix contract?
- Were the Fix Verification steps followed?
- Was unrelated behavior added?

If any task criterion or bug-fix criterion is not met, skip Stage 2 and set the verdict to **FAIL** with specific feedback.

### Step 3: Stage 2 — Code Quality

**Stage 2 Checklist:**
- **Correctness**: Logic handles expected inputs and edge cases correctly.
- **Tests**: Tests exist, cover both success and failure paths, and are independent (no shared mutable state). For a design-review task, the equivalent is the Work Log design-review record (see Design-Review Tasks); it replaces the tests.
- **Security**: No hardcoded secrets, all external input is validated, database queries are parameterized.
- **Readability**: Names are descriptive, functions are focused, no dead code or commented-out blocks.
- **Performance**: No unnecessary loops, blocking calls, or resource leaks.

**Bug Fix Addendum:**
For bug fixes, also check:
- The fix is minimal — only the code required to address the isolated fault was changed.
- A regression test that fails before the fix and passes after it exists when the defect can be tested automatically, or the Work Log explains why only manual verification is possible.
- No unrelated refactoring, cleanup, or feature code is bundled into the fix.
- The Diagnosis Log fix contract (reproduction status, evidence captured, isolated fault, root cause or fault hypothesis, planned verification) matches what was actually implemented.

### Design-Review Tasks

This section applies when the task's Verification section holds the line `Design review:`. Detect the line, not the first line of the section: the task template's Verification comment may precede it. Such a task has no tests; the Developer's evidence is a Work Log design-review record.

Check, in Stage 1:
- **The planning choice.** The diff changes only prose that no test pins. A change to code, CLI output, or a rule a test can observe is at least **Important**: the task needed a test.
- **The record.** The Work Log names the documents checked, each conflict found and how it was fixed, and the result. Verify the claimed consistency against the listed references: every reference in the Verification section. Read S-000 at review time, when the task lists it, not at session start.

A missing record, or one that omits a listed reference, is at least **Important**, as missing red/green evidence is.

### Severity

Rate every finding from Stage 1 and Stage 2:

| Severity | Meaning | Effect |
|---|---|---|
| **Critical** | Breaks an acceptance criterion or the fix contract, loses data, or opens a security hole | FAIL |
| **Important** | The work cannot be trusted until it is fixed: missing or untrustworthy tests, wrong behavior in a realistic case, scope violations | FAIL |
| **Minor** | Real but non-blocking: naming, small duplication, a style or readability improvement within project standards | PASS; recorded under the `#### Deferred Minor findings` heading — never only inline in the findings — so Gate 5 can roll it up |

A finding is at least **Important** when it breaks CI or depends on an environment CI does not provide — for example local git history beyond the checkout depth, network access, or the developer's installed tool versions. When the project has CI configuration, compare the new tests against it.

An unmet acceptance criterion, an incomplete bug evidence chain, or a finding that contradicts an explicit sentence of the task Description (for example "The function never raises") is never Minor.

### Cannot Verify From the Diff

Some claims cannot be confirmed from the diff and the work item alone — for example, that a changed function's other callers still work, or that a behavior matches a task completed earlier in the run. Do not guess PASS or FAIL for them. List each one as `⚠️ Cannot verify from diff` with the claim and what would confirm it. The active loop holds the cross-task context and resolves each item before integration.
If a finding already warrants FAIL, issue FAIL; the unverifiable items are still listed.

### Step 4: Produce Verdict

The Reviewer's self-recovery threshold is **one review cycle** for ESCALATE-worthy issues. For ordinary quality issues, issue FAIL (the active loop allows up to three FAIL cycles per work item before it forces escalation on its own).

- If no Critical or Important finding remains → **PASS**. Record the verdict for the active loop, with any Minor findings and `⚠️ Cannot verify from diff` items listed.
- If any Critical or Important finding remains (bug in logic, missing test, unmet criterion, etc.) → **FAIL** with specific, actionable feedback. The Developer fixes and re-submits.
- If the code has a fundamental design issue that no amount of Developer fixes can address within the approved specification → **ESCALATE** immediately. Do not issue FAIL first and wait. ESCALATE-worthy examples: the spec is internally contradictory, the acceptance criteria cannot be met without a spec change, the diagnosis points at a root cause outside the bug's stated scope.

### Step 5: Record the Verdict
Append to the task or bug file under a `### Review Verdict — [date]` heading, from whatever branch is checked out.
The first line of the section must be one of: `PASS`, `FAIL`, or `ESCALATE`.
Do not commit anything: the verdict, and any bug filed through `new-bug` during this review, live in the tracker outside version control.

**On PASS:** Record the verdict with a brief confirmation that both stages passed. Under a `#### Deferred Minor findings` heading, list each Minor finding with its location and suggested change, one per line. Under `#### ⚠️ Cannot verify from diff`, list each unverifiable claim. Omit a heading that has no entries. The `status-report` skill rolls the deferred Minor findings up for triage at Gate 5, so write each one so a person who has not seen the diff can act on it.

**On FAIL:** Record the verdict and list each failed check with the location, what is wrong, and what should change. The work item stays `in-progress`. The Developer fixes the issues and re-submits. The active loop tracks the review cycle count. On a third consecutive FAIL, the active loop escalates to the Architect — the Reviewer does not need to change the verdict type.

## Output Format

PASS, FAIL, and ESCALATE append a `### Review Verdict — [date]` section to the task or bug file in the tracker.
The first line of the section is always one of: `PASS`, `FAIL`, or `ESCALATE`.

### On PASS
Verdict: `PASS`
A brief confirmation that both stages passed, then the `#### Deferred Minor findings` and `#### ⚠️ Cannot verify from diff` lists when they have entries.
Next owner: active Development Loop or Bug-Fix Loop.

### On FAIL
Verdict: `FAIL`
For each failed check:
- **Severity** — Critical or Important.
- **File and location** — which file, which section or line.
- **What is wrong** — specific description of the issue.
- **What should change** — actionable guidance on how to fix it.

List Minor findings and `⚠️ Cannot verify from diff` items after the failed checks, under the same headings as on PASS.

### On ESCALATE
Verdict: `ESCALATE`
Record the verdict under `### Review Verdict — [date]` and include a structured escalation request using the standard four-field block:

```text
Problem: [the fundamental design issue observed in the code]
Attempted: [what review cycles and Developer fixes preceded this verdict]
Failed because: [why ordinary Developer fixes cannot resolve it within the approved specification]
Question: [specific decision or guidance needed from the Architect]
```

Next owner: active loop for Architect consultation.

## Quality Criteria

- Every acceptance criterion was explicitly checked (not assumed).
- For bug fixes, the diagnosis→fix evidence chain was explicitly verified before any other check.
- For bug fixes, diagnostic evidence and Fix Verification were explicitly checked.
- Feedback is specific and actionable — never vague.
- Every finding carries a severity, and the verdict follows from it.
- Claims in the Work Log were checked against the diff, not accepted.
- The reviewed range runs from the recorded base commit to the branch head.
- Every Minor finding and unverifiable claim is recorded where the loop and Gate 5 can find it.
- For design-review tasks, the planning choice and the Work Log design-review record were checked against every listed reference.
- The reviewer checked the actual code, not just the test results.
- No personal style preferences were enforced — only project standards from the coding guidelines.

## Rationalizations

These thoughts mean stop and verify against the code.

| Excuse | Reality |
|---|---|
| "The Work Log says it works, and the tests pass." | The Work Log is the Developer's claim. Check the claim against the diff. |
| "The Developer explained why this is fine." | A stated rationale never lowers a finding's severity. Judge the code. |
| "It is only a small deviation from the criteria." | An unmet acceptance criterion is a FAIL, however small. |
| "I cannot tell from the diff, so I will guess PASS to keep things moving." | Record it as `Cannot verify from diff` so the loop can check it with the cross-task context you lack. |
| "This is a style preference, but I will block on it anyway." | Enforce project standards only. A preference is at most a deferred Minor finding. |
| "The diff is large, so I will skim the rest." | Review the whole range, or return a FAIL asking for a smaller one. A skimmed review is a rubber stamp. |

## Common Pitfalls

- **Trusting the report** — accepting the Work Log's summary or the Developer's rationale instead of reading the diff.
- **Reviewing only the last commit** — the range starts at `BASE`, the commit the branch was created from, not at `HEAD~1`.
- **Re-running the Developer's tests** — the Work Log carries that evidence; a repeat run adds latency, not coverage.
- **Silent Minor findings** — noting a Minor observation in prose that no one will read. Use the `Deferred Minor findings` list.
- **Rubber-stamping** — approving because tests pass without reading the code. Tests can have gaps.
- **Bikeshedding** — spending review time on naming preferences or formatting instead of correctness and security.
- **Vague feedback** — "this could be better" is not actionable. "This function handles the success case but does not handle the empty-input case described in acceptance criterion 3" is.
- **Scope creep in review** — reviewing code outside the task's scope. Only review what the task changed.
- **Inferring intent from the diff** — for bug fixes, do not guess what the fix was meant to address. Require a complete evidence chain in the Diagnosis Log before reviewing the implementation.
