---
name: new-spec
description: Create a new specification document via the ai-team CLI. Use when a feature design is ready to be written up as a spec.
argument-hint: "[optional: specification title]"
allowed-tools: Read, Write, Bash, Skill(git-conventions)
---

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

4. Open the created spec file and fill its body sections from the supplied `description`, using the **content-boundary rule** and the **section recipes** below. Leave any section that still needs exploration marked `[TODO]`.

5. Run the **pre-submission checklist** (below) against the filled spec. Fix any unchecked item before returning. Leave items genuinely unresolvable marked `[TODO]`.

6. Inspect the draft for human-answerable `[TODO]` markers before any review handoff.
   - Human-answerable `[TODO]` markers must be resolved before Architecture Consistency Review.
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

### Exclusions

For every alternative rejected during brainstorm, and every scope-expanding question the human said "no" to, write an explicit exclusion with the reason.

Almost every spec has at least one. `"no exclusions apply"` should be rare and should follow an explicit human confirmation.

### Architecture — Design Principles

Scoped to this spec. Each principle is a **constraint on the design space**, not an implementation choice. State it as a property the design must satisfy.

Good: "Validation must run in under three minutes on the median PR."
Bad: "Use GitHub Actions." (That picks the implementation; reframe as a constraint, e.g. "must integrate with the project's existing PR review surface.")

### Interfaces

Cover the component or feature of this spec only. System-wide structure lives in S-000; the Purpose names the S-000 component the spec covers.

Three lines max:
- **Purpose:** one sentence — what it does.
- **Estimated size:** small / medium / large, or rough effort.
- **Interfaces:** exposed and consumed, named at the interface level.

No function lists. No field lists.

### Workflow

End-to-end flow from trigger to completion. Each step is a sentence or short phrase. Mark human gates with `★`. Include error paths only when a failure mode is interesting.

### Configuration Requirements

For each setting, four bullets:
- **What must exist** — the requirement, named.
- **Where it lives** — env var, config file, CI variable, secret store — described, not pasted.
- **Constraints** — allowed range, format, security class.
- **Missing-value behaviour** — default, error, or refuse-to-start.

Do not paste a real configuration file. The Developer writes the file against project conventions; this section tells them what the file must guarantee.

### Success Criteria

A numbered list of criteria that together show the spec is satisfied. Each one is measurable; see **Measurable success criteria** below.

### Implementation Order

Coarse phases (typically two to five). Each phase delivers an observable outcome. State each phase's dependency on the previous ones. A phase is NOT a task — `spec-breakdown` produces the actual tasks from these phases.

### Amendment Log

Leave empty when the spec is first written. Add rows only after Gate 1 approval when scope changes while tasks are in flight. Each amendment bumps the minor `version` (for example `0.1` → `0.2`). The one exception is a spec-truth reconciliation row from `architecture-consistency-review`, which records a verdict, changes no scope, and does not bump `version`.

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
- [ ] **Every requirement is measurable.** An outside reader can describe how to verify it.
- [ ] **Interfaces are described for this spec's own component or feature**, at the interface level. No method signatures, no attribute lists.
- [ ] **Success Criteria are listed**, each one measurable.
- [ ] **Implementation Order has coarse phases**, not tasks.
- [ ] **Amendment Log is empty** (until amendments arrive after Gate 1).

Items genuinely unresolvable at write-time may be left `[TODO]`, but human-answerable `[TODO]` markers block Architecture Consistency Review and Gate 1 until they are resolved. Everything else must be checked before returning.
