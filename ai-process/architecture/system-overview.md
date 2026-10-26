---
title: "AI Team System Overview"
status: approved
created: 2026-03-10
---

# AI Team System Overview

## What This Defines

This document describes the architecture of an AI team — how roles are organized, how work flows between them, and how quality is maintained. It is not about a specific software product; it is the operating model that any AI-developed project can adopt.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                           AI TEAM                           │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ PLANNER  │  │  ARCHITECT   │  │    INTEGRATOR      │     │
│  │          │  │              │  │                    │     │
│  │ creative │  │ structural   │  │ merge + test       │     │
│  │ + struct │  │ + gate eval  │  │ + conflict resolve │     │
│  └────┬─────┘  └──────┬───────┘  └──────────┬─────────┘     │
│       │               │                     │               │
│       ↓               ↓ (on demand)         ↑               │
│  ┌──────────────────────────────────────────┤               │
│  │         EXECUTION POOL                   │               │
│  │                                          │               │
│  │  ┌─────────────┐  ┌─────────────┐        │               │
│  │  │  DEVELOPER  │  │  DEVELOPER  │  ...   │               │
│  │  │   (TDD)     │  │   (TDD)     │        │               │
│  │  └──────┬──────┘  └──────┬──────┘        │               │
│  │         ↓                ↓               │               │
│  │  ┌─────────────┐  ┌─────────────┐        │               │
│  │  │  REVIEWER   │  │  REVIEWER   │        │               │
│  │  └──────┬──────┘  └──────┬──────┘        │               │
│  │         └────────────────┴───────────────┘               │
│  └──────────────────────────────────────────────────────────┘
│                                                             │
│  ★ GATES: spec, task plan, review, integration, final       │
└─────────────────────────────────────────────────────────────┘
```

## Layers

### Planning Layer

**Roles:** Planner, Architect.
**Purpose:** Transform a feature request into an approved specification and a set of executable tasks.
**Key principle:** Separate creative exploration (brainstorming) from structured decomposition (task breakdown).

### Process Layer

**Processes:** Development Loop and Bug-Fix Loop.
**Purpose:** Drive the full Developer → Reviewer loop autonomously across pending tasks and open bugs.
**Key principle:** The product owner starts the appropriate loop when its queue is ready: the development loop after Gate 2 passes, or the bug-fix loop when open bugs need resolution.
The loop runs until the queue is empty or a hard stop is hit (blocked task, unresolved bug, escalation).
No product owner input is required between work items.

### Execution Layer

**Roles:** Developer, Reviewer.
**Purpose:** Produce working, tested, reviewed code for each task.
**Key principle:** Tasks are atomic and independent. The Developer writes both tests and production code using the test-driven implementation procedure. The Reviewer evaluates spec compliance and code quality. Both are assigned and sequenced by the Development Loop process.
For bug fixes, the Developer follows a diagnosis-first debugging procedure before changing production code, and the Reviewer checks the diagnostic evidence as part of review.

### Integration Layer

**Procedure:** Integrate.
**Role:** Integrator (conflict resolution and manual merges into `dev-agent` or preserved task branches).
**Purpose:** Merge completed work, run integration tests, and resolve conflicts.
**Key principle:** Merge in dependency order. Test the source branch before the merge and the destination branch after it. Revert and file bugs on failure.

### Oversight Layer

**Role:** Product Owner.
**Purpose:** Approve high-impact decisions at product-owner-controlled gates.
**Key principle:** The product owner stays in the loop without becoming a bottleneck. Gate 1 and Gate 5 are mandatory product owner gates.

## Information Flow

> Note: the Development Loop is a process, not a role. The table tracks control/data flow between roles and procedures.

| From | To | What |
|---|---|---|
| Product Owner | Planner | Feature request or problem description |
| Planner | Product Owner | Specification for approval |
| Planner | Local tracker | Tasks created as `planned`, set to `pending` after the planning branch merges; follow-up tasks from spec-truth reconciliation are created `pending` (ADR-002) |
| Planner | Architect | Gate 2 evaluation request |
| Planner | Architect | Created/changed spec or change-request for Architecture Consistency Review (before Gate 1, or before change-request amendments are applied) |
| Architect | Planner | Consistency findings on a created/changed spec or change-request |
| Architect | Development Loop | Validated task plan — ready to run |
| Product Owner | Development Loop | Start signal after Gate 2 passes |
| Development Loop | Developer | Task assignment |
| Developer | Development Loop | Completion signal; Work Log entry in task file |
| Development Loop | Reviewer | Review request |
| Reviewer | Development Loop | Verdict in task file (`PASS`/`FAIL`/`ESCALATE`) |
| Development Loop | Developer | Feedback routing (on `FAIL`) |
| Development Loop | Integrate | Merge request (on `PASS`) |
| Integrate | Local tracker | State transitions (`in-progress` → `completed`) |
| Development Loop | Local tracker | State transitions (`in-progress` → `blocked`) |
| Development Loop | Product Owner | Stop notification (queue empty, blocked, or escalation) |
| Any role | Architect | Escalation request |
| Architect | Requesting role | Advisory guidance |
| Architect | Product Owner | Escalation (if architect cannot resolve) |
| Product Owner | `main` | Final merge from `dev-agent` after Gate 5 sign-off |

## Design Decisions

1. **File-based task tracking** — roles read and write Markdown files natively. No external databases or issue trackers required.
2. **Lifecycle state machines** — task, bug, and gate state transitions are defined in the workflow overview and referenced by the rest of the process.
3. **Separation of roles and procedures** — roles define who acts; procedures define how repeatable work is performed. Procedures can be composed and reused across roles. Each document type is authoritative for a distinct domain; see "Content Boundaries" below.
4. **Five gates** — Gate 1 (spec approval), Gate 2 (task plan preflight), Gate 3 (code review), Gate 4 (integration tests), and Gate 5 (final merge sign-off). Gate 1 and Gate 5 are product owner gates; Gate 2 through Gate 4 are automated role or procedure gates.
5. **Process-driven orchestration** — the Developer → Reviewer loop is driven by the Development Loop process. A process is the right primitive when control flow is deterministic and product-owner-started.
6. **Spec layer vs. export layer** — `ai-process/` is the specification layer for the rules the AI team follows. It is not exported by `ai-team init`. The CLI package owns what gets exported to adopting projects; the authoritative sources for exported agents, skills, and templates live in `cli/src/ai_team/init/sources/`. The export layer writes Claude agents and skills only (`.claude/agents/`, `.claude/skills/`). The `.claude/` folder in this meta-repository is local project configuration that implements the rules defined in `ai-process/`; it is not the product source for init exports.

## Content Boundaries

Three document types in the AI team framework each have a distinct authority domain. Each type is the source of truth for its domain; placing information in the wrong type causes redundancy and drift.

### Component map (`ai-process/architecture/component-map.md`)

Authoritative for **structure**: which roles, processes, procedures, and gates exist; their purpose; lifecycle ownership; and the high-level data flow between them.
When a component is added, removed, or reassigned, the component map is updated first.

### Role implementation files (`.claude/agents/`)

Authoritative for **identity and constraints**: who the role is, which procedures it has access to, what it can decide alone, when it must stop and escalate, and what "done" looks like for its output.

**Must not contain** step-by-step procedures, numbered workflows, or conditional branching logic — those belong in a procedure implementation.

A role implementation file may include an "Interaction Pattern" section describing its upstream and downstream neighbours; this should stay consistent with the component map and the procedure implementation files that define the actual routing logic.

### Procedure implementation files (`.claude/skills/*/SKILL.md`)

Authoritative for **procedures**: the exact steps of repeatable work, the input/output contract at each step, which role is assigned when, and what happens on `PASS`/`FAIL`/`ESCALATE` verdicts.

**Must not contain** role identity, decision authority, scope boundaries, or structural mapping — those belong in the role implementation file or component map.

### Keeping them consistent

The three document types cover different domains and should not conflict. When they do conflict, it means one was not updated when a change was made. Resolve by identifying which is correct for its own domain and bringing the others into alignment.
