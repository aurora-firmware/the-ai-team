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
    [
        "Alternatives Considered",
        "Workflow",
        "Configuration Requirements",
        "Implementation Order",
    ],
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


def test_spec_template_has_alternatives_and_interfaces_but_no_architecture() -> None:
    headings = _headings(load_template("spec"), "## ")

    assert "Alternatives Considered" in headings
    assert "Interfaces" in headings
    assert "Architecture" not in headings


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
