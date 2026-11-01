---
name: git-conventions
description: Branch model, commit message format, per-role commit rules, and hard git rules for the AI team. Use whenever any role commits, merges, or creates a branch — consult this skill for the authoritative branch model and commit format.
allowed-tools: Read
---

# Git Conventions

These rules apply to all AI roles working within any project that uses this framework.
Project-specific commit scopes and any overrides belong in the project's own `AGENTS.md`.

## Branch Model

| Branch | Purpose | Who touches it |
|---|---|---|
| `main` | Production-ready releases | Product owner only — never automated roles |
| `{{integration_branch}}` | Integration target | The integration procedure merges task branches here; the Integrator handles manual merges and conflicts; the Planner merges planning branches here after Gate 2; Architects commit ADRs raised outside planning here |
| `plan/S-NNN-short-description` or `plan/CR-NNN-short-description` | Planning branch for one spec or change-request: the spec, spec amendments, ADRs raised by its consistency review, and the ADRs and architecture-document updates from its feature architecture | Planner and Architect only — no source code |
| `task/T-NNN-short-description` | Single task implementation branch | Developer only for source, tests, and project artifacts |
| `bug/B-NNN-short-description` | Single bug diagnosis and fix branch | Developer only for source, tests, and project artifacts |

**Rules:**
- No automated role ever commits to `main`.
- `{{integration_branch}}` receives merge commits from the integration procedure, the Integrator role, and planning-branch merges, and direct ADR commits from the Architect (no direct source code).
- Developer always works on a task branch, never on `{{integration_branch}}`.
- Task branches are created when the development loop picks up a task and deleted after successful integration into `{{integration_branch}}`.
- Bug branches are created when the bug-fix loop picks up a bug.
  Existing-defect bug branches are based on `{{integration_branch}}`; task-regression bug branches are based on the bug report's `source_branch`.
- Planning branches are created from `{{integration_branch}}` when a spec or change-request is created. Every planning artifact for that work is committed there, never directly on `{{integration_branch}}`.
  The Planner merges the planning branch into `{{integration_branch}}` with `--no-ff` only after Gate 2 passes, then deletes it with `git branch -d`. The only exception is S-000, whose own planning branch does not wait for Gate 2 (only its bootstrap task plan does): its planning branch merges into {{integration_branch}} with `--no-ff` after Gate 1, once S-000 is `approved`.
  `{{integration_branch}}` therefore never carries a spec amendment without the task plan that implements it, except the S-000 planning branch, which merges after Gate 1 once S-000 is `approved`. Abandoning a spec or change-request means the product owner deletes its planning branch.
- Tasks, bugs, and change-requests live in the local tracker (`ai-team tracker path`), outside version control and outside every branch.
  Their lifecycle state is the frontmatter `status` field. Recording state, Work Logs, Diagnosis Logs, or Review Verdicts never creates a commit and never requires a branch switch.

### Opening a Planning Branch

The skill that creates a spec or change-request opens its planning branch:

1. Run the before-point Workspace Hygiene check, then `git checkout {{integration_branch}}`.
2. Run `git branch --list 'plan/*'`. Spec and ADR IDs are allocated from the files on the current branch, so two open planning branches can allocate the same spec or ADR ID.
   Task and change-request IDs come from the shared tracker and never collide.
   If another planning branch is open and this one will create a spec or an ADR, stop and ask the product owner whether to merge or abandon the other branch first, or to continue and renumber at merge time.
3. Run the CLI command that allocates the artifact ID.
4. Run `git checkout -b plan/<id>-<slug>`. A new spec file is untracked and carries over; commit it there. A change-request is created in the tracker and is never committed.

When an approved spec already on `{{integration_branch}}` needs a breakdown and has no planning branch, open one the same way and skip step 3.

## Commit Message Format

```
<type>(<component>): <description>
```

- **type** — `feat`, `fix`, `test`, `docs`, `chore`
- **component** — architecture area (project-specific; see project `AGENTS.md`)
- **description** — imperative, lowercase, no period, ≤ 72 chars total

The branch name already carries task and role context — do not repeat it in the message.

**Examples:**
```
feat(db): add conversations table migration
fix(ui): correct sidebar active state color
test(api): cover SSE disconnection edge case
docs(specs): add phase2 boardroom role selection
chore(plan): merge S-004 billing export
```

## When Each Role Commits

| Role | Commits when | Branch |
|---|---|---|
| **Planner** | Each spec or spec amendment is finalized | `plan/…` |
| **Planner** | One merge commit per planning branch after Gate 2 passes (S-000: after Gate 1, once S-000 is `approved`) | `{{integration_branch}}` |
| **Developer** | After each implementation cycle for source, tests, and project artifacts | `task/T-NNN-…` or `bug/B-NNN-…` |
| **Architect** | After producing an ADR or amendment, and after updating the architecture documents in feature architecture | `plan/…` when raised during planning; otherwise `{{integration_branch}}` |
| **Integrator** | One merge commit per task or bug branch merged into its target branch | target branch |

## Workspace Hygiene

A dirty working tree must never block a procedure, and no procedure may leave one behind.
Every orchestrating procedure (`dev-loop`, `bug-loop`, `integrate`, `spec-breakdown`) runs the hygiene check:

- **Before** — at startup and before every branch switch.
- **After** — after every merge, and before reporting the procedure complete or stopped.

### Hygiene Check

1. Run `git status --porcelain --untracked-files=all`. Empty output means the tree is clean — continue.
2. Classify each entry and act on it:

| Entry | Action |
|---|---|
| Generated artifact — test or tool caches, coverage output, build output, logs, generated reports, merge leftovers such as `*.orig` | Add the narrowest matching pattern to the repository `.gitignore` and commit it on the current branch: `chore(gitignore): ignore <pattern>`. Never ignore source, test, spec, or decision files. |
| Produced by the current step and inside its scope — for example a spec amendment written by this step | Commit it on the branch the owning rule names. |
| Anything else — unknown untracked files, or tracked changes this step did not make | Park it: `git stash push --include-untracked -m "ai-team: <work-item or procedure> parked at <step>"`. |

3. Re-run step 1. The tree must be clean before continuing.

### Restoring Parked Changes

When the procedure that parked changes ends — on success or on a stop — return to the branch where they were parked and restore them.
If the procedure deleted that branch — `integrate` deletes a merged source branch — restore them on the branch it was merged into, which now contains its history:

1. Find the entry by its message in `git stash list` and run `git stash pop stash@{n}` for that entry only.
2. If the pop conflicts, stop and report. Git keeps the stash entry on conflict; leave it there for the product owner.
3. List every park and restore in the procedure's final report, so the product owner can see what was moved.

### Never

- Never run `git clean`, delete untracked files, or discard changes the current step did not make (`git restore`, `git checkout -- <path>`).
- Never run `git stash drop` or `git stash clear`.
- Never park changes while a merge, rebase, or revert is in progress — finish or abort that operation first.

## Hard Rules

- No `--no-verify`. Fix the hook failure instead.
- No `--force` or `--force-with-lease` on shared branches (`{{integration_branch}}`, `main`).
- No amending commits that have already been pushed.
- Never commit secrets, `.env` files, or credentials.
- Never discard or delete work the current step did not create — park it as described in Workspace Hygiene.
- Never commit or merge lifecycle files — tasks, bugs, and change-requests — from an implementation branch or any other branch: they live in the local tracker, outside version control.
- No routine forced branch deletion (`git branch -D`) during integration. Use safe deletion (`git branch -d`) only. If `-d` is refused, stop and report instead of forcing deletion.

## Rationalizations

These thoughts mean stop and follow the branch and commit rules.

| Excuse | Reality |
|---|---|
| "It is a one-line change, so I can commit it straight to the integration branch." | Implementation belongs on a task or bug branch. The size of the change does not move the rule. |
| "The hook is slow or noisy, so `--no-verify` just this once." | Fix the cause of the hook failure. |
| "I will amend the pushed commit to tidy the history." | Pushed commits are shared. Add a new commit instead. |
| "These untracked files are in my way, so I will delete them." | Work this step did not create is not yours to discard. Park it as Workspace Hygiene describes. |
| "I will force-push; nobody else uses this branch." | Shared branches never take a force-push. Check, then stop. |
| "I will commit the task file with the code so it stays in sync." | Work items live in the tracker, outside every branch. Never commit them. |

## Common Pitfalls

- Repeating the task or bug ID in the commit message — the branch name already carries it.
- Committing implementation code to `{{integration_branch}}` — implementation belongs on a task or bug branch.
- Using `--no-verify` to bypass a hook failure — fix the underlying cause instead.
