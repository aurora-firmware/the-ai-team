"""Tests for T-076: spec TODO readiness in source spec-authoring skills.

AC-1: WHEN brainstorm creates a spec THE SYSTEM SHALL scan the created spec for
      `[TODO]` markers before setting or treating the spec as review-ready.
AC-2: WHEN brainstorm finds a human-answerable `[TODO]` marker THE SYSTEM SHALL
      ask the human one contextual question and update the spec with the answer
      before continuing to the next marker.
AC-3: IF human-answerable `[TODO]` markers remain in a created spec THEN THE
      SYSTEM SHALL NOT hand the spec to Architect consistency review or Gate 1
      approval.
AC-4: WHEN new-spec prepares a draft for architecture consistency review THE
      SYSTEM SHALL require human-answerable TODOs to be resolved first or
      explicitly report the blocker.
"""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text


def _skill_scaffold(skill_name: str) -> str:
    return skill_export_path(skill_name).read_text(encoding="utf-8")


def test_brainstorm_scans_created_spec_for_todos_before_review_ready() -> None:
    """AC-1: brainstorm must scan the created spec for TODO markers before review readiness."""
    body = skill_source_text("brainstorm").lower()
    assert "scan the created spec for `[todo]` markers" in body
    assert "before setting or treating the spec as review-ready" in body


def test_brainstorm_resolves_human_answerable_todos_one_question_at_a_time() -> None:
    """AC-2: brainstorm must resolve human-answerable TODOs one contextual question at a time."""
    body = skill_source_text("brainstorm")
    assert "human-answerable `[TODO]`" in body
    assert "one contextual question" in body
    assert "update the spec with the answer" in body
    assert "before continuing to the next marker" in body


def test_brainstorm_blocks_review_handoffs_while_human_todos_remain() -> None:
    """AC-3: brainstorm must block Architecture Consistency Review and Gate 1 while TODOs remain."""
    body = skill_source_text("brainstorm")
    assert "If any human-answerable `[TODO]` markers remain" in body
    assert "must not hand the spec to Architecture Consistency Review" in body
    assert "must not hand the spec to Gate 1 approval" in body
    assert "The document is ready for Gate 1 (Spec Approval)." not in body, (
        "brainstorm skill source must not claim unconditional Gate 1 readiness"
    )


def test_new_spec_requires_human_todo_resolution_before_architecture_review() -> None:
    """AC-4: new-spec must require human-answerable TODO resolution or report a blocker."""
    body = skill_source_text("new-spec")
    assert "human-answerable `[TODO]`" in body
    assert "resolved before Architecture Consistency Review" in body
    assert "explicitly report the blocker" in body


def test_todo_readiness_rules_propagate_to_scaffolds() -> None:
    """AC-1..4: scaffolded brainstorm and new-spec skills must include the TODO readiness rules."""
    brainstorm_phrases = (
        "scan the created spec for `[TODO]` markers",
        "one contextual question",
        "must not hand the spec to Architecture Consistency Review",
        "must not hand the spec to Gate 1 approval",
    )
    new_spec_phrases = (
        "human-answerable `[TODO]`",
        "resolved before Architecture Consistency Review",
        "explicitly report the blocker",
    )

    brainstorm_lower = _skill_scaffold("brainstorm").lower()
    new_spec_scaffold = _skill_scaffold("new-spec")

    for phrase in brainstorm_phrases:
        assert phrase.lower() in brainstorm_lower, (
            f"brainstorm scaffold must include: {phrase!r}"
        )

    for phrase in new_spec_phrases:
        assert phrase in new_spec_scaffold, (
            f"new-spec scaffold must include: {phrase!r}"
        )
