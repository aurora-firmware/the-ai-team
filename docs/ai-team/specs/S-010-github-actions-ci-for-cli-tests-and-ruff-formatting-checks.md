---
title: GitHub Actions CI for CLI tests and Ruff formatting checks
version: '0.2'
status: approved  # draft | review | approved | superseded
created: '2026-05-14'
author: planner
id: S-010
---

# GitHub Actions CI for CLI tests and Ruff formatting checks

## Purpose

This spec covers the S-000 **CI pipelines** component. The `ai-team` CLI under `cli/`
has a test suite, a generated command reference and a Ruff configuration, but none of
them is checked unless someone remembers to run them locally, and releases would
otherwise be built by hand. Every pull request and every push to `main` gets
independent `lint` and `test` checks, and a version tag that passes both produces a
GitHub Release carrying the built packages and the command reference.

## Users and Journeys

| Actor | Goal | Priority | Outcome | Requirements |
|---|---|---|---|---|
| Contributor (human or agent) opening a pull request | Learn whether the change keeps the CLI formatted, lint-clean, documented and passing its tests | P1 | The pull request shows a pass or fail result for `lint` and for `test` | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 |
| Product owner merging into `main` | Merge only changes whose checks pass, without running them locally | P1 | The checks on the pull request and on `main` commits are visible before and after the merge | REQ-001, REQ-005 |
| Product owner cutting a release | Publish a version without building it by hand | P2 | Pushing a version tag publishes a GitHub Release once the checks pass | REQ-007, REQ-008 |
| Project owner installing ai-team | Download a released version | P2 | The release holds the wheel, the source distribution and the command reference for that tag | REQ-008 |

## Exclusions

What this specification explicitly does NOT cover:

- **Markdown linting.** The repository is mostly markdown (skills, agents,
  `ai-process/`, guides), but linting that content is out of scope — it needs its
  own linter selection and rule-set decision.
- **Auto-format-and-commit-back.** CI never commits or pushes to any branch. On a
  violation it fails the job and the developer fixes and re-pushes.
- **CI on `dev-agent` or task/bug branches.** Triggers are limited to pull requests,
  pushes to `main`, and version tags. The `integrate`-skill workflow that merges
  task/bug branches into `dev-agent` is unchanged and gains no CI gate here.
- **Changes to the `integrate` skill or any agent/skill definition.** This is
  infrastructure only.
- **Publishing to a package index.** A release attaches its files to the GitHub
  Release only.

## Architecture

### Design Principles

- **No writes to the repository.** CI observes and reports. The only thing it
  publishes is a GitHub Release for a version tag; it never commits or pushes
  (REQ-009).
- **Independent signals.** Test failures and lint failures are reported as separate
  checks so one never masks the other (REQ-005).
- **Self-contained runner setup.** Each job brings its own `uv` and Python 3.14
  toolchain, so nothing is assumed about the shared self-hosted runner beyond Docker
  support and network access to pull that toolchain.
- **Single source of truth for tooling config.** Ruff configuration lives in
  `cli/pyproject.toml`; the workflow invokes Ruff with no inline rule overrides
  (REQ-002).
- **Releases are gated.** A release is built only for a version tag and only after
  `lint` and `test` pass (REQ-007).

### System Diagram

```
        trigger: pull_request | push to main | push of a version tag
                                   │
                                   ▼
             .github/workflows/ci.yml  (self-hosted docker runner,
                                        uv + Python 3.14 container)
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
        job: lint                                  job: test
   ruff format --check, ruff check             uv run pytest
   commands.md drift check
              └────────────────────┬────────────────────┘
                                   ▼ (version tags only, both passed)
                             job: release
   version from tag, uv build, regenerate commands.md,
   publish GitHub Release
```

### Responsibility Separation

| Component | Responsibility | Notes |
|---|---|---|
| `.github/workflows/ci.yml` | Defines the triggers and the `lint`, `test` and `release` jobs | The only workflow file |
| `lint` job | Ruff format check, Ruff lint, and the generated-docs drift check over `cli/` | Fails on any violation or drift |
| `test` job | Runs the CLI test suite | Fails on any test failure |
| `release` job | Builds and publishes a GitHub Release for a version tag | Needs `lint` and `test`; the only job granted write permission |
| `cli/pyproject.toml` | Declares Ruff as a dev dependency and holds the Ruff configuration | Single source of truth for lint/format rules |

### Alternatives Considered

- **Installing `uv` on the runner with the `astral-sh/setup-uv` action.** The original
  design provisioned the toolchain with this action. It was replaced by running every
  job in the `ghcr.io/astral-sh/uv:python3.14-trixie-slim` container, which brings
  `uv` and Python 3.14 together and keeps the shared self-hosted runner free of
  project-specific setup (CR-003).

## Interfaces

**Exposed — status checks (REQ-001, REQ-005).** The workflow reports two status
checks, named `lint` and `test`, on every pull request and every commit pushed to
`main`. Each reports pass or fail on its own.

**Exposed — triggers (REQ-001, REQ-007).** **Contract:** the workflow runs on
every `pull_request` event; on a push to the `main` branch; and on a push of a tag
matching `MAJOR.MINOR.PATCH` or `MAJOR.MINOR.PATCH-<suffix>`, where each part is
one or more digits. No other branch or tag push starts it.

**Exposed — drift message (REQ-003).** When the command reference is stale, the
`lint` job fails with the error
`cli/docs/commands.md is out of date. Run 'bash cli/scripts/gen_docs.sh' and commit the result.`
and shows the difference.

**Exposed — GitHub Release (REQ-008).** **Contract:** for a version tag, a GitHub
Release named exactly after the tag, with release notes generated by GitHub and
three kinds of attached file: the wheel (`*.whl`), the source distribution
(`*.tar.gz`) and `commands.md`. The package version is the tag with its first `-`
replaced by `+` (a PEP 440 local version), so `1.2.3` builds `1.2.3` and
`1.2.3-rc.1` builds `1.2.3+rc.1`. Builds that are not for a tag use the placeholder
version `0.0.0`.

**Consumed.**
- The Ruff configuration in `cli/pyproject.toml` (see Configuration Requirements).
- The CLI test suite under `cli/tests/`, run with `uv run pytest` from `cli/`.
- `cli/scripts/gen_docs.sh`, the command-reference generator owned by S-008.
- The package build with `uv build` from `cli/`, which takes its version from
  `SETUPTOOLS_SCM_PRETEND_VERSION`.

## Workflow

```
Contributor pushes a branch and opens a PR (or a commit lands on main)   (REQ-001)
  ↓
GitHub dispatches ci.yml to the self-hosted runner
  ↓
lint and test jobs each: container → shallow checkout → uv sync           (REQ-006)
  ↓
lint: ruff format --check + ruff check + commands.md drift check          (REQ-002, REQ-003)
test: uv run pytest                                                       (REQ-004)
  ↓
Each job reports an independent pass/fail status check                    (REQ-005)
  ↓
On failure: contributor fixes locally and re-pushes; CI never auto-fixes  (REQ-009)
On success: both checks green — ★ product owner review and merge proceed as before

★ Product owner pushes a version tag
  ↓
lint and test run as above
  ↓
If either fails: no release job runs and nothing is published             (REQ-007)
If both pass: release builds and publishes the GitHub Release             (REQ-008)
```

Failure paths: a push to any other branch or a non-matching tag starts no run
(REQ-001). When no runner with the required labels is available, jobs stay queued and
no check reports (see Configuration Requirements).

## Behavioral Requirements

### REQ-001 — Triggers

The CI workflow SHALL run the `lint` and `test` jobs on every pull request, on every
push to `main`, and on every push of a tag matching `MAJOR.MINOR.PATCH` or
`MAJOR.MINOR.PATCH-<suffix>`, and SHALL NOT run on any other push.

#### AC-001.1 — Pull request

- **Given:** a branch with at least one commit not on `main`
- **When:** a pull request is opened from it
- **Then:** the pull request shows a `lint` check and a `test` check

**Verification:** Demonstration: open a pull request and observe both checks; inspect
the `on:` block of `.github/workflows/ci.yml` for the `pull_request` trigger.

#### AC-001.2 — Push to `main` and version tag

- **Given:** the workflow is on `main`
- **When:** a commit is pushed to `main`, or the tag `1.2.3` or `1.2.3-rc.1` is pushed
- **Then:** the workflow runs `lint` and `test` for that commit

**Verification:** Inspection: the `on.push` block lists the `main` branch and both
tag patterns.

#### AC-001.3 — Other branches and tags

- **Given:** the workflow is on `main`
- **When:** a commit is pushed to `dev-agent` or a task branch with no pull request,
  or the tag `v1.2.3` is pushed
- **Then:** no workflow run starts

**Verification:** Inspection: no branch other than `main` is listed, and `v1.2.3`
matches neither tag pattern.

### REQ-002 — Formatting and lint check

The `lint` job SHALL run the Ruff format check and the Ruff lint check over `cli/`,
using only the configuration in `cli/pyproject.toml`, and SHALL fail when either
reports a violation.

#### AC-002.1 — Clean code passes

- **Given:** `uv run ruff format --check .` and `uv run ruff check .` both pass in
  `cli/`
- **When:** the `lint` job runs on that commit
- **Then:** the Ruff steps of `lint` pass

**Verification:** Demonstration: the `lint` check on a pull request whose local Ruff
checks pass reports success (as on pull request #51).

#### AC-002.2 — Violation fails

- **Given:** a commit with a file under `cli/` that Ruff would reformat, or with a
  lint violation such as an unused import
- **When:** the `lint` job runs
- **Then:** `lint` fails and its log names the offending file

**Verification:** Inspection: the workflow runs `uv run ruff format --check .` and
`uv run ruff check .` in `cli/` with no extra arguments; both exit non-zero on a
violation, which fails the job.

### REQ-003 — Command reference is current

The `lint` job SHALL regenerate `cli/docs/commands.md` with
`cli/scripts/gen_docs.sh` and SHALL fail, with the fix command in its error, when the
result differs from the committed file.

#### AC-003.1 — Stale reference fails

- **Given:** a commit that changes a CLI command's help text without regenerating
  `cli/docs/commands.md`
- **When:** the `lint` job runs
- **Then:** `lint` fails, shows the difference, and reports the drift message from
  Interfaces

**Verification:** Inspection: the drift step compares a copy of the committed file
with the regenerated one and exits 1 with the error on any difference.

#### AC-003.2 — Current reference passes

- **Given:** a commit whose `cli/docs/commands.md` was regenerated after its last CLI
  change
- **When:** the `lint` job runs
- **Then:** the drift step passes

**Verification:** Demonstration: the `lint` check passes on `main`.

### REQ-004 — Test suite

The `test` job SHALL run the full CLI test suite with `uv run pytest` in `cli/` and
SHALL fail when any test fails or errors.

#### AC-004.1 — Failing test fails the check

- **Given:** a commit where one test under `cli/tests/` fails
- **When:** the `test` job runs
- **Then:** `test` fails and its log names the failing test

**Verification:** Inspection: the job's last step is `uv run pytest` in `cli/` with
no test selection, and pytest exits non-zero on any failure.

#### AC-004.2 — Passing suite passes the check

- **Given:** a commit where `uv run pytest` passes locally
- **When:** the `test` job runs
- **Then:** `test` passes

**Verification:** Demonstration: the `test` check passes on `main`.

### REQ-005 — Independent checks

The `lint` and `test` jobs SHALL run independently, and each SHALL report its own
result whatever the other's result.

#### AC-005.1 — Lint failure does not hide test results

- **Given:** a commit with a Ruff violation and a passing test suite
- **When:** the workflow runs
- **Then:** `lint` reports failure and `test` reports success

**Verification:** Inspection: neither job declares `needs:` on the other.

### REQ-006 — Shallow checkout

The `lint` and `test` jobs SHALL check out only the triggering commit, without
history, and the CLI test suite SHALL pass in such a checkout.

#### AC-006.1 — Tests need no history

- **Given:** a test that reads git history beyond the checked-out commit
- **When:** the `test` job runs
- **Then:** the test fails in CI, so such a test cannot be merged

**Verification:** Inspection: `lint` and `test` use `actions/checkout@v6` with its
default depth; only `release` sets `fetch-depth: 0`.

### REQ-007 — Gated release

The `release` job SHALL run only for a version-tag push and only after `lint` and
`test` both pass.

#### AC-007.1 — Release after passing checks

- **Given:** a commit on which `lint` and `test` pass
- **When:** the tag `1.2.3` is pushed for it
- **Then:** the `release` job runs

**Verification:** Inspection: `release` has `needs: [lint, test]` and runs only when
the ref starts with `refs/tags/`.

#### AC-007.2 — No release after a failed check

- **Given:** a tagged commit on which `test` fails
- **When:** the workflow runs for the tag
- **Then:** `release` is skipped and no GitHub Release is created

**Verification:** Inspection: `needs: [lint, test]` skips `release` when either job
fails.

#### AC-007.3 — No release outside tags

- **Given:** a pull request or a push to `main`
- **When:** the workflow runs
- **Then:** `release` is skipped

**Verification:** Inspection: the `release` condition is false for any ref outside
`refs/tags/`.

### REQ-008 — Release contents

The `release` job SHALL publish a GitHub Release named after the tag, with generated
release notes, the wheel, the source distribution and `commands.md` attached, and with
the package version derived from the tag as defined in Interfaces.

#### AC-008.1 — Plain version tag

- **Given:** lint and test pass on a commit tagged `1.2.3`
- **When:** `release` runs
- **Then:** a GitHub Release named `1.2.3` exists with generated notes, a wheel and
  source distribution of version `1.2.3`, and `commands.md`

**Verification:** Demonstration: the GitHub Release for the most recent version tag
holds the three kinds of file and its wheel filename carries the tag's version.

#### AC-008.2 — Tag with a suffix

- **Given:** lint and test pass on a commit tagged `1.2.3-rc.1`
- **When:** `release` runs
- **Then:** the built packages carry version `1.2.3+rc.1` and the Release is named
  `1.2.3-rc.1`

**Verification:** Inspection: the version step replaces the first `-` in the tag
name with `+` and passes it to `uv build` through `SETUPTOOLS_SCM_PRETEND_VERSION`.

## Quality Requirements

### REQ-009 — No repository writes

The workflow SHALL NOT commit, push or change any branch or tag, and SHALL grant
write permission to the `release` job only, which uses it only to publish the GitHub
Release.

#### AC-009.1 — Write permission is confined to release

- **Given:** the workflow file on `main`
- **When:** its job permissions are read
- **Then:** only `release` declares `contents: write`, and no step in any job runs
  `git commit`, `git push` or `git tag`

**Verification:** Inspection of `.github/workflows/ci.yml`.

No performance, availability or run-time target was agreed for the checks, so none
is set here.

## Configuration Requirements

**Self-hosted runner** (REQ-001)
- **What must exist:** a runner registered for the repository with the `self-hosted`
  and `docker` labels.
- **Where it lives:** the repository's GitHub Actions runner settings.
- **Constraints:** must run job containers and reach `ghcr.io` and the package mirrors
  the jobs install from.
- **Missing-value behaviour:** jobs stay queued and no check reports.

**Release permission** (REQ-009)
- **What must exist:** `contents: write` for the release job only.
- **Where it lives:** the job's `permissions` in the workflow file.
- **Constraints:** the release job is the only job the workflow grants write permission.
- **Missing-value behaviour:** publishing the Release fails; nothing else is affected.

**Ruff configuration** (REQ-002)
- **What must exist:** `ruff` in the `dev` dependency group, a Python 3.14 target
  matching `requires-python`, a line length of 88, and the lint rule selection `E`,
  `F` and `I` with `E501` ignored, so line length is left to the formatter.
- **Where it lives:** `cli/pyproject.toml`.
- **Constraints:** the workflow passes no rule options of its own.
- **Missing-value behaviour:** without the dependency, `uv run ruff` fails and `lint`
  fails; without the settings, Ruff falls back to its defaults and `lint` reports
  against different rules.

**Placeholder package version** (REQ-008)
- **What must exist:** `SETUPTOOLS_SCM_PRETEND_VERSION` set to `0.0.0` for every job,
  and to the tag-derived version for the release build.
- **Where it lives:** the workflow's `env` and the release build step.
- **Constraints:** a PEP 440 version.
- **Missing-value behaviour:** the build derives its version from git history, which
  the shallow checkout of `lint` and `test` does not have.

## Assumptions and Dependencies

- **GitHub Actions hosts the workflow**, and the repository is on GitHub. Status
  checks, triggers and Releases all depend on it.
- **The self-hosted runner has Docker and outbound network access.** Confirmed in
  CR-003: every job pulls its container from `ghcr.io` and installs git with
  `apt-get`. Without either, no job starts.
- **The `ghcr.io/astral-sh/uv:python3.14-trixie-slim` image** provides `uv` and
  Python 3.14. If it is withdrawn or changes Python version, every job fails at
  container start or at `uv sync`.
- **`actions/checkout@v6` and `softprops/action-gh-release@v2`** check out the
  repository and publish the Release. A breaking change in either fails the job that
  uses it.
- **`cli/scripts/gen_docs.sh` (S-008)** regenerates the command reference
  deterministically. If its output varied between runs, REQ-003 would fail on
  unchanged code.

## Success Criteria

1. Every pull request and every commit on `main` shows a `lint` and a `test` check,
   each passed or failed (REQ-001, REQ-002, REQ-004, REQ-005).
2. A pull request that changes CLI help text without regenerating
   `cli/docs/commands.md` shows a failed `lint` check with the drift message
   (REQ-003).
3. Pushing a version tag on a commit that passes both checks produces a GitHub
   Release named after the tag with the wheel, the source distribution and
   `commands.md` attached (REQ-007, REQ-008).
4. No commit or tag in the repository was created by the CI workflow (REQ-009).

## Implementation Order

All phases are delivered: Ruff adoption with the one-time formatting pass, the
workflow with `lint` and `test`, and verification on a real pull request. The
generated-docs drift check and the `release` job were added to the workflow later
(see the Amendment Log). Later changes follow the amendment flow.

## Open Questions

None. The three questions left open at approval are answered from the repository
(CR-003): the Ruff rule selection is recorded under Configuration Requirements; the
pinned actions and the container image under Assumptions and Dependencies; and the
runner's network access is confirmed there too.

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-20 | Moved out of `specs/archive/` as S-010 (was a duplicate `S-001`). The workflow contract now matches `.github/workflows/ci.yml`: version-tag triggers; jobs in the `uv` Python 3.14 container on the self-hosted docker runner; `actions/checkout@v6`; the `commands.md` drift check in `lint` (the exclusion of that check is removed); the `release` job (`contents: write`, publishes a GitHub Release, commits nothing); shallow checkout for `lint` and `test`. Ruff selection pinned to `E`, `F`, `I` ignoring `E501`. Resolved the three open questions from `cli/pyproject.toml` and `.github/workflows/ci.yml`; the embedded YAML and TOML became prose. Driven by CR-003 §10 and Architecture Consistency Review finding F5. | The spec was still `approved` in the archive and the only written contract for CI, but its exclusions, triggers and runner setup no longer matched the workflow. | None in flight |
| 2026-10-25 | Restructured to the spec format from PR #51: added Users and Journeys, Alternatives Considered, Interfaces, Behavioral Requirements REQ-001–REQ-008 with acceptance scenarios, Quality Requirements REQ-009, Assumptions and Dependencies, and Success Criteria; the Components section was split into Interfaces, requirements and Configuration Requirements, and its workflow line references were dropped. Format restructure only, no scope change, so the version is unchanged. | The validator now rejects approved specs without the new sections. | None |
| 2026-10-26 | The actor called "the human" is now named the product owner, as S-000 defines it. Wording only. Driven by PR #59. | One name for the main actor across the framework and its specs. | None |
