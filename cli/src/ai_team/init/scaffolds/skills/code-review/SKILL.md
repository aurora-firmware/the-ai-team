---
name: code-review
description: Two-stage code review for completed tasks and bug fixes. Use when a Developer submits work and the Reviewer must check the Developer's claims and the project's rules, or check the Developer's answers to an earlier Review Verdict.
allowed-tools: Read, Edit, Grep, Glob, Bash, Skill(new-bug), Skill(coding-standards)
effort: high
---

# Code Review

## Input Requirements

- **Task or bug file** — the acceptance criteria, or the bug report with its Diagnosis Log and Fix Verification. On a re-review it also holds the earlier Review Verdicts and, in the latest Work Log entry, the Developer's answer to each open finding. Its location is the `path` of `ai-team show <id> --json`.
- **Code changes** — the review package the loop wrote (`git log`, `git diff --stat` and `git diff -U10` for `BASE..HEAD`, plus `git diff -U10` for `LAST..HEAD` on a re-review, where `LAST` is the `Reviewed through:` commit of the previous verdict), or a range to diff yourself. A first review covers the whole `BASE..HEAD` range, never `HEAD~1` alone.
- **Test evidence** — the `Verification:` lines of the Developer's Work Log entry (written by `tdd` Step 9). Do not re-run a command the Work Log shows passing; run one only to check something the Work Log does not cover.

The review checks the work against two things:

1. **The Developer's claims** — the acceptance criteria or the fix contract the work says it meets, and every statement in the Work Log.
2. **The project's rules** — the project `AGENTS.md`, the coding guidelines the project guidance names (default `docs/development/coding_guidelines.md`), the `coding-standards` skill (the project's guidelines override it), the approved spec, the architecture documents the project guidance names, accepted ADRs, and the work item's scope.

Every place where the work differs from a claim or a rule is a **finding**: what is not as claimed or required, and why, citing the claim or rule. **A finding never proposes a fix**; how to resolve it is the Developer's decision, and the Developer may show that it does not hold.
The Developer answers every finding with `receive-code-review`. The review ends when both agree on every finding: none is non-blocking, and none is carried past the work item.

Prove what you confirm or raise with the code you read (`file:line`) or a command you ran, in the evidence forms of `role-report`; cite a Work Log run as `per Work Log session N`.

## Procedure

### Step 1: Read the Work Item

Read the task or bug file completely. Treat every Work Log statement as an unverified claim to check against the diff; a stated rationale is not evidence.
When Source Requirements cites a feature spec, its REQ and AC obligations are part of the claims, and the task's verification must cover its assigned scenarios. A change-request or S-000 is cited by section.

For a bug fix, check the evidence chain before anything else. The Diagnosis Log must hold a complete fix contract, as the `debug` skill defines it, recorded before the fix's first Work Log entry. If it is missing or incomplete, record that as a finding and return **FAIL** without reviewing the implementation: do not infer the fix's intent from the diff.

### Step 2: Settle Earlier Findings (Re-review Only)

Take every `Open` finding of the latest Review Verdict and the Developer's answer to it, and judge the answer on its evidence:

- **Fixed** — verify the fix against the finding as written, not the Developer's description: read the code at the location, re-check the claim or rule in its Basis, and confirm the cited commit is in the range. Resolved → `Fixed (confirmed)`. Missing or not resolving it → `Open`, with a note on what is still wrong. A new discrepancy the fix introduces is a new finding, not a reopen.
- **Won't Fix** — a dispute. The answer must show one of:
  - *Misinterpretation* — the claim or rule does not say what the finding took it to say, or the code does something the finding misread, shown by code, test output or document.
  - *Out of scope* — the issue is real but outside the work item (pre-existing code the work did not change, or behavior outside its Files to Touch and criteria), and the answer names the bug filed with `new-bug`.
  - *Sanctioned* — the task, the approved spec or an accepted ADR requires the behavior, cited.

  Settled by the evidence → `Acknowledged`, with a note on what settled it. Otherwise → `Open`, with a note on what the answer does not address. Engage with the argument; do not repeat the finding.
- **Needs Clarification** — answer the question in a note. If the answer shows the finding was wrong → `Acknowledged`; otherwise → `Open`.
- **No answer** → `Open`, noted `Not answered.`

A finding already `Fixed (confirmed)` or `Acknowledged` is carried into the new verdict unchanged. A finding the Architect parked (a filed bug, or a `### Recorded deviation` in the work item file) is `Acknowledged`, citing the ruling; one the Architect upheld stays open until its fix is confirmed.

On a re-review, Steps 3 and 4 raise new findings only against `LAST..HEAD`: code already reviewed gains none.

### Step 3: Stage 1 — Spec Compliance

Check the work against the Developer's claims. Each check that fails is a finding with a `claim` Basis.

For a task:
- Every acceptance criterion is met, with evidence; no specified functionality is missing.
- No unspecified behavior or feature was added.
- Exclusions and file-scope limits stated in the task are respected. A file changed outside Files to Touch is justified in the Work Log; an unjustified one is a finding.
- Every Work Log claim holds: what was done, and what the tests show.

For a bug fix:
- The fix addresses the isolated fault or root cause of the fix contract, and the contract matches what was implemented.
- The Fix Verification steps were run, or the Work Log explains why they could not be.
- No unrelated behavior was added.

**Inspection and demonstration tasks** — a task whose Verification section holds an `Inspection:` or `Demonstration:` line, detected as the `new-task` skill's Verification Methods describe, has no tests of its own. Check also:
- **The planning choice** — the method fits the change by the `new-task` rule for choosing the method. A change that adds or alters product behavior without a test is a finding.
- **The record** — for an inspection, the Work Log names each criterion and reference checked, each conflict found and how it was fixed, and the result; re-check those claims against the changed artifact and every listed reference (read S-000 now, when listed). For a demonstration, it names the command or steps run and the observed outcome, which matches the expected observation. A missing record, or one that omits a listed criterion, reference or step, is a finding.

### Step 4: Stage 2 — Code Quality

Check the change against the project's rules, as the project defines them (its coding guidelines override the `coding-standards` skill). Each check that fails is a finding with a `rule` Basis; a preference no rule backs is not a finding.

- **Correctness** — logic is correct for expected inputs and edge cases; no off-by-one, null-reference or unhandled state; error handling covers the failure modes the spec describes.
- **Tests** — tests exist for new or changed product behavior and cover success and failure paths; they are independent; none asserts the wording of skills, process documents, guides or specs, or only proves a removal; none depends on an environment CI does not provide (git history beyond the checkout depth, network access, locally installed tool versions — compare with the CI configuration when there is one). The Work Log records the test run, or explains why one was not possible. For an inspection or demonstration task, the record from Step 3 replaces the tests.
- **Security** — no hardcoded secrets; external input is validated; database queries are parameterized; no new permission or access beyond what is needed.
- **Readability** — names are descriptive and follow project conventions; functions are focused; comments explain *why*, not *what*; no dead code, commented-out blocks or debugging artifacts.
- **Performance** — no unnecessary loops over large data, unjustified blocking calls in hot paths, or memory or resource leaks.

For a bug fix, also:
- The fix is minimal and scoped to the isolated cause, with no refactoring, cleanup or feature code bundled in.
- A regression test fails before the fix and passes after it when the defect can be tested automatically; otherwise the Work Log explains why only manual verification is possible.

### Step 5: Write the Findings

Number findings `F1`, `F2`, … in the order first raised, and keep the numbering across cycles: a new finding takes the next unused number.

```markdown
#### F1 — <short title> — `<file>:<line or section>`
**Basis:** claim: "<quoted claim>" (<source>) | rule: <rule> (`<file>`)
<What is not as claimed or required, where, and why it matters. Precise enough to reproduce. No fix.>
**Status:** Open
```

Strip any remedy before recording a finding; if nothing is left, it was a preference: drop it.
On a re-review, the finding text stays as first written, and the settlement goes under it as `> **Reviewer:** <note>`, above the `**Status:**` line.

Some claims cannot be confirmed from the diff and the work item, such as that a changed function's other callers still work. Do not guess: list each one under `#### ⚠️ Cannot verify from diff`, with the claim and what would confirm it. The active loop holds the cross-task context and resolves them before integration.

### Step 6: Decide and Record the Verdict

- Every finding `Fixed (confirmed)` or `Acknowledged`, and no new one → **PASS**.
- Any finding `Open` → **FAIL**. The work item stays `in-progress`, and the active loop returns it to the Developer; the loop's review-cycle cap decides when a stalemate goes to the Architect.
- A fundamental design issue that no Developer fix can resolve within the approved specification → **ESCALATE**, at once, without a FAIL first (see Escalation).

Append to the task or bug file, from whatever branch is checked out:

```markdown
### Review Verdict — YYYY-MM-DD
PASS | FAIL | ESCALATE
Reviewed through: <HEAD sha>
<every finding of the work item, closed and open, in the Step 5 format>
#### ⚠️ Cannot verify from diff
<one entry per unverifiable claim; omit the heading when empty>
```

The latest verdict holds the full state of the review.
Commit nothing: the verdict and any bug filed with `new-bug` live in the tracker, outside version control.

## Escalation

Return `ESCALATE` when the code has a fundamental design issue that Developer fixes cannot resolve within the approved specification: the spec is internally contradictory, the criteria cannot be met without a spec change, or the diagnosis points at a root cause outside the bug's scope.
Record the verdict and findings as on FAIL, and add the request; the active loop routes it to the Architect through `escalation-review`.

```text
Problem: [the fundamental design issue observed in the code]
Attempted: [the review cycles and Developer fixes that preceded this verdict]
Failed because: [why Developer fixes cannot resolve it within the approved specification]
Question: [the decision or guidance needed from the Architect]
```

## Output Format

- **Review Verdict** — the Step 6 section appended to the work item file.
- **Bugs** — any out-of-scope defect filed with `new-bug`.
- **Next Owner** — the active Development Loop or Bug-Fix Loop, whatever the verdict.

## Quality Criteria

- Every acceptance criterion or fix-contract field was checked against the code, not assumed from the Work Log.
- Every finding cites its claim or rule, says what is wrong and why, and proposes no fix.
- On a re-review, every earlier open finding was settled on its answer's evidence, and new findings come only from `LAST..HEAD`.
- PASS was issued only with every finding closed.
- Every unverifiable claim is listed where the loop can find it.

## Rationalizations

These thoughts mean stop and verify against the code.

| Excuse | Reality |
|---|---|
| "The Developer explained why this is fine." | Judge the explanation's evidence, not its confidence. |
| "It is small, so I will let it pass." | There are no non-blocking findings. It differs from a claim or rule, or it is dropped. |
| "The Developer disputed it again; I will accept it to keep moving." | Close a finding on evidence only. A stalemate goes to the Architect at the loop's review-cycle cap. |
| "I cannot tell from the diff, so I will pass it." | List it under Cannot verify from diff; the loop has the context you lack. |
| "The diff is large, so I will skim the rest." | Review the whole range. A skimmed review is a rubber stamp. |

## Common Pitfalls

- **Rubber-stamping** — passing because the tests pass, without reading the code. Tests have gaps.
- **Vague findings** — "this could be better" names no claim or rule. "Acceptance criterion 3 requires the empty-input case; `parse()` at `src/parse.py:40` raises `IndexError` on an empty list" does.
- **Scope creep** — reviewing code the work item did not change.
