"""CR-003 T-108: the tdd skill carries a design-review tasks section."""

from __future__ import annotations

import pytest

from tests.source_paths import skill_export_path, skill_source_text

COPIES = {
    "source": skill_source_text("tdd"),
    "claude": skill_export_path("tdd").read_text(encoding="utf-8"),
}
DESIGN_REVIEW_RECORD = (
    "**Design-review record** — for design-review tasks, the Work Log handoff "
    "names the documents checked, each conflict found and how it was fixed, "
    "and the result; no test file is produced."
)
TEST_ONLY_BULLET_STARTS = (
    "- For test tasks, tests cover both success and failure paths.",
    "- For test tasks, tests are independent",
    "- For test tasks, test names describe",
    "- For test tasks, the implementation is minimal",
    "- For test tasks, all tests pass when run together.",
)


def body() -> str:
    return skill_source_text("tdd")


def flat(text: str) -> str:
    return " ".join(text.split())


def section_of(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def section() -> str:
    text = body()
    start = text.index("## Design-review tasks")
    next_heading = text.find("\n## ", start + 1)
    return flat(text[start:] if next_heading == -1 else text[start:next_heading])


def test_section_applies_when_verification_holds_design_review_line():
    text = section()
    assert text.startswith("## Design-review tasks")
    assert "`Design review:`" in text
    assert "Verification section" in text
    assert "detect the line" in text


def test_section_replaces_red_green_cycle_with_reading_and_checking_references():
    text = section()
    assert "in place of the red/green cycle (Steps 2-6)" in text
    assert "Read every reference" in text
    assert "S-000" in text
    assert "when running the review" in text
    assert "Check the changed text against each" in text
    assert "Steps 0, 7 and 9 still apply" in text


def test_section_requires_work_log_to_record_documents_conflicts_and_result():
    text = section()
    assert "Work Log handoff" in text
    assert "the documents checked" in text
    assert "each conflict found and how it was fixed" in text
    assert "the result" in text


def test_section_escalates_instead_of_adding_an_undeclared_test():
    text = section()
    assert "escalate" in text
    assert "a test can observe" in text
    assert "outside Files to Touch" in text
    assert "changing a reference document" in text
    assert "undeclared test" in text


def test_input_and_quality_sections_distinguish_design_review_tasks():
    text = body()
    for heading in ("## Input Requirements", "## Quality Criteria"):
        assert "design-review" in flat(section_of(text, heading)).lower(), heading
    assert "For test tasks, every acceptance criterion has at least one test" in flat(
        text
    )


@pytest.mark.parametrize("copy", COPIES.values(), ids=COPIES.keys())
def test_output_format_pins_design_review_record_and_test_task_qualifiers(copy):
    output = flat(section_of(copy, "## Output Format"))
    assert DESIGN_REVIEW_RECORD in output
    assert "**Test files** — for test tasks, one or more" in output
    assert "**Implementation files** — for test tasks, production code" in output


@pytest.mark.parametrize("copy", COPIES.values(), ids=COPIES.keys())
def test_quality_criteria_scope_test_bullets_to_test_tasks(copy):
    quality = section_of(copy, "## Quality Criteria")
    bullets = {flat(line) for line in quality.splitlines() if line.startswith("- ")}
    for start in TEST_ONLY_BULLET_STARTS:
        matching = [b for b in bullets if b.startswith(start)]
        assert len(matching) == 1, start
