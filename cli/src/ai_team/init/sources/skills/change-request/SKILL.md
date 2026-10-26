---
name: change-request
description: Create a new change-request artifact via the ai-team CLI. Use when a small change does not warrant a full spec.
argument-hint: "[change request title]"
allowed-tools: Read, Write, Bash, Skill(git-conventions)
---

# Change Request

Create a new change-request artifact using `ai-team change-request new --json`, then fill the body with the proposed scope change.

## Input Requirements

Provide these values directly when possible:
- `title` — required
- `description` — required; summarize the requested change, why it is needed, affected specs or tasks, and any known risk

When invoked directly and required fields are missing, ask only for the missing fields before proceeding.

## Procedure

1. Resolve inputs:
   - Use the caller-provided `title` and `description` when present.
   - Use `$ARGUMENTS` as the title when it is the only provided input.
   - If the title or description is still missing, ask for the missing value.

2. Open the planning branch and create the artifact:
   - Follow **Opening a Planning Branch** in the `git-conventions` skill, running `ai-team change-request new "<title>" --json` at its step 3.
   - Parse the JSON response to capture `id` and `path`.
   - The change-request file is created in the local tracker, outside version control: never commit it.
   - The planning branch carries only the spec amendments the change-request drives and any ADRs raised by its consistency review. Nothing reaches `{{integration_branch}}` until Gate 2 passes and `spec-breakdown` merges the branch.

3. Open the created file and replace template placeholders with the supplied description.
   - Keep the frontmatter produced by the CLI.
   - Preserve the template structure unless the product owner explicitly requested a different format.
   - Mark unknown details as `[TODO]` instead of inventing them.

4. Confirm the created file exists and return the CLI response values and the planning branch name.

5. For a newly created CR or an updated CR body, inspect the document for product-owner-answerable `[TODO]` markers.
   - Resolve each product-owner-answerable `[TODO]` marker one at a time with the product owner.
   - Before each question, cite the relevant CR section so the product owner can answer in context.
   - After each answer, update the CR and re-scan for the next product-owner-answerable `[TODO]`.
   - Complete this loop before asking for approval; do not ask for approval while any product-owner-answerable `[TODO]` marker remains.

6. When the CR is TODO-free, ask the product owner to approve the full change-request as written.
   - On approval, run `ai-team change-request set-status <id> approved`.
   - On rejection, run `ai-team change-request set-status <id> rejected`, set any of its `planned` tasks to `cancelled`, and ask the product owner whether to delete its planning branch. Stop.

7. After the product owner approves the TODO-free CR, continue directly into Architecture Consistency Review rather than stopping with only a passive handoff.
   - Pass the approved change-request path and delta as the changed artifact under review.
   - Treat the approved change-request as the authoritative intent for any downstream consistency fixes.
   - If review findings can be resolved without changing that approved intent, route the corrections to the owning role and continue the process.
   - Only findings that would change the approved change-request intent stop for product owner decision.

## Quality Criteria

- The artifact id and path come from the CLI response.
- The title is reflected in the file heading.
- The body states the requested change, reason, affected artifacts, and unresolved questions.
- Each proposed feature-spec amendment names the REQ and AC identifiers it adds, changes, or retires.
- Unknown or unconfirmed details remain marked `[TODO]`.
- Product-owner-answerable `[TODO]` markers are resolved one at a time before approval.
- A TODO-free CR continues into Architecture Consistency Review instead of ending with only a passive handoff.

## Common Pitfalls

- **Raising a change-request when a new spec is warranted** — if the proposed change adds a significant new capability, a new workflow, or a new system component, open a spec instead. A change-request is for scope amendments to an existing, approved spec, not a vehicle for speccing new work.
- **Vague change description** — "update the spec" or "fix the task" is not a change description. Name the specific section, requirement, or acceptance criterion that must change and state why the current wording is wrong or incomplete.
- **Missing affected-artifact list** — every change-request must name the specs, tasks, or other artifacts it touches. Omitting this forces reviewers to guess the blast radius and risks silent conflicts with in-flight tasks.
- **Missing risk notes** — if the change could break a dependency, invalidate work already in progress, or require re-review of a gate, say so. Silently omitting known risks is the most common reason change-requests are rejected or returned for revision.
- **Inventing details instead of marking `[TODO]`** — when the full impact of a change is not yet known, mark the gap `[TODO]` rather than filling it with plausible-sounding but unconfirmed content. Invented details mislead reviewers and produce incorrect downstream tasks.

## Output Format

Always return:

```text
Result: PASS | FAIL | BLOCKED

Summary:
- <brief statement of the change request created>

Artifacts:
- <change-request file created>

Evidence:
- <CLI command result or reason not run>

Obstacles Encountered:
- <missing input, unresolved scope issue, or "none">

Next Owner:
- <Product Owner | Planner | Architect | none>

Next Action:
- <specific follow-up required, or "none">
```
