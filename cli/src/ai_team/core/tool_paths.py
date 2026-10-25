"""Export paths shared by `init` and layout validation."""

from __future__ import annotations

# Each pair maps a scaffold subfolder to its repo-relative destination.
EXPORT_PATHS: tuple[tuple[str, str], ...] = (
    ("agents", ".claude/agents"),
    ("skills", ".claude/skills"),
)
