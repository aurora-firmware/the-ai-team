"""Root Typer application and console-script entry point for ai-team."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import Annotated, Optional

import typer
from typer.core import TyperGroup

from ai_team.commands import discover_and_mount
from ai_team.core.layout import resolve_layout
from ai_team.core.locator import ProjectRootNotFound, find_project_root

DEVELOPMENT_WARNING = (
    "Warning: ai-team is under development. Please report issues at "
    "https://github.com/aurora-firmware/the-ai-team/issues"
)
VERSION_MISMATCH_WARNING = (
    "Warning: .ai-team.toml framework_version {configured} does not match "
    "ai-team {running}. Install ai-team {configured}, or run "
    "`ai-team init --update-skills` to update the project to {running}."
)


class DevelopmentWarningGroup(TyperGroup):
    """Root command group that warns once before processing an invocation."""

    def main(self, *args, **kwargs):
        typer.echo(DEVELOPMENT_WARNING, err=True)
        return super().main(*args, **kwargs)

    def invoke(self, ctx):
        """Report a missing project as a plain error instead of a traceback."""
        try:
            return super().invoke(ctx)
        except ProjectRootNotFound as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1) from exc


app = typer.Typer(
    name="ai-team",
    help="Manage AI-team artifacts: specs, tasks, bugs, and ADRs.",
    add_completion=False,
    cls=DevelopmentWarningGroup,
)

# Register all command modules discovered under ai_team.commands.
discover_and_mount(app)


def _version_callback(value: bool) -> None:
    if value:
        version = importlib.metadata.version("ai-team")
        typer.echo(version)
        raise typer.Exit()


def _warn_on_version_mismatch() -> None:
    """Warn when the project marker records a different framework version.

    The warning is advisory, so a failed project or marker lookup is ignored
    and the command proceeds.
    """
    try:
        root = find_project_root(Path.cwd())
        running_version = importlib.metadata.version("ai-team")
        contract, _ = resolve_layout(root.repo, current_version=running_version)
    except Exception:  # advisory only: any lookup failure must not affect the command
        return
    if (
        contract.version_status == "valid"
        and contract.configured_version != contract.current_version
    ):
        typer.echo(
            VERSION_MISMATCH_WARNING.format(
                configured=contract.configured_version,
                running=contract.current_version,
            ),
            err=True,
        )


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            help="Print the ai-team version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """ai-team — AI-team artifact management CLI."""
    if ctx.invoked_subcommand != "init":
        _warn_on_version_mismatch()
