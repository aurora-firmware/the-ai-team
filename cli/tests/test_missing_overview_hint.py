"""Tests for the advisory missing-S-000 hint in `validate` and `report`."""

import json

import pytest
from typer.testing import CliRunner

from ai_team.commands._shared import OVERVIEW_HINT, hint_missing_overview
from ai_team.core.locator import find_project_root


@pytest.fixture
def project(monkeypatch, tmp_path):
    (tmp_path / "ai-team" / "specs").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _add_overview(project) -> None:
    (project / "ai-team" / "specs" / "S-000-system-overview.md").write_text(
        "", encoding="utf-8"
    )


def test_hint_is_a_single_line_naming_the_remedies():
    assert "\n" not in OVERVIEW_HINT
    assert "ai-team spec new --overview" in OVERVIEW_HINT
    assert "new-system-overview" in OVERVIEW_HINT


def test_hint_missing_overview_writes_hint_to_stderr_only_when_no_s_000(
    project, capsys
):
    hint_missing_overview(find_project_root(project))

    captured = capsys.readouterr()
    assert captured.err.strip() == OVERVIEW_HINT
    assert captured.out == ""


def test_hint_missing_overview_writes_nothing_when_s_000_exists(project, capsys):
    _add_overview(project)

    hint_missing_overview(find_project_root(project))

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_validate_prints_hint_to_stderr_and_keeps_json_stdout_clean(project):
    from ai_team.cli import app

    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert json.loads(result.stdout) == []


def test_validate_prints_no_hint_when_s_000_exists(project):
    from ai_team.cli import app

    _add_overview(project)

    result = CliRunner().invoke(app, ["validate", "--json"])

    assert OVERVIEW_HINT not in result.stderr


def test_validate_keeps_error_exit_code_when_hint_is_printed(project):
    from ai_team.cli import app

    (project / "ai-team" / "specs" / "S-001-bad.md").write_text(
        "not frontmatter", encoding="utf-8"
    )

    result = CliRunner().invoke(app, ["validate", "--specs", "--json"])

    assert OVERVIEW_HINT in result.stderr
    assert result.exit_code == 1


def test_report_prints_hint_to_stderr_and_stdout_is_only_the_path(project):
    from ai_team.cli import app

    out = project / "report.md"

    result = CliRunner().invoke(app, ["report", "--out", str(out)])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert result.stdout.strip() == str(out.resolve())


def test_report_prints_no_hint_when_s_000_exists(project):
    from ai_team.cli import app

    _add_overview(project)

    result = CliRunner().invoke(app, ["report", "--out", str(project / "r.md")])

    assert OVERVIEW_HINT not in result.stderr


def test_hint_is_printed_even_when_config_file_is_present(project):
    from ai_team.cli import app

    (project / ".ai-team.toml").write_text("", encoding="utf-8")

    result = CliRunner().invoke(app, ["validate", "--json"])

    assert OVERVIEW_HINT in result.stderr


def _raise(error: Exception):
    def _fail(_root):
        raise error

    return _fail


@pytest.mark.parametrize(
    "error",
    [
        PermissionError("denied"),
        OSError("io"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"),
    ],
)
def test_hint_missing_overview_swallows_existence_check_errors(
    project, capsys, monkeypatch, error
):
    monkeypatch.setattr("ai_team.commands._shared.overview_exists", _raise(error))

    hint_missing_overview(find_project_root(project))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_validate_keeps_stdout_and_exit_code_when_existence_check_raises(
    project, monkeypatch
):
    from ai_team.cli import app

    baseline = CliRunner().invoke(app, ["validate", "--json"])
    monkeypatch.setattr(
        "ai_team.commands._shared.overview_exists", _raise(PermissionError("denied"))
    )

    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code == baseline.exit_code == 0
    assert result.stdout == baseline.stdout
    assert OVERVIEW_HINT not in result.stderr


def test_hint_missing_overview_does_not_raise_for_undecodable_spec_file(
    project, capsys
):
    (project / "ai-team" / "specs" / "S-009-binary.md").write_bytes(b"---\n\xff\xfe")

    hint_missing_overview(find_project_root(project))

    assert capsys.readouterr().out == ""


def test_spec_new_prints_hint_to_stderr_and_stdout_is_only_the_path(project):
    from ai_team.cli import app

    result = CliRunner().invoke(app, ["spec", "new", "Billing"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert result.stdout.strip().endswith("S-001-billing.md")


def test_spec_new_json_stdout_stays_clean_when_hint_is_printed(project):
    from ai_team.cli import app

    result = CliRunner().invoke(app, ["spec", "new", "Billing", "--json"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert {"id", "path"} <= set(json.loads(result.stdout))


def test_spec_new_overview_prints_no_hint(project):
    from ai_team.cli import app

    result = CliRunner().invoke(app, ["spec", "new", "--overview"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT not in result.stderr


def test_spec_new_prints_no_hint_when_s_000_exists(project):
    from ai_team.cli import app

    _add_overview(project)

    result = CliRunner().invoke(app, ["spec", "new", "Billing"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT not in result.stderr


def test_adr_new_prints_hint_to_stderr_and_stdout_is_only_the_path(project):
    from ai_team.cli import app

    (project / "ai-team" / "decisions").mkdir()

    result = CliRunner().invoke(app, ["adr", "new", "Use queues"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert result.stdout.strip().endswith("use-queues.md")


def test_adr_new_prints_no_hint_when_s_000_exists(project):
    from ai_team.cli import app

    (project / "ai-team" / "decisions").mkdir()
    _add_overview(project)

    result = CliRunner().invoke(app, ["adr", "new", "Use queues"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT not in result.stderr


def test_status_prints_hint_to_stderr_and_keeps_json_stdout_clean(project):
    from ai_team.cli import app

    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert "counts" in json.loads(result.stdout)


def test_status_prints_no_hint_when_s_000_exists(project):
    from ai_team.cli import app

    _add_overview(project)

    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT not in result.stderr


_TRACKER_COMMANDS = [
    ["task", "new", "Do thing"],
    ["bug", "new", "Broken thing"],
    ["change-request", "new", "Change thing"],
]


@pytest.mark.parametrize("args", _TRACKER_COMMANDS)
def test_tracker_new_commands_print_hint_to_stderr_when_no_s_000(project, args):
    from ai_team.cli import app

    result = CliRunner().invoke(app, [*args, "--json"])

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert {"id", "path"} <= set(json.loads(result.stdout))


@pytest.mark.parametrize("args", _TRACKER_COMMANDS)
def test_tracker_new_commands_print_no_hint_when_s_000_exists(project, args):
    from ai_team.cli import app

    _add_overview(project)

    result = CliRunner().invoke(app, args)

    assert result.exit_code == 0
    assert OVERVIEW_HINT not in result.stderr


def test_task_new_for_s_000_succeeds_and_still_prints_hint_when_s_000_is_missing(
    project,
):
    from ai_team.cli import app

    result = CliRunner().invoke(
        app, ["task", "new", "Do thing", "--spec", "S-000", "--json"]
    )

    assert result.exit_code == 0
    assert OVERVIEW_HINT in result.stderr
    assert OVERVIEW_HINT not in result.stdout
    assert {"id", "path"} <= set(json.loads(result.stdout))
