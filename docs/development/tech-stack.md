# Tech Stack

Answers to the Decisions needed of the development-infrastructure components in
[S-000](../ai-team/specs/S-000-system-overview.md). This repository is brownfield:
these answers record the setup that already exists.

## Development environment

- **Language and version.** Python 3.14 or newer (`requires-python = ">=3.14"` in
  `cli/pyproject.toml`).
- **Reproducing the environment.** [mise](https://mise.jdx.dev/) installs the tools
  pinned in `mise.toml` (Python 3.14 and `uv`). `uv sync` in `cli/` creates the
  virtual environment from `cli/uv.lock`, including the `dev` dependency group.
  The package version comes from git tags through `hatch-vcs`, so a checkout needs
  its tags.
- **Settings and environment values.**
  - `.ai-team.toml` holds this repository's framework settings: project folder
    `docs/ai-team`, tracker folder `.ai-team/tracker`, integration branch
    `dev-agent`. `[init].framework_version` is pinned to the last release, so the
    CLI run from source shows the version mismatch warning; that is accepted.
  - `UV_CACHE_DIR` may point at a writable folder (for example under `/tmp`) where
    the default `uv` cache is not writable.
  - `AI_TEAM_ROOT` overrides project-root detection (see `cli/docs/usage.md`).
- **Files kept out of version control.** `.gitignore`: the local agent folders
  (`.claude`, `.agents`, `.pi`), Python caches and wheels, root-level
  `pr-*-review.md` reports, and the local tracker `/.ai-team/`.
- **Remote.** A remote is required. The repository is hosted on GitHub as
  `aurora-firmware/the-ai-team` and is reached as `origin`. Access is confirmed when
  `git ls-remote --heads origin` lists at least one branch.

## Test tooling

- **Test harness.** pytest, in `cli/tests/`.
- **Formatting and lint.** Ruff, configured in `cli/pyproject.toml`: target `py314`,
  line length 88, lint rules `E`, `F` and `I`, with `E501` ignored. An optional
  pre-commit hook (`bash cli/scripts/install-hooks.sh`) runs the format check.
- **Commands** (from `cli/`), all of which must pass before work is complete:
  - `uv run pytest`
  - `uv run ruff format --check .`
  - `uv run ruff check .`

## CI pipelines

- **Service and runners.** GitHub Actions (`.github/workflows/ci.yml`) on
  self-hosted Docker runners, in the `ghcr.io/astral-sh/uv:python3.14-trixie-slim`
  container.
- **Triggers.** Every pull request, pushes to `main`, and version tags
  (`X.Y.Z` or `X.Y.Z-label`).
- **Checks that block a merge.** The `lint` job (ruff format check, ruff lint, and
  `cli/docs/commands.md` up to date with `gen_docs.sh`) and the `test` job (pytest).
- **Releases.** On a version tag, after `lint` and `test` pass, the `release` job
  builds the wheel and sdist with `uv build` (a `-label` suffix becomes a PEP 440
  local version) and publishes a GitHub Release with the wheel, the sdist and
  `cli/docs/commands.md`, with generated release notes.

## Internal documentation

- **Where architecture and technology choices live.** In `docs/development/`:
  [`architecture.md`](architecture.md) and this file. Contracts live in the specs
  and ADRs under `docs/ai-team/`; these documents describe the current setup and
  never restate them.
- **Who keeps them current.** Whoever changes the setup they describe updates them
  in the same change.
- **The other internal documents** are indexed in [`AGENTS.md`](AGENTS.md).
