---
name: new-adr
description: Create a new Architecture Decision Record via the ai-team CLI. Use when an architecture-affecting decision must be recorded, an existing ADR superseded, or a proposed ADR accepted after the product owner's decision.
argument-hint: "[optional: decision title]"
allowed-tools: Read, Write, Edit, Bash, Skill(architecture-consistency-review), Skill(git-conventions)
---

# New ADR

Create an Architecture Decision Record (ADR) with `ai-team adr new --json`, commit it, and check it for consistency.

## Input Requirements

Argument: `$ARGUMENTS`

- `title` — required.
- `description` — required: why the decision is needed, the decision, the options rejected and why. Callers pass these facts only; this skill owns how they are written up.
- `status` — required:
  - `accepted` for a decision the Architect makes itself, the normal case;
  - `proposed` only when the decision needs the product owner, meaning an escalation condition of `feature-architecture`; an ADR records only a decision the work needs.
- `supersedes` — optional: the ID of the ADR the new one replaces, for example `ADR-002`.

A calling skill provides every required field; use them without follow-up questions.
When the product owner invokes this skill directly, ask only for the missing fields.

## Procedure

1. Resolve the inputs. Use the argument as `title` when it is the only input.
2. Run `ai-team adr new "<title>" --status "<status>" --json`, adding `--supersedes "<id>"` only when `supersedes` is given. Parse `id` and `path` from the JSON.
3. Fill the ADR's body sections from `description`, replacing the template placeholders. An ADR is one decision stated briefly: a few sentences per section, and no section that has nothing to say.
4. When `supersedes` is given, set the old ADR's frontmatter `status:` to `superseded`.
5. Commit the new ADR, and the superseded one, in one commit on the branch that is checked out, without switching branches. When `main` is checked out, commit nothing and return `BLOCKED`; `git-conventions` owns the rule, including the renumbering of an ADR whose ID the merge target already holds. Message: `docs(architecture): record <id> <short title>`.
6. Unless the caller is `architecture-consistency-review`, which checks the ADR within its own review, run `architecture-consistency-review` on the new ADR.

### Accepting a Proposed ADR

When the product owner decides a `proposed` ADR, set its `status:` to `accepted`, commit it as in step 5 with the message `docs(architecture): accept <id> <short title>`, and run step 6 on it.

## Output Format

- **Final response:** the ADR `id` and `path`, the commit hash, and the consistency-review verdict (or "run by the caller").
