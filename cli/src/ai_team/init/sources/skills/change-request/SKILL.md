---
name: change-request
description: Create a new change-request artifact via the ai-team CLI. Use when a small change to approved scope — requirements of existing specs added, changed or retired — does not warrant a new spec.
argument-hint: "[change request title]"
allowed-tools: Read, Write, Bash, Skill(git-conventions)
---

# Change Request

Create a change-request with `ai-team change-request new --json`, fill it with the proposed scope change, and take it to the product owner's approval.
A change that adds a significant new capability, workflow, or system component needs a spec instead (`brainstorm`, then `new-spec`).

## Input Requirements

Argument: `$ARGUMENTS`

- `title` — required.
- `description` — required: the requested change, why it is needed, the affected specs or tasks, and any known risk.

Use the argument as the title when it is the only input. When invoked directly and a required value is missing, ask only for it.

## Procedure

1. Open the planning branch and create the artifact.
   Follow **Opening a Planning Branch** in the `git-conventions` skill, running `ai-team change-request new "<title>" --json` at its step 3, and capture `id` and `path`.
   The change-request file is created in the local tracker, outside version control: never commit it.

2. Fill the created file from `description`, keeping the CLI frontmatter and the template structure unless the product owner asked for a different format.
   - Name the specific section, requirement, or acceptance criterion that must change, and why the current wording is wrong or incomplete.
   - Under Possible Spec Amendments, name for each feature spec the REQ and AC identifiers the amendment adds, changes, or retires.
   - Under Potential Impact, name every affected spec, task, or other artifact, and each risk: a dependency it could break, work in progress it could invalidate, a gate it could reopen.
   - Mark every detail you do not know `[TODO]`; never fill it with plausible content.

3. Resolve the product-owner-answerable `[TODO]` markers one at a time: cite the change-request section, ask, update the file, and re-scan for the next. Do the same whenever the body is updated later.

4. When the change-request is TODO-free, ask the product owner to approve it as written.
   - On approval, run `ai-team change-request set-status <id> approved`.
   - On rejection, run `ai-team change-request set-status <id> rejected`, ask the product owner whether to delete its planning branch, and stop.

5. After approval, stop and return `Next Owner: Architect`, with the Architect's `architecture-consistency-review` of the approved change-request (its path and the change it makes) as `Next Action`.
   When resumed with the review's findings, treat the approved change-request as the authoritative intent:
   - a finding that leaves that intent unchanged is a correction to make — update the change-request body;
   - a finding that would change the intent stops for the product owner's decision (`Next Owner: Product Owner`).
   Once the review passes, the change-request is ready for `spec-breakdown`, which applies its spec amendments.

## Output Format

Return the report `role-report` defines, with these values:

- **Result:** `PASS` | `FAIL` | `BLOCKED`.
- **Next Owner:** `Architect` after approval, for the consistency review; `Product Owner` when a decision or an answer is needed, or after a rejection; `none` once the review has passed and the change-request waits for `spec-breakdown`.
- **Artifacts:** the change-request `id` and `path`, and the planning branch.

## Quality Criteria

- The artifact id and path come from the CLI response, and the title is reflected in the file heading.
- The body states the requested change, reason, affected artifacts, risks, and unresolved questions.
- No product-owner-answerable `[TODO]` remains when approval is asked.
