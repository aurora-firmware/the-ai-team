"""
ai_team.core.models — dataclasses for AI-team artifact types parsed from
YAML frontmatter.

Provides:
  - ``Task``, ``Bug``, ``Spec``, ``Adr``, ``ChangeRequest`` dataclasses holding
    frontmatter fields.
  - ``parse_task``, ``parse_bug``, ``parse_spec``, ``parse_adr``,
    ``parse_change_request`` — read an artifact file and return the
    corresponding dataclass.
  - ``dump_frontmatter(model, body) -> str`` — serialise a model back to a complete
    markdown file (YAML frontmatter block + body).
  - ``FrontmatterError`` — raised when a required field is missing or invalid.

This module has no Typer dependency and performs only the I/O needed to read
the supplied path.

``ruamel.yaml`` in round-trip mode (``typ="rt"``) is used throughout so that
comments and key order are preserved when the caller rewrites a file.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class FrontmatterError(ValueError):
    """Raised when a frontmatter field is missing or has an invalid value.

    The message always names the problematic field and the source path so
    callers can surface a clear diagnostic.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_yaml_frontmatter(path: Path) -> CommentedMap:
    """Extract the YAML frontmatter block from *path* and return it as a CommentedMap.

    Returns a ``CommentedMap`` (the ruamel.yaml round-trip type) so that inline
    comments and key order are preserved for later use by ``dump_frontmatter``.

    Raises
    ------
    FrontmatterError
        If the file does not start with a ``---`` fence or the block is
        syntactically invalid YAML.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise FrontmatterError(f"No YAML frontmatter block found in {path!s}")

    # Find the closing --- fence (must be on its own line after the opener).
    rest = text[3:]
    close_idx = rest.find("\n---")
    if close_idx == -1:
        raise FrontmatterError(
            f"Unclosed YAML frontmatter block (missing closing ---) in {path!s}"
        )

    yaml_text = rest[:close_idx]
    yaml = YAML(typ="rt")
    try:
        data = yaml.load(yaml_text)
    except Exception as exc:
        raise FrontmatterError(
            f"YAML parse error in frontmatter of {path!s}: {exc}"
        ) from exc

    if data is None:
        return CommentedMap()
    # Return the CommentedMap directly so comments and key order are preserved.
    return data


def _require(data: CommentedMap, key: str, path: Path) -> Any:
    """Return ``data[key]`` or raise :class:`FrontmatterError` naming *key* and *path*.

    The raw YAML key (e.g. ``"assigned-role"``) is used directly in the error
    so that callers see the exact field name from the template.
    """
    if key not in data or data[key] is None:
        raise FrontmatterError(
            f"Required frontmatter field '{key}' is missing or null in {path!s}"
        )
    return data[key]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """Frontmatter fields for a task artifact."""

    id: str
    title: str
    status: str
    priority: str
    assigned_role: str  # YAML key: assigned-role
    created: str
    spec: str | None = None  # Optional reference to a spec slug
    plan: str | None = None  # Optional spec or change-request whose plan introduced it
    # Holds the original CommentedMap from parsing so comments survive dump.
    # Excluded from equality and repr so it does not affect model comparisons.
    _source_map: CommentedMap | None = field(default=None, compare=False, repr=False)


@dataclass
class Bug:
    """Frontmatter fields for a bug artifact."""

    id: str
    title: str
    severity: str
    status: str
    # Optional because legacy resolved artifacts pre-date this field requirement.
    created: str | None = None
    task: str | None = None  # Optional reference to a related task ID
    source_branch: str | None = None  # Branch a task-regression bug came from
    # Holds the original CommentedMap from parsing so comments survive dump.
    _source_map: CommentedMap | None = field(default=None, compare=False, repr=False)


@dataclass
class Spec:
    """Frontmatter fields for a specification artifact.

    Historically specs had no ``id`` in their frontmatter and were identified
    solely by their filename slug. ``ai-team spec new`` now writes an ``id``
    field (e.g. ``S-001``), so ``id`` is populated when present but remains
    optional for legacy specs that predate it.
    """

    title: str
    version: str
    status: str
    created: str
    author: str
    id: str | None = None  # Optional frontmatter id, e.g. "S-001"
    # Holds the original CommentedMap from parsing so comments survive dump.
    _source_map: CommentedMap | None = field(default=None, compare=False, repr=False)


@dataclass
class Adr:
    """Frontmatter fields for an Architecture Decision Record."""

    id: str
    title: str
    status: str
    created: str
    supersedes: str | None = None  # Optional reference to a superseded ADR ID
    # Holds the original CommentedMap from parsing so comments survive dump.
    _source_map: CommentedMap | None = field(default=None, compare=False, repr=False)


@dataclass
class ChangeRequest:
    """Frontmatter fields for a change-request artifact."""

    id: str
    title: str
    status: str
    created: str
    # Holds the original CommentedMap from parsing so comments survive dump.
    _source_map: CommentedMap | None = field(default=None, compare=False, repr=False)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_task(path: Path) -> Task:
    """Parse a task artifact file and return a :class:`Task`.

    Parameters
    ----------
    path:
        Path to the ``.md`` task file.

    Raises
    ------
    FrontmatterError
        If any required field is missing, null, or the frontmatter block is
        absent or malformed.
    """
    path = Path(path)
    data = _parse_yaml_frontmatter(path)
    return Task(
        id=str(_require(data, "id", path)),
        title=str(_require(data, "title", path)),
        status=str(_require(data, "status", path)),
        priority=str(_require(data, "priority", path)),
        assigned_role=str(_require(data, "assigned-role", path)),
        created=str(_require(data, "created", path)),
        spec=str(data["spec"]) if data.get("spec") is not None else None,
        plan=str(data["plan"]) if data.get("plan") is not None else None,
        _source_map=data,
    )


def parse_bug(path: Path) -> Bug:
    """Parse a bug artifact file and return a :class:`Bug`.

    Raises
    ------
    FrontmatterError
        If any required field is missing or the frontmatter is malformed.
    """
    path = Path(path)
    data = _parse_yaml_frontmatter(path)
    raw_created = data.get("created")
    return Bug(
        id=str(_require(data, "id", path)),
        title=str(_require(data, "title", path)),
        severity=str(_require(data, "severity", path)),
        status=str(_require(data, "status", path)),
        created=str(raw_created) if raw_created is not None else None,
        task=str(data["task"]) if data.get("task") is not None else None,
        source_branch=str(data["source_branch"])
        if data.get("source_branch") is not None
        else None,
        _source_map=data,
    )


def parse_spec(path: Path) -> Spec:
    """Parse a spec artifact file and return a :class:`Spec`.

    Note: legacy specs have no ``id`` in their frontmatter — their identifier
    is the filename slug. When ``id`` is present (as written by
    ``ai-team spec new``), it is populated on the returned model.

    Raises
    ------
    FrontmatterError
        If any required field is missing or the frontmatter is malformed.
    """
    path = Path(path)
    data = _parse_yaml_frontmatter(path)
    return Spec(
        title=str(_require(data, "title", path)),
        version=str(_require(data, "version", path)),
        status=str(_require(data, "status", path)),
        created=str(_require(data, "created", path)),
        author=str(_require(data, "author", path)),
        id=str(data["id"]) if data.get("id") is not None else None,
        _source_map=data,
    )


def parse_adr(path: Path) -> Adr:
    """Parse an ADR artifact file and return an :class:`Adr`.

    Raises
    ------
    FrontmatterError
        If any required field is missing or the frontmatter is malformed.
    """
    path = Path(path)
    data = _parse_yaml_frontmatter(path)
    return Adr(
        id=str(_require(data, "id", path)),
        title=str(_require(data, "title", path)),
        status=str(_require(data, "status", path)),
        created=str(_require(data, "created", path)),
        supersedes=str(data["supersedes"])
        if data.get("supersedes") is not None
        else None,
        _source_map=data,
    )


def parse_change_request(path: Path) -> ChangeRequest:
    """Parse a change-request artifact file and return a :class:`ChangeRequest`.

    Raises
    ------
    FrontmatterError
        If any required field is missing or the frontmatter is malformed.
    """
    path = Path(path)
    data = _parse_yaml_frontmatter(path)
    return ChangeRequest(
        id=str(_require(data, "id", path)),
        title=str(_require(data, "title", path)),
        status=str(_require(data, "status", path)),
        created=str(_require(data, "created", path)),
        _source_map=data,
    )


# ---------------------------------------------------------------------------
# Dumper
# ---------------------------------------------------------------------------

# Field definitions per model type: each entry is (yaml_key, attribute_name).
# Order here determines the key order in the dumped YAML.
_TASK_FIELDS: list[tuple[str, str]] = [
    ("id", "id"),
    ("title", "title"),
    ("status", "status"),
    ("priority", "priority"),
    ("assigned-role", "assigned_role"),
    ("created", "created"),
    ("spec", "spec"),  # optional — omitted when None
    ("plan", "plan"),  # optional — omitted when None
]

_BUG_FIELDS: list[tuple[str, str]] = [
    ("id", "id"),
    ("title", "title"),
    ("severity", "severity"),
    ("status", "status"),
    ("created", "created"),
    ("task", "task"),  # optional — omitted when None
    ("source_branch", "source_branch"),  # optional — omitted when None
]

_SPEC_FIELDS: list[tuple[str, str]] = [
    ("title", "title"),
    ("version", "version"),
    ("status", "status"),
    ("created", "created"),
    ("author", "author"),
    ("id", "id"),  # optional — omitted when None (legacy specs carry no id)
]

_ADR_FIELDS: list[tuple[str, str]] = [
    ("id", "id"),
    ("title", "title"),
    ("status", "status"),
    ("created", "created"),
    ("supersedes", "supersedes"),  # optional — omitted when None
]

_CHANGE_REQUEST_FIELDS: list[tuple[str, str]] = [
    ("id", "id"),
    ("title", "title"),
    ("status", "status"),
    ("created", "created"),
]

# Map each model type to its ordered field list.
_MODEL_FIELDS: dict[type, list[tuple[str, str]]] = {
    Task: _TASK_FIELDS,
    Bug: _BUG_FIELDS,
    Spec: _SPEC_FIELDS,
    Adr: _ADR_FIELDS,
    ChangeRequest: _CHANGE_REQUEST_FIELDS,
}


def dump_frontmatter(model: Task | Bug | Spec | Adr | ChangeRequest, body: str) -> str:
    """Serialise *model* back to a complete markdown file string.

    The output has the form::

        ---
        key: value
        ...
        ---

        <body>

    When the model was produced by a ``parse_*`` function it carries an
    internal ``_source_map`` holding the original ``CommentedMap`` from
    ruamel.yaml.  In that case, ``dump_frontmatter`` updates field values
    in-place on the source map and dumps it, so that inline comments survive
    the parse→dump cycle.  If no source map is available (e.g. the model was
    constructed by hand), a fresh ``CommentedMap`` is built from the
    ``_*_FIELDS`` ordering, preserving key order but not carrying any comments.

    Optional fields (those whose value is ``None``) are omitted from the
    output so that round-tripping a file with no optional fields produces
    clean output without extra null keys.

    Parameters
    ----------
    model:
        A :class:`Task`, :class:`Bug`, :class:`Spec`, :class:`Adr`, or
        :class:`ChangeRequest` instance.
    body:
        The markdown body text to place after the frontmatter block.

    Returns
    -------
    str
        A complete markdown file as a string: frontmatter fence + body.

    Raises
    ------
    TypeError
        If *model* is not one of the supported types.
    """
    model_type = type(model)
    if model_type not in _MODEL_FIELDS:
        raise TypeError(
            f"dump_frontmatter does not support model type {model_type.__name__!r}"
        )

    ordered_fields = _MODEL_FIELDS[model_type]
    source_map: CommentedMap | None = getattr(model, "_source_map", None)

    if source_map is not None:
        # Update the original CommentedMap in-place so comments are preserved.
        # Apply current field values; remove optional keys that became None.
        for yaml_key, attr_name in ordered_fields:
            value = getattr(model, attr_name)
            if value is None:
                # Remove the key if it is now None (optional field cleared).
                source_map.pop(yaml_key, None)
            else:
                source_map[yaml_key] = value
        cm = source_map
    else:
        # No source map: build a fresh CommentedMap with canonical key order.
        cm = CommentedMap()
        for yaml_key, attr_name in ordered_fields:
            value = getattr(model, attr_name)
            if value is None:
                # Omit optional fields when they are None.
                continue
            cm[yaml_key] = value

    # Serialise to a YAML string.
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    # ruamel folds scalars at 80 columns by default, which wraps long titles and
    # leaves trailing spaces in tracker files; a very large width keeps each
    # scalar on one line.
    yaml.width = 4096
    stream = io.StringIO()
    yaml.dump(cm, stream)
    yaml_text = stream.getvalue()

    return f"---\n{yaml_text}---\n\n{body}"
