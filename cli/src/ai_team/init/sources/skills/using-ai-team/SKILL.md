---
name: using-ai-team
description: Establishes how to find and invoke the AI team's skills, and requires matching a skill to the situation before any other action. Use at the start of any request or work item, before clarifying questions, code search, or edits.
allowed-tools: Read, Glob, Grep, Bash, Agent, Skill
---

# Using the AI Team

Find and invoke the AI team's skills before acting.
The skills hold the procedures, gates, and artifact rules for this project; acting from memory instead of from the matching skill skips them.

## Input Requirements

- **The current request or work item:** the product owner's message, or the task, bug, spec, or change-request being worked.
- **Required tools or dependencies:** the `ai-team` CLI.

If you were dispatched as a subagent with an explicit task and a named skill, skip this skill and follow that skill instead.

## Procedure

### Step 1: Classify the Situation

Before the first action of a request — including a clarifying question, a code search, or a file edit — find the row below that matches the situation.

| Situation | Skill to invoke first |
|---|---|
| A feature request or problem needs a design before anything is built | `brainstorm`, then `new-spec` |
| `ai-team list specs` shows no `S-000`, or the project is being adopted into the ai-team process | Suggest the system overview (`new-system-overview`) before any feature spec. The product owner decides |
| S-000 is approved and `ai-team list tasks` shows no task naming S-000 as its source spec | Suggest the project bootstrap: `spec-breakdown` on S-000, which plans only the bootstrap tasks. The product owner decides |
| A small change does not warrant a full spec | `change-request` |
| A spec, ADR, or change-request was created or changed | `architecture-consistency-review` |
| An approved spec or change-request needs a task breakdown | `spec-breakdown` (run by the Planner) |
| The Planner returns `Next Owner: Architect` during `spec-breakdown` | Spawn the Architect with the Planner's inputs: `feature-architecture` at the start of the breakdown, `spec-breakdown-review` (Gate 2) once the tasks are written. Then resume the Planner with the Architect's report |
| A task is ready to implement | `tdd` |
| A bug, failing test, or unexpected behavior must be fixed | `debug`, then `tdd` for the fix |
| Completed task or bug work needs review | `code-review` |
| A Review Verdict lists Open findings that need answers | `receive-code-review` |
| A reviewed branch must be merged | `integrate`, and `merge-conflicts` when a conflict arises |
| Work is blocked after self-recovery was exhausted | `escalation-review` |
| The task queue is drained: no task of a spec or change-request is still pending, in progress or blocked | Before `/status-report` and Gate 5, have the Architect run `architecture-consistency-review` in completion mode (spec-truth reconciliation) for each approved spec the work touched, S-000 excluded |
| A spec, task, bug, or ADR must be created | `new-spec`, `new-task`, `new-bug`, or `new-adr` — never hand-create the file |
| Anything commits, branches, or merges | `git-conventions` |
| About to claim work is complete, passing, fixed, merged, or reviewed | `evidence-before-claims` |
| The product owner asks for project state or Gate 5 context | none — `status-report` is product-owner-invoked; tell the product owner to run `/status-report` |

A suggestion the product owner declines is not repeated in the same session; continue as before.

`dev-loop` and `bug-loop` start only when the product owner invokes them, and drive each work item through `review-cycle`. Never start either on your own.

### Step 2: Check the Gate Preconditions

The skill chain is gated.
Before starting a stage, confirm the artifact it needs exists:

1. Implementing a task needs a task that passed Gate 2, or a follow-up task routed by spec-truth reconciliation, which is exempt. Either one is `pending` or `in-progress` in the tracker and needs an approved spec or an approved change-request.
2. Fixing a bug needs a bug file with a Diagnosis Log, produced by `debug`.
3. Task breakdown needs a spec that is approved and free of product-owner-answerable `[TODO]` markers.
4. Integration needs a Reviewer PASS recorded in the task or bug file.
5. Merging the integration branch into `main` needs the product owner's Gate 5 sign-off.

If a precondition is missing, stop and report which artifact is missing and which skill produces it.
Do not do the earlier stage's work inline to get around it.

### Step 3: Invoke, Then Act

1. Invoke the matching skill and follow it exactly. If it carries a checklist, work through it in order.
2. When several skills match, invoke the process skill first (`brainstorm`, `debug`, `spec-breakdown`) and the implementation skill (`tdd`) after it.
3. When no row matches, proceed without a skill. Do not invent a match.
4. Instructions from the product owner and the project's root `AGENTS.md` take precedence over a skill. Skills take precedence over default behavior.

## Output Format

- **Final response:** none of its own. This skill ends by invoking the matching skill, or by stating that no skill applies.
- **When blocked:** name the missing precondition, the artifact that should satisfy it, and the skill that produces it.

## Common Pitfalls

- Treating a request as too small for a skill. A one-line fix still starts with `debug` or `tdd`.
- Remembering a skill instead of invoking it. Skills change; load the current text.
