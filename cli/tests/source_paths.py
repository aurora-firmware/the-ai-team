"""Locations of skill and agent sources and exports, for tests.

Tests read skill and agent files only through these helpers, so a change to the
source or export layout is made here and nowhere else.
"""

from __future__ import annotations

import re
from pathlib import Path

_INIT_ROOT = Path(__file__).resolve().parents[1] / "src" / "ai_team" / "init"
_SCAFFOLDS = _INIT_ROOT / "scaffolds"

SKILL_SOURCES = _INIT_ROOT / "sources" / "skills"


def skill_source_text(name: str) -> str:
    return (SKILL_SOURCES / name / "SKILL.md").read_text(encoding="utf-8")


def skill_frontmatter(name: str) -> str:
    """Return the leading `---` ... `---` block of a skill's SKILL.md."""
    match = re.match(r"---\n.*?\n---(?=\n)", skill_source_text(name), re.DOTALL)
    if match is None:
        raise ValueError(f"{name} SKILL.md has no leading frontmatter block")
    return match.group(0)


def skill_export_path(name: str) -> Path:
    return _SCAFFOLDS / "skills" / name / "SKILL.md"


def agent_source_path(role: str) -> Path:
    return _INIT_ROOT / "sources" / "agents" / f"{role}.md"


def agent_export_path(role: str) -> Path:
    return _SCAFFOLDS / "agents" / f"{role}.md"
