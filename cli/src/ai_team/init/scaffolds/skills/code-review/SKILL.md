---
name: code-review
description: Two-stage code review for completed tasks and bug fixes. Use when a Developer submits work and the Reviewer must check the Developer's claims and the project's rules, or check the Developer's answers to an earlier Review Verdict.
allowed-tools: Read, Edit, Grep, Glob, Bash, Skill(new-bug)
effort: high
---

# Code Review

## Input Requirements

- **Task or bug file** — the task definition with acceptance criteria, or the bug report with diagnosis and fix-verification steps. On a re-review it also holds the earlier Review Verdicts and, in the latest Work Log entry, the Developer's answer to each open finding.
- **Code changes** — the review package the loop wrote (`git log`, `git diff --stat`, and `git diff -U10` for `BASE..HEAD`, plus `git diff -U10` for `LAST..HEAD` on a re-review, where `LAST` is the head of the previous review), or a range to diff yourself. Review the whole `BASE..HEAD` range on a first review. Never review `HEAD~1` alone: a multi-commit branch silently loses its earlier commits.
- **Test results** — the test evidence in the Developer's Work Log (command and output). Do not re-run tests the Work Log already shows passing; run a command only to check something the Work Log does not cover.

The task or bug file lives in the local tracker, outside version control; `ai-team show <id> --json` reports its path.
Review verdicts are written there, never committed, and never placed on the implementation branch.
The two-stage checklist below is the canonical quality bar for all code reviews.

## The Review Loop

The review checks the work against two things:

1. **The Developer's claims** — the acceptance criteria or fix contract the work says it meets, and every statement in the Work Log: what was done, what the tests show, what is out of scope.
2. **The project's rules** — the project `AGENTS.md`, `{{project_dir}}/docs/coding_guidelines.md`, the framework coding standards, the approved spec, accepted ADRs, and the task's own scope limits.

Every place where the work differs from a claim or a rule is a **finding**. A finding states **what** is not as claimed or required and **why**, citing the claim or rule. **A finding never proposes a fix** — no patch, no "change X to Y", no "consider Z". How to resolve it is the Developer's decision, and the Developer may show that the finding does not hold.

The review is a loop with the Developer, who answers every finding with the `receive-code-review` skill. The loop ends when Reviewer and Developer agree on every finding: each one is confirmed fixed, or its justification is accepted. No finding is non-blocking, and none is carried past the work item.

## Procedure

When Source Requirements cites a feature spec, verify the linked REQ and AC obligations are respected and task verification covers its assigned scenarios. Use section references for change-requests and S-000.

### Step 1: Read the Work Item
Read the task or bug file completely.
Treat the Work Log and every summary in it as unverified claims about the code, and check each claim against the diff. A stated rationale is not evidence; judge the code.
For tasks, understand what was asked, what the acceptance criteria are, and which files should have been modified.
For bugs, understand the symptom, reproduction status, diagnostic evidence, isolated fault, root cause or fault hypothesis, and Fix Verification steps.

For bug fixes, verify the diagnosis→fix evidence chain before proceeding to Stage 1:
- Does the Diagnosis Log exist and contain a complete fix contract (reproduction status, evidence captured, isolated fault, root cause or fault hypothesis, planned verification)?
- If the evidence chain is missing or incomplete, record it as a finding and return **FAIL** immediately. Do not infer intent from the diff.

### Step 2: Settle Earlier Findings (Re-review Only)
Skip this step on the first review of a work item.

Take every finding of the latest Review Verdict whose status is `Open`, and read the Developer's answer to it in the latest Work Log entry. Judge each answer on its evidence, then set the finding's status in the new verdict:

- **Fixed** — verify the fix against the finding as written, not against the Developer's description of it: read the code at the location, re-check the claim or rule in its Basis, and confirm the cited commit is in the range. If the finding no longer holds → `Fixed (confirmed)`. If the change is missing or does not resolve the finding → `Open`, with a note saying what is still not as it should be and why. A new discrepancy that the fix introduces is a new finding, not a reopen.
- **Won't Fix** — a dispute. The answer must show one of:
  - *Misinterpretation* — the claim or rule does not say what the finding took it to say, or the code does something the finding misread; the answer cites the code, test output, or document that shows it.
  - *Out of scope* — the issue is real but outside the work item: pre-existing code the work did not change, or behavior outside its Files to Touch and criteria. The answer names the bug the Developer filed with `new-bug` so the issue is not lost.
  - *Sanctioned* — the task, the approved spec, or an accepted ADR requires the behavior; the answer cites it.
  
  If the evidence settles it → `Acknowledged`, with a note saying what settled it. If not → `Open`, with a note saying what the answer does not address — a bare preference, an unverified assertion, evidence that does not touch the finding. Engage with the argument; do not repeat the finding.
- **Needs Clarification** — answer the question in a note. If the answer shows the finding was wrong → `Acknowledged`. Otherwise → `Open`.
- **No answer** → `Open`, with the note `Not answered.`

A finding whose status is already `Fixed (confirmed)` or `Acknowledged` is closed; carry it into the new verdict unchanged. A finding the Architect parked (a filed bug or a `### Recorded deviation` in the work item file) is `Acknowledged`, citing the ruling; one the Architect upheld stays open until its fix is confirmed.

### Step 3: Stage 1 — The Developer's Claims
On a re-review, raise new findings only against the changes in `LAST..HEAD`. Code already reviewed does not gain new findings in a later cycle.

For tasks, check each acceptance criterion against the code:
- Is the criterion met? (yes/no, with evidence)
- Was any unspecified behavior or functionality added?
- Were unexpected files modified?
- Does each Work Log claim hold: what was done, what the tests show, why a file outside Files to Touch changed?

For bug fixes, check:
- Does the Diagnosis Log include reproduction status and evidence?
- Does the fix address the isolated fault or documented root cause from the fix contract?
- Were the Fix Verification steps followed?
- Was unrelated behavior added?

Each check that does not hold is a finding with a `claim` Basis.

### Step 4: Stage 2 — The Project's Rules

**Stage 2 Checklist:**
- **Correctness**: Logic handles expected inputs and edge cases correctly.
- **Tests**: Tests exist, cover both success and failure paths, and are independent (no shared mutable state). For an inspection or demonstration task, the equivalent is the Work Log record (see Inspection and Demonstration Tasks); it replaces the tests. Tests never assert the wording of skills, guides, process documents, or specs.
- **Security**: No hardcoded secrets, all external input is validated, database queries are parameterized.
- **Readability**: Names are descriptive, functions are focused, no dead code or commented-out blocks.
- **Performance**: No unnecessary loops, blocking calls, or resource leaks.
- **CI**: The change does not break CI or depend on an environment CI does not provide — for example local git history beyond the checkout depth, network access, or the developer's installed tool versions. When the project has CI configuration, compare the new tests against it.

Apply the checklist as the project defines it: the project's coding guidelines override the framework standards. Each check that does not hold is a finding with a `rule` Basis. A preference that no project rule backs is not a finding.

**Bug Fix Addendum:**
For bug fixes, also check:
- The fix is minimal — only the code required to address the isolated fault was changed.
- A regression test that fails before the fix and passes after it exists when the defect can be tested automatically, or the Work Log explains why only manual verification is possible.
- No unrelated refactoring, cleanup, or feature code is bundled into the fix.
- The Diagnosis Log fix contract (reproduction status, evidence captured, isolated fault, root cause or fault hypothesis, planned verification) matches what was actually implemented.

### Inspection and Demonstration Tasks

This section applies when the task's Verification section holds the line `Inspection:` or `Demonstration:`, as the `new-task` skill's Verification Methods define them. Detect the line, not the first line of the section: the task template's Verification comment may precede it. Such a task has no tests of its own; the Developer's evidence is a Work Log record, plus the full-suite run when the project documents one.

Check, in Stage 1:
- **The planning choice.** The method matches the change, by the `new-task` rule for choosing the method. A change that adds or alters product behavior under an inspection or demonstration is a finding: the task needed a test.
- **The record.** For an inspection, the Work Log names each criterion and reference checked, each conflict found and how it was fixed, and the result. Re-check the claims against the changed artifact and every listed reference. Read S-000 at review time, when the task lists it, not at session start. For a demonstration, the Work Log names the command or steps run and the observed outcome, and the outcome matches the expected observation.

A missing record, or one that omits a listed criterion or reference, is a finding, as missing red/green evidence is.

### Writing a Finding

Number findings `F1`, `F2`, … in the order they are first raised, and keep the numbering across cycles: a new finding in a later verdict takes the next unused number. Record each one as:

```markdown
#### F1 — <short title> — `<file>:<line or section>`
**Basis:** claim: "<quoted claim>" (<source>) | rule: <rule> (`<file>`)
<What is not as claimed or required, where, and why it matters. Precise enough to reproduce. No fix.>
**Status:** Open
```

Before recording a finding, strip any remedy from it. If nothing is left once the remedy is gone, the finding was a preference: drop it.

On a re-review, the finding text stays as first written. Add the settlement under it as `> **Reviewer:** <note>` above the `**Status:**` line.

### Cannot Verify From the Diff

Some claims cannot be confirmed from the diff and the work item alone — for example, that a changed function's other callers still work, or that a behavior matches a task completed earlier in the run. Do not guess. List each one as `⚠️ Cannot verify from diff` with the claim and what would confirm it. The active loop holds the cross-task context and resolves each item before integration.

### Step 5: Produce Verdict

The Reviewer's self-recovery threshold is **one review cycle** for ESCALATE-worthy issues. For findings, issue FAIL (the active loop allows up to three FAIL cycles per work item before it forces escalation on its own).

- If every finding is `Fixed (confirmed)` or `Acknowledged`, and this review raised no new finding → **PASS**.
- If any finding is `Open` → **FAIL**. The Developer answers each open finding and re-submits.
- If the code has a fundamental design issue that no amount of Developer fixes can address within the approved specification → **ESCALATE** immediately. Do not issue FAIL first and wait. ESCALATE-worthy examples: the spec is internally contradictory, the acceptance criteria cannot be met without a spec change, the diagnosis points at a root cause outside the bug's stated scope.

### Step 6: Record the Verdict
Append to the task or bug file under a `### Review Verdict — [date]` heading, from whatever branch is checked out.
The first line of the section must be one of: `PASS`, `FAIL`, or `ESCALATE`.
The second line is `Reviewed through: <HEAD sha>`; the next review cycle diffs from it.
Then list every finding of the work item, closed and open, in the Writing a Finding format, so the latest verdict holds the full state of the review. List each unverifiable claim under `#### ⚠️ Cannot verify from diff`. Omit a heading that has no entries.
Do not commit anything: the verdict, and any bug filed through `new-bug` during this review, live in the tracker outside version control.

The work item stays `in-progress` on FAIL. The active loop tracks the review cycle count. On a third consecutive FAIL, the active loop escalates to the Architect — the Reviewer does not need to change the verdict type.

## Output Format

PASS, FAIL, and ESCALATE append a `### Review Verdict — [date]` section to the task or bug file in the tracker.
The first line of the section is always one of: `PASS`, `FAIL`, or `ESCALATE`; the second is `Reviewed through: <sha>`.

### On PASS
Verdict: `PASS`
A brief confirmation that both stages passed, then every finding of the work item with its closing status, and the `#### ⚠️ Cannot verify from diff` list when it has entries.
Next owner: active Development Loop or Bug-Fix Loop.

### On FAIL
Verdict: `FAIL`
Every finding of the work item in the Writing a Finding format, with its status, then the `#### ⚠️ Cannot verify from diff` list when it has entries.
Next owner: active loop, which returns the work item to the Developer.

### On ESCALATE
Verdict: `ESCALATE`
Record the verdict under `### Review Verdict — [date]`, list the findings as on FAIL, and include a structured escalation request using the standard four-field block:

```text
Problem: [the fundamental design issue observed in the code]
Attempted: [what review cycles and Developer fixes preceded this verdict]
Failed because: [why ordinary Developer fixes cannot resolve it within the approved specification]
Question: [specific decision or guidance needed from the Architect]
```

Next owner: active loop for Architect consultation.

## Quality Criteria

- Every acceptance criterion was explicitly checked (not assumed).
- For bug fixes, the diagnosis→fix evidence chain was explicitly verified before any other check.
- For bug fixes, diagnostic evidence and Fix Verification were explicitly checked.
- Every finding cites the claim or rule it measures the work against, says what is wrong and why, and proposes no fix.
- On a re-review, every earlier open finding was settled against its answer's evidence, and new findings come only from `LAST..HEAD`.
- PASS was issued only with every finding confirmed fixed or acknowledged.
- Claims in the Work Log were checked against the diff, not accepted.
- The first review covers the range from the recorded base commit to the branch head.
- Every unverifiable claim is recorded where the loop can find it.
- For inspection and demonstration tasks, the planning choice and the Work Log record were checked, an inspection against every listed criterion and reference.
- The reviewer checked the actual code, not just the test results.
- No personal style preferences were enforced — only project standards from the coding guidelines.

## Rationalizations

These thoughts mean stop and verify against the code.

| Excuse | Reality |
|---|---|
| "The Work Log says it works, and the tests pass." | The Work Log is the Developer's claim. Check the claim against the diff. |
| "The Developer explained why this is fine." | Judge the explanation's evidence, not its confidence. Accept it only when it shows the finding does not hold. |
| "Saying how to fix it saves a cycle." | The fix is the Developer's decision. State what is wrong and why, and stop there. |
| "It is small, so I will let it pass." | There are no non-blocking findings. Either it differs from a claim or rule and is a finding, or it does not and is dropped. |
| "The Developer disputed it again; I will accept it to keep moving." | Close a finding on evidence only. A stalemate goes to the Architect when the cycle cap is reached. |
| "I cannot tell from the diff, so I will guess PASS to keep things moving." | Record it as `Cannot verify from diff` so the loop can check it with the cross-task context you lack. |
| "This is a style preference, but I will raise it anyway." | Enforce project rules only. A preference no rule backs is not a finding. |
| "I missed this in the first cycle; I will add it now." | New findings come only from `LAST..HEAD`. Code already reviewed is settled. |
| "The diff is large, so I will skim the rest." | Review the whole range, or return a FAIL asking for a smaller one. A skimmed review is a rubber stamp. |

## Common Pitfalls

- **Trusting the report** — accepting the Work Log's summary or the Developer's rationale instead of reading the diff.
- **Trusting the fix** — marking a finding `Fixed (confirmed)` because the Developer says so, without re-checking its Basis at the location.
- **Prescribing the fix** — "rename X to Y", "add a test for Z". Say what is missing and which claim or rule requires it.
- **Reviewing only the last commit** — the first review's range starts at `BASE`, the commit the branch was created from, not at `HEAD~1`.
- **Re-running the Developer's tests** — the Work Log carries that evidence; a repeat run adds latency, not coverage.
- **Rubber-stamping** — approving because tests pass without reading the code. Tests can have gaps.
- **Bikeshedding** — spending review time on naming preferences or formatting instead of correctness and security.
- **Vague findings** — "this could be better" names no claim or rule. "Acceptance criterion 3 requires the empty-input case; `parse()` at `src/parse.py:40` raises `IndexError` on an empty list" does.
- **Scope creep in review** — reviewing code outside the task's scope. Only review what the task changed.
- **Inferring intent from the diff** — for bug fixes, do not guess what the fix was meant to address. Require a complete evidence chain in the Diagnosis Log before reviewing the implementation.
