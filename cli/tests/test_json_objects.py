"""One flat JSON object per artifact from `new`, `list` and `show` (S-006 REQ-017)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _invoke_json(*args: str) -> object:
    from ai_team.cli import app

    result = CliRunner().invoke(app, [*args, "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)


@pytest.fixture
def repo(monkeypatch, tmp_path) -> Path:
    from ai_team.cli import app

    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    result = CliRunner().invoke(app, ["init", str(path), "--no-interactive"])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(path)
    return path


def _row(rows: object, artifact_id: str) -> dict:
    matching = [row for row in rows if row["id"] == artifact_id]
    assert len(matching) == 1, rows
    return matching[0]


def _without_body(shown: dict) -> dict:
    return {key: value for key, value in shown.items() if key != "body"}


def _assert_same_object(created: dict, listed: dict, shown: dict) -> None:
    assert created == listed == _without_body(shown)
    assert Path(created["path"]).is_absolute()
    assert "state" not in created
    assert "frontmatter" not in created
    assert "frontmatter" not in shown


def test_task_json_object_is_the_same_from_new_list_and_show(repo):
    created = _invoke_json("task", "new", "Demo", "--spec", "S-001", "--plan", "S-001")
    listed = _row(_invoke_json("list", "tasks"), created["id"])
    shown = _invoke_json("show", created["id"])

    _assert_same_object(created, listed, shown)
    assert created["status"] == "pending"
    assert created["spec"] == "S-001"
    assert created["plan"] == "S-001"
    assert {"title", "priority", "assigned-role"} <= set(created)


def test_bug_json_object_is_the_same_from_new_list_and_show(repo):
    created = _invoke_json("bug", "new", "Broken", "--severity", "low")
    listed = _row(_invoke_json("list", "bugs"), created["id"])
    shown = _invoke_json("show", created["id"])

    _assert_same_object(created, listed, shown)
    assert created["status"] == "open"
    assert created["severity"] == "low"


def test_change_request_json_object_is_the_same_from_new_list_and_show(repo):
    created = _invoke_json("change-request", "new", "Tweak")
    listed = _row(_invoke_json("list", "change-requests"), created["id"])
    shown = _invoke_json("show", created["id"])

    _assert_same_object(created, listed, shown)
    assert created["status"] == "pending"


def test_spec_json_object_is_the_same_from_new_list_and_show(repo):
    created = _invoke_json("spec", "new", "Widgets")
    listed = _row(_invoke_json("list", "specs"), created["id"])
    shown = _invoke_json("show", created["id"])

    _assert_same_object(created, listed, shown)
    assert created["status"] == "draft"
    assert created["version"] == "0.1"


def test_adr_json_object_is_the_same_from_new_list_and_show(repo):
    created = _invoke_json("adr", "new", "Choose storage")
    listed = _row(_invoke_json("list", "adrs"), created["id"])
    shown = _invoke_json("show", created["id"])

    _assert_same_object(created, listed, shown)
    assert created["status"] == "proposed"
