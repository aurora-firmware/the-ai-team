# Customization Guide

This guide explains what to adapt when adopting the AI team framework for your project.

## What ai-team init Exports As-Is

The `ai-team init` command exports these files from the CLI package scaffold sources. They are generic and work for any project without modification:

| Category | Destination in your project |
|---|---|
| **Agent definitions** | `.claude/agents/` — roles are universal |
| **Skill definitions** | `.claude/skills/` — procedures are language-agnostic |
| **Action skills** | Action skills in `.claude/skills/` (`disable-model-invocation: true` only for product-owner-only actions that no other skill invokes) |

The `ai-process/` specification documents (process docs, guidelines, architecture docs) are **not** exported. They live in the AI team definition meta-repository and serve as the authoritative spec for the rules that agents and skills implement. Your project does not need them; the agent and skill files already embed the rules they need to execute.

## What to Customize

Artifact templates (for example task, bug, spec, and ADR templates) are bundled in the `ai-team` CLI and rendered by commands such as `ai-team task new`. They are not copied into your project and there is no project-level override, so changing a template means changing `cli/src/ai_team/templates/` in the framework.

Exported skill files in `.claude/skills/` may be edited for your project, but they are overwritten only when an upgrade updates the agents and skills (you answer yes to that question, or pass `--update-skills` or `--force`), or on an adoption answered yes or run with `--force`.

### Must Customize

**`AGENTS.md`** — Your project's identity:
- Add a title and a short description of your project above the sections.
- Add your tech stack, repository layout, and the specific build/run/test/lint commands agents should use.
- Point agents to project-local conventions, including `ai-team/docs/coding_guidelines.md` if present.
- Keep the five sections `ai-team check-layout` requires: `## Build and Install`, `## Test`, `## Run`, `## Lint and Format`, and `## Key Conventions`.

**`README.md`** — Your project's README:
- Write a new README describing your actual project, not the framework.
- Reference the framework workflow in a "Development Process" section.

**Project-local coding guidance** — Stack-specific rules:
- The framework's general, language-agnostic coding standards are built into the exported agents and skills; you do not edit them.
- Put project-specific coding rules in `ai-team/docs/coding_guidelines.md` or another project-local document referenced by your `AGENTS.md`.
- Include formatter, linter, test framework, dependency policy, naming conventions, file layout, and framework conventions there.
- Agents and skills should discover these details from the target project instead of relying on hardcoded defaults in the framework.

**Verification commands** — Project-specific commands:
- Define build, run, lint, test, and integration verification commands in `AGENTS.md`, task files, README, or project-local docs.
- The integration procedure reads these commands from the project; it should stop and ask if it cannot determine the correct command.

### Root AGENTS.md

`ai-team init` can scaffold one root-level guidance file from a starter template.
`AGENTS.md` is the only generated project and root guidance file:

- **`AGENTS.md`** (repo root) — read by the dev-loop and the agents. It documents
  the build, test, run, and lint commands and the conventions for your project.
  The dev-loop reads this file before starting any session so agents can run
  your tests without guessing.

The starter comes from the root guidance template
(`cli/src/ai_team/init/sources/root/AGENTS.md`) and uses the five sections
`ai-team check-layout` requires: `## Build and Install`, `## Test`, `## Run`,
`## Lint and Format`, and `## Key Conventions`.

#### What it's for

This file gives AI tools the project-specific context they cannot infer from
source code alone: how to install dependencies, how to run the test suite, how
to lint, and what environment assumptions apply. Without it, agents fall back
to guessing — or stop and ask, slowing down the loop.

#### The command sections

The dev-loop reads `## Test` for the baseline verification command; agents use
the other sections for build, run, and lint commands. For example:

```markdown
## Test

\`\`\`bash
uv run pytest
\`\`\`

## Lint and Format

\`\`\`bash
uv run ruff format --check .
uv run ruff check .
\`\`\`
```

Keep these sections accurate. If a command changes (new linter added,
test runner changed), update `AGENTS.md` in the same commit.

#### Workflow after `ai-team init` scaffolds it

1. Open the generated `AGENTS.md` from the starter template.
2. Replace the generic `# Project Guidance for Claude` title and introduction with your project's name and description.
3. Fill in your actual commands under `## Build and Install`, `## Test`,
   `## Run`, and `## Lint and Format`.
4. Add your tech stack, repo layout, and any agent-facing conventions under
   `## Key Conventions`.
5. Commit the file. It is yours to maintain — re-running `ai-team init`
   on an initialized project asks the upgrade questions and overwrites nothing
   without a yes, and `--force` overwrites root guidance only as described in
   the setup guide.

### Changing the Process

The agent roles, quality gates and escalation thresholds are defined by the framework's `ai-process/` documents, which are not exported, and carried out by the exported agents and skills. The workflow expects all five agents (Planner, Architect, Developer, Reviewer, Integrator): the procedures hand work to each of them by name (the loops spawn the Developer, Reviewer and Architect, integration hands merge conflicts to the Integrator, and Gate 2 runs between the Planner and the Architect).

To change the gate model, the escalation thresholds or the set of roles, change the framework itself: update `ai-process/` first, then the agents and skills that implement it, as described in the framework's README ("Contributing to This Project"). Editing the exported files in `.claude/` instead is possible, but an upgrade that updates the agents and skills overwrites those edits.

## Extending the Framework

### Adding New Agent Roles

Use `guides/agent_template.md` as a reference. Common additions:
- **DevOps agent** — manages CI/CD, deployment, infrastructure.
- **Documentation agent** — writes user-facing docs, API references.
- **Security agent** — dedicated security review, dependency auditing.

### Adding New Skills

Create a new directory under `.claude/skills/<name>/` with a `SKILL.md` file. Common additions:
- **Database migration** — schema changes with rollback procedures.
- **API design** — REST/GraphQL endpoint design following project conventions.
- **Performance profiling** — identify and fix performance bottlenecks.

### Adding New Action Skills

Create a new directory under `.claude/skills/<name>/` with a `SKILL.md` file. Add the `disable-model-invocation: true` frontmatter field if the skill should be user-invocable only (not triggered by the model). Reference existing skills as examples.

## Retrofitting Into an Existing Project

If you have an existing codebase:

1. Follow the setup guide to create the directory structure alongside your existing code. `ai-team init` detects the adoption case (no `.ai-team.toml` that records `[init] framework_version`, but some files it would write already exist), lists those files and asks once whether to overwrite them; answer no to keep them and write only the missing ones.
2. Your existing source code stays where it is — the framework directories are additive.
3. Write or update `AGENTS.md` so agents can find project commands and repository layout.
4. Migrate existing issues/tasks by creating a task for each open item with `ai-team task new` (they land in the local tracker).
5. Write the S-000 system overview spec — what the project is for and how it divides into components (`ai-team spec new --overview` or the `new-system-overview` skill), and get it approved.
6. Run the project bootstrap after S-000 is approved (`spec-breakdown` on S-000): its tasks fill in the project guidance and the coding guidelines in `ai-team/docs/coding_guidelines.md`, instead of you writing them by hand.
7. Create an ADR in `ai-team/decisions/` documenting the decision to adopt this framework.
