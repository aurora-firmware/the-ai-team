---
title: CLI-owned framework scaffolds
version: '0.8'
status: approved  # draft | review | approved | superseded
created: '2026-05-14'
author: planner
id: S-009
---

# CLI-owned framework scaffolds

## Purpose

This spec covers the S-000 **Generators** component and the `init` command of the
**CLI** component. The framework once had several product copies of its agent and
skill definitions — repository-root tool folders such as `.claude/`, the bundled init
scaffolds, and an exportable `ai-process/` snapshot — and copies drift, while the
process layer must stay the authoritative documentation in this repository. The CLI
package is now the only product source: maintainers edit
`cli/src/ai_team/init/sources/`, a generator produces the committed scaffolds from them,
and `ai-team init` writes those scaffolds into a consuming project, filling in its
settings. Every agent, skill and skill supporting file a project receives comes from
the sources, each skill is authored once as the `SKILL.md` Claude reads, and the
committed scaffolds always equal a fresh generation. Claude is the only export target
(CR-007, ADR-003).

## Users and Journeys

| Actor | Goal | Priority | Outcome | Requirements |
|---|---|---|---|---|
| Maintainer changing an agent or skill | Change it in one place and ship it | P1 | One source edit plus one generator run updates the committed scaffolds; a test fails if they drift | REQ-001–REQ-007 |
| Human or agent setting up a new project | Get agents, skills, the project skeleton and settings in one command | P1 | `init` writes everything with the project's settings filled in and reports each file | REQ-008–REQ-011, REQ-014, REQ-015, REQ-017 |
| Human or agent upgrading a project | Take a newer framework version without losing project content | P1 | `init` asks before replacing docs or skills, recreates missing skeleton files, keeps settings and the project's coding guidelines | REQ-010–REQ-012, REQ-014–REQ-016 |
| Human or agent adopting an existing repository | Add the framework without silently replacing existing files | P2 | `init` asks once about existing files and keeps them unless told otherwise | REQ-011, REQ-013–REQ-015 |
| Skill author | Know which files of a skill are exported and how placeholders behave | P2 | The skill authoring guide states the rules | REQ-020 |

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
- **Removing skills or agents a version no longer ships.** An upgrade warns about them
  and leaves them in place (REQ-012).
- **The export paths and the layout check.** The agent and skill destination folders are
  owned by S-003 (level 1 of the layout check) and the tracker by S-006. This spec
  refers to them rather than restating them.

## Architecture

### Design Principles

1. **CLI package owns exported framework assets.** Anything `ai-team init` writes into a
   consuming project comes from package-owned data under `cli/src/ai_team/init/`
   (REQ-001).
2. **Root tool folders are local configuration.** Repository-root tool folders such as
   `.claude/` are for developing this repository, not for shipping the framework, and no
   source or generator reads them (REQ-001).
3. **One file per skill.** Each skill is authored once as a source `SKILL.md`, its
   frontmatter followed by its procedural body, in the form Claude reads. The generator
   copies it unchanged; there is no header merge (REQ-002).
4. **Generated output is reproducible.** The committed scaffolds must equal a fresh run
   of the generator over the committed sources; a source change and its regenerated
   output are committed together (REQ-007).
5. **Project settings are filled in at init time.** Generated scaffolds keep their
   placeholders; `init` is the only step that knows the project's settings (REQ-009).
6. **No process duplication.** `ai-process/` remains the specification layer in this
   repository and is not bundled into the CLI init scaffolds (REQ-018).
7. **Documentation follows ownership.** README, guides, CLI docs, and architecture docs
   describe the package-owned scaffolding model and name the generator, not root tool
   folders, as the way exported definitions change (REQ-020).

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

### Alternatives Considered

- **Direct package copies.** Keep separate Claude and Codex scaffold files directly
  under the CLI package and copy them as-is. Simpler, but the shared skill text drifts
  between tool formats unless every change is duplicated by hand.
- **Shared skill body with generated tool scaffolds.** Store each skill body once and
  generate Claude and Codex files with tool-specific metadata. Chosen while two tools
  were exported; CR-007 dropped Codex, so the header merge no longer removes any
  duplication, and each skill is now one source `SKILL.md` copied as is.
- **Fully structured framework model.** Model agents and skills as structured data and
  generate every tool artifact from that schema. Cleaner long-term but too broad: it
  needs a new schema, migration rules, and a review of every agent definition.
- **Rendering placeholders in the generator (CR-003).** Rejected: the project directory
  and integration branch are only known when `init` runs in a consuming project.

## Interfaces

**Exposed — source tree (REQ-001–REQ-005).** **Contract:**
`cli/src/ai_team/init/sources/` holds `skills/<name>/SKILL.md` with optional
`assets/`, `references/` and `scripts/` folders; `agents/*.md`; `project/` (the project
`AGENTS.md`, `.gitignore` and the `coding_guidelines.md` placeholder); and `root/` (the
root `AGENTS.md` template). Source text names project settings only through the
`{{project_dir}}` and `{{integration_branch}}` placeholders.

**Exposed — generator (REQ-002–REQ-007).** `python scripts/sync_init_scaffolds.py`,
run from `cli/`, rewrites `cli/src/ai_team/init/scaffolds/` (`project/`, `agents/`,
`skills/`). `--help` or `-h` prints usage; an unknown argument prints usage and fails;
neither touches the scaffolds.

**Exposed — `ai-team init [PATH]` (REQ-008–REQ-019).** Options: `--project-dir`,
`--integration-branch`, `--create-root-guidance`, `--update-docs`, `--update-skills`,
`--no-interactive`, `--dry-run`, `--force`. The full list and help text are in
`cli/docs/commands.md`. `--tools` and `--include-ai-process` are unknown options.

**Exposed — `.ai-team.toml` (REQ-010).** `init` records `[project] dir`,
`[tracker] dir`, `[git] integration_branch` and `[init] framework_version`.

**Exposed — report lines (REQ-011, REQ-014, REQ-015).** **Contract:** on stdout,
`WROTE: <path>`, `OVERWROTE: <path>`, `CREATED: <path>` and `UPDATED: <path>` for the
real run; `WOULD WRITE`, `WOULD OVERWRITE`, `WOULD CREATE`, `WOULD UPDATE` and
`WOULD PROMPT: <path>` for a dry run, which starts with a line naming the detected
case. Kept files of an adoption are listed on stderr.

**Consumed.**
- The agent and skill export paths from S-003 level 1, and the tracker folder and
  ignore rule from S-006.
- The installed distribution version, recorded as `framework_version`.

## Workflow

### Maintainer Asset Flow

```
Edit a package-owned source asset
  ↓
Run the scaffold generator                                         (REQ-002–REQ-006)
  ↓
Generated scaffolds update under cli/src/ai_team/init/scaffolds/
  ↓
Run the tests (scaffolds match a fresh generation)                 (REQ-007)
  ↓
Commit the source change, the generated output, and test/doc updates together
```

### Consumer Init Flow

```
ai-team init [PATH]
  ↓
Detect the case: new project, adoption or upgrade                  (REQ-011)
  ↓
Ask the case's questions, unless flags or --no-interactive answer them
                                                                   (REQ-012, REQ-013)
  ↓
Write the project skeleton to the configured project directory     (REQ-005, REQ-016)
  ↓
Write the agents and skills to the S-003 export paths,
filling in placeholders (non-UTF-8 files copied byte for byte)     (REQ-008, REQ-009)
  ↓
Write or refresh .ai-team.toml, keeping existing settings          (REQ-010)
  ↓
Create the tracker folder and its ignore rule (S-006)
  ↓
★ Offer root AGENTS.md when missing                                (REQ-017)
  ↓
Report every file written, replaced, created or kept               (REQ-015)
```

Failure and boundary paths: a source skill without `SKILL.md` stops the generator
(REQ-002). `--tools` or `--include-ai-process` is rejected and nothing is written
(REQ-008, REQ-018). With `--no-interactive`, an unanswered question means "no"
(REQ-012, REQ-013). `--dry-run` writes nothing (REQ-014).

## Behavioral Requirements

### REQ-001 — Single product source

Every agent, skill, skill supporting file and project skeleton file that `init` writes
SHALL come from `cli/src/ai_team/init/sources/` through the generated scaffolds, and no
source or the generator SHALL read repository-root tool folders or `ai-process/`.

#### AC-001.1 — Sources cover the export

- **Given:** the source tree
- **When:** its skills and agents are listed
- **Then:** each skill source holds a `SKILL.md` and no `body.md` or `metadata.toml`,
  and every exported role has an agent source

**Verification:** Tests:
`test_package_owned_skill_sources_hold_only_skill_md_with_frontmatter` and
`test_package_owned_agent_sources_cover_each_exported_role` in
`cli/tests/test_init_scaffolds.py`; inspection of the generator for reads outside
`sources/`.

### REQ-002 — Skill copy

The generator SHALL copy each source skill's `SKILL.md` unchanged into the skill
scaffold, and SHALL stop with an error naming the skill when a source skill has no
`SKILL.md`.

#### AC-002.1 — Unchanged copy and missing file

- **Given:** source skills, one of them without `SKILL.md`
- **When:** the generator runs
- **Then:** it stops and names that skill; without it, every `SKILL.md` is copied
  byte for byte

**Verification:** Tests: `test_sync_script_copies_each_skill_md_unchanged` and
`test_sync_script_stops_naming_the_skill_when_skill_md_is_missing` in
`cli/tests/test_init_scaffolds.py`.

### REQ-003 — Skill supporting folders

The generator SHALL copy a source skill's `assets/`, `references/` and `scripts/`
folders, when present, next to its `SKILL.md`, byte for byte and with placeholders
unchanged, leaving out `__pycache__` and `.DS_Store`. No other file or folder in a
source skill directory SHALL be exported.

#### AC-003.1 — Supporting folders exported

- **Given:** a fixture skill with `assets/`, `scripts/`, an extra `notes.md` and a
  `__pycache__` folder
- **When:** the generator runs
- **Then:** `assets/` and `scripts/` are copied byte for byte; `notes.md` and
  `__pycache__` are not

**Verification:** Tests in `cli/tests/test_cr003_skill_supporting_folders.py`.

### REQ-004 — Agents copied

The generator SHALL copy every agent source into the agent scaffold as a real file,
never a symlink.

#### AC-004.1 — Agent scaffolds

- **Given:** the agent sources
- **When:** the generator runs twice
- **Then:** each agent scaffold equals its source, an agent whose source was removed
  is gone, and the second run changes nothing

**Verification:** Tests: `test_sync_script_copies_package_owned_agents` and
`test_sync_script_is_idempotent_for_agent_scaffolds` in
`cli/tests/test_init_scaffolds.py`.

### REQ-005 — Project skeleton

The generated project skeleton SHALL hold `specs/`, `decisions/` and `docs/`, each kept
with an empty placeholder file; a `docs/coding_guidelines.md` placeholder with no
project-specific rules; the project `AGENTS.md`, which explains the purpose of the
generated artifact folders and files; and a `.gitignore` that ignores the
`.ai-team.lock` sentinel. It SHALL hold no task, bug or change-request folders.

#### AC-005.1 — Skeleton contents

- **Given:** the sources
- **When:** the generator runs
- **Then:** the project scaffold holds exactly the folders and files above

**Verification:** Tests: `test_sync_script_replaces_project_with_empty_lifecycle_skeleton`,
`test_sync_script_copies_project_guidance_files_from_source`,
`test_sync_script_copies_coding_guidelines_placeholder_into_project_docs`,
`test_package_owned_coding_guidelines_placeholder_has_no_project_specific_rules` and
`test_sync_script_copies_project_gitignore_ignoring_the_lock_sentinel` and
`test_project_guidance_sources_exist_and_describe_project_artifact_folders` in
`cli/tests/test_init_scaffolds.py`.

### REQ-006 — Generator run

Each generator run SHALL replace the generated scaffolds completely, so a removed
source leaves no stale scaffold, and SHALL NOT modify the sources. `--help`, `-h` or an
unknown argument SHALL print usage without regenerating.

#### AC-006.1 — Sources untouched

- **Given:** the source tree
- **When:** the generator runs
- **Then:** no source file changes

**Verification:** Test: `test_sync_script_does_not_modify_sources_directory` in
`cli/tests/test_init_scaffolds.py`.

#### AC-006.2 — Arguments

- **Given:** existing scaffolds
- **When:** the generator runs with `--help`, `-h` or `--bogus`
- **Then:** it prints usage, the unknown argument fails, and the scaffolds are
  unchanged; with no argument it regenerates

**Verification:** Tests: `test_sync_script_long_help_prints_usage_and_leaves_scaffolds_untouched`,
`test_sync_script_short_help_prints_usage_and_leaves_scaffolds_untouched`,
`test_sync_script_rejects_unknown_argument_with_usage_and_leaves_scaffolds_untouched`
and `test_sync_script_without_arguments_generates_scaffolds` in
`cli/tests/test_init_scaffolds.py`.

### REQ-007 — Committed scaffolds match

The committed scaffolds SHALL equal a fresh generator run over the committed sources.

#### AC-007.1 — No drift

- **Given:** a clean checkout
- **When:** the generator runs into a temporary folder
- **Then:** its output equals the committed scaffolds

**Verification:** Test: `test_committed_scaffolds_match_fresh_sync_output` in
`cli/tests/test_init_scaffolds.py`.

### REQ-008 — Agents and skills always exported

`init` SHALL always write the agents and skills, as real files and directories with
their supporting folders, to the export paths of S-003 level 1. There SHALL be no tool
selection: `--tools` SHALL be rejected as an unknown option, and `init` SHALL NOT read
or write `[init] tools`.

#### AC-008.1 — Claude export

- **Given:** an empty directory
- **When:** `init --no-interactive` runs
- **Then:** the agents and skills are written under `.claude/`, and the marker has no
  `tools` key

**Verification:** Tests: `test_init_writes_only_claude_agents_and_skills_non_interactively`
and `test_init_never_adds_tools_to_the_marker` in `cli/tests/test_init.py`, and
`test_exports_agents_and_skills_under_dot_claude` in `cli/tests/test_tool_paths.py`.

#### AC-008.2 — `--tools` rejected

- **Given:** an empty directory
- **When:** `init --tools claude` runs
- **Then:** it fails as an unknown option and writes nothing

**Verification:** Test: `test_init_rejects_the_tools_option_and_writes_nothing` in
`cli/tests/test_init.py`.

### REQ-009 — Placeholders and binary files

`init` SHALL replace `{{project_dir}}` and `{{integration_branch}}` in every UTF-8
scaffold file it writes — skills, supporting files, agents and project guidance — with
the values from the `init` flags or `.ai-team.toml`, defaulting to `ai-team` and
`dev-agent`. A scaffold file that does not decode as UTF-8 SHALL be copied byte for
byte without replacement.

#### AC-009.1 — Configured and default values

- **Given:** `init --project-dir docs/ai-team --integration-branch develop`, and a
  plain `init`
- **When:** the generated files are read
- **Then:** the first uses `docs/ai-team` and `develop`, the second `ai-team` and
  `dev-agent`, and no placeholder remains

**Verification:** Tests: `test_generated_output_uses_configured_folder_and_branch` and
`test_default_init_renders_default_folder_and_branch` in
`cli/tests/test_configurable_project_settings.py`.

#### AC-009.2 — Non-UTF-8 file

- **Given:** a scaffold file with invalid UTF-8 bytes
- **When:** `init` writes it
- **Then:** the destination is byte-identical to the source and no error is raised

**Verification:** Tests: `test_writes_non_utf8_file_byte_for_byte` and
`test_does_not_raise_unicode_error_for_invalid_utf8` in
`cli/tests/test_cr003_init_binary_scaffolds.py`.

### REQ-010 — Project settings

`init` SHALL record `[project] dir`, `[tracker] dir`, `[git] integration_branch` and
`[init] framework_version` in `.ai-team.toml`, and SHALL write the project skeleton to
the project directory taken from `--project-dir`, else `[project] dir`, else
`ai-team`. On a repository with a marker, it SHALL
keep the configured project directory and integration branch unless the matching flag
is given, SHALL always keep `[tracker] dir`, and SHALL keep every other setting the
user added.

#### AC-010.1 — Settings kept

- **Given:** a marker with a custom project directory, branch and an unrelated table
- **When:** `init --force` runs without `--project-dir` or `--integration-branch`
- **Then:** all of them are unchanged

**Verification:** Tests: `test_force_reinit_keeps_configured_settings_and_unrelated_tables`
in `cli/tests/test_configurable_project_settings.py` and
`test_upgrade_keeps_the_marker_bytes_when_no_setting_changes` in
`cli/tests/test_init_upgrade.py`.

#### AC-010.2 — Explicit setting changes

- **Given:** an upgraded project
- **When:** `init --integration-branch main` runs
- **Then:** the marker records `main`

**Verification:** Test: `test_upgrade_rewrites_the_marker_when_an_explicit_setting_changes`
in `cli/tests/test_init_upgrade.py`.

### REQ-011 — Project state detection

Before writing, `init` SHALL detect one case: **upgrade** when `.ai-team.toml` records
`[init] framework_version`; otherwise **new project** when none of the files `init`
would write exist, or **adoption** when some do. A hand-written marker without
`framework_version` SHALL be a first run whose settings are kept.

#### AC-011.1 — Cases

- **Given:** an empty directory; a directory with existing scaffold files and no
  marker; a marker with `framework_version`; and a marker without it
- **When:** `init --dry-run` runs in each
- **Then:** the first line names new project, adoption, upgrade, and new project or
  adoption respectively

**Verification:** Tests: `test_dry_run_on_an_empty_directory_starts_with_the_new_project_case_line`,
`test_dry_run_with_existing_scaffold_files_but_no_marker_is_adoption`,
`test_dry_run_upgrade_starts_with_the_upgrade_case_line`,
`test_a_marker_without_a_framework_version_is_a_first_run_that_records_it` and
`test_a_marker_without_a_framework_version_with_existing_skills_is_an_adoption` in
`cli/tests/test_init_upgrade.py`.

### REQ-012 — Upgrade

On an upgrade, `init` SHALL ask two questions in order, skipping one that covers no
files: update the ai-team docs (the project `AGENTS.md` and `.gitignore`), then update
the agents and skills. `--update-docs` and `--update-skills` SHALL answer them, and
with `--no-interactive` an unanswered question SHALL mean "no". When the agents and
skills are updated, `framework_version` SHALL be set to the running version, and
skills and agents the running version does not ship SHALL be listed in a stderr
warning and never removed. A missing project directory, and any missing skeleton file
no question covers, SHALL be written without a question; an existing skeleton file
SHALL never be overwritten.

#### AC-012.1 — Questions and flags

- **Given:** an upgraded project
- **When:** `init` runs interactively, then with each flag, then with
  `--no-interactive`
- **Then:** it asks docs then skills; each flag answers its question; the
  non-interactive run changes and reports nothing

**Verification:** Tests: `test_upgrade_asks_for_docs_then_for_agents_and_skills`,
`test_update_docs_flag_answers_the_docs_question_without_prompting`,
`test_update_skills_flag_answers_the_skills_question_without_prompting` and
`test_no_interactive_upgrade_changes_nothing_and_reports_nothing` in
`cli/tests/test_init_upgrade.py`.

#### AC-012.2 — Version and stale definitions

- **Given:** an upgraded project with a skill the running version does not ship
- **When:** `init --update-skills` runs
- **Then:** `framework_version` becomes the running version, the extra skill is named
  in a stderr warning and stays in place

**Verification:** Tests: `test_skills_update_sets_framework_version_and_keeps_other_settings`,
`test_framework_version_is_unchanged_when_skills_are_not_updated`,
`test_skills_update_warns_on_stderr_about_definitions_the_version_does_not_ship` and
`test_skills_update_never_deletes_definitions_the_version_does_not_ship` in
`cli/tests/test_init_upgrade.py`.

#### AC-012.3 — Missing skeleton files

- **Given:** an upgraded project missing its project directory, or missing
  `docs/coding_guidelines.md` or a `specs/` placeholder
- **When:** `init --no-interactive` runs
- **Then:** the missing files are written and reported as `WROTE`, without a question

**Verification:** Tests: `test_upgrade_recreates_a_missing_project_directory`,
`test_upgrade_recreates_a_missing_coding_guidelines_file_and_reports_it`,
`test_upgrade_recreates_missing_specs_and_decisions_placeholders` and
`test_force_upgrade_never_overwrites_an_existing_skeleton_file` in
`cli/tests/test_init_upgrade.py`.

### REQ-013 — Adoption

On an adoption, `init` SHALL write `.ai-team.toml`, the project directory and the
agents and skills, and SHALL ask once about the existing agent, skill and
project-skeleton files it would replace, listing them all; `--force` SHALL answer yes.
Root guidance and an existing `docs/coding_guidelines.md` SHALL NOT be part of that
question. When the question is not answered yes, the files SHALL be kept and listed on
stderr.

#### AC-013.1 — One question

- **Given:** a repository with some of the files `init` would write
- **When:** `init` runs and the question is answered yes, then no
- **Then:** yes overwrites them; no keeps them and lists them on stderr

**Verification:** Tests: `test_asks_once_listing_every_existing_file_and_overwrites_on_yes`,
`test_keeps_existing_files_when_the_question_is_answered_no` and
`test_reports_kept_files_on_stderr_without_naming_force_when_answered_no` in
`cli/tests/test_init_adoption.py`.

#### AC-013.2 — Non-interactive and excluded files

- **Given:** the same repository plus root `AGENTS.md` and `docs/coding_guidelines.md`
- **When:** `init --no-interactive` runs
- **Then:** existing files are kept and reported, the exit code is 0, and root guidance
  and coding guidelines are not in the question

**Verification:** Tests: `test_no_interactive_skips_existing_files_reports_them_and_exits_zero`
and `test_does_not_ask_about_coding_guidelines_or_root_guidance` in
`cli/tests/test_init_adoption.py`.

### REQ-014 — `--force` and `--dry-run`

`--force` SHALL answer yes to every overwrite question; without it an existing file
SHALL be replaced only on a yes. `--dry-run` SHALL write nothing, SHALL report the
detected case and then what the real run with the same flags would write, and SHALL
print `WOULD PROMPT: <path>` for each file an unanswered question covers. What a yes
would trigger — the stale-definition warning and the `framework_version` bump — SHALL
be reported only when a flag, `--force` or `--no-interactive` answers the question.

#### AC-014.1 — Dry run equals real run

- **Given:** any repository
- **When:** `init --dry-run` and then `init` run with the same flags
- **Then:** the dry run writes nothing, and its `WOULD WRITE` paths equal the real
  run's written paths

**Verification:** Tests: `test_init_dry_run_lists_files_and_writes_nothing` and
`test_dry_run_write_set_equals_paths_the_real_run_writes` in `cli/tests/test_init.py`.

#### AC-014.2 — Unanswered questions

- **Given:** an upgraded project
- **When:** `init --dry-run` runs interactively
- **Then:** it prints `WOULD PROMPT: <path>` for each covered file

**Verification:** Test: `test_dry_run_upgrade_prompts_for_each_file_an_unanswered_question_covers`
in `cli/tests/test_init_upgrade.py`.

#### AC-014.3 — What a yes would trigger

- **Given:** an upgraded project with a skill the running version does not ship
- **When:** `init --dry-run --update-skills` runs, and `init --dry-run` runs
  interactively
- **Then:** the first reports the `framework_version` bump and the stale-definition
  warning without writing them; the second prints only `WOULD PROMPT` lines for the
  skills question

**Verification:** Tests: `test_dry_run_reports_the_version_bump_without_writing_it` and
`test_dry_run_upgrade_prints_case_then_would_lines_then_the_stale_warning` in
`cli/tests/test_init_upgrade.py`; inspection for the interactive case, which no test
covers.

### REQ-015 — Reporting

`init` SHALL report on stdout each file it creates as `WROTE: <path>` and each file it
replaces as `OVERWROTE: <path>`, matching its dry run's `WOULD WRITE` and
`WOULD OVERWRITE`, and the tracker folder and the root `.gitignore` rule as
`CREATED: <path>` and `UPDATED: <path>`, matching `WOULD CREATE` and `WOULD UPDATE`.
Only an adoption SHALL list kept files, on stderr, excluding root guidance and an
existing `docs/coding_guidelines.md`.

#### AC-015.1 — New project

- **Given:** an empty git repository
- **When:** `init --no-interactive` runs
- **Then:** every created file is reported as `WROTE`, the tracker as `CREATED` and the
  `.gitignore` rule as `UPDATED`

**Verification:** Tests: `test_new_project_reports_every_created_file_as_wrote`,
`test_new_project_reports_the_tracker_folder_as_created` and
`test_new_project_reports_the_root_gitignore_rule_as_updated` in
`cli/tests/test_init_adoption.py`.

#### AC-015.2 — Upgrade matches its dry run

- **Given:** an upgraded project
- **When:** a dry run and then the real run execute with the same flags
- **Then:** the real run reports every file its dry run listed

**Verification:** Test: `test_upgrade_real_run_reports_every_file_its_dry_run_would_write`
in `cli/tests/test_init_upgrade.py`.

### REQ-016 — Coding guidelines kept

`init` SHALL write `docs/coding_guidelines.md` in the project directory only when it is
missing, SHALL never overwrite it, even with `--force`, and SHALL NOT count an existing
one as a collision.

#### AC-016.1 — Existing guidelines

- **Given:** a project with its own `docs/coding_guidelines.md`
- **When:** `init --force` runs
- **Then:** the file is unchanged and not reported

**Verification:** Tests: `test_init_writes_coding_guidelines_placeholder_when_missing`,
`test_init_keeps_existing_coding_guidelines_without_counting_a_collision` and
`test_init_force_keeps_existing_coding_guidelines` in `cli/tests/test_init.py`.

### REQ-017 — Root guidance

`init` SHALL offer to create a missing root `AGENTS.md` from the root template:
interactively it asks; `--create-root-guidance` creates it without asking;
`--no-interactive` without that flag skips it. When the human declines, `init` SHALL
print follow-up guidance that autonomous loops need documented project commands. The
root template SHALL invite the project's commands, including the test command. An
existing root `AGENTS.md` SHALL be replaced only with `--force` and a yes, or with
`--force` and `--create-root-guidance`.

#### AC-017.1 — Offer and decline

- **Given:** a repository without root `AGENTS.md`
- **When:** `init` runs interactively and the offer is declined, then
  `init --no-interactive --create-root-guidance` runs
- **Then:** the first prints the follow-up message; the second creates `AGENTS.md` from
  the template

**Verification:** Tests: `test_interactive_init_prompts_to_create_root_agents_md_when_missing`,
`test_declining_root_guidance_prints_followup_message`,
`test_non_interactive_init_skips_root_guidance_by_default`,
`test_non_interactive_init_creates_root_guidance_with_flag` and
`test_root_guidance_file_created_from_stable_template` in `cli/tests/test_init.py`.

#### AC-017.2 — Existing root guidance

- **Given:** a repository with root `AGENTS.md`
- **When:** `init` runs without `--force`, then with `--force` answered no
- **Then:** the file is unchanged both times

**Verification:** Tests: `test_root_guidance_file_existing_agents_md_is_not_overwritten`
and `test_interactive_force_keeps_and_does_not_report_root_guidance_on_no` in
`cli/tests/test_init.py`.

### REQ-018 — No `ai-process/` export

`init` SHALL never write `ai-process/`, SHALL reject `--include-ai-process` as an
unknown option, and SHALL ask no question about it; the scaffolds SHALL contain no
`ai-process/`.

#### AC-018.1 — Option rejected

- **Given:** an empty directory
- **When:** `init --include-ai-process` runs, and `init` runs interactively
- **Then:** the first fails as an unknown option; the second asks nothing about
  `ai-process/` and writes no such folder

**Verification:** Tests: `test_init_include_ai_process_is_unknown_option`,
`test_init_interactive_does_not_prompt_for_ai_process_snapshot` and
`test_init_defaults_to_cwd_and_scaffolds_project_claude_and_marker` (no `ai-process/`
written) in `cli/tests/test_init.py`.

### REQ-019 — No Codex handling

`init` SHALL NOT read, migrate or remove Codex files a project already has (`.codex/`,
`.agents/skills/`) and SHALL print no note about them.

#### AC-019.1 — Codex folders left alone

- **Given:** a project with a framework-named skill under a Codex folder
- **When:** `init --update-skills` or a first `init --force` runs
- **Then:** the Codex folder is unchanged

**Verification:** Tests: `test_upgrade_leaves_a_framework_named_codex_skill_folder_in_place`
and `test_first_init_with_force_leaves_a_framework_named_codex_skill_folder_in_place` in
`cli/tests/test_init_upgrade.py`.

### REQ-020 — Documentation of ownership

The README, `guides/setup-guide.md`, `cli/docs/` and the `ai-process/` architecture docs
SHALL state that `ai-process/` is not exported, that the CLI package sources are the
product source changed through the generator, and that repository-root tool folders are
local configuration. `guides/skill_template.md` SHALL state which files of a source
skill are exported, that supporting folders reach the export, and that `init` fills
placeholders except in non-UTF-8 files.

#### AC-020.1 — Skill authoring guide

- **Given:** `guides/skill_template.md`
- **When:** its export rules are read
- **Then:** it states the one-`SKILL.md` rule, the supporting folders and the
  placeholder and byte-copy rules

**Verification:** Tests in `cli/tests/test_cr003_skill_template_guide.py`.

#### AC-020.2 — Ownership statements

- **Given:** `cli/docs/usage.md` and the README
- **When:** their scaffold sections are read
- **Then:** they name the sources and the generator and say `init` never copies
  `ai-process/`

**Verification:** Tests: `test_usage_md_states_never_copies_ai_process`,
`test_usage_md_documents_scaffold_source_maintenance` and
`test_usage_md_documents_scaffold_generator_script` in `cli/tests/test_usage_guide.py`;
inspection of the README.

## Quality Requirements

None. `init` and the generator are local file operations with no security, privacy,
accessibility or performance target agreed; reproducibility is REQ-007.

## Configuration Requirements

**Scaffold placeholders** (REQ-009)
- **What must exist:** the `{{project_dir}}` and `{{integration_branch}}` placeholders
  are the only way a source asset names the project's settings.
- **Where it lives:** in the package-owned source files; values come from the `init`
  flags or `.ai-team.toml`.
- **Constraints:** the generator leaves them unchanged; `init` fills them in every UTF-8
  scaffold file it writes.
- **Missing-value behaviour:** with no flag and no configured value, `init` uses
  `ai-team` and `dev-agent`.

**Skill source file** (REQ-002)
- **What must exist:** a `SKILL.md` per source skill, with its frontmatter and body.
- **Where it lives:** `cli/src/ai_team/init/sources/skills/<name>/SKILL.md`.
- **Constraints:** must not require reading repository-root tool folders.
- **Missing-value behaviour:** the generator stops with an error naming the skill.

## Assumptions and Dependencies

- **S-003 owns the export paths** (`.claude/agents/`, `.claude/skills/`) that REQ-008
  writes to, and S-006 owns the tracker folder and ignore rule `init` creates.
- **The installed distribution version** is available to `init` for
  `framework_version`.
- **Maintainers run the generator** before committing a source change; REQ-007's test
  catches a forgotten run, and S-010's CI runs that test on every pull request.
- **Claude Code reads `.claude/agents/`, `.claude/skills/` and root `AGENTS.md`**
  (ADR-003). If that changes, S-003 and this spec change together.

## Success Criteria

1. `cli/tests/test_init_scaffolds.py::test_committed_scaffolds_match_fresh_sync_output`
   passes on every pull request (REQ-007).
2. After `ai-team init --no-interactive` in an empty git repository, the agents and
   skills are under `.claude/`, the project skeleton is in `ai-team/`, the marker
   records the four settings, no placeholder remains in any UTF-8 file, and no
   `ai-process/` exists (REQ-005, REQ-008–REQ-010, REQ-018).
3. A dry run and the real run with the same flags report the same files in every case
   (REQ-014, REQ-015).
4. No `init` run, with any flags, changes an existing `docs/coding_guidelines.md`
   (REQ-016).
5. The `init` and generator test files named in the acceptance scenarios pass
   (REQ-001–REQ-020).

## Implementation Order

All phases are delivered: package-owned sources, the generator, bundled scaffolds
without `ai-process/`, the `init` contract, tests and documentation; the CR-003
supporting folders, byte copy and skill-guide rules; the CR-005 project states and
reporting; and the CR-007 single `SKILL.md` per skill with Claude as the only target.
Later changes follow the amendment flow.

## Open Questions

None.

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
| 2026-10-25 | Maintainer Asset Flow and the CR-003 Implementation Order no longer name shared bodies or two exports. Wording only. Driven by the CR-007 spec-truth reconciliation (D2). | Two-tool leftovers the CR-007 amendment missed; the generator copies each `SKILL.md` into one export. | None in flight |
| 2026-10-26 | Restructured to the spec format from PR #51: added Users and Journeys, Interfaces (source tree, generator, `init` options, marker keys, report lines), Behavioral Requirements REQ-001–REQ-020 with acceptance scenarios, Quality Requirements, Assumptions and Dependencies, Success Criteria and Open Questions; Alternatives Considered moved under Architecture; the Components section became requirements; the stale reference to S-007 requirement 12 was dropped. Scope moved in: REQ-017, the root `AGENTS.md` offer, from the superseded S-002, which this spec's init contract already referred to. Version bumped to 0.8. | The validator rejects approved specs without the new sections; S-002 was superseded. | None |
