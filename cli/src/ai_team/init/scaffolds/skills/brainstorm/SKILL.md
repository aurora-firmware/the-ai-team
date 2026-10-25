---
name: brainstorm
description: Explore solution space for a feature request or problem. Use when a new feature needs a design before implementation, or when an existing approach was rejected and alternatives need exploration.
allowed-tools: Read, Grep, Glob, Write, Skill(new-spec)
effort: high
---

# Brainstorm

Interactive design session between the human and the Planner.
The goal is to arrive at a well-understood, agreed direction *before* writing the specification — not to produce a document for the human to approve cold.

## Input Requirements

- **Feature request or problem description** — what needs to be solved and why.
- **Existing specifications and decisions** — context from `{{project_dir}}/specs/` and `{{project_dir}}/decisions/` to avoid contradictions.
- **Constraints** — any technical, time, or scope constraints stated by the human.

## Procedure

### Step 0: Triage the Scope

When `ai-team list specs` shows no `S-000`, suggest to the human starting with the system overview (`new-system-overview`) before writing a feature spec; the human decides. If the human declines, continue as before; the suggestion is not repeated in the same session.

Read the request, then judge its size before spending any clarifying question.
If it describes several independent subsystems — pieces that could be specified, built, and verified separately, such as "a billing system with invoicing, tax reporting, and a customer portal" — it is too large for one spec. An oversized spec needs constant amendment and stops being true.

1. Say so to the human, and list the independent sub-projects with one line each.
2. Propose the order, and the dependency between sub-projects, if any.
3. Ask the human to confirm the split, then brainstorm only the first sub-project. Each remaining sub-project gets its own brainstorm, spec, and task plan later.

If the request is a single coherent unit, continue to Step 1 without comment.

### Step 1: Understand the Request

Read the feature request thoroughly.
Separate what is known from what is unknown or ambiguous:
- **Known**: stated requirements, explicit constraints, referenced existing systems.
- **Unknown**: unstated priorities, scope boundaries, user-facing behaviour details, performance expectations, integration points not mentioned.

Read `{{project_dir}}/specs/` and `{{project_dir}}/decisions/` to surface any existing decisions that bear on this feature.

### Step 2: Clarification Round

Before exploring solutions, resolve the unknowns that would materially change the solution space.

Use these internal categories to plan coverage. Do not expose category names or `[Category]` labels in the questions you ask the human.

**Internal categories:**
- **Scope & Requirements** — clarify required outcomes, boundaries, and the prominent exclusions question: "What is explicitly NOT included in this feature?"
- **Technical Constraints** — identify constraints such as performance targets, backwards compatibility, integrations, rollout strategy, security, or operational limits.
- **Users & Surfaces** — clarify who is affected, which interfaces or workflows change, and what each user type must experience.
- **Edge Cases & Error Handling** — surface failure modes, unusual inputs, partial states, rollback needs, and expected handling.
- **Prior Decisions** — check existing specifications, decision records, and project conventions for constraints or contradictions.
- **Verification** — clarify how success will be observed, tested, reviewed, or accepted.

**Example question pool:**
- What outcome must this feature guarantee for the user?
- What is explicitly NOT included in this feature?
- Which existing behavior must remain unchanged?
- Are there performance, compatibility, rollout, or operational constraints I should account for?
- Which user types or workflows are affected first?
- Are there surfaces where this should not appear, even if they seem related?
- What should happen when the required data is missing, stale, or contradictory?
- What failure mode would be most damaging if we handled it poorly?
- Are there prior specs, decisions, or conventions this must follow?
- Has any approach already been rejected or ruled out?
- What would make the first version acceptable enough to ship?
- How should we verify that the change works as intended?
- What evidence should reviewers look for before approving the spec or implementation?
- If requirements conflict, which priority should decide the trade-off?

**Rules:**
- Aim for about five focused questions per round as a recommendation, not a hard cap.
- Coverage of all six internal categories is the binding constraint. If one round cannot cover the material unknowns clearly, ask another round before moving on.
- Silent skip is acceptable when a category has no material unknown for this request. Do not ask filler questions.
- Avoid details that belong in the implementation phase, such as exact naming or file structure, unless they materially change the solution space.
- Prefer multiple-choice questions where the answers can be enumerated. Offer your recommended choice first and say why; leave an open option for the human's own answer.
- Ask the human and **stop**. Do not continue until answers are received.

If there are no material unknowns, skip this step and proceed.

### Step 3: Explore the Solution Space

With clarified requirements, generate at least two distinct approaches.
For each approach describe concisely (one short paragraph each):
- How it works at a high level
- What components or changes it requires
- Key trade-offs: complexity, flexibility, implementation effort, alignment with existing architecture

Do not self-censor. Include approaches that seem impractical — they may contain useful ideas or help the human articulate what they *don't* want.

Do not write a full spec at this stage. These are sketches, not blueprints.

### Step 4: Present Alternatives and Get Direction

Present the alternatives to the human in brief.
**Lead with your recommended option and explain why** — tied to the human's stated priorities — before describing the others.
Ask the human to indicate their preferred direction — or to name any constraint that should decide it.

**Stop and wait for the human's response before continuing.**

If the human picks an approach with modifications, note the modifications.
If the human is undecided, ask one focused question to identify the deciding factor (e.g. "Is extensibility or simplicity the higher priority here?").

### Step 5: Refine (if needed)

If the chosen direction has remaining open questions about scope or behaviour — not about implementation — ask them now.
Maximum one follow-up round.

Skip this step if the direction is clear enough to write the spec.

### Step 6: Confirm the Approach Section by Section

The spec becomes durable truth, so the human signs off on the design incrementally, not once at the end.
Present the chosen approach in these sections, one at a time, each sized to its complexity (a few sentences when straightforward, a short paragraph when nuanced):

1. **What it does** — the outcome and the main behavior.
2. **Scope and exclusions** — an exclusions line with one or more concrete exclusions, or the exact statement "no exclusions apply" when the human confirms there are none.
3. **Components and interfaces** — the parts that change and how they connect.
4. **Constraints, error handling, and verification** — the constraints it assumes, how failures are handled, and how success will be observed.

After each section ask: "Does this section match your intent?" **Stop and wait for the human's answer before presenting the next section.**
If the human corrects a section, revise it and confirm it again. If the correction changes an earlier section, return to that section.

When all sections are approved, state the full approach in two or three sentences and ask: "I'll write the spec based on this — ready?"

**Stop and wait for confirmation before proceeding to Step 7.**

### Step 7: Produce the Specification

Invoke the `new-spec` skill to create the specification file. Provide the full required input set in the invocation text:
- `title`: the confirmed spec title
- `description`: the confirmed approach and all approved behavioral decisions, actors/journeys, acceptance examples, constraints, assumptions, exclusions, and rejected alternatives with rationale from Step 6. Preserve decisions rather than compressing them into an outcome-only summary.
- `author`: `planner` unless the human provided a different author
- `status`: `draft`

`new-spec` handles template loading, frontmatter scaffolding, and section-by-section filling. It carries the **content-boundary rule** (no implementation code, config files, or build manifests in the spec body), the **section recipes** for each part of the template, and the **pre-submission checklist** — apply them through that skill rather than re-deriving them here.

When `new-spec` returns, also fill in the alternatives considered and why they were rejected (this is the brainstorm-specific content that the new-spec recipes do not generate).

Scan the created spec for `[TODO]` markers before setting or treating the spec as review-ready.
- For each human-answerable `[TODO]` marker, ask the human one contextual question tied to that section or requirement.
- After each answer, update the spec with the answer before continuing to the next marker.
- Re-scan after each update so the next question reflects the current document state.

If any human-answerable `[TODO]` markers remain, explicitly report the blocker and stop.
- The spec must not hand the spec to Architecture Consistency Review while those markers remain.
- The spec must not hand the spec to Gate 1 approval while those markers remain.

Before updating the spec `status` to `review`, confirm that every decision approved in Step 6 appears in the spec, then complete the `new-spec` handoff steps.

Only then is the document ready for Architecture Consistency Review and Gate 1 confirmation.
Because the human shaped the spec interactively, Gate 1 should be a quick confirmation — not a cold review.

## Quality Criteria

- Every clarifying question was material — not asked out of habit.
- At least two alternatives were genuinely considered (not strawmen).
- The chosen approach has clear rationale tied to the human's stated priorities.
- Exclusions are explicit.
- The spec is self-contained: readable without opening other files, except precise references to existing external contracts.
- Approved discovery decisions survive into identifiable requirements and acceptance scenarios, not only later task criteria.
- Rejected implementation approaches are recorded as rationale, distinct from out-of-scope behavior.
- The human confirmed the direction before the spec was written.
- An oversized request was split into sub-projects, and only the first was brainstormed.
- The human approved the design section by section, not only once at the end.
- Recommended options were stated first, with reasons.

## Common Pitfalls

- **Writing the spec before aligning** — producing a full document, then waiting for approval. The goal is to arrive at the spec *together*.
- **Asking too many questions in one round** — aim for about five per round. If the six internal categories cannot be covered materially within that budget, run a second round rather than stretching a single round indefinitely.
- **Brainstorming an oversized request whole** — a spec that spans several independent subsystems will need constant amendment. Split it in Step 0.
- **One big confirmation at the end** — compressing the whole design into a single "does this match?" lets a wrong section ride through. Approve each section.
- **Anchoring on the first idea** — always generate at least one meaningfully different alternative before committing to a direction.
- **Solving the wrong problem** — re-read the original request after generating alternatives to verify you are addressing the actual need.
- **Scope creep** — if an alternative requires significantly more work, record it as an explicit exclusion in the spec's Exclusions section rather than folding it into the current scope.
- **Missing constraints** — check `{{project_dir}}/decisions/` before proposing anything that contradicts a prior decision.
- **Embedding the implementation in the spec** — pasting near-complete config files, CI manifests, or build files into the spec, instead of describing them as requirements. This pre-empts the task plan and the Developer, and the spec rots when the real code evolves. Describe the contract; the implementation is the Developer's job.
