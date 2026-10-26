"""Regression coverage for model-invocable skill-to-skill targets."""

from __future__ import annotations

import re

from tests.source_paths import (
    SKILL_SOURCES,
    skill_frontmatter,
)

SKILL_INVOCATION = re.compile(r"Skill\(([^)]+)\)")
MODEL_INVOCATION_DISABLED = re.compile(
    r"^disable-model-invocation:\s*true\s*$", re.MULTILINE
)


def test_skill_invocation_targets_allow_model_invocation() -> None:
    """A skill named in Skill(...) must be callable by the invoking model."""
    for skill_dir in sorted(SKILL_SOURCES.iterdir()):
        caller_header = skill_frontmatter(skill_dir.name)
        for target_name in SKILL_INVOCATION.findall(caller_header):
            target_header = skill_frontmatter(target_name)
            assert not MODEL_INVOCATION_DISABLED.search(target_header), (
                f"{skill_dir.name} invokes {target_name}, but "
                "the target disables model invocation"
            )
