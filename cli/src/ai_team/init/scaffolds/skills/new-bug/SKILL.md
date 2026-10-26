---
name: new-bug
description: Create a new bug report via the ai-team CLI. Use when a defect, regression, or out-of-scope finding must be filed as a bug.
argument-hint: "[optional: bug title]"
allowed-tools: Read, Write, Bash
---

# New Bug

Create a new bug report using `ai-team bug new --json`.

## Input Requirements

Required:
- `title`
- `summary` (the bug template's Summary section)
- `severity` (`critical`, `high`, `medium`, or `low`)

Optional:
- `task` (task reference such as `T-021`)
- `details` (extra content for other bug template sections, such as Reproduction Status, Reproduction Steps, Environment, or Suspected Area, keyed by section name)

For **integration-filed regression bugs** (bugs discovered during or after integration of a
task branch), the following additional fields are required:
- `source_branch` — the task or bug branch where the regression was introduced (e.g. `task/T-021-...`).
- `expected_behavior` — the expected behaviour before the regression (Expected Behavior section).
- `actual_behavior` — the actual (broken) behaviour observed (Actual Behavior section).
- `evidence` — test output, logs, or other observable evidence (Evidence section).
- `fix_verification` — the test command or manual step that will confirm the regression is resolved (Fix Verification section).

When invoked by another skill, the caller should provide every required field in the invocation text and this skill must use them without asking follow-up questions.
When invoked directly by the product owner and required fields are missing, ask only for the missing fields before proceeding.

## Procedure

1. Resolve inputs from the caller. Use `$ARGUMENTS` as `title` when it is the only provided input.
2. Build the CLI command:
   - Base: `ai-team bug new "<title>" --severity "<severity>" --json`
   - Add `--task "<task>"` only when `task` is provided.
   - Add `--source-branch "<source_branch>"` only when `source_branch` is provided.
3. Execute the command and parse the JSON response to capture the created bug file path and ID.
4. Open the created bug file and fill the Summary section from the supplied `summary`.
5. If `details` content is provided, replace only the matching details placeholders/sections supplied by the caller. Leave unspecified sections unchanged.
6. For regression bugs, populate the regression fields in the bug file:
   - Confirm the frontmatter `source_branch` matches the value passed with `--source-branch`.
   - Fill in the expected and actual behaviour sections.
   - Fill in the evidence section with the supplied observable evidence.
   - Fill in the fix-verification section.
7. Confirm the file exists at the path the CLI returned (the tracker's `bugs/` folder, status `open`) and return the created path and ID.
   The bug file is outside version control: never commit it, from any branch.
