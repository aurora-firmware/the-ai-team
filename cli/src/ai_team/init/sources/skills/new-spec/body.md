# New Spec

Create a new specification document using `ai-team spec new --json`, then fill its body following the section-by-section recipes below.

## Input Requirements

Provide these values directly when possible:
- `title` — required
- `description` — required (free-form prose: problem, approach, exclusions, constraints; used to fill body sections in step 4 — NOT passed to the CLI)
- `author` — optional; defaults to `planner`
- `status` — optional; defaults to `draft`

When invoked by another skill, the caller should provide every required field in the invocation text and this skill must use them without asking follow-up questions.
When invoked directly by a human and required fields are missing, ask only for the missing fields before proceeding.

## Procedure

1. Resolve inputs:
   - Use the caller-provided `title`, `description`, `author`, and `status` when they are present.
   - If invoked directly and some required fields are missing, ask only for the missing fields.
   - Use `$ARGUMENTS` as the title when it is the only provided input.

2. Build the CLI command:
   - Base: `ai-team spec new "<title>" --json`
   - Add `--author "<author>"` only when `author` is provided; otherwise allow the CLI default.
   - Add `--status "<status>"` only when `status` is provided; otherwise allow the CLI default.
   - Do NOT pass `description` to the CLI — the CLI has no `--description` flag.

3. Open the planning branch and execute the command.
   Follow **Opening a Planning Branch** in the `git-conventions` skill, running this command at its step 3.
   Skip opening a branch only when the caller says the spec is being written on an existing planning branch.
   Parse the JSON response to capture:
   - `id` (for example, `S-003`)
   - `path` (absolute path to the created file, named `S-NNN-<slug>.md`)

4. Open the created spec file and fill its body sections from the supplied `description`, using the **content-boundary rule** and the **section recipes** below. Preserve `spec-format: behavior-v1` from the template. Leave any section that still needs exploration marked `[TODO]`. Do not remove the marker to bypass readiness checks.

5. Run the **pre-submission checklist** (below) against the filled spec, including `ai-team validate --specs` once its status is `review`. Validate again after revisions; fix findings without rewriting unrelated existing specs. Fix any unchecked item before returning. Leave items genuinely unresolvable marked `[TODO]`.

6. Inspect the draft for human-answerable `[TODO]` markers before any review handoff.
   - Human-answerable `[TODO]` markers must be resolved before Architecture Consistency Review.
   - Every unresolved question affecting behavior, contracts, acceptance, or feasibility also blocks handoff, even if it needs technical investigation rather than a human answer.
   - Only internal design investigations that cannot change approved behavior may remain in Open Questions; each needs an owner and resolution condition. No unresolved placeholder markers may remain in a review-ready feature spec.
   - Once ready for handoff, set status to `review` and run `ai-team validate --specs`; fix this spec's findings before handing it on. Only explicit human approval permits status `approved`. Report unrelated findings without rewriting those specs.
   - If any human-answerable `[TODO]` markers remain, explicitly report the blocker and stop instead of handing the draft to Architecture Consistency Review or Gate 1 approval.

7. Confirm the created file exists, commit it on the planning branch (`docs(specs): add <id> draft`), and return the CLI response values (`id` and `path`) and the planning branch name.
   Commit every later revision — Architect findings, `[TODO]` resolutions, Gate 1 approval — on the same planning branch, never on `{{integration_branch}}`.

8. Remind that the new spec requires human Gate 1 approval unless the caller explicitly says it is already being prepared for that gate.
9. Once human-answerable `[TODO]` markers are resolved before Architecture Consistency Review, hand the draft spec to the Architect for an Architecture Consistency Review before Gate 1 (Next Owner: Architect). The Architect checks it against existing approved specs and accepted ADRs and returns findings — like a Gate 2 review, this does not amend the draft. Revise the draft on those findings until the Architect and Planner agree it is consistent; the human then approves at Gate 1 as usual.

---

## Content-boundary rule (strict)

A specification describes **requirements, contracts, and measurable criteria in prose**. It does NOT embed:
- Implementation code (function signatures, class layouts, executable snippets that *are* the implementation).
- Full configuration files, CI manifests, or build files.
- File-by-file plans — those are the `spec-breakdown` skill's output.

Concrete code, config, and manifests belong in the **tasks** that `spec-breakdown` produces and in the **Developer's output**, not in the spec body.

**Rare exception:** a code or config block is acceptable when the block *is itself the contract* — a public API schema, a wire-protocol fragment, an externally-fixed configuration key. Mark such blocks **Contract**, not **Example**. If in doubt, use prose.

If you find yourself pasting a near-complete file into the spec, you are writing the implementation — replace it with prose that describes what the file must guarantee.

---

## Section recipes

Use these recipes to fill each section of the spec file the CLI created.

### Purpose

Three to four sentences, naming the S-000 component the spec covers:
1. The problem (what is broken or missing today).
2. Why it matters now (the constraint or trigger that forced the spec).
3. The outcome (what is observably true when the work is done).
4. Optional: the metric that confirms success.

Avoid restating the title. Always name the *why*.

### Users and Journeys

Name the relevant people or downstream systems, their goals, journey priority, and independently verifiable outcomes.
Link each journey to the REQ identifiers that deliver it; use S-000 for system context rather than repeating its decomposition.

### Exclusions

Record deliberately excluded behaviors and their reasons. Keep rejected implementation approaches and their rationale distinct from scope exclusions; choosing a design does not exclude a user capability.

Almost every spec has at least one. `"no exclusions apply"` should be rare and should follow an explicit human confirmation.

### Architecture — Design Principles

Scoped to this spec. Each principle is a **constraint on the design space**, not an implementation choice. State it as a property the design must satisfy.

Good: "Validation must run in under three minutes on the median PR."
Bad: "Use GitHub Actions." (That picks the implementation; reframe as a constraint, e.g. "must integrate with the project's existing PR review surface.")

### Interfaces

Cover the component or feature of this spec only. System-wide structure lives in S-000; the Purpose names the S-000 component the spec covers.

Describe exposed and consumed external contracts with enough detail to prevent incompatible interpretations: inputs, outputs, validation, errors, authorization, and compatibility as applicable.
Reference the REQ identifiers owning those guarantees.
Public field definitions, protocol fragments, and precise versioned public-schema references are allowed as **Contract** material.
Exclude internal function lists, private class layouts, and implementation inventories.
There is no fixed line limit; detail is proportional to ambiguity and risk.

### Workflow

End-to-end flow from trigger to completion. Each step is a sentence or short phrase. Mark human gates with `★`. Include applicable failure, boundary, empty-input, concurrent-access, and state-dependent paths and their REQ identifiers.

### Behavioral Requirements

Use `### REQ-NNN — Short title`, starting at REQ-001, for one observable obligation per requirement with SHALL or MUST wording.
Keep rationale separate, and use EARS where useful to name the trigger or state and expected outcome.
Each requirement has one or more `#### AC-NNN.M — Scenario title` headings; NNN matches the owning REQ and M is a positive scenario number.
Each scenario gives concrete acceptance conditions and outcomes, normally Given/When/Then, and a `**Verification:**` method: a test, demonstration, inspection, or analysis with a pass/fail observation.
Cover applicable success, rejection, boundary, and recovery cases; examples must exercise the requirement rather than merely rephrase it.
Keep REQ and AC identifiers stable across amendments; never renumber or reuse retired identifiers.

### Quality Requirements

Use the same REQ/AC structure and identifier space for applicable security, privacy, accessibility, performance, reliability, compatibility, and recovery guarantees.
Record agreed measurement conditions and thresholds; do not invent targets.
Review applicability rather than manufacturing requirements to fill sections; if none apply, write None with the reason.

### Configuration Requirements

For each setting, four bullets:
- **What must exist** — the requirement, named.
- **Where it lives** — env var, config file, CI variable, secret store — described, not pasted.
- **Constraints** — allowed range, format, security class.
- **Missing-value behaviour** — default, error, or refuse-to-start.

Do not paste a real configuration file. The Developer writes the file against project conventions; this section tells them what the file must guarantee.

### Assumptions and Dependencies

Record assumptions and their confirmation basis, external dependencies, and failure implications.
Confirm premises that determine behavior or feasibility before approval.
If none apply, write None with a reason.

### Success Criteria

A numbered list of overall outcomes linked to the REQ identifiers that deliver them. These complement, rather than replace, per-requirement acceptance scenarios. Each one is measurable; see **Measurable success criteria** below.

### Implementation Order

Coarse phases (typically two to five). Each phase delivers an observable outcome. State each phase's dependency on the previous ones. A phase is NOT a task — `spec-breakdown` produces the actual tasks from these phases.

### Open Questions

Resolve questions affecting behavior, external contracts, acceptance, or feasibility before review, regardless of who can answer them.
Only deferred internal design investigations that cannot change approved behavior may remain; name their owner and resolution condition, or write None.

### Amendment Log

Leave empty when the spec is first written. Add rows only after Gate 1 approval when scope changes while tasks are in flight. Each scope amendment names the affected REQ/AC identifiers and tasks, and bumps the minor `version` (for example `0.1` → `0.2`). The one exception is a spec-truth reconciliation row from `architecture-consistency-review`, which records a verdict, changes no scope, and does not bump `version`.

---

## Measurable success criteria

A criterion is **measurable** when an outside party can run a check (command, observation, metric query) and get an unambiguous pass/fail.

Good: "Every PR targeting `main` shows a `ci/tests` check that has passed or failed within five minutes of opening."
Vague (avoid): "The CI is fast." "The CI works well." "Coverage is high."

If you cannot describe how to verify a criterion, it is not yet measurable — rewrite it.

---

## Pre-submission checklist

Before returning the created spec, confirm every item:

- [ ] **Problem is concrete.** Purpose names the problem, the trigger, and the observable outcome.
- [ ] **At least one exclusion.** Or a human-confirmed "no exclusions apply" statement.
- [ ] **Each design principle is a constraint, not an implementation choice.**
- [ ] **No implementation artefacts.** No full config files, no CI manifests, no function-by-function decompositions. Any literal-value-as-contract block is labelled **Contract**.
- [ ] **Every requirement is measurable.** It has one obligation, a stable REQ identifier, concrete AC scenarios, and a verification method.
- [ ] **Discovery decisions are preserved.** Actors, journeys, applicable failure cases, and quality constraints are explicitly linked to requirements.
- [ ] **Assumptions and dependencies are explicit**, with behavior-affecting premises confirmed.
- [ ] **No unresolved behavioral questions remain**; deferred internal investigations have an owner and resolution condition.
- [ ] **Structural validation passes.** Run `ai-team validate --specs` on the review-ready document, and assess completeness, terminology, feasibility, and contradictions semantically. The validator does not prove these properties.
- [ ] **Interfaces are described for this spec's own component or feature**, with sufficient external contract detail. Public schemas may be named or included as Contract material; internal implementation inventories are excluded.
- [ ] **Success Criteria are listed**, each one measurable.
- [ ] **Implementation Order has coarse phases**, not tasks.
- [ ] **Amendment Log is empty** (until amendments arrive after Gate 1).

Items genuinely unresolvable at write-time may be left `[TODO]`, but human-answerable `[TODO]` markers block Architecture Consistency Review and Gate 1 until they are resolved. Everything else must be checked before returning.
