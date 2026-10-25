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

This spec covers the CLI's part of the S-000 **End-user documentation** component and
the CLI command mapping in the architecture layer. The CLI was built under a
development spec, now superseded in `specs/archive/`, that described the CLI to be
built rather than the CLI as it is, so users had to piece its behaviour together from
the README, `guides/setup-guide.md` and `ai-team --help`, and maintainers had nothing
on its module layout or release process. A reader can install, initialise and operate
the CLI, and a maintainer can extend it, from `cli/docs/` alone; the command reference
never drifts from the code; and `ai-process/architecture/component-map.md` records
which skills invoke which CLI commands.

## Users and Journeys

| Actor | Goal | Priority | Outcome | Requirements |
|---|---|---|---|---|
| End user running `ai-team` in a consuming project | Install, initialise and use the CLI without reading its source | P1 | `cli/docs/usage.md` walks them from installation through daily workflows, and `cli/docs/commands.md` answers any flag question | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007 |
| Maintainer developing the CLI in this repository | Find the module layout, add a command, test, build, release and keep the reference current | P1 | The maintainer section and one regeneration command cover each step | REQ-005, REQ-008, REQ-009, REQ-012 |
| Reader of the architecture layer (human or agent) | Learn which skills use which CLI commands | P2 | `component-map.md` maps each action skill to its commands | REQ-010 |
| Newcomer starting from the README or setup guide | Reach the CLI documentation | P2 | Both link to `cli/docs/` | REQ-011 |

## Exclusions

What this specification explicitly does NOT cover:

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
2. **Generation over transcription for the reference.** The exhaustive command and flag reference must come from the CLI's own command definitions, so it cannot drift from the code (REQ-007). Hand-written prose is reserved for things a generator cannot produce: workflows, the project folder structure, and maintainer guidance.
3. **Two files, two jobs.** `usage.md` is hand-written and explains *how to use and maintain* the CLI. `commands.md` is generated and is the *exhaustive reference*. The split keeps the generated file replaceable without touching hand-written content.
4. **Committed, not built on demand.** `commands.md` is checked into the repository so it is readable without a build step, mirroring how `cli/` commits its bundled init scaffolds (REQ-007).
5. **Drift is caught automatically.** Continuous integration fails when the committed `commands.md` differs from a fresh generation (S-010).
6. **The architecture layer must mention the CLI.** `ai-process/` is the specification layer; `component-map.md` therefore records the CLI as a component the skills compose with (REQ-010).

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
| `cli/docs/usage.md` | Hand-written guide: installation, `init`, daily command workflows, the project and tracker folder structure, and a maintainer section. | Single file for both audiences. Owns everything a generator cannot produce. |
| `cli/docs/commands.md` | Generated exhaustive reference: every command group, subcommand, argument, and flag, including global flags. | Committed to the repo. Regenerated, never hand-edited. |
| `cli/scripts/gen_docs.sh` | Thin wrapper that generates `cli/docs/commands.md` with a generated-file header. | The one regeneration command. |
| CI drift check | Regenerates `commands.md` and fails when it differs from the committed file. | Owned by S-010. |
| `ai-process/architecture/component-map.md` | Maps which skills invoke which `ai-team` commands. | Architecture layer records the CLI's role. |
| `README.md`, `guides/setup-guide.md`, `CLAUDE.md` | Brief CLI mentions that link into `cli/docs/`, and the contributor rule to regenerate `commands.md` when a command or flag changes. | Not documentation homes; just pointers and the rule. |

### Alternatives Considered

- **A custom documentation generator.** Rejected to avoid maintaining generation code.
  The reference comes from Typer's built-in `utils docs` command, and
  `cli/scripts/gen_docs.sh` only wraps it and adds a header.
- **Running `utils docs` through the installed `ai-team` console script.** Rejected
  in favour of the module path `ai_team.cli`, so generation does not depend on an
  installed console script (CR-003).

## Interfaces

**Exposed — `cli/docs/usage.md` (REQ-001–REQ-006).** A hand-written Markdown guide
with sections for installation, initialisation, daily workflows, the project folder
structure and maintainers, linking to `commands.md`.

**Exposed — `cli/docs/commands.md` (REQ-007, REQ-008).** A committed Markdown file
holding Typer's generated reference for the `ai-team` program, preceded by this
header. **Contract:**

```
<!-- GENERATED FILE — do not edit by hand.
     Regenerate with: bash cli/scripts/gen_docs.sh -->
```

**Exposed — `cli/scripts/gen_docs.sh` (REQ-009).**
- Invocation: `bash cli/scripts/gen_docs.sh [--output <path>]`, from any working
  directory.
- Default output: `cli/docs/commands.md` in the repository.
- `--output <path>` writes elsewhere; a relative path resolves against the caller's
  working directory, and missing parent folders are created.
- Errors: an unknown argument, or `--output` without a path, prints an error and a
  usage line to standard error and exits with status 2. A generation failure exits
  non-zero.

**Exposed — `ai-process/architecture/component-map.md` (REQ-010).** A table mapping
each action skill to the `ai-team` commands it invokes.

**Consumed.**
- The Typer app at the module path `ai_team.cli`, whose commands and help text are
  the reference's source.
- `typer-cli`'s `utils docs` command (see Configuration Requirements).

## Workflow

```
Maintainer changes a CLI command, argument, option, or help text
  ↓
Runs bash cli/scripts/gen_docs.sh from the repository root              (REQ-009)
  ↓
Commits the updated cli/docs/commands.md alongside the code change      (REQ-007)
  ↓
Updates cli/docs/usage.md by hand if a workflow or the folder structure changed
  ↓
Updates component-map.md if a skill starts or stops invoking a command  (REQ-010)
  ↓
CI lint job regenerates commands.md and fails on any difference (S-010)
```

Failure paths: if the maintainer forgets to regenerate, the CI drift check fails and
names the command to run (S-010). If `gen_docs.sh` gets a bad argument it exits 2
without touching any file (REQ-009). If `typer-cli` is not installed, generation
fails (see Configuration Requirements).

## Behavioral Requirements

### REQ-001 — Installation

`usage.md` SHALL explain how to install a published release and a local build, and
SHALL state the required Python version.

#### AC-001.1 — Installation section

- **Given:** `cli/docs/usage.md`
- **When:** a reader opens its Installation section
- **Then:** it describes installing from GitHub Releases, building and installing
  locally with the scaffold generator and `uv build`, and the requirement of Python
  3.14 or later

**Verification:** Inspection of the Installation section; the smoke test
`test_usage_md_covers_installation` in `cli/tests/test_usage_guide.py` only checks that
the section exists.

### REQ-002 — Initialisation

`usage.md` SHALL document `ai-team init`: its flags, what it scaffolds, and the
`.ai-team.toml` marker.

#### AC-002.1 — Init section

- **Given:** `cli/docs/usage.md`
- **When:** a reader opens its Initialisation section
- **Then:** it lists every `init` flag that `commands.md` lists, describes the files
  `init` creates, and explains the `.ai-team.toml` marker

**Verification:** Inspection: compare the flags in the Initialisation section with
the `init` entry of `commands.md`. Smoke tests: `test_usage_md_covers_init_command`,
`test_usage_md_describes_ai_team_toml_marker` and
`test_usage_md_does_not_mention_nonexistent_flags` in
`cli/tests/test_usage_guide.py`.

### REQ-003 — Daily workflows

`usage.md` SHALL describe task-oriented command sequences: create and ship a task,
file and resolve a bug, file a change request, generate a Gate 5 report, and validate
and archive artifacts.

#### AC-003.1 — Workflow sections

- **Given:** `cli/docs/usage.md`
- **When:** a reader opens Daily Workflows
- **Then:** each of the five sequences has its own section, and every command it
  names exists in `commands.md`

**Verification:** Inspection: each sequence has a section, and each command it names
appears in `commands.md`. Smoke tests: `test_usage_md_covers_daily_workflows` and
`test_usage_md_covers_gate5_report_workflow` in `cli/tests/test_usage_guide.py`.

### REQ-004 — Folder structure

`usage.md` SHALL describe the project folder (`[project] dir`, default `ai-team`) with
`specs/` and its `archive/`, `decisions/` and `docs/`; the local tracker folder
(`[tracker] dir`) with `tasks/`, `bugs/`, `change-requests/` and `archive/`, where
state is the `status` field (S-006); the `.ai-team.toml` marker; and the locator
resolution order.

#### AC-004.1 — Folder structure section

- **Given:** `cli/docs/usage.md`
- **When:** a reader opens Project Folder Structure
- **Then:** it names each folder above, the marker, and the order in which the CLI
  looks for the project

**Verification:** Inspection of the Project Folder Structure section. The marker and
locator are also checked by `test_usage_md_describes_ai_team_toml_marker` and
`test_usage_md_describes_locator_resolution_order` in `cli/tests/test_usage_guide.py`;
no test checks the tracker folders.

### REQ-005 — Maintainer section

`usage.md` SHALL have a maintainer section covering the module map, how to add a
command, how to run the tests, how to build and release, and how to regenerate
`commands.md`.

#### AC-005.1 — Maintainer topics

- **Given:** `cli/docs/usage.md`
- **When:** a maintainer opens For Maintainers
- **Then:** each of the five topics is covered, including the `--output` option of
  `gen_docs.sh`

**Verification:** Tests: `test_usage_md_has_maintainer_section`,
`test_usage_md_has_module_map`, `test_usage_md_explains_how_to_add_a_command`,
`test_usage_md_explains_how_to_run_tests`,
`test_usage_md_explains_how_to_build_and_release`,
`test_usage_md_explains_how_to_regenerate_commands_md` and
`test_usage_md_documents_gen_docs_output_option` in `cli/tests/test_usage_guide.py`.

### REQ-006 — Link to the reference

`usage.md` SHALL link to `commands.md` for the exhaustive reference.

#### AC-006.1 — Link present

- **Given:** `cli/docs/usage.md`
- **When:** its links are read
- **Then:** one points to `commands.md`

**Verification:** Test: `test_usage_md_links_to_commands_md` in
`cli/tests/test_usage_guide.py`.

### REQ-007 — Generated, committed reference

`cli/docs/commands.md` SHALL be committed to the repository and SHALL equal the output
of `gen_docs.sh` for the committed code, covering every command group, subcommand,
argument and flag, including the global flags.

#### AC-007.1 — Committed file matches generation

- **Given:** a clean checkout
- **When:** `gen_docs.sh --output <temp file>` runs
- **Then:** the temp file is byte-identical to `cli/docs/commands.md`

**Verification:** Test: `test_committed_commands_md_matches_generated_output` in
`cli/tests/test_gen_docs.py`; CI drift check (S-010).

#### AC-007.2 — Commands and global flags present

- **Given:** `cli/docs/commands.md`
- **When:** it is searched for each top-level command and for `--version` and
  `--help`
- **Then:** each is found

**Verification:** Test: `test_committed_commands_md_matches_generated_output` in
`cli/tests/test_gen_docs.py`, since the generated reference covers every command. Smoke
tests: `test_commands_md_contains_key_command`, `test_commands_md_contains_global_flags`
and `test_generated_commands_md_contains_check_layout_command`.

### REQ-008 — Generated-file header

`commands.md` SHALL start with the header defined in Interfaces, stating that it is
generated, must not be edited by hand, and is regenerated with
`bash cli/scripts/gen_docs.sh`.

#### AC-008.1 — Header present

- **Given:** `cli/docs/commands.md`
- **When:** its first lines are read
- **Then:** they are the header from Interfaces

**Verification:** Tests: `test_commands_md_has_generated_header_note` and
`test_commands_md_header_names_regeneration_command` in `cli/tests/test_gen_docs.py`.

### REQ-009 — Regeneration command

`gen_docs.sh` SHALL regenerate the reference with one command, SHALL write
`cli/docs/commands.md` by default, SHALL write to `--output <path>` when given, and
SHALL reject invalid arguments as defined in Interfaces.

#### AC-009.1 — Default output

- **Given:** a checkout with the `dev` dependencies installed
- **When:** `bash cli/scripts/gen_docs.sh` runs from the repository root
- **Then:** `cli/docs/commands.md` is rewritten

**Verification:** Demonstration: run the script from the repository root and see
`cli/docs/commands.md` rewritten. `test_gen_docs_default_output_path_is_committed_commands_md`
in `cli/tests/test_gen_docs.py` checks the default path in the script.

#### AC-009.2 — Relative output path

- **Given:** a working directory other than the repository root
- **When:** `gen_docs.sh --output relative.md` runs there
- **Then:** `relative.md` is created in that working directory

**Verification:** Test: `test_gen_docs_resolves_relative_output_against_caller_cwd`
in `cli/tests/test_gen_docs.py`.

#### AC-009.3 — Invalid arguments

- **Given:** a checkout
- **When:** `gen_docs.sh --bogus` or `gen_docs.sh --output` runs
- **Then:** it exits non-zero and prints a usage line to standard error

**Verification:** Test: `test_gen_docs_rejects_invalid_arguments` in
`cli/tests/test_gen_docs.py`.

### REQ-010 — CLI command mapping

`ai-process/architecture/component-map.md` SHALL map each action skill to the
`ai-team` commands it invokes, and the mapping SHALL be updated when a skill starts or
stops invoking a command.

#### AC-010.1 — Mapping rows

- **Given:** `component-map.md`
- **When:** its CLI mapping is read
- **Then:** it maps `new-spec` to `ai-team spec new`, `new-system-overview` to
  `ai-team spec new --overview`, `new-task` to `ai-team task new`, `new-bug` to
  `ai-team bug new`, `new-adr` to `ai-team adr new`, change-request intake to
  `ai-team change-request new`, and `status-report` to `ai-team status` and
  `ai-team report`

**Verification:** Inspection of `ai-process/architecture/component-map.md`.

### REQ-011 — Pointers and contributor rule

`README.md` and `guides/setup-guide.md` SHALL link to `cli/docs/usage.md` and
`cli/docs/commands.md` rather than document the CLI themselves, and `README.md` and
`CLAUDE.md` SHALL tell contributors to run `gen_docs.sh` and commit the result when a
command or flag changes.

#### AC-011.1 — Links and rule present

- **Given:** `README.md`, `guides/setup-guide.md` and `CLAUDE.md`
- **When:** they are searched for `cli/docs/` and `gen_docs.sh`
- **Then:** the README and setup guide link to both files, and the README and
  `CLAUDE.md` state the regeneration rule

**Verification:** Inspection of the three files.

## Quality Requirements

### REQ-012 — Deterministic generation

Running `gen_docs.sh` twice on the same code SHALL produce identical output, so the
drift check fails only on real changes.

#### AC-012.1 — Two runs match

- **Given:** a checkout
- **When:** `gen_docs.sh --output` runs twice to two files
- **Then:** the files are identical

**Verification:** Test: `test_gen_docs_is_idempotent` in `cli/tests/test_gen_docs.py`.

Security, privacy, accessibility and performance requirements do not apply: the
documentation is static Markdown in the repository, holds no secrets or personal
data, and no generation-time target was agreed.

## Configuration Requirements

**Documentation tooling dependency** (REQ-009)
- **What must exist:** `typer-cli`, which provides `utils docs`.
- **Where it lives:** the `dev` dependency group of `cli/pyproject.toml`.
- **Constraints:** installed by `uv sync` in `cli/`, as the `lint` and `test` jobs do.
- **Missing-value behaviour:** `gen_docs.sh` fails, and the CI drift check fails with it.

## Assumptions and Dependencies

- **Typer's `utils docs` output is deterministic** for unchanged code. Confirmed by
  REQ-012's test. If a `typer-cli` upgrade changes its output format, the drift check
  fails until `commands.md` is regenerated.
- **`uv` is available** to run the generator; `gen_docs.sh` runs it through
  `uv run python -m typer`.
- **S-010's CI drift check** enforces REQ-007 on every pull request. Without it, drift
  is caught only by the local test suite.
- **The specs that define each command** (S-003, S-006, S-007, S-009 and others) own
  the behaviour `usage.md` describes; when they change, `usage.md` follows.

## Success Criteria

1. Every pull request whose committed `commands.md` differs from a fresh generation
   fails CI (REQ-007, REQ-012).
2. `cli/tests/test_usage_guide.py` and `cli/tests/test_gen_docs.py` pass, covering
   each required `usage.md` topic, the reference, its header and the generator
   (REQ-001–REQ-009, REQ-012).
3. Inspection finds every command `usage.md` names in `commands.md`, and
   `test_usage_md_does_not_mention_nonexistent_flags` passes (REQ-002, REQ-003).
4. Each action skill that invokes a CLI command has a row in `component-map.md`
   (REQ-010).

## Implementation Order

All phases are delivered: the `typer-cli` dependency, `gen_docs.sh` and the committed `commands.md`; `usage.md`; the component-map CLI mapping; the archived development spec; and the README, setup-guide and contributor-rule pointers. The CI drift check was added under S-010. Later changes follow the amendment flow.

## Open Questions

None. The three questions left open at approval are answered from the repository
(CR-003): the `utils docs` invocation uses the module path (Alternatives Considered);
`typer-cli` is in the `dev` dependency group (Configuration Requirements); and the CI
drift check is wired in (S-010).

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-07-05 | Replaced stale repo-local `.claude/` ownership wording with package-owned scaffold source ownership. | S-004 architecture consistency review found the archived documentation spec contradicted the approved scaffold ownership model. | none |
| 2026-10-20 | Moved out of `specs/archive/` as S-008 (it had no ID). Removed the delivered Component 5 (archive the development spec) and the one-time authoring flow; replaced `--include-ai-process` with the current `init` flags; replaced the folder-based `tasks/`/`bugs/` structure with the project directory plus the S-006 tracker; added the CI drift check (S-010) as a design principle; resolved the three open questions from `cli/scripts/gen_docs.sh`, `cli/pyproject.toml` and `.github/workflows/ci.yml`; the TOML example became prose. Driven by CR-003 §10 and Architecture Consistency Review finding F4. | The spec was still `approved` in the archive and the only written contract for `cli/docs/`, but described a removed flag, the pre-S-006 folder structure and completed work. | None in flight |
| 2026-10-25 | Initialisation no longer lists `--tools`. Driven by CR-007. | `init` has no tool selection (S-009, ADR-003). | None in flight |
| 2026-10-25 | Restructured to the spec format from PR #51: added Users and Journeys, Alternatives Considered (the custom generator, moved from Exclusions, and the console-script invocation), Interfaces, Behavioral Requirements REQ-001–REQ-011 with acceptance scenarios, Quality Requirements REQ-012, Assumptions and Dependencies, and Success Criteria; the Components section was split into Interfaces and requirements, the `init` flag list was replaced by a link to `commands.md`, and source line references were dropped. Format restructure only, no scope change, so the version is unchanged. | The validator now rejects approved specs without the new sections. | None |
