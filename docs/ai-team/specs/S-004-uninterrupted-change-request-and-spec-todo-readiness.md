---
title: Uninterrupted Change Request and Spec TODO Readiness
version: '0.2'
status: approved  # draft | review | approved | superseded
created: '2026-07-05'
author: planner
id: S-004
---

# Uninterrupted Change Request and Spec TODO Readiness

<!--
This spec describes requirements and measurable criteria in prose.
It is not the implementation. Do not paste full configuration files,
build manifests, or implementation code into the sections below.
Concrete code belongs in the tasks the spec-breakdown skill produces
and in the Developer's output. See the Spec Authoring Guide for the
content contract this template implements.
-->

## Purpose

The change-request path currently creates an artifact and reports the next owner
instead of continuing through the process steps that are already defined for
change-request intake. That leaves humans to manually resume Architect review
and Planner iteration, and it also allows `[TODO]` markers in change-requests or
new specs to reach review even when the missing information is human intent.
When this work is complete, source process guidance and generated skill
scaffolds require the Planner to resolve each human-answerable TODO
interactively before review, then continue change-request processing through
architecture consistency review and Planner iteration without unnecessary
interruptions. Success is observable when the generated brainstorm and
change-request skills contain this flow and the process docs describe the same
handoff and stopping conditions.

## Exclusions

<!-- For every alternative rejected during brainstorm, and every scope-expanding
  question the human said "no" to, record an explicit exclusion with the reason.
  Almost every spec has at least one. "No exclusions apply" should be rare and
  should follow an explicit human confirmation. -->

What this specification explicitly does NOT cover:

- **New reusable TODO-resolution skill.** The shared rule belongs in the
  process contract and the affected skill procedures. Creating a separate skill
  would add a new process component for behavior currently needed by only
  brainstorm and change-request.
- **Editing repo-local exported skill copies.** Repository-root tool folders such as
  `.claude/` are not the source of truth for framework
  behavior. This work updates source process documents and source skill
  definitions, then regenerates packaged scaffolds.
- **Changing the autonomous development loop.** This work ends at the point
  where accepted change-requests can proceed to amendments, task breakdown, and
  existing downstream gates. Development-loop execution semantics remain
  unchanged.
- **Skipping human approval for intended scope changes.** The change-request may
  continue automatically after the human approves it, but findings that would
  change the approved human intent must return to the human.

Alternatives considered:

- **Skill-local orchestration only.** Rejected because it would make the skill
  bodies carry process behavior that the workflow and gate docs do not state.
  That risks future drift between the process contract and generated skills.
- **Process-first state model with skill procedures implementing it.** Chosen
  because the human specifically needs process docs, source skills, and
  generated scaffolds to stay consistent while avoiding edits to local exported
  skill copies.
- **New reusable artifact-readiness procedure or skill.** Rejected for this
  iteration because it introduces a new abstraction before more than two skills
  need it.

## Architecture

### Design Principles

- **Human intent must be complete before review.** A spec or change-request
  cannot be handed to Architect review or approval while it contains
  human-answerable `[TODO]` markers.
- **Change-request approval establishes the intended change.** After the human
  approves a TODO-free change-request, downstream consistency work treats that
  change-request as the new source of intended scope unless a finding would
  modify the approved intent itself.
- **Planner and Architect ownership remains separate.** The Architect reports
  consistency findings; the Planner resolves spec amendments and draft-spec
  revisions.
- **Automation continues until a real human decision is needed.** The
  change-request skill must continue through architecture consistency review and
  Planner iteration when the next steps are procedural, and stop only for
  missing human intent, approval, or a finding that would change the approved
  request.
- **Source definitions drive generated behavior.** Framework behavior changes
  must be made in process docs and source skill definitions, then reflected in
  generated scaffolds.

### System Diagram

<!-- ASCII boxes and arrows. One screen wide. Components labelled. Show data
  flow, not the call graph. Class diagrams of internal classes do not belong
  here. -->

```
Human change request
  |
  v
Planner creates CR artifact
  |
  v
Planner resolves each [TODO] with human, one by one
  |
  v
★ Human approves TODO-free CR
  |
  v
Architect consistency review
  |
  +-- procedural consistency findings --> Planner amends affected specs/tasks
  |                                      and resubmits as needed
  |
  +-- finding changes approved intent --> Human revises or rejects CR
  |
  v
Accepted CR continues to existing task breakdown and Gate 2 flow
```

### Responsibility Separation

<!-- One row per component. Stay at the interface level — no method signatures
  or attribute lists. -->

| Component | Responsibility | Notes |
|---|---|---|
| Workflow and gate docs | Define the artifact-readiness rule, CR approval semantics, and handoff stopping conditions. | Process docs are the contract source that skills must implement. |
| Brainstorm source skill | Creates specs through the existing interactive flow and resolves any remaining `[TODO]` markers before moving the spec to review or Architect consistency review. | Consumes human answers one TODO at a time with local context. |
| Change-request source skill | Creates CRs, resolves TODOs, gets human approval, continues through architecture consistency review, and routes Planner-owned fixes without stopping unnecessarily. | Stops for human only when intent is missing, approval is needed, or approved intent must change. |
| Architecture consistency review source skill | Reports consistency findings with routing that honors approved CR intent as authoritative for Planner-owned amendments. | Does not edit specs directly. |
| Generated scaffolds | Provide the same behavior to initialized projects for supported agent runtimes. | Generated from source definitions rather than edited by hand. |

## Components

<!-- One short block per component, three lines max:
  - Purpose: one sentence — what it does.
  - Estimated size: small / medium / large, or rough effort.
  - Interfaces: exposed and consumed, named at the interface level.
  No function lists. No field lists. -->

### Component 1: Process Documentation Contract

**Purpose:** Records the TODO-readiness rule and uninterrupted CR flow in the
workflow and gate descriptions.
**Estimated size:** Small.
**Interfaces:** `ai-process/processes/workflow-overview.md`,
`ai-process/processes/quality-gates.md`, generated skill behavior.

### Component 2: Brainstorm Spec Readiness

**Purpose:** Ensures specs created by brainstorm do not advance to review with
human-answerable TODOs.
**Estimated size:** Small.
**Interfaces:** Brainstorm skill source, new-spec output, human clarification
dialogue, Architect consistency review handoff.

### Component 3: Change-Request Continuation

**Purpose:** Turns change-request intake into a continuous flow from artifact
creation through approval, consistency review, and Planner-owned corrections.
**Estimated size:** Medium.
**Interfaces:** Change-request skill source, architecture consistency review
skill, approved specs, accepted ADRs, task breakdown flow.

### Component 4: Scaffold Synchronization

**Purpose:** Regenerates exported scaffolds from source after
the process and source skills change.
**Estimated size:** Small.
**Interfaces:** Skill source tree, sync script, generated scaffold tree.

## Workflow

<!-- End-to-end flow from trigger to completion. Each step is a sentence or
  short phrase. Mark human gates with ★. Show error paths only when a failure
  mode is interesting. -->

```
Spec path:

Human requests feature
  ↓
Planner brainstorms and confirms direction
  ↓
Planner creates spec
  ↓
Planner scans for [TODO] markers
  ↓
Human-answerable TODO found -> ask one contextual question and update spec
  ↓
No [TODO] markers remain
  ↓
Architect consistency review
  ↓
★ Gate 1 spec approval
```

```
Change-request path:

Human requests smaller change
  ↓
Planner creates change-request
  ↓
Planner scans for [TODO] markers
  ↓
Human-answerable TODO found -> ask one contextual question and update CR
  ↓
No [TODO] markers remain
  ↓
★ Human approves CR as intended change
  ↓
Architect consistency review
  ↓
Planner resolves spec amendments and consistency fixes using the approved CR as
authoritative intent
  ↓
Finding would alter approved CR intent -> stop for human decision
  ↓
Accepted CR proceeds to existing task breakdown and Gate 2 flow
```

## Configuration Requirements

- **What must exist:** A source-of-truth authoring path for skill behavior.
  **Where it lives:** `cli/src/ai_team/init/sources/skills/` and the process
  docs under `ai-process/processes/`.
  **Constraints:** Repository-root tool folders such as `.claude/` are not
  edited to change framework behavior.
  **Missing-value behaviour:** If source skill definitions or process docs
  cannot be updated consistently, the work is incomplete.

- **What must exist:** Regenerated skill scaffolds after source changes.
  **Where it lives:** `cli/src/ai_team/init/scaffolds/`.
  **Constraints:** Generated skill outputs must reflect the
  source definitions after synchronization.
  **Missing-value behaviour:** If scaffolds are stale relative to sources, the
  change fails verification.

- **What must exist:** A documented marker for unresolved artifact details.
  **Where it lives:** Artifact bodies that use `[TODO]` to mark unresolved
  information.
  **Constraints:** Human-answerable TODOs are resolved one at a time with
  relevant context before review or approval handoff.
  **Missing-value behaviour:** If a TODO cannot be resolved because it changes
  human intent, the process stops for human decision instead of continuing.

## Implementation Order

<!-- Coarse phases (typically two to five). Each phase delivers an observable
  outcome. A phase is NOT a task — the spec-breakdown skill produces the actual
  tasks from these phases. -->

| Phase | What | Depends On |
|---|---|---|
| 1 | Update workflow and quality-gate documentation with TODO readiness, CR approval semantics, and continuation/stopping rules. | Nothing |
| 2 | Update source brainstorm, change-request, and architecture consistency review skill bodies to implement the documented process. | Phase 1 |
| 3 | Regenerate skill scaffolds from the updated sources and verify they match the source behavior. | Phase 2 |
| 4 | Run repository checks relevant to process/source/scaffold consistency. | Phase 3 |

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-20 | The exclusion and configuration requirement on repo-local exported skill copies also name `.agents/`. Wording only. Driven by CR-002. | Codex skills are now exported to `.agents/skills/`. | None in flight |
| 2026-10-25 | Repo-local tool folders and the generated scaffolds no longer name Codex. Wording only. Driven by CR-007. | Claude is the only export target (ADR-003). | None in flight |
