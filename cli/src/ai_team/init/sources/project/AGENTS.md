# Project Guidance

This `{{project_dir}}/` directory stores project-local planning and execution artifacts.

## Folder Purpose

- `specs/` holds feature and change specifications, whatever their status.
- `decisions/` stores Architecture Decision Records (ADRs) and amendments.
- `docs/reports/` stores status reports generated on demand; it is git-ignored by default. The location is fixed and `docs/` holds nothing else: the project's own documents live outside `{{project_dir}}/`, by default in `docs/development/`.

Keep specs and ADRs under version control so automation and reviewers can read
the same canonical project state.

Work items — tasks, bugs, and change-requests — are not stored here. They live in the local
tracker (`ai-team tracker path`), outside version control, and are read and
changed only through `ai-team` commands.
