"""Tests for T-017: ai-team validate command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.spec_fixtures import feature_spec_body


@pytest.fixture(autouse=True)
def _project_dir(tmp_path):
    """The locator needs the project directory; work items live in the tracker."""
    (tmp_path / "ai-team").mkdir(exist_ok=True)


TASK_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: {status}
priority: medium
assigned-role: developer
created: 2026-05-10
{extra_frontmatter}
---

Body.
"""

BUG_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
severity: medium
status: {status}
created: 2026-05-10
{extra_frontmatter}
---

Body.
"""

SPEC_TEMPLATE = """\
---
title: "{title}"
version: "0.1"
status: approved
created: 2026-05-10
author: planner
id: "{id}"
---

{body}
"""

ADR_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: accepted
created: 2026-05-10
{extra_frontmatter}
---

Body.
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _task(task_id: str, title: str, status: str, *, extra_frontmatter: str = "") -> str:
    return TASK_TEMPLATE.format(
        id=task_id,
        title=title,
        status=status,
        extra_frontmatter=extra_frontmatter,
    )


def _bug(bug_id: str, title: str, status: str, *, extra_frontmatter: str = "") -> str:
    return BUG_TEMPLATE.format(
        id=bug_id,
        title=title,
        status=status,
        extra_frontmatter=extra_frontmatter,
    )


def _spec(spec_id: str, title: str) -> str:
    return SPEC_TEMPLATE.format(id=spec_id, title=title, body=feature_spec_body())


def _adr(adr_id: str, title: str, *, extra_frontmatter: str = "") -> str:
    return ADR_TEMPLATE.format(
        id=adr_id,
        title=title,
        extra_frontmatter=extra_frontmatter,
    )


def _seed_valid_project(root: Path) -> None:
    _write(
        root / "ai-team" / "specs" / "roadmap-spec.md",
        _spec("S-001", "Roadmap Spec"),
    )
    _write(
        root / ".ai-team" / "tracker" / "tasks" / "T-001-roadmap-task.md",
        _task(
            "T-001",
            "Roadmap Task",
            "pending",
            extra_frontmatter='spec: "roadmap-spec"\n',
        ),
    )
    _write(
        root / ".ai-team" / "tracker" / "bugs" / "B-001-roadmap-bug.md",
        _bug(
            "B-001",
            "Roadmap Bug",
            "open",
            extra_frontmatter='task: "T-001"\n',
        ),
    )
    _write(
        root / "ai-team" / "decisions" / "ADR-001-roadmap-decision.md",
        _adr("ADR-001", "Roadmap Decision"),
    )


def test_validate_exits_zero_and_reports_zero_findings_for_clean_project(
    monkeypatch, tmp_path
):
    """`ai-team validate` exits 0 with zero findings for valid artifacts."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "0 finding" in result.stdout


def test_validate_emits_error_when_status_is_not_an_allowed_value(
    monkeypatch, tmp_path
):
    """Task status must be one of the allowed tracker statuses (S-006)."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-002-status-mismatch.md",
        _task("T-002", "Mismatch Task", "done"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(
        finding["code"] == "status-invalid"
        and finding["path"].endswith(".ai-team/tracker/tasks/T-002-status-mismatch.md")
        for finding in findings
    )


def test_validate_emits_error_when_cross_references_do_not_resolve(
    monkeypatch, tmp_path
):
    """Missing task->spec, bug->task, and ADR supersedes references are errors."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-003-missing-spec.md",
        _task(
            "T-003",
            "Task Missing Spec",
            "pending",
            extra_frontmatter='spec: "missing-spec"\n',
        ),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-002-missing-task.md",
        _bug(
            "B-002",
            "Bug Missing Task",
            "open",
            extra_frontmatter='task: "T-999"\n',
        ),
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "ADR-002-missing-supersedes.md",
        _adr(
            "ADR-002",
            "Missing Supersedes",
            extra_frontmatter='supersedes: "ADR-999"\n',
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(
        finding["code"] == "task-spec-missing" and "missing-spec" in finding["message"]
        for finding in findings
    )
    assert any(
        finding["code"] == "bug-task-missing" and "T-999" in finding["message"]
        for finding in findings
    )
    assert any(
        finding["code"] == "adr-supersedes-missing" and "ADR-999" in finding["message"]
        for finding in findings
    )


def test_validate_json_outputs_plain_list_without_rich_table(monkeypatch, tmp_path):
    """`validate --json` prints only a JSON list and no Rich table/frame output."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-010-bad-status.md",
        _task("T-010", "Bad status", "done"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code != 0
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, list)
    assert "┏" not in result.stdout
    assert "Validation Findings" not in result.stdout


def test_validate_exits_non_zero_when_any_error_finding_exists(monkeypatch, tmp_path):
    """Any error-level finding causes a non-zero exit code."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-010-status-mismatch.md",
        _bug("B-010", "Bad bug status", "closed"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate"])

    assert result.exit_code != 0
    assert "status-invalid" in result.stdout


def test_validate_detects_frontmatter_id_and_filename_violations(monkeypatch, tmp_path):
    """Validation reports required-frontmatter, id pattern, and filename issues."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "not-task.md",
        _task("TASK-001", "Bad Task ID", "pending"),
    )
    _write(
        tmp_path / "ai-team" / "specs" / "Bad Spec Name.md",
        """\
---
title: "Bad Spec"
version: "0.1"
status: approved
created: 2026-05-10
---

Body.
""",
    )
    _write(
        tmp_path / "ai-team" / "decisions" / "ADR-010.md",
        _adr("ADR-010", "Missing Slug"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    codes = {finding["code"] for finding in findings}
    assert "frontmatter-invalid" in codes
    assert "id-pattern" in codes
    assert "filename-pattern" in codes


def test_validate_scope_flags_limit_checked_artifact_kinds(monkeypatch, tmp_path):
    """Selecting `--tasks` excludes unrelated bug validation findings."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-010-status-mismatch.md",
        _bug("B-010", "Bad bug status", "closed"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--tasks", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


CHANGE_REQUEST_TEMPLATE = """\
---
id: "{id}"
title: "{title}"
status: {status}
created: 2026-05-10
---

Body.
"""


def _change_request(cr_id: str, title: str, status: str) -> str:
    return CHANGE_REQUEST_TEMPLATE.format(
        id=cr_id,
        title=title,
        status=status,
    )


def test_validate_change_requests_reports_valid_cr_with_no_findings(
    monkeypatch, tmp_path
):
    """`validate --change-requests` reports zero findings for a valid change request."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "change-requests" / "CR-001-add-step.md",
        _change_request("CR-001", "Add step", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--change-requests", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_change_requests_reports_frontmatter_error_for_missing_required_field(
    monkeypatch, tmp_path
):
    """`validate --change-requests` emits frontmatter-invalid for a malformed CR."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "change-requests" / "CR-002-bad.md",
        """\
---
title: "Bad CR missing id"
status: pending
created: 2026-05-10
---

Body.
""",
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--change-requests", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(finding["code"] == "frontmatter-invalid" for finding in findings)


def test_validate_change_requests_reports_id_pattern_error(monkeypatch, tmp_path):
    """`validate --change-requests` emits id-pattern for a non-CR-NNN id."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "change-requests" / "CR-003-bad-id.md",
        _change_request("CHANGE-003", "Bad ID format", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--change-requests", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(finding["code"] == "id-pattern" for finding in findings)


def test_validate_change_requests_reports_filename_pattern_error(monkeypatch, tmp_path):
    """`validate --change-requests` emits filename-pattern for wrong filename format."""
    from ai_team.cli import app

    _write(
        tmp_path / ".ai-team" / "tracker" / "change-requests" / "not-a-cr.md",
        _change_request("CR-004", "Good ID bad filename", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--change-requests", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(finding["code"] == "filename-pattern" for finding in findings)


def test_validate_scope_change_requests_flag_excludes_other_artifact_kinds(
    monkeypatch, tmp_path
):
    """`--change-requests` scope flag excludes bugs and tasks from validation."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    # A bug with a bad status — should not appear when only --change-requests is set
    _write(
        tmp_path / ".ai-team" / "tracker" / "bugs" / "B-010-status-mismatch.md",
        _bug("B-010", "Bad bug status", "closed"),
    )
    # A valid change request
    _write(
        tmp_path / ".ai-team" / "tracker" / "change-requests" / "CR-001-valid.md",
        _change_request("CR-001", "Valid CR", "pending"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--change-requests", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_default_scope_includes_change_requests(monkeypatch, tmp_path):
    """Default validate (no scope flags) also validates change requests."""
    from ai_team.cli import app

    _seed_valid_project(tmp_path)
    _write(
        tmp_path / ".ai-team" / "tracker" / "change-requests" / "CR-999-bad.md",
        """\
---
title: "Missing id field"
status: pending
created: 2026-05-10
---

Body.
""",
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(finding["code"] == "frontmatter-invalid" for finding in findings)


def test_validate_specs_accepts_new_s_nnn_slug_filename_with_matching_id(
    monkeypatch, tmp_path
):
    """`validate --specs` reports no findings for a valid S-NNN-<slug>.md spec."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001-launch-plan.md",
        _spec("S-001", "Launch Plan"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--specs", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_specs_reports_filename_id_mismatch_when_prefix_does_not_match_frontmatter(
    monkeypatch, tmp_path
):
    """`validate --specs` emits filename-pattern when S-NNN prefix mismatches frontmatter id."""
    from ai_team.cli import app

    # File named S-002-launch-plan.md but frontmatter id is S-001
    _write(
        tmp_path / "ai-team" / "specs" / "S-002-launch-plan.md",
        _spec("S-001", "Launch Plan"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--specs", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(finding["code"] == "filename-pattern" for finding in findings)


def test_validate_specs_accepts_legacy_slug_only_filename_without_id_prefix(
    monkeypatch, tmp_path
):
    """`validate --specs` reports no filename-pattern finding for legacy <slug>.md specs."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "roadmap-spec.md",
        _spec("S-001", "Roadmap Spec"),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--specs", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_resolves_task_spec_reference_by_frontmatter_id(monkeypatch, tmp_path):
    """A task spec reference matching a new-style spec's frontmatter id resolves.

    Regression for B-013: `ai-team spec new` produces `S-NNN-<slug>.md` files,
    and `ai-team task new --spec S-NNN` records the bare id verbatim. That
    combination must not raise `task-spec-missing`.
    """
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001-launch-plan.md",
        _spec("S-001", "Launch Plan"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-do-thing.md",
        _task(
            "T-001",
            "Do Thing",
            "pending",
            extra_frontmatter='spec: "S-001"\n',
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--tasks", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_resolves_task_spec_reference_by_bare_slug_of_new_style_filename(
    monkeypatch, tmp_path
):
    """A task spec reference using the legacy bare slug of an S-NNN-<slug>.md spec resolves."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001-launch-plan.md",
        _spec("S-001", "Launch Plan"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-do-thing.md",
        _task(
            "T-001",
            "Do Thing",
            "pending",
            extra_frontmatter='spec: "launch-plan"\n',
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--tasks", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_resolves_task_spec_reference_to_archived_spec(monkeypatch, tmp_path):
    """A task spec reference to a spec under specs/archive/ resolves cleanly."""
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "archive" / "S-001-launch-plan.md",
        _spec("S-001", "Launch Plan"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-do-thing.md",
        _task(
            "T-001",
            "Do Thing",
            "pending",
            extra_frontmatter='spec: "S-001"\n',
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--tasks", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_validate_still_reports_task_spec_missing_for_genuinely_missing_spec(
    monkeypatch, tmp_path
):
    """A task spec reference that resolves to no spec at all is still an error.

    Widening spec-reference resolution to accept ids and bare slugs must not
    suppress true negatives.
    """
    from ai_team.cli import app

    _write(
        tmp_path / "ai-team" / "specs" / "S-001-launch-plan.md",
        _spec("S-001", "Launch Plan"),
    )
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-do-thing.md",
        _task(
            "T-001",
            "Do Thing",
            "pending",
            extra_frontmatter='spec: "missing-spec"\n',
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--tasks", "--json"])

    assert result.exit_code != 0
    findings = json.loads(result.stdout)
    assert any(
        finding["code"] == "task-spec-missing" and "missing-spec" in finding["message"]
        for finding in findings
    )


def _validate_tasks_findings(monkeypatch, tmp_path, *, spec_value, spec_files=()):
    from ai_team.cli import app

    for name, spec_id, title in spec_files:
        _write(tmp_path / "ai-team" / "specs" / name, _spec(spec_id, title))
    extra = f'spec: "{spec_value}"\n' if spec_value else ""
    _write(
        tmp_path / ".ai-team" / "tracker" / "tasks" / "T-001-do-thing.md",
        _task("T-001", "Do Thing", "pending", extra_frontmatter=extra),
    )
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--tasks", "--json"])
    return json.loads(result.stdout)


OVERVIEW_SPEC_FILES = (("S-000-system-overview.md", "S-000", "System Overview"),)


@pytest.mark.parametrize("reference", ["S-000", "S-000-system-overview"])
def test_validate_reports_no_finding_for_task_whose_spec_is_s000(
    monkeypatch, tmp_path, reference
):
    findings = _validate_tasks_findings(
        monkeypatch,
        tmp_path,
        spec_value=reference,
        spec_files=OVERVIEW_SPEC_FILES,
    )

    assert findings == []


@pytest.mark.parametrize("alias", ["system-overview", "S-000-system-overview.md"])
def test_validate_reports_no_finding_for_task_whose_spec_reaches_s000_by_alias(
    monkeypatch, tmp_path, alias
):
    findings = _validate_tasks_findings(
        monkeypatch,
        tmp_path,
        spec_value=alias,
        spec_files=OVERVIEW_SPEC_FILES,
    )

    assert findings == []


def test_validate_bug_task_reference_ignores_the_tracker_archive(monkeypatch, tmp_path):
    from ai_team.cli import app

    tracker = tmp_path / ".ai-team" / "tracker"
    _write(
        tracker / "archive" / "2026-05" / "T-050-archived-task.md",
        _task("T-050", "Archived Task", "done"),
    )
    _write(
        tracker / "bugs" / "B-050-archived-reference.md",
        _bug(
            "B-050", "Archived Reference", "open", extra_frontmatter='task: "T-050"\n'
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    findings = json.loads(result.stdout)
    assert any(
        finding["code"] == "bug-task-missing" and "T-050" in finding["message"]
        for finding in findings
    )


def test_validate_task_change_request_reference_ignores_the_tracker_archive(
    monkeypatch, tmp_path
):
    from ai_team.cli import app

    tracker = tmp_path / ".ai-team" / "tracker"
    _write(
        tracker / "archive" / "2026-05" / "CR-050-archived-request.md",
        _change_request("CR-050", "Archived Request", "done"),
    )
    _write(
        tracker / "tasks" / "T-051-archived-reference.md",
        _task(
            "T-051",
            "Archived Reference",
            "pending",
            extra_frontmatter='spec: "CR-050"\n',
        ),
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["validate", "--json"])

    findings = json.loads(result.stdout)
    assert any(
        finding["code"] == "task-spec-missing" and "CR-050" in finding["message"]
        for finding in findings
    )
