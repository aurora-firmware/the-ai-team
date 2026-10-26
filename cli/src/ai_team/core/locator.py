"""
ai_team.core.locator — locate the consuming project's root directory.

Resolution order:
  1. Explicit ``root`` keyword argument.
  2. ``AI_TEAM_ROOT`` environment variable.
  3. Walk up from ``cwd`` looking for ``.ai-team.toml``; use its ``[project] dir``
     setting as the artifact-folder name.
  4. Walk up from ``cwd`` looking for a folder whose name matches ``project_dir``
     (default ``DEFAULT_PROJECT_DIR``, ``"ai-team"``).
  5. Raise ``ProjectRootNotFound`` with a message naming the searched paths and
     suggesting ``ai-team init``.

This module has no Typer dependency and may be imported from anywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ai_team.core.config import marker_project_dir, read_marker
from ai_team.core.tracker import resolve_tracker_dir

DEFAULT_PROJECT_DIR = "ai-team"
"""Artifact folder used when ``.ai-team.toml`` sets no ``[project] dir``."""


class ProjectRootNotFound(RuntimeError):
    """Raised when no project root can be resolved from the given cwd."""


@dataclass(frozen=True)
class ProjectRoot:
    """Absolute paths to every AI-team artifact directory in a project.

    Specs, ADRs, and docs live in the project directory under version control.
    Tasks, bugs, and change-requests live in the local tracker (spec S-006).
    """

    repo: Path
    """The repository root (the directory that contains the project folder)."""

    project_dir: Path
    """The top-level artifact directory (e.g. ``repo/project``)."""

    specs: Path
    """``project_dir/specs``."""

    tracker: Path
    """The local work-item tracker folder (``[tracker] dir``; outside version control)."""

    tasks: Path
    """``tracker/tasks`` — task files; state is the ``status`` field."""

    bugs: Path
    """``tracker/bugs`` — bug files; state is the ``status`` field."""

    change_requests: Path
    """``tracker/change-requests`` — change-request files."""

    decisions: Path
    """``project_dir/decisions``."""

    docs: Path
    """``project_dir/docs``."""

    @classmethod
    def _from_repo_and_project_dir_name(
        cls, repo: Path, project_dir_name: str
    ) -> "ProjectRoot":
        """Build a ProjectRoot from a repo root and the artifact folder name."""
        pd = repo / project_dir_name
        tracker = resolve_tracker_dir(repo)
        return cls(
            repo=repo,
            project_dir=pd,
            specs=pd / "specs",
            decisions=pd / "decisions",
            docs=pd / "docs",
            tracker=tracker,
            tasks=tracker / "tasks",
            bugs=tracker / "bugs",
            change_requests=tracker / "change-requests",
        )


def find_project_root(
    cwd: Path,
    *,
    root: Path | None = None,
    project_dir: str = DEFAULT_PROJECT_DIR,
) -> ProjectRoot:
    """Locate the project root and return a ``ProjectRoot`` with all artifact paths.

    Parameters
    ----------
    cwd:
        The directory to start searching from.  Must be an absolute path when
        the caller relies on ``ProjectRoot.repo`` being absolute, but any
        ``Path`` is accepted (it is resolved internally).
    root:
        When provided, treat this directory as the repo root and skip all
        environment-variable and filesystem searches.  The ``project_dir``
        folder must still exist under ``root``.
    project_dir:
        Relative path of the artifact folder (default ``"ai-team"``; nested
        paths such as ``docs/ai-team`` are accepted).  Used
        when no ``.ai-team.toml`` override is found.

    Raises
    ------
    ProjectRootNotFound
        When no project root can be resolved.  The message names the paths
        that were searched and suggests ``ai-team init``.
    """
    cwd = cwd.resolve()

    # ------------------------------------------------------------------
    # Strategy 1: explicit root= argument.
    # ------------------------------------------------------------------
    if root is not None:
        repo = root.resolve()
        dir_name = _toml_project_dir(repo) or project_dir
        if (repo / dir_name).is_dir():
            return ProjectRoot._from_repo_and_project_dir_name(repo, dir_name)
        raise ProjectRootNotFound(
            f"No '{dir_name}/' folder found under the provided --root {repo!s}. "
            "Run 'ai-team init' to bootstrap the project structure."
        )

    # ------------------------------------------------------------------
    # Strategy 2: AI_TEAM_ROOT environment variable.
    # ------------------------------------------------------------------
    env_root = os.environ.get("AI_TEAM_ROOT")
    if env_root:
        repo = Path(env_root).resolve()
        dir_name = _toml_project_dir(repo) or project_dir
        if (repo / dir_name).is_dir():
            return ProjectRoot._from_repo_and_project_dir_name(repo, dir_name)
        raise ProjectRootNotFound(
            f"No '{dir_name}/' folder found under AI_TEAM_ROOT={repo!s}. "
            "Run 'ai-team init' to bootstrap the project structure."
        )

    # ------------------------------------------------------------------
    # Strategy 3: Walk up looking for .ai-team.toml; use configured dir.
    # Strategy 4: Walk up looking for a folder named project_dir.
    #
    # Both strategies share a single upward walk.  At each directory we
    # check for .ai-team.toml first (strategy 3) then fall through to the
    # folder-name check (strategy 4).
    # ------------------------------------------------------------------
    searched: list[Path] = []
    candidate = cwd
    while True:
        searched.append(candidate)

        toml_dir_name = _toml_project_dir(candidate)
        if toml_dir_name is not None:
            # .ai-team.toml found; honour the configured dir name.
            if (candidate / toml_dir_name).is_dir():
                return ProjectRoot._from_repo_and_project_dir_name(
                    candidate, toml_dir_name
                )
            # TOML present but the declared folder is missing — keep walking.

        if (candidate / project_dir).is_dir():
            return ProjectRoot._from_repo_and_project_dir_name(candidate, project_dir)

        parent = candidate.parent
        if parent == candidate:
            # Reached the filesystem root without a match.
            break
        candidate = parent

    searched_str = ", ".join(str(p) for p in searched)
    raise ProjectRootNotFound(
        f"Could not locate a '{project_dir}/' directory by walking up from "
        f"{cwd!s}. Searched: {searched_str}. "
        "Run 'ai-team init' to bootstrap the project structure."
    )


def _toml_project_dir(directory: Path) -> str | None:
    """Return the usable ``[project] dir`` value from ``.ai-team.toml`` in *directory*.

    Returns ``None`` if the file does not exist, cannot be parsed, or does not
    hold a valid relative folder (any depth, no ``..``) under ``[project] dir``.
    """
    return marker_project_dir(read_marker(directory))
