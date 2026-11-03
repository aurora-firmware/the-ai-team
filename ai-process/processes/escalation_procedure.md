# Escalation Procedure

## Overview

Escalation is a two-stage safety net that prevents roles from spinning indefinitely on unsolvable problems.
It separates **role-level retries** (the role tries to fix the problem itself) from **escalation** (asking for outside help).

```
Role encounters problem
    ↓
Phase 1: Role Self-Recovery (role retries within its own threshold)
    ↓ threshold exceeded
Phase 2: Escalation Chain
    ├── Step 1: Architect Consultation (one attempt)
    │       ├── Resolved → Role continues
    │       └── Not resolved ↓
    └── Step 2: Product Owner Escalation
                The product owner decides next action
```

## Phase 1: Role Self-Recovery

Before escalating, every role must make a reasonable effort to solve the problem on its own.
Each role's skills specify its retry threshold.
These retries happen **before** entering the escalation chain.

| Role | Self-recovery threshold |
|-------|------------------------|
| Developer | Three consecutive failed attempts to make tests pass |
| Reviewer | One review cycle for ESCALATE-worthy issues — if the code has fundamental design problems that no amount of Developer fixes can address, issue ESCALATE immediately rather than FAIL. For ordinary quality issues, issue FAIL; the Development Loop allows up to three total review cycles before forcing escalation |
| Integrator | One merge attempt — if a post-merge regression cannot be attributed to the source branch just merged, escalate immediately |

Once the role exceeds its threshold, it stops retrying and enters Phase 2.

## Phase 2: Escalation Chain

### Step 1: Architect Consultation

- **Who:** The Architect.
- **How:** The blocked role sends a structured request describing the problem, what was attempted, and why it failed.
- **Scope:** The Architect analyses the problem, foresees impact on other tasks and the broader codebase, and — within the bounds of the approved spec — issues directives or correction requests. The Architect may recommend task-scope adjustments, clarifying tasks, or task-description amendments, but the Planner owns task-plan edits. The Architect does not modify implementation or test files.
- **Rounds:** The Architect provides one consultation response per escalation.
- **Escalation trigger:** The Architect escalates to the product owner only when: (a) the problem requires changing an approved specification, or (b) the Architect cannot resolve it after full analysis.

**Architect request format:**
```
Problem: [What went wrong]
Attempted: [What the role tried, including number of retries]
Failed because: [Why it did not work]
Question: [Specific question for the Architect]
```

### Step 2: Product Owner Escalation

- **Who:** The product owner.
- **How:** A notification is sent with the full context (original task, role's self-recovery attempts, Architect's analysis, and a precise statement of why product owner input is required).
- **When reached:** Only when a spec change is needed, or the Architect has exhausted its analysis and cannot resolve the issue.
- **Outcome:** The product owner chooses one of the following actions:

| Product owner decision | What happens next | Role responsible |
|---------------|-------------------|-------------------|
| Revise the spec | The Planner amends the spec on an [amendment planning branch](../guidelines/git_conventions.md#amendment-planning-branch), adds an entry to the spec's Amendment Log section, and identifies affected tasks. The Architect runs the [Architecture Consistency Review](quality_gates.md#architecture-consistency-review) (the `architecture-consistency-review` skill) on the amended spec and routes any further amendments the change exposes; on PASS the Planner merges the branch. The loop adds a note to each affected `in-progress` task referencing the amendment. The stopped item then resumes. | Planner and Architect, then the loop |
| Modify the task | The product owner updates the task file directly with new or changed requirements, or the Planner raises a change-request. The stopped item then resumes, and the Developer re-reads the task. | Product Owner, or Planner through a change-request |
| Provide guidance | The guidance is recorded in the work item file. The stopped item then resumes, and the blocked role applies the guidance. | Blocked role |
| Defer the work | The item is `blocked` with the reason noted: the loop already blocked it when it stopped, so it stays `blocked`. The spec issue is not addressed now, and no loop resumes the item until it is unblocked. | Product Owner |

**Resuming the stopped item.** A task stopped by escalation is `blocked`. Once the decision is applied, `ai-team task unblock` sets it back to `in-progress`. A bug stopped by escalation stays `in-progress`; only a deferred bug is `blocked`, and `ai-team bug unblock` sets it back to `in-progress` once the blocker is resolved. At its next start, the loop resumes every `in-progress` item on its existing branch before it picks new work (see the [workflow overview](workflow_overview.md#when-the-development-loop-stops)); the product owner does not restart the item by hand.

## When to Escalate

A role enters the escalation chain when it **cannot complete its assigned task** after exhausting its self-recovery threshold. Specific triggers:

- **Developer:** Tests fail repeatedly (3 attempts). Requirements are ambiguous or untestable. Conflicting constraints make the task impossible as specified.
- **Reviewer:** Code has fundamental design issues that cannot be fixed without changing the specification.
- **Integrator:** Merge conflicts that cannot be resolved without understanding both sides' intent. Integration tests fail and the regression cannot be attributed to the source branch just merged.

## Rules

1. **Retry first, then escalate** — roles must exhaust their self-recovery threshold before entering the escalation chain. Once in the chain, the Architect gets one consultation attempt. If that fails, escalate to the product owner immediately. Do not loop.
2. **Always include context** — every escalation must carry the full chain of what was attempted. The receiving party should never need to ask "what did you try?"
3. **Do not skip steps** — always consult the Architect before escalating to the product owner, unless the Architect is the one that is stuck.
4. **No silent failures** — if a role is stuck, it must escalate. Doing nothing is not acceptable.
