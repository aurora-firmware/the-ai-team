---
name: git-conventions
description: Branch model, planning-branch steps, commit message format, per-role commit rules, workspace hygiene, and hard git rules for the AI team. Use whenever any role commits, merges, creates or deletes a branch, or finds a dirty working tree.
allowed-tools: Read, Bash
---

# Git Conventions

Project-specific commit scopes and any overrides are in the project's root `AGENTS.md`.

## Branch Model

| Branch | Holds | Created / merged / deleted | Who commits |
|---|---|---|---|
| `main` | Production-ready releases | — | Product owner only. No automated role ever commits or merges here |
| `{{integration_branch}}` | Integrated work | — | Merge commits only (reviewed task and bug branches, planning branches), plus direct ADR commits from the Architect for ADRs raised outside planning, and hygiene `.gitignore` commits. Never direct source code |
| `plan/S-NNN-<slug>` or `plan/CR-NNN-<slug>` | One spec or change-request: the spec and its amendments, cross-spec amendments, and the ADRs and architecture-document updates from its feature architecture and consistency review. Never source code | See Planning Branches | Planner and Architect |
| `task/T-NNN-<slug>` | One task | Created when the development loop picks the task, from `{{integration_branch}}`. Deleted with `git branch -d` after it integrates | Developer only: source, tests, and project artifacts |
| `bug/B-NNN-<slug>` | One bug's diagnosis and fix | Created when the bug-fix loop picks the bug: an existing defect from `{{integration_branch}}`, a task regression from the bug's `source_branch` (the preserved task branch, which it merges back into). Deleted with `git branch -d` after it integrates | Developer only: source, tests, and project artifacts |

Tasks, bugs and change-requests live in the local tracker (`ai-team tracker path`), outside version control and outside every branch.
Their state is the frontmatter `status` field.
Recording state, Work Logs, Diagnosis Logs or Review Verdicts never creates a commit and never needs a branch switch.

## Planning Branches

### Opening a Planning Branch

The skill that creates a spec or change-request opens its planning branch:

1. Run the before-point Hygiene Check, then `git checkout {{integration_branch}}`.
2. Run `git branch --list 'plan/*'`. Spec and ADR IDs are allocated from the files on the current branch, so two open planning branches can allocate the same spec or ADR ID; task and change-request IDs come from the shared tracker and never collide. If another planning branch is open and this one will create a spec or an ADR, stop and ask the product owner whether to merge or abandon the other branch first, or to continue and renumber at merge time.
3. Run the CLI command that allocates the artifact ID.
4. Run `git checkout -b plan/<id>-<slug>`. A new spec file is untracked and carries over; commit it there. A change-request is created in the tracker and never committed.

An approved spec already on `{{integration_branch}}` that needs a breakdown and has no planning branch gets one the same way, skipping step 3.

### Amendment Planning Branch

An approved spec amended after its planning branch merged — because spec-truth reconciliation found it stale, by the product owner's "Revise the spec" escalation decision, or for drift found during development — gets a new planning branch. Follow-up tasks routed by reconciliation never need one: they go straight into the tracker as `pending`, exempt from Gate 2.

1. The Planner opens `plan/S-NNN-<slug>`, or `plan/CR-NNN-<slug>` when an approved change-request drives the amendment, as in Opening a Planning Branch, skipping step 3.
2. The Planner amends the spec, bumps its `version`, records the change in its Amendment Log, adds the `Reconciliation record:` row when reconciliation drives the amendment (that row bumps no `version`), and commits on the branch.
3. The Architect runs the architecture consistency review on the amended spec and commits any ADR it raises on the same branch.
4. On PASS, the Planner merges the branch (Merging a Planning Branch), never waiting for follow-up tasks or a reconciliation re-run. If the amendment creates tasks, they are created `planned` and the merge waits for Gate 2.

A `Reconciliation record:` with no spec change goes in the spec's Amendment Log on its own amendment planning branch, which the Planner merges as soon as the row is committed.

### Cross-Spec Amendments

When a planning branch amends an approved spec other than its own, the Planner bumps that spec's `version` and adds its Amendment Log entry on the branch, and lists the amendment (spec, changed requirements, new `version`) for the product owner to approve with the branch's own spec at Gate 1.
The amendment reaches `{{integration_branch}}` only with the branch's merge.

### Merging a Planning Branch

The Planner merges with `git checkout {{integration_branch}}`, `git merge --no-ff plan/<id>-<slug>` (message `chore(plan): merge <id> <short description>`), then `git branch -d plan/<id>-<slug>`.
The merge happens:

- after Gate 2 passes, for a feature spec or change-request;
- after Gate 1, once S-000 is `approved`, for S-000's own branch (only its bootstrap task plan waits for Gate 2);
- after the Architect's consistency review passes, for an amendment planning branch that creates no tasks, or once the row is committed, for one that carries only a `Reconciliation record:`.

`{{integration_branch}}` never carries a spec amendment without the task plan that implements it, apart from those last two cases. Abandoning a spec or change-request means the product owner deletes its planning branch.

## Commit Message Format

```text
<type>(<component>): <description>
```

- **type** — `feat`, `fix`, `test`, `docs`, `chore`
- **component** — the architecture area (project-specific; see the root `AGENTS.md`)
- **description** — imperative, lowercase, no period, ≤ 72 characters for the whole line

Do not repeat the task or bug ID: the branch name carries it.

```text
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
| **Planner** | One merge commit per planning branch, at the point Merging a Planning Branch names | `{{integration_branch}}` |
| **Developer** | After each implementation cycle | `task/T-NNN-…` or `bug/B-NNN-…` |
| **Architect** | After producing an ADR or amendment, and after updating the architecture documents in feature architecture | `plan/…` when raised during planning or for an amendment planning branch; otherwise `{{integration_branch}}` |
| **Integrator, or the loop running `integrate`** | One merge commit per task or bug branch merged into its target branch | the target branch |

## Workspace Hygiene

A dirty working tree must never block a procedure, and no procedure may leave one behind.
Every procedure that switches branches or merges runs the Hygiene Check — among them `dev-loop`, `bug-loop`, `integrate`, `spec-breakdown`, and every skill that opens a planning branch:

- **Before:** at startup and before every branch switch.
- **After:** after every merge, and before reporting the procedure complete or stopped.

### Hygiene Check

1. Run `git status --porcelain --untracked-files=all`. Empty output means the tree is clean: continue.
2. Act on each entry:

| Entry | Action |
|---|---|
| Generated artifact: test or tool caches, coverage output, build output, logs, generated reports, merge leftovers such as `*.orig` | Add the narrowest matching pattern to the repository `.gitignore` and commit it on the current branch as `chore(gitignore): ignore <pattern>`. Never ignore source, test, spec or decision files |
| Produced by the current step and inside its scope, such as a spec amendment this step wrote | Commit it on the branch its owning rule names |
| Anything else: unknown untracked files, or tracked changes this step did not make | Park it: `git stash push --include-untracked -m "ai-team: <work-item or procedure> parked at <step>"` |

3. Re-run step 1. Continue only on a clean tree.

### Restoring Parked Changes

When the procedure that parked changes ends, on success or on a stop, check out the branch where they were parked; if the procedure deleted it (`integrate` deletes a merged source branch), use the branch it was merged into.

1. Find the entry by its message in `git stash list` and run `git stash pop stash@{n}` for that entry only.
2. If the pop conflicts, stop and report. Git keeps the entry on conflict; leave it for the product owner.
3. List every park and restore in the procedure's final report.

### Never

- Never run `git clean`, delete untracked files, or discard changes the current step did not make (`git restore`, `git checkout -- <path>`).
- Never run `git stash drop` or `git stash clear`.
- Never park changes while a merge, rebase or revert is in progress: finish or abort it first.

## Hard Rules

- No `--no-verify`. Fix the hook failure instead.
- No `--force` or `--force-with-lease` on shared branches (`{{integration_branch}}`, `main`).
- No amending commits that have already been pushed.
- Never commit secrets, `.env` files, or credentials.
- Never commit or merge lifecycle files — tasks, bugs and change-requests — from any branch: they live in the local tracker, outside version control.
- Never discard or delete work the current step did not create; park it as Workspace Hygiene describes.
- No forced branch deletion (`git branch -D`) during integration. Use `git branch -d`; if it is refused, stop and report.
