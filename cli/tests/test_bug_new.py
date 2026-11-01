"""Tests for T-011: ai-team bug new command."""

import json
import threading
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.core.models import parse_bug


@pytest.fixture(autouse=True)
def _project_dir(tmp_path):
    """The locator needs the project directory; work items live in the tracker."""
    (tmp_path / "ai-team").mkdir(exist_ok=True)


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def test_bug_new_creates_open_bug_with_defaults_and_prints_absolute_path(
    monkeypatch, tmp_path
):
    """`ai-team bug new` creates one open bug file and echoes its absolute path."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "bugs")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", "new", "Crash on launch"])

    expected = tmp_path / ".ai-team" / "tracker" / "bugs" / "B-001-crash-on-launch.md"

    assert result.exit_code == 0
    assert result.stdout.strip() == str(expected)

    files = list((tmp_path / ".ai-team" / "tracker" / "bugs").glob("*.md"))
    assert files == [expected]

    bug = parse_bug(expected)
    assert bug.id == "B-001"
    assert bug.title == "Crash on launch"
    assert bug.severity == "medium"
    assert bug.status == "open"
    assert bug.created == date.today().isoformat()
    assert bug.task is None


def test_bug_new_supports_custom_flags_and_json_output(monkeypatch, tmp_path):
    """`bug new --json` emits id/path and writes frontmatter from supplied flags."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "bugs")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "bug",
            "new",
            "Fix auth race",
            "--severity",
            "critical",
            "--task",
            "T-011",
            "--json",
        ],
    )

    expected = tmp_path / ".ai-team" / "tracker" / "bugs" / "B-001-fix-auth-race.md"
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["id"] == "B-001"
    assert payload["severity"] == "critical"
    assert payload["task"] == "T-011"
    assert payload["path"] == str(expected)
    assert "┏" not in result.stdout

    bug = parse_bug(expected)
    assert bug.id == "B-001"
    assert bug.title == "Fix auth race"
    assert bug.severity == "critical"
    assert bug.status == "open"
    assert bug.created == date.today().isoformat()
    assert bug.task == "T-011"


def test_bug_new_refuses_to_overwrite_when_allocated_path_exists(monkeypatch, tmp_path):
    """Existing output path causes non-zero exit and preserves file bytes."""
    from ai_team.cli import app

    open_folder = tmp_path / ".ai-team" / "tracker" / "bugs"
    _mkdir(open_folder)

    existing = open_folder / "B-001-crash-on-launch.md"
    existing.write_text("existing bytes\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("ai_team.commands.bug.next_bug_id", lambda _root: "B-001")
    result = CliRunner().invoke(app, ["bug", "new", "Crash on launch"])

    assert result.exit_code != 0
    assert "already exists" in result.stderr.lower()
    assert existing.read_text(encoding="utf-8") == "existing bytes\n"


def test_bug_new_substitutes_body_h1_with_provided_title(monkeypatch, tmp_path):
    """`bug new` replaces the `# [Bug Title]` body placeholder with the given title."""
    from ai_team.cli import app

    _mkdir(tmp_path / ".ai-team" / "tracker" / "bugs")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", "new", "Crash on startup"])

    assert result.exit_code == 0

    expected = tmp_path / ".ai-team" / "tracker" / "bugs" / "B-001-crash-on-startup.md"
    content = expected.read_text(encoding="utf-8")

    assert "# Crash on startup" in content
    assert "# [Bug Title]" not in content


def test_bug_new_allocates_distinct_ids_for_two_concurrent_callers(
    monkeypatch, tmp_path
):
    """B-014: two racing `new_bug` calls must never write the same B-NNN id.

    ``CliRunner.invoke`` is not thread-safe (it patches global ``sys.stdout``
    per call), so this drives ``new_bug`` directly. It reproduces the
    diagnosed race deterministically by delaying the *first* caller's
    ``slugify`` call (the step between "id computed" and "file written") with
    a ``threading.Event`` -- never ``time.sleep`` -- so the second caller's
    directory scan is forced to attempt to run while the first is still
    mid-critical-section.
    """
    import ai_team.commands.bug as bug_cmd

    open_folder = tmp_path / ".ai-team" / "tracker" / "bugs"
    _mkdir(open_folder)
    for state in ("in-progress", "resolved"):
        _mkdir(tmp_path / "ai-team" / "bugs" / state)

    monkeypatch.chdir(tmp_path)

    real_slugify = bug_cmd.slugify
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

    monkeypatch.setattr(bug_cmd, "slugify", patched_slugify)

    errors: list[BaseException] = []

    def worker(title: str) -> None:
        try:
            bug_cmd.new_bug(
                title=title,
                severity="medium",
                task=None,
                source_branch=None,
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

    files = sorted(open_folder.glob("B-*.md"))
    assert len(files) == 2
    ids = {parse_bug(path).id for path in files}
    assert len(ids) == 2, f"expected two distinct bug ids, got files: {files}"


def test_bug_new_writes_source_branch_when_given(monkeypatch, tmp_path):
    """`bug new --source-branch` records the regression branch in frontmatter."""
    from ai_team.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["bug", "new", "Regression", "--source-branch", "task/T-021-login"]
    )

    assert result.exit_code == 0
    text = Path(result.stdout.strip()).read_text(encoding="utf-8")
    assert "source_branch: task/T-021-login" in text


def test_bug_new_omits_source_branch_by_default(monkeypatch, tmp_path):
    """Without `--source-branch` the bug is an existing defect with no branch key."""
    from ai_team.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["bug", "new", "Existing defect"])

    assert result.exit_code == 0
    text = Path(result.stdout.strip()).read_text(encoding="utf-8")
    assert "source_branch" not in text
