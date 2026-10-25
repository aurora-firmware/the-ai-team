"""CR-003 T-109: spec-breakdown chooses each task's verification mode."""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text


def source() -> str:
    return skill_source_text("spec-breakdown")


def export() -> str:
    return skill_export_path("spec-breakdown").read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.split())


def step3_bullet(text: str) -> str:
    start = text.index("- **Verification mode**")
    return text[start : text.index("During task writing", start)]


def test_step3_requires_choosing_test_or_design_review_per_task():
    bullet = step3_bullet(flat(source()))
    assert "the Planner decides" in bullet
    assert "**test**" in bullet
    assert "**design review**" in bullet


def test_step3_gives_code_cli_output_or_observable_rule_a_test_with_test_file_listed():
    bullet = step3_bullet(flat(source()))
    assert "changes code, CLI output, or a rule a test can observe" in bullet
    assert "test file is in Files to Touch" in bullet
    assert "Anything a test can observe gets a test" in bullet


def test_step3_keeps_baseline_suite_rule_for_shared_interfaces():
    bullet = step3_bullet(flat(source()))
    assert "project's documented baseline/full-suite command" in bullet


def test_step3_prose_only_task_gets_design_review_with_references():
    bullet = step3_bullet(flat(source()))
    assert "changes only prose" in bullet
    assert "`Design review:` Verification form" in bullet
    assert "the source spec" in bullet
    assert "the accepted ADRs" in bullet
    assert "S-000 when it exists" in bullet


def test_verifiable_quality_criterion_accepts_named_design_review():
    text = flat(source())
    start = text.index("Every task is **verifiable**")
    assert (
        "design review" in text[start : text.index("Every task is **self-contained**")]
    )


def test_verification_pitfall_accepts_named_design_review():
    text = flat(source())
    start = text.index("- **Forgetting verification")
    assert "design review" in text[start : text.index("- **File conflicts**")]


def test_generated_skill_carries_the_verification_mode_rule():
    assert "**Verification mode**" in flat(export())


def step3_text(text: str) -> str:
    start = text.index("### Step 3")
    return text[start : text.index("### Step 4", start)]


def step6_text(text: str) -> str:
    start = text.index("### Step 6")
    return text[start : text.index("### Step 7", start)]


def test_step3_task_regenerates_generated_files_its_change_affects():
    step3 = step3_text(flat(source()))
    assert "regenerates the generated files" in step3
    assert "its own change affects" in step3
    assert "lists them in Files to Touch" in step3


def test_plan_never_ends_with_a_regenerate_everything_task():
    text = flat(source())
    assert 'never ends with a separate "regenerate everything" task' in text
    step4 = text[text.index("### Step 4") : text.index("### Step 5")]
    assert "regenerate everything" in step4


def test_step3_command_change_lists_the_projects_generated_command_reference():
    step3 = step3_text(flat(source()))
    assert "arguments, options or help text" in step3
    assert "generated command reference" in step3
    assert "named in its guidance" in step3
    assert "the project's own" in step3


def test_regeneration_wording_does_not_hardcode_this_repositorys_files():
    for text in [source(), export()]:
        assert "cli/docs/commands.md" not in text
        assert "gen_docs.sh" not in text


def test_step6_no_longer_claims_the_architect_does_not_run_commands():
    for text in [source(), export()]:
        assert "does not run commands" not in step6_text(flat(text))


def test_step6_architect_receives_absolute_task_paths_ai_team_reported():
    step6 = step6_text(flat(source()))
    assert "absolute task paths" in step6
    assert "`ai-team` reported" in step6
