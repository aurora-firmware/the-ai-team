---
name: feature-architecture
description: Decide how an approved spec or change-request is built — technology, protocol stacks and implementation design — and record it in the architecture documents and ADRs. Use when task breakdown starts on an approved feature spec or approved change-request and the Planner hands back with Next Owner Architect.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(new-adr), Skill(git-conventions)
effort: high
---

# Feature Architecture

**Ownership boundary:** this skill owns the *how* of one approved spec or change-request: the technology, protocol stacks and implementation design it is built with. The spec owns the *what* (behaviour, requirements, interfaces) and is never edited here. Task decomposition is `spec-breakdown`'s.

The main session runs this skill when the Planner stops at the start of `spec-breakdown` with Next Owner: Architect, and resumes the Planner with the result.

## Input Requirements

- **Approved work** — the path and ID of the approved feature spec or approved change-request, and its planning branch (`plan/<id>-…`).
- **Architecture documents** — the documents the project guidance names for architecture and technology, by default `docs/development/architecture.md` (the design of the solution components) and `docs/development/tech_stack.md` (the technology answers).
- **Decision records** — all ADRs in `{{project_dir}}/decisions/`; `accepted` ones are binding.
- **Coding guidelines** — the coding guidelines the project guidance names (default `docs/development/coding_guidelines.md`) and the project `AGENTS.md`.
- **S-000** — when it exists and is approved.

Return `BLOCKED`, deciding and committing nothing, when:

- the approved work or its planning branch is not given;
- the work is S-000, which has no feature architecture: its project bootstrap writes the first architecture documents, so the Planner skips this step.

## Procedure

### Step 1: Read the Work and the Architecture

Check out the planning branch, following the before-point Hygiene Check in `git-conventions`.
Read the approved spec or change-request, S-000, the architecture documents, every accepted ADR, and the coding guidelines. Read the project structure where the existing code shows how a component is built today.

If the architecture documents do not exist, create them at the location the project guidance names, or at the default location, and say so under `Obstacles Encountered`: the project bootstrap has not written them.

### Step 2: List What the Work Needs

Go through the requirements, interfaces, quality requirements and configuration requirements, and list each thing the work needs from the architecture. Add each Open Questions entry owned by the Architect: it is a need to decide, and the preference it names is weighed in Step 4, not taken as decided.

- the components that carry it, and how they connect;
- the technology each component uses: language, framework, libraries;
- protocols and formats between internal components;
- where and how data is stored;
- how a quality requirement (performance, security, reliability) is met.

A technology or format the spec fixes as an interface (Contract material that users or external systems see) is a given here, not a decision.

### Step 3: Classify Each Need

- **Covered** — an architecture document or an accepted ADR already decides it, and the decision meets the spec.
- **Gap** — nothing decides it yet.
- **Conflict** — an existing decision cannot meet a requirement of the work.

### Step 4: Decide the Gaps and Conflicts

For each gap, choose the option that meets the work's requirements and fits the existing architecture and coding guidelines. Prefer what the project already uses; a new framework for one feature needs a reason the existing one cannot meet.

- A **durable decision** — hard to reverse, or relied on by more than this work — is recorded with `new-adr`, status `accepted`. Provide `title`, and as `description` the spec or change-request ID, the need, the options considered and the reason for the choice. `new-adr` commits the ADR on the planning branch and runs its consistency review; list each correction that review routes to the Planner under `Spec findings`.
- A **local design choice** that only this work relies on is recorded in the architecture documents, without an ADR.

For each conflict, decide whether the existing decision changes. If it does, record the new decision with `new-adr`, `supersedes` naming the old ADR. If no decision can meet the requirement, escalate.

### Step 5: Update the Architecture Documents

Bring the architecture documents in line with every decision from Step 4: the component design and how components connect in the architecture document, and each technology answer, with its ADR ID when there is one, in the technology document. Describe the design; do not write task lists or file-by-file plans.

A spec or change-request that makes a technology choice or records implementation design is reported under `Spec findings` for the Planner; the decision is still made here.

### Step 6: Commit

Commit the architecture-document changes on the planning branch, following `git-conventions` (`docs(architecture): add <id> feature architecture`). When nothing changed, commit nothing and say so in the output.

## Escalation

The Architect is the escalation target, so this escalation goes to the product owner.
Return `ESCALATE` on first detection, without retrying, only when the decision requires changing the approved spec or the approved change-request intent:

- no technology or design can meet a requirement, and meeting it needs the approved spec or change-request to change;
- a decision would change approved behaviour or interfaces;
- a conflict needs an accepted ADR superseded, and the new ADR's consistency review finds that another approved spec would become untrue.

Every other decision is the Architect's, including one that brings a cost or an external service; record that consequence in the ADR.

Append the Escalation Request block and the Product Owner Escalation Report, both in the formats `escalation-review` owns:

```text
Problem: [the need that cannot be met]
Attempted: [the options considered and why each fails]
Failed because: [why no option meets the approved work]
Question: [the specific decision the product owner must make]
```

## Output Format

The verdict goes in `Result:`. Next Owner is `Planner` for `PASS` and `BLOCKED`, and `Product Owner` for `ESCALATE`.

| Result | When |
|---|---|
| `PASS` | Every need is covered or decided |
| `ESCALATE` | A need must go to the product owner (Escalation) |
| `BLOCKED` | An input is missing, or the work is S-000 |

```text
Work: <spec or change-request ID and path>
Architecture documents: <paths read and updated>

Covered:
- <need>: <architecture document section or ADR ID>

Decided:
- <need>: <decision> (<ADR ID and its consistency-review verdict, or architecture document section>)

Spec findings:
- <statement in the spec that makes a technology choice or records implementation design, or a correction an ADR's consistency review routed to the Planner; or "none">

Commit:
- <commit hashes on the planning branch, or "none: the existing architecture covers the work">
```

## Quality Criteria

- Every requirement, interface, quality requirement and configuration requirement of the work was checked against the architecture.
- Every need is covered, decided, or escalated; none is left for the Developer to choose.
- The architecture documents agree with every accepted ADR after the update.
