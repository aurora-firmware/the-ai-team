"""Tests for the local work-item tracker (spec S-006)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.core.locator import find_project_root
from ai_team.core.models import parse_change_request
from ai_team.core.tracker import resolve_tracker_dir


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    return path


def _invoke(*args: str):
    from ai_team.cli import app

    return CliRunner().invoke(app, list(args))


@pytest.fixture
def initialized_repo(monkeypatch, tmp_path) -> Path:
    """A committed `ai-team init` repository with the cwd set to its root."""
    repo = _git_repo(tmp_path / "repo")
    result = _invoke("init", str(repo), "--no-interactive")
    assert result.exit_code == 0, result.output
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    monkeypatch.chdir(repo)
    return repo


def test_tracker_path_defaults_to_repository_root(initialized_repo):
    result = _invoke("tracker", "path")

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == str(initialized_repo / ".ai-team" / "tracker")


def test_tracker_path_json_lists_the_tracker_folders_without_an_archive(
    initialized_repo,
):
    result = _invoke("tracker", "path", "--json")

    assert result.exit_code == 0, result.output
    assert set(json.loads(result.stdout)) == {
        "tracker",
        "tasks",
        "bugs",
        "change_requests",
    }


def test_every_worktree_resolves_the_same_tracker(initialized_repo, monkeypatch):
    worktree = initialized_repo.parent / "linked"
    _git(initialized_repo, "worktree", "add", "-q", "-b", "task/T-001", str(worktree))
    # .ai-team.toml is committed here, so the linked worktree has the marker too.
    monkeypatch.chdir(worktree)

    result = _invoke("tracker", "path")

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == str(initialized_repo / ".ai-team" / "tracker")
    assert resolve_tracker_dir(worktree) == resolve_tracker_dir(initialized_repo)


@pytest.mark.parametrize("configured", ["work/items", "ABSOLUTE", "~/items"])
def test_tracker_dir_honours_relative_absolute_and_home_paths(
    tmp_path, monkeypatch, configured
):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    repo = tmp_path / "repo"
    (repo / "ai-team").mkdir(parents=True)
    value = str(tmp_path / "abs") if configured == "ABSOLUTE" else configured
    (repo / ".ai-team.toml").write_text(
        f'[project]\ndir = "project"\n\n[tracker]\ndir = "{value}"\n', encoding="utf-8"
    )

    root = find_project_root(repo)

    expected = {
        "work/items": repo / "work" / "items",
        "ABSOLUTE": tmp_path / "abs",
        "~/items": tmp_path / "home" / "items",
    }[configured]
    assert root.tracker == expected
    assert root.tasks == expected / "tasks"


def test_full_lifecycle_leaves_the_working_tree_clean(initialized_repo):
    created = json.loads(_invoke("task", "new", "Ship it", "--json").stdout)
    for args in (
        ("task", "start", created["id"]),
        ("task", "block", created["id"], "--reason", "waiting"),
        ("task", "unblock", created["id"]),
        ("task", "complete", created["id"]),
        ("bug", "new", "Crash", "--json"),
        ("bug", "start", "B-001"),
        ("bug", "resolve", "B-001"),
        ("change-request", "new", "Tweak scope", "--json"),
        ("change-request", "set-status", "CR-001", "approved"),
    ):
        result = _invoke(*args)
        assert result.exit_code == 0, (args, result.output)

    Path(created["path"]).write_text(
        Path(created["path"]).read_text(encoding="utf-8") + "\nReview Verdict\n",
        encoding="utf-8",
    )

    assert _git(initialized_repo, "status", "--porcelain") == ""


def test_planned_tasks_stay_out_of_the_pending_queue_until_activated(
    initialized_repo,
):
    _invoke("task", "new", "Planned work", "--status", "planned", "--spec", "S-001")
    _invoke("task", "new", "Other plan", "--status", "planned", "--spec", "CR-002")
    _invoke("task", "new", "Ready work")

    pending = json.loads(
        _invoke("list", "tasks", "--state", "pending", "--json").stdout
    )
    assert [row["id"] for row in pending] == ["T-003"]

    planned = json.loads(
        _invoke(
            "list", "tasks", "--state", "planned", "--spec", "S-001", "--json"
        ).stdout
    )
    assert [row["id"] for row in planned] == ["T-001"]
    assert set(planned[0]) == {"id", "title", "state", "priority", "assigned-role"}

    assert _invoke("task", "set-status", "T-001", "pending").exit_code == 0
    pending = json.loads(
        _invoke("list", "tasks", "--state", "pending", "--json").stdout
    )
    assert [row["id"] for row in pending] == ["T-001", "T-003"]


def test_change_request_set_status_and_show(initialized_repo):
    created = json.loads(_invoke("change-request", "new", "Tweak", "--json").stdout)

    result = _invoke("change-request", "set-status", created["id"], "rejected")
    assert result.exit_code == 0, result.output
    assert parse_change_request(Path(created["path"])).status == "rejected"

    shown = json.loads(_invoke("show", created["id"], "--json").stdout)
    assert shown["path"] == created["path"]
    assert shown["frontmatter"]["status"] == "rejected"

    rows = json.loads(
        _invoke("list", "change-requests", "--state", "rejected", "--json").stdout
    )
    assert [row["id"] for row in rows] == ["CR-001"]


def test_commands_ignore_files_in_legacy_work_item_folders(initialized_repo):
    legacy = initialized_repo / "ai-team" / "tasks" / "pending" / "T-009-old.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("legacy", encoding="utf-8")

    result = _invoke("list", "tasks", "--json")

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []
    assert "legacy" not in result.stderr.lower()
    assert "migrat" not in result.stderr.lower()


def test_project_in_a_repository_subfolder_keeps_its_tracker_beside_it(
    monkeypatch, tmp_path
):
    repo = _git_repo(tmp_path / "repo")
    project = repo / "sub"
    project.mkdir()
    result = _invoke("init", str(project), "--no-interactive")
    assert result.exit_code == 0, result.output
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    monkeypatch.chdir(project)

    assert _invoke("tracker", "path").stdout.strip() == str(
        project / ".ai-team" / "tracker"
    )
    assert _invoke("task", "new", "Nested").exit_code == 0
    assert (project / ".ai-team" / "tracker" / "tasks").is_dir()
    assert _git(repo, "status", "--porcelain") == ""


def _bare_clone_with_worktrees(tmp_path: Path, name: str) -> tuple[Path, Path, Path]:
    seed = _git_repo(tmp_path / f"seed-{name}")
    (seed / ".ai-team.toml").write_text('[project]\ndir = "project"\n', "utf-8")
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "seed")
    bare = tmp_path / "src" / f"{name}.git"
    _git(tmp_path, "clone", "-q", "--bare", str(seed), str(bare))
    first = tmp_path / "wt" / name / "main"
    second = tmp_path / "wt" / name / "feature"
    _git(bare, "worktree", "add", "-q", str(first), "main")
    _git(bare, "worktree", "add", "-q", "-b", "feature", str(second))
    return bare, first, second


def test_bare_repository_worktrees_share_one_tracker(tmp_path):
    bare, first, second = _bare_clone_with_worktrees(tmp_path, "a")

    expected = bare / ".ai-team" / "tracker"
    assert resolve_tracker_dir(first) == expected
    assert resolve_tracker_dir(second) == expected


def test_sibling_bare_repositories_keep_separate_trackers(tmp_path):
    _, first_a, _ = _bare_clone_with_worktrees(tmp_path, "a")
    _, first_b, _ = _bare_clone_with_worktrees(tmp_path, "b")

    assert resolve_tracker_dir(first_a) != resolve_tracker_dir(first_b)


def test_legacy_archive_folder_prints_no_warning(initialized_repo):
    legacy = initialized_repo / "ai-team" / "archive" / "2026-01" / "T-001-old.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("legacy", encoding="utf-8")

    result = _invoke("validate", "--json")

    assert "legacy" not in result.stderr.lower()


def test_tasks_may_cite_a_change_request_as_their_spec(initialized_repo):
    _invoke("change-request", "new", "Tweak")
    _invoke("task", "new", "From CR", "--status", "planned", "--spec", "CR-001")

    result = _invoke("validate", "--tasks", "--json")

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == []

    _invoke("task", "new", "Dangling", "--spec", "CR-009")
    codes = [f["code"] for f in json.loads(_invoke("validate", "--json").stdout)]
    assert codes == ["task-spec-missing"]


def test_list_spec_filter_matches_every_form_of_a_spec_reference(initialized_repo):
    specs = initialized_repo / "ai-team" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "S-001-login.md").write_text(
        "---\ntitle: Login\nversion: '0.1'\nstatus: approved\n"
        "created: '2026-10-16'\nauthor: planner\nid: S-001\n---\n\n# Login\n",
        encoding="utf-8",
    )
    for reference in ("S-001", "S-001-login", "login.md"):
        _invoke("task", "new", reference, "--status", "planned", "--spec", reference)

    for query in ("S-001", "S-001-login.md", "login"):
        rows = json.loads(
            _invoke(
                "list", "tasks", "--state", "planned", "--spec", query, "--json"
            ).stdout
        )
        assert [row["id"] for row in rows] == ["T-001", "T-002", "T-003"], query
