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

AI-team commands currently discover malformed repository layouts only when a
later operation fails, and the CLI does not tell users that its command
contract is still evolving. This makes missing scaffolds, invalid artifacts,
stale guidance, and version drift harder to diagnose than necessary. The CLI
will provide a read-only `ai-team check-layout` command that reports every
detected problem with a suggested correction, while every CLI invocation emits
a one-line development warning. A correctly initialized and maintained project
will produce a clean layout report without any filesystem mutation.

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
  diagnostics. The version mismatch warning never changes a command's stdout,
  JSON output, or exit code.

## Architecture

### Design Principles

- **Observation only.** Every check is read-only and produces diagnostics rather
  than changing repository state.
- **Ordered diagnosis.** Checks run from structural prerequisites to deeper
  content validation so the report distinguishes missing inputs from malformed
  inputs.
- **Current installed contract.** Expected scaffolds, guidance requirements, and
  framework version are evaluated against the running CLI distribution, not a
  network source or a hard-coded historical release.
- **Actionable aggregation.** One invocation reports all issues it can safely
  determine, and every issue identifies the affected path, the violated rule,
  and a suggested correction.
- **Output compatibility.** The development warning appears for every CLI
  invocation without corrupting command output intended for machine parsing.

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
| Version mismatch warning | Tells users and agents that the project's scaffolds were written by a different CLI version than the one running. | Emitted once, on stderr, after the development warning, only when `.ai-team.toml` records a `framework_version` that differs from the running CLI. Never changes stdout, JSON output, or the exit code. |
| Layout contract resolver | Determines the repository root, configured project directory, expected scaffold directories, and running CLI version. | Consumes `.ai-team.toml` when present and the current installed package contract; does not consult the network. |
| Layout checks | Evaluate the four validation levels without modifying the repository. | Later levels report blocked or missing prerequisites clearly instead of crashing. |
| Issue reporter | Aggregates findings into human-readable CLI output. | Each finding exposes level, path, problem, and suggested fix; a clean project has an unambiguous success result. |

## Components

### Component 1: Development Warning

**Purpose:** Emit a one-line warning on every `ai-team` invocation.
**Estimated size:** Small.
**Interfaces:** CLI process entry point and stderr; must preserve stdout command contracts.

### Component 2: Layout Contract Resolution

**Purpose:** Resolve the expected repository structure and root guidance from local configuration and the installed CLI.
**Estimated size:** Medium.
**Interfaces:** Project locator, `.ai-team.toml`, packaged scaffold contract, and installed distribution version.

### Component 3: Hierarchical Layout Checks

**Purpose:** Execute the four ordered validation levels and return structured findings without mutation.
**Estimated size:** Medium.
**Interfaces:** Resolved layout contract, existing artifact parsers and validators, and root guidance files.

### Component 4: Layout Report

**Purpose:** Present all detected issues and their suggested fixes in one CLI report.
**Estimated size:** Small.
**Interfaces:** `ai-team check-layout`, hierarchical check findings, terminal output, and process exit status.

### Component 5: Version Mismatch Warning

Amendment 2026-10-20 (CR-002).

**Purpose:** Warn on every invocation inside a project whose recorded framework version differs from the running CLI.
**Estimated size:** Small.
**Interfaces:** CLI process entry point, the `.ai-team.toml` reader shared with level 4, the installed distribution version, and stderr.

## Workflow

```
User invokes any ai-team command
  +--> emit the development warning once on stderr
  +--> if .ai-team.toml records a framework_version that differs from the
  |    running CLI, emit the version mismatch warning once on stderr
  +--> continue normal command processing

User invokes ai-team check-layout
  ↓
Resolve repository root, .ai-team.toml, and installed version
  ↓
Check level 1: all expected project, agent and skill directories exist, and
  the tracker and legacy work-item folders are where S-006 expects them
  ↓
Check level 2: all managed artifact files have valid names and frontmatter
  ↓
Check level 3: relevant root guidance files contain the required sections
  ↓
Check level 4: configured framework version equals the running CLI version
  ↓
Render every finding with a suggested correction; do not modify the repository
```

The command must continue with independent checks after a finding whenever the
required inputs for those checks are still available. When a missing or invalid
prerequisite prevents a deeper check, the report must explain which check could
not be completed rather than raising an unhandled exception.

### Validation Contracts

1. **Level 1 — expected directories and tracker placement.** The repository must contain the
   configured project directory and every directory in the current CLI project
   scaffold, plus the agent directory `.claude/agents/` and the skill directory
   `.claude/skills/`. `[init] tools` is never read (CR-007). Extra directories,
   including any Codex folder, are permitted and are not findings. A missing
   `docs/coding_guidelines.md` in the project directory is a finding; the
   suggested fix is to create it from the scaffold placeholder (CR-004).

   Tasks, bugs, and change requests live in the local tracker (S-006), not in
   the project directory. Two tracker conditions are level 1 findings: a
   tracker folder inside the repository that git does not ignore, and a legacy
   `tasks/`, `bugs/`, `change-requests/`, or `archive/` folder in the project
   directory that still holds a markdown file at any depth, other than
   `.gitkeep` or a `TEMPLATE-*.md` file. The suggested fix for a legacy folder
   names the documented migration procedure.
2. **Level 2 — artifact names and frontmatter.** Every managed artifact file
   must match the filename convention for its artifact type and must have
   syntactically valid, type-appropriate required frontmatter. Managed
   artifacts are specs and decisions in the project directory, and tasks, bugs,
   and change requests in the local tracker. For tasks, bugs, and change
   requests, a frontmatter `status` outside the allowed values for their type
   is a finding. For specs and decisions, `status` is a required field and is
   only checked for presence. The `status` field is the only lifecycle state
   (S-006), so no folder is compared with it. Scaffold
   placeholders such as `.gitkeep` and non-artifact documentation are ignored.
3. **Level 3 — root guidance.** The repository requires root `AGENTS.md`;
   root `CLAUDE.md` is neither required nor read (CR-007). The file must contain non-placeholder
   guidance under `Build and Install`, `Test`, `Run`, `Lint and Format`, and
   `Key Conventions`. Missing files, missing sections, or sections that retain
   only starter-template placeholder text are findings.
4. **Level 4 — version alignment.** `.ai-team.toml` must contain an init
   framework version exactly equal to the running `ai-team` distribution
   version. A missing marker, missing value, invalid value, or mismatch is a
   finding that reports both configured and current values when available.

The command exits successfully when no issues are found and unsuccessfully when
one or more issues are reported. The report order follows validation level,
then path, so repeated runs against unchanged input are deterministic.

**Contract — warning text:** `Warning: ai-team is under development. Please report issues at https://github.com/aurora-firmware/the-ai-team/issues`

**Contract — version mismatch warning text:** ``Warning: .ai-team.toml framework_version <configured> does not match ai-team <running>. Install ai-team <configured>, or run `ai-team init --update-skills` to update the project to <running>.``

The version mismatch warning uses the same exact comparison as level 4. It is
not emitted when no `.ai-team.toml` is found, when the marker has no `[init]`
table or no `framework_version` value, when the marker cannot be parsed, for
`ai-team init`, or for `--help` and `--version` runs that do not resolve a
project. Those marker cases remain level 4 findings.

## Configuration Requirements

- **What must exist:** The repository marker identifying the project directory
  and scaffold framework version.
  **Where it lives:** Root `.ai-team.toml`.
  **Constraints:** The project directory is a usable relative directory name;
  `[init] tools` is not read; the framework version is
  compared exactly with the installed distribution version, both by level 4
  and by the version mismatch warning.
  **Missing-value behaviour:** Record an actionable finding and continue every
  check that can still be evaluated safely from repository conventions. The
  version mismatch warning is skipped.

- **What must exist:** Root project guidance.
  **Where it lives:** Root `AGENTS.md`.
  **Constraints:** Required sections contain project-specific, non-placeholder
  guidance; no command in those sections is executed by `check-layout`.
  **Missing-value behaviour:** Record an actionable finding naming the missing
  file or section.

- **What must exist:** A stable issue-reporting destination for the development
  warning.
  **Where it lives:** The CLI warning contract in this specification.
  **Constraints:** The URL is public, emitted as part of the single warning
  line, and no network request is made.
  **Missing-value behaviour:** There is no fallback URL; changing the destination
  requires a reviewed specification amendment.

## Implementation Order

| Phase | What | Depends On |
|---|---|---|
| 1 | Add the process-wide development warning while preserving all existing stdout and JSON contracts. | Nothing |
| 2 | Establish local layout-contract resolution and the four read-only validation levels with automated coverage. | Phase 1 |
| 3 | Expose `ai-team check-layout` with deterministic reporting, suggested fixes, and clean/issue exit behavior. | Phase 2 |
| 4 | Update user and generated command documentation, then verify the complete CLI test, lint, scaffold-sync, and build checks. | Phases 1-3 |
| 5 | Add the version mismatch warning, and move the level 1 Codex skill path to `.agents/skills/` with the legacy-folder finding (CR-002). | Phases 1-4 |
| 6 | Drop tool selection: level 1 expects the Claude agent and skill directories and loses the legacy Codex finding; level 3 requires root `AGENTS.md` only (CR-007). | Phases 1-5 |

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
