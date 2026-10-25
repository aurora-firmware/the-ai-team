"""T-090: S-000 checks in the consistency review skill and quality gates."""

from __future__ import annotations

from pathlib import Path

from tests.source_paths import skill_source_text

REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATES_PATH = REPO_ROOT / "ai-process" / "processes" / "quality-gates.md"


def _skill_body() -> str:
    return skill_source_text("architecture-consistency-review")


def _quality_gates() -> str:
    return QUALITY_GATES_PATH.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    next_heading = text.find("\n## ", start + len(heading))
    return text[start:] if next_heading == -1 else text[start:next_heading]


def test_skill_checks_spec_against_s000_purpose_and_component_boundaries() -> None:
    body = _skill_body()
    assert "approved S-000" in body
    assert "purpose" in body
    assert "boundary" in body
    assert "responsibility" in body


def test_skill_names_amendment_or_cut_back_when_spec_exceeds_s000() -> None:
    body = _skill_body()
    assert "S-000 amendment" in body
    assert "cut back to scope" in body
    assert "naming which" in body


def test_skill_reviews_s000_for_internal_consistency_and_plain_language() -> None:
    body = _skill_body()
    assert "internal consistency" in body
    assert "plain-language" in body


def test_completion_mode_keeps_s000_out_with_the_bootstrap_reason() -> None:
    section = _section(_skill_body(), "## Completion Mode")
    assert "S-000 is never a touched spec" in section
    assert "bootstrap tasks answer questions S-000 only asks" in section
    assert "S-000 makes no assertion for that work to drift from" in section
    assert "no tasks or Work Logs" not in section


def test_changed_s000_is_checked_for_groups_decisions_needed_and_component_checks() -> (
    None
):
    body = _skill_body()
    section = body[body.index("### Step 3b") : body.index("### Step 4")]
    assert "Solution" in section
    assert "Development infrastructure" in section
    assert "Decisions needed" in section
    assert "three component checks" in section


def test_gate_1_lists_s000_pass_criteria() -> None:
    gate_1 = _section(_quality_gates(), "## Gate 1: Specification Approval").lower()
    for criterion in (
        "plain language",
        "no technology or interfaces",
        "every use case is tied to a pain point",
        "every component has a boundary and a responsibility",
        "no unresolved `[todo]`",
    ):
        assert criterion in gate_1


def test_gate_1_says_s000_criteria_replace_task_derivation_criterion() -> None:
    gate_1 = _section(_quality_gates(), "## Gate 1: Specification Approval")
    assert "replace the criterion that the architecture is detailed enough" in gate_1


def test_completion_review_text_excludes_s000() -> None:
    text = _quality_gates()
    review = _section(text, "## Architecture Consistency Review")
    gate_5 = _section(text, "## Gate 5: Final Merge Sign-off")
    assert "does not include S-000" in review
    assert "does not include S-000" in gate_5
