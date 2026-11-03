"""Tests for T-007: ai-team status command."""

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
{extra_frontmatter}
---

{body}
"""

BUG_TEMPLATE = """\
---
id: \"{id}\"
title: \"{title}\"
severity: {severity}
status: {status}
created: 2026-05-10
---

Body.
"""

SPEC_TEMPLATE = """\
---
title: \"{title}\"
version: \"{version}\"
status: {status}
created: 2026-05-10
author: planner
---

Body.
"""

ADR_TEMPLATE = """\
---
id: \"{id}\"
title: \"{title}\"
status: {status}
created: 2026-05-10
---

Body.
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _task(
    id: str,
    title: str,
    status: str,
    *,
    priority: str = "medium",
    assigned_role: str = "developer",
    body: str = "Body.",
    extra_frontmatter: str = "",
) -> str:
    return TASK_TEMPLATE.format(
        id=id,
        title=title,
        status=status,
        priority=priority,
        assigned_role=assigned_role,
        body=body,
        extra_frontmatter=extra_frontmatter,
    )


def _bug(id: str, title: str, severity: str, status: str) -> str:
    return BUG_TEMPLATE.format(
        id=id,
        title=title,
        severity=severity,
        status=status,
    )


def _spec(title: str, version: str, status: str) -> str:
    return SPEC_TEMPLATE.format(
        title=title,
        version=version,
        status=status,
    )


def _adr(id: str, title: str, status: str) -> str:
    return ADR_TEMPLATE.format(
        id=id,
        title=title,
        status=status,
    )


def test_status_rich_summary_includes_counts_and_key_lists(monkeypatch, tmp_path):
    """`ai-team status` shows counts plus key task and bug lists."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001.md", _spec("Spec 1", "0.1", "approved")
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Pending task", "pending"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-002.md",
        _task("T-002", "In progress task", "in-progress", assigned_role="reviewer"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-003.md",
        _task("T-003", "Completed task", "completed"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-004.md",
        _task(
            "T-004",
            "Blocked task",
            "blocked",
            extra_frontmatter="blocking-reason: waiting on dependency\n",
        ),
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "ADR-001.md",
        _adr("ADR-001", "Decision 1", "accepted"),
    )

    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-001.md",
        _bug("B-001", "Critical bug", "critical", "open"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-002.md",
        _bug("B-002", "High bug", "high", "open"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-003.md",
        _bug("B-003", "Low bug", "low", "open"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-004.md",
        _bug("B-004", "In-progress bug", "medium", "in-progress"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-005.md",
        _bug("B-005", "Resolved bug", "medium", "resolved"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status"])

    assert result.exit_code == 0
    assert "Active specs" in result.stdout
    assert "1" in result.stdout
    assert "Pending tasks" in result.stdout
    assert "In progress" in result.stdout
    assert "Completed" in result.stdout
    assert "Blocked" in result.stdout
    assert "Open bugs" in result.stdout
    assert "Bugs in progress" in result.stdout
    assert "ADRs" in result.stdout

    assert "T-002" in result.stdout
    assert "reviewer" in result.stdout

    assert "T-004" in result.stdout
    assert "waiting on dependency" in result.stdout

    assert "B-001" in result.stdout
    assert "B-002" in result.stdout
    assert "B-003" not in result.stdout


def test_status_json_emits_structured_payload_without_rich_table(monkeypatch, tmp_path):
    """`ai-team status --json` emits JSON and no Rich frame characters."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001.md", _spec("Spec 1", "0.1", "approved")
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-100.md",
        _task("T-100", "Do work", "in-progress", assigned_role="developer"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["counts"]["specs_active"] == 1
    assert payload["counts"]["tasks"]["in_progress"] == 1
    assert payload["in_progress_tasks"] == [
        {
            "id": "T-100",
            "title": "Do work",
            "assigned_role": "developer",
        }
    ]
    assert payload["counts"]["tasks"] == {
        "planned": 0,
        "pending": 0,
        "in_progress": 1,
        "completed": 0,
        "blocked": 0,
        "cancelled": 0,
    }
    assert payload["counts"]["bugs"] == {
        "open": 0,
        "in_progress": 0,
        "blocked": 0,
        "resolved": 0,
    }
    assert payload["blocked_bugs"] == []
    assert payload["counts"]["adrs"] == 0
    assert payload["latest_integration_result"] == "not found"
    assert "┏" not in result.stdout


def test_status_blocked_task_uses_latest_work_log_when_frontmatter_reason_missing(
    monkeypatch, tmp_path
):
    """Blocked reason falls back to latest Work Log entry when missing."""
    from ai_team.cli import app

    blocked_body = """\
## Description

Blocked.

## Work Log

### Session 1 — 2026-05-10
waiting on API contract clarification

### Session 2 — 2026-05-11
stuck on reviewer approval
"""
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-200.md",
        _task(
            "T-200",
            "Needs review",
            "blocked",
            body=blocked_body,
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["blocked_tasks"] == [
        {
            "id": "T-200",
            "title": "Needs review",
            "blocking_reason": "stuck on reviewer approval",
        }
    ]


def test_status_counts_and_lists_blocked_bugs(monkeypatch, tmp_path):
    """Blocked bugs are counted and listed with their latest Work Log reason."""
    from ai_team.cli import app

    blocked_bug = _bug("B-300", "Deferred crash", "high", "blocked") + (
        "\n## Work Log\n\n### Session 1 — 2026-05-11\n"
        "Blocked: deferred by the product owner\n"
    )
    _write(tmp_path / ".ai-team" / "tracker" / "bugs" / "B-300.md", blocked_bug)
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-300.md",
        _task(
            "T-300",
            "Blocked task",
            "blocked",
            extra_frontmatter="blocking-reason: waiting on dependency\n",
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["counts"]["bugs"]["blocked"] == 1
    assert payload["counts"]["tasks"]["blocked"] == 1
    assert payload["blocked_bugs"] == [
        {
            "id": "B-300",
            "title": "Deferred crash",
            "blocking_reason": "Blocked: deferred by the product owner",
        }
    ]
    assert [row["id"] for row in payload["blocked_tasks"]] == ["T-300"]
    assert payload["critical_high_open_bugs"] == []

    rich = CliRunner().invoke(app, ["status"])
    assert "Blocked bugs: 1" in rich.stdout
    assert "B-300" in rich.stdout
    assert "deferred by the product owner" in rich.stdout


def _git(tmp_path: Path, cmd: str) -> None:
    import subprocess

    subprocess.run(
        cmd,
        shell=True,
        check=True,
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _init_repo(tmp_path: Path) -> None:
    _git(tmp_path, "git init -b main")
    _git(tmp_path, "git config user.name 'Test User'")
    _git(tmp_path, "git config user.email 'test@example.com'")
    _git(tmp_path, "git add .")
    _git(tmp_path, "git commit -m 'chore(repo): initial fixture'")


def _integration_result(monkeypatch, tmp_path: Path) -> str:
    from ai_team.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    return json.loads(result.stdout)["latest_integration_result"]


def _work_log(*sessions: tuple[int, str, str]) -> str:
    entries = "\n\n".join(
        f"### Session {number} — {date}\n{text}" for number, date, text in sessions
    )
    return f"## Work Log\n\n{entries}\n\n## Review\n"


def test_status_ignores_matching_commit_on_unmerged_branch(monkeypatch, tmp_path):
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Pending task", "pending"),
    )
    _init_repo(tmp_path)
    _git(tmp_path, "git checkout -b feature/x")
    _git(tmp_path, "git commit --allow-empty -m 'wip: add test scaffolding'")
    _git(tmp_path, "git checkout main")

    assert _integration_result(monkeypatch, tmp_path) == "not found"


def test_status_ignores_spec_merge_commit_on_integration_branch(monkeypatch, tmp_path):
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Pending task", "pending"),
    )
    _init_repo(tmp_path)
    _git(
        tmp_path,
        "git commit --allow-empty -m 'chore(plan): merge S-007 system overview spec'",
    )

    assert _integration_result(monkeypatch, tmp_path) == "not found"


def test_status_reports_latest_work_log_session_of_completed_items(
    monkeypatch, tmp_path
):
    tracker = tmp_path / ".ai-team" / "tracker"
    _write(
        tracker / "tasks" / "T-001.md",
        _task(
            "T-001",
            "Old task",
            "completed",
            body=_work_log((1, "2026-05-01", "Old verification output.")),
        ),
    )
    _write(
        tracker / "tasks" / "T-002.md",
        _task(
            "T-002",
            "Pending with newer log",
            "pending",
            body=_work_log((1, "2026-06-30", "Not completed, must be ignored.")),
        ),
    )
    _write(
        tracker / "bugs" / "B-003.md",
        BUG_TEMPLATE.format(
            id="B-003", title="Fixed bug", severity="low", status="resolved"
        ).replace(
            "Body.",
            _work_log(
                (1, "2026-05-02", "First pass."),
                (2, "2026-06-01", "pytest: 12 passed."),
            ),
        ),
    )

    assert _integration_result(monkeypatch, tmp_path) == (
        "B-003 Session 2 (2026-06-01): pytest: 12 passed."
    )


def test_status_breaks_date_ties_with_highest_item_id(monkeypatch, tmp_path):
    tracker = tmp_path / ".ai-team" / "tracker" / "tasks"
    for number in (5, 12):
        _write(
            tracker / f"T-{number:03d}.md",
            _task(
                f"T-{number:03d}",
                "Task",
                "completed",
                body=_work_log((1, "2026-06-01", f"Result {number}.")),
            ),
        )

    assert _integration_result(monkeypatch, tmp_path) == (
        "T-012 Session 1 (2026-06-01): Result 12."
    )


def test_status_breaks_same_number_ties_between_task_and_bug_by_item_id(
    monkeypatch, tmp_path
):
    tracker = tmp_path / ".ai-team" / "tracker"
    _write(
        tracker / "tasks" / "T-012.md",
        _task(
            "T-012",
            "Task",
            "completed",
            body=_work_log((1, "2026-06-01", "Task result.")),
        ),
    )
    _write(
        tracker / "bugs" / "B-012.md",
        BUG_TEMPLATE.format(
            id="B-012", title="Bug", severity="low", status="resolved"
        ).replace("Body.", _work_log((1, "2026-06-01", "Bug result."))),
    )

    assert _integration_result(monkeypatch, tmp_path) == (
        "T-012 Session 1 (2026-06-01): Task result."
    )


def test_status_reports_not_found_when_completed_item_has_no_sessions(
    monkeypatch, tmp_path
):
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001.md",
        _task("T-001", "Done task", "completed"),
    )

    assert _integration_result(monkeypatch, tmp_path) == "not found"


def test_status_counts_every_task_state(monkeypatch, tmp_path):
    """`status --json` counts planned and cancelled tasks alongside the others."""
    from ai_team.cli import app

    tasks = tmp_path / ".ai-team" / "tracker" / "tasks"
    _write(tasks / "T-001.md", _task("T-001", "Planned", "planned"))
    _write(tasks / "T-002.md", _task("T-002", "Cancelled", "cancelled"))

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    counts = json.loads(result.stdout)["counts"]["tasks"]
    assert counts["planned"] == 1
    assert counts["cancelled"] == 1

    rich = CliRunner().invoke(app, ["status"])
    assert "Planned tasks: 1" in rich.stdout
    assert "Cancelled tasks: 1" in rich.stdout


def test_status_active_specs_exclude_superseded_and_overview(monkeypatch, tmp_path):
    """Superseded specs and the S-000 overview are not counted as active specs."""
    from ai_team.cli import app

    specs = tmp_path / "ai-team" / "specs"
    _write(specs / "S-000-overview.md", _spec("Overview", "0.1", "approved"))
    _write(specs / "S-001-a.md", _spec("Live", "0.1", "approved"))
    _write(specs / "S-002-b.md", _spec("Old", "0.1", "superseded"))

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["counts"]["specs_active"] == 1
