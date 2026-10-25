# The AI Team Definition

> Agent-development guide for this repository. For user-facing setup and usage,
> see [README.md](README.md) and `guides/`.

This repository defines the AI-team framework itself: the rules in `ai-process/`,
the authoring contracts in `guides/`, and the CLI/package implementation in
`cli/`.

## Build and Install

From `cli/`:

```bash
python scripts/sync_init_scaffolds.py
uv build
```

Run `python scripts/sync_init_scaffolds.py` whenever source scaffolds change.
If you update command output or release guidance, regenerate `cli/docs/commands.md`
with `bash cli/scripts/gen_docs.sh` (from the repository root) before committing.

## Test

From `cli/`:

```bash
uv run pytest
```

Use the repo-level checks before reporting work complete. If `uv` cannot write to
its default cache in this environment, point the cache at a writable location
under `/tmp`.

## Run

No project-specific application run command is documented for this repository.
If a required project-specific command or rule is not documented here, stop and
ask rather than guessing.

## Lint and Format

From `cli/`:

```bash
uv run ruff format --check .
uv run ruff check .
```

## Key Conventions

| Path | Purpose |
|---|---|
| `ai-process/` | Framework rules: workflows, standards, and architecture |
| `guides/` | Authoring contracts for agents, skills, specs, and setup |
| `cli/src/ai_team/init/sources/` | Source of truth for exported agents, skills, and scaffolds |
| `cli/src/ai_team/templates/` | Source of truth for CLI artifact templates |
| `cli/docs/` | User and maintainer documentation for the CLI |
| `docs/ai-team/` | Task, bug, spec, ADR, and report artifacts for this repo |

`cli/src/ai_team/init/scaffolds/` is generated from the source tree above.
Do not edit generated scaffolds to change framework behavior.

- Keep framework behavior in `ai-process/`, `guides/`, or the CLI source tree.
- Do not read from or depend on the repo-local `.claude/` folder.
- Do not hardcode project-specific test, build, deploy, or run commands into the
  framework sources; consuming projects must supply those details themselves.
- Keep skills procedural and agents role-based. If a rule is shared, own it in
  one place and reference it elsewhere.
- Update the source of truth first, then regenerate scaffolds and docs together.
- Use the existing git and review conventions in `ai-process/guidelines/`.
- Reference docs:
  - `guides/agent_template.md`
  - `guides/skill_template.md`
  - `guides/spec-authoring-guide.md`
  - `guides/setup-guide.md`
  - `ai-process/processes/workflow-overview.md`

If a change would alter the framework contract, update the owning spec or guide
before changing the implementation.
