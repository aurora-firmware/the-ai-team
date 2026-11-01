"""Tests for T-005: ai-team list command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def _project_dir(tmp_path):
    """The locator needs the project directory; work items live in the tracker."""
    (tmp_path / "ai-team").mkdir(exist_ok=True)


TASK_TEMPLATE = """\
---
id: \"{id}\"
title: \"{title}\"
status: {status}
priority: {priority}
assigned-role: {assigned_role}
created: 2026-05-10
---

Body.
"""

BUG_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
severity: {severity}
status: {status}
created: 2026-05-10
---

Body.
"""

SPEC_TEMPLATE = """\
---
title: "{title}"
version: "{version}"
status: {status}
created: 2026-05-10
author: planner
id: "{id}"
---

Body.
"""

ADR_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: {status}
created: 2026-05-10
---

Body.
"""

CHANGE_REQUEST_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: {status}
created: 2026-05-10
---

Body.
"""


def _fields_of(rows: list[dict], *keys: str) -> list[dict]:
    """Return *rows* reduced to *keys*, after checking each row carries an absolute path."""
    for row in rows:
        assert Path(row["path"]).is_absolute()
        assert "state" not in row
    return [{key: row[key] for key in keys} for row in rows]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _task(
    id: str,
    title: str,
    status: str,
    priority: str = "medium",
    assigned_role: str = "developer",
) -> str:
    return TASK_TEMPLATE.format(
        id=id,
        title=title,
        status=status,
        priority=priority,
        assigned_role=assigned_role,
    )


def _bug(id: str, title: str, severity: str, status: str) -> str:
    return BUG_TEMPLATE.format(
        id=id,
        title=title,
        severity=severity,
        status=status,
    )


def _spec(title: str, version: str, status: str, spec_id: str = "S-001") -> str:
    return SPEC_TEMPLATE.format(
        title=title,
        version=version,
        status=status,
        id=spec_id,
    )


def _adr(id: str, title: str, status: str) -> str:
    return ADR_TEMPLATE.format(
        id=id,
        title=title,
        status=status,
    )


def _change_request(id: str, title: str, status: str) -> str:
    return CHANGE_REQUEST_TEMPLATE.format(
        id=id,
        title=title,
        status=status,
    )


def test_list_tasks_displays_all_states_in_rich_table_and_skips_templates(
    monkeypatch, tmp_path
):
    """`ai-team list tasks` prints non-template tasks from every state."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Pending task", "pending", "high"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-002.md",
        _task("T-002", "In-progress task", "in-progress"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-003.md",
        _task("T-003", "Completed task", "completed", "low", "reviewer"),
    )
    _write(tmp_path / ".ai-team" / "tracker" / "tasks" / ".gitkeep", "")
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "TEMPLATE-task.md",
        _task("T-000", "Template task", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "tasks"])

    assert result.exit_code == 0
    assert "ID" in result.stdout
    assert "Title" in result.stdout
    assert "Status" in result.stdout
    assert "Priority" in result.stdout
    assert "Assigned-Role" in result.stdout
    assert "T-001" in result.stdout
    assert "T-002" in result.stdout
    assert "T-003" in result.stdout
    assert "Template task" not in result.stdout
    assert "T-000" not in result.stdout


def test_list_tasks_state_filter_only_includes_matching_folder(monkeypatch, tmp_path):
    """`--state` filters tasks by task state folder name."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Pending task", "pending"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-002.md",
        _task("T-002", "In-progress task", "in-progress"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "tasks", "--state", "pending"])

    assert result.exit_code == 0
    assert "T-001" in result.stdout
    assert "Pending task" in result.stdout
    assert "T-002" not in result.stdout
    assert "In-progress task" not in result.stdout


def test_list_tasks_json_outputs_plain_list_without_rich_table(monkeypatch, tmp_path):
    """`--json` emits a JSON list with task fields and no table title/header."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Pending task", "pending", "high", "developer"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "tasks", "--json"])

    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert _fields_of(parsed, "id", "title", "status", "priority", "assigned-role") == [
        {
            "id": "T-001",
            "title": "Pending task",
            "status": "pending",
            "priority": "high",
            "assigned-role": "developer",
        }
    ]
    assert "Tasks" not in result.stdout
    assert "┏" not in result.stdout


def test_list_bugs_renders_table_and_json_and_skips_templates(monkeypatch, tmp_path):
    """`list bugs` shows id/title/state/severity and supports JSON output."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-001.md",
        _bug("B-001", "Open bug", "high", "open"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-002.md",
        _bug("B-002", "In-progress bug", "low", "in-progress"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "TEMPLATE-bug.md",
        _bug("B-000", "Template bug", "low", "open"),
    )
    _write(tmp_path / ".ai-team" / "tracker" / "bugs" / ".gitkeep", "")

    monkeypatch.chdir(tmp_path)

    table_result = CliRunner().invoke(app, ["list", "bugs"])
    assert table_result.exit_code == 0
    assert "ID" in table_result.stdout
    assert "Title" in table_result.stdout
    assert "Status" in table_result.stdout
    assert "Severity" in table_result.stdout
    assert "B-001" in table_result.stdout
    assert "B-002" in table_result.stdout
    assert "Template bug" not in table_result.stdout

    json_result = CliRunner().invoke(app, ["list", "bugs", "--json"])
    assert json_result.exit_code == 0
    parsed = json.loads(json_result.stdout)
    assert _fields_of(parsed, "id", "title", "status", "severity") == [
        {
            "id": "B-001",
            "title": "Open bug",
            "status": "open",
            "severity": "high",
        },
        {
            "id": "B-002",
            "title": "In-progress bug",
            "status": "in-progress",
            "severity": "low",
        },
    ]
    assert "Bugs" not in json_result.stdout


def test_list_specs_and_adrs_include_expected_columns_and_fields(monkeypatch, tmp_path):
    """`list specs` and `list adrs` expose required columns and JSON fields."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "ai-team-cli.md",
        _spec("CLI Spec", "0.1", "approved"),
    )
    _write(
        tmp_path / "ai-team" / "specs" / "TEMPLATE-spec.md",
        _spec("Template spec", "0.0", "draft"),
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "ADR-001.md",
        _adr("ADR-001", "Use Rich tables", "accepted"),
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "TEMPLATE-adr.md",
        _adr("ADR-000", "Template adr", "proposed"),
    )

    monkeypatch.chdir(tmp_path)

    specs_table = CliRunner().invoke(app, ["list", "specs"])
    assert specs_table.exit_code == 0
    assert "ID" in specs_table.stdout
    assert "Title" in specs_table.stdout
    assert "Status" in specs_table.stdout
    assert "Version" in specs_table.stdout
    assert "S-001" in specs_table.stdout
    assert "CLI Spec" in specs_table.stdout
    assert "Template spec" not in specs_table.stdout

    specs_json = CliRunner().invoke(app, ["list", "specs", "--json"])
    assert specs_json.exit_code == 0
    assert _fields_of(
        json.loads(specs_json.stdout), "id", "title", "status", "version"
    ) == [
        {
            "id": "S-001",
            "title": "CLI Spec",
            "status": "approved",
            "version": "0.1",
        }
    ]

    adrs_table = CliRunner().invoke(app, ["list", "adrs"])
    assert adrs_table.exit_code == 0
    assert "ID" in adrs_table.stdout
    assert "Title" in adrs_table.stdout
    assert "Status" in adrs_table.stdout
    assert "ADR-001" in adrs_table.stdout
    assert "Template adr" not in adrs_table.stdout

    adrs_json = CliRunner().invoke(app, ["list", "adrs", "--json"])
    assert adrs_json.exit_code == 0
    assert _fields_of(json.loads(adrs_json.stdout), "id", "title", "status") == [
        {
            "id": "ADR-001",
            "title": "Use Rich tables",
            "status": "accepted",
        }
    ]


def test_list_change_requests_displays_id_title_state_in_rich_table(
    monkeypatch, tmp_path
):
    """`list change-requests` shows ID, Title, and Status columns in a table."""
    from ai_team.cli import app

    _write(
        tmp_path
        / ".ai-team"
        / "tracker"
        / "change-requests"
        / "CR-001-add-new-step.md",
        _change_request("CR-001", "Add new step", "pending"),
    )
    _write(
        tmp_path
        / ".ai-team"
        / "tracker"
        / "change-requests"
        / "CR-002-revise-scope.md",
        _change_request("CR-002", "Revise scope", "approved"),
    )
    _write(
        tmp_path
        / ".ai-team"
        / "tracker"
        / "change-requests"
        / "TEMPLATE-change-request.md",
        _change_request("CR-000", "Template CR", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "change-requests"])

    assert result.exit_code == 0
    assert "ID" in result.stdout
    assert "Title" in result.stdout
    assert "Status" in result.stdout
    assert "CR-001" in result.stdout
    assert "Add new step" in result.stdout
    assert "CR-002" in result.stdout
    assert "Revise scope" in result.stdout
    assert "Template CR" not in result.stdout
    assert "CR-000" not in result.stdout


def test_list_change_requests_json_outputs_machine_readable_rows(monkeypatch, tmp_path):
    """`list change-requests --json` emits JSON rows without table formatting."""
    from ai_team.cli import app

    _write(
        tmp_path
        / ".ai-team"
        / "tracker"
        / "change-requests"
        / "CR-001-add-new-step.md",
        _change_request("CR-001", "Add new step", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "change-requests", "--json"])

    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert _fields_of(parsed, "id", "title", "status") == [
        {
            "id": "CR-001",
            "title": "Add new step",
            "status": "pending",
        }
    ]
    assert "Change Requests" not in result.stdout
    assert "┏" not in result.stdout


def test_list_change_requests_returns_empty_list_when_no_change_requests_exist(
    monkeypatch, tmp_path
):
    """`list change-requests` returns an empty list without error when folder is empty."""
    from ai_team.cli import app

    (tmp_path / ".ai-team" / "tracker" / "change-requests").mkdir(
        parents=True, exist_ok=True
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "change-requests", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_list_specs_reports_frontmatter_id_not_filename_stem_for_prefixed_filenames(
    monkeypatch, tmp_path
):
    """`list specs` ID column shows frontmatter id, not the filename stem."""
    from ai_team.cli import app

    # New-style filename: S-NNN-slug.md — stem is "S-007-my-spec", frontmatter id is "S-007"
    _write(
        tmp_path / "ai-team" / "specs" / "S-007-my-spec.md",
        _spec("My Spec", "1.0", "approved", spec_id="S-007"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "specs", "--json"])

    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert _fields_of(parsed, "id", "title", "status", "version") == [
        {
            "id": "S-007",
            "title": "My Spec",
            "status": "approved",
            "version": "1.0",
        }
    ]


def test_list_specs_and_adrs_state_filter_keeps_matching_status(monkeypatch, tmp_path):
    """`list specs --state` and `list adrs --state` keep only matching statuses."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001-a.md",
        _spec("Approved spec", "0.1", "approved", spec_id="S-001"),
    )
    _write(
        tmp_path / "ai-team" / "specs" / "S-002-b.md",
        _spec("Draft spec", "0.1", "draft", spec_id="S-002"),
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "ADR-001.md",
        _adr("ADR-001", "Accepted adr", "accepted"),
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "ADR-002.md",
        _adr("ADR-002", "Proposed adr", "proposed"),
    )

    monkeypatch.chdir(tmp_path)

    specs = CliRunner().invoke(app, ["list", "specs", "--state", "draft", "--json"])
    assert specs.exit_code == 0
    assert [row["id"] for row in json.loads(specs.stdout)] == ["S-002"]

    adrs = CliRunner().invoke(app, ["list", "adrs", "--state", "accepted", "--json"])
    assert adrs.exit_code == 0
    assert [row["id"] for row in json.loads(adrs.stdout)] == ["ADR-001"]
