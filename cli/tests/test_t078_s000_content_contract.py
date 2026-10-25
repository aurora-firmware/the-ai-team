"""Tests for T-078: S-000 content contract in the spec authoring guide."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = REPO_ROOT / "guides" / "spec-authoring-guide.md"
HEADING = "## The system overview spec (S-000)"
NEXT_HEADING = "## How to write measurable success criteria"
S000_SECTIONS = [
    "Purpose",
    "Users",
    "Pain points",
    "Use cases",
    "Solution overview",
    "Components",
    "Project exclusions",
]


def _s000_section() -> str:
    text = GUIDE_PATH.read_text(encoding="utf-8")
    assert HEADING in text, f"missing heading {HEADING!r}"
    start = text.index(HEADING)
    end = text.index(NEXT_HEADING)
    assert start < end, "S-000 section must precede the success-criteria section"
    return text[start:end]


def test_s000_section_lists_seven_sections_in_order() -> None:
    section = _s000_section()
    positions = []
    for name in S000_SECTIONS:
        match = re.search(rf"^\d+\.\s+\*\*{re.escape(name)}\*\*", section, re.M)
        assert match, f"missing S-000 section entry {name}"
        positions.append(match.start())
    assert positions == sorted(positions)


def test_s000_section_states_component_entry_fields() -> None:
    section = _s000_section().lower()
    for field in ("name", "owned responsibility", "boundary", "works with"):
        assert field in section, f"missing component field {field}"


def test_s000_section_states_exclusions_of_content() -> None:
    section = _s000_section().lower()
    for item in (
        "technology choices",
        "interface definitions",
        "configuration",
        "implementation order",
        "per-component status",
        "plain language",
    ):
        assert item in section, f"missing {item}"


def test_s000_section_states_boundary_rule() -> None:
    section = _s000_section().lower()
    assert "owns the decomposition" in section
    assert "contract of one component or feature" in section
    assert "purpose names the s-000 component" in section


def test_feature_spec_recipe_headings_are_still_present_in_order() -> None:
    text = GUIDE_PATH.read_text(encoding="utf-8")
    headings = [
        "### Purpose",
        "### Exclusions",
        "### Architecture — Design Principles",
        "### Interfaces",
        "### Workflow",
        "### Configuration Requirements",
        "### Implementation Order",
        "### Amendment Log",
    ]
    positions = []
    for heading in headings:
        match = re.search(rf"^{re.escape(heading)}$", text, re.M)
        assert match, f"missing feature-spec recipe heading {heading}"
        positions.append(match.start())
    assert positions == sorted(positions)
    assert text.index("## How to write each section") < positions[0]
    assert positions[-1] < text.index(HEADING)


TEMPLATE_PATH = (
    REPO_ROOT / "cli" / "src" / "ai_team" / "templates" / "system-overview.md"
)


def test_s000_section_defines_component_and_its_kinds() -> None:
    section = _s000_section().lower()
    assert (
        "a part of the software solution, or something that affects the "
        "solution's use, delivery or deployment" in section
    )
    for kind in ("software", "documentation", "delivery and deployment", "tooling"):
        assert kind in section, f"missing component kind {kind}"


def test_s000_section_states_the_three_component_checks() -> None:
    section = _s000_section().lower()
    assert "three checks" in section
    assert "serves at least one use case" in section
    assert "one spec could own its contract" in section
    assert "boundary would hold if the implementation were reorganised" in section


def test_s000_section_splits_components_into_solution_and_infrastructure() -> None:
    section = _s000_section()
    assert "**Solution**" in section
    assert "**Development infrastructure**" in section


def test_s000_section_requires_decisions_needed_and_asks_without_answering() -> None:
    section = _s000_section()
    assert "**Decisions needed**" in section
    assert "asks technology questions and never answers them" in section


def test_s000_section_states_users_scope() -> None:
    section = _s000_section().lower()
    assert "users names the users of the solution" in section


FLAT_LIST_SOURCES = [
    GUIDE_PATH,
    REPO_ROOT / "cli" / "src" / "ai_team" / "templates" / "system-overview.md",
    REPO_ROOT
    / "cli"
    / "src"
    / "ai_team"
    / "init"
    / "sources"
    / "skills"
    / "new-system-overview"
    / "SKILL.md",
    REPO_ROOT
    / "cli"
    / "src"
    / "ai_team"
    / "init"
    / "sources"
    / "skills"
    / "architecture-consistency-review"
    / "SKILL.md",
]


def test_no_source_keeps_a_flat_component_list_valid() -> None:
    """S-007 0.3: an S-000 without the component groups is not grandfathered."""
    for path in FLAT_LIST_SOURCES:
        text = " ".join(path.read_text(encoding="utf-8").lower().split())
        assert "stays valid" not in text, f"{path} still grandfathers a flat list"


def test_template_keeps_seven_sections_and_groups_components() -> None:
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    top = re.findall(r"^## (.+)$", text, re.M)
    assert top[:7] == S000_SECTIONS
    components = text[text.index("## Components") : text.index("## Project exclusions")]
    assert components.index("### Solution") < components.index(
        "### Development infrastructure"
    )
    infrastructure = components[components.index("### Development infrastructure") :]
    assert "**Decisions needed:**" in infrastructure
