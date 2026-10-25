"""Tests for the shared per-tool export path table."""

from __future__ import annotations

import importlib.resources as resources

from ai_team.core.tool_paths import TOOL_EXPORT_PATHS, framework_skill_names


def test_claude_exports_agents_and_skills_under_dot_claude() -> None:
    assert TOOL_EXPORT_PATHS["claude"] == (
        ("agents", ".claude/agents"),
        ("skills", ".claude/skills"),
    )


def test_framework_skill_names_match_packaged_claude_skill_folders() -> None:
    skills_root = (
        resources.files("ai_team.init")
        .joinpath("scaffolds")
        .joinpath("claude", "skills")
    )
    packaged = sorted(entry.name for entry in skills_root.iterdir() if entry.is_dir())

    assert packaged
    assert framework_skill_names("claude") == packaged
