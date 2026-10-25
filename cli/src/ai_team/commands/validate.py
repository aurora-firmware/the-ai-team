"""`ai-team validate` command."""

from __future__ import annotations

import typer
from rich.table import Table

from ai_team.commands._shared import hint_missing_overview, project_root
from ai_team.core.validate import validate_project
from ai_team.render import console, print_json

NAME = "validate"
app = typer.Typer(
    help="Validate artifact metadata, cross-references, and versioned feature-spec structure.",
    invoke_without_command=True,
)


def _selected_scopes(
    all_scopes: bool,
    tasks: bool,
    bugs: bool,
    specs: bool,
    adrs: bool,
    change_requests: bool,
) -> tuple[bool, bool, bool, bool, bool]:
    if all_scopes or not any((tasks, bugs, specs, adrs, change_requests)):
        return (True, True, True, True, True)
    return (tasks, bugs, specs, adrs, change_requests)


def _render_findings_table(findings: list[dict[str, str]]) -> None:
    table = Table(title="Validation Findings")
    table.add_column("Path")
    table.add_column("Level")
    table.add_column("Code")
    table.add_column("Message")
    for finding in findings:
        table.add_row(
            finding["path"],
            finding["level"],
            finding["code"],
            finding["message"],
        )
    console.print(table)


@app.callback()
def default(
    all_scopes: bool = typer.Option(
        False, "--all", help="Validate all artifact types."
    ),
    tasks: bool = typer.Option(False, "--tasks", help="Validate tasks only."),
    bugs: bool = typer.Option(False, "--bugs", help="Validate bugs only."),
    specs: bool = typer.Option(False, "--specs", help="Validate specs only."),
    adrs: bool = typer.Option(False, "--adrs", help="Validate ADRs only."),
    change_requests: bool = typer.Option(
        False, "--change-requests", help="Validate change requests only."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    root = project_root()
    hint_missing_overview(root)
    (
        selected_tasks,
        selected_bugs,
        selected_specs,
        selected_adrs,
        selected_change_requests,
    ) = _selected_scopes(all_scopes, tasks, bugs, specs, adrs, change_requests)
    findings = validate_project(
        root,
        tasks=selected_tasks,
        bugs=selected_bugs,
        specs=selected_specs,
        adrs=selected_adrs,
        change_requests=selected_change_requests,
    )
    payload = [finding.as_dict() for finding in findings]

    if as_json:
        print_json(payload)
    else:
        _render_findings_table(payload)
        typer.echo(f"{len(payload)} findings")

    has_error = any(finding["level"] == "error" for finding in payload)
    if has_error:
        raise typer.Exit(code=1)
