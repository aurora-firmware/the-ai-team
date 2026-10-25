---
name: evidence-before-claims
description: Requires a fresh command and its actual output before any claim that work is complete, passing, fixed, merged, or reviewed. Use before reporting a result, writing an Evidence entry, or recording a gate verdict.
allowed-tools: Read, Bash
---

# Evidence Before Claims

Claiming work is done, fixed, passing, or reviewed without fresh evidence is a false report, not a shortcut. Every role's `Evidence:` field and every gate verdict rests on this rule.

## Input Requirements

- **The claim about to be made** — for example "tests pass", "the bug is fixed", "the branch is merged", "the spec is consistent".
- **Required tools or dependencies:** whatever command proves the claim.

## Procedure

### Step 1: Gate Function

Before making any claim or writing any `Evidence:` entry:

This gate covers a claim about your own work. Two exceptions apply: a claim that rests on someone else's recorded run is cited, not re-run (Step 3); a claim about a document or approval is proved by the artifact read, not a command (Step 2).

1. **Identify** the command that proves the claim.
2. **Run** the full command, fresh and complete — not a subset, and not a result from earlier in the session.
3. **Read** the full output: check the exit code and count the failures.
4. **Verify** that the output confirms the claim.
5. **Only then** make the claim, citing the command and what it printed.

If any step is skipped, do not make the claim. State what was not verified instead.

### Step 2: Check the Claim Against the Common Failures

| Claim | Requires | Not sufficient |
|---|---|---|
| Tests pass | Test command output with zero failures, from this run, or a recorded run by another role cited as such (Step 3) | Your own earlier run, "should pass", a passing subset |
| Build succeeds | Build command output with exit code 0 | Linting passing, a clean-looking log |
| Bug is fixed | The original reproduction now passing, plus the regression test | The code changed, "looks right" |
| Regression test works | Red then green: it failed without the fix and passes with it | It passes once |
| Agent or loop step completed | The diff or tracker state showing the change | The agent reporting success |
| Requirements met | A line-by-line check of each acceptance criterion | Tests passing |
| Branch merged | The merge commit on the destination and a green post-merge run | The merge command exiting 0 |
| Document or plan is consistent, approved, or complete | The artifact path plus the decisive line, section, or verdict read from it; for approval, the human's confirmation quoted | "Looks consistent", an unread file |
| Review passed | The verdict recorded in the work item file | A chat message saying PASS |

### Step 3: Record the Evidence

Write each `Evidence:` entry as the claim, the command run, and the decisive output (exit code, pass and fail counts, the relevant lines).
Use `not run` only with the reason, and never alongside a claim that the check passed.

A claim that rests on someone else's earlier run (for example a Developer's Work Log test result a Reviewer is told not to repeat) is cited, not re-run: write `tests pass (per Work Log session N: <command> — <output>)`. A cited claim is labelled as cited and never presented as this role's own run.
A claim about a document or approval is recorded as `<claim> — <artifact path, line or verdict> — <what it says>`; the form is used whenever the proof is an artifact read, not a command run.

## Output Format

- **Evidence entries:** one per claim, in the form `<claim> — <command> — <decisive output>`; a cited run reads `<claim> (per <source>: <command> — <output>)`; a document claim reads `<claim> — <artifact and line or verdict> — <what it says>`.
- **Unverified claims:** listed separately as `not verified: <claim> — <reason>`.

## Quality Criteria

- Every claim of completion, passing, fixed, or merged names the command that proved it, or the cited run or artifact read that proved it.
- The command ran in full after the last change to the code under test.
- Failures and warnings in the output were read, not skimmed.
- A claim that could not be verified is reported as unverified, not omitted.

## Rationalizations

These thoughts mean stop and run the command.

| Excuse | Reality |
|---|---|
| "It should work now." | Should is a guess. Run the command. |
| "I am confident." | Confidence is not evidence. |
| "I ran it earlier, and only changed a comment since." | Run it again. Cheap to repeat, expensive to be wrong. |
| "The subagent reported success." | Check the diff or the tracker state yourself. |
| "The linter passed, so the build is fine." | A linter is not a compiler or a test run. |
| "I am tired of re-running the suite." | Tiredness is not a reason to report an unchecked result. |

## Common Pitfalls

- Writing `Evidence: tests pass` with no command or output.
- Reusing output from before the last edit.
- Reporting a partial run as a full one.
- Hedging a claim ("seems to work") instead of verifying it or marking it unverified.
