"""Tests for T-010: ai-team task new command."""

import json
import threading
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.core.models import parse_task


@pytest.fixture(autouse=True)
def _project_dir(tmp_path):
    """The locator needs the project directory; work items live in the tracker."""
    (tmp_path / "ai-team").mkdir(exist_ok=True)


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def test_task_new_creates_pending_task_with_defaults_and_prints_absolute_path(
    monkeypatch, tmp_path
):
    """`ai-team task new` creates one pending task file and echoes its absolute path."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "tasks")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "new", "Ship API"])

    expected = tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-ship-api.md"

    assert result.exit_code == 0
    assert result.stdout.strip() == str(expected)

    files = list((tmp_path / ".ai-team" / "tracker" / "tasks").glob("*.md"))
    assert files == [expected]

    task = parse_task(expected)
    assert task.id == "T-001"
    assert task.title == "Ship API"
    assert task.status == "pending"
    assert task.priority == "medium"
    assert task.assigned_role == "unassigned"
    assert task.created == date.today().isoformat()
    assert task.spec is None


def test_task_new_supports_custom_flags_and_json_output(monkeypatch, tmp_path):
    """`task new --json` emits id/path and writes frontmatter from supplied flags."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "tasks")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "task",
            "new",
            "Build Auth Gateway",
            "--priority",
            "critical",
            "--assigned-role",
            "developer",
            "--spec",
            "S-101",
            "--json",
        ],
    )

    expected = (
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-build-auth-gateway.md"
    )
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["id"] == "T-001"
    assert payload["path"] == str(expected)
    assert "┏" not in result.stdout

    task = parse_task(expected)
    assert task.id == "T-001"
    assert task.title == "Build Auth Gateway"
    assert task.status == "pending"
    assert task.priority == "critical"
    assert task.assigned_role == "developer"
    assert task.created == date.today().isoformat()
    assert task.spec == "S-101"


def test_task_new_refuses_to_overwrite_when_allocated_path_exists(
    monkeypatch, tmp_path
):
    """Existing output path causes non-zero exit and preserves file bytes."""
    from ai_team.cli import app

    pending = tmp_path / ".ai-team" / "tracker" / "tasks"
    _mkdir(pending)

    existing = pending / "T-001-ship-api.md"
    existing.write_text("existing bytes\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("ai_team.commands.task.next_task_id", lambda _root: "T-001")
    result = CliRunner().invoke(app, ["task", "new", "Ship API"])

    assert result.exit_code != 0
    assert "already exists" in result.stderr.lower()
    assert existing.read_text(encoding="utf-8") == "existing bytes\n"


def test_task_new_substitutes_body_h1_with_provided_title(monkeypatch, tmp_path):
    """`task new` replaces the body H1 placeholder with the provided title."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "tasks")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "new", "My New Task"])

    assert result.exit_code == 0

    expected = tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-my-new-task.md"
    content = expected.read_text(encoding="utf-8")

    assert "# My New Task" in content
    assert "# [Task Title]" not in content


def test_task_new_body_holds_no_task_quality_rules_comment(monkeypatch, tmp_path):
    """B-047: the created task carries no template-only authoring guidance block."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "tasks")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "new", "Demo task"])

    assert result.exit_code == 0

    created = tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-demo-task.md"
    assert "Task Quality Rules" not in created.read_text(encoding="utf-8")


def test_task_new_allocates_distinct_ids_for_two_concurrent_callers(
    monkeypatch, tmp_path
):
    """B-014: two racing `new_task` calls must never write the same T-NNN id.

    ``CliRunner.invoke`` is not thread-safe (it patches global ``sys.stdout``
    per call), so this drives ``new_task`` directly. It reproduces the
    diagnosed race deterministically by delaying the *first* caller's
    ``slugify`` call (the step between "id computed" and "file written") with
    a ``threading.Event`` -- never ``time.sleep`` -- so the second caller's
    directory scan is forced to attempt to run while the first is still
    mid-critical-section.
    """
    import ai_team.commands.task as task_cmd

    pending = tmp_path / ".ai-team" / "tracker" / "tasks"
    _mkdir(pending)
    for state in ("in-progress", "completed", "blocked"):
        _mkdir(tmp_path / "ai-team" / "tasks" / state)

    monkeypatch.chdir(tmp_path)

    real_slugify = task_cmd.slugify
    call_count = {"value": 0}
    count_lock = threading.Lock()
    first_call_started = threading.Event()
    release_first_call = threading.Event()

    def patched_slugify(title: str) -> str:
        with count_lock:
            call_count["value"] += 1
            this_call = call_count["value"]
        result = real_slugify(title)
        if this_call == 1:
            first_call_started.set()
            assert release_first_call.wait(timeout=5), "never released"
        return result

    monkeypatch.setattr(task_cmd, "slugify", patched_slugify)

    errors: list[BaseException] = []

    def worker(title: str) -> None:
        try:
            task_cmd.new_task(
                title=title,
                priority="medium",
                assigned_role="unassigned",
                spec=None,
                plan=None,
                status="pending",
                as_json=False,
            )
        except BaseException as exc:  # noqa: BLE001 - surfaced via `errors`
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=("Parallel Alpha",))
    t1.start()
    assert first_call_started.wait(timeout=5)

    t2 = threading.Thread(target=worker, args=("Parallel Beta",))
    t2.start()
    t2.join(timeout=1)
    assert t2.is_alive(), "second caller should still be blocked by the lock"

    release_first_call.set()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive()
    assert not t2.is_alive()

    assert errors == []

    files = sorted(pending.glob("T-*.md"))
    assert len(files) == 2
    ids = {parse_task(path).id for path in files}
    assert len(ids) == 2, f"expected two distinct task ids, got files: {files}"


def test_task_new_creates_task_with_overview_spec_and_json_output(
    monkeypatch, tmp_path
):
    import json

    from ai_team.cli import app

    tasks_dir = tmp_path / ".ai-team" / "tracker" / "tasks"
    _mkdir(tasks_dir)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["task", "new", "Bootstrap tooling", "--spec", "S-000", "--json"]
    )

    assert result.exit_code == 0
    created = json.loads(result.stdout)
    assert created["id"] == "T-001"
    assert parse_task(tasks_dir / "T-001-bootstrap-tooling.md").spec == "S-000"


def test_task_new_accepts_feature_spec_reference(monkeypatch, tmp_path):
    from ai_team.cli import app

    tasks_dir = tmp_path / ".ai-team" / "tracker" / "tasks"
    _mkdir(tasks_dir)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["task", "new", "Feature", "--spec", "S-007"])

    assert result.exit_code == 0
    assert parse_task(tasks_dir / "T-001-feature.md").spec == "S-007"
