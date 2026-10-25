"""CR-003 T-111: Gate 2 accepts a named design review as verification."""

from __future__ import annotations

from tests.source_paths import skill_source_text


def flat(text: str) -> str:
    return " ".join(text.split())


def step(heading: str) -> str:
    text = skill_source_text("spec-breakdown-review")
    start = text.index(heading)
    end = text.find("\n### ", start + 1)
    return flat(text[start:] if end == -1 else text[start:end])


def test_step_1_reads_verification_command_or_design_review():
    assert "verification command or design review" in step("### Step 1")


def test_step_6_accepts_design_review_section_listing_references():
    text = step("### Step 6")
    assert "No clear verification command." not in text
    assert "clear verification command" in text
    assert "task that changes only prose" in text
    assert "`Design review:`" in text
    assert "lists its references" in text


def test_step_6_flags_design_review_task_a_test_can_observe():
    text = step("### Step 6")
    assert "design-review task" in text
    assert "code, CLI output, or a rule a test can observe" in text
    assert "needs a test" in text


def test_step_6_flags_design_review_task_with_empty_or_specless_references():
    text = step("### Step 6")
    assert "reference list is empty or omits the source spec" in text
