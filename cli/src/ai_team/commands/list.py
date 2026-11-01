"""`ai-team list` command group for listing project artifacts."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from ai_team.commands._shared import project_root
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


def _collect_by_status(
    folder: Path,
    state: str | None,
    parser,
    row_builder,
) -> list[dict[str, str]]:
    """Parse every work item in *folder*, keeping those whose status is *state*."""
    rows: list[dict[str, str]] = []
    for path in iter_items(folder):
        model = parser(path)
        if state is not None and model.status != state:
            continue
        rows.append(row_builder(model))
    return rows


def _render_table(title: str, columns: list[str], rows: list[dict[str, str]]) -> None:
    table = Table(title=title)
    for name in columns:
        table.add_column(name)
    for row in rows:
        table.add_row(*(row[column.lower()] for column in columns))
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
    rows = [
        row
        for row in _collect_by_status(
            root.tasks,
            state,
            parse_task,
            lambda task: {
                "id": task.id,
                "title": task.title,
                "state": task.status,
                "priority": task.priority,
                "assigned-role": task.assigned_role,
                "spec": task.spec or "",
                "plan": task.plan or "",
            },
        )
        if (aliases is None or row["spec"] in aliases)
        and (plan_aliases is None or row["plan"] in plan_aliases)
    ]
    for row in rows:
        del row["spec"]
        del row["plan"]
    if as_json:
        print_json(rows)
        return
    _render_table("Tasks", ["ID", "Title", "State", "Priority", "Assigned-Role"], rows)


@app.command()
def bugs(
    state: str | None = typer.Option(None, "--state", help="Filter by bug status."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List bugs from the tracker."""
    root = project_root()
    rows = _collect_by_status(
        root.bugs,
        state,
        parse_bug,
        lambda bug: {
            "id": bug.id,
            "title": bug.title,
            "state": bug.status,
            "severity": bug.severity,
        },
    )
    if as_json:
        print_json(rows)
        return
    _render_table("Bugs", ["ID", "Title", "State", "Severity"], rows)


@app.command()
def specs(
    state: str | None = typer.Option(None, "--state", help="Filter by spec status."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List specs from the project specs folder."""
    root = project_root()
    rows: list[dict[str, str]] = []
    for path in _iter_markdown_files(root.specs):
        spec = parse_spec(path)
        if state is not None and spec.status != state:
            continue
        spec_id = spec.id or path.stem
        rows.append(
            {
                "id": spec_id,
                "title": spec.title,
                "status": spec.status,
                "version": spec.version,
            }
        )
    if as_json:
        print_json(rows)
        return
    _render_table("Specs", ["ID", "Title", "Status", "Version"], rows)


@app.command()
def adrs(
    state: str | None = typer.Option(None, "--state", help="Filter by ADR status."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List ADRs from the project decisions folder."""
    root = project_root()
    rows: list[dict[str, str]] = []
    for path in _iter_markdown_files(root.decisions):
        adr = parse_adr(path)
        if state is not None and adr.status != state:
            continue
        rows.append(
            {
                "id": adr.id,
                "title": adr.title,
                "status": adr.status,
            }
        )
    if as_json:
        print_json(rows)
        return
    _render_table("ADRs", ["ID", "Title", "Status"], rows)


@app.command("change-requests")
def change_requests(
    state: str | None = typer.Option(
        None, "--state", help="Filter by change-request status."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List change requests from the tracker."""
    root = project_root()
    rows = _collect_by_status(
        root.change_requests,
        state,
        parse_change_request,
        lambda cr: {"id": cr.id, "title": cr.title, "state": cr.status},
    )
    if as_json:
        print_json(rows)
        return
    _render_table("Change Requests", ["ID", "Title", "State"], rows)
