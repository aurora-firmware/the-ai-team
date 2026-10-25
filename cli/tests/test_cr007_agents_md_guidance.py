"""CR-007: skills and agents name AGENTS.md, never CLAUDE.md, as the guidance file."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.source_paths import SKILL_SOURCES, skill_source_text

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_SOURCES = SKILL_SOURCES.parent / "agents"
GUIDANCE_SKILLS = ["using-ai-team", "integrate", "git-conventions", "dev-loop", "tdd"]


def test_no_skill_or_agent_source_mentions_claude_md() -> None:
    offenders = [
        str(path)
        for root in (SKILL_SOURCES, AGENT_SOURCES)
        for path in root.rglob("*")
        if path.is_file()
        and "CLAUDE.md" in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == []


@pytest.mark.parametrize("skill", GUIDANCE_SKILLS)
def test_guidance_skill_names_agents_md(skill: str) -> None:
    assert "AGENTS.md" in skill_source_text(skill)


def test_git_conventions_guideline_names_agents_md_and_skill_pointer() -> None:
    text = (REPO_ROOT / "ai-process" / "guidelines" / "git-conventions.md").read_text(
        encoding="utf-8"
    )
    assert "CLAUDE.md" not in text
    assert "AGENTS.md" in text
    assert "sources/skills/git-conventions/SKILL.md" in text
    assert "body.md" not in text
