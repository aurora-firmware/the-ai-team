# Contributing

Start here to work on ai-team, whether you are a person or an agent.
This guide routes you to the document that owns each rule, and holds the conventions that have no other home: writing style, and how to use the pull request and issue templates.

## Get Set Up

[`AGENTS.md`](../../AGENTS.md) has the commands to build, test, lint and run the project, including the two `ai-team` CLIs used here.
[`tech_stack.md`](tech_stack.md) explains the environment and the CI pipeline.

## Find the Rule

| You need | Read |
|---|---|
| How work flows, and the quality gates | [`ai-process/processes/`](../../ai-process/processes/) |
| Git branches and commit messages | [`git_conventions.md`](../../ai-process/guidelines/git_conventions.md) |
| Code rules | [`coding_guidelines.md`](coding_guidelines.md) |
| Markdown rules | [`markdown_conventions.md`](../../ai-process/guidelines/markdown_conventions.md) |
| How to write an agent, skill or spec | [`guides/`](../../guides/) |
| How the solution is built | [`architecture.md`](architecture.md) |
| Every other internal document | [The index](AGENTS.md) |

`ai-process/` decides whenever documents disagree.

## Choose a Path

Feature work follows the full process in [`workflow_overview.md`](../../ai-process/processes/workflow_overview.md).
Review fixes and small housekeeping changes do not; [`AGENTS.md`](../../AGENTS.md) lists these exceptions.
Name these branches as you like.

## Update What the Change Touches

| You change | Also do this |
|---|---|
| A workflow, standard or convention | Update `ai-process/` first, then the agents and skills that implement it |
| An agent or skill | Make sure it agrees with `ai-process/`, or revises it in the same change |
| Bundled init content, or a CLI command or flag | Regenerate the scaffolds or the command reference, as described in [`AGENTS.md`](../../AGENTS.md#build-and-install) |
| A rule a README diagram shows | Update and rerun [`generate_diagrams.py`](../images/readme/generate_diagrams.py) |
| An architecture-affecting decision | Record an ADR with `ai-team adr new` before implementing |

## Write Clearly

- Be clear and get to the point: use short sentences and plain words, and say what changed and why.
- Link to a rule instead of repeating it, so each rule has one owner.
- Report only what you checked, and say what you did not.
- Do not add AI co-author trailers or "Generated with" lines to commits or pull requests.

## Pull Requests

Write the title like a commit message: `docs(readme): enlarge the diagram text`.

Fill in the [pull request template](../../.github/pull_request_template.md), and add a section when reviewers need more, such as upgrade impact.

Lint and test must pass before merging.

## Issues

The tasks, bugs and change-requests of the ai-team process live in the local tracker.
These templates are for GitHub issues.

| Type | Title | Template |
|---|---|---|
| Bug | `Bug: <short description>` | [`bug.md`](../../.github/ISSUE_TEMPLATE/bug.md) |
| Feature | `Feature: <short description>` | [`feature.md`](../../.github/ISSUE_TEMPLATE/feature.md) |
| Task | `Task: <short description>` | [`task.md`](../../.github/ISSUE_TEMPLATE/task.md) |

Creating an issue from the command line? Use the same title, sections and issue type.
Record priority in the Project's priority field, never in the body or as a label.
