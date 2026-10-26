# Architecture

High-level design of the ai-team solution components named in
[S-000](../ai-team/specs/S-000-system-overview.md). This document describes the
repository as it is; the contract of each component is owned by its specs and ADRs
in [`docs/ai-team/`](../ai-team/).

## Components

| Component | Lives in | Role |
|---|---|---|
| Team definition | `ai-process/`, `cli/src/ai_team/init/sources/agents/`, `cli/src/ai_team/init/sources/skills/` | The process rules, and the agent roles and procedures that carry them out |
| Generators | `cli/scripts/sync_init_scaffolds.py`, `cli/src/ai_team/init/scaffolds/` (generated), `cli/src/ai_team/init/sources/project/`, `cli/src/ai_team/init/sources/root/`, `cli/src/ai_team/templates/` | Produce every file the CLI hands to a project: exported agents and skills, the project skeleton, starter guidance and artifact templates |
| CLI | `cli/src/ai_team/` (`cli.py`, `commands/`, `core/`) | The `ai-team` command: `init`, `check-layout`, artifact creation, listing, validation, lifecycle moves, the local tracker and reports |
| End-user documentation | `cli/docs/usage.md`, `cli/docs/commands.md` (generated), `guides/setup-guide.md`, `guides/customization-guide.md` | How to install, set up, customise and use ai-team |

## How they fit together

```
ai-process/ ──(rules)──> sources/agents, sources/skills ──┐
                                                          │ sync_init_scaffolds.py
sources/project, sources/root ────────────────────────────┼──> init/scaffolds/ (generated)
                                                          │
templates/ ───────────────────────────────────────────────┘
                                                               │
                                       packaged in the wheel   ▼
                                          ai-team CLI ── init ──> adopting project
                                              │                   (.claude/, ai-team/, AGENTS.md,
                                              │                    .ai-team.toml)
                                              └── gen_docs.sh ──> cli/docs/commands.md
```

- **Single source.** Agents, skills and the project skeleton are authored once under
  `cli/src/ai_team/init/sources/`. `cli/scripts/sync_init_scaffolds.py` regenerates
  `cli/src/ai_team/init/scaffolds/`, which ships inside the package. Generated
  scaffolds are never edited by hand.
- **One export target.** Claude is the only agent tool the CLI exports to (ADR-003).
- **CLI layering.** `cli.py` wires the Typer app; `commands/` holds one module per
  command group; `core/` holds the shared logic (locator, config, tracker, layout,
  validation, templates, IDs). Commands call `core`; `core` does not import
  `commands`.
- **Artifacts.** Specs and ADRs live in the project folder (`[project] dir`, here
  `docs/ai-team/`) under version control. Tasks, bugs and change-requests live in the
  local tracker (`[tracker] dir`, here `.ai-team/tracker/`), outside version control
  (S-006).
- **Command reference.** `cli/docs/commands.md` is generated from the CLI by
  `bash cli/scripts/gen_docs.sh`; CI fails when it is stale.
