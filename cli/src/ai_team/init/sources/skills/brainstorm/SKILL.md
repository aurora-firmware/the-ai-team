---
name: brainstorm
description: Explore solution space for a feature request or problem. Use when a new feature needs a design before implementation, or when an existing approach was rejected and alternatives need exploration.
allowed-tools: Read, Grep, Glob, Write, Bash, Skill(new-spec), Skill(new-system-overview)
effort: high
---

# Brainstorm

Interactive design session between the product owner and the Planner.
The goal is to arrive at a well-understood, agreed direction *before* writing the specification — not to produce a document for the product owner to approve cold.

## Input Requirements

- **Feature request or problem description** — what needs to be solved and why.
- **Existing specifications and decisions** — context from `{{project_dir}}/specs/` and `{{project_dir}}/decisions/` to avoid contradictions.
- **Constraints** — any technical, time, or scope constraints stated by the product owner.

## Procedure

### Step 0: Triage the Scope

When the S-000 row of the `using-ai-team` routing table applies, suggest the system overview first, as that row says; the product owner decides.
If they accept, run `new-system-overview` instead of this skill.

Read the request, then judge its size before spending any clarifying question.
If it describes several independent subsystems — pieces that could be specified, built, and verified separately, such as "a billing system with invoicing, tax reporting, and a customer portal" — it is too large for one spec:

1. Say so to the product owner, and list the independent sub-projects with one line each.
2. Propose the order, and the dependency between sub-projects, if any.
3. Ask the product owner to confirm the split, then brainstorm only the first sub-project. Each remaining sub-project gets its own brainstorm, spec, and task plan later.

### Step 1: Understand the Request

Separate what is known (stated requirements, explicit constraints, referenced systems) from what is unknown or ambiguous (priorities, scope boundaries, user-facing behaviour, performance expectations, unmentioned integration points).
Read `{{project_dir}}/specs/` and `{{project_dir}}/decisions/` for existing decisions that bear on this feature.

### Step 2: Clarification Round

Before exploring solutions, resolve the unknowns that would materially change the solution space.
Plan coverage with these internal categories; never show category names or labels to the product owner:

- **Scope & Requirements** — required outcomes, boundaries, and always the exclusions question: "What is explicitly NOT included in this feature?"
- **Technical Constraints** — performance targets, compatibility, integrations, rollout, security, operational limits.
- **Users & Surfaces** — who is affected, which interfaces or workflows change, what each user type must experience.
- **Edge Cases & Error Handling** — failure modes, unusual inputs, partial states, rollback needs.
- **Prior Decisions** — existing specifications, decision records, and project conventions.
- **Verification** — how success will be observed, tested, reviewed, or accepted.

Questions that often pay off: Which existing behavior must remain unchanged? What should happen when the required data is missing, stale, or contradictory? Which failure would be most damaging? Has any approach already been ruled out? What would make the first version acceptable to ship? If requirements conflict, which priority decides?

Rules:
- Aim for about five focused questions per round. Coverage of all six categories is the binding constraint: run another round rather than leave a material unknown open.
- Skip a category silently when it has no material unknown. Ask no filler questions.
- Leave implementation details (naming, file structure) out unless they change the solution space.
- Prefer multiple-choice questions. Offer your recommended choice first and say why; leave an open option for the product owner's own answer.
- Ask the product owner and **stop**. Do not continue until answers are received.

If there are no material unknowns, skip this step.

### Step 3: Explore the Solution Space

When the need has real design choices, generate at least two distinct approaches: different behaviour, interaction, or interfaces for the same need.
When it has only one sensible shape, say so and why; the spec then records `None`, with that reason, under Alternatives Considered.
Describe each approach in one short paragraph:
- what users and external systems see and do;
- which interfaces and existing behaviour change;
- key trade-offs: user value, scope, flexibility, fit with existing specs and decisions.

Approaches differ in what the product does, not in how it is built. Do not compare technologies, frameworks, storage, or internal designs; the Architect decides those after Gate 1. When the product owner names a technology that users or external systems do not see, note it as a technology preference for Step 7.

Include approaches that seem impractical; they help the product owner say what they do *not* want. These are sketches, not a spec.

### Step 4: Present Alternatives and Get Direction

Present the alternatives briefly, **leading with your recommended option and why**, tied to the product owner's stated priorities.
Ask for the preferred direction, or for the constraint that should decide it.

**Stop and wait for the product owner's response.**

If the product owner picks an approach with modifications, note them.
If they are undecided, ask one focused question to find the deciding factor (e.g. "Is extensibility or simplicity the higher priority here?").

### Step 5: Refine (if needed)

If the chosen direction still has open questions about scope or behaviour — not implementation — ask them now, in one follow-up round at most.

### Step 6: Confirm the Approach Section by Section

Present the chosen approach in these sections, one at a time, each sized to its complexity:

1. **What it does** — the outcome, the users and journeys it serves, and the main behavior.
2. **Scope and exclusions** — one or more concrete exclusions, or the exact statement "no exclusions apply" when the product owner confirms there are none.
3. **Interfaces** — what users and external systems see change: commands, screens, files they edit, APIs, messages.
4. **Constraints and assumptions** — the constraints it must satisfy, the assumptions it relies on, configuration users set, and any quality thresholds the product owner agrees.
5. **Behavior examples and verification** — key success, failure, and boundary examples, how failures are handled, and how success will be observed.

After each section ask: "Does this section match your intent?" **Stop and wait for the answer before presenting the next section.**
If the product owner corrects a section, revise it and confirm it again; if the correction changes an earlier section, return to that section.

When all sections are approved, state the full approach in two or three sentences and ask: "I'll write the spec based on this — ready?"
**Stop and wait for confirmation.**

### Step 7: Produce the Specification

Invoke `new-spec` with:
- `title`: the confirmed spec title;
- `description`: everything approved in Step 6 — the problem, users and journeys, behavior and its examples, interfaces, constraints, assumptions, configuration, quality thresholds, and exclusions — plus the alternatives rejected in Step 4 with their reasons (or `None` with the reason from Step 3), and any technology preferences from Step 3 for the spec's Open Questions. Preserve each decision rather than compressing it into an outcome summary;
- `author`: `planner` unless the product owner named another author;
- `status`: `draft`.

`new-spec` writes, checks, resolves the remaining `[TODO]` markers with the product owner, sets the spec to `review`, commits it, and stops.
When it returns, check that Alternatives Considered records every approach rejected in Step 4 with its reason, and that every Step 6 decision appears in the spec; fix any gap on the planning branch and commit it.

## Output Format

- **Final response:** `new-spec`'s result — the spec `id`, `path`, planning branch, and `status` — or the blocker it reported.
  The spec then goes to the Architect's consistency review and to Gate 1, which the Planner arranges.

## Quality Criteria

- Every clarifying question was material.
- Alternatives were genuine (not strawmen), and the recommendation was stated first with reasons tied to the product owner's priorities.
- Approved discovery decisions survive into identifiable requirements and acceptance scenarios, not only later task criteria.
- Rejected approaches are recorded in Alternatives Considered, distinct from out-of-scope behavior.

## Common Pitfalls

- **Writing the spec before aligning** — producing a full document, then waiting for approval. The spec is arrived at *together*.
- **Solving the wrong problem** — re-read the original request after generating alternatives to verify you are addressing the actual need.
- **Scope creep** — an alternative that needs significantly more work becomes an explicit exclusion, not part of the current scope.
