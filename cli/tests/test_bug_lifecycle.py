"""Tests for bug lifecycle commands on field-based state (S-006).

Bugs live in the local tracker; every transition rewrites the frontmatter
``status`` in place and never moves the file.
"""

from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.core.fs import read_artifact, update_status
from ai_team.core.models import parse_bug

BUG_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
severity: {severity}
status: {status}
created: 2026-05-10
---

## Summary

Bug body.
"""


def _write_bug(tmp_path: Path, bug_id: str, status: str) -> Path:
    (tmp_path / "ai-team").mkdir(exist_ok=True)
    path = tmp_path / ".ai-team" / "tracker" / "bugs" / f"{bug_id}-demo-bug.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        BUG_TEMPLATE.format(
            id=bug_id, title="Demo Bug", severity="high", status=status
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("command", "from_status", "to_status"),
    [
        ("start", "open", "in-progress"),
        ("resolve", "in-progress", "resolved"),
        ("unblock", "blocked", "in-progress"),
    ],
)
def test_bug_transition_updates_status_in_place(
    monkeypatch, tmp_path, command, from_status, to_status
):
    """Bug transitions set the status field and leave the file where it is."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-007", from_status)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", command, "B-007"])

    assert result.exit_code == 0, result.output
    assert path.exists()
    assert parse_bug(path).status == to_status


def test_bug_block_sets_blocked_and_appends_reason(monkeypatch, tmp_path):
    """`bug block --reason` sets blocked status and logs a dated reason entry."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-012", "in-progress")
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n## Work Log\n\n### Session 1 — 2026-05-09\ndiagnosis started\n")

    monkeypatch.chdir(tmp_path)
    reason = "deferred by the product owner"
    result = CliRunner().invoke(app, ["bug", "block", "B-012", "--reason", reason])

    assert result.exit_code == 0, result.output
    assert parse_bug(path).status == "blocked"
    _, body = read_artifact(path, "bug")
    assert "### Session 2" in body
    assert date.today().isoformat() in body
    assert f"Blocked: {reason}" in body


def test_bug_block_accepts_resolved_bug(monkeypatch, tmp_path):
    """`bug block` can block a bug from any status."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-013", "resolved")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["bug", "block", "B-013", "--reason", "regressed, waiting on upstream"]
    )

    assert result.exit_code == 0, result.output
    assert parse_bug(path).status == "blocked"


@pytest.mark.parametrize(
    ("command", "status", "extra_args"),
    [
        ("start", "in-progress", []),
        ("resolve", "resolved", []),
        ("block", "blocked", ["--reason", "new reason"]),
        ("unblock", "in-progress", []),
    ],
)
def test_bug_lifecycle_command_is_idempotent_when_already_in_destination_status(
    monkeypatch, tmp_path, command, status, extra_args
):
    """A bug already in the target status is left byte-for-byte unchanged."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-009", status)
    before_bytes = path.read_bytes()

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", command, "B-009", *extra_args])

    assert result.exit_code == 0
    assert f"already in {status}" in result.output
    assert path.read_bytes() == before_bytes


@pytest.mark.parametrize(
    ("command", "status"),
    [
        ("start", "resolved"),
        ("start", "blocked"),
        ("resolve", "open"),
        ("resolve", "blocked"),
        ("unblock", "open"),
    ],
)
def test_bug_lifecycle_command_rejects_unexpected_source_status(
    monkeypatch, tmp_path, command, status
):
    """A shortcut command refuses a bug that is not in its expected source status."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-010", status)
    before_bytes = path.read_bytes()

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", command, "B-010"])

    assert result.exit_code != 0
    assert f"is '{status}'" in result.stderr
    assert path.read_bytes() == before_bytes


@pytest.mark.parametrize("status", ["open", "in-progress", "blocked", "resolved"])
def test_bug_set_status_accepts_every_allowed_status(monkeypatch, tmp_path, status):
    """`bug set-status` moves a bug to any allowed status."""
    from ai_team.cli import app

    start = "open" if status != "open" else "in-progress"
    path = _write_bug(tmp_path, "B-014", start)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", "set-status", "B-014", status])

    assert result.exit_code == 0, result.output
    assert parse_bug(path).status == status


def test_bug_set_status_rejects_unknown_status(monkeypatch, tmp_path):
    """`bug set-status` refuses values outside the allowed bug statuses."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-015", "open")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", "set-status", "B-015", "deferred"])

    assert result.exit_code != 0
    assert parse_bug(path).status == "open"


def test_bug_set_status_records_reason(monkeypatch, tmp_path):
    """`bug set-status` sets any allowed status and logs an optional reason."""
    from ai_team.cli import app

    path = _write_bug(tmp_path, "B-011", "resolved")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["bug", "set-status", "B-011", "open", "--reason", "regressed again"]
    )

    assert result.exit_code == 0, result.output
    assert parse_bug(path).status == "open"
    _, body = read_artifact(path, "bug")
    assert "Status set to open: regressed again" in body


@pytest.mark.parametrize(
    ("command", "extra_args"),
    [
        ("start", []),
        ("resolve", []),
        ("block", ["--reason", "deferred"]),
        ("unblock", []),
    ],
)
def test_bug_lifecycle_command_reports_not_found_and_names_tracker_folder(
    monkeypatch, tmp_path, command, extra_args
):
    """A missing bug ID returns non-zero and names the tracker bugs folder."""
    from ai_team.cli import app

    (tmp_path / "ai-team").mkdir()

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", command, "B-999", *extra_args])

    assert result.exit_code != 0
    assert "not found" in result.stderr.lower()
    assert ".ai-team/tracker/bugs" in result.stderr


WRAPPED_TITLE_BUG = (
    "---\n"
    'id: "B-008"\n'
    "title: Frontmatter titles longer than the default YAML width must stay on one \n"
    "  line for grep and whitespace linters to read them whole\n"
    "severity: low\n"
    "status: open\n"
    "created: 2026-05-10\n"
    "---\n"
    "\n"
    "## Summary\n"
    "\n"
    "Bug body.\n"
)


def test_update_status_rewrites_wrapped_frontmatter_title_on_one_line(tmp_path):
    """A status change rewrites a previously wrapped title as one line with no trailing space."""
    path = tmp_path / "B-008-wrapped-title.md"
    path.write_text(WRAPPED_TITLE_BUG, encoding="utf-8")

    update_status(path, "in-progress")

    rewritten = path.read_text(encoding="utf-8")
    title_line = rewritten.split("\n")[2]
    assert title_line == (
        "title: Frontmatter titles longer than the default YAML width must stay on one "
        "line for grep and whitespace linters to read them whole"
    )
    assert parse_bug(path).status == "in-progress"
    assert all(line == line.rstrip() for line in rewritten.split("\n")[:8])
