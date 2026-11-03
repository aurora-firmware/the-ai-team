"""`ai-team bug` command group for bug artifact operations.

Bugs live in the local tracker; their lifecycle state is the frontmatter
``status`` field (spec S-006).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import typer
from slugify import slugify

from ai_team.commands._shared import (
    append_work_log_entry,
    artifact_object_from_file,
    hint_missing_overview,
    project_root,
    template_body,
)
from ai_team.core.fs import ArtifactExists, read_artifact, update_status
from ai_team.core.ids import next_bug_id
from ai_team.core.lock import LockTimeout, create_artifact_with_lock
from ai_team.core.models import Bug
from ai_team.core.templates import load_template
from ai_team.core.tracker import BUG_STATUSES, find_item
from ai_team.render import print_json

NAME = "bug"
app = typer.Typer(help="Create and manage bug artifacts.")

Severity = Literal["critical", "high", "medium", "low"]
BugStatus = Literal["open", "in-progress", "blocked", "resolved"]


def _transition_bug(
    bug_id: str,
    *,
    command: str,
    allowed_from: tuple[str, ...] | None,
    new_status: str,
    work_log_text: str | None = None,
) -> None:
    """Set *bug_id* to *new_status* in place, enforcing *allowed_from* when given."""
    root = project_root()
    path = find_item(root.bugs, bug_id)
    if path is None:
        typer.echo(f"Bug '{bug_id}' not found in {root.bugs}", err=True)
        raise typer.Exit(code=1)

    bug, _ = read_artifact(path, "bug")
    if bug.status == new_status:
        typer.echo(f"Bug {bug_id} already in {new_status}.")
        return

    if allowed_from is not None and bug.status not in allowed_from:
        typer.echo(
            f"Bug {bug_id} is '{bug.status}'; '{command}' expects one of: "
            + ", ".join(allowed_from),
            err=True,
        )
        raise typer.Exit(code=1)

    if work_log_text is not None:
        append_work_log_entry(path, "bug", work_log_text)
    update_status(path, new_status, kind="bug")
    typer.echo(str(path.resolve()))


@app.command("new")
def new_bug(
    title: str,
    severity: Severity = typer.Option("medium", "--severity"),
    task: str | None = typer.Option(None, "--task"),
    source_branch: str | None = typer.Option(
        None,
        "--source-branch",
        help="Branch that introduced a task regression; omit for existing defects.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a new open bug in the tracker from the bundled template."""
    root = project_root()
    hint_missing_overview(root)

    def build(bug_id: str) -> tuple[Path, Bug, str]:
        slug = slugify(title)
        dest = root.bugs / f"{bug_id}-{slug}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)

        body = template_body(load_template("bug"), "Bug")
        body = body.replace("# [Bug Title]", f"# {title}", 1)
        model = Bug(
            id=bug_id,
            title=title,
            severity=severity,
            status="open",
            created=date.today().isoformat(),
            task=task,
            source_branch=source_branch,
        )
        return dest, model, body

    try:
        bug_id, dest = create_artifact_with_lock(
            root.tracker,
            allocate_id=lambda: next_bug_id(root),
            build=build,
        )
    except (ArtifactExists, LockTimeout) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    absolute_path = str(dest.resolve())
    if as_json:
        print_json(artifact_object_from_file(dest, "bug"))
        return

    typer.echo(absolute_path)


@app.command("start")
def start_bug(bug_id: str) -> None:
    """Set an open bug to in-progress."""
    _transition_bug(
        bug_id, command="start", allowed_from=("open",), new_status="in-progress"
    )


@app.command("resolve")
def resolve_bug(bug_id: str) -> None:
    """Set an in-progress bug to resolved."""
    _transition_bug(
        bug_id, command="resolve", allowed_from=("in-progress",), new_status="resolved"
    )


@app.command("unblock")
def unblock_bug(bug_id: str) -> None:
    """Set a blocked bug back to in-progress."""
    _transition_bug(
        bug_id, command="unblock", allowed_from=("blocked",), new_status="in-progress"
    )


@app.command("block")
def block_bug(
    bug_id: str,
    reason: str = typer.Option(..., "--reason"),
) -> None:
    """Set a bug to blocked and record the blocking reason in its Work Log."""
    _transition_bug(
        bug_id,
        command="block",
        allowed_from=None,
        new_status="blocked",
        work_log_text=f"Blocked: {reason}",
    )


@app.command("set-status")
def set_bug_status(
    bug_id: str,
    status: BugStatus = typer.Argument(..., help="One of: " + ", ".join(BUG_STATUSES)),
    reason: str | None = typer.Option(
        None, "--reason", help="Recorded as a Work Log entry."
    ),
) -> None:
    """Set a bug to any allowed status."""
    _transition_bug(
        bug_id,
        command="set-status",
        allowed_from=None,
        new_status=status,
        work_log_text=None if reason is None else f"Status set to {status}: {reason}",
    )
