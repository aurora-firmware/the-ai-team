# Skill Template

Use this template when creating a new skill for this framework. Skills are **procedures**: they describe what to do, in what order, with which inputs and outputs.

This template reflects the [Claude Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): concise `SKILL.md`, specific discovery metadata, progressive disclosure for detail, clear workflows, validation loops for quality-critical work.

## Core Principles

### Concise is key

The context window is shared with the system prompt, conversation history, other skills' metadata, and the actual request. Only the `name` and `description` of every skill are pre-loaded; `SKILL.md` is read on demand. Even so, every token in `SKILL.md` competes with conversation history once loaded.

Default assumption: **Claude is already smart**. Only add context Claude does not already have. Challenge each line: "Does Claude need this? Can I assume it knows? Does this paragraph justify its tokens?"

Keep `SKILL.md` body **under 500 lines** for optimal performance. Above that, move detail into `references/` (see Progressive Disclosure).

### Set appropriate degrees of freedom

Match instruction specificity to the task's fragility:

- **High freedom** (text guidance) — multiple valid approaches, decisions depend on context. Example: "Analyse code structure, check for edge cases, suggest readability improvements."
- **Medium freedom** (templates, parameterised scripts) — preferred pattern exists, some variation acceptable. Example: "Use this template; customise as needed."
- **Low freedom** (specific scripts, no parameters) — fragile, error-prone, consistency critical. Example: "Run exactly `python scripts/migrate.py --verify --backup`. Do not modify."

Procedure skills in this framework lean **medium-to-low freedom**: numbered steps, named outputs, fixed verdict vocabulary. Orchestrator spawn prompts are **low freedom**: word them uniformly.

### Test with the models you ship to

A skill that works for Opus may need more detail for Haiku. If a skill will be invoked across multiple models in this team (e.g., Haiku for cheap orchestration, Sonnet for implementation, Opus for review), exercise it on each.

## Skill Categories

Skills fall into three categories. The shape of the `SKILL.md` differs slightly per category.

- **Procedures** — analytical, multi-step work. Have a numbered `Procedure`, `Escalation` section, `Quality Criteria`, and `Common Pitfalls`. Examples: `tdd`, `code-review`, `integrate`, `debug`, `merge-conflicts`, `spec-breakdown-review`, `escalation-review`, `brainstorm`, `spec-breakdown`.
- **Orchestrators** — autonomous loops that spawn subagents and drive workflows. Have a numbered `Procedure` with explicit `**Spawn the <Role> subagent**` blocks, `Cycle Counter Reset`, `Commit Conventions`, `Hard Stops`, and `What This Skill Does NOT Do`. Stay model-invocable so the product owner can delegate a loop to an agent; the `using-ai-team` rule forbids starting one unasked. Examples: `dev-loop`, `bug-loop`.
- **Actions** — simple document-creation or single-purpose operations. Short numbered list, usually no escalation section. Product-owner-only actions may carry `disable-model-invocation: true`; actions invoked by another skill must remain model-invocable. Examples: `new-spec`, `new-task`, `new-bug`, `new-adr`, `status-report`, `git-conventions`.

## The Separation Rule

A skill file must **not** contain:
- Role identity, decision authority, or scope ("I am the Reviewer", "the Architect can decide X alone") — those belong in the agent file of whichever role invokes the skill.
- Operational cross-references to other agents ("then the Developer agent takes over") — describe the handoff back to the *caller* (often an orchestrator skill), not to another agent.

A skill file **should** contain:
- Steps.
- Thresholds ("three consecutive failures", "one bisect cycle").
- Output format and verdict vocabulary.
- The 4-field escalation request block when the skill can return `ESCALATE`.

## Directory Structure

```text
skill-name/
├── SKILL.md
├── assets/
│   └── example_template.md
├── references/
│   └── reference-topic.md
└── scripts/
    └── helper.py
```

Only create `assets/`, `references/`, or `scripts/` when the skill needs them. Do not add `README.md`, quick references, or changelogs — the `SKILL.md` is the single entry point.

### Export Rules for Skills in This Repository

A source skill is one `SKILL.md` (frontmatter plus body) under `cli/src/ai_team/init/sources/skills/<name>/`, with optional `assets/`, `references/` and `scripts/` folders. Only those are exported. Any other file in that directory stays in the source tree.

The supporting folders reach the export next to `SKILL.md`. The generator copies them byte for byte. When `ai-team init` writes them into a project, it fills in `{{project_dir}}` and `{{integration_branch}}`. Files that are not UTF-8 text are copied byte for byte, without placeholder filling.

## Canonical Section Order

For **procedure skills**:

1. `# Skill Title`
2. `## Input Requirements`
3. `## Procedure` (numbered steps)
4. `## Escalation` (if the skill can return `ESCALATE`)
5. `## Output Format`
6. `## Quality Criteria`
7. `## Rationalizations` (optional: a table of the excuses an agent gives for skipping a rule, each with its rebuttal; see `guides/skill_testing_guide.md`)
8. `## Common Pitfalls`

For **orchestrator skills**, append after `## Procedure`:

- `## Cycle Counter Reset` (if the procedure has review or retry cycles)
- `## Commit Conventions` (canonical patterns — defer authoritative rules to `git-conventions`)
- `## Hard Stops (Do Not Continue)`
- `## What This Skill Does NOT Do`

## SKILL.md Template (procedure skill)

````markdown
---
name: skill-name
description: Does the specific work this skill is responsible for. Use when [trigger], when a workflow reaches [process point], or when [artifact/context] must be handled.
allowed-tools: Read, Glob, Grep, Bash
---

# Skill Title

## Input Requirements

- **Input artifact:** `path/or/artifact-name`
- **Required context:** [spec, task, bug, ADR, branch, logs, user answer]
- **Required tools or dependencies:** [tool/script/package], or `none`

Stop and return `BLOCKED` if a required input is missing and cannot be inferred safely.

## Procedure

### Step 1: Read Input
Read the input artifact and relevant prior context.

### Step 2: Identify the Work
Identify the concrete work required and the acceptance or completion criteria.

### Step 3: Perform the Action
Perform the smallest sufficient action that satisfies the criteria.

### Step 4: Validate
Run or perform the primary verification.
If validation fails, fix the issue and repeat validation before finishing.
If validation cannot be run, record why and provide the best available evidence.

### Step 5: Produce Output
Record the outcome in the required output location.

## Escalation

Return `ESCALATE` under any of these conditions. All cases use the same structured four-field request; the active loop forwards it to the Architect via the `escalation-review` skill. Do not resume the procedure until the Architect responds.

**Retry threshold.** [State the concrete count, e.g. "three consecutive Step N failures"].

**Boundary violations (no retry — escalate on first detection):**
- [Condition 1]
- [Condition 2]

```text
Problem: [what went wrong]
Attempted: [what was tried, including retry count]
Failed because: [why it did not work]
Question: [specific decision or guidance needed from the Architect]
```

## Output Format

- **Updated files:** [which files or directories this skill may write]
- **Log entry or verdict:** [required heading or format]
- **Final response:** [what the caller should be told, including the verdict vocabulary]

Skills used inside an agent's Output Format should align with the agent's `Result: PASS | FAIL | BLOCKED | ESCALATE` vocabulary. Do not invent alternative verdict words (e.g. a skill returning `Gate 2 Verdict:` when the surrounding agent output uses `Result:` — use `Result:`).

## Quality Criteria

- The skill triggered only for the intended use case.
- The procedure produced the expected artifact or state transition.
- Validation evidence is recorded.
- The implementation stayed within the skill's scope.
- The instructions remained concise and avoided duplicate reference content.

## Common Pitfalls

- Using a vague description that does not help skill discovery.
- Putting large reference material directly in `SKILL.md` instead of `references/`.
- Offering many equivalent options instead of a recommended default.
- Skipping validation or failing to define what success means.
- Mixing role identity or authority into a procedure skill.
````

## Orchestrator Additions

Orchestrators drive autonomous loops. They spawn subagents using a uniform prompt shape.

### Subagent spawn prompt

Use the exact wording `**Spawn the <Role> subagent** (tier: <cheap | standard | most capable>) with this prompt:` followed by a quoted prompt block. Name the model tier at every spawn; the orchestrator's Dispatch Discipline section defines the tiers. The prompt must:

- Name the skill the subagent should use (e.g., *"implement it using the `tdd` skill"*).
- Name the target branch or canonical file path.
- Specify the expected verdict vocabulary (`PASS / FAIL / ESCALATE`, or the full Output Format block).
- End with: *"Populate every field of the Output Format block, including `Obstacles Encountered`."*

Example from `dev-loop/SKILL.md`:

```markdown
**Spawn the Developer subagent** (tier: standard) with this prompt:

> "Pick up the task from the task file `<task-path>` and implement it using the tdd skill.
> You are on branch `task/T-NNN-...`. Commit after each red→green→refactor cycle.
> The task file is in the local tracker, outside version control: do not edit it, and never add it to a commit.
> Return a Work Log handoff entry at session end. The entry's heading is `### Session N — YYYY-MM-DD`; the body is free prose covering what was done, what was tried and rejected, and what remains. The loop will append it to the task file.
> Populate every field of the Output Format block, including `Obstacles Encountered`."
```

### Frontmatter

Orchestrators declare `Agent` in `allowed-tools` (to spawn subagents). They stay model-invocable so the product owner can delegate a loop to an agent, for example to keep the main session clean; the `using-ai-team` rule that a loop starts only when the product owner asks is the guard against starting one unasked. End the description with a sentence limiting use to an explicit product owner request.

```yaml
allowed-tools: Read, Glob, Grep, Bash, Agent, Skill(integrate), Skill(git-conventions)
```

### Phase-2 product owner escalation

When an orchestrator exhausts Phase 2, Step 1 (Architect) without resolution, it produces a Phase 2 Product Owner Escalation Report using the canonical template defined in `escalation-review/SKILL.md`. Do not reinvent the report shape — point at that template.

## Frontmatter Guidance

`name`:
- **Maximum 64 characters.** Lowercase letters, numbers, and hyphens only.
- **Cannot contain** XML tags or the reserved words `anthropic`, `claude`.
- Short and specific. Prefer action-oriented or noun-phrase names (`spec-breakdown`, `code-review`, `git-conventions`). Anthropic's published guidance recommends gerund form (`writing-plans`); both are acceptable in this framework, but stay consistent with neighbouring skills.
- Avoid vague names such as `helper`, `utils`, `tools`.

`description`:
- **Maximum 1024 characters.** Non-empty. No XML tags.
- **Always third person.** The description is injected into the system prompt; first/second person ("I can…", "You can…") causes discovery problems.
- State **what the skill does and when to use it** in the same sentence — concrete trigger words, artifacts, and process states. Put the weight on the triggering conditions and never list the steps: a description that summarizes the workflow gets followed in place of the skill (see `guides/skill_testing_guide.md`, *Skill Discovery Wording*).
- Distinguish the skill from neighbouring skills.

**Good example** (from `code-review/SKILL.md`):
```yaml
description: Two-stage code review for completed tasks and bug fixes. Use when a Developer submits work and the Reviewer must check the Developer's claims and the project's rules, or check the Developer's answers to an earlier Review Verdict.
```

**Avoid:**
```yaml
description: Helps with code review.   # vague — no trigger
description: I can review code.        # first person
description: Use this when needed.     # no specifics
```

`allowed-tools`:
- Declare every tool the skill actually invokes.
- Declare every other skill invoked in-process via `Skill(other-skill)`.
- Referential mentions ("the active loop routes this to `escalation-review`") do **not** require a `Skill()` declaration when the current skill does not call it itself.

`argument-hint`:
- Use for skills invoked as slash commands with positional arguments. Document the argument shape tersely in frontmatter and fully in `## Input Requirements`.

`disable-model-invocation`:
- Set to `true` for product-owner-only actions such as `status-report`. Do not set it on orchestrators: they stay model-invocable so the product owner can delegate a loop to an agent, and the `using-ai-team` rule forbids starting one unasked.
- Do not set it to `true` on a skill referenced through another skill's `Skill(<name>)` declaration. The target must remain model-invocable for that in-process call to work.

## Explicit Skill Invocation

When one skill invokes another in-process, declare it in `allowed-tools` as `Skill(other-skill)` and reference it in prose by its backticked name. Example audit pattern:

| Skill | Invokes in-process | `allowed-tools` | Prose reference form |
|---|---|---|---|
| `integrate` | `merge-conflicts`, `new-bug`, `git-conventions` | `Skill(merge-conflicts), Skill(new-bug), Skill(git-conventions)` | `` Invoke the `merge-conflicts` skill `` |
| `code-review` | `git-conventions` | `Skill(git-conventions)` | `` Commit using the `git-conventions` skill `` |

Descriptive mentions — referring to skills the caller will invoke, or skills downstream in the chain — do not need a declaration. Example: `tdd` mentions `escalation-review` in prose to say *"the active loop forwards the request via `escalation-review`"*, but `tdd` itself does not invoke it, so it is not in `allowed-tools`.

## Escalation Mechanics Live Here

Agents carry only a one-paragraph `## Escalation` pointer. The actual mechanics — retry thresholds, boundary-violation triggers, the 4-field escalation request block — live in the skill. When you add or change a threshold, change it in the skill and the agent needs no edit.

Uniform 4-field block (mandatory shape when a skill can return `ESCALATE`):

```text
Problem: [what went wrong]
Attempted: [what was tried, including retry count or review cycle]
Failed because: [why it did not work]
Question: [specific decision or guidance needed]
```

## Self-Contained `.claude/` Rule

Skills must not reference content outside `.claude/`. If a cross-cutting rule (e.g. git conventions, coding standards) is needed in multiple skills, extract it into its own skill (see `git-conventions`). If it is needed in only one role, embed it in that role's agent `Quality Bar` (see `developer.md` coding standards, `reviewer.md` review checklist).

## Progressive Disclosure

Keep `SKILL.md` focused on the core workflow. Move detail out when it is conditional, large, or only needed for some variants:

- Put reusable templates in `assets/` (for example, a `report_template.md` that the skill copies and fills in).
- Put domain references, schemas, examples, or long policies in `references/`.
- Put deterministic or fragile operations in `scripts/`.

Reference every optional file directly from `SKILL.md` using `${CLAUDE_SKILL_DIR}/...` or `.claude/skills/<skill>/...`. **Keep references one level deep.** When a referenced file links to *another* file, Claude often previews with `head` instead of reading fully — leading to incomplete information. Every supplementary file should be reachable from `SKILL.md` directly.

For reference files longer than ~100 lines, include a **table of contents** at the top so partial reads still expose the full scope.

### Pattern 1 — High-level guide with references

`SKILL.md` shows the most-common path inline, then points to deep dives:

```markdown
## Quick start
[the 80% path, inline]

## Advanced
**Form filling**: see [references/forms.md](references/forms.md)
**API reference**: see [references/api.md](references/api.md)
```

### Pattern 2 — Domain-specific organisation

When the skill spans multiple domains, organise references by domain so Claude only loads the relevant slice:

```text
bigquery-skill/
├── SKILL.md
└── references/
    ├── finance.md
    ├── sales.md
    └── product.md
```

`SKILL.md` lists each domain and its file. A request about sales metrics never loads `finance.md`.

### Pattern 3 — Conditional details

Show the basic case inline; link advanced variants:

```markdown
## Editing documents
For simple edits, modify the XML directly.
**For tracked changes**: see [references/redlining.md](references/redlining.md)
```

## Workflows And Feedback Loops

### Numbered steps and checklists

For multi-step procedures, number steps and — for particularly long workflows — provide a checklist Claude can copy into its response and tick off:

````markdown
## Workflow

Copy this checklist and check off as you go:

```
- [ ] Step 1: Read input
- [ ] Step 2: Identify acceptance criteria
- [ ] Step 3: Perform action
- [ ] Step 4: Validate
- [ ] Step 5: Produce output
```

**Step 1: …**
````

### Validation loops

For quality-critical work, build an explicit *validate → fix → re-validate* loop into the procedure:

```markdown
1. Make the change.
2. Run the validator (script, linter, or checklist).
3. If validation fails, fix and return to step 2.
4. Only proceed when validation passes.
```

This is the same pattern `tdd` uses (red → green → refactor with tests as the validator) and `code-review` uses (Stage 1 acceptance, Stage 2 quality).

### Plan–validate–execute (for destructive or batch work)

For complex, error-prone, or destructive operations, insert an intermediate machine-checkable artifact:

```markdown
1. Analyse inputs.
2. **Produce a plan file** (e.g. `changes.json`).
3. **Validate the plan** with a script that emits specific errors.
4. Execute the plan.
5. Verify the output.
```

Catches errors before they touch the real artifact and gives Claude an objective signal to iterate against.

## Common Patterns

### Template pattern

When the skill produces a document or report, embed the template directly. State whether it is **strict** ("ALWAYS use this exact structure") or **flexible** ("Sensible default; adapt as needed"). Most agent-output blocks in this framework (`Result:`, `Diagnosis Log`, escalation block) are strict.

### Examples pattern

When output quality depends on style or tone (commit messages, escalation requests, review comments), include 2–3 concrete input/output pairs. Examples beat description.

### Conditional workflow pattern

When the procedure branches on input type, surface the decision point first:

```markdown
## Workflow

1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow"
   **Editing existing?** → Follow "Editing workflow"

2. Creation workflow: …
3. Editing workflow: …
```

If branches grow large, push each into its own `references/` file.

## Content Guidelines

### Avoid time-sensitive information

Do not write "if you're doing this before August 2026, use X". Use a current section plus an `<details>`-folded *Old patterns* section for historical context. Prefer durable framing: name the API version, not the date.

### Use consistent terminology

Pick one term per concept and use it throughout the skill (e.g., always "API endpoint" — never mix in "URL", "route", "path"). Inconsistent vocabulary makes Claude hedge and re-derive meaning.

## Scripts

For skills that bundle scripts under `scripts/`:

- **Solve, don't punt.** Handle expected error conditions inside the script with specific messages — don't leave Claude to figure out a stack trace. Example: a missing-file path should print `File X not found; creating default` rather than raising `FileNotFoundError`.
- **No voodoo constants.** Every magic number needs a one-line comment explaining the value (`# 30s covers slow connections`). If you don't know the right value, neither will Claude.
- **Forward slashes only.** `scripts/helper.py`, never `scripts\helper.py`. Unix paths work everywhere; Windows paths break on Linux.
- **Be explicit about execute vs. read.** "Run `analyze.py`" (execute, output is what matters) vs "See `analyze.py` for the algorithm" (read as reference). Most utility scripts should be executed — it saves tokens and is more reliable than asking Claude to recreate the logic.
- **Document required packages.** List them in `SKILL.md` and verify they're available in the runtime. The Claude API runtime has no network access; `claude.ai` can install from PyPI/npm. Don't assume `pip install` succeeds.
- **Specific error messages.** `Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed` is far more useful than `KeyError`.

## MCP Tool References

If a skill invokes an MCP tool, always use the fully qualified `ServerName:tool_name` form (e.g., `BigQuery:bigquery_schema`, `GitHub:create_issue`). Without the prefix, lookup fails when multiple MCP servers are configured.

## Validation And Evaluation

The method for proving a skill or a rule change works — baseline pressure scenario, change, re-run — is in `guides/skill_testing_guide.md`. The steps below are the summary.

Build evaluations **before** writing extensive documentation. Skills should solve real, observed problems — not imagined ones.

1. **Identify the gap.** Run a representative task without the skill. Note where Claude lacks context, picks the wrong default, or skips a step.
2. **Author 3+ evaluation scenarios** that exercise the gap. Suggested JSON shape:

   ```json
   {
     "skills": ["my-skill"],
     "query": "…the user request…",
     "files": ["fixtures/input.pdf"],
     "expected_behavior": [
       "Triggered the skill",
       "Read the right reference file",
       "Produced output matching the verdict format"
     ]
   }
   ```
3. **Establish baseline** without the skill, measure with the skill, iterate until the skill closes the gap.
4. **Test triggering both ways.** Verify the skill triggers for in-scope requests and does *not* trigger for adjacent out-of-scope requests.
5. **Test on every model the skill ships to.** Haiku may need more explicit step labels than Opus.

### Iterative authoring with Claude

The most effective workflow is **Claude A authors, Claude B uses**:

- Use one Claude session to draft and refine `SKILL.md`.
- Use a fresh Claude session (with the skill loaded) to perform real tasks.
- Bring observations from session B back to session A. Refine. Repeat.

When Claude B forgets a rule, the rule probably isn't prominent enough — strengthen the wording (`MUST` instead of `always`) or move it earlier in the procedure rather than adding more prose.

## Anti-Patterns

- Embedding role identity or authority in a skill.
- Inventing a custom verdict vocabulary (`Gate 2 Verdict:`, `Review Status:`) instead of aligning with the caller's `Result:` shape.
- Prose-only escalation without the 4-field structured block.
- Inconsistent spawn wording (`Spawn the X role`, `invoke the X agent`). Use `**Spawn the <Role> subagent** (tier: ...)` uniformly.
- Declaring `Skill(x)` in `allowed-tools` when the skill only references `x` descriptively and never invokes it.
- Referencing `ai-process/` paths. Skills must be self-contained within `.claude/`.
- First/second person in `description` (`I can…`, `You can…`). Always third person.
- Vague descriptions (`Helps with X`) — no trigger words means Claude cannot pick the skill.
- `SKILL.md` body over 500 lines. Split into `references/` instead.
- Deeply nested references (`SKILL.md` → `a.md` → `b.md`). Keep one level deep.
- Time-sensitive guidance (`before August 2026, do X`). Use durable framing or an *Old patterns* fold.
- Inconsistent terminology across the skill.
- Offering many equivalent options without a recommended default.
- Windows-style paths (`scripts\helper.py`). Forward slashes only.
- "Voodoo" constants in scripts with no justifying comment.
- Punt-style error handling that leaves Claude to interpret raw exceptions.
- MCP tool references without the `ServerName:` prefix.

## Pre-Publication Checklist

Before treating a skill as ready:

**Discovery and scope**
- [ ] `name` ≤64 chars, lowercase-hyphen only, no reserved words.
- [ ] `description` ≤1024 chars, third person, names *what* and *when*.
- [ ] `allowed-tools` lists every tool and every in-process `Skill()` invoked.
- [ ] `disable-model-invocation: true` set only on product-owner-only actions (never on orchestrators) and not targeted by another skill's `Skill()` declaration.

**Content**
- [ ] `SKILL.md` body under 500 lines.
- [ ] References one level deep; long ones have a TOC.
- [ ] Consistent terminology.
- [ ] No time-sensitive content (or in *Old patterns* fold).
- [ ] No role identity or authority embedded.
- [ ] No `ai-process/` paths.

**Procedure**
- [ ] Numbered steps with clear inputs and outputs.
- [ ] Validation loop where quality matters.
- [ ] Verdict vocabulary aligned with `Result: PASS | FAIL | BLOCKED | ESCALATE`.
- [ ] 4-field escalation block present if the skill can return `ESCALATE`.
- [ ] Orchestrators use `**Spawn the <Role> subagent** (tier: ...)` wording uniformly.

**Scripts (if any)**
- [ ] Forward-slash paths only.
- [ ] Constants justified with comments.
- [ ] Explicit error handling with actionable messages.
- [ ] Required packages listed and verified in the runtime.
- [ ] Execution intent (run vs. read) is explicit.

**Validation**
- [ ] At least three evaluation scenarios authored.
- [ ] Skill triggers for in-scope, does not trigger for adjacent out-of-scope.
- [ ] Tested on every model the skill is expected to run under.
