# ai-team CLI Usage Guide

This guide covers installation, initialisation, daily workflows, the expected
`ai-team/` folder structure, and a maintainer section. For an exhaustive list
of every command, flag, and argument, see [commands.md](commands.md).

---

## Table of Contents

1. [Installation](#installation)
2. [Initialisation](#initialisation)
3. [Daily Workflows](#daily-workflows)
4. [Project Folder Structure](#project-folder-structure)
5. [For Maintainers](#for-maintainers)

---

## Development warning

For every invocation, `ai-team` emits this warning exactly once:

```text
Warning: ai-team is under development. Please report issues at https://github.com/aurora-firmware/the-ai-team/issues
```

The warning goes to stderr for help, version, successful commands, failed
commands, and commands that emit JSON. Normal human-readable and JSON output
remains on stdout, so redirect or parse stdout without including the warning.

### Version mismatch warning

When the project's `.ai-team.toml` records an `[init].framework_version` that
differs from the running `ai-team` version (exact string comparison, as in
`ai-team check-layout`), every command except `init` also writes this warning
once to stderr, after the development warning:

```text
Warning: .ai-team.toml framework_version <configured> does not match ai-team <running>. Install ai-team <configured>, or run `ai-team init --update-skills` to update the project to <running>.
```

The warning is skipped when:

- no project or no `.ai-team.toml` is found;
- the versions are equal;
- `[init].framework_version` is missing, empty, or not a version string;
- `.ai-team.toml` is not valid TOML;
- the command is `ai-team init`, or the run is root `--help` or `--version`.

The warning never changes stdout, `--json` output, or the exit code.

---

## Installation

**Requirements:** Python 3.14 or later.

### From GitHub Releases

```bash
pipx install https://github.com/<org>/<repo>/releases/download/<tag>/ai_team-<version>-py3-none-any.whl
```

### From a local build

Clone this repository, then:

```bash
cd cli
python scripts/sync_init_scaffolds.py   # refreshes bundled scaffold snapshots
uv build
pipx install --force dist/*.whl
```

`sync_init_scaffolds.py` regenerates the bundled scaffolds in
`cli/src/ai_team/init/scaffolds/` from the package-owned sources in
`cli/src/ai_team/init/sources/` so that `ai-team init` ships up-to-date
scaffolds. It never reads the repository's `.claude/` folder, so edit the
sources and re-run it rather than editing the generated output. Always run it
before `uv build`.

### Verify the install

```bash
ai-team --version
```

---

## Initialisation

`ai-team init` scaffolds a fresh AI-team repository, adopts a repository that
already has some of the files, and upgrades one that is already initialised.
Run it from the target project's root directory.

```bash
ai-team init [PATH] [OPTIONS]
```

`PATH` defaults to `.` (the current directory).

### Init cases

`init` looks at the repository and picks one of three cases. The detection
does not depend on any flag: `init` detects an upgrade from `[init] framework_version`
in `.ai-team.toml`.

| Case | Detected when | What `init` does |
|---|---|---|
| Upgrade | `.ai-team.toml` exists in the repository root and records `[init] framework_version`. | Keeps every configured setting and asks two questions (below); a question that covers no files is not asked. Nothing is overwritten without a yes. Missing project-skeleton files that no question covers are written without a question and never overwritten. |
| New project | There is no `.ai-team.toml` that records `[init] framework_version` (a hand-written one that presets settings is kept), and none of the files `init` would write exists. | Writes the scaffold, the tracker folder and `.ai-team.toml`. No overwrite question is asked. |
| Adoption | There is no `.ai-team.toml` that records `[init] framework_version`, but some files `init` would write already exist: agent, skill or project files, or a root `AGENTS.md`. | Lists the existing agent, skill and project files and asks once: `Overwrite these existing files?` Root `AGENTS.md` is not part of that question; it follows the table under [Root guidance files](#root-guidance-files). |

**Upgrade questions.** An upgrade asks, in order:

1. `Update the ai-team docs (AGENTS.md, .gitignore) in <project dir>?`
2. `Update the agents and skills?`

Each defaults to no. `--update-docs` answers the first yes and `--update-skills`
answers the second yes without asking; with `--no-interactive` an unanswered
question is no. A yes on the agents and skills question also bumps
`[init].framework_version` in `.ai-team.toml`, so run it to clear the version
mismatch warning.
`docs/coding_guidelines.md` is never overwritten, whatever the answers.

**Adoption question.** Answering no (or running with `--no-interactive`) keeps
every existing file, writes only the missing ones and lists the skipped files.
Answering yes overwrites them, and each replaced file is reported as
`OVERWROTE: <path>`.

**Stale definitions.** After an upgrade updates the agents and skills, any agent
or skill in `.claude/agents/` and `.claude/skills/` that this version of `ai-team` does not ship is
left alone, and `init` writes this warning to stderr:

```text
Warning: these skills or agents are not shipped by this version of ai-team; they were neither updated nor removed:
- <path>
```

### Flags

| Flag | Description |
|---|---|
| `--dry-run` | Print what the real run with the same flags would do, without touching the filesystem. Lines are `WOULD WRITE` (new file), `WOULD OVERWRITE` (every approved overwrite, including `--update-docs` and `--update-skills` on an upgrade), `WOULD CREATE` (a missing tracker folder), `WOULD UPDATE` (a `.gitignore` missing the tracker rule) and `WOULD PROMPT` (a root `AGENTS.md`, or a file covered by an upgrade or adoption question, that the interactive run would ask about; a dry run never prompts). The first line reports the detected case: `CASE: upgrade`, `CASE: new project` or `CASE: adoption`. Root guidance files the real run would skip are not listed. |
| `--force` | Answer yes to every overwrite question: on an upgrade both the docs and the agents-and-skills questions, on an adoption the single overwrite question, and the root guidance prompts per the table under [Root guidance files](#root-guidance-files). Configured `[project] dir`, `[tracker] dir`, `[git] integration_branch` and any other tables are kept on an upgrade. `docs/coding_guidelines.md` is the exception: it is written only when missing and never overwritten, even with `--force`. Every existing file that is replaced is reported as `OVERWROTE: <path>`. |
| `--update-docs` | On an upgrade, update the ai-team docs without asking. |
| `--update-skills` | On an upgrade, update the agents and skills without asking. |
| `--project-dir TEXT` | Artifact folder, at any depth (e.g. `docs/ai-team`). Defaults to the configured `[project] dir`, else `ai-team`. Must be relative and contain no `..`. |
| `--integration-branch TEXT` | Branch that task, bug, and planning work integrates into. Defaults to the configured `[git] integration_branch`, else `dev-agent`. |
| `--no-interactive` | Skip all prompts. |
| `--create-root-guidance` | Create root `AGENTS.md` from a starter template without prompting, in interactive and non-interactive mode. An existing file is replaced only together with `--force`. Defaults to false. |

### What gets scaffolded

`ai-team init` never copies `ai-process/`. All scaffolded files come from
package-owned snapshots bundled inside the `ai_team.init.scaffolds` package.

`init` always writes `.claude/agents/` and `.claude/skills/`. Running
`ai-team init .` writes:

```
ai-team/
  AGENTS.md       ← project guidance file
  specs/
  decisions/
  docs/
.ai-team/
  tracker/        ← local work-item tracker (git-ignored)
.claude/
  agents/
  skills/
.ai-team.toml     ← includes [tracker] dir = ".ai-team/tracker"
.gitignore        ← gains a /.ai-team/ rule
```

The next steps printed by `init` name each skill as `/name`.

Each folder is created with a `.gitkeep` placeholder so git tracks the
empty directories.

`.ai-team.toml` is the marker file that tells the CLI where the project root
is. It records the framework version used.

### Root guidance files

After scaffolding the project skeleton and tool files, `ai-team init` offers to
create a root-level `AGENTS.md` from a starter template. `AGENTS.md` is the only
guidance file `init` generates, in the project folder and in the repository root.
It tells AI tools how to build, test, and run your project.

- **Interactive mode** (default): the CLI prompts for the file. Answer `y` to
  create a starter template, or `n` to skip.
- **`--create-root-guidance`**: creates the file without prompting, in
  interactive and non-interactive mode. Useful in CI or scripted setup flows.
- **`--no-interactive` without `--create-root-guidance`**: skips the file.

Existing root guidance files are never overwritten unless `--force` is also passed:

| Flags, file exists | Interactive | `--no-interactive` |
|---|---|---|
| none | left untouched | left untouched |
| `--force` | prompts; overwritten on yes | left untouched |
| `--force --create-root-guidance` | overwritten, no prompt | overwritten, no prompt |

Every file `init` creates is reported on stdout as `WROTE: <path>` (`WOULD WRITE` in a dry run) and every file it replaces as `OVERWROTE: <path>` (`WOULD OVERWRITE` in a dry run). The tracker folder it creates is reported as `CREATED: <path>` (`WOULD CREATE` in a dry run) and the root `.gitignore` it adds the tracker rule to as `UPDATED: <path>` (`WOULD UPDATE` in a dry run). Only an adoption lists kept files, on stderr: the existing agent, skill and project-skeleton files its overwrite question kept. Kept root guidance and an existing `docs/coding_guidelines.md` are not listed, and an upgrade lists no kept files. The `WROTE` and `OVERWROTE` lines cover root guidance, generated agents and skills, project-skeleton files, and `.ai-team.toml`.

### Example: preview then initialise

```bash
# Preview without writing
ai-team init . --no-interactive --dry-run

# Initialise for real (interactive: prompts for root AGENTS.md)
ai-team init .

# Non-interactive with root guidance files
ai-team init . --no-interactive --create-root-guidance
```

---

## Daily Workflows

### Check the repository layout

Run the read-only layout diagnostic from anywhere inside an initialized
repository:

```bash
ai-team check-layout
```

The command runs four ordered validation levels:

1. **Level 1 — expected directories.** Checks the configured project directory,
   every directory in the current project scaffold, and the agent and skill
   directories. Extra directories are allowed. Also
   reports a tracker folder that lies inside the repository but is not ignored
   by git, and legacy `tasks/`, `bugs/`, `change-requests/`, or `archive/`
   folders in the project directory that still hold a markdown file other than
   `.gitkeep` or `TEMPLATE-*.md`. Also reports a missing
   `docs/coding_guidelines.md` in the project directory, with the suggested fix
   to create it from the scaffold placeholder.
2. **Level 2 — artifact names and frontmatter.** Checks managed specs and
   decisions in the project directory, and tasks, bugs, and change requests in
   the tracker, for the expected filename and required frontmatter. Tasks, bugs,
   and change requests must have an allowed `status` value; specs and decisions
   must have a `status` field.
3. **Level 3 — root guidance.** Requires root `AGENTS.md`. It must contain
   non-placeholder `Build and Install`, `Test`, `Run`, `Lint and Format`, and
   `Key Conventions` guidance.
4. **Level 4 — version alignment.** Checks that the framework version recorded
   in `.ai-team.toml` exactly matches the running CLI distribution version.

Each finding reports `Level`, `Path`, `Problem`, and `Suggested fix`. Findings
are ordered by level and then path. A clean repository prints an explicit
success message and returns exit code 0; one or more findings are all reported
before the command returns exit code 1.

`check-layout` only observes the repository: it does not repair, create, move,
rename, rewrite, or delete files or directories. Suggested fixes are guidance
for the user, and no project guidance command is executed.

### Create and ship a task

```bash
# 1. Create a new pending task
ai-team task new "Add user onboarding flow" --priority high --assigned-role developer

# 2. Start work (sets status: in-progress)
ai-team task start T-001

# 3. Mark complete (sets status: completed)
ai-team task complete T-001
```

If a task gets stuck:

```bash
# Block with a reason
ai-team task block T-001 --reason "Waiting for API contract from backend team"

# Unblock when the blocker is resolved
ai-team task unblock T-001
```

List all tasks (all states) or filter by state:

```bash
ai-team list tasks
ai-team list tasks --state in-progress
```

Show a specific task (rendered markdown):

```bash
ai-team show T-001
```

### File and resolve a bug

```bash
# 1. File a new bug
ai-team bug new "Login crashes on empty token" --severity high

# A regression from a task branch records that branch as source_branch;
# the bug-fix loop bases the bug branch on it
ai-team bug new "Login regressed" --source-branch task/T-021-login

# 2. Start investigation (sets status: in-progress)
ai-team bug start B-001

# 3. Resolve when fixed (sets status: resolved)
ai-team bug resolve B-001
```

List bugs:

```bash
ai-team list bugs
ai-team list bugs --state open
```

### Create a spec or ADR

```bash
# New specification (lands in ai-team/specs/ as S-NNN-<slug>.md)
ai-team spec new "Billing reconciliation" --author "planner" --status draft

# New Architecture Decision Record (lands in ai-team/decisions/)
ai-team adr new "Use PostgreSQL for ledger storage" --status proposed
```

`spec new` writes a draft scaffold of a feature spec. The spec-writing agent
fills it through the exported `new-spec` skill, which follows the authoring
contract in the framework's spec authoring guide.

### System overview (S-000)

S-000 is the project's system overview. Create it once with:

```bash
ai-team spec new --overview
```

The title is optional with `--overview`; the spec is created from the
system-overview template. Agents can do the same through the
`new-system-overview` skill.

When a project has no S-000, `validate`, `report`, `status` and the `new`
commands (`task new`, `bug new`, `change-request new`, `spec new`, `adr new`) print an
advisory hint to stderr: "this project has no system overview (S-000)". The
hint is always on, never changes stdout or exit codes, and disappears once
S-000 exists.

`ai-team task new --spec S-000` creates the project bootstrap tasks, the
tasks that set a new project up from its system overview.
`validate` does not report them, because their source spec is the system
overview.

### File a change request

Change requests capture proposed changes before they are planned as tasks.
They land in the local tracker's `change-requests/` folder (outside version control) with a `CR-NNN-<slug>.md` filename.

```bash
# Create a new pending change request (lands in the tracker)
ai-team change-request new "Revamp onboarding flow"

# Emit machine-readable output for agent use
ai-team change-request new "Revamp onboarding flow" --json

# Record the human decision
ai-team change-request set-status CR-001 approved
```

Tasks, bugs, and change-requests all live in the local tracker; `ai-team tracker path`
prints its location. Their state is the frontmatter `status` field, changed with
`ai-team task|bug|change-request set-status` or the `start`/`complete`/`block`/`resolve`
shortcuts — never by moving files.

List change requests, specs, and ADRs:

```bash
ai-team list change-requests
ai-team list specs
ai-team list adrs
```

### Generate a Gate 5 status report

Gate 5 is the human sign-off before merging `dev-agent` to `main`. These two
commands give the context needed:

```bash
# Inline summary in the terminal
ai-team status

# Write a full progress report to ai-team/docs/reports/
ai-team report

# Override the output path
ai-team report --out /tmp/custom-report.md
```

`ai-team status` shows counts of active specs (not superseded, excluding the
S-000 overview), tasks in every state, bugs by state,
in-progress tasks, blocked tasks, critical/high bugs, and the latest
integration result. The integration result cites the newest Work Log session
of a completed task or resolved bug (ID, session, date, and first line), or
`not found` when no such session exists. The integration result is read only
from Work Log headings of the exact form `### Session N — YYYY-MM-DD` (an em
dash, with `N` a session number); a completed task or resolved bug whose
sessions use any other heading form reports `not found`.

`ai-team report` renders the same data into a markdown file using the bundled
report template.

### Validate artifacts

```bash
# Validate all artifact types
ai-team validate --all

# Validate tasks and bugs only
ai-team validate --tasks --bugs

# Validate change requests only
ai-team validate --change-requests

# Emit JSON for scripting
ai-team validate --json
```

For feature specs in `review` or `approved` status, `validate --specs` also
checks the spec structure, ignoring comments and code:

- every required section is present once and is not empty (Amendment Log may be
  empty);
- Behavioral Requirements has at least one `REQ-NNN — Title` heading, numbered
  from 001, and each requirement states a SHALL or MUST obligation;
- Quality Requirements holds requirements or `None` followed by a reason;
- each requirement has `AC-NNN.M — Title` scenarios with matching numbers,
  nested under it, with content and a nonempty `**Verification:**` line;
- requirement and scenario identifiers are unique, and no scenario sits outside
  a requirement;
- no TODO, TBD, TBR, or clarification placeholders, and no unchanged template
  headings, remain.

Drafts are not checked, and S-000 follows its separate system-overview
contract. These checks establish structure, not semantic completeness or human
approval.

Exit code is 1 if any error-level finding is reported.

### Archive old artifacts

Completed tasks and resolved bugs older than a threshold are moved to
`<tracker>/archive/YYYY-MM/`. Both the age and the `YYYY-MM` month come from the
item's `created` date:

```bash
# Preview what would be archived (default: older than 90 days)
ai-team archive --dry-run

# Archive with a custom threshold
ai-team archive --older-than 30d
```

Supported units: `d` (days), `w` (weeks), `m` (months, = 30 days),
`y` (years, = 365 days).

---

## Project Folder Structure

Every command that reads or writes artifacts resolves the project root through
the **locator**, which tries four strategies in order:

1. **Explicit `root=` argument** — only when callers pass `root` programmatically.
2. **`AI_TEAM_ROOT` environment variable** — set this to override auto-detection
   in CI or scripts:
   ```bash
   export AI_TEAM_ROOT=/path/to/repo
   ```
3. **Walk up from `cwd` looking for `.ai-team.toml`** — uses the `[project] dir`
   value from the file as the artifact folder name.
4. **Walk up from `cwd` looking for a folder named `ai-team`** — the
   convention-based fallback.

If no project root is found the CLI prints an error that suggests running
`ai-team init` and exits with code 1.

### The `.ai-team.toml` marker

`ai-team init` writes `.ai-team.toml` in the repository root with content
similar to:

```toml
[project]
dir = "ai-team"

[tracker]
dir = ".ai-team/tracker"

[git]
integration_branch = "dev-agent"

[init]
framework_version = "0.1.0"
```

The `[project] dir` key is what the locator reads in strategy 3. It accepts any
relative folder inside the repository, at any depth (for example
`docs/ai-team`), with no `..` component; `check-layout` validates it and checks
the artifacts inside it. Projects initialised before the default changed keep
their `dir = "project"` setting and need no change.

To preset settings before the first `ai-team init`, write only the `[project]`,
`[tracker]` and `[git]` tables and leave out `[init]`: `init` writes `[init]` itself,
and a marker that already records `[init] framework_version` is treated as an upgrade.

The `[git] integration_branch` key names the branch that task, bug, and
planning work integrates into (default `dev-agent`).

The generated agents and skills name these two settings through the
`{{project_dir}}` and `{{integration_branch}}` placeholders. `ai-team init`
fills them in from `.ai-team.toml` when it writes the files, so after changing
either setting, run `ai-team init . --update-skills --update-docs` to refresh them.
Hand edits to generated files are overwritten by that refresh.

### Expected layout

```
<repo-root>/
  .ai-team.toml               ← locator marker; written by ai-team init
  ai-team/                    ← artifact root (name comes from [project] dir)
    specs/                    ← feature specifications
      archive/                ← superseded spec versions
    decisions/                ← Architecture Decision Records (ADR-NNN-*.md)
    docs/                     ← project-specific docs: coding guidelines,
                              │  commands, stack-specific notes
  .ai-team/tracker/           ← local work-item tracker ([tracker] dir; git-ignored)
    tasks/                    ← T-NNN-*.md; state is the status field
    bugs/                     ← B-NNN-*.md; state is the status field
    change-requests/          ← CR-NNN-*.md; state is the status field
    archive/
      YYYY-MM/                ← old completed/resolved items (ai-team archive)
    review-packages/          ← loop scratch files: <id>.md review package
```

Tasks, bugs, and change-requests live in the tracker, outside version control.
A relative `[tracker] dir` resolves against the folder holding `.ai-team.toml`
in the repository's main working tree, so every git worktree shares one
tracker; `ai-team tracker path` prints the resolved folder. The development
and bug-fix loops write scratch review packages to
`<tracker>/review-packages/<id>.md`, locating the tracker with
`ai-team tracker path`.

Artifact filenames follow the patterns `T-NNN-<slug>.md` (tasks),
`B-NNN-<slug>.md` (bugs), `S-NNN-<slug>.md` (specs), and `ADR-NNN-<slug>.md`
(ADRs). The CLI allocates the next sequential task, bug, and change-request ID
by scanning the tracker, including its archive, and the next spec ID by
scanning `specs/` on the current branch. Legacy spec files without the `S-NNN-` prefix are
also accepted by validation.

### The `.ai-team.lock` sentinel

The first time `ai-team task new`, `bug new`, or `change-request new` runs, it
creates a sentinel file at `<tracker>/.ai-team.lock`, and `spec new` creates one
at `<project_dir>/.ai-team.lock`, to coordinate concurrent artifact-ID
allocation across processes and worktrees. This file is deliberately
never deleted: the lock is a kernel-level `flock` on the file, released
automatically when the holding process exits, so leaving the sentinel on disk
is harmless and removing it would reopen the race the lock exists to prevent.

`ai-team init` scaffolds an `ai-team/.gitignore` with a `.ai-team.lock` entry,
so the sentinel never shows up as untracked in `git status`, and a
`docs/reports/` entry that keeps on-demand status reports untracked. Projects that ran `ai-team init` before this `.gitignore` was added
will not receive it retroactively — add a `.ai-team.lock` entry to your own
`.gitignore` (at the repository root or inside the project directory) to get
the same effect.

---

## For Maintainers

### Module map

The `ai_team` package lives in `cli/src/ai_team/` and is structured as:

| Module / Package | Purpose |
|---|---|
| `ai_team.cli` | Root Typer app and console-script entry point (`ai-team`). |
| `ai_team.commands/` | One module per command group; auto-discovered at startup. |
| `ai_team.core/` | Pure-Python helpers with no Typer dependency. |
| `ai_team.core.locator` | Project root resolution (four-strategy locator). |
| `ai_team.core.ids` | Sequential ID allocation (`T-NNN`, `B-NNN`, etc.). |
| `ai_team.core.fs` | Artifact file read/write helpers. |
| `ai_team.core.models` | Dataclasses for task, bug, spec, and ADR frontmatter. |
| `ai_team.core.templates` | Loads bundled Markdown templates from the package. |
| `ai_team.core.validate` | Artifact metadata validation logic. |
| `ai_team.core.spec_content` | Structural checks for feature-spec bodies. |
| `ai_team.templates/` | Bundled Markdown artifact templates (task, bug, spec, adr, report). |
| `ai_team.init/` | Scaffold data for `ai-team init`. |
| `ai_team.init.scaffolds/` | Package-owned snapshots: `scaffolds/{project,agents,skills}/`. |
| `ai_team.render` | Rich console and JSON output helpers. |

### How to add a new command

1. Create a new module in `cli/src/ai_team/commands/`, e.g. `my_cmd.py`.
2. Expose two module-level attributes:
   - `NAME: str` — the subcommand name as it appears on the CLI.
   - `app: typer.Typer` — the Typer application for the command group.
3. No changes to `cli.py` or `commands/__init__.py` are needed; auto-discovery
   picks up the new module via `pkgutil.iter_modules` at startup.

A broken command module (import error or missing attributes) is skipped silently
so it cannot crash the whole CLI.

### How to run the tests

```bash
cd cli
uv run pytest
```

Run a specific test file:

```bash
uv run pytest tests/test_task_new.py -v
```

### How to maintain scaffold sources

The scaffold files shipped inside the package are **package-owned copies** —
they are not read from the repository's `.claude/` tree at runtime. This
means any change to the canonical agent or skill definitions must be reflected
in the bundled snapshots before the next release.

The generator script `scripts/sync_init_scaffolds.py` keeps the snapshots
in sync. It reads from:

- `cli/src/ai_team/init/sources/skills/<name>/SKILL.md` — one source file per
  skill (`sources/skills/<name>/SKILL.md`)
- `cli/src/ai_team/init/sources/agents/*.md` — one source file per agent
  (`sources/agents/*.md`)

and writes the output into:

- `cli/src/ai_team/init/scaffolds/agents/` — agent definitions for `.claude/agents/`
- `cli/src/ai_team/init/scaffolds/skills/` — skill definitions for `.claude/skills/`
- `cli/src/ai_team/init/scaffolds/project/` — project skeleton

The three folders together are `scaffolds/{project,agents,skills}/`.

Run `sync_init_scaffolds.py` whenever the canonical agent or skill files
change. The script is also run automatically at the start of the local-build
installation step (see `From a local build` above).

`ai-team init` never copies `ai-process/`. The specification layer is
intentionally excluded from the scaffold — only the implementation layer
(agents, skills) and the project skeleton are bundled.

### How to build and release

Before building, refresh the bundled scaffold snapshots so `ai-team init` ships
the latest `.claude/agents/` and `.claude/skills/`:

```bash
cd cli
python scripts/sync_init_scaffolds.py
uv build
```

The wheel and source distribution land in `cli/dist/`. To publish a release,
push a version tag with no `v` prefix (`1.2.3`, or `1.2.3-label`, which CI
builds as the PEP 440 local version `1.2.3+label`; the GitHub Release is not
marked as a pre-release):

```bash
git tag 1.2.3
git push origin 1.2.3
```

CI then builds the wheel and sdist, regenerates `commands.md`, and publishes a
GitHub Release with those files attached.

To install the local wheel for manual testing:

```bash
pipx install --force cli/dist/*.whl
```

### How to regenerate `commands.md`

`cli/docs/commands.md` is a generated file — do not edit it by hand. Regenerate
it with:

```bash
bash cli/scripts/gen_docs.sh
```

Run this from the repository root. The script calls `typer ai_team.cli utils docs`
via `uv run` and prepends the generated-file header.

The full usage form is:

```bash
bash cli/scripts/gen_docs.sh [--output <path>]
```

Without `--output`, the script writes the tracked `cli/docs/commands.md`. Pass
`--output <path>` to write the generated docs elsewhere, for example to compare
them against the tracked file without modifying it:

```bash
bash cli/scripts/gen_docs.sh --output /tmp/commands.md
```

A relative `<path>` resolves against the caller's working directory.
