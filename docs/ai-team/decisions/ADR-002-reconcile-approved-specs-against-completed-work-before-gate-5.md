---
id: ADR-002
title: Reconcile approved specs against completed work before Gate 5
status: accepted
created: '2026-10-19'
---

# ADR-002: Reconcile approved specs against completed work before Gate 5

## Context

Approved specs stay true while work is in flight: the Amendment Log records scope changes, and `architecture-consistency-review` runs whenever a spec, ADR or change-request changes.
Nothing reconciles a spec against what was built once the work is done. Gate 5 compares a status summary with the spec, so a spec can be signed off while it no longer describes the system (issue #31).

## Decision

After the task queue drains and before Gate 5, the Architect runs `architecture-consistency-review` in completion mode on each approved spec the work touched, against the completed task and bug Work Logs and the ADRs created while the work was in flight.
For each drift it decides which side is authoritative: the Planner amends a stale spec; when the spec is right and the work falls short, the Planner creates follow-up tasks under the same spec or change-request, and the Architect re-runs the review once they are completed.
Follow-up tasks are created `pending` and are exempt from Gate 2, because the finding and the approved spec fix their scope and the re-run checks them; the Planner chooses each one's verification method by the `new-task` rule.
The Architect escalates to the product owner when the authoritative side is unclear, when both sides must change, or when drift persists after its follow-up tasks are completed.
Gate 5 requires the latest reconciliation to return `PASS`, or every correction it routed to be done: each amendment applied, and each follow-up task completed with a re-run that returns `PASS`.

## Consequences

- "Specs and ADRs are always true" is enforced by a gate, and deviations surface before sign-off as amendments or follow-up tasks.
- No new skill or role: the review's binding set, findings format and escalation are reused, and the Architect still never edits specs.
- One more Architect pass per release, and Gate 5 can wait for amendments or follow-up tasks.
- The product owner, or the loop's suggested next action, triggers the reconciliation; the loops do not invoke reviews themselves.

## Alternatives Considered

- **A separate reconciliation skill:** it would duplicate the binding set, findings format and routing of `architecture-consistency-review`, and the two copies would drift.
- **Keep the product owner's comparison at Gate 5:** it compares a summary, not the completed work, with the spec, and relies on the product owner noticing deviations no artifact records.
