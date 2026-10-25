from pathlib import Path

import pytest

from ai_team.core.templates import load_template


def test_load_template_task_matches_bundled_source() -> None:
    source_template = (
        Path(__file__).resolve().parents[1] / "src/ai_team/templates/task.md"
    )

    assert load_template("task") == source_template.read_text(encoding="utf-8")


def test_load_template_change_request_matches_bundled_source() -> None:
    source_template = (
        Path(__file__).resolve().parents[1] / "src/ai_team/templates/change-request.md"
    )

    assert load_template("change-request") == source_template.read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "kind",
    ["task", "bug", "spec", "adr", "report", "change-request", "system-overview"],
)
def test_load_template_returns_non_empty_frontmatter_for_each_kind(kind: str) -> None:
    content = load_template(kind)

    assert content
    assert content.startswith("---")


def test_change_request_template_mentions_desired_changes_and_spec_amendments() -> None:
    content = load_template("change-request").lower()

    assert "desired changes" in content
    assert "spec amendments" in content


def test_load_template_rejects_unknown_kind_with_supported_kinds() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported template kind 'unknown'. Supported kinds: task, bug, spec, adr, report, change-request, system-overview"
        ),
    ):
        load_template("unknown")


def _headings(content: str, prefix: str) -> list[str]:
    return [
        line[len(prefix) :].strip()
        for line in content.splitlines()
        if line.startswith(prefix)
    ]


def test_system_overview_template_matches_bundled_source() -> None:
    source_template = (
        Path(__file__).resolve().parents[1] / "src/ai_team/templates/system-overview.md"
    )

    assert load_template("system-overview") == source_template.read_text(
        encoding="utf-8"
    )


def test_system_overview_template_has_the_s000_sections_in_order() -> None:
    assert _headings(load_template("system-overview"), "## ") == [
        "Purpose",
        "Users",
        "Pain points",
        "Use cases",
        "Solution overview",
        "Components",
        "Project exclusions",
        "Amendment Log",
    ]


@pytest.mark.parametrize(
    "heading",
    ["Architecture", "Workflow", "Configuration Requirements", "Implementation Order"],
)
def test_system_overview_template_omits_feature_spec_heading(heading: str) -> None:
    assert heading not in _headings(load_template("system-overview"), "## ")


def test_system_overview_template_uses_the_spec_title_placeholders() -> None:
    content = load_template("system-overview")

    assert 'title: "[Specification Title]"' in content
    assert "\n# [Specification Title]\n" in content


def test_system_overview_template_shows_one_component_example_with_all_fields() -> None:
    content = load_template("system-overview")

    for label in ("Name", "Responsibility", "Boundary", "Works with"):
        assert f"- **{label}:**" in content


REPO_ROOT = Path(__file__).resolve().parents[2]
NEW_SPEC_SKILL = REPO_ROOT / "cli/src/ai_team/init/sources/skills/new-spec/body.md"
AUTHORING_GUIDE = REPO_ROOT / "guides/spec-authoring-guide.md"
REMOVED_TERMS = ("System Diagram", "Responsibility Separation")


def _guide_feature_spec_part() -> str:
    text = AUTHORING_GUIDE.read_text(encoding="utf-8")
    start = text.index("## The content boundary")
    end = text.index("## The system overview spec (S-000)")
    after_s000 = text.index("## How to write measurable success criteria")
    return text[start:end] + text[after_s000:]


@pytest.mark.parametrize("heading", ["System Diagram", "Responsibility Separation"])
def test_spec_template_omits_system_wide_architecture_heading(heading: str) -> None:
    assert heading not in _headings(load_template("spec"), "### ")


def test_spec_template_keeps_design_principles_and_interfaces_headings() -> None:
    content = load_template("spec")

    assert "Design Principles" in _headings(content, "### ")
    assert "Interfaces" in _headings(content, "## ")
    assert "Components" not in _headings(content, "## ")


def test_spec_template_says_purpose_names_the_s000_component() -> None:
    content = load_template("spec")

    assert "system-wide structure lives in S-000" in content
    assert "Purpose names the S-000 component" in content


def test_new_spec_skill_describes_interfaces_and_not_removed_sections() -> None:
    content = NEW_SPEC_SKILL.read_text(encoding="utf-8")

    assert "### Interfaces" in content
    assert "**Interfaces are described for this spec's own component" in content
    for term in REMOVED_TERMS:
        assert term not in content
    assert "### Components" not in content
    assert "**Components are described" not in content


def test_authoring_guide_feature_spec_part_drops_removed_sections() -> None:
    content = _guide_feature_spec_part()

    for term in REMOVED_TERMS:
        assert term not in content
    assert "### Components" not in content
    assert "## Components" not in content
    assert "**Components are described" not in content
    assert "### Interfaces" in content
    assert "## Interfaces" in content


def test_authoring_guide_content_boundary_points_to_s000_for_decomposition() -> None:
    text = AUTHORING_GUIDE.read_text(encoding="utf-8")
    boundary = text[text.index("## The content boundary") :]
    boundary = boundary[: boundary.index("\n## How to write each section")]

    assert "S-000" in boundary


def test_authoring_guide_implementations_table_lists_system_overview_surfaces() -> None:
    text = AUTHORING_GUIDE.read_text(encoding="utf-8")
    table = text[text.index("## Implementations of this guide") :]

    assert "cli/src/ai_team/templates/system-overview.md" in table
    assert "cli/src/ai_team/init/sources/skills/new-system-overview/body.md" in table


def test_system_overview_template_points_at_nothing_outside_the_project() -> None:
    # Consuming projects receive templates but not guides/ or ai-process/.
    content = load_template("system-overview")

    assert "Spec Authoring Guide" not in content
    assert "Boundary rule" in content


DELIVERED_TREES = (
    REPO_ROOT / "cli/src/ai_team/templates",
    REPO_ROOT / "cli/src/ai_team/init/sources",
    REPO_ROOT / "cli/src/ai_team/init/scaffolds",
)
UNDELIVERED_REFERENCES = ("Spec Authoring Guide", "guides/", "ai-process/")


def test_delivered_files_do_not_refer_to_documents_init_never_delivers() -> None:
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {reference}"
        for tree in DELIVERED_TREES
        for path in sorted(tree.rglob("*"))
        if path.is_file()
        for reference in UNDELIVERED_REFERENCES
        if reference in path.read_text(encoding="utf-8", errors="ignore")
    ]

    assert offenders == []
