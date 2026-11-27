"""Tests for task lifecycle commands on field-based state (T-014, S-006).

Tasks live in the local tracker; every transition rewrites the frontmatter
``status`` in place and never moves the file.
"""

from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.core.fs import read_artifact
from ai_team.core.models import parse_task

TASK_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: {status}
priority: medium
assigned-role: developer
created: 2026-05-10
---

## Description

Task body.

## Work Log
"""


def _tasks_dir(tmp_path: Path) -> Path:
    (tmp_path / "ai-team").mkdir(exist_ok=True)
    return tmp_path / ".ai-team" / "tracker" / "tasks"


def _write_task(tmp_path: Path, task_id: str, status: str) -> Path:
    path = _tasks_dir(tmp_path) / f"{task_id}-demo-task.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        TASK_TEMPLATE.format(id=task_id, title="Demo Task", status=status),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("command", "from_status", "to_status"),
    [
        ("start", "pending", "in-progress"),
        ("complete", "in-progress", "completed"),
        ("unblock", "blocked", "in-progress"),
    ],
)
def test_transition_updates_status_in_place(
    monkeypatch, tmp_path, command, from_status, to_status
):
    """Transitions set the status field and leave the file where it is."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-042", from_status)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", command, "T-042"])

    assert result.exit_code == 0, result.output
    assert path.exists()
    assert parse_task(path).status == to_status
    assert str(path.resolve()) in result.output


def test_task_block_sets_blocked_and_appends_reason(monkeypatch, tmp_path):
    """`task block --reason` sets blocked status and logs a dated reason entry."""
    from ai_team.cli import app

    path = _tasks_dir(tmp_path) / "T-045-demo-task.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        TASK_TEMPLATE.format(id="T-045", title="Demo Task", status="pending")
        + "\n### Session 1 — 2026-05-09\ninitial setup complete\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    reason = "waiting on architect decision"
    result = CliRunner().invoke(app, ["task", "block", "T-045", "--reason", reason])

    assert result.exit_code == 0, result.output
    assert parse_task(path).status == "blocked"
    _, body = read_artifact(path, "task")
    assert "### Session 2" in body
    assert date.today().isoformat() in body
    assert f"Blocked: {reason}" in body


def test_task_block_accepts_completed_task(monkeypatch, tmp_path):
    """`task block` can block a task from any status."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-046", "completed")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["task", "block", "T-046", "--reason", "needs rework"]
    )

    assert result.exit_code == 0, result.output
    assert parse_task(path).status == "blocked"


@pytest.mark.parametrize(
    ("command", "status", "extra_args"),
    [
        ("start", "in-progress", []),
        ("complete", "completed", []),
        ("block", "blocked", ["--reason", "new reason"]),
        ("unblock", "in-progress", []),
    ],
)
def test_lifecycle_command_is_idempotent_when_already_in_destination_status(
    monkeypatch, tmp_path, command, status, extra_args
):
    """Lifecycle commands are byte-for-byte no-ops when already in the target status."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-050", status)
    before_bytes = path.read_bytes()

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", command, "T-050", *extra_args])

    assert result.exit_code == 0
    assert f"already in {status}" in result.output
    assert path.read_bytes() == before_bytes


@pytest.mark.parametrize(
    ("command", "status"),
    [
        ("start", "completed"),
        ("start", "planned"),
        ("complete", "pending"),
    ],
)
def test_lifecycle_command_rejects_unexpected_source_status(
    monkeypatch, tmp_path, command, status
):
    """A shortcut command refuses a task that is not in its expected source status."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-060", status)
    before_bytes = path.read_bytes()

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", command, "T-060"])

    assert result.exit_code != 0
    assert f"is '{status}'" in result.stderr
    assert path.read_bytes() == before_bytes


@pytest.mark.parametrize(
    "status", ["planned", "pending", "in-progress", "blocked", "completed", "cancelled"]
)
def test_set_status_accepts_every_allowed_status(monkeypatch, tmp_path, status):
    """`task set-status` moves a task to any allowed status."""
    from ai_team.cli import app

    start = "pending" if status != "pending" else "planned"
    path = _write_task(tmp_path, "T-070", start)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "set-status", "T-070", status])

    assert result.exit_code == 0, result.output
    assert parse_task(path).status == status


def test_set_status_rejects_unknown_status(monkeypatch, tmp_path):
    """`task set-status` refuses values outside the allowed task statuses."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-071", "pending")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "set-status", "T-071", "done"])

    assert result.exit_code != 0
    assert parse_task(path).status == "pending"


def test_set_status_records_reason_in_work_log(monkeypatch, tmp_path):
    """`task set-status --reason` records the reason as a Work Log entry."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-072", "planned")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        ["task", "set-status", "T-072", "cancelled", "--reason", "CR-004 rejected"],
    )

    assert result.exit_code == 0, result.output
    _, body = read_artifact(path, "task")
    assert "Status set to cancelled: CR-004 rejected" in body


def test_lifecycle_command_reports_not_found_and_names_tracker_folder(
    monkeypatch, tmp_path
):
    """A missing task ID returns non-zero and names the tracker tasks folder."""
    from ai_team.cli import app

    _tasks_dir(tmp_path).mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "start", "T-999"])

    assert result.exit_code != 0
    assert "not found" in result.stderr.lower()
    assert ".ai-team/tracker/tasks" in result.stderr


@pytest.mark.parametrize("before", ["pending", "in-progress", "planned"])
def test_unblock_restores_the_status_held_before_block(monkeypatch, tmp_path, before):
    """`task block` records the previous status and `task unblock` restores it."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-080", before)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["task", "block", "T-080", "--reason", "wait"])
    assert result.exit_code == 0, result.output
    assert parse_task(path).blocked_from == before

    result = CliRunner().invoke(app, ["task", "unblock", "T-080"])
    assert result.exit_code == 0, result.output
    task = parse_task(path)
    assert task.status == before
    assert task.blocked_from is None
    assert "blocked_from" not in path.read_text(encoding="utf-8")


def test_set_status_blocked_is_restored_by_unblock(monkeypatch, tmp_path):
    """`task set-status blocked` records the previous status like `block` does."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-081", "pending")
    monkeypatch.chdir(tmp_path)

    assert (
        CliRunner().invoke(app, ["task", "set-status", "T-081", "blocked"]).exit_code
        == 0
    )
    assert CliRunner().invoke(app, ["task", "unblock", "T-081"]).exit_code == 0
    assert parse_task(path).status == "pending"


def test_unblock_without_a_recorded_status_falls_back_to_in_progress(
    monkeypatch, tmp_path
):
    """A task blocked by hand, with no recorded status, unblocks to in-progress."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-082", "blocked")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["task", "unblock", "T-082"])

    assert result.exit_code == 0, result.output
    assert parse_task(path).status == "in-progress"


def test_unblock_leaves_a_task_that_is_not_blocked_unchanged(monkeypatch, tmp_path):
    """`task unblock` on a task that is not blocked changes nothing."""
    from ai_team.cli import app

    path = _write_task(tmp_path, "T-083", "pending")
    before_bytes = path.read_bytes()
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["task", "unblock", "T-083"])

    assert result.exit_code == 0
    assert "not blocked" in result.output
    assert path.read_bytes() == before_bytes
