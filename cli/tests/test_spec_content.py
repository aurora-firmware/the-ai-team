"""Behavioral specification contracts exercised through the public CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_team.cli import app
from ai_team.core.models import parse_spec
from tests.spec_fixtures import EXPORT_REQUIREMENT, SPEC_SECTIONS, feature_spec_body


def _write_spec(
    root: Path,
    body: str,
    *,
    status: str = "approved",
    spec_id: str = "S-001",
) -> Path:
    path = root / "ai-team/specs" / f"{spec_id}-export.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {spec_id}\ntitle: Export\nversion: '0.1'\nstatus: {status}\n"
        f"created: 2026-10-25\nauthor: planner\n---\n\n{body}\n"
    )
    return path


def _validate(monkeypatch, root: Path) -> tuple[int, list[dict[str, str]]]:
    monkeypatch.chdir(root)
    result = CliRunner().invoke(app, ["validate", "--specs", "--json"])
    assert result.exception is None or isinstance(result.exception, SystemExit), (
        result.output
    )
    return result.exit_code, json.loads(result.stdout)


def test_cli_generates_feature_spec_and_system_overview(monkeypatch, tmp_path):
    (tmp_path / "ai-team/specs").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    feature = runner.invoke(app, ["spec", "new", "Export", "--json"])
    overview = runner.invoke(app, ["spec", "new", "--overview", "--json"])
    assert feature.exit_code == overview.exit_code == 0
    content = Path(json.loads(feature.stdout)["path"]).read_text()
    assert set(parse_spec(Path(json.loads(feature.stdout)["path"]))._source_map) == {
        "id",
        "title",
        "version",
        "status",
        "created",
        "author",
    }
    for section in SPEC_SECTIONS:
        assert f"\n## {section}\n" in content
    assert "### REQ-001" in content
    assert "#### AC-001.1" in content
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize("status", ["review", "approved"])
def test_complete_behavior_contract_is_valid(monkeypatch, tmp_path, status):
    _write_spec(tmp_path, feature_spec_body(), status=status)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize(
    ("old", "new", "code"),
    [
        ("## Users and Journeys", "## Other", "spec-section-missing"),
        ("Prevent disclosure of workspace records.", "", "spec-section-empty"),
        ("### REQ-001", "### REQ-01", "spec-requirement-heading"),
        (EXPORT_REQUIREMENT, "None.", "spec-requirements-missing"),
        (
            EXPORT_REQUIREMENT,
            EXPORT_REQUIREMENT + "\n" + EXPORT_REQUIREMENT,
            "spec-requirement-duplicate",
        ),
        ("#### AC-001.1", "#### AC-002.1", "spec-acceptance-owner"),
        ("#### AC-001.1", "#### AC-001.0", "spec-acceptance-heading"),
        (
            EXPORT_REQUIREMENT,
            EXPORT_REQUIREMENT.split("####")[0],
            "spec-acceptance-missing",
        ),
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
    path = _write_spec(tmp_path, feature_spec_body().replace(old, new))
    before = path.read_bytes()
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert code in {finding["code"] for finding in findings}
    assert all(
        finding["path"] == "ai-team/specs/S-001-export.md" for finding in findings
    )
    assert path.read_bytes() == before


def test_quality_requirements_share_ids_and_acceptance_rules(monkeypatch, tmp_path):
    quality = EXPORT_REQUIREMENT.replace("REQ-001", "REQ-002").replace(
        "AC-001", "AC-002"
    )
    body = feature_spec_body().replace(
        "## Quality Requirements\n\nNone — not applicable to this feature.",
        f"## Quality Requirements\n\n{quality}",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_acceptance_ids_cannot_be_reused(monkeypatch, tmp_path):
    scenario = EXPORT_REQUIREMENT[EXPORT_REQUIREMENT.index("####") :]
    _write_spec(
        tmp_path,
        feature_spec_body().replace(EXPORT_REQUIREMENT, EXPORT_REQUIREMENT + scenario),
    )
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
    _write_spec(tmp_path, feature_spec_body() + example)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_comment_only_acceptance_is_not_evidence(monkeypatch, tmp_path):
    _write_spec(
        tmp_path,
        feature_spec_body().replace(
            EXPORT_REQUIREMENT, f"<!-- {EXPORT_REQUIREMENT} -->"
        ),
    )
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-requirements-missing" in {f["code"] for f in findings}


@pytest.mark.parametrize("status", ["draft", "superseded"])
def test_feature_content_is_checked_when_ready_for_review(
    monkeypatch, tmp_path, status
):
    _write_spec(tmp_path, "Unfinished. [TODO]", status=status)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_system_overview_uses_its_own_contract(monkeypatch, tmp_path):
    _write_spec(tmp_path, "System overview content.", spec_id="S-000")
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize("status", ["review", "approved"])
def test_feature_spec_must_include_requirements_and_acceptance(
    monkeypatch, tmp_path, status
):
    path = _write_spec(tmp_path, "Incomplete content. [TODO]", status=status)
    before = path.read_bytes()
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert {"spec-section-missing", "spec-placeholder"} <= {f["code"] for f in findings}
    assert path.read_bytes() == before


def test_inline_verification_command_is_valid(monkeypatch, tmp_path):
    body = feature_spec_body().replace(
        "an authorization acceptance test for AC-001.1.",
        "`run-authorization-check AC-001.1`",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize("spec_id", ["S-001", "S-000"])
def test_invalid_status_is_reported_once_for_every_spec(monkeypatch, tmp_path, spec_id):
    _write_spec(tmp_path, feature_spec_body(), status="ready", spec_id=spec_id)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert [f["code"] for f in findings] == ["status-invalid"]


def test_duplicate_sections_are_rejected(monkeypatch, tmp_path):
    _write_spec(tmp_path, feature_spec_body() + "\n## Purpose\n\nOther intent.\n")
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-section-duplicate" in {f["code"] for f in findings}


def test_subsection_heading_alone_does_not_fill_a_required_section(
    monkeypatch, tmp_path
):
    body = feature_spec_body().replace(
        "## Interfaces\n\nNone — not applicable to this feature.",
        "## Interfaces\n\n### Exposed contracts",
    )
    _write_spec(tmp_path, body)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert any(
        f["code"] == "spec-section-empty" and "Interfaces" in f["message"]
        for f in findings
    )


@pytest.mark.parametrize("disposition", ["It should be fast.", "None", "None."])
def test_quality_disposition_must_use_requirements_or_explicit_non_applicability(
    monkeypatch, tmp_path, disposition
):
    body = feature_spec_body().replace(
        "## Quality Requirements\n\nNone — not applicable to this feature.",
        f"## Quality Requirements\n\n{disposition}",
    )
    _write_spec(tmp_path, body)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-quality-disposition" in {f["code"] for f in findings}


@pytest.mark.parametrize("term", ["todo", "Todo", "TODO"])
def test_todo_domain_language_is_not_an_unresolved_placeholder(
    monkeypatch, tmp_path, term
):
    body = feature_spec_body().replace(
        "Prevent disclosure of workspace records.",
        f"Users manage {term} lists and mark {term} items complete.",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize(
    "marker",
    [
        "[TODO]",
        "[TODO: define behavior]",
        "[TBD]",
        "[TBR]",
        "[NEEDS CLARIFICATION: limits]",
        "TODO: define behavior",
        "TBD",
        "TBR",
        "TODO",
        "- TODO: define behavior",
        "  TODO: define behavior",
        "1. TBD",
        "- [ ] TODO: define behavior",
        "- Export formats\n    - [TODO] agree on formats",
        "- Export formats\n\n    [TODO] agree on formats",
        "- Export formats\n\t- TBD",
    ],
)
def test_explicit_unresolved_markers_still_block_review(monkeypatch, tmp_path, marker):
    _write_spec(
        tmp_path,
        feature_spec_body().replace("Prevent disclosure of workspace records.", marker),
    )
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-placeholder" in {f["code"] for f in findings}


@pytest.mark.parametrize(
    "section", ["Behavioral Requirements", "Quality Requirements", "Workflow"]
)
def test_acceptance_scenarios_without_a_requirement_owner_are_rejected(
    monkeypatch, tmp_path, section
):
    orphan = EXPORT_REQUIREMENT[EXPORT_REQUIREMENT.index("####") :].replace(
        "AC-001", "AC-999"
    )
    body = feature_spec_body().replace(f"## {section}\n", f"## {section}\n\n{orphan}\n")
    _write_spec(tmp_path, body)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-acceptance-orphan" in {f["code"] for f in findings}


def test_orphan_acceptance_ids_are_included_in_duplicate_checks(monkeypatch, tmp_path):
    orphan = EXPORT_REQUIREMENT[EXPORT_REQUIREMENT.index("####") :]
    body = feature_spec_body().replace(
        "## Behavioral Requirements\n", f"## Behavioral Requirements\n\n{orphan}\n"
    )
    _write_spec(tmp_path, body)
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-acceptance-duplicate" in {f["code"] for f in findings}


def test_acceptance_in_the_document_preamble_is_not_skipped(monkeypatch, tmp_path):
    orphan = EXPORT_REQUIREMENT[EXPORT_REQUIREMENT.index("####") :]
    _write_spec(tmp_path, orphan + "\n" + feature_spec_body())
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    codes = {f["code"] for f in findings}
    assert {"spec-acceptance-orphan", "spec-acceptance-duplicate"} <= codes


def test_indented_code_block_is_not_prose(monkeypatch, tmp_path):
    body = feature_spec_body().replace(
        "Prevent disclosure of workspace records.",
        "Prevent disclosure of workspace records.\n\n    ### REQ-009 — Literal\n    [TODO]",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("REQ-001 — Deny unauthorized exports", "REQ-001 — Requirement title"),
        ("AC-001.1 — Access denied", "AC-001.1 — Scenario title"),
    ],
)
def test_template_heading_titles_are_placeholders(monkeypatch, tmp_path, old, new):
    _write_spec(tmp_path, feature_spec_body().replace(old, new))
    exit_code, findings = _validate(monkeypatch, tmp_path)
    assert exit_code == 1
    assert "spec-placeholder" in {f["code"] for f in findings}


def test_quoted_comment_opener_does_not_hide_content(monkeypatch, tmp_path):
    body = (
        feature_spec_body().replace(
            "Prevent disclosure of workspace records.",
            "Prevent disclosure of workspace records. Markers like `<!--` open comments.",
        )
        + "\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_comment_still_hides_placeholders_and_fences(monkeypatch, tmp_path):
    body = feature_spec_body().replace(
        "Prevent disclosure of workspace records.",
        "Prevent disclosure of workspace records. <!-- [TODO]\n```\n### REQ-009 — Hidden\n-->",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


@pytest.mark.parametrize("marker", ["- ", "* ", "1. "])
def test_verification_may_be_a_list_item(monkeypatch, tmp_path, marker):
    body = feature_spec_body().replace(
        "**Verification:**", f"{marker}**Verification:**"
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])


def test_comment_opener_in_indented_code_does_not_hide_content(monkeypatch, tmp_path):
    body = feature_spec_body().replace(
        "Prevent disclosure of workspace records.",
        "Prevent disclosure of workspace records.\n\n    <!-- html sample",
    )
    _write_spec(tmp_path, body)
    assert _validate(monkeypatch, tmp_path) == (0, [])
