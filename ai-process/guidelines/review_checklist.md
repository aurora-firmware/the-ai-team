# Code Review Checklist

This checklist is used by the Reviewer role during the two-stage code review procedure.

## Stage 1: Spec Compliance

- [ ] All acceptance criteria from the task are met.
- [ ] No functionality is missing compared to what the task specifies.
- [ ] No unspecified behavior or features were added.
- [ ] Any exclusions or file-scope constraints stated in the task are respected.
- [ ] Any file created or modified outside the task's stated scope is explicitly justified in the Work Log — otherwise this is a **Fail**.

## Stage 2: Code Quality

### Correctness
- [ ] Logic is correct for all expected inputs (including edge cases).
- [ ] Error handling covers failure modes described in the spec.
- [ ] No off-by-one errors, null reference issues, or unhandled states.

### Tests
- [ ] Tests exist for the new or modified product behavior.
- [ ] No test asserts the wording of skills, process documents, guides, or specs, or only proves something was removed.
- [ ] Tests cover both success and failure paths.
- [ ] Tests are independent (no shared mutable state).
- [ ] New tests do not depend on an environment CI does not provide (local git history beyond the checkout depth, network access, locally installed tool versions).
- [ ] The Work Log records local test evidence or explains why a local test run was not possible. Gate 4 owns authoritative pre-merge and post-merge test execution.
- [ ] For an inspection or demonstration task, the Work Log record is present and covers every listed criterion and reference, or the listed steps and observed outcome.

### Security
- [ ] No hardcoded credentials or secrets.
- [ ] External input is validated before use.
- [ ] Database queries use parameterized statements.
- [ ] No new permissions or access beyond what is needed.

### Readability
- [ ] Names are descriptive and follow project conventions.
- [ ] Functions are focused (one responsibility each).
- [ ] Comments explain *why*, not *what* (no redundant comments).
- [ ] No dead code, commented-out blocks, or debugging artifacts.

### Performance
- [ ] No unnecessary loops over large data sets.
- [ ] No blocking operations in hot paths without justification.
- [ ] No obvious memory leaks or resource leaks.

## Bug Fix Review Addendum

Use these checks when reviewing a bug fix:

- [ ] The bug file contains a Diagnosis Log entry before the fix Work Log entry.
- [ ] Reproduction status is explicit: confirmed, intermittent, or not yet reproduced.
- [ ] Relevant logs, stack traces, failing assertions, or command output are recorded or summarized.
- [ ] The isolated fault, root cause or fault hypothesis, and planned verification are documented.
- [ ] The fix is scoped to the isolated cause and does not add unrelated behavior.
- [ ] A regression test covers the defect when practical; if not, the Work Log explains why.
- [ ] The Fix Verification steps were run, or the Work Log explains why they could not be run.

## Review Verdict

**Pass** — all checks are satisfied, and every earlier finding is confirmed fixed or its justification accepted.
**Fail** — one or more checks are not satisfied, or an earlier finding is still open. Each finding states what is wrong and why, citing the claim or rule it fails; it never proposes a fix. The Developer answers every finding before the next review.
**Escalate** — the code has a fundamental design issue that Developer fixes cannot resolve within the approved specification. The active loop consults the Architect.
