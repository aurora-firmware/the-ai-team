"""Per-tool export paths shared by `init` and layout validation."""

from __future__ import annotations

import importlib.resources as resources

# Each pair maps a scaffold subfolder to its repo-relative destination.
TOOL_EXPORT_PATHS: dict[str, tuple[tuple[str, str], ...]] = {
    "claude": (
        ("agents", ".claude/agents"),
        ("skills", ".claude/skills"),
    ),
}


def framework_skill_names(tool: str) -> list[str]:
    """Return the sorted skill folder names packaged for a tool."""

    skills_root = (
        resources.files("ai_team.init")
        .joinpath("scaffolds")
        .joinpath(tool)
        .joinpath("skills")
    )
    return sorted(entry.name for entry in skills_root.iterdir() if entry.is_dir())
