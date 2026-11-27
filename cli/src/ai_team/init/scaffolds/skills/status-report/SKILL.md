---
name: status-report
description: Generate a Gate 5 project status report on demand by scanning specs, tasks, bugs and decisions, and running the test suite on the integration branch. Use when the product owner asks for project status or final merge sign-off context.
allowed-tools: Read, Glob, Grep, Write, Bash, Skill(git-conventions)
---

# Status Report

The development and bug-fix loops never invoke this skill; they end with a short run summary.

## Input Requirements

- **The `ai-team` CLI:** `ai-team status` and `ai-team report`.
- **Project state:** specs in `{{project_dir}}/specs/`, ADRs in `{{project_dir}}/decisions/`; tasks, bugs and change-requests in the local tracker.

## Procedure

### Step 1: Print the Summary

Run `ai-team status` from the repository root.
Its output is the inline summary: counts of specs, tasks by status, bugs by status (including `Blocked bugs`) and ADRs; the in-progress tasks; the blocked tasks and bugs with their reasons; and the critical and high unresolved bugs.
Use it as printed. `ai-team status --json` gives the same data (`blocked_tasks`, `blocked_bugs`, …) when you need to reason over it.

If the command cannot run, collect the same data and present it in the CLI's format:

- tasks and bugs by status from `ai-team list tasks --json` and `ai-team list bugs --json`: tasks `planned`, `pending`, `in-progress`, `completed`, `blocked`, `cancelled`; bugs `open`, `in-progress`, `blocked`, `resolved`;
- specs and ADRs counted from their folders, excluding templates and `.gitkeep`;
- the blocking reason of each blocked task or bug from its Work Log.

```markdown
## Status Report

### Summary
- Active specs: N
- Planned tasks: N
- Pending tasks: N
- In progress: N
- Completed: N
- Blocked: N
- Cancelled tasks: N
- Open bugs: N
- Bugs in progress: N
- Blocked bugs: N
- Resolved bugs: N
- ADRs: N

### In Progress
[ID — title (assigned role), or "none"]

### Blocked
[blocked tasks and bugs: ID — title: blocking reason, or "none"]

### Unresolved Critical/High Bugs
[unresolved bugs: ID — title (severity), or "none"]
```

### Step 2: Run the Integration Tests

Gate 5 needs the test suite green on `{{integration_branch}}` as it stands now.
Find the project's baseline command with the Discovery Order of the `integrate` skill, check out `{{integration_branch}}` (Workspace Hygiene of `git-conventions` first), run the command from the repository root, and return to the branch you started on.
Append `Integration tests: <command> on <short sha> — <passed | failed: failing tests>` after the summary. When no command is documented, write `Integration tests: no automated command documented`.

### Step 3: Check Completion Reconciliation

When no task is `pending`, `in-progress` or `blocked` (cancelled tasks are allowed), check that the Architect's completion reconciliation (`architecture-consistency-review` in completion mode) has run for each approved spec the work touched, S-000 excluded.
Read the dated `spec-truth reconciliation` line in the spec's Amendment Log, or in the change-request file for change-request work.
Gate 5 needs a `PASS`, or every routed correction done: an applied spec amendment, or a follow-up task completed and re-reviewed.
Append the reconciliation state after the summary.

### Step 4: Recommend Actions

When there are blocked tasks or bugs, critical or high unresolved bugs, failing integration tests, or a reconciliation that has not passed, append a `Recommended Actions` section with the next step for each.

### Step 5: Write the Report File (Only When Asked)

Only when the product owner asks for a file, run `ai-team report`.
It writes `{{project_dir}}/docs/reports/progress-report-<today>.md`, which the scaffolded `.gitignore` ignores.
Tell the product owner the path, and commit the file only if they ask.

## Output Format

- **Inline summary:** the `ai-team status` output, then the integration test line, the reconciliation state and any `Recommended Actions`.
- **Report file:** only when the product owner asked for one.

## Quality Criteria

- Critical and high unresolved bugs are listed, and every blocked task and bug has its reason when one is recorded.
- The sign-off integration test run is stated, or marked as not documented.
- When the queue is drained, the reconciliation state is stated.
- The report gives the product owner enough context for Gate 5 sign-off, a status sign-off rather than a code review.
