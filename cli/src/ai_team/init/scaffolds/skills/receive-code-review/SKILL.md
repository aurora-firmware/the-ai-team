---
name: receive-code-review
description: Answers each open finding of an ai-team Review Verdict, either by fixing it on the task or bug branch or by showing with evidence that it does not hold. Use when an ai-team Developer resumes a task or bug whose latest Review Verdict in the tracker lists Open findings.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Skill(new-bug), Skill(git-conventions)
---

# Receive Code Review

The Developer's half of the review loop with `code-review`. The Reviewer reports where the work differs from the Developer's claims or the project's rules — what is wrong and why, never how to fix it. The Developer answers **every** open finding. Neither answer closes a finding; the Reviewer settles each one in the next review cycle, and the loop continues until both agree on every finding.

The Reviewer saw the diff and the work item; the Developer holds the implementation context. Judge each finding on its own, against the code and its cited Basis, not against the Reviewer's confidence or your own.

## Input Requirements

- **Task or bug file** — its latest `### Review Verdict` (`FAIL`, or `ESCALATE` after the Architect's guidance) lists findings with `**Status:** Open`. The file lives in the local tracker; the active loop passes its path.
- **The assigned task or bug branch** — `task/T-NNN-...` or `bug/B-NNN-...`, checked out. Every change goes on this branch, before it is integrated.
- **What the findings cite** — the acceptance criteria or fix contract, the Work Log, the approved spec, accepted ADRs, the project `AGENTS.md` and `{{project_dir}}/docs/coding_guidelines.md`.

Stop and return `BLOCKED` if the latest verdict has no open finding, or the branch is not the one the work item names.

## Procedure

### Step 1: Collect the Open Findings
Read the latest Review Verdict. Collect every finding whose status is `Open`, including one the Reviewer reopened or rebutted. A finding marked `Fixed (confirmed)` or `Acknowledged` is closed; leave it.
For a reopened finding, read the Reviewer's latest note: it is the point to answer.

### Step 2: Verify Before Deciding
For each finding, in turn: read the code at the cited location, reproduce what the finding describes (run the test or the command when there is one), and read the claim or rule in its Basis. Decide from that evidence, not from the finding's text alone. Agreeing or disagreeing from the text is how wrong fixes and wrong rebuttals both happen.

### Step 3: Answer the Finding
Choose one answer:

- **Fixed** — the Reviewer is right. Change the code, docs, or tests so the finding no longer holds. When the finding is that a Work Log claim is false, make the claim true or correct it in this session's Work Log entry, whichever reflects what the work is meant to do. Fix the cause the finding describes, not just the line it points at: the Reviewer re-checks everything its Basis covers. Change nothing the finding does not describe; extra changes are more for the next review to check. Keep within the task's Files to Touch or the bug's fix contract. Run the relevant tests, and the full suite when the project documents one. Commit on the branch with the `git-conventions` skill.
- **Won't Fix** — the finding does not hold. Say which kind of answer it is, and lead with the evidence:
  - *Misinterpretation* — what the claim or rule actually says, or what the code actually does. Cite the code, test output, or document that shows it.
  - *Out of scope* — the issue is real but outside the work item: pre-existing code the work did not change, or behavior outside its Files to Touch and criteria. Show both, and file the issue with the `new-bug` skill so it is not lost; cite the bug ID.
  - *Sanctioned* — the task, the approved spec, or an accepted ADR requires the behavior. Cite it.
  
  "Intentional", "I prefer it", or a restated design choice is not evidence. An answer taken on faith comes back `Open`.
- **Needs Clarification** — the finding is unclear. Do not guess the Reviewer's intent, and do not fix a guess. Ask one specific question that shows what you checked and where it stopped making sense.

When the Reviewer rebutted an earlier `Won't Fix`, answer the rebuttal's specific point with new evidence, or concede and fix it. Repeating the argument stalls the loop.

### Step 4: Record the Answers
Add a `#### Review answers` block to this session's Work Log handoff, one entry per open finding, in finding order:

```markdown
#### Review answers
- **F2** — Fixed in `a3f9c2d`: <what changed and why that resolves the finding>
- **F3** — Won't Fix (out of scope): <the evidence, then the conclusion; filed B-NNN>
- **F4** — Needs Clarification: <the question>
```

A `Fixed` answer cites the commit, which must be on the branch. Return the handoff to the active loop, which appends it to the work item file; do not edit the tracker file yourself.

## Escalation

This skill does not return `ESCALATE` for a disagreement: a dispute is answered with evidence, and the active loop takes a finding still open after three review cycles to the Architect. Return `ESCALATE` with the four-field request only when the `tdd` skill's boundary violations apply to a fix: it needs a file outside Files to Touch, an undeclared dependency, or a change to the approved specification.

```text
Problem: [the finding and the boundary its fix would cross]
Attempted: [what was checked, and why neither a fix within scope nor a justification answers it]
Failed because: [the specific boundary]
Question: [specific guidance needed to continue within the approved specification]
```

## Output Format

- **Commits** — every `Fixed` answer's change, committed on the task or bug branch.
- **Bugs** — every `Won't Fix (out of scope)` issue, filed through `new-bug`.
- **Work Log handoff** — the session's `### Session N — YYYY-MM-DD` entry with its `#### Review answers` block, answering every open finding.

## Quality Criteria

- Every open finding has exactly one answer; none is skipped.
- Each answer was decided after reading the cited code and Basis, not from the finding's text.
- Every `Fixed` answer cites a commit on the branch, and the tests it touches pass.
- Every `Won't Fix` answer names its kind and leads with evidence; an out-of-scope answer cites the filed bug.
- No change goes beyond what a finding describes or outside the work item's scope.

## Common Pitfalls

- **Performative agreement** — fixing a finding without checking it holds. A wrong fix is a new finding.
- **Reflexive rebuttal** — defending the code because you wrote it. The Basis decides, not authorship.
- **Fixing the symptom** — changing the cited line while the cause the finding describes remains elsewhere.
- **Silent scope growth** — bundling refactors with a fix. Answer the finding, nothing more.
- **Losing an out-of-scope issue** — declining it without filing the bug.
- **Unpushed evidence** — citing a commit that is not on the branch; the Reviewer reopens the finding.
