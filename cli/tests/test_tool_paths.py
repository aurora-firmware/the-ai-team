"""Tests for the shared export path table."""

from __future__ import annotations

import importlib.resources as resources

from ai_team.core.tool_paths import EXPORT_PATHS, framework_skill_names


def test_exports_agents_and_skills_under_dot_claude() -> None:
    assert EXPORT_PATHS == (
        ("agents", ".claude/agents"),
        ("skills", ".claude/skills"),
    )


def test_framework_skill_names_match_packaged_skill_folders() -> None:
    skills_root = resources.files("ai_team.init").joinpath("scaffolds", "skills")
    packaged = sorted(entry.name for entry in skills_root.iterdir() if entry.is_dir())

    assert packaged
    assert framework_skill_names() == packaged
