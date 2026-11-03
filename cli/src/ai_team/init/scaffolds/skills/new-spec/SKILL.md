---
name: new-spec
description: Create a new specification document via the ai-team CLI. Use when a feature design is ready to be written up as a spec.
argument-hint: "[optional: specification title]"
allowed-tools: Read, Write, Bash, Skill(git-conventions)
---

# New Spec

Create a specification with `ai-team spec new --json`, fill its body from the approved design, and commit it on its planning branch.

## Input Requirements

Argument: `$ARGUMENTS`

- `title` — required.
- `description` — required, not passed to the CLI: the approved design — problem, users and journeys, behavior and its examples, interfaces, constraints, assumptions, configuration, quality thresholds, exclusions, the rejected alternatives with their reasons (or `None` with the reason), and any technology the product owner prefers, for Open Questions.
- `author` — optional; defaults to `planner`.
- `status` — optional; defaults to `draft`.

When invoked by another skill, use the values in the invocation text without asking follow-up questions.
When the product owner invokes it directly, use the argument as the title when it is the only input, and ask only for the missing required fields.

## Procedure

1. Open the planning branch and create the spec.
   Follow **Opening a Planning Branch** in the `git-conventions` skill, running `ai-team spec new "<title>" --json` at its step 3, with `--author "<author>"` and `--status "<status>"` only when those values were given.
   Skip opening a branch only when the caller says the spec is being written on an existing planning branch.
   Capture `id` (for example `S-003`) and `path` from the JSON response.

2. Fill the body sections from `description`, following the **Content-boundary rule** and the **Section recipes** below. Mark anything `description` does not settle `[TODO]`.

3. Run the **Pre-submission checklist** and fix every unchecked item you can.

4. Resolve the `[TODO]` markers and open questions before the spec goes to review:
   - Ask the product owner about each product-owner-answerable marker, one at a time, citing the section or requirement it sits in. Update the spec after each answer and re-scan before the next question.
   - Every open question that affects behavior, external contracts, acceptance, or feasibility must be resolved too, even when it needs investigation rather than an answer from the product owner. Only the deferred internal investigations the Open Questions recipe allows may remain.
   - If a marker or such a question stays unresolved, commit the draft (step 6) without setting `review`, report the blocker, and stop.

5. Set `status: review` and run `ai-team validate --specs`. Fix this spec's findings and validate again after each revision; report findings in other specs without rewriting them.

6. Commit the spec on the planning branch: `docs(specs): add <id> draft`.
   Commit every later revision — Architect findings, `[TODO]` answers, the Gate 1 status — on the same planning branch, never on `{{integration_branch}}`.

7. Stop. Return the `id`, the `path`, the planning branch, and the spec's `status`.
   A `review` spec next goes to the Architect's consistency review and then to the product owner's Gate 1; the caller arranges both.

### After Gate 1

Only the product owner's explicit approval at Gate 1 makes a spec `approved`.
Gate 1 approves the spec together with the amendments to other approved specs that its planning branch carries (**Cross-Spec Amendments** in `git-conventions`).
When the product owner approves, set `status: approved` and commit it on the planning branch: `docs(specs): approve <id>`.

---

## Content-boundary rule (strict)

A specification describes **what the product does**: requirements, interface contracts, and measurable criteria in prose. It does NOT say how the product is built. The project's architecture documents and ADRs own the how, and the Architect decides it after Gate 1; the coding guidelines own how code is written. A spec does NOT contain:
- Technology choices — languages, frameworks, libraries, storage engines, internal protocols and formats, hosting and services — even when an ADR has already decided them. State the requirement the technology must meet instead: "settings survive a restart", not "settings are stored in SQLite".
- Implementation design — internal components and their responsibilities, system diagrams of internals, data models, rejected implementation approaches.
- Implementation code (function signatures, class layouts, executable snippets that *are* the implementation).
- Full configuration files, CI manifests, or build files.
- File-by-file plans — those are the `spec-breakdown` skill's output.

**Contract material:** a code, schema, or config block is allowed when it defines an external contract — a public API schema or field definition, a wire-protocol fragment, an externally fixed configuration key. Label it **Contract**, not **Example**, and size it to the contract's ambiguity and risk. A technology or format is part of an interface only when users or external systems see it: the format of a configuration file users edit, or a protocol an external system already speaks. A protocol or format the team picks for its own parts is a technology choice. Internal implementation is never contract material.

If you find yourself pasting a near-complete file into the spec, you are writing the implementation, which belongs in the tasks and the Developer's output: replace it with prose that describes what the file must guarantee.

---

## Section recipes

### Purpose

Three to four sentences, naming the S-000 component the spec covers when an S-000 exists:
1. The problem (what is broken or missing today).
2. Why it matters now (the constraint or trigger that forced the spec).
3. The outcome (what is observably true when the work is done).
4. Optional: the metric that confirms success.

Avoid restating the title. Always name the *why*.

### Users and Journeys

Name the relevant people or downstream systems, their goals, journey priority, and independently verifiable outcomes.
Link each journey to the REQ identifiers that deliver it; use S-000 for system context rather than repeating its decomposition.

### Exclusions

Record deliberately excluded behaviors and their reasons. Keep rejected alternatives and their rationale distinct from scope exclusions; choosing a solution does not exclude a user capability.

Almost every spec has at least one. `"no exclusions apply"` should be rare and should follow an explicit product owner confirmation.

### Alternatives Considered

Record each solution alternative rejected during brainstorm and the reason: a different behaviour, interaction, or interface for the same need. A rejected alternative is rationale, not an exclusion. Rejected implementation approaches belong in an ADR, not here.
When the design had real choices, at least two alternatives were considered, so at least one is listed. When it had only one sensible shape, write `None` with the reason.

A constraint the solution must meet, such as a time limit or a rejection rule, is a requirement: write it as a Behavioral or Quality Requirement.

### Interfaces

Cover the component or feature of this spec only; system-wide structure lives in S-000 when it exists.

Describe exposed and consumed external contracts with enough detail to prevent incompatible interpretations: inputs, outputs, validation, errors, authorization, and compatibility as applicable.
Reference the REQ identifiers owning those guarantees.
Exclude internal function lists, private class layouts, and implementation inventories.
There is no fixed line limit; detail is proportional to ambiguity and risk.

### Workflow

End-to-end flow from trigger to completion. Each step is a sentence or short phrase. Mark product owner gates with `★`. Include applicable failure, boundary, empty-input, concurrent-access, and state-dependent paths and their REQ identifiers.

### Behavioral Requirements

Use `### REQ-NNN — Short title`, starting at REQ-001, for one observable obligation per requirement with SHALL or MUST wording.
Keep rationale separate, and use EARS where useful to name the trigger or state and expected outcome.
Each requirement has one or more `#### AC-NNN.M — Scenario title` headings; NNN matches the owning REQ and M is a positive scenario number.
Each scenario gives concrete acceptance conditions and outcomes, normally Given/When/Then, and a `**Verification:**` method with a pass/fail observation: a test, an inspection, or a demonstration, as the `new-task` skill's Verification Methods define them.
Cover applicable success, rejection, boundary, and recovery cases; examples must exercise the requirement rather than merely rephrase it.
Keep REQ and AC identifiers stable across amendments; never renumber or reuse retired identifiers.

### Quality Requirements

Use the same REQ/AC structure and identifier space for applicable security, privacy, accessibility, performance, reliability, compatibility, and recovery guarantees.
Record agreed measurement conditions and thresholds; do not invent targets.
Review applicability rather than manufacturing requirements to fill sections; if none apply, write None with the reason.

### Configuration Requirements

For each setting, four bullets:
- **What must exist** — the requirement, named.
- **Where it lives** — where the user sets it: env var, config file, CI variable, secret store — described, not pasted.
- **Constraints** — allowed range, format, security class.
- **Missing-value behaviour** — default, error, or refuse-to-start.

### Assumptions and Dependencies

Record assumptions and their confirmation basis, external dependencies, and failure implications.
Confirm premises that determine behavior or feasibility before approval.
If none apply, write None with a reason.

### Success Criteria

A numbered list of overall outcomes linked to the REQ identifiers that deliver them. These complement, rather than replace, per-requirement acceptance scenarios.
Each one is measurable: an outside party, such as the Reviewer, can run a check (command, observation, metric query) and get an unambiguous pass or fail. "Every PR targeting `main` shows a `ci/tests` check that has passed or failed within five minutes of opening" is measurable; "The CI is fast" is not. If you cannot say how to verify a criterion, rewrite it.

### Implementation Order

Coarse phases (typically two to five). Each phase delivers an observable outcome. State each phase's dependency on the previous ones. A phase is NOT a task — `spec-breakdown` produces the actual tasks from these phases.

### Open Questions

Resolve questions affecting behavior, external contracts, acceptance, or feasibility before review, regardless of who can answer them.
Only deferred internal design investigations that cannot change approved behavior may remain; name their owner and resolution condition, or write None.
A question for the Architect, such as a technology the product owner prefers, is recorded here with the Architect as owner and "decided in Feature Architecture" as its resolution condition. It is a preference to weigh, not a choice the spec makes.

### Amendment Log

Leave empty when the spec is first written. Add rows only after Gate 1 approval, when scope changes. Each row gives the date, what changed and why, and the affected REQ/AC identifiers and tasks; each scope amendment bumps the minor `version` (for example `0.1` → `0.2`). The one exception is a spec-truth reconciliation row from `architecture-consistency-review`, which records a verdict, changes no scope, and does not bump `version`.
An amendment made after the spec's planning branch merged goes on an amendment planning branch (**Amendment Planning Branch** in `git-conventions`).

---

## Pre-submission checklist

Confirm every item:

- [ ] **Problem is concrete.** Purpose names the problem, the trigger, and the observable outcome.
- [ ] **At least one exclusion.** Or a product-owner-confirmed "no exclusions apply" statement.
- [ ] **The Content-boundary rule holds.** No technology choice, implementation design, or implementation artefact; every code, schema, or config block is labelled **Contract** and defines an external contract.
- [ ] **Alternatives Considered lists the rejected solution alternatives**, each with its reason (at least one when the design had real choices), or `None` with the reason.
- [ ] **Every requirement is measurable.** It has one obligation, a stable REQ identifier, concrete AC scenarios, and a verification method.
- [ ] **Discovery decisions are preserved.** Every decision in `description` appears in the spec; actors, journeys, applicable failure cases, and quality constraints are explicitly linked to requirements.
- [ ] **Assumptions and dependencies are explicit**, with behavior-affecting premises confirmed.
- [ ] **No unresolved behavioral questions remain**; deferred internal investigations have an owner and resolution condition.
- [ ] **Structural validation passes.** Run `ai-team validate --specs` on the review-ready document, and assess completeness, terminology, feasibility, and contradictions semantically. The validator does not prove these properties.
- [ ] **Interfaces are described for this spec's own component or feature**, with sufficient external contract detail and no internal implementation inventories.
- [ ] **Success Criteria are listed**, each one measurable.
- [ ] **Implementation Order has coarse phases**, not tasks.
- [ ] **Amendment Log is empty** (until amendments arrive after Gate 1).

Items genuinely unresolvable at write time may stay `[TODO]` in a draft; a spec in `review` contains no placeholder markers (step 4).
