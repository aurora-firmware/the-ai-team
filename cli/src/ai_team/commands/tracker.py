"""`ai-team tracker` command group for the local work-item tracker."""

from __future__ import annotations

import typer

from ai_team.commands._shared import project_root
from ai_team.render import print_json

NAME = "tracker"
app = typer.Typer(help="Inspect the local work-item tracker.")


@app.command("path")
def tracker_path(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Print the absolute tracker folder shared by every worktree of this repository."""
    root = project_root()
    if as_json:
        print_json(
            {
                "tracker": str(root.tracker),
                "tasks": str(root.tasks),
                "bugs": str(root.bugs),
                "change_requests": str(root.change_requests),
            }
        )
        return
    typer.echo(str(root.tracker))
