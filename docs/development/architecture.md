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
| End-user documentation | `cli/docs/usage.md`, `cli/docs/commands.md` (generated), `guides/setup_guide.md`, `guides/customization_guide.md` | How to install, set up, customise and use ai-team |

## How they fit together

```
ai-process/ ──(rules)──> sources/agents, sources/skills ──┐
                                                          │ sync_init_scaffolds.py
sources/project ──────────────────────────────────────────┴──> init/scaffolds/ (generated, committed)
                                                                     │
sources/root, templates/ ──(read at runtime)──┐                      │
                                              ▼                      ▼
                               packaged in the wheel: ai-team CLI ── init ──> adopting project
                                              │                    (.claude/, ai-team/, AGENTS.md,
                                              │                     .ai-team.toml)
                                              └── gen_docs.sh ──> cli/docs/commands.md
```

- **Single source.** Agents, skills, the project skeleton and the root guidance
  starter are authored once under `cli/src/ai_team/init/sources/`.
  `cli/scripts/sync_init_scaffolds.py` regenerates `cli/src/ai_team/init/scaffolds/`
  from `sources/project/`, `sources/agents/` and `sources/skills/`; the scaffolds are
  committed and ship inside the package, and a test fails when they differ from a
  fresh sync. Generated scaffolds are never edited by hand.
- **Read at runtime.** The root guidance starter (`sources/root/AGENTS.md`) and the
  artifact templates (`cli/src/ai_team/templates/`) are not synced: `init` and the
  `new` commands read them from the installed package.
- **One export target.** Claude is the only agent tool the CLI exports to (ADR-003).
- **CLI layering.** `cli.py` wires the Typer app; `commands/` holds one module per
  command group; `core/` holds the shared logic; the module map is in
  [`cli/docs/usage.md`](../../cli/docs/usage.md#module-map). Commands call `core`; `core` does not import
  `commands`.
- **Artifacts.** Specs and ADRs live in the project folder (`[project] dir`, here
  `docs/ai-team/`) under version control. Tasks, bugs and change-requests live in the
  local tracker (`[tracker] dir`, here `.ai-team/tracker/`), outside version control
  (S-006).
- **Command reference.** `cli/docs/commands.md` is generated from the CLI by
  `bash cli/scripts/gen_docs.sh`; CI fails when it is stale.

## Component design

How the parts behind each spec are built. The specs own what each part does; this
section records the design that used to sit in their Architecture sections.

### Layout diagnostics (S-003)

- `check-layout` (`core/layout.py`) only reads. `resolve_layout` works out the
  repository root, the project folder, the expected scaffold folders and the running
  CLI version from `.ai-team.toml` and the installed package, never from the network.
- Four levels run in order, from structural prerequisites to content, so a missing
  input is told apart from a malformed one: (1) expected folders and tracker
  placement, (2) artifact names and frontmatter, (3) the configured root guidance,
  (4) the scaffold and CLI version match. A later level reports a missing
  prerequisite instead of failing.
- Each level returns `LayoutFinding` entries (level, path, problem, suggested fix),
  and one run reports them all together.
- The development warning and the version mismatch warning go to stderr, so output
  meant for machine parsing stays clean.

### Local tracker (S-006)

- `core/tracker.py` resolves `[tracker] dir` (`resolve_tracker_dir`). A relative path
  resolves against the `.ai-team.toml` folder in the main working tree, so every
  worktree of a repository sees the same tracker.
- The store keeps one flat folder per kind (`tasks/`, `bugs/`, `change-requests/`),
  plus `review-packages/` for loop scratch files. A work item's state is its
  `status` field only; no folder or filename encodes it.
- Skills create, find and transition work items only through `ai-team` commands.
  They edit the body of a file whose path a command reported.

### System overview support (S-007)

Where each S-000 rule lives:

| Rule | Owner |
|---|---|
| Fixed section structure of the overview | `cli/src/ai_team/templates/system-overview.md` |
| S-000 content contract: sections, component definition and checks, groups, Decisions needed, Users scope, S-000 versus spec boundary | `guides/spec_authoring_guide.md` |
| Writing S-000 with the product owner, greenfield or brownfield; completion after Gate 1; brownfield change request; hand-over to the bootstrap | `new-system-overview` skill |
| Feature spec Purpose names the S-000 component; system-wide structure stays in S-000 | `cli/src/ai_team/templates/spec.md` and the `new-spec` skill |
| Creating S-000, protecting its ID, accepting bootstrap tasks from S-000, the missing-S-000 hint | `ai-team spec new`, `task new`, `validate` and the hint |
| Project bootstrap tasks from S-000, including the default `docs/development/` location | `spec-breakdown` skill, Gate 2 in `ai-process/processes/quality_gates.md` |
| Planner and Architect read S-000 first when it exists | Planner and Architect agent descriptions |
| Suggesting the overview when S-000 does not exist | `using-ai-team` and `brainstorm` skills |
| A new or changed spec stays within S-000's components | `architecture-consistency-review` skill |
| Gate 1 criteria for S-000; S-000 left out of the pre-Gate-5 completion review | `ai-process/processes/quality_gates.md` |
| S-000's planning branch merges after Gate 1 | `git-conventions` skill and `ai-process/guidelines/git_conventions.md` |

Every rule that treats S-000 differently from other specs is keyed on the ID
`S-000` alone.

### CLI documentation (S-008)

- `cli/docs/usage.md` is hand-written and holds what a generator cannot produce:
  installation, `init`, workflows, the folder structure and the maintainer notes.
- `cli/docs/commands.md` is generated by `cli/scripts/gen_docs.sh` and committed, so
  it is readable without a build and the generated file can be replaced without
  touching hand-written text. The CI `lint` job fails when it is stale. The
  generator is described in [`tech_stack.md`](tech_stack.md#command-reference-generation).
- `ai-process/architecture/component_map.md` maps each skill to the `ai-team`
  commands it invokes.

### Scaffold generator (S-009)

- Each skill is one source `SKILL.md`, frontmatter followed by its body, in the form
  Claude reads. `sync_init_scaffolds.py` copies sources unchanged and never renders
  placeholders; `init` fills in the project folder and integration branch, because
  only `init` knows them.
- Alternatives that were rejected:
  - Separate scaffold files per tool, copied as is: the shared skill text drifts
    between tool formats unless every change is made twice.
  - One skill body with generated per-tool headers: used while Claude and Codex were
    both exported. After CR-007 dropped Codex, the header merge removed no
    duplication.
  - A fully structured model of agents and skills that generates every tool
    artifact: too broad, because it needs a new schema, migration rules and a review
    of every agent definition.
  - Rendering placeholders in the generator (CR-003): the project folder and
    integration branch are known only when `init` runs.
