"""Skill and agent frontmatter declares consistent skills and tools.

Agents get no `Skill` or `Agent` tool: a subagent runs only the skills
preloaded through its `skills:` field and cannot spawn other subagents.
"""

from __future__ import annotations

import re

import pytest

from tests.source_paths import SKILL_SOURCES, skill_frontmatter

AGENT_SOURCES = SKILL_SOURCES.parent / "agents"

SKILLS = sorted(path.name for path in SKILL_SOURCES.iterdir() if path.is_dir())
AGENTS = sorted(path.stem for path in AGENT_SOURCES.glob("*.md"))


def _field(frontmatter: str, key: str) -> str:
    match = re.search(rf"^{key}:[ \t]*(.*)$", frontmatter, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _allowed_tools(skill: str) -> list[str]:
    value = _field(skill_frontmatter(skill), "allowed-tools")
    return [tool.strip() for tool in value.split(",") if tool.strip()]


def _skill_dependencies(skill: str) -> set[str]:
    return {
        match.group(1)
        for tool in _allowed_tools(skill)
        if (match := re.fullmatch(r"Skill\(([a-z0-9-]+)\)", tool))
    }


def _agent_frontmatter(agent: str) -> str:
    text = (AGENT_SOURCES / f"{agent}.md").read_text(encoding="utf-8")
    match = re.match(r"---\n.*?\n---(?=\n)", text, re.DOTALL)
    if match is None:
        raise ValueError(f"{agent}.md has no leading frontmatter block")
    return match.group(0)


def _preloaded_skills(agent: str) -> set[str]:
    return set(_field(_agent_frontmatter(agent), "skills").split())


def test_sources_are_found():
    assert SKILLS
    assert AGENTS


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_dependencies_name_existing_model_invocable_skills(skill: str):
    for dependency in _skill_dependencies(skill):
        assert dependency in SKILLS, f"{skill} declares missing Skill({dependency})"
        target = skill_frontmatter(dependency)
        assert _field(target, "disable-model-invocation") != "true", (
            f"{skill} declares Skill({dependency}), which disables model invocation"
        )


@pytest.mark.parametrize("agent", AGENTS)
def test_agent_preloads_existing_skills_closed_under_their_dependencies(agent: str):
    preloaded = _preloaded_skills(agent)

    assert preloaded <= set(SKILLS), preloaded - set(SKILLS)
    for skill in sorted(preloaded):
        missing = _skill_dependencies(skill) - preloaded
        assert not missing, f"{agent} preloads {skill} but not {sorted(missing)}"


@pytest.mark.parametrize("agent", AGENTS)
def test_agent_preloads_no_skill_that_spawns_agents(agent: str):
    spawning = {s for s in _preloaded_skills(agent) if "Agent" in _allowed_tools(s)}

    assert not spawning, f"{agent} preloads {sorted(spawning)}, which declare Agent"
