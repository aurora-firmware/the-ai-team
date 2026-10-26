---
id: ADR-002
title: Reconcile approved specs against completed work before Gate 5
status: accepted
created: '2026-10-19'
---

# ADR-002: Reconcile approved specs against completed work before Gate 5

## Context

Approved specs stay true while work is in flight: the Amendment Log records scope changes
during execution, and `architecture-consistency-review` runs whenever a spec, ADR, or
change-request changes. Nothing reconciles a spec against what was actually built once the
work is done.

Gate 5's pass criterion is that "the status summary matches the approved specification" — a
human comparing a summary to a spec, not a check of the completed work against the spec. A
spec can therefore be approved, implemented with undocumented deviations, and signed off while
no longer describing the system. The framework's central promise is that specs and ADRs are
always true; today that holds by planning-time discipline, not by a gate at the end.

The comparison report in `docs/ai-team/docs/superpowers_comparison.md` (section 7) identified
this gap, and issue #31 tracks closing it.

## Decision

Add a standing duty, **spec-truth reconciliation**, that runs after the task queue drains and
before the human gives Gate 5 sign-off.

The Architect re-reads each approved spec touched by the completed work against the completed
task and bug Work Logs, any ADRs created while the work was in flight, and the deferred-Minor
roll-up, then either confirms the spec is still true or routes corrections to the Planner.
For each drift it first decides which side is authoritative. When the spec is stale, the
Planner amends it. When the spec is right and the work falls short, the Planner creates
follow-up tasks under the same spec or change-request, and the Architect re-runs the
reconciliation once they are completed. Follow-up tasks are created `pending` and are exempt
from Gate 2, because the finding and the approved spec already fix their scope; the re-run is
their check. The Planner still chooses each follow-up task's verification method by the
`new-task` rule: a test, an inspection, or a demonstration, as defined in
`guides/spec-authoring-guide.md`. When it is unclear which side is authoritative, or
both need to change, the Architect escalates to the human to decide. It also escalates when a
re-run still finds drift on a finding whose follow-up tasks are completed, rather than routing
another round of tasks that skip Gate 2.

It reuses `architecture-consistency-review` rather than adding a skill: same binding set, same
findings block, same escalation procedure. The routing adds the follow-up-task and
authoritative-side escalation routes above to the existing rules (the Planner amends approved
specs and records the change in the Amendment Log; the Architect amends or supersedes ADRs).
Only the trigger differs — completion of the work instead of change to an artifact.

Gate 5 gains a pass criterion: the latest reconciliation returned `PASS`, or every correction
it routed is done — each spec amendment applied, and each follow-up task completed with a
re-run that returns `PASS`.

## Consequences

### Positive

- "Specs and ADRs are always true" becomes a property enforced by a gate, not only by planning
  discipline.
- Deviations discovered during implementation are surfaced before sign-off, as spec amendments
  or as follow-up tasks.
- No new skill or role to maintain.

### Negative

- One more Architect pass per release, which costs time and tokens on large specs.
- Gate 5 can be delayed while amendments are applied or follow-up tasks are completed.

### Neutral

- The Architect still never edits specs; the Planner owns amendments, as before.
- The reconciliation is triggered by the human or the loop's suggested next action, because the
  loops end with a short run summary and do not invoke reviews on their own.

## Alternatives Considered

### Alternative A: A separate reconciliation skill

**Description:** Author a `spec-reconciliation` skill with its own procedure and output.
**Rejected because:** It would duplicate the binding-set reading, findings format, and routing
rules of `architecture-consistency-review`, and the two copies would drift.

### Alternative B: Keep the human comparison at Gate 5

**Description:** Leave the status-summary-versus-spec comparison as the only check.
**Rejected because:** It compares a summary to a spec, not completed work to a spec, and relies
on the human noticing deviations that no artifact records.

## Amendments

- **2026-10-21:** Added the follow-up-task route. The CR-003 reconciliation found two drifts
  (F1, F2) where the spec was right and the completed work fell short. Amending the spec would
  have recorded the gap as intended, so the Planner created follow-up tasks (T-126, T-127) and
  the Architect re-ran the review to `PASS`. The decision now states that route, and the Gate 5
  criterion accepts completed follow-up tasks with a passing re-run. A drift whose authoritative
  side is unclear, or where both sides must change, escalates to the human. Follow-up tasks
  are exempt from Gate 2, and the Planner chooses their verification mode by the
  spec-breakdown rule. A drift that persists after its follow-up tasks escalates to the human,
  so follow-up rounds cannot repeat without a human decision.
- **2026-10-26:** Verification vocabulary. Tasks are now verified by a test, an inspection, or
  a demonstration, as defined in `guides/spec-authoring-guide.md`; design review is folded
  into inspection. The Planner chooses each follow-up task's verification method by the
  `new-task` rule, which replaces the spec-breakdown rule the 2026-10-21 entry names.

