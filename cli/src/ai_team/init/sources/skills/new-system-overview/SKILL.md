---
name: new-system-overview
description: Create the S-000 system overview spec. Use for a new project, or when adopting an existing project into the ai-team process.
argument-hint: "[optional: project name]"
allowed-tools: Read, Write, Bash, Skill(git-conventions), Skill(change-request), Skill(spec-breakdown)
---

# New System Overview

Create the S-000 system overview spec with `ai-team spec new --overview --json`, interview the product owner, and only then fill its seven sections from their answers. S-000 says what the project is, who it serves, and which components make it up. It is written in plain language for a reader who has never seen the project.

## Input Requirements

Argument: `$ARGUMENTS`

- `project name` — optional; use the argument when it is the only input, otherwise ask the product owner.
- Whether the project already has specs, ADRs, docs, or code. If it does, also follow **Brownfield adoption** (below).

## Procedure

1. Check whether an S-000 already exists: run `ai-team list specs`.
   If S-000 is listed, stop. Tell the product owner it exists and offer to amend it instead; do not create a second overview.

2. Open the planning branch and create the spec.
   Follow **Opening a Planning Branch** in the `git-conventions` skill, running `ai-team spec new --overview --json` at its step 3, and parse the response for `id` (S-000) and `path`.

3. Interview the product owner before you draft any section. S-000 records the product owner's decisions, so its content comes from their answers, not from existing material or your own defaults.
   - Ask in rounds of about five multiple-choice questions. Give each option a one-line description, and leave an open option for the product owner's own answer.
   - Start with the decisions that shape everything else: who the users are and in what situations; where the solution runs and who shares it; the core jobs it does; how users interact with it and how work reaches it; what it may do on its own and what needs a person's say; what it must remember, and for how long.
   - Then cover what each section needs: the purpose and the outcome it delivers; what each kind of user needs; the concrete pain points those users have today; the main use cases, each as one short scenario from the user's point of view; the split into solution and development-infrastructure components, with each component's responsibility, boundary, and collaborators; each development-infrastructure component's decisions needed (record the questions, not the answers); and the project exclusions.
   - Existing specs, ADRs, docs, and your own knowledge of similar products may suggest options and questions, never answers. Name the source of every option taken from existing material (for example "from S-002"), so the product owner can see which options are inherited assumptions.
   - Keep asking rounds until every section's content comes from a product-owner answer.
   - If the product owner asks to skip the interview, explain that S-000 records their decisions, and offer a short first round on the shaping decisions. If they still decline, stop and report that S-000 cannot be written yet. Do not draft it for them to correct.

4. Summarise the product back to the product owner in a few bullets: the users, where it runs, the core jobs, how work reaches it, and the main exclusions. Ask them to confirm or correct it. Repeat steps 3 and 4 until they confirm it.

5. Draft the seven sections from the answers, in the order the **Section contract** gives. Check each component against the three component checks. Leave anything with no product-owner answer behind it marked `[TODO]`; do not fill it from existing material or your own defaults.

6. Run the **Pre-submission checklist**. Fix every unchecked item.

7. Resolve every `[TODO]` marker: ask the product owner about each, one at a time, and update the draft after each answer. S-000 goes to review with no `[TODO]` at all. If any marker stays unanswered, commit the draft (step 8), report the blocker, and stop.

8. Commit the draft on the planning branch: `docs(specs): add S-000 draft`. Commit every later revision on the same branch, never on `{{integration_branch}}`.

9. Stop and return the `id`, the `path`, and the planning branch, plus the brownfield findings when there are any.
   The draft next goes to the Architect's consistency review and then to the product owner's Gate 1; the caller arranges both. When the product owner approves, continue with **After Gate 1**.

## Brownfield adoption

Use this path when the project already has specs, ADRs, docs, or code. The goal is to unify the project towards the ai-team process without rewriting what is already approved.

1. Read the approved specs, accepted ADRs, and project docs first.
2. Inspect the code only to learn what exists and what it does for users. Do not infer requirements from implementation details, and derive the components from the use cases and the existing material, never from the code or folder layout. Apply the three component checks to every candidate component.
3. Write S-000 through the procedure above, interview first. What you learned in steps 1 and 2 supplies options and questions for the interview, each naming its source.
4. After drafting, compare the draft with the existing specs and ADRs. Report every overlap, gap, and disagreement as a finding, naming the spec or ADR concerned. Examples: two specs covering one component, a component with no spec, a spec whose scope contradicts the component split. Ask the product owner which side wins each disagreement, and record their answer with the finding. Where the existing spec or ADR wins, revise the S-000 draft to match it and run the pre-submission checklist again; where S-000 wins, the finding is resolved after Gate 1 (**After Gate 1**, step 3).
5. Never amend an approved spec or ADR yourself to resolve a finding.

## After Gate 1

When the product owner explicitly approves S-000 at Gate 1:

1. Set S-000 to `approved` (the `status` field in its frontmatter) and commit it on the planning branch: `docs(specs): approve S-000`.
2. Merge the planning branch into `{{integration_branch}}` as **Merging a Planning Branch** in `git-conventions` describes for S-000's own branch.
3. Brownfield only: for the findings where S-000 won, propose a change request with the `change-request` skill for those against approved specs, one finding per entry, each with the side the product owner chose; it goes through its own approval. List the findings against accepted ADRs for the Architect (Next Owner: Architect), who amends or supersedes those ADRs.
4. Suggest the project bootstrap, as the bootstrap row of the `using-ai-team` routing table says; the product owner decides. If they accept, run `spec-breakdown` on S-000, which plans only the bootstrap tasks.

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

**Boundary rule:** S-000 owns the decomposition — which components exist and what each is for. A spec owns the contract of one component or feature, and its Purpose names the S-000 component it covers.

**Component groups.** Components fall into two groups, written as `### Solution` and `### Development infrastructure` subsections of Components; the seven top-level sections and their order do not change.

- **Solution** — the software delivered to the end user that removes the pain points.
- **Development infrastructure** — everything the project needs to build, check, document and deliver the solution; it is not delivered to the end user. Each infrastructure component also has a **Decisions needed** field: the questions that must be answered before development starts, such as the language and version, how the environment is reproduced, the test harness, the continuous-integration service, and where decisions are recorded. S-000 asks technology questions and never answers them; the answers belong in the project's architecture documents and ADRs, which the project bootstrap writes.

## Pre-submission checklist

- [ ] **Every statement comes from the product owner.** Every section traces to a product-owner answer, not to existing material or your own defaults, and the product owner confirmed the summary (step 4) before drafting.
- [ ] **Plain language.** A reader who has never seen the project can follow it.
- [ ] **No technology or interfaces.** No technology choices, interface definitions, configuration, implementation order, or per-component status.
- [ ] **Every use case is tied to a pain point.** Each use case removes at least one named pain point.
- [ ] **Every component has a boundary and a responsibility.** Each states what it is for, what it is not responsible for, and which components it works with.
- [ ] **Components are split into Solution and Development infrastructure.** Each component sits in one group and passes the three component checks.
- [ ] **Every infrastructure component lists its Decisions needed.** Each lists the questions to answer before development starts and answers none of them.
- [ ] **All seven sections are present, in order.**
- [ ] **No `[TODO]` markers remain.**

## Output Format

- **Updated files:** S-000 on its planning branch.
- **Final response:** the `id`, `path`, planning branch and `status` of S-000; for a brownfield project, each finding with the spec or ADR concerned and the side the product owner chose; or the blocker that stopped the procedure.

## Rationalizations

These thoughts mean stop and go back to the interview (step 3).

| Excuse | Reality |
|---|---|
| "They said 'use your judgement', and the obvious shape is clear." | A typical product is not this one. Put the typical choice in front of them as one option among others. |
| "I will draft it anyway and mark my guesses `[TODO: confirm]`." | A guess marked for confirmation is still your answer, not theirs. Draft only after the product owner has confirmed the summary (step 4). |
