---
name: new-system-overview
description: Create the S-000 system overview spec, for a new project or when adopting an existing one into the ai-team process
argument-hint: "[optional: project name]"
allowed-tools: Read, Write, Bash, Skill(git-conventions)
---

# New System Overview

Create the S-000 system overview spec with `ai-team spec new --overview --json`, then fill its seven sections by interviewing the product owner. S-000 says what the project is, who it serves, and which components make it up. It is written in plain language for a reader who has never seen the project.

## Section contract

S-000 has seven sections, in this order:

1. **Purpose** — one short paragraph: what the project is and the outcome it exists to deliver.
2. **Users** — the users of the solution and in what situations, one line per kind of user, naming what each needs from it. The people and agents who develop the project are served by the development infrastructure and are not listed unless they also use the solution.
3. **Pain points** — the concrete problems those users have today that the project removes.
4. **Use cases** — the main things a user does with the system, each as one short scenario from the user's point of view and each tied to the pain point it removes.
5. **Solution overview** — how the system addresses the pain points, in a few paragraphs, without naming technologies.
6. **Components** — the parts the system is divided into. Each component entry gives its name, its owned responsibility (what it is for), its boundary (what it is not responsible for), and the other components it works with. Components are split into the Solution and Development infrastructure groups (below).
7. **Project exclusions** — what the project deliberately does not do, each with a one-line reason.

S-000 contains no technology choices, interface definitions, configuration, implementation order, or per-component status. Those belong in feature specs, ADRs, and the tracker.

**What a component is.** A component is a part of the software solution, or something that affects the solution's use, delivery or deployment. A component can be software, documentation (internal or for end users), delivery and deployment (pipelines, scripts), or tooling (development environment, debugging interfaces, test harnesses). Each component passes three checks: it serves at least one use case, or, in the infrastructure group, affects the solution's use, delivery or deployment; one spec could own its contract; and its boundary would hold if the implementation were reorganised.

**Boundary rule:** S-000 owns the decomposition — which components exist and what each is for. A spec owns the contract of one component or feature. A spec's Purpose names the S-000 component it covers.

**Component groups.** Components fall into two groups, written as `### Solution` and `### Development infrastructure` subsections of Components; the seven top-level sections and their order do not change.

### Solution

The software delivered to the end user that removes the pain points.

### Development infrastructure

Everything the project needs to build, check, document and deliver the solution; it is not delivered to the end user. Each infrastructure component also has a **Decisions needed** field: the questions that must be answered before development starts, such as the language and version, how the environment is reproduced, the test harness, the continuous-integration service, and where decisions are recorded. S-000 asks technology questions and never answers them; the answers belong in the project's internal development documentation, later specs and ADRs.


## Input Requirements

- `project name` — optional; use `$ARGUMENTS` when it is the only input, otherwise ask the product owner.
- Whether the project already has specs, ADRs, docs, or code. If it does, follow **Brownfield adoption** (below) for step 4.

## Procedure

1. Check whether an S-000 already exists: run `ai-team list specs`.
   If S-000 is listed, stop. Tell the product owner it exists and offer to amend it instead; do not create a second overview.

2. Open the planning branch.
   Follow **Opening a Planning Branch** in the `git-conventions` skill, running the command in step 3 as its allocation step.

3. Run `ai-team spec new --overview --json` and parse the response for `id` (S-000) and `path`.

4. Fill the seven sections in the order the **Section contract** (above) gives: Purpose, Users, Pain points, Use cases, Solution overview, Components, Project exclusions.
   Interview the product owner for:
   - the purpose of the project and the outcome it delivers;
   - who the users are and what each needs;
   - the concrete pain points those users have today;
   - the main use cases, each as one short scenario from the user's point of view;
   - the split into solution and development-infrastructure components, with each component's responsibility, boundary, and collaborators;
   - each development-infrastructure component's decisions needed: the technology and tooling questions that must be answered before development starts (record the questions, not the answers).
   Check each component against the three checks in the Section contract. Write the Solution overview and Project exclusions from those answers, asking the product owner to confirm the exclusions. Leave anything still unanswered marked `[TODO]`.

5. Run the **pre-submission checklist** (below). Fix every unchecked item.

6. Inspect the draft for product-owner-answerable `[TODO]` markers. If any remain, report the blocker and stop instead of handing the draft on.

7. Commit the draft on the planning branch (`docs(specs): add S-000 draft`). Commit every later revision on the same branch, never on `{{integration_branch}}`.

8. Hand the draft to the Architect for an Architecture Consistency Review (Next Owner: Architect). The Architect checks it against existing approved specs and accepted ADRs and returns findings without amending the draft. Revise on those findings until the Architect and Planner agree it is consistent.

9. Present the revised draft to the product owner for Gate 1 approval. S-000 is not approved until the product owner says so. When the product owner approves, follow **After Gate 1** (below).

## Pre-submission checklist

- [ ] **Plain language.** A reader who has never seen the project can follow it.
- [ ] **No technology or interfaces.** No technology choices, interface definitions, configuration, implementation order, or per-component status.
- [ ] **Every use case is tied to a pain point.** Each use case removes at least one named pain point.
- [ ] **Every component has a boundary and a responsibility.** Each states what it is for, what it is not responsible for, and which components it works with.
- [ ] **Components are split into Solution and Development infrastructure.** Each component sits in one group and passes the three component checks.
- [ ] **Every infrastructure component lists its Decisions needed.** Each lists the questions to answer before development starts and answers none of them.
- [ ] **All seven sections are present, in order.**
- [ ] **No `[TODO]` markers remain** that the product owner can answer.

## Brownfield adoption

Use this path when the project already has specs, ADRs, docs, or code. The goal is to unify the project towards the ai-team process without rewriting what is already approved.

1. Read the approved specs, accepted ADRs, and project docs first.
2. Inspect the code only to learn what exists and what it does for users. Do not infer requirements from implementation details, and derive the components from the use cases and the existing material, never from the code or folder layout. Apply the three component checks (Section contract) to every candidate component.
3. Draft S-000 in plain language through the same procedure above (steps 1 to 6), using what you learned to prefill the interview and asking the product owner to confirm or correct it.
4. Compare the draft with the existing specs and ADRs. Report every overlap, gap, and disagreement as a finding in your handoff, naming the spec or ADR concerned. Examples: two specs covering one component, a component with no spec, a spec whose scope contradicts the component split.
5. Never amend an approved spec yourself to resolve a finding. Amending an approved spec is a separate change that goes through its own Gate 1 approval; the product owner decides which side of each disagreement changes.
6. Go through the same Architect review and product owner Gate 1 as a greenfield S-000 (steps 8 and 9), then **After Gate 1**.

## After Gate 1

When the product owner approves S-000 at Gate 1, direct the Planner to do the following, in order:

1. Set S-000 to `approved` (the `status` field in its frontmatter) and commit that change on the planning branch.
2. Merge the planning branch into `{{integration_branch}}` with `--no-ff`, then delete it with `git branch -d`. S-000's own planning branch does not wait for Gate 2 (only its bootstrap task plan does), so this merge follows Gate 1; the `git-conventions` skill owns this S-000 exception.
3. Brownfield only: if the findings from the **Brownfield adoption** comparison call for changes to approved specs or ADRs, propose a change request from them with the `change-request` skill, one finding per entry. The product owner decides which side of each disagreement changes; the change request goes through its own approval.
4. Start the project bootstrap: run `spec-breakdown` on S-000. It plans only the bootstrap tasks for the development-infrastructure components and their Decisions needed.
