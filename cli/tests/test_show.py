"""Tests for T-006: ai-team show command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def _project_dir(tmp_path):
    """The locator needs the project directory; work items live in the tracker."""
    (tmp_path / "ai-team").mkdir(exist_ok=True)


TASK_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: pending
priority: medium
assigned-role: developer
created: 2026-05-10
---

# {title}

{body}
"""

BUG_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
severity: high
status: {status}
created: 2026-05-10
---

# {title}

{body}
"""

SPEC_TEMPLATE = """\
---
title: "{title}"
version: "0.1"
status: approved
created: 2026-05-10
author: planner
---

# {title}

{body}
"""

ADR_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: accepted
created: 2026-05-10
---

# {title}

{body}
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _task(id: str, title: str, body: str) -> str:
    return TASK_TEMPLATE.format(id=id, title=title, body=body)


def _bug(id: str, title: str, status: str, body: str) -> str:
    return BUG_TEMPLATE.format(id=id, title=title, status=status, body=body)


def _spec(title: str, body: str) -> str:
    return SPEC_TEMPLATE.format(title=title, body=body)


def _adr(id: str, title: str, body: str) -> str:
    return ADR_TEMPLATE.format(id=id, title=title, body=body)


def test_show_exact_id_single_match_prints_markdown(monkeypatch, tmp_path):
    """`ai-team show T-001` prints markdown when exactly one file matches."""
    from ai_team.cli import app

    task_path = (
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-initial-scaffold.md"
    )
    _write(task_path, _task("T-001", "Initial scaffold", "Task body line."))

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["show", "T-001"])

    assert result.exit_code == 0
    assert "Initial scaffold" in result.stdout
    assert "Task body line." in result.stdout


def test_show_json_returns_flat_fields_path_and_body(monkeypatch, tmp_path):
    """`--json` emits one JSON object and no Rich output."""
    import json

    from ai_team.cli import app

    task_path = tmp_path / ".ai-team" / "tracker" / "tasks" / "T-002-json-case.md"
    _write(task_path, _task("T-002", "JSON case", "Body for json."))

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["show", "T-002", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "path": str(task_path),
        "id": "T-002",
        "title": "JSON case",
        "status": "pending",
        "priority": "medium",
        "assigned-role": "developer",
        "created": "2026-05-10",
        "body": "# JSON case\n\nBody for json.\n",
    }


@pytest.mark.parametrize(
    ("artifact_path", "identifier", "expected_text"),
    [
        (
            ("tasks", "in-progress", "T-040-follow-up.md"),
            "T-040",
            "Follow up",
        ),
        (
            ("bugs", "resolved", "B-007-context-loss.md"),
            "B-007",
            "Context loss",
        ),
        (
            ("specs", "S-003-artifact-index.md"),
            "S-003",
            "Artifact index",
        ),
        (
            ("specs", "S-003-artifact-index.md"),
            "artifact-index",
            "Artifact index",
        ),
        (
            ("decisions", "ADR-001-show-command.md"),
            "ADR-001",
            "Adopt show command",
        ),
    ],
)
def test_show_resolves_ids_across_artifact_types_and_states(
    monkeypatch, tmp_path, artifact_path, identifier, expected_text
):
    """IDs resolve across tasks/bugs/specs/decisions and state folders."""
    from ai_team.cli import app

    if artifact_path[0] == "tasks":
        path = tmp_path / ".ai-team" / "tracker" / "tasks" / artifact_path[2]
        content = _task(identifier, expected_text, "Task content.")
    elif artifact_path[0] == "bugs":
        path = tmp_path / ".ai-team" / "tracker" / "bugs" / artifact_path[2]
        content = _bug(identifier, expected_text, artifact_path[1], "Bug content.")
    elif artifact_path[0] == "specs":
        path = tmp_path / "ai-team" / artifact_path[0] / artifact_path[1]
        content = _spec(expected_text, "Spec content.")
    else:
        path = tmp_path / "ai-team" / artifact_path[0] / artifact_path[1]
        content = _adr(identifier, expected_text, "ADR content.")

    _write(path, content)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["show", identifier])

    assert result.exit_code == 0
    assert expected_text in result.stdout


def test_show_multiple_matches_prints_candidates_to_stderr_and_exits_non_zero(
    monkeypatch, tmp_path
):
    """Ambiguous identifiers print candidate paths to stderr and exit non-zero."""
    from ai_team.cli import app

    first = tmp_path / ".ai-team" / "tracker" / "tasks" / "T-100-shared-slug.md"
    second = tmp_path / ".ai-team" / "tracker" / "tasks" / "T-101-shared-slug.md"
    _write(first, _task("T-100", "Shared slug one", "Body one."))
    _write(second, _task("T-101", "Shared slug two", "Body two."))

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["show", "shared-slug"])

    assert result.exit_code != 0
    assert str(first) in result.stderr
    assert str(second) in result.stderr
    assert "multiple artifacts matched" in result.stderr.lower()


def test_show_no_match_prints_not_found_with_searched_roots_and_exits_non_zero(
    monkeypatch, tmp_path
):
    """No matches print a not-found message naming searched roots and exit non-zero."""
    from ai_team.cli import app

    (tmp_path / ".ai-team" / "tracker" / "tasks").mkdir(parents=True)
    (tmp_path / ".ai-team" / "tracker" / "bugs").mkdir(parents=True)
    (tmp_path / "ai-team" / "specs").mkdir(parents=True)
    (tmp_path / "ai-team" / "decisions").mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["show", "T-999"])

    assert result.exit_code != 0
    stderr = result.stderr
    assert "not found" in stderr.lower()
    assert "T-999" in stderr
    assert str(tmp_path / ".ai-team" / "tracker" / "tasks") in stderr
    assert str(tmp_path / ".ai-team" / "tracker" / "bugs") in stderr
    assert str(tmp_path / ".ai-team" / "tracker" / "change-requests") in stderr
    assert str(tmp_path / "ai-team" / "specs") in stderr
    assert str(tmp_path / "ai-team" / "decisions") in stderr
