---
name: feature-architecture
description: Decide how an approved spec or change-request is built — technology, protocol stacks and implementation design — and record it in the architecture documents and ADRs. Use when task breakdown starts on an approved feature spec or approved change-request.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(new-adr), Skill(git-conventions)
effort: high
---

# Feature Architecture

**Ownership boundary:** this skill owns the *how* of one approved spec or change-request: the technology, protocol stacks and implementation design it is built with. The spec owns the *what* (behaviour, requirements, interfaces) and is never edited here. Task decomposition is owned by `spec-breakdown`; Gate 2 checks the plan against the result of this skill.

## Input Requirements

- **Approved work** — the path and ID of the approved feature spec or approved change-request, and its planning branch (`plan/<id>-…`).
- **Architecture documents** — the documents the project guidance names for architecture and technology, by default `docs/development/architecture.md` (the design of the solution components) and `docs/development/tech_stack.md` (the technology answers).
- **Decision records** — all ADRs in `{{project_dir}}/decisions/`; `accepted` ones are binding.
- **Coding guidelines** — `{{project_dir}}/docs/coding_guidelines.md` and the project `AGENTS.md`.
- **S-000** — when it exists and is approved.

Return `BLOCKED` when the approved work or its planning branch is not provided. Return `BLOCKED` for S-000: its project bootstrap writes the first architecture documents, and it has no feature architecture.

## Procedure

### Step 1: Read the Work and the Architecture

Check out the planning branch, following the before-point Workspace Hygiene check in `git-conventions`.
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

For each need, decide one of:

- **Covered** — an architecture document or an accepted ADR already decides it, and the decision meets the spec.
- **Gap** — nothing decides it yet.
- **Conflict** — an existing decision cannot meet a requirement of the work.

### Step 4: Decide the Gaps and Conflicts

For each gap, choose the option that meets the work's requirements and fits the existing architecture and coding guidelines. Prefer what the project already uses.

- A **durable decision** — hard to reverse, or relied on by more than this work — is recorded with `new-adr`, status `accepted`. Provide `title`, and as `description` the spec or change-request ID, the need, the options considered and the reason for the choice.
- A **local design choice** that only this work relies on is recorded in the architecture documents, without an ADR.

For each conflict, decide whether the existing decision changes. If it does, record the new decision with `new-adr`, `supersedes` naming the old ADR. If no decision can meet the requirement, escalate.

### Step 5: Update the Architecture Documents

Bring the architecture documents in line with every decision from Step 4: the component design and how components connect in the architecture document, and each technology answer, with its ADR ID when there is one, in the technology document. Describe the design; do not write task lists or file-by-file plans, which are `spec-breakdown`'s output.

Never edit the spec or change-request. A spec that makes a technology choice or records implementation design is reported to the caller as a finding for the Planner; the decision is still made here.

### Step 6: Commit

Commit the ADRs and the architecture-document changes on the planning branch, following `git-conventions` (`docs(architecture): add <id> feature architecture`). When every need was covered and nothing changed, commit nothing and say so in the output.

## Escalation

Return `ESCALATE` on first detection, without retrying, only when the decision requires changing an approved specification or the approved change-request intent:

- no technology or design can meet a requirement, and meeting it needs the approved spec or change-request to change;
- a decision would change approved behaviour or interfaces;
- a conflict needs an accepted ADR superseded and the change would make another approved spec untrue.

Every other decision is the Architect's, including one that brings a cost or an external service; record that consequence in the ADR.

```text
Problem: [what went wrong]
Attempted: [the options considered and why each fails]
Failed because: [why no option meets the approved work]
Question: [the specific decision the product owner must make]
```

## Output Format

The verdict goes in the Architect envelope's `Result:` line: `PASS` when every need is covered or decided, `ESCALATE` when a need must go to the product owner, `BLOCKED` when an input is missing.

```text
Work: <spec or change-request ID and path>
Architecture documents: <paths read and updated>

Covered:
- <need>: <architecture document section or ADR ID>

Decided:
- <need>: <decision> (<ADR ID, or architecture document section>)

Spec findings:
- <statement in the spec that makes a technology choice or records implementation design, or "none">

Commit:
- <commit hash on the planning branch, or "none: the existing architecture covers the work">
```

## Quality Criteria

- Every requirement, interface, quality requirement and configuration requirement of the work was checked against the architecture.
- Every need is covered, decided, or escalated; none is left for the Developer to choose.
- Each durable decision has an accepted ADR; each local choice is in the architecture documents.
- The architecture documents agree with every accepted ADR after the update.
- The spec and change-request were not edited.

## Common Pitfalls

- **Leaving the choice to the Developer.** A technology nobody decided gets decided in a task branch, where no one reviews it as a decision.
- **Writing the decision into the spec.** The spec says what; the architecture documents and ADRs say how. Report a spec that names a technology, do not copy it.
- **Recording a local choice as an ADR.** ADRs are for decisions others rely on; a one-feature design detail belongs in the architecture documents.
- **Planning tasks.** Components and their connections are design; which files each task touches is the Planner's.
- **Ignoring what the project already uses.** A new framework for one feature needs a reason the existing one cannot meet.
