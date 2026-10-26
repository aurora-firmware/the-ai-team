---
title: System Overview Spec (S-000)
version: '0.4'
status: approved  # draft | review | approved | superseded
created: '2026-10-19'
author: planner
id: S-007
---

# System Overview Spec (S-000)

## Purpose

This spec covers the system-overview support in the S-000 **Team definition**,
**Generators** and **CLI** components. A project started with the AI team had no
document above its specs, so every spec re-invented why the project exists and how it
is split, specs overlapped, left gaps or fixed interfaces before the component
boundaries were settled, and a new session had no single place to learn what the
project is for. Each project can have one canonical, plain-language overview spec,
**S-000**, that states its purpose, users, pain points, use cases and solution and
breaks the solution into components with explicit boundaries, without defining
technology or interfaces. The framework provides the template, the authoring
contract, the writing procedure and the CLI support for it, and every later spec names
the S-000 component it covers.

## Users and Journeys

| Actor | Goal | Priority | Outcome | Requirements |
|---|---|---|---|---|
| Product owner starting a project, with the Planner | Write down what the project is for and how it divides before any feature spec | P1 | `ai-team spec new --overview` creates S-000 from its template, and the `new-system-overview` skill guides writing it | REQ-001, REQ-005, REQ-006, REQ-008 |
| Product owner or agent in a project with no S-000 | Learn that the overview is missing and how to create it | P2 | CLI commands print a one-line hint on stderr | REQ-004 |
| Planner creating the project bootstrap tasks | Create tasks whose source is S-000 | P1 | `task new` and `validate` accept S-000 as a task's spec | REQ-003 |
| Planner writing a feature spec | Place the spec inside the decomposition | P1 | The feature spec template asks the Purpose to name its S-000 component | REQ-007 |
| Team adopting an existing project | Write S-000 from existing specs, decisions and code | P2 | The `new-system-overview` skill has a brownfield path | REQ-008 |

## Exclusions

- **A separate artifact type or folder for the overview.** S-000 is a spec, so it reuses spec numbering, status, Gate 1 approval, the Amendment Log and the architecture consistency review.
- **A `component` field in spec frontmatter, or a component-to-spec mapping.** The ID `0` is the only marker that a spec is the project overview. A spec names the S-000 component it covers in its Purpose, in prose.
- **Progress tracking inside S-000.** S-000 does not record which components are specified, in progress or done. Pending and completed work is read from specs and tasks.
- **Technology choices and interface contracts in S-000.** S-000 may ask the technology questions, in a development-infrastructure component's Decisions needed; the answers belong in the project's internal development documentation, later specs and ADRs.
- **Mandatory S-000 in existing projects.** Projects that already have specs are not required to create S-000.
- **A switch to turn the missing-S-000 hint off.** The hint is always on.
- **Process rules for S-000.** Session-start reading, Gate 1 criteria, the completion review, the planning-branch merge, the project bootstrap and the brownfield findings are owned by the agents, skills and `ai-process/` documents listed under Responsibility Separation; this spec does not restate them.

## Architecture

### Design Principles

- S-000 must stay abstract enough that it rarely changes: it describes what the project is for and how it is divided, not how any part works.
- S-000 must be readable by a non-technical stakeholder; it uses plain language and names no technology. It may ask which technology to use; it never answers.
- Every rule that treats S-000 differently from other specs must be keyed on the ID `S-000` alone (REQ-001–REQ-004).
- S-000 produces only the project bootstrap tasks for its development-infrastructure components. Feature work always comes from a feature spec, never from S-000.
- Each rule has one owner: the S-000 content contract lives in the spec authoring guide, procedures live in skills, process rules in agents and `ai-process/`, and enforcement lives in the CLI.

### Responsibility Separation

| Component | Responsibility | Owner |
|---|---|---|
| S-000 template | Fixed section structure for the overview | `cli/src/ai_team/templates/system-overview.md` |
| S-000 content contract | Sections, component definition and checks, groups, Decisions needed, Users scope, S-000 versus spec boundary | `guides/spec-authoring-guide.md` |
| Writing procedure | Writing S-000 with the product owner, greenfield or brownfield; completion after Gate 1; brownfield change request; hand-over to the bootstrap | `new-system-overview` skill |
| Feature spec template | Purpose names the S-000 component; system-wide structure stays in S-000 | `cli/src/ai_team/templates/spec.md` and the `new-spec` skill |
| CLI | Creates S-000, protects its ID, accepts bootstrap tasks from S-000, hints when S-000 is missing | `ai-team spec new`, `task new`, `validate` and the hint |
| Project bootstrap | Tasks from S-000 that answer the Decisions needed and set up the environment and internal documentation, including the default `docs/development/` location | `spec-breakdown` skill, Gate 2 in `ai-process/processes/quality-gates.md` |
| Session-start reading | Planner and Architect read S-000 first when it exists | Planner and Architect agent descriptions |
| Overview suggestions | Suggest the overview when S-000 does not exist | `using-ai-team` and `brainstorm` skills |
| Consistency check | A new or changed spec stays within S-000's components | `architecture-consistency-review` skill |
| Gate 1 and completion review | S-000 pass criteria; S-000 excluded from the pre-Gate-5 completion review | `ai-process/processes/quality-gates.md` |
| Planning-branch merge | S-000's planning branch merges after Gate 1 | `git-conventions` skill and `ai-process/guidelines/git-conventions.md` |

### Alternatives Considered

- **A separate artifact type or folder for the overview.** Rejected: as a spec, S-000
  reuses spec numbering, status, Gate 1, the Amendment Log and the consistency review
  without new machinery.
- **A `component` field in spec frontmatter.** Rejected in favour of the Purpose
  naming the component in prose, so no mapping has to be kept in step.
- **A bootstrap spec.** Rejected: the bootstrap tasks come straight from S-000, since
  they only answer the questions S-000 asks.

## Interfaces

**Exposed — `ai-team spec new --overview` (REQ-001).** Creates
`<specs>/S-000-<slug>.md` from the system-overview template, with the usual spec
frontmatter and ID `S-000`. The title argument is optional and defaults to
`System Overview`. With `--json` it prints the `id` and `path`. It refuses, exiting
non-zero, when an S-000 already exists in the specs folder or its archive.

**Exposed — the S-000 template (REQ-005).** **Contract:** the seven top-level sections
in this order: Purpose, Users, Pain points, Use cases, Solution overview, Components,
Project exclusions; then the Amendment Log. Their content rules are owned by the spec
authoring guide (REQ-006).

**Exposed — missing-S-000 hint (REQ-004).** **Contract:** one line on stderr:
``Hint: this project has no system overview (S-000). Create one with `ai-team spec new --overview`, or ask your agent to use the new-system-overview skill.``

**Consumed.**
- The spec ID allocator, which skips `S-000` for normal specs.
- The spec archive, searched for an existing S-000.

## Workflow

```
Product owner describes the project
  ↓
Planner writes S-000 with the product owner (new-system-overview)          (REQ-001, REQ-008)
  ↓
Architect reviews S-000 for internal consistency
  ↓
★ Product owner approves S-000 (Gate 1)
  ↓
Planner sets S-000 to approved and merges its planning branch
  ↓
Brownfield only: Planner proposes a change request aligning existing specs with S-000
  ↓
Planner creates the project bootstrap tasks from S-000                     (REQ-003)
  ↓
★ Architect checks the bootstrap task plan (Gate 2) → development loop
  ↓
Planner writes one spec per component or slice, naming its component      (REQ-007)
  ↓
Architect checks each spec against S-000 (consistency review)
  ↓
★ Product owner approves each spec (Gate 1) → breakdown → tasks
```

The owners of each step are listed under Responsibility Separation. Failure paths:
`spec new --overview` refuses a second S-000, including one in the archive (REQ-001).
While no S-000 exists, the CLI keeps hinting but never blocks (REQ-004).

## Behavioral Requirements

### REQ-001 — Creating S-000

`ai-team spec new --overview` SHALL create S-000 from the system-overview template in
the specs folder with ID `S-000`, and SHALL refuse when an S-000 already exists in the
specs folder or its archive.

#### AC-001.1 — Creation

- **Given:** a project with no S-000
- **When:** `ai-team spec new --overview --json` runs
- **Then:** `S-000-system-overview.md` is created from the system-overview template
  with title `System Overview`, and the JSON holds its `id` and `path`

**Verification:** Tests:
`test_spec_new_overview_creates_s_000_from_system_overview_template`,
`test_spec_new_overview_json_emits_id_and_path` and
`test_spec_new_overview_defaults_title_to_system_overview` in
`cli/tests/test_spec_new.py`.

#### AC-001.2 — Duplicate refused

- **Given:** an S-000 in the specs folder, or one in the spec archive
- **When:** `ai-team spec new --overview` runs
- **Then:** it fails and creates nothing

**Verification:** Tests: `test_spec_new_overview_refuses_when_s_000_exists_in_specs`
and `test_spec_new_overview_refuses_when_s_000_exists_in_archive` in
`cli/tests/test_spec_new.py`.

### REQ-002 — Normal spec numbering

Normal spec creation SHALL start at `S-001` and SHALL never allocate `S-000`.

#### AC-002.1 — S-000 is skipped

- **Given:** a project whose only spec is S-000
- **When:** `ai-team spec new "Feature"` runs
- **Then:** the new spec is `S-001`

**Verification:** Tests: `test_spec_new_allocates_s_001_when_s_000_is_the_only_spec` in
`cli/tests/test_spec_new.py` and `test_next_spec_id_returns_s_001_when_s_000_is_the_only_spec`
in `cli/tests/test_ids.py`.

### REQ-003 — Tasks from S-000

`ai-team task new` SHALL accept `S-000` as a task's source spec, and `ai-team validate`
SHALL NOT report a task whose spec is S-000, under any form of the reference.

#### AC-003.1 — Bootstrap task accepted

- **Given:** a project with an S-000
- **When:** `ai-team task new "Set up CI" --spec S-000` runs and then `validate` runs
- **Then:** the task is created and `validate` reports nothing for it

**Verification:** Tests: `test_task_new_creates_task_with_overview_spec_and_json_output`
in `cli/tests/test_task_new.py`, and `test_validate_reports_no_finding_for_task_whose_spec_is_s000`
and `test_validate_reports_no_finding_for_task_whose_spec_reaches_s000_by_alias` in
`cli/tests/test_validate.py`.

### REQ-004 — Missing-S-000 hint

WHILE no S-000 exists in the specs folder or its archive, `validate`, `status`,
`report` and every artifact-creating command (`spec new`, `task new`, `bug new`,
`adr new`, `change-request new`) SHALL write the hint from Interfaces once to stderr.
The hint SHALL NOT change stdout or the exit code, SHALL NOT be configurable, and
SHALL NOT be written by `spec new --overview` or once S-000 exists. A failure while
checking for S-000 SHALL NOT change the command's result.

#### AC-004.1 — Hint on stderr only

- **Given:** a project with no S-000
- **When:** `validate --json`, `status --json`, `report`, `spec new`, `adr new` or a
  tracker `new` command runs
- **Then:** stderr holds the hint; stdout holds only the command's own output

**Verification:** Tests: the `*_prints_hint_to_stderr_*` tests,
`test_hint_is_printed_even_when_config_file_is_present` and
`test_tracker_new_commands_print_hint_to_stderr_when_no_s_000` in
`cli/tests/test_missing_overview_hint.py`.

#### AC-004.2 — No hint when S-000 exists or is being created

- **Given:** a project with an S-000, or a project running `spec new --overview`
- **When:** the commands above run
- **Then:** no hint is written

**Verification:** Tests: the `*_prints_no_hint_*` tests and
`test_spec_new_overview_prints_no_hint` in `cli/tests/test_missing_overview_hint.py`.

#### AC-004.3 — Exit codes and errors unchanged

- **Given:** a project with no S-000 and a validation error, or an S-000 check that
  raises
- **When:** `validate` runs
- **Then:** it keeps its error exit code and stdout; a failing check prints no hint
  and changes nothing

**Verification:** Tests: `test_validate_keeps_error_exit_code_when_hint_is_printed`,
`test_validate_keeps_stdout_and_exit_code_when_existence_check_raises` and
`test_hint_missing_overview_swallows_existence_check_errors` in
`cli/tests/test_missing_overview_hint.py`.

### REQ-005 — S-000 template

The framework SHALL ship a system-overview template, separate from the feature spec
template, with the seven sections from Interfaces in order; a Components section
split into `### Solution` and `### Development infrastructure`, each with an example
component showing its name, responsibility, boundary and the components it works
with, the infrastructure example adding **Decisions needed**; and none of the
feature-spec sections.

#### AC-005.1 — Template shape

- **Given:** `cli/src/ai_team/templates/system-overview.md`
- **When:** its headings are read
- **Then:** the seven sections appear in order, Solution comes before Development
  infrastructure, the examples show every component field and the infrastructure one
  has Decisions needed, and no feature-spec heading appears

**Verification:** Tests: `test_system_overview_template_has_the_s000_sections_in_order`,
`test_system_overview_template_omits_feature_spec_heading` and
`test_system_overview_template_shows_one_component_example_with_all_fields` in
`cli/tests/test_templates.py`.

### REQ-006 — Content contract in the guide

The spec authoring guide SHALL own the S-000 content contract: the seven sections, the
component entry fields, the definition of a component and its three checks, the
Solution and Development infrastructure groups, the Decisions needed field, the Users
scope, the content S-000 excludes, and the S-000 versus spec boundary.

#### AC-006.1 — Guide states the contract

- **Given:** `guides/spec-authoring-guide.md`
- **When:** its S-000 section is read
- **Then:** it states each element above

**Verification:** Inspection of the guide's S-000 section.

### REQ-007 — Feature specs name their component

The feature spec template SHALL tell the author to name the S-000 component the spec
covers in its Purpose and to leave system-wide structure to S-000.

#### AC-007.1 — Template comment

- **Given:** `cli/src/ai_team/templates/spec.md`
- **When:** its Purpose comment is read
- **Then:** it says the Purpose names the S-000 component and system-wide structure
  lives in S-000

**Verification:** Inspection of the spec template's Purpose comment.

### REQ-008 — Writing procedure

The framework SHALL ship a `new-system-overview` skill that creates S-000 with the CLI
command from REQ-001 and guides writing it with the product owner, for a new project and, from
existing specs, decisions and code, for an existing one. The procedure is owned by the
skill.

#### AC-008.1 — Skill present and routed

- **Given:** the skill sources
- **When:** the `new-system-overview` skill and the `using-ai-team` dispatch table are
  read
- **Then:** the skill runs `ai-team spec new --overview`, names the seven sections,
  has a brownfield section, and the dispatch table names it

**Verification:** Inspection of the `new-system-overview` skill and the `using-ai-team` dispatch table.

## Quality Requirements

None. The behaviour is local file creation and an advisory hint; no security, privacy,
accessibility or performance target applies.

## Configuration Requirements

None. The hint is always on and S-000 is found by its ID; no setting is involved.

## Assumptions and Dependencies

- **The spec ID allocator and archive lookup** are shared with normal specs; REQ-001
  and REQ-002 rely on them treating `S-000` by ID alone.
- **The owners under Responsibility Separation** keep the S-000 process rules. When
  one changes, the owner changes; this spec changes only if the CLI, template or
  guide contract changes.

## Success Criteria

1. In a project with no specs, `ai-team spec new --overview` creates
   `S-000-system-overview.md` with the seven sections, and a second run fails
   (REQ-001, REQ-005).
2. After S-000 exists, `ai-team spec new "Feature"` creates `S-001` (REQ-002).
3. A task created with `--spec S-000` passes `ai-team validate` (REQ-003).
4. Without S-000, every listed command prints the hint on stderr with unchanged stdout
   and exit code; with S-000, none does (REQ-004).
5. The system-overview template tests in `cli/tests/test_templates.py` pass (REQ-005), and
   inspection finds the guide, the spec template and the skill as REQ-006–REQ-008 state.

## Implementation Order

| Phase | What | Depends On |
|---|---|---|
| 1 | Authoring guide: S-000 content contract and S-000 versus spec boundary | Nothing |
| 2 | S-000 template, `ai-team spec new` creation path, ID and duplicate protection | Phase 1 |
| 3 | `new-system-overview` skill, including the brownfield path; CLI acceptance of tasks from S-000; missing-S-000 hints | Phase 2 |
| 4 | Feature spec template and the process owners' S-000 rules | Phases 1–3 |
| 5 | Regenerate scaffolds and CLI docs; update the component map | Phase 4 |

## Open Questions

None.

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-20 | Requirement 3: a design-review task may name S-000 as a reference; the Developer and Reviewer read it when they run or check that review, not at session start. Driven by CR-003 §2 and Architecture Consistency Review finding F2. | CR-003 introduces design-review verification against the source spec, accepted ADRs and S-000, which the session-start rule for Developer and Reviewer did not allow for. | None in flight |
| 2026-10-24 | Content contract: component definition and checks, solution and development-infrastructure groups, Decisions needed, Users scope. Exclusions and Design Principles: S-000 asks technology questions and produces only bootstrap tasks. Workflow, Requirements 2, 9 and 10 restated; Requirements 11–14 added (post-Gate-1 completion, project bootstrap, internal development documentation, brownfield findings). Brownfield adoption: components from use cases; findings become a CR. Driven by CR-004 items 1–9. | Writing this repository's S-000 needed a component model and a post-approval step the contract did not define (CR-004). | None in flight |
| 2026-10-24 | Workflow: the brownfield change request comes before the bootstrap tasks, matching `new-system-overview`; Requirement 11 reworded ("S-000's own planning branch does not wait for Gate 2"). In-flight CR-004 amendment from the PR #48 review. | The diagram and the skill gave different orders, and "S-000 has no Gate 2" read as contradicting the bootstrap plan's Gate 2. | None in flight |
| 2026-10-26 | Restructured to the spec format from PR #51, with three scope changes decided by the product owner. (1) Removed the backward-compatibility promises: old requirement 8's "existing approved specs stay valid unchanged", the content contract's "an S-000 with a flat Components list stays valid", and "existing specs are not rewritten to the new template" from the exclusions. (2) The S-000 content contract is no longer restated; REQ-006 makes the spec authoring guide its owner. (3) Process rules owned elsewhere (old requirements 3, 4, 6, 7, 9–14 and the Brownfield adoption section) are no longer restated; Responsibility Separation names their owners. New REQ-001–REQ-008 cover the CLI, template, guide, feature template and skill. Version bumped to 0.3. | The validator rejects approved specs without the new sections; the no-backward-compatibility policy; single ownership of shared rules. | None; the flat-list promise is removed from the guide, the system-overview template, and the `new-system-overview` and `architecture-consistency-review` skills on the same branch |
| 2026-10-26 | AC-005.1 drops the removed `test_t078_s000_content_contract.py` test; AC-006.1, AC-007.1 and AC-008.1 are verified by inspection; Success Criterion 5 follows. | Tests that assert the wording of skills, process documents, guides or user docs were removed; under the spec authoring guide's Verification methods such criteria are verified by inspection. | None |
