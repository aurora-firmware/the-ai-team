# The AI Team Definition

> Agent-development guide for this repository. For user-facing setup and usage,
> see [README.md](README.md) and `guides/`. The index of internal documents is
> [`docs/development/AGENTS.md`](docs/development/AGENTS.md).

This repository defines the AI-team framework itself: the rules in `ai-process/`,
the authoring contracts in `guides/`, and the CLI/package implementation in
`cli/`.

## Build and Install

From `cli/`:

```bash
python scripts/sync_init_scaffolds.py
uv build
```

Run `python scripts/sync_init_scaffolds.py` whenever anything under
`cli/src/ai_team/init/sources/project/`, `sources/agents/` or `sources/skills/`
changes, and commit the regenerated `cli/src/ai_team/init/scaffolds/` with the
change: `uv run pytest` fails when the committed scaffolds differ from a fresh
sync. `sources/root/` and `cli/src/ai_team/templates/` are read by the CLI at
runtime and need no sync.

If you change a command, a flag or its help text, regenerate `cli/docs/commands.md`
with `bash cli/scripts/gen_docs.sh` (from the repository root) before committing;
CI fails when it is stale. Building, tagging and publishing a release are described
in [`cli/docs/usage.md`, For Maintainers](cli/docs/usage.md#for-maintainers).

## Test

From `cli/`:

```bash
uv run pytest
```

Use the repo-level checks before reporting work complete. If `uv` cannot write to
its default cache in this environment, point the cache at a writable location
under `/tmp`.

## Run

Two `ai-team` CLIs are used in this repository:

- **The released CLI** manages this repository's own artifacts (specs, ADRs and the
  tracker). `mise run setup:ai-team` installs the version pinned by `AI_TEAM_REF` in
  `mise.toml` into `.tmp/tools/`, which mise puts on `PATH`. It matches
  `[init].framework_version` in `.ai-team.toml`. To try another ref, set
  `AI_TEAM_REF` in the git-ignored `mise.local.toml`.
- **The CLI built from source** tries out changes: `uv run ai-team <command>` from
  `cli/`. It prints the version mismatch warning in this repository; that is
  expected.

If a required project-specific command or rule is not documented here, stop and
ask rather than guessing.

## Lint and Format

From `cli/`:

```bash
uv run ruff format --check .
uv run ruff check .
```

`bash cli/scripts/install-hooks.sh` installs an optional pre-commit hook that runs
the format check.

## Key Conventions

| Path | Purpose |
|---|---|
| `ai-process/` | Framework rules: workflows, standards, and architecture. The single source of truth |
| `guides/` | Authoring contracts for agents, skills and specs, and the adopter setup and customization guides |
| `cli/src/ai_team/init/sources/` | Source of truth for exported agents, skills, the project skeleton and the root guidance starter |
| `cli/src/ai_team/templates/` | Source of truth for CLI artifact templates |
| `cli/docs/` | User and maintainer documentation for the CLI |
| `docs/ai-team/` | Spec and ADR artifacts for this repo; tasks, bugs and change-requests live in the local tracker (`ai-team tracker path`) |
| `docs/development/` | Internal developer docs: architecture, tech stack, and the index of internal documents |

`cli/src/ai_team/init/scaffolds/` is generated from `sources/project/`,
`sources/agents/` and `sources/skills/`.
Do not edit generated scaffolds to change framework behavior.

- `ai-process/` dictates what the agents, skills, guides and CLI do. Where another
  document is unclear, follow `ai-process/`. Where `ai-process/` itself seems
  wrong, stop and tell the product owner instead of working around it.
- Keep framework behavior in `ai-process/`, `guides/`, or the CLI source tree.
- Do not read from or depend on the repo-local `.claude/` folder.
- Do not hardcode project-specific test, build, deploy, or run commands into the
  framework sources; consuming projects must supply those details themselves.
- Keep skills procedural and agents role-based. If a rule is shared, own it in
  one place and reference it elsewhere.
- Update the source of truth first, then regenerate scaffolds and docs together.
- Name hand-written documents in snake_case (`ai-process/guidelines/markdown_conventions.md`).
- Use the existing git and review conventions in `ai-process/guidelines/`.
- Not every change goes through the full ai-team process (spec, tasks, gates,
  loops). Fixes for review comments on an open PR are committed directly on
  that PR's branch, and small housekeeping changes are made directly on a
  short-lived branch from `main` (for example `chore/<slug>` or `fix/<slug>`)
  that merges back through a PR, without filing a task or bug. This is this
  repository's override of the branch model in
  `ai-process/guidelines/git_conventions.md`.
- Framework changes carry no backward compatibility, migrations, or upgrade
  notes. The framework is under heavy development and 1.0.0 has not been
  released, so artifacts created with an older version may fail validation.
- Reference docs:
  - `guides/agent_template.md`
  - `guides/skill_template.md`
  - `guides/spec_authoring_guide.md`
  - `guides/skill_testing_guide.md`
  - `guides/setup_guide.md`
  - `ai-process/processes/workflow_overview.md`

If a change would alter the framework contract, update the owning spec or guide
before changing the implementation.
