---
name: merge-conflicts
description: Resolve git merge conflicts preserving the intent of both sides. Use when a merge conflict arises during integration of task or bug branches.
allowed-tools: Read, Grep, Glob, Edit, Bash
---

# Conflict Resolution

## Input Requirements

- **Both sides of the conflict** — the changes from each task or bug branch.
- **Work item files for both sides** — what each task or bug fix was trying to accomplish.
- **The base version** — the common ancestor before both changes.

## Procedure

### Step 1: Understand Both Sides
Read the task or bug files for both conflicting branches.
Understand the INTENT of each change, not just the code.
Ask: what was each task or bug fix trying to accomplish?

### Step 2: Analyze the Conflict
Examine the conflict markers in the file.
Classify the conflict:
- **Additive**: Both sides added new code in the same location. Resolution: include both additions in the correct order.
- **Modifying**: Both sides changed the same existing code. Resolution: determine which change is correct, or combine them if they address different aspects.
- **Structural**: Both sides reorganized the same code differently. Resolution: choose the structure that better serves both tasks, or escalate.

### Step 3: Resolve
Apply the resolution that preserves the intent of both changes.
If the changes are incompatible (one deletes what the other modifies), or the conflict is Structural and neither side clearly serves both tasks, stop and return `ESCALATE` using the structured four-field request below. The caller (typically the `integrate` skill) routes the request to the Architect via the `escalation-review` skill.

```text
Problem: [the specific conflict that cannot be resolved — file, lines, incompatibility]
Attempted: [which resolution strategies were considered, including reading both work items]
Failed because: [why neither side's intent can be preserved without guessing]
Question: [specific decision or guidance needed from the Architect]
```

### Step 4: Verify
Run the test suites or fix-verification commands for both work items to confirm neither is broken.
Run the full integration test suite.
If any test fails, the resolution was incorrect. Review and revise.

## Output Format

- **Resolved file(s)** — the merged code with conflicts resolved.
- **Resolution notes** — brief explanation of how each conflict was resolved and why.
- **Test results** — confirmation that both work item verification suites pass.

## Quality Criteria

- The intent of both changes is preserved in the merged result.
- No code from either side is silently dropped.
- All tests from both work items pass after resolution.
- Resolution notes explain the reasoning (for future reference).

## Common Pitfalls

- **Choosing one side blindly** — "accept theirs" or "accept ours" without understanding what both sides intended. This silently drops work.
- **Resolving without reading the work items** — the code alone may not reveal intent. Always check what each task or bug fix was supposed to accomplish.
- **Not testing after resolution** — a syntactically correct merge can still be logically wrong. Always run tests.
- **Resolving structural conflicts without escalating** — if two tasks fundamentally reorganized the same area, the resolution may require architectural guidance. Escalate rather than guess.
