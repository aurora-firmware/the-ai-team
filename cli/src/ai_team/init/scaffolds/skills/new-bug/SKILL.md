---
name: new-bug
description: Create a new bug report via the ai-team CLI. Use when a defect, regression, or out-of-scope finding must be filed as a bug.
argument-hint: "[optional: bug title]"
allowed-tools: Read, Write, Bash
---

# New Bug

Create a new bug report using `ai-team bug new --json`.

## Input Requirements

Argument: `$ARGUMENTS`

Required:
- `title`
- `summary` (the bug template's Summary section)
- `severity` (`critical`, `high`, `medium`, or `low`)

Optional:
- `task` (task reference such as `T-021`)
- `source_branch` — for a regression found at integration, the task or bug branch that introduced it (e.g. `task/T-021-...`)
- `details` — content for other bug template sections, keyed by section name, written as the heading or in snake case (`Expected Behavior` or `expected_behavior`). When `source_branch` is set, `details` must include Expected Behavior, Actual Behavior, Evidence and Fix Verification.

When invoked by another skill, the caller should provide every required field in the invocation text and this skill must use them without asking follow-up questions.
When invoked directly by the product owner and required fields are missing, ask only for the missing fields before proceeding.

## Procedure

1. Resolve inputs from the caller. Use the argument as `title` when it is the only provided input.
2. Build the CLI command:
   - Base: `ai-team bug new "<title>" --severity "<severity>" --json`
   - Add `--task "<task>"` only when `task` is provided.
   - Add `--source-branch "<source_branch>"` only when `source_branch` is provided.
3. Execute the command and parse the JSON response to capture the created bug file path and ID.
4. Open the created bug file and fill the Summary section from the supplied `summary`.
5. Replace only the sections that `details` supplies; leave the others unchanged.
6. When `source_branch` was passed, confirm the frontmatter `source_branch` matches it.
7. Confirm the file exists at the path the CLI returned (the tracker's `bugs/` folder, status `open`) and return the created path and ID.
   The bug file is outside version control: never commit it, from any branch.
