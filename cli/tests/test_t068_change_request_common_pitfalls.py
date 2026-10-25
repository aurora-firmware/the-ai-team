"""Tests for T-068: Add a Common Pitfalls section to the change-request skill body.

AC-1: The change-request skill body SHALL include a Common Pitfalls section,
      consistent in shape with the new-spec and new-task skills.
AC-2: The Common Pitfalls section SHALL cover the common misuses — using a
      change-request when a full spec is warranted, vague change descriptions,
      missing affected-artifact or risk notes, and inventing details instead of
      marking [TODO].
"""

from __future__ import annotations

from tests.source_paths import skill_source_text


def _common_pitfalls_section(body: str) -> str:
    """Extract the text of the ## Common Pitfalls section from the body."""
    start = body.find("## Common Pitfalls")
    if start == -1:
        return ""
    # Find the next ## heading after Common Pitfalls, or end of file
    next_heading = body.find("\n## ", start + 1)
    if next_heading == -1:
        return body[start:]
    return body[start:next_heading]


# ---------------------------------------------------------------------------
# AC-1: change-request body contains a ## Common Pitfalls section
# ---------------------------------------------------------------------------


def test_change_request_has_common_pitfalls_heading() -> None:
    """AC-1: change-request skill source must contain a '## Common Pitfalls' heading."""
    body = skill_source_text("change-request")
    assert "## Common Pitfalls" in body, (
        "change-request skill source must contain '## Common Pitfalls' heading, "
        "consistent with new-spec and new-task skills"
    )


# ---------------------------------------------------------------------------
# AC-2: the Common Pitfalls section covers the four required misuses
# ---------------------------------------------------------------------------


def test_change_request_pitfalls_covers_spec_warranted_misuse() -> None:
    """AC-2: the Common Pitfalls section must cover using a change-request when
    a full spec is warranted instead."""
    body = skill_source_text("change-request")
    section = _common_pitfalls_section(body)
    assert section, "Common Pitfalls section must exist before checking its content"
    section_lower = section.lower()
    assert "spec" in section_lower, (
        "change-request skill source Common Pitfalls must address the misuse of raising "
        "a change-request when a full spec is warranted"
    )


def test_change_request_pitfalls_covers_vague_description() -> None:
    """AC-2: the Common Pitfalls section must cover vague change descriptions."""
    body = skill_source_text("change-request")
    section = _common_pitfalls_section(body)
    assert section, "Common Pitfalls section must exist before checking its content"
    section_lower = section.lower()
    assert "vague" in section_lower, (
        "change-request skill source Common Pitfalls must address vague change descriptions"
    )


def test_change_request_pitfalls_covers_missing_affected_artifacts_or_risk() -> None:
    """AC-2: the Common Pitfalls section must cover missing affected-artifact or
    risk notes."""
    body = skill_source_text("change-request")
    section = _common_pitfalls_section(body)
    assert section, "Common Pitfalls section must exist before checking its content"
    section_lower = section.lower()
    has_artifacts = "artifact" in section_lower or "affected" in section_lower
    has_risk = "risk" in section_lower
    assert has_artifacts and has_risk, (
        "change-request skill source Common Pitfalls must address missing affected-artifact "
        "notes and missing risk notes"
    )


def test_change_request_pitfalls_covers_inventing_details_instead_of_todo() -> None:
    """AC-2: the Common Pitfalls section must cover inventing details instead of
    marking [TODO]."""
    body = skill_source_text("change-request")
    section = _common_pitfalls_section(body)
    assert section, "Common Pitfalls section must exist before checking its content"
    assert "[TODO]" in section or "TODO" in section, (
        "change-request skill source Common Pitfalls must address inventing details "
        "instead of marking [TODO]"
    )
