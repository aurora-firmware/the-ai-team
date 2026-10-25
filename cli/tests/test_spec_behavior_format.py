"""Behavioral specification contracts exercised through the public CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.cli import app

SECTIONS = (
    "Purpose",
    "Users and Journeys",
    "Exclusions",
    "Architecture",
    "Interfaces",
    "Workflow",
    "Behavioral Requirements",
    "Quality Requirements",
    "Configuration Requirements",
    "Assumptions and Dependencies",
    "Success Criteria",
    "Implementation Order",
    "Open Questions",
    "Amendment Log",
)

REQUIREMENT = """### REQ-001 — Deny unauthorized exports

The system SHALL reject exports requested by an actor without workspace access.

#### AC-001.1 — Access denied

- **Given:** an actor without access to workspace A
- **When:** the actor requests an export from workspace A
- **Then:** the request is rejected without returning workspace records

**Verification:** an authorization acceptance test for AC-001.1.
"""


def _body() -> str:
    values = dict.fromkeys(SECTIONS, "None — not applicable to this feature.")
    values["Purpose"] = "Prevent disclosure of workspace records."
    values["Users and Journeys"] = "Workspace users request exports (REQ-001)."
    values["Behavioral Requirements"] = REQUIREMENT
    values["Amendment Log"] = ""
    return "\n\n".join(f"## {name}\n\n{value}" for name, value in values.items())


def _write_spec(
    root: Path,
    body: str,
    *,
    status: str = "approved",
    spec_format: str | None = "behavior-v1",
    spec_id: str = "S-001",
) -> Path:
    path = root / "ai-team/specs" / f"{spec_id}-export.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = "" if spec_format is None else f"spec-format: {spec_format}\n"
    path.write_text(
        f"---\nid: {spec_id}\ntitle: Export\nversion: '0.1'\nstatus: {status}\n"
        f"created: 2026-10-25\nauthor: planner\n{marker}---\n\n{body}\n"
    )
    return path


def _validate(monkeypatch, root: Path) -> tuple[int, list[dict[str, str]]]:
    monkeypatch.chdir(root)
    result = CliRunner().invoke(app, ["validate", "--specs", "--json"])
    assert result.exception is None or isinstance(result.exception, SystemExit), (
        result.output
    )
    return result.exit_code, json.loads(result.stdout)


def test_cli_generates_versioned_feature_contract_and_keeps_overview_separate(
    monkeypatch, tmp_path
):
    (tmp_path / "ai-team/specs").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    feature = runner.invoke(app, ["spec", "new", "Export", "--json"])
    overview = runner.invoke(app, ["spec", "new", "--overview", "--json"])
    assert feature.exit_code == overview.exit_code == 0
    content = Path(json.loads(feature.stdout)["path"]).read_text()
    assert "spec-format: behavior-v1" in content
    for section in SECTIONS:
        assert f"\n## {section}\n" in content
    assert "### REQ-001" in content
    assert "#### AC-001.1" in content
    assert "spec-format:" not in Path(json.loads(overview.stdout)["path"]).read_text()
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize("status", ["review", "approved"])
def test_complete_behavior_contract_is_valid(monkeypatch, tmp_path, status):
    _write_spec(tmp_path, _body(), status=status)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize(
    ("old", "new", "code"),
    [
        ("## Users and Journeys", "## Other", "spec-section-missing"),
        ("Prevent disclosure of workspace records.", "", "spec-section-empty"),
        ("### REQ-001", "### REQ-01", "spec-requirement-heading"),
        (REQUIREMENT, "None.", "spec-requirements-missing"),
        (REQUIREMENT, REQUIREMENT + "\n" + REQUIREMENT, "spec-requirement-duplicate"),
        ("#### AC-001.1", "#### AC-002.1", "spec-acceptance-owner"),
        ("#### AC-001.1", "#### AC-001.0", "spec-acceptance-heading"),
        (REQUIREMENT, REQUIREMENT.split("####")[0], "spec-acceptance-missing"),
        (
            "The system SHALL reject exports requested by an actor without workspace access.",
            "",
            "spec-requirement-statement",
        ),
        (
            "**Verification:** an authorization acceptance test for AC-001.1.",
            "**Verification:**",
            "spec-verification-missing",
        ),
        (
            "Prevent disclosure of workspace records.",
            "[TODO] agree on behavior",
            "spec-placeholder",
        ),
    ],
)
def test_invalid_behavior_contract_reports_actionable_error(
    monkeypatch, tmp_path, old, new, code
):
    path = _write_spec(tmp_path, _body().replace(old, new))
    before = path.read_bytes()
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert code in {finding["code"] for finding in findings}
    assert all(
        finding["path"] == "ai-team/specs/S-001-export.md" for finding in findings
    )
    assert path.read_bytes() == before


def test_quality_requirements_share_ids_and_acceptance_rules(monkeypatch, tmp_path):
    quality = REQUIREMENT.replace("REQ-001", "REQ-002").replace("AC-001", "AC-002")
    body = _body().replace(
        "## Quality Requirements\n\nNone — not applicable to this feature.",
        f"## Quality Requirements\n\n{quality}",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_acceptance_ids_cannot_be_reused(monkeypatch, tmp_path):
    scenario = REQUIREMENT[REQUIREMENT.index("####") :]
    _write_spec(tmp_path, _body().replace(REQUIREMENT, REQUIREMENT + scenario))
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-acceptance-duplicate" in {f["code"] for f in findings}


@pytest.mark.parametrize("fence", ["```", "````", "~~~"])
def test_contract_examples_and_comments_do_not_define_requirements_or_placeholders(
    monkeypatch, tmp_path, fence
):
    example = (
        f"\n{fence}markdown\n### REQ-001 — Literal external content\n"
        f"[TODO]\n{fence}\n<!-- ### REQ-001\n[TODO] -->\n"
        "The external tool uses the literal token `[TODO]`.\n"
    )
    _write_spec(tmp_path, _body() + example)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_comment_only_acceptance_is_not_evidence(monkeypatch, tmp_path):
    _write_spec(tmp_path, _body().replace(REQUIREMENT, f"<!-- {REQUIREMENT} -->"))
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-requirements-missing" in {f["code"] for f in findings}


@pytest.mark.parametrize(
    ("status", "spec_format", "spec_id"),
    [
        ("draft", "behavior-v1", "S-001"),
        ("approved", None, "S-001"),
        ("approved", None, "S-000"),
    ],
)
def test_drafts_legacy_specs_and_overviews_do_not_require_new_content(
    monkeypatch, tmp_path, status, spec_format, spec_id
):
    _write_spec(
        tmp_path,
        "Existing content. [TODO]",
        status=status,
        spec_format=spec_format,
        spec_id=spec_id,
    )
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_unknown_format_is_not_silently_accepted(monkeypatch, tmp_path):
    _write_spec(tmp_path, _body(), status="draft", spec_format="behavior-v99")
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-format-unsupported" in {f["code"] for f in findings}


def test_inline_verification_command_is_valid(monkeypatch, tmp_path):
    body = _body().replace(
        "an authorization acceptance test for AC-001.1.",
        "`run-authorization-check AC-001.1`",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize("marker", ["null", "false", "''"])
def test_explicit_invalid_format_is_not_treated_as_a_legacy_spec(
    monkeypatch, tmp_path, marker
):
    _write_spec(tmp_path, _body(), spec_format=marker)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-format-unsupported" in {f["code"] for f in findings}


def test_invalid_status_cannot_skip_feature_content_validation(monkeypatch, tmp_path):
    _write_spec(tmp_path, _body(), status="ready")
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-status-invalid" in {f["code"] for f in findings}


def test_duplicate_sections_are_rejected(monkeypatch, tmp_path):
    _write_spec(tmp_path, _body() + "\n## Purpose\n\nOther intent.\n")
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-section-duplicate" in {f["code"] for f in findings}


def test_subsection_heading_alone_does_not_fill_a_required_section(
    monkeypatch, tmp_path
):
    body = _body().replace(
        "## Architecture\n\nNone — not applicable to this feature.",
        "## Architecture\n\n### Design Principles",
    )
    _write_spec(tmp_path, body)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert any(
        f["code"] == "spec-section-empty" and "Architecture" in f["message"]
        for f in findings
    )


def test_quality_disposition_must_use_requirements_or_explicit_non_applicability(
    monkeypatch, tmp_path
):
    body = _body().replace(
        "## Quality Requirements\n\nNone — not applicable to this feature.",
        "## Quality Requirements\n\nIt should be fast.",
    )
    _write_spec(tmp_path, body)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-quality-disposition" in {f["code"] for f in findings}
