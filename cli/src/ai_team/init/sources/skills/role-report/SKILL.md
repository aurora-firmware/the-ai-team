---
name: role-report
description: Defines the result report every AI-team role returns — its fields, the evidence entry forms, the allowed Result and Next Owner values, and how an escalation block is passed on. Use when a Planner, Architect, Developer, Reviewer or Integrator writes its final result, or when a caller reads one.
allowed-tools: Read
user-invocable: false
---

# Role Report

Every role ends its session with one report in the shape below.
The caller (the main session, an active loop, or the product owner) reads `Result` and `Next Owner` to decide what happens next, so both use only the values listed here.

## Input Requirements

- **The outcome of the session:** the result of the skill the role ran, the artifacts it touched, and the proof gathered with `evidence-before-claims`.
- **Required tools or dependencies:** none.

If a required input of the role is missing and cannot be inferred safely, ask the caller for it, or return `Result: BLOCKED` naming the missing input.
Never guess it.

## Procedure

### Step 1: Fill the Report

Return exactly these fields, in this order:

```text
Result: <one value from Step 2>

Summary:
- <what was done and the outcome, as the role's Summary hint describes>

Artifacts:
- <files, branches, commits, tracker items or ADRs created, updated, or read as primary evidence>

Evidence:
- <one entry per claim, in a form from Step 3>

Obstacles Encountered:
- <missing input, setup issue, workaround, special command flag, environment quirk, or "none">

Next Owner:
- <one value from Step 2>

Next Action:
- <the specific follow-up the Next Owner must take, or "none">
```

When the skill the role ran has its own output block (a Findings block, a Classification and Analysis, a `Reconciliation record:` line), put it inside the report after `Summary:` and do not repeat its verdict there.
The skill's verdict goes in `Result:`.

### Step 2: Choose Result and Next Owner

**Result:**

| Value | Meaning |
|---|---|
| `PASS` | The skill's work is complete and its check passed |
| `FAIL` | The check ran and found problems the caller must route back (corrections, open findings, a failed merge) |
| `BLOCKED` | A required input or precondition is missing; nothing was guessed |
| `ESCALATE` | The skill's self-recovery is exhausted or a boundary was hit; Step 4 applies |

A skill returns only the values it defines.
These skills use a subset:

| Skill | Result values |
|---|---|
| `code-review` | `PASS`, `FAIL`, `ESCALATE` |
| `feature-architecture` | `PASS`, `BLOCKED`, `ESCALATE` |
| `escalation-review` | `PASS` (guidance resolves the blocker), `BLOCKED` (request or work item missing), `ESCALATE` (product owner decision needed) |
| `change-request` | `PASS`, `FAIL`, `BLOCKED`, `ESCALATE` |

**Next Owner** names who acts on this report next.
A result that goes back to a running loop names that loop, which routes it on (to the Developer, the Reviewer, the Architect or integration); a role named outside a loop is spawned by the main session, and a loop named outside a loop run is one the product owner can start.

| Role | Allowed Next Owner values |
|---|---|
| Planner | `Product Owner`, `Architect`, `Development Loop`, `none` |
| Architect | `Planner`, `Development Loop`, `Bug-Fix Loop`, `Product Owner`, `none` |
| Developer | `Development Loop`, `Bug-Fix Loop`, `Architect`, `Product Owner`, `none` |
| Reviewer | `Development Loop`, `Bug-Fix Loop`, `Architect`, `Product Owner`, `none` |
| Integrator | `Architect`, `Product Owner`, `none` |

A role that stops mid-procedure to hand back for another role's step (the Planner in `spec-breakdown`) returns `Result: PASS` with that role as `Next Owner` and a `Next Action` naming the step to resume at.

Use these exact names.
Do not write `Loop`, `active loop`, `Requesting agent` or a role the table does not list.

### Step 3: Write the Evidence Entries

Prove each claim with `evidence-before-claims` first, then write one entry per claim in one of these forms:

| Proof | Entry form |
|---|---|
| A command you ran | `<claim> — <command> — <decisive output: exit code, pass and fail counts, relevant lines>` |
| Inspection of a file or artifact (a document, a spec, an inspection task, a verdict) | `<claim> — <path and line, section or verdict> — <what it says>` |
| A product owner approval | `<claim> — product owner: "<quoted confirmation>"` |
| A run another role recorded, cited instead of repeated | `<claim> (per <source, e.g. Work Log session N>: <command> — <output>)` |
| Nothing checked | `not verified: <claim> — <reason>` |

A claim with no proof is written only in the `not verified` form, never as done.
A cited run is labelled as cited and never presented as this role's own.

### Step 4: Pass On an Escalation

When `Result` is `ESCALATE`, append after the report the blocks the skill returned, unchanged: the four-field Escalation Request, the Product Owner Escalation Report, or both, as the skill produced them.
Do not rewrite the fields or merge blocks from several skills.

When the escalation arose outside a skill, fill the four fields `Problem`, `Attempted` (including the number of retries), `Failed because` and `Question` in the format `escalation-review` defines.

The role never forwards the escalation itself: the caller routes it to the Architect through `escalation-review`, or to the product owner when the Architect escalated.

## Output Format

- **Final response:** the report from Step 1, followed on `ESCALATE` by the blocks from Step 4.

## Quality Criteria

- Every field is present, with `none` where nothing applies.
- `Result` and `Next Owner` hold one allowed value each for the role and skill.
- Every `Evidence:` entry uses a form from Step 3.
