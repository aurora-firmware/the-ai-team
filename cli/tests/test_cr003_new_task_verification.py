"""CR-003 T-106: new-task defines verification modes, the design-review contract, and run context."""

from __future__ import annotations

from tests.source_paths import skill_source_text


def body() -> str:
    return skill_source_text("new-task")


def flat(text: str) -> str:
    return " ".join(text.split())


def test_new_task_defines_test_and_design_review_verification_modes():
    text = flat(body())
    assert "## Verification Modes" in text
    assert "**test**" in text
    assert "**design review**" in text
    assert "test file is listed in Files to Touch" in text
    assert "`spec-breakdown` chooses" in text


def test_new_task_design_review_verification_holds_design_review_line_and_reference_bullets():
    text = flat(body())
    assert "`Design review:`" in text
    assert "one bullet per reference" in text
    assert "each accepted ADR" in text
    assert "S-000" in text
    assert "no test command" in text


def test_new_task_states_verification_line_run_context():
    text = flat(body())
    assert "from the repository root in a fresh shell" in text
    assert "independently of the other lines" in text
    assert "changes into it on that same line" in text
    assert "cd <dir> && <command>" in text


def test_new_task_verifiable_rule_and_pitfall_name_the_design_review_alternative():
    lines = body().splitlines()
    verifiable = next(line for line in lines if line.startswith("- **Verifiable**"))
    pitfall = next(
        line for line in lines if line.startswith("- **No verification command**")
    )
    assert "design review" in verifiable.lower()
    assert "design review" in pitfall.lower()


def test_new_task_source_does_not_hardcode_uv_run():
    assert "uv run" not in body()
