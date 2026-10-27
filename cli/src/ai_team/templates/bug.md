---
id: "B-000"
title: "[Bug Title]"
severity: medium  # critical | high | medium | low
status: open  # open | in-progress | resolved
created: YYYY-MM-DD
source_branch: ""  # required for task-regression bugs; blank for existing defects on dev-agent
---

# [Bug Title]

## Summary

One-paragraph description of the bug and its impact.

## Reproduction Status

Status: confirmed | intermittent | not yet reproduced

Evidence-backed status notes.

## Evidence

- Logs / stack traces / failing assertions:
- Screenshots or recordings:
- Failing command or test:
- First diagnostic step if not yet reproduced:

## Reproduction Steps

1. Step one
2. Step two
3. Step three

## Expected Behavior

What should happen.

## Actual Behavior

What happens instead.
Include error messages, stack traces, or unexpected output.

## Environment

- OS / platform:
- Language / runtime version:
- Relevant dependencies:
- Branch / commit:

## Related

- Task: `T-XXX` (if applicable)
- Specification: `specification-name.md` (if applicable)

## Suspected Area

Known suspected component, file, or subsystem.
Use `unknown` if not yet isolated.

## Fix Verification

<!-- Run context: each line runs from the repository root in a fresh shell,
independently of the other lines; a line that needs another directory changes
into it on that line (`cd <dir> && <command>`). -->

```bash
# Command(s) to verify the bug is fixed
```

## Diagnosis Log

<!-- Mandatory before implementation. Append one entry before changing production code. Format:
### Diagnosis N — YYYY-MM-DD
Reproduction status:
Evidence captured:
Isolated fault:
Root cause or fault hypothesis:
Planned verification:
-->

## Work Log

<!-- Mandatory. Append one entry per session boundary. Format:
### Session N — YYYY-MM-DD
Free-prose body: what was done this session, what was tried and
rejected, decisions made, what remains for next session.

Start every session by reading the entries below.
The final entry serves as the handoff to the reviewer. -->

## Review

<!-- Reviewer: append verdict here after each review cycle.

### Review Verdict — YYYY-MM-DD
PASS | FAIL | ESCALATE
Reviewed through: <HEAD sha>

- Every finding of the work item, numbered F1, F2, ... across cycles: location,
  the claim or rule it is measured against, what is wrong and why (never a fix),
  and its status: Open, Fixed (confirmed), or Acknowledged.
- For PASS: brief confirmation that diagnosis, fix, verification, and code quality passed; every finding is closed.
- For ESCALATE: design issue and why normal Developer fixes cannot resolve it.
-->
