"""`ai-team change-request` command group for change-request artifact operations.

Change-requests live in the local tracker; their state is the frontmatter
``status`` field (spec S-006).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import typer
from slugify import slugify

from ai_team.commands._shared import (
    artifact_object_from_file,
    hint_missing_overview,
    project_root,
    template_body,
)
from ai_team.core.fs import ArtifactExists, read_artifact, update_status
from ai_team.core.ids import next_change_request_id
from ai_team.core.lock import LockTimeout, create_artifact_with_lock
from ai_team.core.models import ChangeRequest
from ai_team.core.templates import load_template
from ai_team.core.tracker import CHANGE_REQUEST_STATUSES, find_item
from ai_team.render import print_json

NAME = "change-request"
app = typer.Typer(help="Create and manage change-request artifacts.")

ChangeRequestStatus = Literal["pending", "approved", "rejected"]


@app.command("new")
def new_change_request(
    title: str,
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a new change-request in the tracker from the bundled template."""
    root = project_root()
    hint_missing_overview(root)

    def build(cr_id: str) -> tuple[Path, ChangeRequest, str]:
        slug = slugify(title)
        dest = root.change_requests / f"{cr_id}-{slug}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)

        body = template_body(load_template("change-request"), "Change-request")
        body = body.replace("# [Change Request Title]", f"# {title}", 1)
        model = ChangeRequest(
            id=cr_id,
            title=title,
            status="pending",
            created=date.today().isoformat(),
        )
        return dest, model, body

    try:
        cr_id, dest = create_artifact_with_lock(
            root.tracker,
            allocate_id=lambda: next_change_request_id((root.change_requests,)),
            build=build,
        )
    except (ArtifactExists, LockTimeout) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    absolute_path = str(dest.resolve())
    if as_json:
        print_json(artifact_object_from_file(dest, "change-request"))
        return

    typer.echo(absolute_path)


@app.command("set-status")
def set_change_request_status(
    cr_id: str,
    status: ChangeRequestStatus = typer.Argument(
        ..., help="One of: " + ", ".join(CHANGE_REQUEST_STATUSES)
    ),
) -> None:
    """Set a change-request to pending, approved, or rejected."""
    root = project_root()
    path = find_item(root.change_requests, cr_id)
    if path is None:
        typer.echo(
            f"Change request '{cr_id}' not found in {root.change_requests}", err=True
        )
        raise typer.Exit(code=1)

    cr, _ = read_artifact(path, "change-request")
    if cr.status == status:
        typer.echo(f"Change request {cr_id} already {status}.")
        return
    update_status(path, status, kind="change-request")
    typer.echo(str(path.resolve()))
