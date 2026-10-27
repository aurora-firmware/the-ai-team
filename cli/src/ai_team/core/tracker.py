"""
ai_team.core.tracker — the local work-item tracker (spec S-006).

Tasks, bugs, and change-requests live outside version control in one tracker
folder per repository. Lifecycle state is the frontmatter ``status`` field;
no folder or filename encodes it.

Provides:
  - ``resolve_tracker_dir(repo)`` — the tracker folder configured by
    ``[tracker] dir`` in ``.ai-team.toml`` (default ``.ai-team/tracker``).
    Relative paths resolve against the project's folder in the repository's
    main working tree so that every git worktree shares one tracker.
  - ``TASK_STATUSES``, ``BUG_STATUSES``, ``CHANGE_REQUEST_STATUSES`` — the
    allowed ``status`` values per work-item kind.
  - ``iter_items(folder)`` / ``find_item(folder, item_id)`` — enumerate and
    look up work-item files.

This module has no Typer dependency and does not import the locator.
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

DEFAULT_TRACKER_DIR = ".ai-team/tracker"

TASK_STATUSES = (
    "planned",
    "pending",
    "in-progress",
    "blocked",
    "completed",
    "cancelled",
)
BUG_STATUSES = ("open", "in-progress", "resolved")
CHANGE_REQUEST_STATUSES = ("pending", "approved", "rejected")


def _toml_tracker_dir(repo: Path) -> str | None:
    """Return the ``[tracker] dir`` value from ``repo/.ai-team.toml``, if any."""
    toml_path = repo / ".ai-team.toml"
    if not toml_path.is_file():
        return None
    try:
        with toml_path.open("rb") as fh:
            data = tomllib.load(fh)
    except OSError, tomllib.TOMLDecodeError:
        return None
    value = data.get("tracker", {}).get("dir")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _git(repo: Path, *args: str) -> str | None:
    """Return the stdout of ``git -C repo <args>``, or None when git fails."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError, subprocess.CalledProcessError:
        return None
    return completed.stdout


def main_worktree(repo: Path) -> Path:
    """Return the main working tree of the git repository containing *repo*.

    This is the first entry of ``git worktree list``, which every linked
    worktree reports identically. When the repository is bare (a "bare repo
    plus worktrees" layout), there is no main working tree; the bare repository
    folder itself is used instead, so its worktrees share one anchor and
    sibling bare repositories never share a tracker. Falls back to *repo* when
    *repo* is not inside a git repository or git is unavailable.
    """
    listing = _git(repo, "worktree", "list", "--porcelain")
    if not listing:
        return repo
    first_line = listing.splitlines()[0]
    return Path(first_line.removeprefix("worktree "))


def _project_offset(repo: Path) -> Path:
    """Return the path of *repo* relative to the top of its working tree."""
    prefix = _git(repo, "rev-parse", "--show-prefix")
    return Path(prefix.strip()) if prefix else Path()


def resolve_tracker_dir(repo: Path) -> Path:
    """Return the absolute tracker folder for the project rooted at *repo*.

    *repo* is the folder holding ``.ai-team.toml``. Absolute and ``~`` paths
    are used as given. Relative paths resolve against the same folder in the
    repository's main working tree, so a Developer in a linked worktree and a
    loop in the main checkout read and write the same tracker, and a project
    that lives in a subfolder of its git repository keeps its tracker beside
    its ``.ai-team.toml``.
    """
    configured = Path(_toml_tracker_dir(repo) or DEFAULT_TRACKER_DIR).expanduser()
    if configured.is_absolute():
        return configured
    return main_worktree(repo) / _project_offset(repo) / configured


def is_inside(path: Path, directory: Path) -> bool:
    """Return True when *path* is *directory* or lies below it."""
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def _should_skip(path: Path) -> bool:
    return path.name == ".gitkeep" or path.match("TEMPLATE-*.md")


def iter_items(folder: Path) -> list[Path]:
    """Return the sorted work-item markdown files directly inside *folder*."""
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.glob("*.md")
        if path.is_file() and not _should_skip(path)
    )


def find_item(folder: Path, item_id: str) -> Path | None:
    """Return the file in *folder* whose name is ``<item_id>.md`` or ``<item_id>-*.md``."""
    for path in iter_items(folder):
        if path.stem == item_id or path.stem.startswith(f"{item_id}-"):
            return path
    return None
