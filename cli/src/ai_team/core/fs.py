"""
ai_team.core.fs — single chokepoint for filesystem mutation of AI-team artifacts.

Provides:
  - ``read_artifact(path, kind)`` — parse an artifact file and return ``(model, body)``.
  - ``write_artifact(path, model, body, *, overwrite=False)`` — write an artifact file;
    refuses to overwrite unless ``overwrite=True``.
  - ``move_artifact(src, dest)`` — atomically rename a file; refuses if dest exists;
    no-op if src == dest after path normalisation.
  - ``update_status(path, new_status)`` — rewrite only the ``status`` frontmatter field,
    preserving all other frontmatter content and the body bytes verbatim.
  - ``ArtifactNotFound`` — raised when a required source file is absent.
  - ``ArtifactExists`` — raised when a write or move would overwrite an existing file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from ai_team.core.models import (
    Adr,
    Bug,
    ChangeRequest,
    Spec,
    Task,
    dump_frontmatter,
    parse_adr,
    parse_bug,
    parse_change_request,
    parse_spec,
    parse_task,
)

ArtifactKind = Literal["task", "bug", "spec", "adr", "change-request"]
ArtifactModel = Task | Bug | Spec | Adr | ChangeRequest

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ArtifactNotFound(FileNotFoundError):
    """Raised when an artifact file that must exist is not found at the given path."""


class ArtifactExists(FileExistsError):
    """Raised when an operation would silently overwrite an existing artifact file."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Maps kind literal to the corresponding parse_* function.
_PARSERS = {
    "task": parse_task,
    "bug": parse_bug,
    "spec": parse_spec,
    "adr": parse_adr,
    "change-request": parse_change_request,
}


def _extract_body(path: Path) -> str:
    """Return the markdown body that follows the closing ``---`` frontmatter fence.

    The body is the text after the ``---\\n\\n`` separator that ``dump_frontmatter``
    produces.  The one blank line between the fence and the body content is
    consumed here so that a parse → dump → parse cycle yields the same body string.
    """
    text = path.read_text(encoding="utf-8")
    # Skip opening fence (first 3 chars are "---"), then find the closing fence.
    rest = text[3:]
    close_idx = rest.find("\n---")
    # Advance past the "\n---\n" sequence (4 chars for "\n---" + 1 for "\n").
    body_start = close_idx + 5
    body = rest[body_start:]
    # dump_frontmatter always writes "---\n\n<body>", so the file has a blank
    # line between the fence and body content.  Strip exactly one leading
    # newline so that the body round-trips consistently.
    if body.startswith("\n"):
        body = body[1:]
    return body


def _infer_kind(path: Path) -> ArtifactKind:
    """Infer the artifact kind of *path*.

    Change-requests are recognised by their ``CR-`` filename prefix, because
    their frontmatter fields are a subset of an ADR's. Otherwise the heuristic
    inspects unique field names present in the frontmatter block.

      - ``severity`` key  → bug
      - ``assigned-role`` key → task
      - ``author`` key → spec
      - otherwise → adr
    """
    if path.name.startswith("CR-"):
        return "change-request"
    text = path.read_text(encoding="utf-8")
    # Extract only the text between the two --- fences.
    parts = text.split("---")
    frontmatter = parts[1] if len(parts) >= 3 else ""
    if "severity:" in frontmatter:
        return "bug"
    if "assigned-role:" in frontmatter:
        return "task"
    if "author:" in frontmatter:
        return "spec"
    return "adr"


def _write_atomically(path: Path, content: str) -> None:
    """Write *content* to *path* atomically via a sibling temp file.

    Uses ``os.replace`` to ensure the destination is updated as a single
    operation, avoiding partially-written files on failure.
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp~")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_artifact(
    path: Path | str,
    kind: ArtifactKind,
) -> tuple[ArtifactModel, str]:
    """Parse an artifact file and return ``(model, body)``.

    The returned *body* is the markdown text that follows the closing ``---``
    frontmatter fence (with the blank separator line consumed so that
    ``dump_frontmatter(model, body)`` reconstructs the original file exactly).

    Parameters
    ----------
    path:
        Path to the artifact ``.md`` file.
    kind:
        The artifact kind; determines which ``parse_*`` function is used.

    Returns
    -------
    tuple[model, body]
        A ``(model, body)`` pair for the requested kind.

    Raises
    ------
    ArtifactNotFound
        When *path* does not exist.
    FrontmatterError
        When the frontmatter block is absent or malformed (propagated from models).
    """
    path = Path(path)
    if not path.exists():
        raise ArtifactNotFound(f"Artifact file not found: {path!s}")

    parse = _PARSERS[kind]
    model = parse(path)
    body = _extract_body(path)
    return model, body


def write_artifact(
    path: Path | str,
    model: ArtifactModel,
    body: str,
    *,
    overwrite: bool = False,
) -> None:
    """Write an artifact file to *path*.

    Uses ``dump_frontmatter`` to serialise *model* + *body* into a complete
    markdown file, then writes it atomically via ``os.replace``.

    Parameters
    ----------
    path:
        Destination path for the artifact file.
    model:
        The model instance to serialise.
    body:
        The markdown body to append after the frontmatter block.
    overwrite:
        When ``False`` (default), raises :class:`ArtifactExists` if *path*
        already exists.  When ``True``, the existing file is replaced.

    Raises
    ------
    ArtifactExists
        When *path* exists and ``overwrite=False``.
    """
    path = Path(path)
    if path.exists() and not overwrite:
        raise ArtifactExists(
            f"Artifact already exists at {path!s}; pass overwrite=True to replace it."
        )

    content = dump_frontmatter(model, body)
    _write_atomically(path, content)


def move_artifact(src: Path | str, dest: Path | str) -> None:
    """Atomically rename *src* to *dest*.

    Uses ``os.replace`` for atomicity.  When *src* and *dest* resolve to the
    same path (after normalisation), the function returns immediately without
    touching the filesystem.

    Parameters
    ----------
    src:
        The current path of the artifact.
    dest:
        The desired path for the artifact.

    Raises
    ------
    ArtifactNotFound
        When *src* does not exist.
    ArtifactExists
        When *dest* already exists (and is not the same file as *src*).
    """
    src = Path(src).resolve()
    dest = Path(dest).resolve()

    # No-op when src and dest are the same path after normalisation.
    if src == dest:
        return

    if not src.exists():
        raise ArtifactNotFound(f"Source artifact not found: {src!s}")

    if dest.exists():
        raise ArtifactExists(
            f"Destination already exists: {dest!s}; cannot move artifact there."
        )

    os.replace(src, dest)


def update_status(
    path: Path | str, new_status: str, kind: ArtifactKind | None = None
) -> None:
    """Rewrite the ``status`` frontmatter field in *path*, preserving everything else.

    For a task or bug, moving to ``blocked`` also records the previous status in
    ``blocked_from``, and moving to any other status removes that field.

    Reads the artifact using the appropriate ``parse_*`` function (which
    captures the round-trip ``_source_map``), updates ``model.status``, then
    writes back via ``dump_frontmatter`` so that YAML comments and key order
    survive the rewrite.

    The artifact kind is inferred from the filename and frontmatter field names
    unless *kind* is given.

    Parameters
    ----------
    path:
        Path to the artifact file.
    new_status:
        The new status string to write into the frontmatter.

    Raises
    ------
    ArtifactNotFound
        When *path* does not exist.
    FrontmatterError
        When the frontmatter block is absent or malformed.
    """
    path = Path(path)
    if not path.exists():
        raise ArtifactNotFound(f"Artifact file not found: {path!s}")

    if kind is None:
        kind = _infer_kind(path)
    model, body = read_artifact(path, kind)
    if hasattr(model, "blocked_from"):
        # Remember the status a task or bug held before it was blocked so that
        # `unblock` can restore it; any other transition clears the record.
        model.blocked_from = model.status if new_status == "blocked" else None
    model.status = new_status
    content = dump_frontmatter(model, body)
    _write_atomically(path, content)
