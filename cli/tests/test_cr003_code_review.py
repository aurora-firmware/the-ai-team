"""CR-003 section 3: the code-review severity rubric for CI and Description findings."""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text

COPIES = {
    "source": skill_source_text("code-review"),
    "export": skill_export_path("code-review").read_text(encoding="utf-8"),
}


def severity_section(text: str) -> str:
    start = text.index("### Severity")
    end = text.index("### Cannot Verify From the Diff")
    return text[start:end]


def test_severity_makes_ci_breaking_findings_at_least_important():
    for name, text in COPIES.items():
        section = severity_section(text)
        assert "at least **Important**" in section, name
        assert "breaks CI" in section, name
        for example in (
            "local git history",
            "network access",
            "installed tool versions",
        ):
            assert example in section, (name, example)


def test_severity_directs_reviewer_to_compare_new_tests_against_ci_configuration():
    for name, text in COPIES.items():
        section = severity_section(text)
        assert "CI configuration" in section, name
        assert (
            "When the project has CI configuration, compare the new tests against it."
            in section
        ), name


def test_severity_names_no_ci_provider_or_file_path():
    section = severity_section(COPIES["source"])
    for forbidden in (
        "GitHub",
        "GitLab",
        ".github",
        ".gitlab-ci",
        "Jenkins",
        "CircleCI",
    ):
        assert forbidden not in section


def test_never_minor_rule_covers_contradicting_a_task_description_sentence():
    for name, text in COPIES.items():
        section = severity_section(text)
        assert "never Minor" in section, name
        assert "explicit sentence of the task Description" in section, name
        assert "The function never raises" in section, name


def design_review_section(text: str) -> str:
    start = text.index("### Design-Review Tasks")
    end = text.index("### Severity")
    return text[start:end]


def test_design_review_section_applies_when_verification_holds_design_review_line():
    for name, text in COPIES.items():
        section = design_review_section(text)
        assert "`Design review:`" in section, name
        assert "Verification section" in section, name


def test_design_review_section_checks_work_log_record_against_listed_references():
    for name, text in COPIES.items():
        section = design_review_section(text)
        assert "Work Log" in section, name
        for element in (
            "documents checked",
            "each conflict found and how it was fixed",
            "the result",
            "listed references",
        ):
            assert element in section, (name, element)


def test_design_review_section_checks_planning_choice_and_rates_observable_change():
    for name, text in COPIES.items():
        section = design_review_section(text)
        assert "planning choice" in section, name
        assert "no test pins" in section, name
        assert "at least **Important**" in section, name
        assert "the task needed a test" in section, name


def test_design_review_section_rates_missing_or_incomplete_record_at_least_important():
    for name, text in COPIES.items():
        section = design_review_section(text)
        assert "missing" in section and "omits a listed reference" in section, name
        assert "red/green evidence" in section, name


def test_design_review_section_reads_s000_at_review_time_when_listed():
    for name, text in COPIES.items():
        section = design_review_section(text)
        assert "S-000" in section, name
        assert "at review time" in section, name
        assert "not at session start" in section, name


def test_stage_two_tests_and_quality_criteria_have_design_review_equivalent():
    for name, text in COPIES.items():
        stage_two = text[
            text.index("**Stage 2 Checklist:**") : text.index("### Design-Review Tasks")
        ]
        assert "design-review task" in stage_two, name
        criteria = text[
            text.index("## Quality Criteria") : text.index("## Rationalizations")
        ]
        assert "design-review record" in criteria, name
