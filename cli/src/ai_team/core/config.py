"""
ai_team.core.config — shared ``.ai-team.toml`` settings and placeholder rendering.

Provides:
  - ``is_valid_project_dir(value)`` — whether ``[project] dir`` is a usable
    relative folder, at any depth (``ai-team`` or ``docs/ai-team``).
  - ``is_valid_branch_name(value)`` — whether a ``[git]`` branch setting is a
    usable branch name.
  - ``read_marker(repo)`` — the parsed marker, or an empty table when it is
    missing or unreadable.
  - ``integration_branch(repo)`` — the configured integration branch.
  - ``release_branch(repo)`` — the configured release branch.
  - ``render_placeholders(text, ...)`` — fill the ``{{project_dir}}``,
    ``{{integration_branch}}`` and ``{{release_branch}}`` placeholders used by
    the packaged sources.

This module has no Typer dependency and imports nothing else from ai_team.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path, PurePosixPath

DEFAULT_INTEGRATION_BRANCH = "dev-agent"
"""Branch that task, bug, and planning work integrates into by default."""

DEFAULT_RELEASE_BRANCH = "main"
"""Branch the integration branch merges into after Gate 5 sign-off, by default."""

PROJECT_DIR_PLACEHOLDER = "{{project_dir}}"
INTEGRATION_BRANCH_PLACEHOLDER = "{{integration_branch}}"
RELEASE_BRANCH_PLACEHOLDER = "{{release_branch}}"

_BRANCH_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")


def is_valid_project_dir(value: object) -> bool:
    """Return True for a relative folder path with no ``.`` or ``..`` components."""
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if value.startswith("/") or value.endswith("/"):
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def is_valid_branch_name(value: object) -> bool:
    """Return True for a plain git branch name (no spaces, ``..``, or ``//``)."""
    if not isinstance(value, str) or _BRANCH_PATTERN.fullmatch(value) is None:
        return False
    return not (
        ".." in value
        or "//" in value
        or value.endswith(("/", ".", ".lock"))
        or "/." in value
    )


def read_marker(repo: Path) -> dict:
    """Return the parsed ``repo/.ai-team.toml``, or ``{}`` when absent or invalid."""
    marker = repo / ".ai-team.toml"
    if not marker.is_file():
        return {}
    try:
        with marker.open("rb") as stream:
            return tomllib.load(stream)
    except OSError, tomllib.TOMLDecodeError:
        return {}


def _table_value(data: dict, table: str, key: str) -> object:
    section = data.get(table)
    return section.get(key) if isinstance(section, dict) else None


def marker_project_dir(data: dict) -> str | None:
    """Return the valid ``[project] dir`` of a parsed marker, else None."""
    value = _table_value(data, "project", "dir")
    return value if is_valid_project_dir(value) else None


def marker_integration_branch(data: dict) -> str | None:
    """Return the valid ``[git] integration_branch`` of a parsed marker, else None."""
    value = _table_value(data, "git", "integration_branch")
    return value if is_valid_branch_name(value) else None


def marker_release_branch(data: dict) -> str | None:
    """Return the valid ``[git] release_branch`` of a parsed marker, else None."""
    value = _table_value(data, "git", "release_branch")
    return value if is_valid_branch_name(value) else None


def integration_branch(repo: Path) -> str:
    """Return the integration branch configured for the project at *repo*."""
    return marker_integration_branch(read_marker(repo)) or DEFAULT_INTEGRATION_BRANCH


def release_branch(repo: Path) -> str:
    """Return the release branch configured for the project at *repo*."""
    return marker_release_branch(read_marker(repo)) or DEFAULT_RELEASE_BRANCH


def render_placeholders(
    text: str, *, project_dir: str, integration_branch: str, release_branch: str
) -> str:
    """Replace the packaged-source placeholders with the project's settings."""
    return (
        text.replace(PROJECT_DIR_PLACEHOLDER, project_dir)
        .replace(INTEGRATION_BRANCH_PLACEHOLDER, integration_branch)
        .replace(RELEASE_BRANCH_PLACEHOLDER, release_branch)
    )
