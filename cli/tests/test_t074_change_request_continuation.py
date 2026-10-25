"""Tests for T-074: uninterrupted change-request continuation in source skills.

AC-1: WHEN change-request creates or updates a CR THE SYSTEM SHALL resolve each
      human-answerable `[TODO]` marker one at a time before asking for approval.
AC-2: WHEN the human approves a TODO-free CR THE SYSTEM SHALL continue to
      architecture consistency review without returning only a passive next-owner
      handoff.
AC-3: WHEN architecture consistency findings require Planner-owned spec
      amendments THE SYSTEM SHALL route them to the Planner using the approved
      CR as authoritative intent.
AC-4: IF a consistency finding would change the approved CR intent THEN THE
      SYSTEM SHALL stop and ask the human to revise, reject, or reaffirm the CR.
AC-5: The system shall preserve the Architect boundary: the Architect reports
      findings and routing, and does not edit specs directly.
"""

from __future__ import annotations

from tests.source_paths import skill_source_text


def test_change_request_resolves_human_answerable_todos_one_at_a_time() -> None:
    """AC-1: change-request body must require one-at-a-time human TODO cleanup
    before approval."""
    body = skill_source_text("change-request").lower()
    assert "human-answerable `[todo]`" in body
    assert "one at a time" in body
    assert "before asking for approval" in body or "before human approval" in body, (
        "change-request skill source must resolve each human-answerable [TODO] "
        "marker one at a time before approval"
    )


def test_change_request_continues_into_architecture_review_after_approval() -> None:
    """AC-2: change-request body must continue into architecture review instead
    of stopping at a passive handoff."""
    body = skill_source_text("change-request").lower()
    assert "continue directly into architecture consistency review" in body
    assert "passive handoff" in body, (
        "change-request skill source must explicitly forbid stopping with only a "
        "passive handoff after human approval"
    )


def test_architecture_review_uses_approved_change_request_as_authoritative_intent() -> (
    None
):
    """AC-3: architecture consistency review must route planner-owned spec work
    using the approved change-request as authoritative intent."""
    body = skill_source_text("architecture-consistency-review").lower()
    assert "approved change-request" in body
    assert "authoritative intent" in body
    assert "planner" in body, (
        "architecture-consistency-review skill source must route planner-owned "
        "consistency fixes using the approved change-request as authoritative intent"
    )


def test_architecture_review_stops_for_human_if_finding_changes_approved_intent() -> (
    None
):
    """AC-4: architecture consistency review must stop for human decision when
    a finding would change approved CR intent."""
    body = skill_source_text("architecture-consistency-review").lower()
    assert "would change the approved change-request intent" in body
    assert "human" in body
    assert "revise, reject, or reaffirm" in body, (
        "architecture-consistency-review skill source must stop for human decision "
        "when a finding would change approved CR intent"
    )


def test_architecture_review_preserves_architect_spec_edit_boundary() -> None:
    """AC-5: architecture consistency review must keep spec editing with the
    Planner rather than the Architect."""
    body = skill_source_text("architecture-consistency-review").lower()
    assert "architect never edits specs" in body, (
        "architecture-consistency-review skill source must preserve the Architect "
        "boundary and forbid direct spec edits"
    )
