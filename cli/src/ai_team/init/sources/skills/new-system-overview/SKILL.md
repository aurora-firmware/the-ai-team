---
name: new-system-overview
description: Create the S-000 system overview spec, for a new project or when adopting an existing one into the ai-team process
argument-hint: "[optional: project name]"
allowed-tools: Read, Write, Bash, Skill(git-conventions)
---

# New System Overview

Create the S-000 system overview spec with `ai-team spec new --overview --json`, interview the product owner, and only then fill its seven sections from their answers. S-000 says what the project is, who it serves, and which components make it up. It is written in plain language for a reader who has never seen the project.

## Section contract

S-000 has seven sections, in this order:

1. **Purpose** — one short paragraph: what the project is and the outcome it exists to deliver.
2. **Users** — the users of the solution and in what situations, one line per kind of user, naming what each needs from it. The people and agents who develop the project are served by the development infrastructure and are not listed unless they also use the solution.
3. **Pain points** — the concrete problems those users have today that the project removes.
4. **Use cases** — the main things a user does with the system, each as one short scenario from the user's point of view and each tied to the pain point it removes.
5. **Solution overview** — how the system addresses the pain points, in a few paragraphs, without naming technologies.
6. **Components** — the parts the system is divided into. Each component entry gives its name, its owned responsibility (what it is for), its boundary (what it is not responsible for), and the other components it works with. Components are split into the Solution and Development infrastructure groups (below).
7. **Project exclusions** — what the project deliberately does not do, each with a one-line reason.

S-000 contains no technology choices, interface definitions, configuration, implementation order, or per-component status. Interface definitions, configuration, and implementation order belong in feature specs; technology choices in the architecture documents and ADRs; per-component status in the tracker.

**What a component is.** A component is a part of the software solution, or something that affects the solution's use, delivery or deployment. A component can be software, documentation (internal or for end users), delivery and deployment (pipelines, scripts), or tooling (development environment, debugging interfaces, test harnesses). Each component passes three checks: it serves at least one use case, or, in the infrastructure group, affects the solution's use, delivery or deployment; one spec could own its contract; and its boundary would hold if the implementation were reorganised.

**Boundary rule:** S-000 owns the decomposition — which components exist and what each is for. A spec owns the contract of one component or feature. A spec's Purpose names the S-000 component it covers.

**Component groups.** Components fall into two groups, written as `### Solution` and `### Development infrastructure` subsections of Components; the seven top-level sections and their order do not change.

### Solution

The software delivered to the end user that removes the pain points.

### Development infrastructure

Everything the project needs to build, check, document and deliver the solution; it is not delivered to the end user. Each infrastructure component also has a **Decisions needed** field: the questions that must be answered before development starts, such as the language and version, how the environment is reproduced, the test harness, the continuous-integration service, and where decisions are recorded. S-000 asks technology questions and never answers them; the answers belong in the project's architecture documents and ADRs, which the project bootstrap writes.


## Input Requirements

Argument: `$ARGUMENTS`

- `project name` — optional; use the argument when it is the only input, otherwise ask the product owner.
- Whether the project already has specs, ADRs, docs, or code. If it does, also follow **Brownfield adoption** (below).

## Procedure

1. Check whether an S-000 already exists: run `ai-team list specs`.
   If S-000 is listed, stop. Tell the product owner it exists and offer to amend it instead; do not create a second overview.

2. Open the planning branch.
   Follow **Opening a Planning Branch** in the `git-conventions` skill, running the command in step 3 as its allocation step.

3. Run `ai-team spec new --overview --json` and parse the response for `id` (S-000) and `path`.

4. Interview the product owner before you draft any section. S-000 records the product owner's decisions, so its content comes from their answers, not from existing material or your own defaults.
   - Ask in rounds of about five multiple-choice questions. Give each option a one-line description, and leave an open option for the product owner's own answer.
   - Start with the decisions that shape everything else: who the users are and in what situations; where the solution runs and who shares it; the core jobs it does; how users interact with it and how work reaches it; what it may do on its own and what needs a person's say; what it must remember, and for how long.
   - Then cover what each section needs: the purpose and the outcome it delivers; what each kind of user needs; the concrete pain points those users have today; the main use cases, each as one short scenario from the user's point of view; the split into solution and development-infrastructure components, with each component's responsibility, boundary, and collaborators; each development-infrastructure component's decisions needed (record the questions, not the answers); and the project exclusions.
   - Existing specs, ADRs, docs, and your own knowledge of similar products may suggest options and questions, never answers. Name the source of every option taken from existing material (for example "from S-002"), so the product owner can see which options are inherited assumptions.
   - Keep asking rounds until every section's content comes from a product-owner answer.
   - If the product owner asks to skip the interview, explain that S-000 records their decisions, and offer a short first round on the shaping decisions. If they still decline, stop and report that S-000 cannot be written yet. Do not draft it for them to correct.

5. Summarise the product back to the product owner in a few bullets: the users, where it runs, the core jobs, how work reaches it, and the main exclusions. Ask them to confirm or correct it. Repeat steps 4 and 5 until they confirm it.

6. Draft the seven sections from the answers, in the order the **Section contract** (above) gives: Purpose, Users, Pain points, Use cases, Solution overview, Components, Project exclusions. Check each component against the three checks in the Section contract. Leave anything with no product-owner answer behind it marked `[TODO]`; do not fill it from existing material or your own defaults.

7. Run the **pre-submission checklist** (below). Fix every unchecked item.

8. Inspect the draft for product-owner-answerable `[TODO]` markers. If any remain, ask the product owner about each. If any are still unanswered, report the blocker and stop instead of handing the draft on.

9. Commit the draft on the planning branch (`docs(specs): add S-000 draft`). Commit every later revision on the same branch, never on `{{integration_branch}}`.

10. Hand the draft to the Architect for an Architecture Consistency Review (Next Owner: Architect). The Architect checks it against existing approved specs and accepted ADRs and returns findings without amending the draft. Revise on those findings until the Architect and Planner agree it is consistent.

11. Present the revised draft to the product owner for Gate 1 approval. S-000 is not approved until the product owner says so. When the product owner approves, follow **After Gate 1** (below).

## Pre-submission checklist

- [ ] **Every statement comes from the product owner.** Every statement in Purpose, Users, Pain points, Use cases, and Project exclusions traces to a product-owner answer, not to existing material or your own defaults, and the product owner confirmed the summary (step 5) before drafting.
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
3. Write S-000 through the same procedure above (steps 1 to 8), interview first. What you learned in steps 1 and 2 supplies options and questions for the interview, each naming its source; it never fills a section or the summary the product owner confirms. Do not prefill a draft and ask the product owner to confirm or correct it: a prefilled draft only raises the questions it already answered.
4. After drafting, compare the draft with the existing specs and ADRs. Report every overlap, gap, and disagreement as a finding in your handoff, naming the spec or ADR concerned. Examples: two specs covering one component, a component with no spec, a spec whose scope contradicts the component split. Ask the product owner which side wins each disagreement, and record their answer with the finding.
5. Never amend an approved spec yourself to resolve a finding. Amending an approved spec is a separate change that goes through its own Gate 1 approval.
6. Go through the same Architect review and product owner Gate 1 as a greenfield S-000 (steps 10 and 11), then **After Gate 1**.

## After Gate 1

When the product owner approves S-000 at Gate 1, direct the Planner to do the following, in order:

1. Set S-000 to `approved` (the `status` field in its frontmatter) and commit that change on the planning branch.
2. Merge the planning branch into `{{integration_branch}}` with `--no-ff`, then delete it with `git branch -d`. S-000's own planning branch does not wait for Gate 2 (only its bootstrap task plan does), so this merge follows Gate 1; the `git-conventions` skill owns this S-000 exception.
3. Brownfield only: if the findings from the **Brownfield adoption** comparison call for changes to approved specs or ADRs, propose a change request from them with the `change-request` skill, one finding per entry, each with the side the product owner chose. The change request goes through its own approval.
4. Start the project bootstrap: run `spec-breakdown` on S-000. It plans only the bootstrap tasks for the development-infrastructure components and their Decisions needed.

## Rationalizations

These thoughts mean stop and go back to the interview (step 4).

| Excuse | Reality |
|---|---|
| "The existing specs are rich and consistent, so I can prefill most of S-000." | Existing material records what was built and assumed, not what the product owner decides now. It supplies options and questions, never answers. |
| "The product owner asked not to be quizzed, so I will draft from the specs for them to skim." | A product owner skimming a draft corrects only what it states; the questions it never asked stay unasked. Offer a short first round; if they still decline, stop. |
| "They said 'use your judgement', and the obvious shape is clear." | A typical product is not this one. Put the typical choice in front of them as one option among others. |
| "I will draft it anyway and mark my guesses `[TODO: confirm]`." | A guess marked for confirmation is still your answer, not theirs. Draft only after the product owner has confirmed the summary (step 5). |
