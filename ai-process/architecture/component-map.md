---
title: "Component Map"
status: approved
created: 2026-03-10
---

# Component Map

This document maps the ai-process roles, procedures, processes, and gates to their implementation files where applicable.

## Roles

| Role | Purpose | Procedures Used | Receives From | Hands Off To | Implementation |
|---|---|---|---|---|---|
| Planner | Creates specifications with the human, then decomposes approved specifications into executable tasks; reads S-000 (the system overview) at session start | New System Overview; Brainstorm; Spec Breakdown | Human | Human (approval), Local tracker (`planned` → `pending` tasks), Architect (Gate 2; Architecture Consistency Review for created/changed specs and change-requests) | `.claude/agents/planner.md` |
| Architect | Owns structural review: Gate 2 preflight, architectural consistency, escalation analysis, and ADR decisions; reads S-000 (the system overview) at session start, checking specs against it | Spec Breakdown Review; Architecture Consistency Review; Escalation Review; New ADR | Planner (Gate 2; Architecture Consistency Review for created/changed specs and change-requests), Any blocked role | Planner (revision requests, consistency findings), Requesting role (directives), Human (escalation), Decision Log | `.claude/agents/architect.md` |
| Developer | Implements tasks and fixes bugs; diagnoses bugs before changing production code | TDD; Debug | Development Loop or Bug-Fix Loop | Reviewer | `.claude/agents/developer.md` |
| Reviewer | Reviews task acceptance, bug diagnosis, targeted fixes, verification evidence, and code quality | Code Review | Developer (via Development Loop or Bug-Fix Loop) | Development Loop or Bug-Fix Loop (verdict in task or bug file) | `.claude/agents/reviewer.md` |
| Integrator | Resolves merge conflicts; supports task and bug integration into target branches | Integrate; Merge Conflicts | Development Loop or Bug-Fix Loop (integration), Human (manual merges), Integrate (conflicts) | `dev-agent` or preserved task branch | `.claude/agents/integrator.md` |

## Procedures

| Procedure | Purpose | Used By | Implementation |
|---|---|---|---|
| New System Overview | Create the S-000 system overview that later specs are checked against; produces only the project bootstrap tasks, never solution tasks | Planner | `.claude/skills/new-system-overview/SKILL.md` |
| Project Bootstrap | Plan the bootstrap tasks of an approved S-000: decisions and architecture documents, environment configuration, coding guidelines, project guidance, and the README description | Planner | `.claude/skills/spec-breakdown/SKILL.md` (run on S-000) |
| Brainstorm | Explore the request, alternatives, constraints, and prior decisions before writing a specification | Planner | `.claude/skills/brainstorm/SKILL.md` |
| Change Request (intake) | Capture smaller desired changes and possible spec amendments without the full brainstorm-to-spec flow; produces tasks and amendments as needed | Planner, Human | `ai-team change-request new`; template at `cli/src/ai_team/templates/change-request.md`; artifacts stored in the local tracker |
| Spec Breakdown | Decompose an approved specification into atomic tasks with dependencies, acceptance criteria, and verification | Planner | `.claude/skills/spec-breakdown/SKILL.md` |
| Spec Breakdown Review | Validate task dependencies, file conflict risk, decision-record consistency, atomicity, and implementation readiness (evaluates Gate 2) | Architect | `.claude/skills/spec-breakdown-review/SKILL.md` |
| Architecture Consistency Review | Check a created or changed spec, ADR, or change-request against every approved spec and accepted ADR, and route corrections for any drift (spec amendments, or follow-up tasks when the spec is right and the work falls short) | Architect | `.claude/skills/architecture-consistency-review/SKILL.md` |
| Evidence Before Claims | Require a fresh command and its actual output before any completion claim or `Evidence:` entry | All roles | `.claude/skills/evidence-before-claims/SKILL.md` |
| Using AI Team | Match the situation to a skill and check gate preconditions before any other action | Main session (human-facing entry point) | `.claude/skills/using-ai-team/SKILL.md` |
| TDD | Write a failing test, verify failure, implement the minimal change, verify pass, and refactor; for a design-review task, check the changed text against the listed references and record the review | Developer | `.claude/skills/tdd/SKILL.md` |
| Debug | Reproduce or confirm a defect, gather evidence, isolate the fault, record a root-cause hypothesis, then permit fixing | Developer | `.claude/skills/debug/SKILL.md` |
| Code Review | Review tasks for acceptance compliance and bugs for diagnosis, root-cause fit, verification, and code quality | Reviewer | `.claude/skills/code-review/SKILL.md` |
| Integrate | Merge task or bug branches, run pre- and post-merge tests, promote completed work, and file regression bugs on failure | Development Loop, Bug-Fix Loop, Integrator | `.claude/skills/integrate/SKILL.md` |
| Merge Conflicts | Resolve git merge conflicts while preserving both sides' intent | Integrator | `.claude/skills/merge-conflicts/SKILL.md` |
| Escalation Review | Analyse blocked work after role self-recovery and issue guidance or escalate to human | Architect | `.claude/skills/escalation-review/SKILL.md` |
| New Specification | Create a specification document from the standard template | Planner | `.claude/skills/new-spec/SKILL.md` |
| New Task | Create a task in the local tracker from the standard template | Planner | `.claude/skills/new-task/SKILL.md` |
| New Bug | Create an evidence-rich `open` bug report in the local tracker from the standard template | Human, Developer, Reviewer, Integrate | `.claude/skills/new-bug/SKILL.md` |
| New ADR | Create an architecture decision record in `ai-team/decisions/` from the standard template | Architect | `.claude/skills/new-adr/SKILL.md` |
| Status Report | Summarize specifications, tasks, bugs, decisions, and integration state for Gate 5, on demand | Human | `.claude/skills/status-report/SKILL.md` |

## Processes

| Process | Purpose | Started By | Implementation |
|---|---|---|---|
| Development Loop | Autonomous task loop across `pending` tasks: Developer → Reviewer → Integration until the queue is empty, blocked, or escalated | Human after Gate 2 passes | `.claude/skills/dev-loop/SKILL.md` |
| Bug-Fix Loop | Diagnosis-first bug loop across `open` bugs: Debug → implementation → Reviewer → Integrate until the queue is empty or escalated | Human when open bugs need resolution | `.claude/skills/bug-loop/SKILL.md` |

## Gates

| Gate | Purpose | Evaluator |
|---|---|---|
| Gate 1: Specification Approval | Confirm the specification is complete and aligned with the feature request | Human |
| Gate 2: Task Plan Preflight | Confirm the task plan is complete, conflict-aware, and implementation-ready | Architect |
| Gate 3: Code Review | Confirm task implementations satisfy acceptance criteria and bug fixes include sound diagnosis, targeted fix, verification, and quality | Reviewer |
| Gate 4: Integration Tests | Confirm merged task or bug work does not regress the target branch | Integrate |
| Gate 5: Final Merge Sign-off | Confirm completed work matches spec intent before `dev-agent` → `main` | Human |

## Documents and Directories

| Component | Type | Purpose | Location |
|---|---|---|---|
| Specifications | Directory | Feature and system specs | `ai-team/specs/` |
| Local Tracker | Directory outside version control | Tasks, bugs, and change-requests; lifecycle state is the frontmatter `status` field; one tracker per repository, shared by all worktrees | `[tracker] dir` in `.ai-team.toml` (default `.ai-team/tracker/`) |
| Decision Log | Directory | Architecture decision records | `ai-team/decisions/` |
| Root Guidance Files | Files | Project-level command documentation for autonomous agents; `## Test` section is the canonical home for the baseline test command consumed by `dev-loop` | `AGENTS.md` at the project root; scaffolded by `ai-team init` from templates in `cli/src/ai_team/init/sources/root/` |
| Project Guidance Files | Files | Artifact directory orientation for agents; always generated by `ai-team init` | `ai-team/AGENTS.md`; scaffolded from `cli/src/ai_team/init/sources/project/` |
| Templates | CLI package assets | Reusable document formats | `cli/src/ai_team/templates/` |
| Process Docs | Directory | Workflow and procedure definitions (spec layer only — not exported by `ai-team init`) | `ai-process/processes/` |
| Guidelines | Directory | Standards and checklists (spec layer only — not exported by `ai-team init`) | `ai-process/guidelines/` |
| Architecture Docs | Directory | System design documentation (spec layer only — not exported by `ai-team init`) | `ai-process/architecture/` |
| Action Procedures | Directory | Automation for document creation and status reporting | `.claude/skills/` (`disable-model-invocation: true` only for human-only actions that no other skill invokes) |
| CLI Scaffold Sources | Package assets | Authoritative source for the Claude agents and skills (`.claude/agents/`, `.claude/skills/`) and templates exported by `ai-team init`; nothing is exported for other agent tools | `cli/src/ai_team/init/sources/` |

## CLI Command Mapping

Action skills that create or report on project artifacts invoke `ai-team` CLI commands. The table below maps each action skill to the command(s) it calls.

| Skill | CLI Command(s) | Purpose |
|---|---|---|
| `new-spec` | `ai-team spec new` | Create a new specification document |
| `new-system-overview` | `ai-team spec new --overview` | Create the S-000 system overview specification |
| `new-task` | `ai-team task new` | Create a new task in the local tracker |
| `new-bug` | `ai-team bug new` | Create a new bug report in the local tracker |
| `new-adr` | `ai-team adr new` | Create a new architecture decision record in `ai-team/decisions/` |
| `status-report` | `ai-team status`, `ai-team report` | Generate inline Gate 5 summary and full progress report |
| *(change-request intake)* | `ai-team change-request new` | Create a change-request in the local tracker |

## Interaction Diagram

```
Human ←──→ Planner ──→ Local Tracker  ──→ Development Loop ──→ Developer ──→ Reviewer ──→ Integration ──→ Human
   │          │                                  │                  ↑             │              ↑
   │          ↓                                  │                  │             │              │
   │     Architect ←──────── escalation ─────────┴──────────────────┴─────────────┘              │
   │          │                                                                                 │
   │          ↓                                                                                 │
   │     Decision Log                                                                           │
   │                                                                                            │
   └──────→ Local Tracker ──→ Bug-Fix Loop ──→ Debug ──→ Developer ──→ Reviewer ─┘
```
