# The AI Team Definition

A reusable operating framework for projects developed by AI agent teams.

## What This Is

The AI Team Definition is a reusable framework that lets a team of AI agents build and maintain software in a project autonomously.
It defines the rules the agents follow (how work is planned, implemented, reviewed, integrated and approved) and installs those rules into any project in one step, together with the agent roles and procedures that carry them out and the tooling that supports them.
With the framework in place, the product owner hands feature work and bug fixes to the agents and gets back changes that have been tested, reviewed and integrated, along with a clear record of what was decided and why.

The product owner stays in control of two decisions: approving a specification before it is broken into tasks, and approving integrated work before it reaches the main line.
Everything between those gates runs without the product owner, and the agents stop and ask only when the rules say they must.

ai-team is made of four components (see [S-000](docs/ai-team/specs/S-000-system-overview.md)):

- **Team definition**: the process rules in `ai-process/`, and the agent roles and procedures (skills) that carry them out, authored under `cli/src/ai_team/init/sources/`.
- **Generators**: produce every file handed to a project: the exported agents and skills, the artifact layout, starter project guidance (`AGENTS.md`), and the fixed artifact templates.
- **CLI** (`cli/`): the `ai-team` command that people and agents use to install and update the framework, check a project's layout, and create, validate and move specs, tasks, bugs, ADRs and change-requests through their lifecycle, with tasks, bugs and change-requests kept in a local tracker outside the project's history.
- **End-user documentation**: how to install, set up, customise and use ai-team (`cli/docs/`, `guides/`).

When a project runs `ai-team init`, the CLI writes the project skeleton, the exported agents and skills, `.ai-team.toml`, and optionally starter root guidance into that project's repository. The `.claude/` folder is **per-project local configuration**: it is not part of this framework's deliverable and, in this repository, is git-ignored and used only when running agents *inside this repo*.

Developer documentation for working on ai-team itself is in [`docs/development/`](docs/development/AGENTS.md).

## The ai-process

The ai-process lives in `ai-process/` and has three layers:

| Layer | Folder | Defines |
|---|---|---|
| Workflows | `ai-process/processes/` | How work flows from idea to shipped feature: the full lifecycle of specs, tasks, bugs, and decisions, plus quality gates and escalation procedures |
| Standards | `ai-process/guidelines/` | How code, git history, and documents must be written: coding standards, review checklists, markdown conventions |
| Structure | `ai-process/architecture/` | How the AI team itself is organized: agent roles, skill boundaries, component responsibilities |

Everything in `ai-process/` is the **specification layer** — the authoritative source of truth.
The agents and skills authored under `cli/src/ai_team/init/sources/` are the **implementation layer** — they must faithfully execute what the ai-process defines, and they are what `ai-team init` exports into a target project.

## Process Overview

```text
                         +----------------------+
                         |    Product Owner     |
                         +----------+-----------+
                                    |
                                    v
        +------------------- Spec + Planning Process -------------------+
        |                                                               |
        |  Feature request -> Planner brainstorm -> Specification       |
        |                         |                                     |
        |                         v                                     |
        |                  Gate 1: product owner approval               |
        |                         |                                     |
        |                         v                                     |
        |             Planner task plan -> Gate 2: Architect            |
        |                         |                                     |
        +-------------------------+-------------------------------------+
                                  |
                                  v
        +---------------- Development Loop (/dev-loop) -----------------+
        |                                                               |
        |  pending task -> Developer -> Reviewer -> Integration         |
        |                     ^           |              |              |
        |                     |           | FAIL         | regression   |
        |                     +-----------+              v              |
        |                                      bug report in open/      |
        +-------------------------+---------------------+---------------+
                                  |                     |
                                  | queue empty         | bugs exist
                                  v                     v
        +---------------- Final Sign-off --------+   +-- Bug Loop (/bug-loop) --+
        |  status report -> Gate 5:              |   |                          |
        |  product owner approves                |   | diagnose -> fix ->       |
        |  dev-agent -> main                     |   | review -> integrate      |
        |                                        |   |            ^             |
        +----------------------------------------+   |            | FAIL        |
                                                     +------------+-------------+

        Escalation path for blocked work:
        Developer / Reviewer / Integrator / Loop -> Architect -> Product Owner
```

## Agent Roles

Each agent implements a distinct role defined in `ai-process/architecture/`:

| Agent | Responsibility |
|---|---|
| **Planner** | Turns approved specs into atomic, independent tasks |
| **Architect** | Designs systems, validates plans, unblocks structural problems |
| **Developer** | Writes tests and production code following TDD |
| **Reviewer** | Two-stage code review: spec compliance, then code quality |
| **Integrator** | Merges branches, runs integration tests, resolves conflicts |

## Skills

Skills are reusable procedures agents invoke for common activities.
Each skill implements a workflow or action defined in the ai-process:

| Skill | What it implements |
|---|---|
| **architecture-consistency-review** | Checks new or changed architecture artifacts against approved specs and accepted ADRs |
| **evidence-before-claims** | Fresh command and actual output required before any claim of completion, passing, or merged |
| **using-ai-team** | Meta-skill: matches the situation to a skill, and checks gate preconditions, before any other action |
| **brainstorm** | Solution-space exploration before a spec is written |
| **spec-breakdown** | Decomposition of a spec into atomic tasks |
| **spec-breakdown-review** | Architect validation of task plans before development starts |
| **tdd** | Test-driven development cycle |
| **debug** | Diagnosis-first debugging: reproduce or confirm, gather evidence, isolate, then fix |
| **code-review** | Two-stage review of the Developer's claims and the project's rules, iterated until both agree on every finding |
| **receive-code-review** | The Developer's answer to each review finding: a fix, or evidence that it does not hold |
| **git-conventions** | The repository's authoritative branch and commit rules |
| **merge-conflicts** | Git conflict resolution preserving both sides' intent |
| **integrate** | Branch merge with project-discovered verification and task completion |
| **escalation-review** | Architect analysis for blocked work before product owner escalation |
| **/dev-loop** | Autonomous Developer → Reviewer → Integration loop across the pending task queue |
| **/bug-loop** | Autonomous diagnosis-first Developer → Reviewer → Integration loop across the open bug queue |
| **/change-request** | Creates a change request by invoking `ai-team change-request new`, then fills its content |
| **/new-spec** | Creates a specification by invoking `ai-team spec new`, then fills spec content |
| **/new-task** | Creates a pending task by invoking `ai-team task new` |
| **/new-bug** | Creates an evidence-backed bug report by invoking `ai-team bug new`, then fills bug content |
| **/new-adr** | Creates an Architecture Decision Record by invoking `ai-team adr new`, then fills ADR content |
| **/status-report** | On demand only: summarizes project state with `ai-team status`, and writes a report file with `ai-team report` only when asked |

## Agent Platform Compatibility

The framework exports agent and skill definitions for Claude Code only. They are authored once as Markdown under `cli/src/ai_team/init/sources/` (`agents/*.md` and `skills/<name>/SKILL.md`) and exported by `ai-team init` into the target project's `.claude/agents/` and `.claude/skills/` directories. `init` has no tool option.

This repository may also contain a `.claude/` folder at its root — it is **local agent configuration for this repository only**, is git-ignored, and is **not** part of the framework deliverable. It mirrors what `ai-team init` would write into a target project, but the CLI and the bundled scaffolds never read from it at runtime.

## Using This Framework in Your Project

Adopting the framework means installing the `ai-team` CLI, using it to scaffold the process files into your project, then adding project-local guidance for your stack and commands.
The full walkthrough is in `guides/setup-guide.md`.
For a narrated usage guide see [`cli/docs/usage.md`](cli/docs/usage.md); for an exhaustive command and flag reference see [`cli/docs/commands.md`](cli/docs/commands.md).

### Install the CLI

Download and install the wheel from the project's GitHub Releases page:

```bash
pipx install https://github.com/<org>/<repo>/releases/download/<tag>/ai_team-<version>-py3-none-any.whl
```

For a local build from this repository:

```bash
cd cli
python scripts/sync_init_scaffolds.py  # regenerates scaffolds from cli/src/ai_team/init/sources/
uv build
pipx install --force dist/*.whl
```

### Initialize a Project

From the target repository root:

```bash
ai-team init . --no-interactive --create-root-guidance
```

This creates the managed `ai-team/` folders, copies the bundled agents and skills into the target project's `.claude/agents/` and `.claude/skills/` directories, writes `.ai-team.toml`, and optionally creates a starter root `AGENTS.md` file.
The `ai-process/` specification documents are not exported; they live in this meta-repository only and serve as the authoritative spec for the rules the agents and skills implement.

Use `--dry-run` to preview files before writing. Use `--force` only when you intentionally want existing files overwritten. In non-interactive setup, omit `--create-root-guidance` if you do not want starter root guidance files.

### Daily CLI Commands

The CLI manages project artifacts directly:

```bash
ai-team status
ai-team list tasks
ai-team show T-001
ai-team task new "Add onboarding flow" --priority high --assigned-role developer
ai-team task start T-001
ai-team task complete T-001
ai-team bug new "Login crashes on empty token" --severity high
ai-team bug start B-001
ai-team bug resolve B-001
ai-team spec new "Billing reconciliation" --author "Team"
ai-team adr new "Use PostgreSQL for ledger storage"
ai-team change-request new "Revise planner handoff format"
ai-team check-layout
ai-team validate
ai-team report
```

The action skills use those commands internally. For example, `/new-task` delegates file creation to `ai-team task new`, `/new-bug` delegates to `ai-team bug new`, `/change-request` delegates to `ai-team change-request new`, and `/status-report` delegates to `ai-team status` plus `ai-team report`.

The most common loop is:

1. Create or approve a spec.
2. Break it into tasks; they live in the local tracker (`ai-team tracker path`), outside version control.
3. Run `/dev-loop` to implement, review, integrate, and complete tasks.
4. Run `/bug-loop` for open bugs.
5. Run `ai-team status` and `ai-team report` for Gate 5 sign-off context.

After initialization, still fill in your project's `AGENTS.md`, stack-specific commands, and coding guidance in `ai-team/docs/`.
Keep the framework files generic unless you intentionally fork the process.

The normal workflow is:

1. The product owner and Planner shape a specification; the product owner approves it at Gate 1.
2. Planner decomposes the approved spec into tasks.
3. Architect validates the task plan at Gate 2.
4. The product owner starts `/dev-loop`; Gate 3 code review and Gate 4 integration run inside the loop.
5. Bugs are filed in the local tracker and handled through `/bug-loop`.
6. The product owner approves the final `dev-agent` → `main` merge at Gate 5.

See `guides/setup-guide.md` for the complete file list, AGENTS.md starter template, and verification steps.

## Guides

| Guide | Purpose |
|---|---|
| [`guides/setup-guide.md`](guides/setup-guide.md) | Step-by-step walkthrough for bootstrapping a new project with the framework |
| [`guides/customization-guide.md`](guides/customization-guide.md) | What to adapt when tailoring the framework to your project's stack and conventions |
| [`guides/agent_template.md`](guides/agent_template.md) | Canonical template and rules for writing new agent definitions |
| [`guides/skill_template.md`](guides/skill_template.md) | Canonical template and rules for writing new skill definitions |

## Repository Structure

```
├── ai-process/
│   ├── processes/       Workflow definitions, quality gates, escalation procedures
│   ├── guidelines/      Coding standards, review checklists, markdown conventions
│   └── architecture/    AI team structure: roles, components, boundaries
├── docs/development/    Internal developer docs: architecture, tech stack, document index
├── docs/ai-team/        This repo's own managed artifacts (see `[project] dir` in .ai-team.toml)
│   ├── specs/           Feature specifications (with archive/ for superseded versions)
│   ├── decisions/       Architecture Decision Records
│   └── docs/            Project-specific commands, coding conventions, operations,
│                        and generated reports under docs/reports/
├── .ai-team/tracker/    Local, git-ignored work-item tracker: tasks, bugs, and change-requests
│                        (state is each file's status field; see `ai-team tracker path`)
├── guides/              User-facing setup and customization guides
└── cli/                 `ai-team` CLI package and bundled init scaffolds (authoritative agent
                         and skill sources live under cli/src/ai_team/init/sources/)
```

> Not shown above: `.claude/` may exist at the repo root as **local-only, git-ignored** agent configuration used when running agents inside this meta-repo. It is not part of the framework deliverable.

## Contributing to This Project

Changes to the framework follow the same workflow the framework defines.

- **Changing a rule** (workflow, standard, convention): update `ai-process/` first, then update any agents or skills that implement the changed rule.
- **Changing an agent or skill**: verify that the change is consistent with — or explicitly revises — the relevant ai-process documents.
- **Changing bundled init content**: update the package-owned source assets in `cli/src/ai_team/init/sources/` (`agents/`, `skills/`, `project/`, and `root/`), then run `python cli/scripts/sync_init_scaffolds.py` to regenerate the bundled scaffolds in `cli/src/ai_team/init/scaffolds/` so `ai-team init` ships the updated content.
- **Changing a CLI command or flag**: update the source, then run `bash cli/scripts/gen_docs.sh` and commit the updated `cli/docs/commands.md` so the reference stays current.
- **Architecture-affecting decisions**: record an ADR in `docs/ai-team/decisions/` before implementing.

The ai-process is the specification.
Agents and skills are the implementation.
Never let them contradict each other.
