"""A skill body is textually substituted by the harness, so the argument
placeholder may appear only once, where the value itself is meant."""

from __future__ import annotations

import pytest

from tests.source_paths import SKILL_SOURCES, skill_source_text

ARGUMENT_PLACEHOLDER = "$ARGUMENTS"
ARGUMENT_VALUE_LINE = f"Argument: `{ARGUMENT_PLACEHOLDER}`"


def _skills_using_placeholder() -> list[str]:
    return sorted(
        path.parent.name
        for path in SKILL_SOURCES.glob("*/SKILL.md")
        if ARGUMENT_PLACEHOLDER in path.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("skill_name", _skills_using_placeholder())
def test_skill_names_the_argument_placeholder_only_once(skill_name: str) -> None:
    occurrences = skill_source_text(skill_name).count(ARGUMENT_PLACEHOLDER)

    assert occurrences == 1, (
        f"{skill_name} names {ARGUMENT_PLACEHOLDER} {occurrences} times; "
        "the harness substitutes every mention, so prose must say 'the argument'"
    )


@pytest.mark.parametrize("skill_name", _skills_using_placeholder())
def test_skill_places_the_argument_placeholder_on_a_dedicated_value_line(
    skill_name: str,
) -> None:
    lines_with_placeholder = [
        line
        for line in skill_source_text(skill_name).splitlines()
        if ARGUMENT_PLACEHOLDER in line
    ]

    assert lines_with_placeholder == [ARGUMENT_VALUE_LINE]
