"""Template frontmatter matches the fields and statuses the CLI writes."""

from ai_team.core.templates import load_template


def test_progress_report_decision_sample_uses_accepted() -> None:
    assert "| 001 | Decision title | accepted |" in load_template("report")
