"""`ai-team task` command group for task artifact operations.

Tasks live in the local tracker; their lifecycle state is the frontmatter
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
    hint_missing_overview,
    project_root,
    template_body,
)
from ai_team.core.fs import ArtifactExists, read_artifact, update_status
from ai_team.core.ids import next_task_id
from ai_team.core.lock import LockTimeout, create_artifact_with_lock
from ai_team.core.models import Task
from ai_team.core.templates import load_template
from ai_team.core.tracker import TASK_STATUSES, find_item
from ai_team.render import print_json

NAME = "task"
app = typer.Typer(help="Create and manage task artifacts.")

Priority = Literal["critical", "high", "medium", "low"]
TaskStatus = Literal[
    "planned", "pending", "in-progress", "blocked", "completed", "cancelled"
]
NewTaskStatus = Literal["planned", "pending"]


def _find_task_or_exit(task_id: str) -> Path:
    root = project_root()
    path = find_item(root.tasks, task_id)
    if path is None:
        typer.echo(f"Task '{task_id}' not found in {root.tasks}", err=True)
        raise typer.Exit(code=1)
    return path


def _transition_task(
    task_id: str,
    *,
    command: str,
    allowed_from: tuple[str, ...] | None,
    new_status: str,
    work_log_text: str | None = None,
) -> None:
    """Set *task_id* to *new_status* in place, enforcing *allowed_from* when given."""
    path = _find_task_or_exit(task_id)
    task, _ = read_artifact(path, "task")

    if task.status == new_status:
        typer.echo(f"Task {task_id} already in {new_status}.")
        return

    if allowed_from is not None and task.status not in allowed_from:
        typer.echo(
            f"Task {task_id} is '{task.status}'; '{command}' expects one of: "
            + ", ".join(allowed_from),
            err=True,
        )
        raise typer.Exit(code=1)

    if work_log_text is not None:
        append_work_log_entry(path, "task", work_log_text)
    update_status(path, new_status, kind="task")
    typer.echo(str(path.resolve()))


@app.command("new")
def new_task(
    title: str,
    priority: Priority = typer.Option("medium", "--priority"),
    assigned_role: str = typer.Option("unassigned", "--assigned-role"),
    spec: str | None = typer.Option(
        None, "--spec", help="Source spec or change-request ID."
    ),
    plan: str | None = typer.Option(
        None,
        "--plan",
        help="Spec or change-request ID of the plan that introduces the task.",
    ),
    status: NewTaskStatus = typer.Option(
        "pending",
        "--status",
        help="'planned' keeps the task out of /dev-loop until its plan merges.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a new task in the tracker from the bundled template."""
    root = project_root()
    hint_missing_overview(root)

    def build(task_id: str) -> tuple[Path, Task, str]:
        slug = slugify(title)
        dest = root.tasks / f"{task_id}-{slug}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)

        body = template_body(load_template("task"), "Task")
        body = body.replace("# [Task Title]", f"# {title}", 1)
        model = Task(
            id=task_id,
            title=title,
            status=status,
            priority=priority,
            assigned_role=assigned_role,
            created=date.today().isoformat(),
            spec=spec,
            plan=plan,
        )
        return dest, model, body

    try:
        task_id, dest = create_artifact_with_lock(
            root.tracker,
            allocate_id=lambda: next_task_id(root),
            build=build,
        )
    except (ArtifactExists, LockTimeout) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    absolute_path = str(dest.resolve())
    if as_json:
        print_json({"id": task_id, "path": absolute_path})
        return

    typer.echo(absolute_path)


@app.command("start")
def start_task(task_id: str) -> None:
    """Set a pending task to in-progress."""
    _transition_task(
        task_id, command="start", allowed_from=("pending",), new_status="in-progress"
    )


@app.command("complete")
def complete_task(task_id: str) -> None:
    """Set an in-progress task to completed."""
    _transition_task(
        task_id,
        command="complete",
        allowed_from=("in-progress",),
        new_status="completed",
    )


@app.command("unblock")
def unblock_task(task_id: str) -> None:
    """Set a blocked task back to in-progress."""
    _transition_task(
        task_id,
        command="unblock",
        allowed_from=("blocked",),
        new_status="in-progress",
    )


@app.command("block")
def block_task(
    task_id: str,
    reason: str = typer.Option(..., "--reason"),
) -> None:
    """Set a task to blocked and record the blocking reason in its Work Log."""
    _transition_task(
        task_id,
        command="block",
        allowed_from=None,
        new_status="blocked",
        work_log_text=f"Blocked: {reason}",
    )


@app.command("set-status")
def set_task_status(
    task_id: str,
    status: TaskStatus = typer.Argument(
        ..., help="One of: " + ", ".join(TASK_STATUSES)
    ),
    reason: str | None = typer.Option(
        None, "--reason", help="Recorded as a Work Log entry."
    ),
) -> None:
    """Set a task to any allowed status."""
    _transition_task(
        task_id,
        command="set-status",
        allowed_from=None,
        new_status=status,
        work_log_text=None if reason is None else f"Status set to {status}: {reason}",
    )
