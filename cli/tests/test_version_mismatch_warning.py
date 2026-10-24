"""Tests for the version mismatch warning emitted by every ai-team command."""

import json

import pytest
from typer.testing import CliRunner

RUNNING_VERSION = "2.0.0"
CONFIGURED_VERSION = "1.0.0"
MISMATCH_WARNING = (
    f"Warning: .ai-team.toml framework_version {CONFIGURED_VERSION} does not match "
    f"ai-team {RUNNING_VERSION}. Install ai-team {CONFIGURED_VERSION}, or run "
    f"`ai-team init --update-skills` to update the project to {RUNNING_VERSION}."
)
DEVELOPMENT_WARNING = (
    "Warning: ai-team is under development. Please report issues at "
    "https://github.com/aurora-firmware/the-ai-team/issues"
)


@pytest.fixture
def running_version(monkeypatch):
    """Pin the running CLI version so tests never depend on the installed one."""
    import importlib.metadata

    real_version = importlib.metadata.version

    def fake_version(name):
        return RUNNING_VERSION if name == "ai-team" else real_version(name)

    monkeypatch.setattr(importlib.metadata, "version", fake_version)


def make_project(tmp_path, marker_text):
    (tmp_path / "ai-team").mkdir()
    if marker_text is not None:
        (tmp_path / ".ai-team.toml").write_text(marker_text)


def marker_with_version(version):
    return f'[init]\ntools = ["claude"]\nframework_version = "{version}"\n'


def run(monkeypatch, tmp_path, args):
    from ai_team.cli import app

    monkeypatch.chdir(tmp_path)
    return CliRunner().invoke(app, args)


def test_warns_once_after_development_warning_when_version_differs(
    monkeypatch, tmp_path, running_version
):
    make_project(tmp_path, marker_with_version(CONFIGURED_VERSION))

    result = run(monkeypatch, tmp_path, ["list", "tasks"])

    assert result.exit_code == 0
    assert result.stderr.count(MISMATCH_WARNING) == 1
    assert result.stderr.index(DEVELOPMENT_WARNING) < result.stderr.index(
        MISMATCH_WARNING
    )


def test_no_warning_when_marker_version_equals_running_version(
    monkeypatch, tmp_path, running_version
):
    make_project(tmp_path, marker_with_version(RUNNING_VERSION))

    result = run(monkeypatch, tmp_path, ["list", "tasks"])

    assert "does not match" not in result.stderr


def test_no_warning_when_no_marker_exists(monkeypatch, tmp_path, running_version):
    make_project(tmp_path, None)

    result = run(monkeypatch, tmp_path, ["list", "tasks"])

    assert result.exit_code == 0
    assert "does not match" not in result.stderr


def test_no_warning_when_no_project_is_found(monkeypatch, tmp_path, running_version):
    import ai_team.cli

    monkeypatch.delenv("AI_TEAM_ROOT", raising=False)
    resolved_layouts = []
    monkeypatch.setattr(
        ai_team.cli,
        "resolve_layout",
        lambda *args, **kwargs: resolved_layouts.append(args),
    )

    result = run(monkeypatch, tmp_path, ["list", "tasks"])

    assert result.exit_code == 1
    assert "ai-team init" in result.stderr
    assert resolved_layouts == []
    assert "does not match" not in result.stderr


@pytest.mark.parametrize(
    "marker_text",
    [
        "[project]\ndir = 'ai-team'\n",
        "[init]\ntools = ['claude']\n",
        "[init]\nframework_version = ''\n",
        "[init]\nframework_version = 'not a version'\n",
        "[init]\nframework_version = 5\n",
        "[init\nbroken = =\n",
    ],
)
def test_no_warning_when_marker_version_is_missing_invalid_or_unparsable(
    monkeypatch, tmp_path, running_version, marker_text
):
    make_project(tmp_path, marker_text)

    result = run(monkeypatch, tmp_path, ["list", "tasks"])

    assert "does not match" not in result.stderr


def test_no_warning_for_init_with_mismatched_marker(
    monkeypatch, tmp_path, running_version
):
    make_project(tmp_path, marker_with_version(CONFIGURED_VERSION))

    result = run(
        monkeypatch,
        tmp_path,
        ["init", "--force", "--no-interactive", "--tools", "claude"],
    )

    assert result.exit_code == 0
    assert "does not match" not in result.stderr


def test_warning_leaves_stdout_json_and_exit_code_unchanged(
    monkeypatch, tmp_path, running_version
):
    make_project(tmp_path, marker_with_version(CONFIGURED_VERSION))
    mismatched = run(monkeypatch, tmp_path, ["list", "tasks", "--json"])
    (tmp_path / ".ai-team.toml").write_text(marker_with_version(RUNNING_VERSION))
    matching = run(monkeypatch, tmp_path, ["list", "tasks", "--json"])

    assert MISMATCH_WARNING in mismatched.stderr
    assert mismatched.exit_code == matching.exit_code
    assert mismatched.stdout == matching.stdout
    assert isinstance(json.loads(mismatched.stdout), list)


def test_lookup_error_is_swallowed_and_command_proceeds(
    monkeypatch, tmp_path, running_version
):
    make_project(tmp_path, marker_with_version(CONFIGURED_VERSION))

    def broken_resolve_layout(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr("ai_team.cli.resolve_layout", broken_resolve_layout)

    result = run(monkeypatch, tmp_path, ["list", "tasks"])

    assert result.exit_code == 0
    assert "does not match" not in result.stderr
