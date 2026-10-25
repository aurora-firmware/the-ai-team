---
id: "T-000"
title: "[Task Title]"
status: pending  # planned | pending | in-progress | blocked | completed | cancelled
priority: medium  # critical | high | medium | low
assigned-role: "[agent role or unassigned]"
created: YYYY-MM-DD
---

# [Task Title]

<!--
Task Quality Rules (see the new-task skill for full details):
  - Atomic — one clear outcome.
  - One-shottable — ≤ 3–4 files touched, ≤ 5 ACs, Description ≈ 20 lines.
  - Verifiable — concrete Verification command, explicit manual steps, or for a prose-only task a design review (Design review: line plus reference bullets).
  - Self-contained — Description is enough to start without follow-up questions.
  - EARS — every AC matches one of the five EARS patterns below.
  - Dependency-honest — list every prior task this one reads from or modifies.
  - Interface-explicit — Interfaces names every type, function, or file the task consumes and produces.
  - No placeholders — no TBD, TODO, "implement later", or "similar to Task N"; every name used is defined in this or a dependency task.
-->

## Description

What needs to be done and why.
Include enough context that an agent can start working without asking questions.

## Source Requirements

<!-- Cite the feature spec ID, REQ identifiers, and AC scenarios this task
  implements or verifies. For a change-request or S-000, cite its relevant
  sections; do not invent feature requirement identifiers for those artifacts. -->

Name the source requirements and acceptance scenarios this task covers.

## Acceptance Criteria

<!-- EARS pattern reference. Every criterion must match one pattern:
  1. Ubiquitous            — The system shall [outcome]
  2. Event-driven          — WHEN [trigger] THE SYSTEM SHALL [outcome]
  3. Unwanted-behaviour    — IF [fault] THEN THE SYSTEM SHALL [outcome]
  4. State-driven          — WHILE [state] THE SYSTEM SHALL [outcome]
  5. Optional              — WHERE [feature included] THE SYSTEM SHALL [outcome]

Examples:
  AC-1: WHEN the user submits valid credentials THE SYSTEM SHALL
        redirect to /dashboard within 200ms.
  AC-2: IF the password is incorrect THEN THE SYSTEM SHALL return 401
        and display "Invalid credentials".
  AC-3: The system shall log every authentication attempt with user id
        and outcome.
-->

AC-1: ...
AC-2: ...
AC-3: ...

## Dependencies

- `T-XXX` — brief description of what must be completed first
- None (if no dependencies)

## Interfaces

<!-- Name each interface exactly as it will appear in code. A name consumed here
must be produced by a task listed under Dependencies, or already exist. -->

- **Consumes:** `name(signature)` from `T-XXX`, or "none"
- **Produces:** `name(signature)` this task adds or changes, or "none"

## Files to Touch

- `path/to/file-a.ext` — what changes are needed
- `path/to/file-b.ext` — what changes are needed

## Verification

<!-- Run context: each line runs from the repository root in a fresh shell,
independently of the other lines; a line that needs another directory changes
into it on that line (`cd <dir> && <command>`).
Design review: a design-review task (chosen during planning; see the new-task
skill) replaces the command block with a `Design review:` line followed by one
bullet per reference: the source spec, each accepted ADR it must agree with,
and S-000 when it exists. -->

```bash
# Command(s) to verify the task is complete
```

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

- For FAIL: file, location, what is wrong, what should change.
- For PASS: brief confirmation that both stages passed.
- For ESCALATE: design issue and why normal Developer fixes cannot resolve it.
-->
