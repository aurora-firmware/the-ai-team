# Project Coding Guidelines

This document extends the framework coding standards in `ai-process/guidelines/coding_standards.md` with the rules for this repository's CLI in `cli/`.

## Stack

- Python 3.14 or newer (`requires-python = ">=3.14"` in `cli/pyproject.toml`).
- `uv` manages the environment and the lock file. Run every tool through `uv run` from `cli/`.
- New runtime dependencies go in `[project] dependencies` in `cli/pyproject.toml`; development tools go in the `dev` dependency group.

## Formatting and Lint

- Ruff is the formatter and linter, configured in `cli/pyproject.toml`: target `py314`, line length 88, lint rules `E`, `F`, and `I` (import sorting), with `E501` ignored.
- Check with `uv run ruff format --check .` and `uv run ruff check .` from `cli/`.

## Testing

- Tests use pytest and live in `cli/tests/`.
- Run them with `uv run pytest` from `cli/`.
- After changing a source scaffold, run `python scripts/sync_init_scaffolds.py` from `cli/` before testing.
