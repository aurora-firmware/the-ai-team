---
name: status-report
description: Generate a Gate 5 project status report on demand by scanning specs, tasks, bugs, decisions, and integration evidence. Product-owner-invoked only — use when the product owner asks for project status or final merge sign-off context.
allowed-tools: Read, Glob, Grep, Write, Bash
disable-model-invocation: true
---

# Status Report

Reporting is for the product owner and runs only on demand: the product owner invokes `/status-report`.
The development and bug-fix loops never invoke this skill — they end with a short run summary instead.

## Input Requirements

- **Project state** — `{{project_dir}}/specs/` and `{{project_dir}}/decisions/` in the repository; tasks, bugs, and change-requests in the local tracker, read through `ai-team list`.
- **Integration evidence** — completed task Work Logs, resolved bug Work Logs, or recent integration commits when available.
- **AI team CLI** — `ai-team status` and `ai-team report` are available.

## Procedure

### Step 1: Generate Inline Summary

Run the CLI status command from the repository root:

```bash
ai-team status
```

The command scans the project state directories, excludes template files and `.gitkeep`, reads primary artifact metadata, inspects integration evidence, and prints the inline Gate 5 summary.

### Step 2: Count Current State

Count specs and ADRs in `{{project_dir}}/specs/` and `{{project_dir}}/decisions/`, excluding template files and `.gitkeep`.
Count tasks and bugs by status with `ai-team list tasks --json` and `ai-team list bugs --json` (the `state` field is the frontmatter `status`):
- tasks: `planned`, `pending`, `in-progress`, `completed`, `blocked`, `cancelled`
- bugs: `open`, `in-progress`, `resolved`

### Step 3: Read Primary Artifacts

Read active specifications and list title, status, and latest amendment or version if present.
For each task with status `in-progress`, read the frontmatter and list ID, title, and assigned role.
For each task with status `blocked`, read the frontmatter and Work Log section to identify the blocking reason.
For each open bug with severity `critical` or `high`, list ID, title, and severity.

### Step 4: Inspect Integration Evidence

Inspect recent integration evidence from completed task Work Logs, resolved bug Work Logs, and recent integration commits when available.
Record the latest integration-test result or state that no integration evidence was found.

### Step 4a: Roll Up Deferred Minor Findings

Scan the `### Review Verdict` sections of completed tasks and resolved bugs for `#### Deferred Minor findings` lists. Collect every entry with its work item ID and location.
Classify entries ending in the literal ` — resolved: promoted to FAIL` marker as resolved for deferred-Minor triage. Retain their work item ID, location, finding and marker in resolved/promoted history; keep entries without that marker in the unresolved list. Preserve every collected entry in one of these two lists.
Promotion resolves the deferred-Minor triage item, not the failure itself. Read the latest Review Verdict and Work Log for the promoted finding's outcome and cite that evidence in its history entry. If they do not establish a passing fix, state that the outcome is unverified or still failing, as the evidence indicates; the marker alone is never proof of a passing fix.
A roll-up nobody reads is a silent discard, so present both lists to the product owner at Gate 5 and ask for a decision only on each unresolved finding: fix now (file a bug or task), accept, or defer with a reason. Do not drop entries because they look small.

### Step 4b: Check Spec-Truth Reconciliation

When every task is `completed`, check whether the Architect has run spec-truth reconciliation (`architecture-consistency-review` in completion mode) for the approved specs the work touched, and what it returned: read the dated `spec-truth reconciliation` line in each spec's Amendment Log, or in the change-request file for change-request work.
If it has not run, or returned `FAIL` with routed corrections still open (an unapplied spec amendment, or a follow-up task not completed and re-reviewed), list that under `Recommended Actions` — Gate 5 requires a `PASS` or every routed correction done.

### Step 5: Produce Inline Summary

Use `ai-team status` output as the inline summary, then always append the Step 4a roll-up and the Step 4b reconciliation state after it. If the command cannot run, manually present the report in this format:

```markdown
## Status Report — [today's date]

### Summary
- Active specs: N
- Planned tasks: N
- Pending tasks: N
- In progress: N
- Completed: N
- Blocked: N
- Cancelled tasks: N
- Open bugs: N (X critical/high)
- Bugs in progress: N
- Resolved bugs: N
- ADRs: N
- Latest integration result: [result or not found]

### Specifications
[list active specs with title and status]

### In Progress
[list of in-progress tasks with ID, title, role]

### Blocked
[list of blocked tasks with ID, title, blocking reason]

### Critical/High Bugs
[list of critical and high severity open bugs]

### Deferred Minor Findings
Unresolved:
[work item ID, location, finding, fix/accept/defer decision needed — or "none"]

Resolved/promoted history:
[work item ID, location, finding with ` — resolved: promoted to FAIL` marker, outcome with latest Review Verdict and Work Log evidence — or "none"]
```

If there are blocked tasks, critical/high bugs, or spec-truth reconciliation has not passed, add a `Recommended Actions` section suggesting next steps.

### Step 6: Write Full Report (Only When Asked)

Skip this step unless the product owner explicitly asked for a report file. The inline summary is the default output.

When a file is requested, run the CLI report command from the repository root:

```bash
ai-team report
```

By default, it writes `{{project_dir}}/docs/reports/progress-report-[today's date].md` and creates `{{project_dir}}/docs/reports/` if needed.
The full report includes completed tasks, in-progress details, blocked items with action needed, bug listing, next actions, and risks or concerns.
`{{project_dir}}/docs/reports/` is ignored by the scaffolded `{{project_dir}}/.gitignore`, so the file does not dirty the working tree.
Tell the product owner the file path. Commit it only if the product owner asks and the project tracks reports.

## Output Format

- **Inline summary:** Gate 5 status summary using the markdown structure above.
- **Report file:** `{{project_dir}}/docs/reports/progress-report-[today's date].md`, only when the product owner asked for one.
- **Evidence:** latest integration result or a clear statement that no integration evidence was found.

## Quality Criteria

- Counts exclude templates and `.gitkeep`.
- Critical and high severity bugs are explicitly listed.
- Blocked tasks include the blocking reason when one is recorded.
- Every deferred Minor finding in the scanned Review Verdicts is retained in either the unresolved list or resolved/promoted history, with its work item ID and location.
- Entries ending in ` — resolved: promoted to FAIL` retain that marker in resolved/promoted history; fix/accept/defer decisions are requested only for unresolved findings.
- A promoted finding's outcome cites the latest Review Verdict and Work Log; promotion alone never establishes a passing fix.
- When the queue is empty, the state of spec-truth reconciliation is stated.
- The latest integration evidence is recorded or explicitly marked as not found.
- The report gives the product owner enough context for Gate 5 final merge sign-off.

## Common Pitfalls

- Treating Gate 5 as a code review instead of a status sign-off.
- Omitting critical or high severity open bugs.
- Reporting green status without integration evidence.
- Writing a report file nobody asked for — the inline summary is the default output.
