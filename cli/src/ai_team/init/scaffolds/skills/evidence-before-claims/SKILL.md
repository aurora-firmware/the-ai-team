---
name: evidence-before-claims
description: Requires fresh proof — a command and its actual output, or the artifact read — before any claim that work is complete, passing, fixed, merged, or reviewed. Use before reporting a result, writing an Evidence entry, or recording a gate verdict.
allowed-tools: Read, Bash
---

# Evidence Before Claims

Claiming work is done, fixed, passing, or reviewed without fresh proof is a false report, not a shortcut.
Every `Evidence:` entry and every gate verdict rests on this rule.

## Input Requirements

- **The claim about to be made** — for example "tests pass", "the bug is fixed", "the branch is merged", "the spec is consistent".
- **Required tools or dependencies:** whatever command or artifact proves the claim.

## Procedure

### Step 1: Pick the Proof

Find the claim in the table and get the proof it requires:

| Claim | Requires | Not sufficient |
|---|---|---|
| Tests pass | Test command output with zero failures, from this run, or a recorded run by another role cited as such (Step 3) | Your own earlier run, "should pass", a passing subset |
| Build succeeds | Build command output with exit code 0 | Linting passing, a clean-looking log |
| Bug is fixed | The original reproduction now passing, plus the regression test | The code changed, "looks right" |
| Regression test works | Red then green: it failed without the fix and passes with it | It passes once |
| Agent or loop step completed | The diff or tracker state showing the change | The agent reporting success |
| Requirements met | A line-by-line check of each acceptance criterion | Tests passing |
| Branch merged | The merge commit on the destination, and a green post-merge run when the project defines a test command | The merge command exiting 0 |
| Document, plan or inspection result is consistent, approved, or complete | The artifact read: its path plus the decisive line, section, or verdict; for approval, the product owner's confirmation quoted | "Looks consistent", an unread file |
| Review passed | The verdict recorded in the work item file | A chat message saying PASS |

### Step 2: Run or Read It Fresh

When the proof is a command:

1. Run the full command after the last change — not a subset, and not a result from earlier in the session.
2. Read the full output: check the exit code and count the failures.
3. Confirm the output supports the claim.

When the proof is an artifact, read the current version and find the line, section or verdict that settles the claim.

If you skip any of this, do not make the claim.

### Step 3: Cite Instead of Repeating

A claim that rests on another role's recorded run (for example a Developer's Work Log test result that a Reviewer is told not to repeat) is cited, not re-run.
Cite the recorded command and output, and never present it as your own run.

### Step 4: Record It

Write each `Evidence:` entry in the form `role-report` defines for the kind of proof: command, inspection, approval, cited run, or `not verified` with the reason.
A claim that could not be checked is reported as `not verified`, not omitted and not hedged ("seems to work").

## Output Format

- **Evidence entries:** one per claim, in the `role-report` forms.

## Quality Criteria

- Every claim of completion, passing, fixed, merged or reviewed names the command, the artifact read or the cited run that proved it.
- Failures and warnings in the output were read, not skimmed.

## Rationalizations

These thoughts mean stop and get the proof.

| Excuse | Reality |
|---|---|
| "I am confident." | Confidence is not evidence. |
| "I am tired of re-running the suite." | Tiredness is not a reason to report an unchecked result. |
