---
title: "ai-team CLI Documentation"
version: "0.3"
status: approved
created: 2026-05-14
author: planner
id: S-008
---

# ai-team CLI Documentation

## Purpose

The `ai-team` CLI was first built under the development spec `ai-team-python-cli.md`, now superseded in `specs/archive/`. That spec described the CLI to be *built*; it never documented the CLI as it *is*. Without documentation of its own, a human installing the CLI had to reconstruct its behaviour from the README, `guides/setup-guide.md`, and `ai-team --help`, a maintainer had nothing describing its module layout or release process, and `ai-process/architecture/component-map.md` did not record how the skills use the CLI.

This specification defines the documentation of the `ai-team` CLI under `cli/docs/`, for end users (humans running `ai-team` in a consuming project) and maintainers (people developing the CLI inside this repository), and the record in `ai-process/architecture/component-map.md` of which skills invoke which CLI commands.

The expected outcome: a reader can install, initialise, and operate the CLI — and a maintainer can extend it — from `cli/docs/` alone; the command reference never drifts from the code; and the architecture layer accurately reflects the CLI's role.

## Exclusions

What this specification explicitly does NOT cover:

- **Custom documentation-generation code.** The command reference is produced by Typer's built-in `utils docs` command. `cli/scripts/gen_docs.sh` only wraps that command and adds a header; no bespoke generator is maintained.
- **A separate maintainer document.** End-user and maintainer content share `cli/docs/usage.md`; there is no distinct `architecture.md` or `contributing.md` under `cli/docs/`.
- **A hosted documentation site.** No MkDocs, Sphinx, Read the Docs, or published docs website. Documentation is plain Markdown read in-repo; a release attaches `commands.md` as a file (S-010).
- **`guides/` and `cli/README.md` as documentation homes.** The CLI documentation lives in `cli/docs/`. CLI mentions in `README.md` and `guides/setup-guide.md` stay brief pointers that link into `cli/docs/`.
- **CLI behaviour.** This is a documentation spec. It does not define any CLI command, flag, or output; those are owned by the specs that introduce them, and `cli/docs/` describes the result.
- **Re-documenting the framework process.** `cli/docs/` documents the CLI tool.
  The AI-team workflow, gates, and roles remain owned by `ai-process/` and the
  package-owned scaffold source definitions that generate exported agent and
  skill files (S-009).
- **Work-item and layout contracts.** The tracker layout is owned by S-006 and the expected project layout by S-003; `usage.md` describes them for readers but does not define them.

## Architecture

### Design Principles

1. **Docs are the source of truth for the CLI as it is.** `cli/docs/`, not the archived development spec, describes the CLI's current behaviour; the development spec stays archived as `superseded` so there are never two contradictory descriptions.
2. **Generation over transcription for the reference.** The exhaustive command/flag reference is generated from the Typer app itself, so it cannot drift from the code. Hand-written prose is reserved for things a generator cannot produce: workflows, the project folder structure, and maintainer guidance.
3. **Two files, two jobs.** `usage.md` is hand-written and explains *how to use and maintain* the CLI. `commands.md` is generated and is the *exhaustive reference*. The split keeps the generated file replaceable without touching hand-written content.
4. **Committed, not built on demand.** `commands.md` is checked into the repository so it is readable without a build step, mirroring how `cli/` commits its bundled init scaffolds.
5. **Drift is caught automatically.** Continuous integration fails when the committed `commands.md` differs from a fresh generation (S-010).
6. **The architecture layer must mention the CLI.** `ai-process/` is the specification layer; `component-map.md` therefore records the CLI as a component the skills compose with.

### System Diagram

```
  ┌──────────────────────┐         ┌───────────────────────────────┐
  │  Typer app           │  intro- │  cli/scripts/gen_docs.sh      │
  │  (ai_team.cli +      │  spect  │  wraps `typer ... utils docs` │
  │   commands/*)        │────────▶│  → writes cli/docs/commands.md│
  └──────────────────────┘         └───────────────────────────────┘
                                        │ commits        ▲ re-runs and diffs
                                        ▼                │
  ┌──────────────────────────────────────────────┐  ┌──────────────────┐
  │  cli/docs/                                   │  │ CI lint job      │
  │    usage.md    ← hand-written: install, init,│  │ (S-010): fails   │
  │                  workflows, folder structure,│  │ on any drift     │
  │                  maintainer notes            │  └──────────────────┘
  │    commands.md ← generated: every command,   │
  │                  subcommand, flag            │
  └──────────────────────────────────────────────┘
        ▲                                   ▲
        │ linked from                       │ referenced by
  ┌─────────────┐                  ┌──────────────────────────────┐
  │ README.md   │                  │ ai-process/architecture/     │
  │ setup-guide │                  │ component-map.md             │
  └─────────────┘                  │  (CLI command mapping)       │
                                   └──────────────────────────────┘
```

### Responsibility Separation

| Component | Responsibility | Notes |
|---|---|---|
| `cli/docs/usage.md` | Hand-written guide: installation, `init`, daily command workflows, the project and tracker folder structure, and a maintainer section (module map, how to add a command, test/build/release, regeneration). | Single file for both audiences. Owns everything a generator cannot produce. |
| `cli/docs/commands.md` | Generated exhaustive reference: every command group, subcommand, argument, and flag, including global flags. | Produced by Typer's built-in `utils docs`. Committed to the repo. Regenerated, never hand-edited. |
| `cli/scripts/gen_docs.sh` | Thin wrapper that runs Typer's `utils docs` against the `ai_team.cli` module and writes `cli/docs/commands.md` with a generated-file header. | Run from the repository root; an optional `--output <path>` writes elsewhere, so tests can generate without touching the tracked file (`cli/scripts/gen_docs.sh:4-12`). |
| `cli/pyproject.toml` | Declares `typer-cli` in the `dev` dependency group so `utils docs` is available. | `cli/pyproject.toml:47-52`. |
| CI drift check | Regenerates `commands.md` and fails when it differs from the committed file. | Owned by S-010; `.github/workflows/ci.yml:32-41`. |
| `ai-process/architecture/component-map.md` | Maps which skills invoke which `ai-team` commands. | Architecture layer records the CLI's role. |
| `README.md`, `guides/setup-guide.md`, `CLAUDE.md` | Brief CLI mentions that link into `cli/docs/`, and the contributor rule to regenerate `commands.md` when a command or flag changes. | Not documentation homes; just pointers and the rule. |

## Components

### Component 1: `cli/docs/usage.md` (hand-written guide)

**Purpose:** The narrative documentation a human reads to install, operate, and maintain the CLI.
**Estimated size:** Medium.
**Interfaces:** Consumes nothing programmatically. Must cover, at minimum:
- **Installation** — installing a published release and a local build (the scaffold generator plus `uv build` flow), and the Python version requirement.
- **Initialisation** — `ai-team init` and its flags (`--project-dir`, `--integration-branch`, `--create-root-guidance`, `--no-interactive`, `--dry-run`, `--force`), what gets scaffolded, and the `.ai-team.toml` marker.
- **Daily workflows** — task-oriented sequences (create-and-ship a task, file-and-resolve a bug, file a change-request, generate a Gate 5 report, validate and archive), not an exhaustive flag list.
- **Expected folder structure** — the project directory (`[project] dir`, default `ai-team`) with `specs/` (and `archive/`), `decisions/` and `docs/`; the local tracker folder (`[tracker] dir`) with its `tasks/`, `bugs/`, `change-requests/` and `archive/` folders, where state is the `status` field (S-006); the `.ai-team.toml` marker; and the locator resolution order.
- **Maintainer section** — module map, how to add a new command, how to run tests, how to build and release, and how to regenerate `commands.md`.
- A link to `commands.md` for the exhaustive reference.

### Component 2: `cli/docs/commands.md` (generated reference)

**Purpose:** The exhaustive, drift-proof reference for every command, subcommand, argument, and flag.
**Estimated size:** Small authored effort (generated content); the file itself may be large.
**Interfaces:** Produced from the Typer app via `typer-cli`'s `utils docs`. Committed to the repo. Starts with a header note stating it is generated, must not be hand-edited, and naming the regeneration command.

### Component 3: `cli/scripts/gen_docs.sh` + `typer-cli` dependency

**Purpose:** Make regeneration a single, documented command and ensure the tooling to do so is declared.
**Estimated size:** Small.
**Interfaces:** `gen_docs.sh` runs from the repository root, changes into `cli/`, and runs `utils docs` through `uv run python -m typer` against the module path `ai_team.cli` with the program name `ai-team` (`cli/scripts/gen_docs.sh:54-55`), so it does not depend on an installed console script. `typer-cli` is in the `dev` dependency group of `cli/pyproject.toml`. The contributor rule in `README.md` and `CLAUDE.md` tells maintainers to run it whenever a command or flag changes, alongside the `sync_init_scaffolds.py` rule.

### Component 4: `ai-process/architecture/component-map.md` update

**Purpose:** Record in the architecture layer where the CLI is used together with the skills.
**Estimated size:** Small.
**Interfaces:** A section mapping action skills to the `ai-team` commands they invoke (for example `new-spec` → `ai-team spec new`, `new-system-overview` → `ai-team spec new --overview`, `new-task` → `ai-team task new`, `new-bug` → `ai-team bug new`, `new-adr` → `ai-team adr new`, change-request intake → `ai-team change-request new`, `status-report` → `ai-team status` + `ai-team report`). The mapping is updated when a skill starts or stops invoking a command.

## Workflow

### Maintenance flow

```
Maintainer changes a CLI command, argument, option, or help text
  ↓
Runs cli/scripts/gen_docs.sh from the repository root
  ↓
Commits the updated cli/docs/commands.md alongside the code change
  ↓
Updates cli/docs/usage.md by hand if a workflow or the folder structure changed
  ↓
CI lint job regenerates commands.md and fails on any difference (S-010)
```

## Configuration

**Documentation tooling dependency**
- **What must exist:** `typer-cli`, which provides `utils docs`.
- **Where it lives:** the `dev` dependency group of `cli/pyproject.toml`.
- **Constraints:** installed by `uv sync` in `cli/`, as the `lint` and `test` jobs do.
- **Missing-value behaviour:** `gen_docs.sh` fails, and the CI drift check fails with it.

**Generated-file header** — **Contract** (`cli/scripts/gen_docs.sh:47-51`): `commands.md` starts with an HTML comment stating that it is a generated file that must not be edited by hand, and that it is regenerated with `bash cli/scripts/gen_docs.sh`.

## Implementation Order

All phases are delivered: the `typer-cli` dependency, `gen_docs.sh` and the committed `commands.md`; `usage.md`; the component-map CLI mapping; the archived development spec; and the README, setup-guide and contributor-rule pointers. The CI drift check was added under S-010. Later changes follow the amendment flow.

## Open Questions

None. The three questions left open at approval are answered from the repository (CR-003):

- **`utils docs` invocation:** the module path, through `uv run python -m typer ai_team.cli utils docs --name "ai-team"` run in `cli/` (`cli/scripts/gen_docs.sh:54-55`), not the installed console script.
- **Dependency group:** `typer-cli>=0.24.0` in the `dev` dependency group (`cli/pyproject.toml:47-52`).
- **CI drift check:** wired in; the CI lint job regenerates `commands.md` and fails on any difference (`.github/workflows/ci.yml:32-41`).

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-07-05 | Replaced stale repo-local `.claude/` ownership wording with package-owned scaffold source ownership. | S-004 architecture consistency review found the archived documentation spec contradicted the approved scaffold ownership model. | none |
| 2026-10-20 | Moved out of `specs/archive/` as S-008 (it had no ID). Removed the delivered Component 5 (archive the development spec) and the one-time authoring flow; replaced `--include-ai-process` with the current `init` flags; replaced the folder-based `tasks/`/`bugs/` structure with the project directory plus the S-006 tracker; added the CI drift check (S-010) as a design principle; resolved the three open questions from `cli/scripts/gen_docs.sh`, `cli/pyproject.toml` and `.github/workflows/ci.yml`; the TOML example became prose. Driven by CR-003 §10 and Architecture Consistency Review finding F4. | The spec was still `approved` in the archive and the only written contract for `cli/docs/`, but described a removed flag, the pre-S-006 folder structure and completed work. | None in flight |
| 2026-10-25 | Initialisation no longer lists `--tools`. Driven by CR-007. | `init` has no tool selection (S-009, ADR-003). | None in flight |
