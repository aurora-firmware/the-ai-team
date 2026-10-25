"""Export paths shared by `init` and layout validation."""

from __future__ import annotations

import importlib.resources as resources

# Each pair maps a scaffold subfolder to its repo-relative destination.
EXPORT_PATHS: tuple[tuple[str, str], ...] = (
    ("agents", ".claude/agents"),
    ("skills", ".claude/skills"),
)


def framework_skill_names() -> list[str]:
    """Return the sorted skill folder names packaged with the framework."""

    skills_root = resources.files("ai_team.init").joinpath("scaffolds", "skills")
    return sorted(entry.name for entry in skills_root.iterdir() if entry.is_dir())
