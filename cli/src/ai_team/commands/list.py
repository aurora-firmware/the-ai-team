"""`ai-team list` command group for listing project artifacts."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from ai_team.commands._shared import artifact_object, project_root
from ai_team.core.models import (
    parse_adr,
    parse_bug,
    parse_change_request,
    parse_spec,
    parse_task,
)
from ai_team.core.tracker import iter_items
from ai_team.core.validate import spec_reference_aliases
from ai_team.render import console, print_json

NAME = "list"
app = typer.Typer(help="List tasks, bugs, specs, ADRs, and change requests.")


def _should_skip(path: Path) -> bool:
    """Return True when *path* is a placeholder or template file."""
    return path.name == ".gitkeep" or path.match("TEMPLATE-*.md")


def _iter_markdown_files(folder: Path) -> list[Path]:
    """Return sorted markdown files in *folder*, excluding templates/placeholders."""
    return sorted(
        path
        for path in folder.glob("*.md")
        if path.is_file() and not _should_skip(path)
    )


def _collect_markdown_files(
    folder: Path,
    state: str | None,
    parser,
) -> list[dict[str, object]]:
    """Return the JSON object of every spec or ADR in *folder* whose status is *state*."""
    objects: list[dict[str, object]] = []
    for path in _iter_markdown_files(folder):
        model = parser(path)
        if state is not None and model.status != state:
            continue
        objects.append(artifact_object(model, path))
    return objects


def _collect_by_status(
    folder: Path,
    state: str | None,
    parser,
) -> list[dict[str, object]]:
    """Return the JSON object of every work item in *folder* whose status is *state*."""
    objects: list[dict[str, object]] = []
    for path in iter_items(folder):
        model = parser(path)
        if state is not None and model.status != state:
            continue
        objects.append(artifact_object(model, path))
    return objects


def _emit(
    title: str,
    columns: list[str],
    objects: list[dict[str, object]],
    as_json: bool,
) -> None:
    """Print *objects* as JSON, or as a table of the named *columns*."""
    if as_json:
        print_json(objects)
        return
    table = Table(title=title)
    for name in columns:
        table.add_column(name)
    for obj in objects:
        table.add_row(*(str(obj.get(column.lower(), "")) for column in columns))
    console.print(table)


@app.command()
def tasks(
    state: str | None = typer.Option(None, "--state", help="Filter by task status."),
    spec: str | None = typer.Option(
        None, "--spec", help="Filter by source spec or change-request ID."
    ),
    plan: str | None = typer.Option(
        None, "--plan", help="Filter by the plan (spec or change-request ID)."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List tasks from the tracker."""
    root = project_root()
    aliases = None if spec is None else spec_reference_aliases(root, spec)
    plan_aliases = None if plan is None else spec_reference_aliases(root, plan)
    objects = [
        obj
        for obj in _collect_by_status(root.tasks, state, parse_task)
        if (aliases is None or obj.get("spec") in aliases)
        and (plan_aliases is None or obj.get("plan") in plan_aliases)
    ]
    _emit(
        "Tasks",
        ["ID", "Title", "Status", "Priority", "Assigned-Role"],
        objects,
        as_json,
    )


@app.command()
def bugs(
    state: str | None = typer.Option(None, "--state", help="Filter by bug status."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List bugs from the tracker."""
    objects = _collect_by_status(project_root().bugs, state, parse_bug)
    _emit("Bugs", ["ID", "Title", "Status", "Severity"], objects, as_json)


@app.command()
def specs(
    state: str | None = typer.Option(None, "--state", help="Filter by spec status."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List specs from the project specs folder."""
    objects = _collect_markdown_files(project_root().specs, state, parse_spec)
    _emit("Specs", ["ID", "Title", "Status", "Version"], objects, as_json)


@app.command()
def adrs(
    state: str | None = typer.Option(None, "--state", help="Filter by ADR status."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List ADRs from the project decisions folder."""
    objects = _collect_markdown_files(project_root().decisions, state, parse_adr)
    _emit("ADRs", ["ID", "Title", "Status"], objects, as_json)


@app.command("change-requests")
def change_requests(
    state: str | None = typer.Option(
        None, "--state", help="Filter by change-request status."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List change requests from the tracker."""
    objects = _collect_by_status(
        project_root().change_requests, state, parse_change_request
    )
    _emit("Change Requests", ["ID", "Title", "Status"], objects, as_json)
