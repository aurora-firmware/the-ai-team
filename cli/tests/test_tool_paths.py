"""Tests for the shared export path table."""

from __future__ import annotations

from ai_team.core.tool_paths import EXPORT_PATHS


def test_exports_agents_and_skills_under_dot_claude() -> None:
    assert EXPORT_PATHS == (
        ("agents", ".claude/agents"),
        ("skills", ".claude/skills"),
    )
