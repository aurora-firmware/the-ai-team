"""Tests for T-064: Consolidate canonical git-conventions and escalation-review skill bodies.

AC-1: git-conventions body exposes stable ## headings for branch model, commit format,
      per-role commits, and hard rules that other skills can cite.
AC-2: escalation-review body contains the frozen four-field request block, an Escalation
      Verdict block, and the canonical Phase 2 Human Escalation Report template as the
      single source; also preserves B-008's description (not context) for new-adr.
AC-3: new-spec body holds the canonical content-boundary rule; brainstorm references it
      rather than restating it (one-line pointer, not full inline rule).
"""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text


def _skill_scaffold(skill_name: str) -> str:
    return skill_export_path(skill_name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-1: git-conventions exposes stable citable headings
# ---------------------------------------------------------------------------


def test_git_conventions_has_branch_model_heading() -> None:
    """AC-1: git-conventions body must contain a stable ## Branch Model heading."""
    body = skill_source_text("git-conventions")
    assert "## Branch Model" in body, (
        "git-conventions skill source must contain '## Branch Model' heading"
    )


def test_git_conventions_has_commit_message_format_heading() -> None:
    """AC-1: git-conventions body must contain a stable ## Commit Message Format heading."""
    body = skill_source_text("git-conventions")
    assert "## Commit Message Format" in body, (
        "git-conventions skill source must contain '## Commit Message Format' heading"
    )


def test_git_conventions_has_per_role_commits_heading() -> None:
    """AC-1: git-conventions body must contain a stable heading for per-role commits."""
    body = skill_source_text("git-conventions")
    assert "## When Each Role Commits" in body, (
        "git-conventions skill source must contain '## When Each Role Commits' heading"
    )


def test_git_conventions_has_hard_rules_heading() -> None:
    """AC-1: git-conventions body must contain a stable ## Hard Rules heading."""
    body = skill_source_text("git-conventions")
    assert "## Hard Rules" in body, (
        "git-conventions skill source must contain '## Hard Rules' heading"
    )


def test_git_conventions_headings_appear_in_scaffolds() -> None:
    """AC-1: the scaffold must expose the four citable headings."""
    required_headings = (
        "## Branch Model",
        "## Commit Message Format",
        "## When Each Role Commits",
        "## Hard Rules",
    )
    scaffold = _skill_scaffold("git-conventions")
    for heading in required_headings:
        assert heading in scaffold, f"git-conventions scaffold must contain {heading!r}"


def test_git_conventions_does_not_restate_hard_rules_in_quality_criteria() -> None:
    """AC-1: git-conventions body must not contain a Quality Criteria section that
    merely duplicates the Hard Rules — the Hard Rules section is the canonical authority."""
    body = skill_source_text("git-conventions")
    assert "## Quality Criteria" not in body, (
        "git-conventions skill source must not have a '## Quality Criteria' section "
        "(it restates Hard Rules; remove it to keep Hard Rules as sole authority)"
    )


# ---------------------------------------------------------------------------
# AC-2: escalation-review has frozen four-field block, verdict, and Phase 2 template
# ---------------------------------------------------------------------------


def test_escalation_review_has_frozen_escalation_request_block() -> None:
    """AC-2: escalation-review body must contain a frozen four-field escalation request block."""
    body = skill_source_text("escalation-review")
    assert "FROZEN" in body, (
        "escalation-review skill source must contain a FROZEN escalation request block"
    )


def test_escalation_review_frozen_block_has_all_four_fields() -> None:
    """AC-2: the frozen block must name all four fields: Problem, Attempted,
    Failed because, Question."""
    body = skill_source_text("escalation-review")
    for field in ("Problem", "Attempted", "Failed because", "Question"):
        assert field in body, (
            f"escalation-review skill source frozen block must include field: {field!r}"
        )


def test_escalation_review_has_escalation_verdict_block() -> None:
    """AC-2: escalation-review body must contain an Escalation Verdict block."""
    body = skill_source_text("escalation-review")
    assert "`Result: ESCALATE`" in body, (
        "escalation-review skill source must map its verdict to the envelope's `Result:` line"
    )


def test_escalation_review_has_phase_2_human_escalation_report_template() -> None:
    """AC-2: escalation-review body must contain the canonical Phase 2 Human
    Escalation Report template."""
    body = skill_source_text("escalation-review")
    assert "Phase 2" in body, (
        "escalation-review skill source must contain the Phase 2 Human Escalation Report template"
    )
    assert "Human Escalation Report" in body, (
        "escalation-review skill source must contain 'Human Escalation Report' template"
    )


def test_escalation_review_phase_2_template_is_single_source() -> None:
    """AC-2: escalation-review must declare itself as the single canonical source
    for the Phase 2 Human Escalation Report template."""
    body = skill_source_text("escalation-review")
    # The body should declare this template is used by all callers
    assert "single canonical" in body.lower() or "all callers" in body.lower(), (
        "escalation-review skill source must declare itself as the single canonical source "
        "for the Phase 2 Human Escalation Report template"
    )


def test_escalation_review_new_adr_invocation_uses_description_not_context() -> None:
    """AC-2: escalation-review body must pass 'description' (not 'context') when
    invoking new-adr — preserving B-008's fix for the new-adr caller contract."""
    body = skill_source_text("escalation-review")
    # Must use description:, not context:
    assert "- `description`:" in body or "`description`" in body, (
        "escalation-review skill source must pass 'description' to new-adr (B-008 fix)"
    )
    # Must NOT use the old 'context' field name in the new-adr invocation block
    # Check that 'context:' isn't used as a new-adr parameter
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if "new-adr" in line.lower() or "`context`" in line:
            # Look for context: being used as a field name in a bullet after new-adr
            if line.strip().startswith("- `context`"):
                assert False, (
                    f"escalation-review skill source line {i + 1} still uses '`context`' for "
                    "new-adr — must use '`description`' (B-008 fix)"
                )


def test_escalation_review_scaffolds_have_frozen_block_and_verdict() -> None:
    """AC-2: the scaffold must contain the FROZEN block and Escalation Verdict."""
    scaffold = _skill_scaffold("escalation-review")
    assert "FROZEN" in scaffold, "escalation-review scaffold must contain FROZEN block"
    assert "`Result: ESCALATE`" in scaffold, (
        "escalation-review scaffold must contain '`Result: ESCALATE`'"
    )
    assert "Phase 2" in scaffold, (
        "escalation-review scaffold must contain 'Phase 2' template"
    )


# ---------------------------------------------------------------------------
# AC-3: new-spec holds content-boundary rule; brainstorm references it
# ---------------------------------------------------------------------------


def test_new_spec_has_content_boundary_rule_section() -> None:
    """AC-3: new-spec body must contain the canonical content-boundary rule section."""
    body = skill_source_text("new-spec")
    assert "content-boundary" in body.lower() or "content boundary" in body.lower(), (
        "new-spec skill source must contain the canonical content-boundary rule"
    )


def test_new_spec_content_boundary_rule_covers_no_implementation_code() -> None:
    """AC-3: new-spec content-boundary rule must state that specs do not embed
    implementation code."""
    body = skill_source_text("new-spec")
    assert "implementation" in body.lower(), (
        "new-spec skill source content-boundary rule must address implementation code"
    )


def test_brainstorm_references_new_spec_for_content_boundary() -> None:
    """AC-3: brainstorm body must reference new-spec for the content-boundary rule
    rather than restating it inline."""
    body = skill_source_text("brainstorm")
    assert "new-spec" in body, (
        "brainstorm skill source must reference new-spec for the content-boundary rule"
    )


def test_brainstorm_does_not_fully_restate_content_boundary_rule() -> None:
    """AC-3: brainstorm body must not reproduce the full content-boundary rule text.
    It should carry only a one-line pointer to new-spec, not the complete rule."""
    body = skill_source_text("brainstorm")
    # The full rule spans multiple paragraphs and includes the 'Rare exception' clause.
    # A pointer version would not have the complete rule with the 'Rare exception' detail.
    # We check that the full canonical text is not duplicated here.
    assert "Rare exception" not in body, (
        "brainstorm skill source must not restate the full content-boundary rule "
        "(it contains 'Rare exception' which belongs only in new-spec)"
    )


def test_brainstorm_content_boundary_reference_is_concise() -> None:
    """AC-3: brainstorm body's reference to content-boundary must be a pointer,
    not a full restatement — the content-boundary rule should appear only in new-spec."""
    body = skill_source_text("brainstorm")
    # The full rule in new-spec has very specific text about config files and manifests.
    # A pointer would just say something like "applies through new-spec" or similar.
    full_rule_markers = (
        "Full configuration files",
        "full configuration files",
        "File-by-file plans",
    )
    for marker in full_rule_markers:
        assert marker not in body, (
            f"brainstorm skill source must not duplicate the content-boundary rule detail: {marker!r}"
        )


def test_new_spec_and_brainstorm_scaffolds_reflect_canonical_ownership() -> None:
    """AC-3: the new-spec scaffold must contain the content-boundary rule;
    the brainstorm scaffold must not duplicate it."""
    new_spec_scaffold = _skill_scaffold("new-spec")
    brainstorm_scaffold = _skill_scaffold("brainstorm")

    assert "content-boundary" in new_spec_scaffold.lower() or (
        "content boundary" in new_spec_scaffold.lower()
    ), "new-spec scaffold must contain the content-boundary rule"

    # brainstorm scaffold must reference new-spec but not have full boundary rule
    assert "new-spec" in brainstorm_scaffold, (
        "brainstorm scaffold must reference new-spec"
    )
    assert "Rare exception" not in brainstorm_scaffold, (
        "brainstorm scaffold must not duplicate the full content-boundary rule"
    )
