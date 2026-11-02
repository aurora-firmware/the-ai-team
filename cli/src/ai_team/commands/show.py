"""`ai-team show` command for displaying artifact files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
from rich.markdown import Markdown
from typer.core import TyperGroup

from ai_team.commands._shared import artifact_object, project_root
from ai_team.core.fs import read_artifact
from ai_team.core.locator import ProjectRoot
from ai_team.core.tracker import iter_items
from ai_team.render import console, print_json

NAME = "show"


class _ShowGroup(TyperGroup):
    """Allow options after positional args for callback-style default command."""

    allow_interspersed_args = True


app = typer.Typer(
    help="Show an artifact by identifier.",
    invoke_without_command=True,
    cls=_ShowGroup,
)


Kind = Literal["task", "bug", "change-request", "spec", "adr"]


def _search_roots(root: ProjectRoot) -> list[tuple[Kind, Path]]:
    return [
        ("task", root.tasks),
        ("bug", root.bugs),
        ("change-request", root.change_requests),
        ("spec", root.specs),
        ("adr", root.decisions),
    ]


def _artifact_files(roots: list[tuple[Kind, Path]]) -> list[tuple[Kind, Path]]:
    files: list[tuple[Kind, Path]] = []
    for kind, folder in roots:
        files.extend((kind, path) for path in iter_items(folder))
    return files


def _matches_identifier(identifier: str, kind: Kind, path: Path) -> bool:
    token = identifier.lower()
    if token in path.stem.lower():
        return True

    if kind == "spec":
        return False

    model, _ = read_artifact(path, kind)
    model_id = getattr(model, "id", None)
    if model_id is None:
        return False
    return token == str(model_id).lower()


def _resolve_matches(
    identifier: str, roots: list[tuple[Kind, Path]]
) -> list[tuple[Kind, Path]]:
    return [
        (kind, path)
        for kind, path in _artifact_files(roots)
        if _matches_identifier(identifier, kind, path)
    ]


@app.callback()
def default(
    identifier: str,
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Show an artifact file by ID or slug fragment."""
    root = project_root()
    search_roots = _search_roots(root)
    matches = _resolve_matches(identifier, search_roots)
    if not matches:
        searched = ", ".join(str(folder) for _, folder in search_roots)
        typer.echo(
            f"Artifact '{identifier}' not found. Searched roots: {searched}",
            err=True,
        )
        raise typer.Exit(code=1)

    if len(matches) > 1:
        typer.echo(
            f"Multiple artifacts matched '{identifier}':",
            err=True,
        )
        for _, match in matches:
            typer.echo(f"- {match}", err=True)
        raise typer.Exit(code=1)

    kind, selected = matches[0]
    if as_json:
        model, body = read_artifact(selected, kind)
        print_json({**artifact_object(model, selected), "body": body})
        return

    # AC-1 requires rendering markdown output through Rich.
    console.print(Markdown(selected.read_text(encoding="utf-8")))
