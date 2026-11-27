---
name: merge-conflicts
description: Resolve git merge conflicts preserving the intent of both sides. Use when a Developer merges the integration branch into its task or bug branch and the merge conflicts.
allowed-tools: Read, Grep, Glob, Edit, Bash
---

# Merge Conflicts

## Input Requirements

- **The merge in progress:** `{{integration_branch}}` merged into the work item branch that is checked out, and the conflicted files (`git status`).
- **The work item file:** what the task or bug fix on the branch set out to do, and its Verification or Fix Verification commands.

## Procedure

### Step 1: Understand Both Sides

1. Read the work item file.
2. `{{integration_branch}}` may carry many work items. For each conflicting hunk, find its commits that touched it (`git log --oneline <merge-base>..{{integration_branch}} -- <file>`, `git blame` on that side). Their merge commits (`chore(tasks|bugs): merge <ID> …`) name the work items; read each file with `ai-team show <ID> --json`.
3. Compare the versions: `git show :1:<file>` (base), `:2:<file>` (the work item branch), `:3:<file>` (`{{integration_branch}}`).

Establish what each side set out to do, not only what its code says.

### Step 2: Classify Each Conflict

- **Additive:** both sides added code in the same place. Keep both additions, in the right order.
- **Modifying:** both sides changed the same code. Keep the correct change, or combine them when they address different aspects.
- **Structural:** both sides reorganized the same code differently. Keep the structure that serves both work items.

### Step 3: Resolve

Edit each conflicted file so the result preserves the intent of both sides and drops nothing silently.
When the changes are incompatible (one side deletes what the other modifies), or a Structural conflict has no structure that serves both work items, go to Step 5.

### Step 4: Verify and Conclude

1. Run the work item's verification commands and the tests of the resolved files on the resolved tree; the full suite runs at integration. If a test fails, the resolution is wrong: return to Step 3.
2. Stage the resolved files with `git add <files>` and conclude with `git commit --no-edit`. This keeps the merge message of `git-conventions` Syncing a Work Branch; for a merge started without one, commit with that message.

### Step 5: Abort

Run `git merge --abort` and confirm with `git status` that no merge is in progress.
Return `ESCALATE` (see Escalation).

## Escalation

Return `ESCALATE` from Step 5 with the four-field request in the format `escalation-review` owns; the Developer returns it, and the loop routes it to the Architect.

```text
Problem: [the conflict that cannot be resolved: file, lines, incompatibility]
Attempted: [the resolutions considered, and the work items read on both sides]
Failed because: [why neither side's intent can be kept without guessing]
Question: [the decision or guidance needed]
```

## Output Format

- **Result:** `PASS` (merge concluded) or `ESCALATE` (merge aborted).
- **Resolution notes:** how each conflict was resolved and why, and the work items each side served.
- **Verification:** the commands run on the resolved tree and their results.

## Quality Criteria

- The intent of both sides is preserved, and no code from either side is silently dropped.
- The merge was concluded with the caller's message, or aborted before returning `ESCALATE`.
