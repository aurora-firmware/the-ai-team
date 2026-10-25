---
title: CLI-owned framework scaffolds
version: '0.6'
status: approved  # draft | review | approved | superseded
created: '2026-05-14'
author: planner
id: S-009
---

# CLI-owned framework scaffolds

## Purpose

The framework once had several product copies of its agent and skill definitions: the
repository-root tool folders such as `.claude/`, and the bundled init scaffolds inside
the `ai-team` CLI package, plus an `ai-process/` snapshot that `ai-team init` could
export. Copies drift, and the process layer must stay the authoritative documentation
in this repository.

This specification makes the CLI package the only product source of truth for exported
framework definitions. A maintainer edits package-owned sources, a generator produces
the bundled Claude scaffolds from them, and `ai-team init` writes those
scaffolds into a consuming project, filling in the project's settings. Repository-root
tool folders are ordinary local configuration for working on this repository, and
`ai-process/` is never exported.

The expected outcome: every agent, skill and skill supporting file a consuming project
receives comes from `cli/src/ai_team/init/sources/`, each skill is authored once as the
`SKILL.md` Claude reads, and the committed scaffolds always equal a fresh generation from
the sources. Claude is the only export target (CR-007, ADR-003).

## Exclusions

What this specification explicitly does NOT cover:

- **Exporting `ai-process/` by any route.** `init` does not copy it, and there is no
  `ai-team export ai-process` command.
- **Generating agents from a structured schema.** Agent definitions remain hand-written
  package-owned Markdown assets. A future spec may define a richer canonical model for
  generating agents.
- **Other agent tools.** Claude is the only export target. There is no tool selection and
  no compatibility with projects set up for Codex (CR-007, ADR-003).
- **Changing workflow semantics.** The AI-team process, gates, role responsibilities,
  escalation chain, and work-item lifecycle are owned elsewhere and are unchanged here.
- **Making repository-root tool folders such as `.claude/` generated.** Those
  folders remain local configuration for this repository. They are not symlinked,
  generated, or read as product sources.
- **Filling placeholders when the scaffolds are generated.** `{{project_dir}}` and
  `{{integration_branch}}` take values from the `init` flags or `.ai-team.toml`, which
  are not known at generation time. Only `init` fills them in (CR-003).
- **Exporting arbitrary files from a skill source directory.** Only `SKILL.md` and
  the `assets/`, `references/` and `scripts/` folders are used; any other file in a
  source skill directory is not exported (CR-003, CR-007).
- **The export paths and the layout check.** The agent and skill destination folders are
  owned by S-003 (level 1 of the layout check) and the tracker by S-006. This spec
  refers to them rather than restating them.

## Architecture

### Design Principles

1. **CLI package owns exported framework assets.** Anything `ai-team init` writes into a
   consuming project comes from package-owned data under `cli/src/ai_team/init/`.
2. **Root tool folders are local configuration.** Repository-root tool folders such as
   `.claude/` are for developing this repository, not for shipping the framework, and no
   source or generator reads them.
3. **One file per skill.** Each skill is authored once as a source `SKILL.md`, its
   frontmatter followed by its procedural body, in the form Claude reads. The generator
   copies it unchanged; there is no header merge (CR-007).
4. **Generated output is reproducible.** The committed scaffolds must equal a fresh run
   of the generator over the committed sources; a source change and its regenerated
   output are committed together.
5. **Project settings are filled in at init time.** Generated scaffolds keep their
   placeholders; `init` is the only step that knows the project's settings.
6. **No process duplication.** `ai-process/` remains the specification layer in this
   repository and is not bundled into the CLI init scaffolds.
7. **Documentation follows ownership.** README, guides, CLI docs, and architecture docs
   describe the package-owned scaffolding model and name the generator, not root tool
   folders, as the way exported definitions change.

### System Diagram

```
Repository root (development workspace)
  .claude/ (and other tool folders)  local tool config only, never read by the generator
  ai-process/                authoritative process specification, not exported
  cli/
    scripts/sync_init_scaffolds.py   generator
    src/ai_team/init/
      sources/                       maintainers edit here
        skills/<name>/SKILL.md, [assets/ references/ scripts/]
        agents/*.md
        project/         project AGENTS.md and .gitignore
        root/            root AGENTS.md template
      scaffolds/                     generated, committed, read by init
        project/   agents/   skills/

ai-team init
  renders placeholders while copying package scaffolds
  writes the project directory, the tool export paths (S-003 level 1),
  the tracker folder (S-006) and .ai-team.toml
  never writes ai-process/
```

### Responsibility Separation

| Component | Responsibility | Notes |
|---|---|---|
| `cli/src/ai_team/init/sources/` | Canonical package-owned source assets for exported framework definitions. | Skill `SKILL.md` files, skill supporting folders, agents, project and root `AGENTS.md` templates. |
| Scaffold generator | Produces the bundled scaffolds from the sources. | `cli/scripts/sync_init_scaffolds.py`; copies, never renders placeholders. |
| `cli/src/ai_team/init/scaffolds/` | Generated package data consumed by `ai-team init`. | Contains `project/`, `agents/`, and `skills/`; never contains `ai-process/`. Do not edit by hand. |
| `ai-team init` | Writes the agent and skill scaffolds and the project skeleton into a target repository, filling in the project's settings. | Export paths per S-003 level 1; tracker per S-006. |
| Tests | Enforce that the scaffolds match a fresh generation, that supporting folders reach the export, and the `init` contract. | Prevent drift and CLI contract regression. |
| Documentation | Explains the source-of-truth boundary and the generator. | README, setup and skill-authoring guides, `cli/docs/`. |

## Components

### Component 1: Package-Owned Scaffold Sources

**Purpose:** Hold every exported framework asset inside the CLI package so the CLI owns
what it ships.
**Estimated size:** Medium (delivered).
**Interfaces:** Provides skill `SKILL.md` files and skill supporting folders to the
generator; agents and the project skeleton files to the generator; the root guidance
template to `init`. The source tree must not read from repository-root tool folders such
as `.claude/`, or from `ai-process/`.

Ownership rules:

- each skill is stored once, as a source `SKILL.md` holding its frontmatter and body;
- a skill may carry `assets/`, `references/` and `scripts/` folders next to its
  `SKILL.md` (CR-003);
- agent definitions are package-owned Markdown assets;
- source text may name the project's settings only through the `{{project_dir}}` and
  `{{integration_branch}}` placeholders.

### Component 2: Skill Scaffold Generation

**Purpose:** Generate the bundled scaffolds from the package-owned sources.
**Estimated size:** Medium (delivered); small for the CR-003 supporting-folder change.
**Interfaces:** Consumes `cli/src/ai_team/init/sources/`; writes
`cli/src/ai_team/init/scaffolds/`. Run by maintainers before committing a source change
and before building the package.

Required behaviour:

- Each source skill's `SKILL.md` is copied unchanged into the skill scaffold. A skill
  without a `SKILL.md` stops the generator with an error naming the skill (CR-007).
- A source skill's `assets/`, `references/` and `scripts/` folders, when present, are
  copied next to its `SKILL.md`, byte for byte (CR-003). No other file in a source skill
  directory is exported.
- Agent definitions are copied as real files, never symlinks.
- The project skeleton holds the `specs/`, `decisions/` and `docs/` folders, each kept
  with an empty placeholder file, plus the project guidance files and `.gitignore` from
  the sources. The `docs/` folder also holds a `coding_guidelines.md` placeholder, which
  the Developer agent and the skills already point to and the project bootstrap fills
  in (S-007 requirement 12; CR-004). It holds no task, bug or change-request folders; those work items live
  in the tracker (S-006).
- The generator copies every file without filling in placeholders.
- Each run replaces the generated output completely, so a removed source leaves no
  stale scaffold, and it never modifies the sources. Argument parsing (`--help`, an
  unknown argument) never reaches the regeneration.

### Component 3: Init Command Contract

**Purpose:** Keep `ai-team init` as the way to scaffold consuming repositories from the
package scaffolds.
**Estimated size:** Small to medium (delivered); small for the CR-003 binary-copy change.
**Interfaces:** `ai-team init`, its command docs, and tests.

Required behaviour:

- `init` always writes the agents and skills; there is no `--tools` option and no
  tool selection (CR-007). `--tools` is rejected as an unknown option.
- The agents and skills are written to the export paths listed in S-003's level 1, as
  real files and directories, not symlinks. Skill supporting folders are written with
  their skill.
- The project skeleton is written to the configured project directory (`[project] dir`,
  `--project-dir`, default `ai-team`). The tracker folder and its ignore rule follow
  S-006.
- **Placeholder rendering (CR-003).** Every scaffold file `init` writes — generated
  skills, skill supporting files, agents and project guidance — has `{{project_dir}}`
  and `{{integration_branch}}` replaced with the values from the `init` flags or
  `.ai-team.toml`, with the defaults `ai-team` and `dev-agent`.
- **Binary files (CR-003).** A scaffold file that does not decode as UTF-8 is copied
  byte for byte, without filling in placeholders, instead of failing.
- `.ai-team.toml` records the `[project] dir`, `[tracker] dir`,
  `[git] integration_branch`, and `[init] framework_version`. `init` never reads or
  writes `[init] tools`; a leftover value is an unread key (CR-007). On a repository
  that already has `.ai-team.toml`, the configured project directory and integration
  branch are kept unless the matching `init` flag (`--project-dir`,
  `--integration-branch`) is given, the configured tracker folder is always kept
  (`[tracker] dir` has no `init` flag), and every other setting the user added is
  preserved.
- **Project state (CR-005).** Before writing anything, `init` detects one of three
  cases from the target repository:
  - **Upgrade** — `.ai-team.toml` exists and records `[init] framework_version`. A missing project directory, and any
    missing project-skeleton file that no upgrade question covers (the `specs/` and
    `decisions/` placeholders and `docs/coding_guidelines.md`), is written without a
    question and reported as `WROTE`; an existing one is never overwritten.
  - **New project** — no `.ai-team.toml` that records `[init] framework_version`, and none of the
    files `init` would write
    exist yet.
  - **Adoption** — no `.ai-team.toml` that records `[init] framework_version`, but some files `init`
    would write already exist.
  - A `.ai-team.toml` the user wrote by hand to preset settings, without `[init] framework_version`,
    is a first run: its settings are kept and the case is a new project or an adoption.
- **Upgrade.** Every setting in `.ai-team.toml` is kept, except where `--project-dir`
  or `--integration-branch` is given explicitly. `init` asks two questions, in
  this order (a question that covers no files is not asked): update the ai-team docs (`AGENTS.md` and `.gitignore` in the
  project directory), then update the agents and skills.
  `--update-docs` and `--update-skills` answer them ahead of time; `--update-skills`
  covers agents and skills. With `--no-interactive`, an unanswered question means
  "no" and that part is left unchanged. When the agents and skills are updated,
  `framework_version` is set to the running version. Skills and agents in the export
  folders that the running version does not ship are never removed; `init` lists them
  in a warning that says they were neither updated nor removed. Root guidance is
  offered as for a new project.
- **New project.** Everything is written, then root guidance is offered, as before.
- **Adoption.** `.ai-team.toml`, the project directory, and the agents and skills are
  written. The existing agent, skill and project-skeleton files `init` would write are
  listed together and asked about once; `--force` answers yes. Root guidance and an
  existing `docs/coding_guidelines.md` are not part of that question. Whenever the question is not answered
  yes (an interactive no, or `--no-interactive` without `--force`), they are kept and
  reported on stderr. Root guidance is offered as for a new project.
- **No Codex compatibility.** `init` never reads, migrates or removes Codex files a
  project already has (`.codex/`, `.agents/skills/`) and prints no note about them
  (CR-007).
- `--force` answers yes to every overwrite question. Without it, an existing file is
  replaced only on a yes. `--dry-run` reports the detected case, then what the real run
  with the same flags would write, without writing. An unanswered question prints
  `WOULD PROMPT: <path>` for each file it covers. What a yes would trigger (the
  stale-definition warning, the `framework_version` bump) is reported only
  when a flag, `--force` or `--no-interactive` answers the question.
- **Reporting.** In every case, each file the real run creates is reported on stdout as
  `WROTE: <path>` and each existing file it replaces as `OVERWROTE: <path>`, so the real
  run reports the same files its dry run lists as `WOULD WRITE` and `WOULD OVERWRITE`.
  This covers skeleton files, files written on a
  yes to an upgrade question, root guidance and `.ai-team.toml`. The tracker folder and
  the root `.gitignore` rule (S-006) are reported as `CREATED: <path>` or
  `UPDATED: <path>`, matching the dry run's `WOULD CREATE` and `WOULD UPDATE`; adding the
  rule is reported as `UPDATED` even when it creates the root `.gitignore`. Only an
  adoption lists kept files, on stderr: the existing files its question kept. Kept root
  guidance and an existing `docs/coding_guidelines.md` are never listed, and an upgrade
  lists no kept files.
- `docs/coding_guidelines.md` in the project directory is written only when it is
  missing. An existing file is never overwritten, even with `--force`, and does not
  count as a collision, so a framework upgrade keeps the project's own guidelines
  (CR-004 item 10).
- `init` never writes `ai-process/`, accepts no `--include-ai-process` option, and asks
  no question about it.

### Component 4: Documentation

**Purpose:** Keep the product/source boundary consistent everywhere it is described.
**Estimated size:** Small.
**Interfaces:** README, `guides/setup-guide.md`, `guides/skill_template.md`, `cli/docs/`,
and `ai-process/` architecture docs.

Documentation must state:

- `ai-process/` is the authoritative process specification in this repository and is
  not exported by `ai-team init`.
- CLI package scaffold sources are the product source for exported agents and skills,
  and the generator is how the bundled scaffolds change.
- Repository-root tool folders are local configuration for this repository, not the
  product source.
- For skill authors (`guides/skill_template.md`): which files of a source skill
  directory are exported, that supporting folders reach the export, and that
  placeholders in them are filled in by `init`, except in files that are not UTF-8
  text (CR-003).

## Workflow

### Maintainer Asset Flow

```
Edit a package-owned source asset
  ↓
Run the scaffold generator
  ↓
Generated scaffolds update under cli/src/ai_team/init/scaffolds/
  ↓
Run the tests (scaffolds match a fresh generation; shared bodies; init behaviour)
  ↓
Commit the source change, the generated output, and test/doc updates together
```

### Consumer Init Flow

```
ai-team init . --no-interactive
  ↓
Writes the project skeleton to the configured project directory
  ↓
Writes the agents and skills to the S-003 export paths,
filling in placeholders (non-UTF-8 files copied byte for byte)
  ↓
Writes or refreshes .ai-team.toml, keeping existing settings
  ↓
Creates the tracker folder and its ignore rule (S-006)
  ↓
Never writes ai-process/
```

## Configuration

**Scaffold placeholders**
- **What must exist:** the `{{project_dir}}` and `{{integration_branch}}` placeholders
  are the only way a source asset names the project's settings.
- **Where it lives:** in the package-owned source files; values come from the `init`
  flags or `.ai-team.toml`.
- **Constraints:** the generator leaves them unchanged; `init` fills them in every UTF-8
  scaffold file it writes.
- **Missing-value behaviour:** with no flag and no configured value, `init` uses
  `ai-team` and `dev-agent`.

**Skill source file**
- **What must exist:** a `SKILL.md` per source skill, with its frontmatter and body.
- **Where it lives:** `cli/src/ai_team/init/sources/skills/<name>/SKILL.md`.
- **Constraints:** must not require reading repository-root tool folders.
- **Missing-value behaviour:** the generator stops with an error naming the skill.

## Alternatives Considered

### Direct Package Copies

Keep separate Claude and Codex scaffold files directly under the CLI package and copy
them as-is. This is simpler, but it permits the shared skill body text to drift between
tool formats unless every change is manually duplicated or heavily tested.

### Shared Skill Body With Generated Tool Scaffolds

Store each skill body once and generate Claude/Codex skill files with tool-specific
metadata. This was the chosen direction while two tools were exported. CR-007 dropped
Codex, so the header merge no longer removes any duplication; each skill is now one
source `SKILL.md` copied as is.

### Fully Structured Framework Model

Model agents and skills as structured data and generate every tool artifact from that
schema. This is cleaner long-term but too broad for this change; it would require a new
schema, migration rules, and broader review of all agent definitions.

### Rendering Placeholders in the Generator (CR-003)

Fill in placeholders when the scaffolds are generated. Rejected: the project directory
and integration branch are only known when `init` runs in a consuming project.

## Implementation Order

The original phases (package-owned sources, the generator, bundled scaffolds without
`ai-process/`, the `init` contract, tests, and documentation) are delivered. The CR-003
amendment adds:

| Phase | What | Depends On |
|---|---|---|
| 1 | The generator copies skill supporting folders into both exports, with a fixture-skill test. | Nothing |
| 2 | `init` copies non-UTF-8 scaffold files byte for byte, with a test. | Nothing |
| 3 | `guides/skill_template.md` states the export and placeholder rules. | Phases 1-2 |

The CR-007 amendment adds:

| Phase | What | Depends On |
|---|---|---|
| 1 | Merge each skill's `metadata.toml` `[claude]` header and `body.md` into one source `SKILL.md`; flatten sources and scaffolds; drop the Codex sources and the generator's per-tool branch. | Nothing |
| 2 | `init` drops `--tools`, `[init] tools`, Codex handling and `CLAUDE.md`, and detects the project state from `[init] framework_version`. | Phase 1 |
| 3 | Tests, guides and CLI docs follow; scaffolds and `commands.md` are regenerated. | Phases 1-2 |

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-20 | Moved out of `specs/archive/` as S-009 (was a duplicate `S-001`) and retitled from "CLI-owned framework scaffolds and remove ai-process init export". Removed the completed `ai-process/` export removal as a work item, keeping "never exports `ai-process/`" as an invariant. Component 2 now copies skill `assets/`, `references/` and `scripts/` folders into both exports byte for byte, and the generator never fills placeholders; Component 3 states placeholder rendering by `init` and byte-for-byte copy of non-UTF-8 files. The project skeleton no longer has lifecycle folders (S-006); export paths now refer to S-003's level 1 table instead of naming `.codex/skills/`; the `.ai-team.toml` contract includes `[tracker] dir` and `[git] integration_branch`; the TOML example became prose. Driven by CR-003 §7 and §10 and Architecture Consistency Review finding F3. | The spec was still `approved` in the archive and the only written contract for the generator, but described a lifecycle skeleton and `.codex/skills/` export that S-006 and CR-002 replaced, and the generator silently dropped skill supporting folders (report #20). | None in flight |
| 2026-10-24 | Project skeleton: `docs/` holds a `coding_guidelines.md` placeholder; Init Command Contract: `init` writes it only when missing and never overwrites it, even with `--force`. Driven by CR-004 item 10 and its Gate 2 finding F1. | Agents and skills already reference the file, but `init` never created it. | None in flight |
| 2026-10-24 | Init Command Contract: state detection (upgrade, new project, adoption), the upgrade questions and `--update-docs` / `--update-skills`, the `framework_version` bump, the stale-definition warning, the adoption collision question, and `--force` / `--dry-run` per case. Driven by CR-005. | `init` treated every run the same: refuse, or overwrite everything with `--force`, so upgrading overwrote the project's own guidance. | None in flight |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005: legacy Codex removal, dry-run unanswered questions and skipped-file reporting not described (amend); skipped-file wording, root guidance not detected as adoption, upgrade not recreating missing skeleton files (follow-up tasks); `--tools` on an upgrade escalated | none |
| 2026-10-25 | Init Command Contract: legacy Codex removal on an approved agents-and-skills overwrite; dry-run reporting of unanswered questions; adoption reports kept files whenever the question is not answered yes; on an upgrade an explicit `--tools` sets `[init] tools` and writes a newly added tool's agents and skills without a question (human decision, option B). Driven by the CR-005 spec-truth reconciliation (F1, F2, F3a, F6). | The completed work was right on F1, F2 and F3a; the human decided F6. | Follow-up tasks for F3b, F4, F5 and F6 |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005 re-run: F1–F6 resolved (T-155 to T-158); upgrade text omits per-file skeleton recreation and the newly-added-tool missing-files-only rule (amend); usage.md and setup-guide.md say new files are not reported, but upgrade prints WROTE (follow-up task) | none |
| 2026-10-25 | Init Command Contract: an upgrade writes every missing project-skeleton file no question covers, without a question, and reports it as `WROTE`; for a tool newly added by `--tools`, only its missing agents and skills are written and its existing files are kept. Driven by the CR-005 spec-truth reconciliation re-run (N1). | The completed work (T-157, T-158) was right and more precise than the text. | Follow-up task for N2 |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005 second re-run: N1 and N2 resolved (S-009 amendment, T-159); usage.md:232 and setup-guide.md:78 overstate WROTE reporting for question-approved and root-guidance writes (escalated); usage.md:233 says skipped files are unreported though an adoption lists them (follow-up task); S-009 omits WROTE for a newly added tool's files (amend) | none |
| 2026-10-25 | Init Command Contract: added the Reporting rule. The real run prints `WROTE` for every file it creates and `OVERWROTE` for every file it replaces, matching its dry run, and kept files are reported on stderr. Driven by the CR-005 spec-truth reconciliation second re-run (N3, human decision: option B; N5). | The real run reported fewer files than its dry run listed, and the docs overstated it. | Follow-up task for N3 and N4 |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005 third re-run: N3 and N5 resolved (T-160, S-009 Reporting rule); N4's false sentence removed, but the kept-files-on-stderr rule (S-009, usage.md:230, setup-guide.md:78) holds only for an adoption (escalated, N6); legacy Codex folders removed when codex is dropped (follow-up task, N7); root .gitignore created without WROTE (escalated, N8) | none |
| 2026-10-25 | Init Command Contract: only an adoption lists the kept files on stderr (N6, human decision: option A); the real run reports the tracker folder and root `.gitignore` rule as `CREATED` / `UPDATED` (N8, option B); legacy Codex removal requires `codex` to be selected and already configured, so dropping or newly adding it removes nothing (N7, human decision). Driven by the CR-005 spec-truth reconciliation third re-run. | The Reporting rule promised kept-file reporting the code only does for an adoption, and left the tracker writes unreported; the legacy removal keyed on the prior configuration alone. | Follow-up task for N6, N7 and N8 |
| 2026-10-25 | Legacy Codex skills: reworded so the "already configured" condition applies only to an upgrade; an adoption removes on a yes or `--force`. Wording only, from the T-161 review. | The previous text could be read as "an adoption never removes", against the code and `usage.md`. | None in flight |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005 fourth re-run: N6, N7 and N8 resolved (T-161, S-009 amendments; a missing .gitignore reports UPDATED, matching WOULD UPDATE); adoption kept-file list covers project-skeleton files but not root guidance or coding_guidelines.md (amend, N9); new project with --force removes legacy Codex folders (amend S-009, usage.md fix, N10) | none |
| 2026-10-25 | Init Command Contract: the adoption question covers the existing agent, skill and project-skeleton files, not root guidance or `docs/coding_guidelines.md`, and only those kept files are listed (N9); a new project with `--force` removes legacy Codex folders (N10, CR-002 behaviour); adding the `.gitignore` rule is reported as `UPDATED` even when it creates the file. Driven by the CR-005 spec-truth reconciliation fourth re-run. | The completed work was right; the text was imprecise. | None in flight |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005 fifth re-run: N9 and N10 resolved (S-009 amendment 25f8639d, usage.md e165706e); usage.md:235 and setup-guide.md:78 still say an adoption lists the existing files it keeps, though kept root guidance and coding_guidelines.md are not listed (docs fix, N11) | none |
| 2026-10-25 | spec-truth reconciliation — PASS | CR-005 sixth re-run: N11 resolved (usage.md:235 and setup-guide.md:78 now state that only an adoption lists kept files, excluding root guidance and coding_guidelines.md, 3fb64634); Init Command Contract matches init.py, usage.md, commands.md, setup-guide.md and customization-guide.md | none |
| 2026-10-25 | Init Command Contract: the upgrade case needs a `.ai-team.toml` that records `[init] tools`; a hand-written marker without it is a first run (new project or adoption) that keeps its settings; an upgrade question that covers no files is not asked. Driven by the PR #49 review. | A preset marker made the first init an upgrade that never recorded `framework_version`, and `--update-skills` stamped the version without updating any file. | None in flight |
| 2026-10-25 | Claude is the only export target: no `--tools` option or `[init] tools` key, and project-state detection keys off `[init] framework_version`; each skill is one source `SKILL.md` copied as is (no `body.md` + `metadata.toml` merge); sources and scaffolds lose the per-tool folder level (`sources/agents/*.md`, `scaffolds/{project,agents,skills}/`); the project and root guidance template is `AGENTS.md` only; the legacy Codex removal and newly-added-tool upgrade rules are dropped, with no Codex compatibility. Driven by CR-007 and ADR-003. | The human dropped Codex support and asked to simplify the two-tool design. | None in flight |
