# Project Guidance

This `docs/ai-team/` directory stores project-local planning and execution artifacts.

## Folder Purpose

- `specs/` holds approved feature or change specifications.
- `decisions/` stores Architecture Decision Records (ADRs) and amendments.
- `docs/reports/` stores status reports generated on demand; this repo tracks them (the scaffold ignores them by default).
- `docs/` stores project-local docs such as coding guidelines and runbooks.

Keep these artifacts under version control so automation and reviewers can read
the same canonical project state.

Work items — tasks, bugs, and change-requests — are not stored here. They live in the local
tracker (`ai-team tracker path`), outside version control, and are read and
changed only through `ai-team` commands.
