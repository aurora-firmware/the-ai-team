---
id: "S-000"
title: "[Specification Title]"
version: "0.1"
status: draft  # draft | review | approved | superseded
created: YYYY-MM-DD
author: "[Author name or agent role]"
---

# [Specification Title]

<!--
Describe observable requirements and measurable outcomes, not implementation
files or task lists. Fill this draft with the new-spec skill, which carries the
section recipes and the pre-submission checklist.
-->

## Purpose

<!-- The Purpose names the S-000 component when an overview exists;
  system-wide structure lives in S-000. Explain the problem, why it matters
  now, and the observable outcome in three to four sentences. -->

[TODO] State the problem, trigger, and expected outcome.

## Users and Journeys

<!-- Identify relevant people or downstream systems, their goals, journey
  priorities, and independently verifiable outcomes. Link to REQ identifiers. -->

[TODO] Name actors, journeys, priorities, and the requirements that serve them.

## Exclusions

<!-- State excluded behavior and why; keep rejected implementation choices
  distinct from scope exclusions. Confirm "no exclusions apply" with the product owner
  if there are none. -->

[TODO] State scope exclusions and their reasons.

## Architecture

### Design Principles

<!-- Properties the design must satisfy, not implementation choices.
  Reference the REQ identifiers owning observable constraints. -->

[TODO] State the constraints on the design space.

### Alternatives Considered

<!-- Each rejected approach and why it was rejected. Rejecting an approach
  does not exclude a user capability; excluded behavior belongs in Exclusions. -->

[TODO] Record each rejected approach and the reason, or None with a reason.

## Interfaces

<!-- Describe this feature's exposed and consumed external contracts with
  enough detail to avoid incompatible implementations: inputs, outputs,
  validation, error outcomes, authorization, and compatibility as applicable.
  Public field definitions or precise versioned schema references are allowed
  as Contract material. No internal function or private class inventories.
  There is no fixed line limit. -->

[TODO] Define the external contracts and link their REQ identifiers.

## Workflow

<!-- From trigger to completion, mark product owner gates with a star (★). Include
  applicable failure, boundary, empty-input, concurrent-access, and state paths;
  link their requirements. Do not walk through internal code. -->

[TODO] Describe the feature's end-to-end behavior and relevant failure paths.

## Behavioral Requirements

<!-- One obligation per REQ, using SHALL or MUST and EARS where useful.
  Each AC-NNN.M belongs to REQ-NNN. Give concrete conditions and expected
  outcomes; include applicable success, rejection, boundary, and recovery cases.
  Verification names a test, inspection, or demonstration, as the new-task
  skill's Verification Methods define them. -->

### REQ-001 — Requirement title

[TODO] State one observable obligation.

#### AC-001.1 — Scenario title

- **Given:** [TODO] a concrete initial condition
- **When:** [TODO] a trigger or observation
- **Then:** [TODO] the required result

**Verification:** [TODO] Name the check and its pass/fail observation.

## Quality Requirements

<!-- Review security, privacy, accessibility, performance, reliability,
  compatibility, and recovery. Use the same REQ/AC structure for applicable
  guarantees, with agreed measurement conditions and thresholds. Do not invent
  targets. If none apply, state None with the reason instead of adding filler. -->

[TODO] Record applicable quality requirements or explain non-applicability.

## Configuration Requirements

<!-- For each setting: what and why, where it lives, constraints, and behavior
  when missing or invalid. Reference its requirement. Do not paste full config
  files. If no settings are involved, state None with a reason. -->

[TODO] Describe required settings and their default or error behavior.

## Assumptions and Dependencies

<!-- Record assumptions and their confirmation basis, external dependencies,
  and their failure implications. Confirm behavior/feasibility premises before
  approval. If there are none, say None and explain. -->

[TODO] Record confirmed assumptions and external dependencies.

## Success Criteria

<!-- Measurable overall outcomes linked to REQ identifiers; these complement,
  rather than replace, the per-requirement acceptance scenarios above. -->

[TODO] List the observable outcomes and how success will be measured.

## Implementation Order

<!-- Typically two to five coarse phases, each with an outcome and dependencies.
  Actual tasks and file-by-file changes are produced during decomposition. -->

[TODO] Describe coarse delivery phases and their dependencies.

## Open Questions

<!-- Resolve every question affecting behavior, contracts, acceptance, or
  feasibility before review, regardless of who can answer it. Only internal
  design investigations that cannot change approved behavior may be deferred;
  name an owner and resolution condition. State None when none remain. -->

[TODO] Resolve blockers; record only owned, bounded internal investigations.

## Amendment Log

<!-- Empty for a new draft. After approval, record date, change, reason,
  affected REQ/AC identifiers and tasks; bump the minor version on scope changes.
  Never renumber or reuse retired identifiers. A reconciliation verdict changes
  no scope and does not bump the version. -->
