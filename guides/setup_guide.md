# Setup Guide — Starting a New Project

This guide walks you through bootstrapping a new project using the AI team framework.

## Prerequisites

- A git repository for your new project.
- Claude Code.
- Python 3.14 or later.
- `pipx` installed (`python -m pip install --user pipx` if needed).

## Setup Steps

### Step 1: Install the `ai-team` CLI

Download the wheel from the project's GitHub Releases page:

```bash
pipx install https://github.com/aurora-firmware/the-ai-team/releases/download/<tag>/ai_team-<version>-py3-none-any.whl
```

To install a local build instead, see [`cli/docs/usage.md`, From a local build](../cli/docs/usage.md#from-a-local-build).

Daily commands you will use most often:

```bash
ai-team status
ai-team task new "<title>"
ai-team task start <task-id>
ai-team validate
ai-team report
```

For a full usage walkthrough see [`cli/docs/usage.md`](../cli/docs/usage.md); for an exhaustive command and flag reference see [`cli/docs/commands.md`](../cli/docs/commands.md).

### Step 2: Initialize the Project

In your target repository, run `ai-team init` to export the bundled agent and skill definitions and create the project folders:

```bash
ai-team init . --no-interactive --create-root-guidance
```

This exports from the CLI package scaffold sources:

- **Agent definitions** into `.claude/agents/`
- **Skill definitions** into `.claude/skills/<name>/SKILL.md`
- **Project directory** `ai-team/` (or the folder set by `--project-dir`) with `specs/`, `decisions/`, and `docs/` folders and its own `AGENTS.md` and `.gitignore`
- **`.ai-team.toml`** configuration file

Tasks, bugs, and change-requests do not live in the project directory. They live in the local tracker, outside version control. `ai-team init` also configures it: it writes `[tracker] dir = ".ai-team/tracker"` to `.ai-team.toml`, creates the folder, and adds `/.ai-team/` to `.gitignore`. To use a different artifact folder (at any depth, such as `docs/ai-team`) or integration branch, pass `--project-dir` and `--integration-branch` to `ai-team init`, or set `[project] dir` and `[git] integration_branch` in `.ai-team.toml` before running it; leave out `[init]`, which `init` writes itself. `ai-team init` keeps existing values. To upgrade an installed project, re-run `ai-team init`: when `.ai-team.toml` exists and records `[init] framework_version` it asks whether to update the ai-team docs (`ai-team/AGENTS.md`, `ai-team/.gitignore`) and whether to update the agents and skills, each defaulting to no, and keeps every configured value. Pass `--update-docs` or `--update-skills` to answer a question yes without asking (`--update-skills` also clears the framework version mismatch warning), or `--force` to answer every question yes. `docs/coding_guidelines.md` in the project directory is never overwritten, even with `--force`, because the project bootstrap fills it in. Generated agents and skills carry the configured folder and branch, so re-run `ai-team init --update-skills --update-docs` after changing either, rather than editing the generated files by hand.

The `ai-process/` specification documents are not exported. They live in the AI team definition meta-repository and serve as the authoritative spec for the rules the agents and skills implement. You do not need them in your project.

The exported files are package-owned: the generator `cli/scripts/sync_init_scaffolds.py` produces them from the sources in the CLI package (`cli/src/ai_team/init/sources/`). The framework's agents, skills and project skeleton are changed in those sources and regenerated, never in the exported copies (see [`cli/docs/usage.md`, How to maintain scaffold sources](../cli/docs/usage.md#how-to-maintain-scaffold-sources)).

### Step 3: Fill In Your Project's AGENTS.md

Fill in the `AGENTS.md` in your project root. `AGENTS.md` is the only generated guidance file, and the one `ai-team check-layout` level 3 requires. The test instructions in this file are especially important: `dev-loop` starts baseline command discovery from root project guidance, then follows clear references to project-local docs such as `ai-team/docs/coding_guidelines.md`, README files, build configuration, or other documented test instructions. If no automated baseline command is documented, or the available guidance is ambiguous, `dev-loop` will ask the product owner for the intended command or for explicit confirmation that no automated baseline test is available before claiming a task.

The Step 2 command created a starter root `AGENTS.md` (`--create-root-guidance`) if it was missing; if you ran `init` without that flag, create the file yourself with the headings below. Request it on that first `init` run; on an initialized project, `--create-root-guidance` adds it later if missing. An existing root `AGENTS.md` is never overwritten unless `--force` is also set: `--force` alone prompts in interactive mode and leaves it untouched with `--no-interactive`, while `--force --create-root-guidance` overwrites it without prompting. Every file `init` creates is reported on stdout as `WROTE: <path>` (`WOULD WRITE` in a dry run) and every file it replaces as `OVERWROTE: <path>` (`WOULD OVERWRITE` in a dry run). The tracker folder it creates is reported as `CREATED: <path>` (`WOULD CREATE` in a dry run) and the root `.gitignore` it adds the tracker rule to as `UPDATED: <path>` (`WOULD UPDATE` in a dry run). Only an adoption lists kept files, on stderr: the existing agent, skill and project-skeleton files its overwrite question kept. Kept root guidance and an existing `docs/coding_guidelines.md` are not listed, and an upgrade lists no kept files.

The starter `AGENTS.md` follows the root guidance template in the CLI package (`cli/src/ai_team/init/sources/root/AGENTS.md`). `ai-team check-layout` requires these `##` sections in the file: `Build and Install`, `Test`, `Run`, `Lint and Format`, and `Key Conventions`. If you write the file by hand, use the same headings and fill in your project's commands and conventions.

### Step 4: Customize for Your Stack

**Baseline test instructions** — Fill in the command agents should run to execute the test suite. Put it in root guidance (`AGENTS.md`) or clearly reference a project-local doc that contains it. `dev-loop` reads project guidance at startup; if the command is missing or ambiguous, the loop asks for product owner clarification before claiming a task. If your project has no automated tests, state that explicitly so the loop can record the confirmation and continue.

**`ai-team/docs/coding_guidelines.md`** — `ai-team init` scaffolds this file as a placeholder; do not create it by hand. It is filled in by the project bootstrap (see Step 6) once S-000 is approved, with project-specific rules:
- Stack and framework conventions.
- Formatter, linter, and dependency policy.
- Naming conventions and file layout.
- Testing conventions and where test fixtures live.
- Any commands not already listed in `AGENTS.md`.

The framework's general, language-agnostic coding standards are already built into the exported agents and skills; this file only adds your project's rules.

**`.claude/settings.json`** — Configure permissions for your project. Every agent runs the `ai-team` CLI through Bash, so allow it, and add your own build and test commands:
```json
{
  "permissions": {
    "allow": ["Bash(ai-team:*)"],
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

4. **Cancel the test task**: `ai-team task set-status <task-id> cancelled --reason "setup check"`. Work items are changed only through `ai-team` commands; there is no delete command.

5. **Project guidance exists**: Confirm root guidance has a real baseline test command or clearly points to `ai-team/docs/coding_guidelines.md` or equivalent project-local guidance that contains it. If the project has no automated baseline test, state that explicitly.

### Step 6: Start Working

Your project is ready. Start with S-000, the system overview (`/new-system-overview`). After S-000 is approved, run the project bootstrap: ask the planner to run `spec-breakdown` on S-000, which plans only the bootstrap tasks (decisions and architecture documents, environment configuration, coding guidelines, project guidance, and the README description). Run `/dev-loop` on those tasks before feature work. The bootstrap fills in `ai-team/docs/coding_guidelines.md`.

The typical feature workflow is then:

1. **Describe a feature** — write what you want built.
2. **Brainstorm** — the planner agent explores approaches and produces a specification (`/new-spec`).
3. **Approve the spec** — the product owner reviews and approves (Gate 1).
4. **Break into tasks** — the planner decomposes the spec into atomic tasks.
5. **Run Gate 2 preflight** — the architect validates the task plan before development starts.
6. **Run `/dev-loop`** — autonomously implements, reviews, and integrates each task. Gate 3 code review and Gate 4 integration verification happen inside the loop.
7. **Fix bugs with `/bug-loop`** — when open bugs exist, the loop diagnoses first, then fixes, reviews, and integrates.
8. **Final approval** — the product owner approves the merge from `dev-agent` to `main` (Gate 5).

For the full workflow details, see `ai-process/processes/workflow_overview.md`.
