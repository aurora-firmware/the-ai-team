# Spec Authoring Guide

A practical playbook for writing a specification that passes Gate 1 and gives the Planner enough information to decompose it into atomic tasks.

This guide is for the **author** of a spec — usually the Planner working interactively with the product owner during `/brainstorm`. Read it once before writing your first spec; refer back to the section recipes while writing.

## Before you write

A specification is a **contract**, not an implementation. Its readers are:

- The Planner, who must derive tasks from it.
- The Developer, who must satisfy every requirement.
- The Reviewer, who must verify the work matches the spec's intent.

Write so all three can do their job from the spec alone, without guessing what you meant.

## The content boundary

> A specification describes what the product does: requirements, interface contracts, and measurable criteria in prose. It does not say how the product is built.

The spec owns the *what*. The project's architecture documents and ADRs own the *how*: technology, protocol stacks, and implementation design. The coding guidelines own how code is written with that stack. The Architect decides the how for a spec after Gate 1, in Feature Architecture; the spec never decides it, even when an ADR has already done so.

**Belongs in the spec:** the problem, the outcome, the constraints, the interface contracts of the component or feature it covers (the decomposition into components lives in S-000), the settings users configure, the success criteria, the exclusions.

**Does not belong in the spec:**

- **Technology choices** — languages, frameworks, libraries, storage engines, internal protocols and formats, hosting and services. State the requirement the technology must meet instead: "settings survive a restart", not "settings are stored in SQLite".
- **Implementation design** — internal components and their responsibilities, system diagrams of internals, data models, rejected implementation approaches.
- **Implementation artefacts** — function signatures, class layouts, full YAML/TOML/JSON config files, complete CI manifests, executable code that *is* the implementation, file-by-file task lists.

**Contract material:** a code, schema, or config block is allowed when it defines an external contract — a public API schema or field definition, a wire-protocol fragment, an externally fixed configuration key. Label it **Contract**, not **Example**, and size it to the contract's ambiguity and risk. A technology or format is part of an interface only when users or external systems see it: the format of a configuration file users edit, or a protocol an external system already speaks. A protocol or format the team picks for its own parts is a technology choice. Internal implementation is never contract material.

If you find yourself pasting a near-complete file, you are writing the implementation. Stop. Describe what the file must guarantee instead.

## Feature specification contract

Feature specifications follow the section and requirement rules below.
S-000 is the system overview and follows its own seven-section contract.

Every observable obligation has a stable `REQ-NNN` identifier and one behavior, with normative SHALL or MUST wording.
Keep rationale separate from the obligation.
Use the same identifier space for behavioral and quality requirements; never renumber or reuse identifiers after approval.
Record removed requirements and affected identifiers in the Amendment Log.
Each requirement has one or more acceptance headings `#### AC-NNN.M — Scenario title`, where NNN matches its requirement and M is a positive scenario number.
Each scenario states concrete conditions and expected results, normally Given/When/Then, and includes `**Verification:**` naming one of the verification methods below and the observation that establishes the result.
Numbering identifies obligations; it does not make vague prose precise.

Run `ai-team validate --specs` once the spec is in `review`; drafts may still contain placeholders.
The CLI usage guide lists what the validator checks.
Those checks are structural only: the author and reviewer still evaluate completeness, feasibility, and correctness.

## Verification methods

This section owns the verification vocabulary. Specs, tasks, skills, and process documents use these three methods and no others. The `new-task` skill implements them for tasks, and the other skills refer to it.

- **Test** — an automated check in the project's test suite that runs the product and passes or fails by assertion. Use it for behavior the product exhibits. A test may check structure the product depends on, such as frontmatter that must parse. A test never asserts the wording of prose: skills, process documents, guides, user documentation, or specs.
- **Inspection** — someone reads the changed artifact, checks the observation each criterion states, and records what was checked and the pass or fail result. For a task, the Developer carries out and records the inspection, and the Reviewer re-checks it. For prose, the inspection also checks that the text agrees with its references: the source spec, each accepted ADR, and S-000 when it exists. Use it for prose, configuration, and changes that only remove something.
- **Demonstration** — someone runs the product or a pipeline once, outside the test suite, and observes the outcome. The record names the command or steps and the observed result. Use it when the behavior depends on an environment the test suite cannot reproduce, such as a CI run. A task's demonstration must be observable from the task branch, for example a CI run on the pushed branch, because its record is checked before the branch is integrated.

A task takes the method its source criteria name, and has one method. When the criteria a piece of work covers name different methods, split it into one task per method. When the source is a change-request or S-000, which have no acceptance criteria, the Planner applies the same rule: a test for product behavior that is added or changed, an inspection for prose, configuration, or a change that only removes something, and a demonstration for behavior that depends on the environment.
Whatever the method, the project's full test suite, when the project documents one, still runs as a regression check.

## How to write each section

The spec template follows this structure. The recipes below tell you how to write each section well, with a strong and a weak example for each.

### Purpose

**Recipe:** Three to four sentences, naming the S-000 component the spec covers.
1. The problem (what is broken or missing today).
2. Why it matters now (the constraint or trigger that forced the spec).
3. The outcome (what is observably true when the work is done).
4. Optional: the metric that confirms success.

**Strong:**
> CI does not run on pull requests, so broken tests reach `main` and block the next release. After the last release was delayed twice by lint failures discovered post-merge, we need automated checks on every PR. When this spec is satisfied, every PR targeting `main` runs the full test and lint suite before merge is enabled, and a failing check blocks the merge button in GitHub.

**Weak:** "Add CI to the project." (No problem, no outcome, no success metric.)

### Users and Journeys

Identify each relevant actor, including downstream systems, their goal, and the end-to-end journey this feature changes.
Name the priority and independent acceptance outcome of each journey; reference the REQ identifiers that establish that outcome.
S-000 supplies the system context, but this section records the feature-specific experience.

### Exclusions

**Strategy:** record each behavior deliberately outside scope with its reason. Keep rejected alternatives and their rationale distinct from exclusions: choosing one solution does not automatically exclude a user capability.

Almost every spec has at least one exclusion. "No exclusions apply" should be rare, and should follow an explicit confirmation from the product owner.

**Strong:**
> - **Deployment pipelines.** Excluded because this spec covers PR validation only; release pipelines are tracked separately under S-NNN.
> - **Coverage reporting.** Excluded because the team has not decided on a threshold; revisit after one month of PR-validation data.

**Weak:** "No exclusions." (Almost never true; often masks unresolved scope.)

### Alternatives Considered

**Recipe:** list each solution alternative rejected during brainstorm and the reason it was rejected: a different behaviour, interaction, or interface for the same need. Rejected alternatives are rationale; excluded behavior goes in Exclusions. Rejected implementation approaches are not recorded here; the Architect records them in an ADR. If no alternative was considered, write `None` with the reason.

A constraint the solution must meet, such as a time limit or a rejection rule, is a requirement: write it as a Behavioral or Quality Requirement.

**Strong:**
> - **Blocking the merge by a reviewer's manual check.** Rejected because reviewers missed failures on busy days; an automated check blocks every PR the same way.

**Weak:** "Rejected Jenkins in favour of GitHub Actions." (An implementation choice; it belongs in an ADR.)

### Interfaces

**Recipe:** describe the external contracts exposed and consumed by this feature, with detail proportional to ambiguity and risk.
Include relevant inputs, outputs, validation, error outcomes, authorization, and compatibility guarantees; reference the REQ identifiers that own them.
A precise referenced public schema is acceptable when its location and contract version are unambiguous.
Public field definitions and protocol fragments are allowed as **Contract** material; internal function lists, private class layouts, and implementation inventories are not.
There is no fixed line limit.
Do not repeat other components' internals; use S-000 for system-wide context.

### Workflow

**Recipe:** end-to-end flow from trigger to completion. Each step is a sentence or short phrase. Mark product owner gates with ★. Include applicable failure, boundary, empty-input, concurrent-access, and state-dependent paths, referencing their requirement identifiers.

**Strong:**
```
PR opened or updated
  ↓
CI runner triggers test + lint suite
  ↓
Results posted as PR check
  ↓
★ Product owner approves or requests changes
  ↓
Merge enabled / blocked by check status
```

**Weak:** a code-flow walkthrough of one CI runner.

### Behavioral Requirements

Use `### REQ-001 — Short title` headings for one observable behavior each.
State the triggering event or state and the required outcome, using EARS when helpful.
Under each requirement, add concrete `#### AC-001.1 — Scenario title` cases and a `**Verification:**` line for each case that names its method (see Verification methods).
Include the applicable success, rejection, boundary, and recovery cases rather than restating the requirement as its only example.
Every approved discovery decision about behavior must appear in a requirement; task decomposition must not invent missing product decisions.

### Quality Requirements

Use the same REQ and AC conventions for applicable security, privacy, accessibility, performance, reliability, compatibility, and recovery guarantees.
Specify measurement conditions and thresholds when agreed; never invent targets or copy arbitrary example numbers.
Review each category and document meaningful non-applicability briefly; do not manufacture requirements to fill a template.
If none apply, state that conclusion and its reason instead of leaving placeholder requirements.

### Configuration Requirements

**Recipe:** for each setting, four bullets:

- **What must exist** — the requirement, named.
- **Where it lives** — where the user sets it: env var, config file, CI variable, secret store — described, not pasted.
- **Constraints** — allowed range, format, security class.
- **Missing-value behaviour** — default, error, or refuse-to-start.

Do not paste a real configuration file. The Developer writes the file against the project's conventions; this section tells them what the file must guarantee.

**Strong:**
> - **Test command.** Must be discoverable from the project's `AGENTS.md` or `ai-team/docs/coding_guidelines.md`. The CI runner must read it from there, not hard-code it. If not found, the runner must fail with an actionable error rather than guessing.

**Weak:** a 20-line `ci.yml` snippet.

### Assumptions and Dependencies

Record explicit assumptions, their confirmation or validation basis, and external dependencies and their failure implications.
An assumption that determines behavior or feasibility must be confirmed before approval.
State `None` with a reason when there are none; do not silently omit this review.

### Success Criteria

**Recipe:** a numbered list of measurable overall outcomes linked to the requirements that deliver them. These outcomes complement, rather than replace, per-requirement acceptance scenarios. Each one is measurable; see [How to write measurable success criteria](#how-to-write-measurable-success-criteria).

### Implementation Order

**Recipe:** coarse phases (typically two to five), each delivering an observable outcome. State each phase's dependency on the previous ones.

A phase is not a task. The `spec-breakdown` skill produces the actual tasks from these phases.

**Strong:**
> | Phase | What | Depends on |
> |---|---|---|
> | 1 | PR-validation pipeline runs and reports its result on every PR. | — |
> | 2 | Merge button is blocked when the pipeline fails. | Phase 1 |
> | 3 | Pipeline results are visible in the project status dashboard. | Phase 1 |

**Weak:** a list of file paths and the functions to edit in each.

### Open Questions

Before review or approval, resolve every question affecting required behavior, external contracts, acceptance, or feasibility, including technical questions the product owner cannot answer directly.
Record only deferred internal design investigations here, each with an owner and resolution condition; they must not change approved behavior.
A question for the Architect, such as a technology the product owner prefers, is recorded here with the Architect as owner and "decided in Feature Architecture" as its resolution condition. It is a preference to weigh, not a choice the spec makes.
Write `None` when no investigations remain.
Product-owner-answerable `[TODO]` markers must be resolved before Architecture Consistency Review; unresolved behavioral questions block it regardless of who can answer them.

### Amendment Log

**Recipe:** leave the table empty when the spec is first written. Add rows only after Gate 1 approval, when scope changes while tasks are in flight. Each row: date, what changed, why, affected requirements and tasks. Each amendment bumps the spec's minor `version` (for example `0.1` → `0.2`). A spec-truth reconciliation row records a verdict, changes no scope, and does not bump `version`.

## The system overview spec (S-000)

S-000 is the canonical project-overview spec: one document that says what the project is, who it serves, and which components make it up. It is written in plain language for a reader who has never seen the project. It has seven sections, in this order:

1. **Purpose** — one short paragraph: what the project is and the outcome it exists to deliver.
2. **Users** — the users of the solution and in what situations, one line per kind of user, naming what each needs from it.
3. **Pain points** — the concrete problems those users have today that the project removes.
4. **Use cases** — the main things a user does with the system, each as one short scenario from the user's point of view and each tied to the pain point it removes.
5. **Solution overview** — how the system addresses the pain points, in a few paragraphs, without naming technologies.
6. **Components** — the parts the system is divided into. Each component entry gives its name, its owned responsibility (what it is for), its boundary (what it is not responsible for), and the other components it works with. Components are split into the Solution and Development infrastructure groups (below).
7. **Project exclusions** — what the project deliberately does not do, each with a one-line reason.

S-000 contains no technology choices, interface definitions, configuration, implementation order, or per-component status. Interface definitions, configuration, and implementation order belong in feature specs; technology choices in the architecture documents and ADRs; per-component status in the tracker.

**What a component is.** A component is a part of the software solution, or something that affects the solution's use, delivery or deployment. A component can be software, documentation (internal or for end users), delivery and deployment (pipelines, scripts), or tooling (development environment, debugging interfaces, test harnesses). Each component passes three checks: it serves at least one use case, or, in the infrastructure group, affects the solution's use, delivery or deployment; one spec could own its contract; and its boundary would hold if the implementation were reorganised.

**Component groups.** Components fall into two groups, written as `### Solution` and `### Development infrastructure` subsections of Components; the seven top-level sections and their order do not change.

- **Solution** — the software delivered to the end user that removes the pain points.
- **Development infrastructure** — everything the project needs to build, check, document and deliver the solution; it is not delivered to the end user. Each infrastructure component also has a **Decisions needed** field: the questions that must be answered before development starts, such as the language and version, how the environment is reproduced, the test harness, the continuous-integration service, and where decisions are recorded. S-000 asks technology questions and never answers them; the answers belong in the project's architecture documents and ADRs, which the project bootstrap writes.

**Users scope.** Users names the users of the solution. The people and agents who develop the project are served by the development infrastructure and are not listed unless they also use the solution.

**Boundary rule:** S-000 owns the decomposition — which components exist and what each is for. A spec owns the contract of one component or feature. A spec's Purpose names the S-000 component it covers.

## How to write measurable success criteria

A criterion is **measurable** when an outside party can run a check (a command, an observation, a metric query) and get an unambiguous pass or fail. The Reviewer must be able to run this check.

**Good:**
- "Every PR targeting `main` shows a `ci/tests` check that has either passed or failed within five minutes of the PR being opened."
- "Merging a PR with a failing `ci/tests` check is rejected by branch protection (verified by attempting the merge and observing the API response)."

**Vague (avoid):**
- "The CI is fast."
- "The CI works well."
- "Coverage is high."

If you cannot describe how to check whether a criterion is met, the criterion is not yet measurable.

## Worked example (compact)

The following is a requirement block, not a complete specification.
The rest of the template still records purpose, journeys, exclusions, contracts, assumptions, and overall outcomes.

```markdown
## Behavioral Requirements

### REQ-001 — Reject unauthorized exports

WHEN an actor requests an export for a workspace they cannot access,
THE SYSTEM SHALL reject the request without returning workspace records.

#### AC-001.1 — Workspace access denied

- **Given:** an actor without access to workspace A
- **When:** the actor requests an export from workspace A
- **Then:** the request is rejected and no workspace records are returned

**Verification:** an authorization acceptance test for AC-001.1.
```

The identifier lets a journey, task, review, and test refer to the same obligation.
The scenario records an observable outcome without prescribing the implementation.

## Pre-submission checklist

Before declaring the spec ready for Gate 1, the author confirms each of these:

- [ ] **Problem is concrete.** Purpose names the problem, the trigger, and the observable outcome.
- [ ] **At least one exclusion.** Or a product-owner-confirmed "no exclusions apply" statement.
- [ ] **No technology choices or implementation design.** No languages, frameworks, libraries, storage engines, internal protocols or formats, internal components, or rejected implementation approaches. A technology appears only as Contract material, when users or external systems see it.
- [ ] **Alternatives Considered lists solution alternatives**, each with its reason, or `None` with a reason.
- [ ] **No implementation artefacts.** No full config files, no CI manifests, no function-by-function decompositions. Where a literal value is the contract, it is labelled **Contract**.
- [ ] **Every requirement is measurable.** Each has a stable REQ identifier, one obligation, concrete acceptance scenarios, and a verification method.
- [ ] **Discovery decisions are preserved.** Actors, journeys, applicable failure cases, and quality constraints are recorded and linked to requirements.
- [ ] **Assumptions and dependencies are explicit.** Behavior-affecting premises are confirmed; deferred internal investigations have an owner and resolution condition.
- [ ] **No unresolved behavioral questions remain**, regardless of who can answer them.
- [ ] **Structural validation passes.** Run `ai-team validate --specs`; also review completeness, consistent terminology, feasibility, and contradictions semantically.
- [ ] **Interfaces are described for this spec's own component or feature**, with sufficient externally observable contract detail. Public schemas may be named or included as Contract material; internal implementation inventories are excluded.
- [ ] **Success Criteria are listed**, each one measurable.
- [ ] **Implementation Order has coarse phases**, not tasks.
- [ ] **Amendment Log is empty** (until amendments arrive after Gate 1).

If every box is checked and Architect consistency findings are resolved, the spec is ready for product owner Gate 1 approval.

## Implementations of this guide

The recipes above are embedded into the CLI sources that fire when `/new-spec` is invoked or when `/brainstorm` produces a spec. Update them together when this guide changes:

| Implements this guide | File |
|---|---|
| Spec document shape | `cli/src/ai_team/templates/spec.md` |
| Section-by-section authoring instructions used by `/new-spec` | `cli/src/ai_team/init/sources/skills/new-spec/SKILL.md` |
| Spec-writing handoff in interactive brainstorm | `cli/src/ai_team/init/sources/skills/brainstorm/SKILL.md` |
| Planner role's spec quality bar | `cli/src/ai_team/init/sources/agents/planner.md` |
| Structural validation of review-ready feature specs | `cli/src/ai_team/core/spec_content.py` |
| System overview (S-000) document shape | `cli/src/ai_team/templates/system-overview.md` |
| Authoring instructions used by `new-system-overview` | `cli/src/ai_team/init/sources/skills/new-system-overview/SKILL.md` |

After changing this guide, mirror the relevant content into the files above and regenerate scaffolds with `cli/scripts/sync_init_scaffolds.py`.
