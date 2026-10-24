---
title: "Setup Guide — Starting a New Project"
status: approved
created: 2026-03-10
---

# Setup Guide — Starting a New Project

This guide walks you through bootstrapping a new project using the AI team framework.

## Prerequisites

- A git repository for your new project.
- Claude Code (or another AI agent platform that reads `CLAUDE.md`).
- `pipx` installed (`python -m pip install --user pipx` if needed).

## Setup Steps

### Step 1: Install the `ai-team` CLI

Download the wheel from the project's GitHub Releases page:

```bash
pipx install https://github.com/<org>/<repo>/releases/download/<tag>/ai_team-<version>-py3-none-any.whl
```

Install from a local wheel build while developing this repository:

```bash
pipx install /path/to/The-AI-team-definition/cli/dist/*.whl
```

Daily commands you will use most often:

```bash
ai-team status
ai-team task new "<title>"
ai-team task start <task-id>
ai-team validate
ai-team report
```

For a full usage walkthrough see [`cli/docs/usage.md`](../cli/docs/usage.md); for an exhaustive command and flag reference see [`cli/docs/commands.md`](../cli/docs/commands.md).

### Release hygiene

Public releases must not include secrets, tokens, passwords, environment
variable values, usernames, emails, machine paths, hostnames, or any other data
that could identify or compromise this machine. Before publishing a release,
scan newly added docs, examples, and scratch files for sensitive material and
replace it with placeholders if needed.

### Step 2: Initialize the Project

In your target repository, run `ai-team init` to export the bundled agent and skill definitions and create the project folders:

```bash
ai-team init . --tools claude --no-interactive --create-root-guidance
```

This exports from the CLI package scaffold sources:

- **Agent definitions** into `.claude/agents/`
- **Skill definitions** into `.claude/skills/<name>/SKILL.md`
- **Project directory** `ai-team/` (or the folder set by `--project-dir`) with `specs/`, `decisions/`, and `docs/` folders and its own `CLAUDE.md`, `AGENTS.md`, and `.gitignore`
- **`.ai-team.toml`** configuration file

Tasks, bugs, and change-requests do not live in the project directory. They live in the local tracker, outside version control. `ai-team init` also configures it: it writes `[tracker] dir = ".ai-team/tracker"` to `.ai-team.toml`, creates the folder, and adds `/.ai-team/` to `.gitignore`. To use a different artifact folder (at any depth, such as `docs/ai-team`) or integration branch, pass `--project-dir` and `--integration-branch` to `ai-team init`, or set `[project] dir` and `[git] integration_branch` in `.ai-team.toml` before running it. `ai-team init` keeps existing values. To upgrade an installed project, re-run `ai-team init`: when `.ai-team.toml` exists it asks whether to update the ai-team docs (`ai-team/CLAUDE.md`, `ai-team/AGENTS.md`, `ai-team/.gitignore`) and whether to update the agents and skills, each defaulting to no, and keeps every configured value. Pass `--update-docs` or `--update-skills` to answer a question yes without asking (`--update-skills` also clears the framework version mismatch warning), or `--force` to answer every question yes. `docs/coding_guidelines.md` in the project directory is never overwritten, even with `--force`, because the project bootstrap fills it in. Generated agents and skills carry the configured folder and branch, so re-run `ai-team init --update-skills` after changing either, rather than editing the generated files by hand.

For OpenAI Codex compatibility, add `--tools codex` (or `--tools claude,codex`) to also export `.codex/agents/*.toml` Codex agent files and the Codex skills in `.agents/skills/`. Those TOML files translate each Claude-style agent into Codex's custom-agent schema: `name`, `description`, and `developer_instructions`, with optional Codex-native settings such as `model` and `model_reasoning_effort`. A Codex subagent takes its sandbox and approval settings from the parent session, not from the agent file. The roles that create files or commit — Architect, Planner, Developer, Reviewer, and Integrator — need a parent Codex session that allows writes.

The `ai-process/` specification documents are not exported. They live in the AI team definition meta-repository and serve as the authoritative spec for the rules the agents and skills implement. You do not need them in your project.

### Step 3: Create Your Project's CLAUDE.md and AGENTS.md

Create a `CLAUDE.md` and `AGENTS.md` in your project root. The test instructions in these files are especially important: `dev-loop` starts baseline command discovery from root project guidance, then follows clear references to project-local docs such as `ai-team/docs/coding_guidelines.md`, README files, build configuration, or other documented test instructions. If no automated baseline command is documented, or the available guidance is ambiguous, `dev-loop` will ask the human for the intended command or for explicit confirmation that no automated baseline test is available before claiming a task.

The Step 2 command already created starter versions of both root guidance files (`--create-root-guidance`) if they were missing. Request them on that first `init` run; on an initialized project, `--create-root-guidance` adds missing ones later. Existing root guidance files are never overwritten unless `--force` is also set: `--force` alone prompts in interactive mode and leaves them untouched with `--no-interactive`, while `--force --create-root-guidance` overwrites them without prompting. Every existing file that `init` replaces is reported as `OVERWROTE: <path>`; newly created files are not.

The starter `CLAUDE.md` and `AGENTS.md` follow the root guidance template in the CLI package (`cli/src/ai_team/init/sources/root/CLAUDE.md`). `ai-team check-layout` requires these `##` sections in each file: `Build and Install`, `Test`, `Run`, `Lint and Format`, and `Key Conventions`. If you write the files by hand, use the same headings and fill in your project's commands and conventions.

### Step 4: Customize for Your Stack

**Baseline test instructions** — Fill in the command agents should run to execute the test suite. Put it in root guidance (`CLAUDE.md` or `AGENTS.md`) or clearly reference a project-local doc that contains it. `dev-loop` reads project guidance at startup; if the command is missing or ambiguous, the loop asks for human clarification before claiming a task. If your project has no automated tests, state that explicitly so the loop can record the confirmation and continue.

**`ai-team/docs/coding_guidelines.md`** — `ai-team init` scaffolds this file as a placeholder; do not create it by hand. It is filled in by the project bootstrap (see Step 7) once S-000 is approved, with project-specific rules:
- Stack and framework conventions.
- Formatter, linter, and dependency policy.
- Naming conventions and file layout.
- Testing conventions and where test fixtures live.
- Any commands not already listed in `CLAUDE.md`.

Keep `ai-process/guidelines/coding-standards.md` as the framework's general, language-agnostic baseline unless you intentionally fork the process.

**`.claude/settings.json`** — Configure permissions for your project:
```json
{
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```

### Step 5: Verify the Setup

Run these checks to confirm everything is in place:

1. **Directory structure**: All exported files and project folders exist. Artifact templates are bundled in the CLI and are not copied into the project.
   ```bash
   ls .claude/agents/developer.md
   ls .claude/skills/new-task/SKILL.md
   ls -d ai-team/specs ai-team/decisions ai-team/docs
   ls .ai-team.toml
   ```

2. **Slash commands work**: Run `/status-report` — it should produce an empty report with zero counts.

3. **Create a test task**: Run `/new-task` and verify a file appears in the `tasks/` folder of the tracker (`ai-team tracker path`) and that `git status` stays clean.

4. **Delete the test task**: Remove the test file you just created.

5. **Project guidance exists**: Confirm root guidance has a real baseline test command or clearly points to `ai-team/docs/coding_guidelines.md` or equivalent project-local guidance that contains it. If the project has no automated baseline test, state that explicitly.

### Step 6: Verify Packaging and Installation End-to-End (Maintainers)

`scripts/sync_init_scaffolds.py` generates the bundled scaffold output in `cli/src/ai_team/init/scaffolds/` from the package-owned source assets in `cli/src/ai_team/init/sources/`. Run this script before every build to ensure `ai-team init` ships up-to-date scaffolds.

Run this sequence from a clean shell to confirm the package builds, installs, and initializes correctly:

```bash
cd cli && python scripts/sync_init_scaffolds.py && uv build \
  && pipx install --force dist/*.whl \
  && d=$(mktemp -d) && ai-team init "$d" --tools claude --no-interactive \
  && ai-team --version && (cd "$d" && ai-team status) \
  && test -d "$d/ai-team" && test -d "$d/.claude" && test -f "$d/.ai-team.toml"
```

### Step 7: Start Working

Your project is ready. Start with S-000, the system overview (`/new-system-overview`). After S-000 is approved, run the project bootstrap: ask the planner to run `spec-breakdown` on S-000, which plans only the bootstrap tasks (decisions and architecture documents, environment configuration, coding guidelines, project guidance, and the README description). Run `/dev-loop` on those tasks before feature work. The bootstrap fills in `ai-team/docs/coding_guidelines.md`.

The typical feature workflow is then:

1. **Describe a feature** — write what you want built.
2. **Brainstorm** — the planner agent explores approaches and produces a specification (`/new-spec`).
3. **Approve the spec** — human reviews and approves (Gate 1).
4. **Break into tasks** — the planner decomposes the spec into atomic tasks.
5. **Run Gate 2 preflight** — the architect validates the task plan before development starts.
6. **Run `/dev-loop`** — autonomously implements, reviews, and integrates each task. Gate 3 code review and Gate 4 integration verification happen inside the loop.
7. **Fix bugs with `/bug-loop`** — when open bugs exist, the loop diagnoses first, then fixes, reviews, and integrates.
8. **Final approval** — human approves the merge from `dev-agent` to `main` (Gate 5).

For the full workflow details, see `ai-process/processes/workflow-overview.md`.

## Migrating to the Local Tracker

Projects created before spec S-006 keep tasks, bugs, and change-requests in the project directory: `tasks/<state>/`, `bugs/<state>/`, `change-requests/`, and archived items in `archive/YYYY-MM/`.
Every tracker command prints a warning, and `ai-team check-layout` reports a finding, while those folders still hold files.
There is no migration command: an agent migrates by hand with this procedure. Lifecycle state was the folder; after migration it is only the frontmatter `status` field.

1. **Start clean.** Check out `dev-agent` and run the Workspace Hygiene check from the `git-conventions` skill. No loop may be running.
2. **Locate the tracker.** Make sure `.ai-team.toml` has a `[tracker]` section (add `dir = ".ai-team/tracker"` if it is missing), then run `ai-team tracker path`. If the tracker lies inside the repository, add an ignore rule for it to the root `.gitignore` (for the default, `/.ai-team/`).
3. **Record the starting counts** of markdown files, excluding `.gitkeep` files and template files, in each legacy folder.
4. **Copy the files** into the tracker, keeping their filenames:
   - `tasks/<state>/*.md` → `<tracker>/tasks/`
   - `bugs/<state>/*.md` → `<tracker>/bugs/`
   - `change-requests/*.md` → `<tracker>/change-requests/`
   - `archive/YYYY-MM/*.md` → `<tracker>/archive/YYYY-MM/`

   If two files would land on the same name, stop and ask the human.
5. **Reconcile status with the old folder.** The folder was authoritative. For every task or bug whose `status` differs from the state folder it came from, set the folder's state with `ai-team task set-status` or `ai-team bug set-status`, adding `--reason "migrated from <folder>"`. Change-requests keep their `status`.
6. **Verify before deleting anything.** `ai-team list tasks --json`, `ai-team list bugs --json`, and `ai-team list change-requests --json` must return the starting counts from step 3, and `ai-team validate` must report no task, bug, or change-request findings.
7. **Remove the legacy folders from the repository** with `git rm -r` (including their `.gitkeep` files), then confirm `ai-team check-layout` no longer reports legacy folders and no command prints the legacy warning.
8. **Commit** on `dev-agent`: `chore(tracker): migrate work items to the local tracker`.
9. **Check other branches.** Branches created before the migration still contain the legacy folders. They should not modify work-item files (those were canonical on `dev-agent` only), but if one does, move the change into the tracker by hand before merging that branch, and let the merge delete the folders.

