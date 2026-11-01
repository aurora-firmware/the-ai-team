# Agent Template

Use this template when creating or updating an agent for this framework.
Agents are **roles**: they define identity, authority, scope, handoffs, and output expectations.
Procedures — the steps, thresholds, and branching logic — belong in skills.

This template applies Anthropic's subagent best practices: specific descriptions, structured output, obstacle reporting, and limited tool access.

## The Separation Rule

- Agent = identity + authority ("who I am, what I'm allowed to decide").
- Skill = procedure ("what to do step by step").

If you need to write "first do X, then Y, then Z" — that's a skill. Put it there and have the agent *invoke* the skill by name.

If you need to write "I can decide X alone; Y needs the Architect; Z needs the product owner" — that's an agent.

## What Goes Where

| Content | Agent | Skill |
|---|---|---|
| One-sentence role purpose | ✅ | ✗ |
| Tools list | ✅ (frontmatter) | ✅ (frontmatter, as `allowed-tools`) |
| List of skills used and when | ✅ | ✗ |
| Decision-authority boundaries (what I can decide alone) | ✅ | ✗ |
| Spawned-by / hands-off-to graph | ✅ | ✗ |
| Folder scope (read / write / never-touch paths) | ✅ | ✗ |
| Quality bar ("done" criteria and embedded checklists) | ✅ | ✗ |
| Structured output format | ✅ | ✅ (procedure skills only) |
| Numbered procedural steps | ✗ | ✅ |
| Retry thresholds / escalation triggers | ✗ | ✅ |
| The 4-field escalation request block | ✗ | ✅ |

## Canonical Section Order

Every agent in this framework uses exactly these nine sections, in this order:

1. `## Purpose`
2. `## Inputs`
3. `## Skills`
4. `## Decision Authority`
5. `## Escalation`
6. `## Interaction Pattern`
7. `## Folder Scope`
8. `## Quality Bar`
9. `## Output Format`

A role that must read something before any other work may add one optional `## Session Start` section between `## Skills` and `## Decision Authority`.

## Agent Source Files

Each agent is one Markdown file under `cli/src/ai_team/init/sources/agents/<role>.md`, exported to `.claude/agents/<role>.md`:
- YAML frontmatter carries `name`, `description`, `tools`, `model`, and `skills`; `tools` and `skills` are first-class frontmatter fields.
- The agent body contains the nine canonical sections in Markdown.

## Agent File Template

````markdown
---
name: agent-name
description: Role-specific description that tells the caller exactly when to use this agent and what inputs to provide. Use for [specific workflow point]. Caller must provide [artifact/path/branch/context].
tools: Read, Glob, Grep, Bash
model: sonnet
skills: skill-one skill-two
---

## Purpose

One short paragraph stating the role this agent plays and the outcome it is responsible for.
Do not include step-by-step procedure logic here.

## Inputs

Inputs are described in the agent description (frontmatter). If any required input is missing, ask for it or return `BLOCKED` — do not guess.

## Skills

- `skill-one` — when this role uses it.
- `skill-two` — when this role uses it.
- `/action-skill` — when this role invokes it.

Skills define procedures. This agent invokes them but does not duplicate their steps.

## Decision Authority

### Can Decide Alone

- [Decision this role owns within its scope]
- [Decision within approved spec/task/bug scope]

## Escalation

The [Role] enters the escalation chain when the `<skill-name>` skill returns `ESCALATE`. Self-recovery thresholds and trigger conditions (retry counts, boundary violations, review cycles) are defined in that skill. The caller (active loop or product owner) routes the structured escalation request to the Architect via the `escalation-review` skill.

## Interaction Pattern

### Receives Work From

- **[Role / process / product owner]** — what state the work arrives in.

### Hands Off To

- **[Role / process / product owner]** — what is delivered and where it is recorded.

## Folder Scope

| Access | Paths |
|---|---|
| Read | [paths or `anywhere`] |
| Write / Edit | [paths or `none`] |
| Never touch | [paths] |

## Quality Bar

- [Done criterion 1 — observable, not procedural]
- [Done criterion 2]
- [Scope constraint]

Embedded checklists (e.g., coding standards for Developer, review checklist for Reviewer) live under this heading. They describe *what good output looks like*, not *how to produce it*.

## Output Format

Always return:

```text
Result: PASS | FAIL | BLOCKED | ESCALATE

Summary:
- <brief statement of what was produced or decided>

Artifacts:
- <files created/updated/read as primary evidence>

Evidence:
- <commands run, checks performed, logs reviewed, verdict location, or "not run" with reason>

Obstacles Encountered:
- <setup issue, missing input, workaround, special command flag, dependency/import issue, environment quirk, or "none">

Next Owner:
- <Developer | Reviewer | Architect | Planner | Integrator | Product Owner | Loop | none>

Next Action:
- <specific follow-up required, or "none">
```

When `Result` is `ESCALATE`, append an Escalation Request block after the fields above:

```text
Problem: [what went wrong]
Attempted: [what was tried, including retry count or review cycle]
Failed because: [why it did not work]
Question: [specific decision or guidance needed]
```
````

## Description Guidance

The `description` is loaded before the full agent file. It controls when the agent is selected and shapes the prompt the caller gives it.

A good description includes:

- The role's concrete responsibility.
- The workflow point where it should be used.
- The exact inputs the caller should provide.

**Good example** (from `reviewer.md`):
```yaml
description: Reviews completed task or bug-fix work after Developer handoff. Caller must provide the task or bug file, source branch, relevant diff or changed files, test evidence, and expected verdict location.
```

**Bad example — too vague:**
```yaml
description: Expert code reviewer.
```

## Tool Guidance

Start with the narrowest viable tool set. Broader access is harder to reason about and prone to accidents.

| Role shape | Tool frontmatter |
|---|---|
| Reads only (research, git or test inspection) | `Read, Glob, Grep, Bash` |
| Writes files (verdicts, planning documents, ADRs, source and test code) | `Read, Glob, Grep, Write, Edit, Bash` |

All five canonical agents write files (the Reviewer appends Review Verdicts and files bugs, the Architect writes ADRs and edits planned tasks), so all of them use the second row.

Every role that uses tracker skills requires `Bash` to invoke the `ai-team` CLI. `Folder Scope` defines its permitted writes.

If a role has broad tools for platform reasons, restate path restrictions in `Folder Scope` and `Quality Bar`.

## Self-Contained `.claude/` Rule

The `.claude/agents/` and `.claude/skills/` folders must be standalone. Agents must **not** reference content outside `.claude/` — no `ai-process/...` paths, no cross-repo citations. If a rule belongs to the framework spec (e.g. coding standards, review checklist), embed the content directly in the agent or skill that owns it, or create a dedicated skill (see `git-conventions` as an example of extracting cross-cutting rules into a skill when multiple callers need them).

## Where Escalation Mechanics Live

**In the agent** — only a one-paragraph `## Escalation` pointer naming which skill(s) own the thresholds.

**In the skills the agent uses** — the actual mechanics:
- Retry threshold (e.g., *"three consecutive Step 4 → Step 5 failures"*).
- Boundary violations (e.g., *"task requires modifying a file not listed in Files to Touch"*).
- The 4-field escalation request block (`Problem / Attempted / Failed because / Question`).

Rationale: thresholds change as the procedure changes. Keeping them in one place (the skill) prevents drift across role definitions.

## Canonical Agents In This Repo (only for reference)

| Agent | Model | Tools | Main skills |
|---|---|---|---|
| Planner | Opus | `Read, Write, Edit, Glob, Grep, Bash` | `brainstorm`, `spec-breakdown`, `new-spec`, `new-task`, `change-request`, `new-system-overview`, `git-conventions`, `evidence-before-claims` |
| Architect | Opus | `Read, Write, Edit, Glob, Grep, Bash` | `feature-architecture`, `spec-breakdown-review`, `architecture-consistency-review`, `escalation-review`, `new-adr`, `git-conventions`, `evidence-before-claims` |
| Developer | Sonnet | `Read, Write, Edit, Glob, Grep, Bash` | `tdd`, `debug`, `receive-code-review`, `new-bug`, `git-conventions`, `evidence-before-claims` |
| Reviewer | Sonnet | `Read, Write, Edit, Glob, Grep, Bash` | `code-review`, `new-bug`, `evidence-before-claims` |
| Integrator | Sonnet | `Read, Write, Edit, Glob, Grep, Bash` | `integrate`, `merge-conflicts`, `git-conventions`, `evidence-before-claims` |

Keep agents stable and small. When behavior becomes a repeatable sequence, create or update a skill rather than expanding the agent file.

## Anti-Patterns

- Embedding numbered procedures in the agent (belongs in a skill).
- Duplicating `Must Escalate` and `Escalation Triggers` as two sections (collapse into one `## Escalation` pointer).
- Generic-expertise descriptions ("expert X"). Describe the role, not the expertise.
- Cross-referencing other agents operationally (*"spawned by the Integrator agent"* when in fact a skill is doing the work).
- Broad tool access without Folder Scope restrictions.
- Referencing `ai-process/` paths. Agents must be self-contained within `.claude/`.
