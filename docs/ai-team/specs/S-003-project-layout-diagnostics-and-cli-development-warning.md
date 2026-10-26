---
title: Project layout diagnostics and CLI development warning
version: '0.4'
status: approved  # draft | review | approved | superseded
created: '2026-06-24'
author: planner
id: S-003
---

# Project layout diagnostics and CLI development warning

## Purpose

This spec covers the layout-checking and warning behaviour of the S-000 **CLI**
component. AI-team commands discovered malformed repository layouts only when a later
operation failed, and the CLI did not say that its command contract is still evolving,
so missing scaffolds, invalid artifacts, stale guidance and version drift were hard to
diagnose. A read-only `ai-team check-layout` command reports every detected problem
with a suggested correction, and every CLI invocation emits a one-line development
warning, plus a version mismatch warning when the project was set up by a different
CLI version. A correctly initialised and maintained project produces a clean layout
report, and no check changes the filesystem.

## Users and Journeys

| Actor | Goal | Priority | Outcome | Requirements |
|---|---|---|---|---|
| Product owner or agent working in a consuming project | Find out what is wrong with the project's layout and how to fix it, in one run | P1 | `check-layout` lists every finding with its level, path, problem and fix, or reports a clean result | REQ-003–REQ-011 |
| Any CLI user | Know that the CLI is under development and where to report defects | P1 | Every run prints the development warning once | REQ-001 |
| Agent parsing CLI output | Read stdout and `--json` output without warnings mixed in | P1 | Warnings go to stderr only and never change stdout, JSON or exit codes | REQ-012 |
| Product owner or agent whose project was set up by another CLI version | Learn that the scaffolds and the running CLI disagree, and how to align them | P2 | Every run inside the project prints the version mismatch warning with both versions and the fix | REQ-002 |

## Exclusions

What this specification explicitly does NOT cover:

- **Automatic repair.** `check-layout` reports problems and suggested fixes but
  never creates, moves, renames, rewrites, or deletes files or directories.
- **Project-specific command validation.** The command checks that required
  guidance sections exist and contain project guidance; it does not execute or
  prove the correctness of build, test, run, lint, or formatting commands.
- **Non-framework repository content.** Source code, arbitrary documentation,
  and files outside AI-team-managed artifact and tool locations are not subject
  to filename or frontmatter validation.
- **A machine-readable report contract.** The first release requires a stable
  human-readable report. A dedicated `check-layout --json` schema may be added
  separately; existing commands that already support JSON must remain valid.
- **Changing existing command failures.** Other commands are not required to
  invoke `check-layout` or replace their current error messages with layout
  diagnostics.

## Architecture

### Design Principles

- **Observation only.** Every check is read-only and produces diagnostics rather
  than changing repository state (REQ-003).
- **Ordered diagnosis.** Checks run from structural prerequisites to deeper
  content validation so the report distinguishes missing inputs from malformed
  inputs (REQ-005–REQ-010).
- **Current installed contract.** Expected scaffolds, guidance requirements, and
  framework version are evaluated against the running CLI distribution, not a
  network source or a hard-coded historical release (REQ-004).
- **Actionable aggregation.** One invocation reports all issues it can safely
  determine, and every issue identifies the affected path, the violated rule,
  and a suggested correction (REQ-010).
- **Output compatibility.** The warnings appear without corrupting command output
  intended for machine parsing (REQ-012).

### System Diagram

```
CLI invocation
  |
  +--> development warning ---------------------------> stderr
  |
  +--> version mismatch warning (marker version differs) --> stderr
  |
  +--> check-layout
         |
         +--> level 1: expected directories + tracker placement
         +--> level 2: artifact names + frontmatter
         +--> level 3: configured root guidance
         +--> level 4: scaffold/CLI version match
         |
         +--> aggregated issue report ----------------> CLI output
```

### Responsibility Separation

| Component | Responsibility | Notes |
|---|---|---|
| CLI development warning | Tells users the CLI is evolving and where to report defects. | Emitted exactly once for every process invocation, including help, version, successful commands, failed commands, and commands using JSON output. |
| Version mismatch warning | Tells users and agents that the project's scaffolds were written by a different CLI version than the one running. | Emitted once, on stderr, after the development warning. |
| Layout contract resolver | Determines the repository root, configured project directory, expected scaffold directories, and running CLI version. | Consumes `.ai-team.toml` when present and the current installed package contract; does not consult the network. |
| Layout checks | Evaluate the four validation levels without modifying the repository. | Later levels report blocked or missing prerequisites clearly instead of crashing. |
| Issue reporter | Aggregates findings into human-readable CLI output. | Each finding exposes level, path, problem, and suggested fix; a clean project has an unambiguous success result. |

### Alternatives Considered

- **`ai-team init --force` as the suggested fix** for a stale scaffold or a missing
  tool directory. Replaced by `ai-team init --update-skills`, because after CR-005
  `--force` also overwrites the project's own guidance, while `--update-skills`
  updates only the agents and skills.
- **Per-tool export paths in level 1**, with a legacy `.codex/skills/` finding
  (CR-002). Dropped when Claude became the only export target (CR-007, ADR-003).

## Interfaces

**Exposed — `ai-team check-layout` (REQ-003–REQ-011).** Takes no options besides
`--help` and may run from any directory inside the repository. It prints either the
clean result `Layout check passed: no findings.` and exits 0, or one block per
finding and exits 1. Each finding block carries four fields:

- **Contract:** `Level:` (1–4), `Path:` (repository-relative), `Problem:` and
  `Suggested fix:`.

Findings are ordered by level, then by path.

**Exposed — development warning (REQ-001).** **Contract:**
`Warning: ai-team is under development. Please report issues at https://github.com/aurora-firmware/the-ai-team/issues`

**Exposed — version mismatch warning (REQ-002).** **Contract:**
``Warning: .ai-team.toml framework_version <configured> does not match ai-team <running>. Install ai-team <configured>, or run `ai-team init --update-skills` to update the project to <running>.``

**Consumed.**
- `.ai-team.toml`: `[project] dir` and `[init] framework_version`. `[init] tools`
  is never read.
- The installed `ai-team` distribution version and its packaged project scaffold.
- Root `AGENTS.md`.
- The existing artifact filename and frontmatter rules, and the tracker location and
  allowed `status` values from S-006.

## Workflow

```
User invokes any ai-team command
  +--> emit the development warning once on stderr                       (REQ-001)
  +--> if .ai-team.toml records a framework_version that differs from the
  |    running CLI, emit the version mismatch warning once on stderr     (REQ-002)
  +--> continue normal command processing; stdout, JSON and exit code
       unchanged                                                         (REQ-012)

User invokes ai-team check-layout
  ↓
Resolve repository root, .ai-team.toml, and installed version           (REQ-004)
  ↓
Level 1: expected directories and tracker placement                     (REQ-005, REQ-006)
  ↓
Level 2: managed artifact names and frontmatter                         (REQ-007)
  ↓
Level 3: root guidance sections                                         (REQ-008)
  ↓
Level 4: configured framework version equals the running CLI version    (REQ-009)
  ↓
Render every finding with a suggested correction, or the clean result;
exit 1 or 0; never modify the repository                                (REQ-003, REQ-010, REQ-011)
```

Failure paths: a missing or unparsable marker is a finding, and the checks continue
from repository conventions (REQ-004). When a missing or invalid prerequisite prevents
a deeper check, the report says which check could not be completed, and independent
checks still run (REQ-010). A missing project directory blocks only the spec and
decision checks; tracker artifacts are still checked (REQ-007).

## Behavioral Requirements

### REQ-001 — Development warning

Every `ai-team` process invocation SHALL write the development warning from Interfaces
exactly once to stderr, including help, version, successful, failed and `--json`
runs, without making a network request.

#### AC-001.1 — Once per invocation

- **Given:** any `ai-team` command, including `--help` and `--version`
- **When:** it runs
- **Then:** stderr holds the development warning exactly once

**Verification:** Test: `test_every_invocation_emits_development_warning_once` in
`cli/tests/test_cli_bootstrap.py`.

#### AC-001.2 — No network request

- **Given:** network access is blocked
- **When:** any command runs
- **Then:** the warning is printed and no connection is attempted

**Verification:** Test: `test_development_warning_does_not_make_a_network_request` in
`cli/tests/test_cli_bootstrap.py`.

### REQ-002 — Version mismatch warning

WHEN `.ai-team.toml` records an `[init] framework_version` that differs from the
running CLI version under the exact comparison of REQ-009, every `ai-team` invocation
inside that project SHALL write the version mismatch warning from Interfaces once to
stderr, after the development warning. The warning SHALL NOT be written when no marker
is found, when the marker has no `[init]` table or no `framework_version`, when the
marker cannot be parsed, for `ai-team init`, or for `--help` and `--version` runs that
do not resolve a project.

#### AC-002.1 — Different version

- **Given:** a project whose marker records `0.1.0` while the CLI is `0.2.0`
- **When:** any command runs inside it
- **Then:** stderr holds the development warning followed by one version mismatch
  warning naming `0.1.0` and `0.2.0`

**Verification:** Test: `test_warns_once_after_development_warning_when_version_differs`
in `cli/tests/test_version_mismatch_warning.py`.

#### AC-002.2 — Same version or no marker

- **Given:** a project whose marker records the running version, or a directory with
  no marker and no project
- **When:** any command runs there
- **Then:** no version mismatch warning is written

**Verification:** Tests: `test_no_warning_when_marker_version_equals_running_version`,
`test_no_warning_when_no_marker_exists` and `test_no_warning_when_no_project_is_found`
in `cli/tests/test_version_mismatch_warning.py`.

#### AC-002.3 — Unusable marker version

- **Given:** a marker whose `framework_version` is missing, invalid, or unparsable
- **When:** any command runs
- **Then:** no warning is written; the problem is left to level 4 of `check-layout`

**Verification:** Test:
`test_no_warning_when_marker_version_is_missing_invalid_or_unparsable` in
`cli/tests/test_version_mismatch_warning.py`.

#### AC-002.4 — `init` is exempt

- **Given:** a project whose marker records a different version
- **When:** `ai-team init` runs
- **Then:** no version mismatch warning is written

**Verification:** Test: `test_no_warning_for_init_with_mismatched_marker` in
`cli/tests/test_version_mismatch_warning.py`.

### REQ-003 — Read-only check

`check-layout` SHALL NOT create, move, rename, rewrite or delete any file or
directory.

#### AC-003.1 — Repository unchanged

- **Given:** a repository with layout findings
- **When:** `check-layout` runs
- **Then:** every file and directory is unchanged afterwards

**Verification:** Tests:
`test_check_layout_reports_malformed_prerequisite_without_mutating_repository` in
`cli/tests/test_check_layout.py` and
`test_check_layout_returns_ordered_findings_without_modifying_repository` in
`cli/tests/test_layout.py`.

### REQ-004 — Layout resolution

`check-layout` SHALL find the repository root from any directory inside it, read the
project directory and framework version from `.ai-team.toml`, and take the expected
scaffold and current version from the installed CLI distribution without consulting
the network. IF the marker is missing or faulty THEN it SHALL report a finding and
continue with the default conventions.

#### AC-004.1 — Nested directory

- **Given:** an initialised repository
- **When:** `check-layout` runs from a nested directory
- **Then:** it checks the repository from its root

**Verification:** Test: `test_check_layout_resolves_repository_root_from_nested_directory`
in `cli/tests/test_check_layout.py`.

#### AC-004.2 — Valid and faulty markers

- **Given:** a valid marker, or a missing or malformed one
- **When:** the layout is resolved
- **Then:** a valid marker's values are used; a faulty one produces a finding and the
  default conventions are used

**Verification:** Tests:
`test_resolve_layout_reads_valid_local_marker_and_distribution_version` and
`test_resolve_layout_reports_marker_faults_and_uses_safe_conventions` in
`cli/tests/test_layout.py`.

### REQ-005 — Level 1: expected directories

Level 1 SHALL report as a finding each missing directory among the configured project
directory, every directory in the current CLI project scaffold, `.claude/agents/` and
`.claude/skills/`, and a missing `docs/coding_guidelines.md` in the project directory.
It SHALL NOT read `[init] tools` and SHALL NOT report extra directories, including any
Codex folder.

#### AC-005.1 — Missing scaffold directories

- **Given:** a project missing some scaffold directories, with extra directories of
  its own
- **When:** `check-layout` runs
- **Then:** each missing directory is a finding, a missing project directory suggests
  a plain `ai-team init`, a missing agent or skill directory suggests
  `ai-team init --update-skills`, and the extra directories are not reported

**Verification:** Tests:
`test_level_1_reports_every_missing_current_scaffold_directory_and_allows_extra`,
`test_level_1_reports_missing_claude_skills`,
`test_level_1_suggests_plain_init_for_a_missing_project_directory` and
`test_level_1_suggests_update_skills_for_a_missing_tool_directory` in
`cli/tests/test_layout.py`.

#### AC-005.2 — Coding guidelines

- **Given:** a project directory without `docs/coding_guidelines.md`
- **When:** `check-layout` runs
- **Then:** a level 1 finding suggests creating it from the scaffold placeholder; an
  existing file of any content is not a finding

**Verification:** Tests:
`test_level_1_reports_missing_coding_guidelines_with_scaffold_fix` and
`test_level_1_reports_no_finding_for_existing_coding_guidelines_of_any_content` in
`cli/tests/test_layout.py`.

#### AC-005.3 — Tool settings ignored

- **Given:** a marker whose `[init] tools` lists Codex or nothing
- **When:** `check-layout` runs
- **Then:** the Claude directories are expected and nothing is reported about Codex
  folders or `CLAUDE.md`

**Verification:** Tests:
`test_level_1_expects_claude_folders_whatever_init_tools_holds` and
`test_marker_listing_codex_reports_nothing_about_codex_folders_or_claude_md` in
`cli/tests/test_layout.py`.

#### AC-005.4 — Fresh project is clean

- **Given:** a project just created by `ai-team init`
- **When:** level 1 runs
- **Then:** it reports nothing

**Verification:** Test: `test_level_1_reports_nothing_for_a_freshly_initialised_project`
in `cli/tests/test_layout.py`.

### REQ-006 — Level 1: tracker placement

Level 1 SHALL report a tracker folder inside the repository that git does not ignore,
and a legacy `tasks/`, `bugs/`, `change-requests/` or `archive/` folder in the project
directory that holds a markdown file at any depth other than `.gitkeep` or a
`TEMPLATE-*.md` file, with a fix naming the documented migration procedure (S-006).

#### AC-006.1 — Legacy work-item folder

- **Given:** a project directory with `tasks/pending/T-001-old.md`, and an empty
  `bugs/open/` folder
- **When:** `check-layout` runs
- **Then:** one level 1 finding names `tasks/` and the migration procedure; the empty
  `bugs/` folder is not reported

**Verification:** Test: `test_level_1_reports_unmigrated_legacy_work_item_folders` in
`cli/tests/test_layout.py`.

#### AC-006.2 — Unignored tracker

- **Given:** a tracker folder configured inside the repository and not ignored by git
- **When:** `check-layout` runs
- **Then:** a level 1 finding names the tracker folder

**Verification:** Test:
`test_level_1_reports_tracker_inside_repository_that_git_does_not_ignore` in
`cli/tests/test_layout.py`.

### REQ-007 — Level 2: artifact names and frontmatter

Level 2 SHALL report each managed artifact — specs and decisions in the project
directory; tasks, bugs and change requests in the local tracker — whose filename does
not match its type's convention or whose required frontmatter is missing or invalid.
For tasks, bugs and change requests, a `status` outside the allowed values for the
type SHALL be a finding; for specs and decisions only the presence of `status` SHALL
be checked. No folder is compared with `status`. Scaffold placeholders and
non-artifact documentation SHALL be ignored.

#### AC-007.1 — Invalid name or frontmatter

- **Given:** a spec with a malformed filename and a task with an unknown `status`
- **When:** `check-layout` runs
- **Then:** each is a level 2 finding with a fix, and other checks continue

**Verification:** Tests: `test_level_2_reuses_artifact_filename_and_frontmatter_rules`,
`test_level_2_reports_invalid_status_values_with_actionable_fix` and
`test_level_2_reports_malformed_artifact_and_continues_independent_checks` in
`cli/tests/test_layout.py`.

#### AC-007.2 — Ignored files

- **Given:** `.gitkeep` files and non-artifact documentation in managed folders
- **When:** `check-layout` runs
- **Then:** none of them is reported

**Verification:** Test: `test_level_2_ignores_placeholders_and_non_artifact_documentation`
in `cli/tests/test_layout.py`.

#### AC-007.3 — Missing project directory

- **Given:** a repository whose project directory is missing and whose tracker holds
  an invalid task
- **When:** `check-layout` runs
- **Then:** the spec and decision checks are reported as blocked, and the task is
  still reported

**Verification:** Test: `test_missing_project_directory_still_checks_tracker_artifacts`
in `cli/tests/test_layout.py`.

### REQ-008 — Level 3: root guidance

Level 3 SHALL require root `AGENTS.md` with non-placeholder guidance under
`Build and Install`, `Test`, `Run`, `Lint and Format` and `Key Conventions`, and SHALL
report a missing file, a missing section, or a section holding only starter
placeholder text. Root `CLAUDE.md` SHALL be neither required nor read, and no command
in the guidance SHALL be executed.

#### AC-008.1 — Missing or placeholder sections

- **Given:** an `AGENTS.md` with one section missing and one left as the starter
  placeholder
- **When:** `check-layout` runs
- **Then:** each is a level 3 finding, and no guidance command is run

**Verification:** Tests:
`test_level_3_reports_each_missing_or_placeholder_contract_section` and
`test_level_3_reports_missing_section_without_executing_guidance_commands` in
`cli/tests/test_layout.py`.

#### AC-008.2 — `AGENTS.md` only

- **Given:** a marker that lists Codex or no tools
- **When:** level 3 runs
- **Then:** only root `AGENTS.md` is required

**Verification:** Tests:
`test_level_3_requires_only_root_agents_md_when_codex_is_configured` and
`test_level_3_requires_agents_md_even_when_init_tools_is_missing` in
`cli/tests/test_layout.py`.

#### AC-008.3 — Unreadable guidance

- **Given:** an `AGENTS.md` that cannot be read
- **When:** level 3 runs
- **Then:** the guidance check is reported as blocked rather than crashing

**Verification:** Test: `test_level_3_reports_unreadable_guidance_as_blocked` in
`cli/tests/test_layout.py`.

### REQ-009 — Level 4: version alignment

Level 4 SHALL report a finding, with the configured and current values when
available, when `.ai-team.toml` is missing, has no `[init] framework_version`, holds
an invalid version, or holds one not exactly equal to the running `ai-team`
distribution version.

#### AC-009.1 — Mismatch and missing values

- **Given:** a marker with no version, a non-string version, or a version that
  differs from the running one
- **When:** `check-layout` runs
- **Then:** each case is a level 4 finding naming both values where known

**Verification:** Test: `test_level_4_reports_missing_invalid_and_non_exact_versions`
in `cli/tests/test_layout.py`.

#### AC-009.2 — Exact match

- **Given:** a marker recording exactly the running version
- **When:** `check-layout` runs
- **Then:** level 4 reports nothing

**Verification:** Test: `test_level_4_accepts_only_an_exact_version_match` in
`cli/tests/test_layout.py`.

### REQ-010 — Aggregated, ordered report

`check-layout` SHALL report every finding it can determine in one run, each with the
four fields from Interfaces, ordered by level and then path. It SHALL continue with
independent checks after a finding, and WHEN a prerequisite prevents a deeper check
it SHALL report that check as not completed instead of raising an unhandled error.

#### AC-010.1 — All findings in order

- **Given:** layout checks that return findings at several levels and paths, in
  mixed order
- **When:** `check-layout` renders them
- **Then:** every finding is reported in level-then-path order with the four fields

**Verification:** Tests:
`test_check_layout_reports_all_findings_in_level_and_path_order` in
`cli/tests/test_check_layout.py` and `test_check_layout_runs_artifact_and_guidance_levels`
in `cli/tests/test_layout.py`.

#### AC-010.2 — Blocked prerequisite

- **Given:** an artifact file with an invalid text encoding
- **When:** `check-layout` runs
- **Then:** that check is reported as blocked and the guidance check still runs

**Verification:** Test:
`test_invalid_artifact_encoding_is_blocked_and_guidance_check_continues` in
`cli/tests/test_layout.py`.

### REQ-011 — Exit status

`check-layout` SHALL print the clean result and exit 0 when there are no findings, and
SHALL exit 1 after reporting all findings when there is at least one.

#### AC-011.1 — Clean project

- **Given:** a correctly initialised project
- **When:** `check-layout` runs
- **Then:** it prints `Layout check passed: no findings.` and exits 0

**Verification:** Test: `test_check_layout_reports_an_unambiguous_clean_result` in
`cli/tests/test_check_layout.py`.

#### AC-011.2 — Findings

- **Given:** layout checks that return at least one finding
- **When:** `check-layout` runs
- **Then:** it reports every finding and exits 1

**Verification:** Test: `test_check_layout_reports_all_findings_in_level_and_path_order`
in `cli/tests/test_check_layout.py`.

## Quality Requirements

### REQ-012 — Output compatibility

The development and version mismatch warnings SHALL go to stderr only and SHALL NOT
change any command's stdout, `--json` output or exit code.

#### AC-012.1 — JSON output stays valid

- **Given:** a project with a version mismatch
- **When:** a command runs with `--json`
- **Then:** stdout parses as JSON without the warnings, and the exit code is the same
  as without the warnings

**Verification:** Tests: `test_json_command_keeps_warning_out_of_stdout` in
`cli/tests/test_cli_bootstrap.py` and
`test_warning_leaves_stdout_json_and_exit_code_unchanged` in
`cli/tests/test_version_mismatch_warning.py`.

#### AC-012.2 — Version lookup failure

- **Given:** the project layout or the installed version cannot be resolved
- **When:** a command runs
- **Then:** no version mismatch warning is written and the command proceeds normally

**Verification:** Test: `test_lookup_error_is_swallowed_and_command_proceeds` in
`cli/tests/test_version_mismatch_warning.py`.

Performance, accessibility and privacy requirements do not apply: the checks read
only local files, and no run-time target was agreed.

## Configuration Requirements

**Repository marker** (REQ-002, REQ-004, REQ-009)
- **What must exist:** the marker identifying the project directory and the
  scaffold framework version.
- **Where it lives:** root `.ai-team.toml`.
- **Constraints:** the project directory is a usable relative directory name;
  `[init] tools` is not read; the framework version is compared exactly with the
  installed distribution version.
- **Missing-value behaviour:** record an actionable finding and continue every
  check that can still be evaluated safely from repository conventions. The
  version mismatch warning is skipped.

**Root project guidance** (REQ-008)
- **What must exist:** root project guidance.
- **Where it lives:** root `AGENTS.md`.
- **Constraints:** required sections contain project-specific, non-placeholder
  guidance; no command in those sections is executed by `check-layout`.
- **Missing-value behaviour:** record an actionable finding naming the missing
  file or section.

**Issue-reporting destination** (REQ-001)
- **What must exist:** a stable issue-reporting destination for the development
  warning.
- **Where it lives:** the warning contract in this specification.
- **Constraints:** the URL is public, emitted as part of the single warning
  line, and no network request is made.
- **Missing-value behaviour:** there is no fallback URL; changing the destination
  requires a reviewed specification amendment.

## Assumptions and Dependencies

- **The installed distribution carries its own version and project scaffold.**
  REQ-004, REQ-005 and REQ-009 compare against them. If the version cannot be read,
  the mismatch warning is skipped (AC-012.2).
- **S-006 owns the tracker** location, the allowed `status` values and the migration
  procedure that REQ-006 and REQ-007 check against.
- **S-009 owns the project scaffold** and `init`, whose plain and `--update-skills`
  runs are the suggested fixes for missing directories.
- **git is available** to tell whether an in-repository tracker folder is ignored
  (REQ-006).
- **The GitHub issues URL** in the development warning stays valid; it changes only
  by amending this spec.

## Success Criteria

1. `check-layout` on a project just created by `ai-team init` prints the clean result
   and exits 0 (REQ-005, REQ-011).
2. On a repository with problems at every level, one run reports all of them, in
   level-then-path order, each with a suggested fix, and exits 1 (REQ-005–REQ-011).
3. No file or directory changes during any `check-layout` run (REQ-003).
4. Every CLI run writes the development warning once to stderr, and `--json` output
   parses unchanged with either warning present (REQ-001, REQ-012).
5. Inside a project recorded with a different framework version, every command
   except `init` prints the version mismatch warning naming both versions (REQ-002).

## Implementation Order

| Phase | What | Depends On |
|---|---|---|
| 1 | Add the process-wide development warning while preserving all existing stdout and JSON contracts. | Nothing |
| 2 | Establish local layout-contract resolution and the four read-only validation levels with automated coverage. | Phase 1 |
| 3 | Expose `ai-team check-layout` with deterministic reporting, suggested fixes, and clean/issue exit behavior. | Phase 2 |
| 4 | Update user and generated command documentation, then verify the complete CLI test, lint, scaffold-sync, and build checks. | Phases 1-3 |
| 5 | Add the version mismatch warning, and move the level 1 Codex skill path to `.agents/skills/` with the legacy-folder finding (CR-002). | Phases 1-4 |
| 6 | Drop tool selection: level 1 expects the Claude agent and skill directories and loses the legacy Codex finding; level 3 requires root `AGENTS.md` only (CR-007). | Phases 1-5 |

## Open Questions

None.

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-20 | Added the version mismatch warning (Component 5, warning text contract, workflow, configuration). Level 1 now names per-tool export paths: Codex skills move from `.codex/skills/` to `.agents/skills/`, and a legacy framework-owned `.codex/skills/<name>/` folder is a finding. Driven by CR-002. | Only `check-layout` compared `framework_version`, so stale scaffolds and an older CLI gave wrong results without a warning (report #1, #7). Codex discovers repository skills in `.agents/skills/` and is deprecating `.codex/skills/`. | None in flight |
| 2026-10-21 | Level 1 no longer requires lifecycle directories; it requires every project scaffold directory and reports an unignored in-repository tracker and legacy work-item folders that still hold a markdown file other than `.gitkeep` or `TEMPLATE-*.md`. Level 2 validates tasks, bugs, and change requests in the local tracker, checks their `status` against the allowed values (specs and decisions get a presence check only), and drops the folder-versus-status mismatch. | S-006 moved work items to the local tracker and made `status` the only lifecycle state; the levels still described lifecycle folders. The Architect raised this during the CR-003 completion review. Level 1 and the status rules document behaviour already implemented. The consistency review of this amendment found that level 2 stopped all checks when the project directory was missing, which broke the existing rule that independent checks continue. `check-layout` now blocks only the spec and decision checks in that case and keeps checking tracker artifacts. | None in flight |
| 2026-10-24 | Level 1 reports a missing `docs/coding_guidelines.md` in the project directory. Driven by CR-004 item 10. | The project skeleton now scaffolds the file (S-009). | None in flight |
| 2026-10-24 | Level 1 legacy-skill fix and the version mismatch warning text now name `ai-team init --update-skills` instead of `--force`. Driven by CR-005's Architecture Consistency Review. | After CR-005, `--force` also overwrites the project's own guidance; `--update-skills` updates only the agents and skills. | None in flight |
| 2026-10-25 | spec-truth reconciliation — FAIL | CR-005: warning and legacy-fix texts hold; level-1 "rerun ai-team init" fix for missing scaffold directories no longer works on an upgrade (follow-up task with S-009 F5) | none |
| 2026-10-25 | spec-truth reconciliation — PASS | CR-005 re-run: version-mismatch warning, legacy fix (--update-skills) and level-1 directory fixes hold; a plain init upgrade recreates missing project dirs, --update-skills restores tool dirs (T-157) | none |
| 2026-10-25 | spec-truth reconciliation — PASS | CR-005 fifth re-run: version-mismatch warning, level-1 directory fixes and the legacy Codex fix (--update-skills, finding reported only when codex is configured) still hold after T-161 | none |
| 2026-10-25 | Claude is the only export target: the resolver no longer reads `[init] tools`; level 1 always expects `.claude/agents/` and `.claude/skills/` and drops the per-tool table and the legacy Codex skill finding; level 3 and the guidance configuration require root `AGENTS.md` only, with `CLAUDE.md` neither required nor read. Driven by CR-007 and ADR-003. | Codex support was dropped and the generated guidance file is `AGENTS.md`, which current Claude Code reads. | None in flight |
| 2026-10-25 | Restructured to the spec format from PR #51: added Users and Journeys, Alternatives Considered, Interfaces (the `check-layout` output and exit contract and both warning texts), Behavioral Requirements REQ-001–REQ-011 with acceptance scenarios, Quality Requirements REQ-012, Assumptions and Dependencies, Success Criteria and Open Questions; the Components section and the Validation Contracts became requirements. Format restructure only, no scope change, so the version is unchanged. | The validator now rejects approved specs without the new sections. | None |
